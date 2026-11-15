"""Pinned container images, each kept only where it is used.

Docker on this computer holds the images a learner or a host-side step runs with
docker. Images that only clusters use are private archives that load straight
into cluster nodes, so they never appear in the learner's own image list.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.models import Runtime, Unit
from dockyard.process import ProcessResult, run
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.store import BusyError

PINNED: dict[str, str] = json.loads((CONTENT / "compatibility.json").read_text())["images"]
ALIAS_PREFIX = "dockyard-cache/"
# Docker itself runs or builds from these in every runtime; clusters never name them.
HOST_ONLY = frozenset({"python", "registry", "git", "kind"})
LABELS = {
    "python": "Python",
    "postgres": "PostgreSQL",
    "redis": "Redis",
    "registry": "image registry",
    "busybox": "BusyBox",
    "kind": "Kubernetes node",
    "git": "Git",
    "calico_calico": "Calico",
    "calico_node": "Calico node",
    "calico_third_party_cni_plugins": "Calico network plugins",
    "traefik": "Traefik",
    "metallb_controller": "MetalLB controller",
    "metallb_speaker": "MetalLB speaker",
    "metrics_server": "metrics server",
    "prometheus": "Prometheus",
    "flux_source": "Flux source controller",
    "flux_kustomize": "Flux kustomize controller",
    "csi_hostpath": "CSI host path driver",
    "csi_registrar": "CSI registrar",
    "csi_liveness": "CSI liveness probe",
    "csi_attacher": "CSI attacher",
    "csi_provisioner": "CSI provisioner",
    "csi_resizer": "CSI resizer",
}


def label(name: str) -> str:
    """A learner-facing name for a pinned image, such as "Calico node"."""
    return LABELS[name]


def alias(name: str) -> str:
    """The name a cluster knows a pinned image by; its tag records the pinned digest."""
    return f"{ALIAS_PREFIX}{name.replace('_', '-')}:{PINNED[name].split('sha256:')[-1][:16]}"


def host_images(unit: Unit) -> list[str]:
    """Pinned images this activity needs in Docker on this computer."""
    if unit.runtime == Runtime.DOCKER:
        return list(dict.fromkeys(unit.images))
    names = [name for name in unit.images if name in HOST_ONLY]
    if unit.runtime == Runtime.KUBERNETES:
        names.append("kind")
    if "loadbalancer" in unit.capabilities:
        # The lesson and its check reach the load balancer from a container on this computer.
        names.append("busybox")
    return list(dict.fromkeys(names))


def digest_reference(reference: str) -> str:
    """A pinned reference as Docker lists it: the repository and digest, without a tag."""
    name, _, digest = reference.partition("@")
    if ":" in name.rpartition("/")[2]:
        name = name.rpartition(":")[0]
    return f"{name}@{digest}"


def cluster_images(unit: Unit) -> list[str]:
    """Pinned images this activity loads into its cluster nodes from private archives."""
    if unit.runtime == Runtime.DOCKER:
        return []
    names = [name for name in unit.images if name not in HOST_ONLY]
    if "native-csi" in unit.capabilities:
        names += [name for name in PINNED if name.startswith("csi_")]
    return list(dict.fromkeys(names))


class ImageStore:
    def __init__(self, tools: Path, env: dict[str, str]):
        self.directory = tools / "image-archives"
        self.locks = tools / "locks"
        self.env = env
        self.platform = "--platform=linux/" + host.architecture()

    def docker(
        self, args: list[str], *, timeout: float = 30, cancel: threading.Event | None = None
    ) -> ProcessResult:
        return run(["docker", *args], env=self.env, timeout=timeout, cancel=cancel)

    @staticmethod
    def require(result: ProcessResult) -> None:
        if result.ok:
            return
        if result.canceled:
            raise RuntimeErrorBase("Download canceled; finished downloads are kept.")
        if result.timed_out:
            raise RuntimeErrorBase("The image download took too long. Check your connection.")
        raise RuntimeErrorBase(result.stderr.strip() or "Docker could not complete the request.")

    @contextmanager
    def exclusive(self, name: str, cancel: threading.Event) -> Iterator[None]:
        """Wait for another operation that is fetching the same image, rather than failing."""
        while True:
            try:
                with operation_lock(self.locks, "image-" + name):
                    yield
                    return
            except BusyError:
                if cancel.wait(0.5):
                    raise RuntimeErrorBase(
                        "Download canceled; finished downloads are kept."
                    ) from None

    def archive_path(self, name: str) -> Path:
        tag = alias(name).removeprefix(ALIAS_PREFIX).replace(":", "-")
        return self.directory / f"{tag}-{host.architecture()}.tar"

    def on_host(self, name: str) -> bool:
        found = self.docker(
            ["image", "inspect", self.platform, "--format", "{{.Architecture}}", PINNED[name]],
            timeout=15,
        )
        return found.ok and found.stdout.strip() == host.architecture()

    def archived(self, name: str) -> bool:
        path = self.archive_path(name)
        return path.is_file() and not path.is_symlink()

    def pull(self, name: str, cancel: threading.Event, report: Callable[[str], None]) -> None:
        report(f"Downloading the {label(name)} image")
        self.require(self.docker(["pull", self.platform, PINNED[name]], timeout=900, cancel=cancel))

    def ensure_host(
        self, name: str, cancel: threading.Event, report: Callable[[str], None]
    ) -> bool:
        """Make sure Docker holds the image; reports whether this call downloaded it."""
        with self.exclusive(name, cancel):
            if self.on_host(name):
                return False
            self.pull(name, cancel, report)
            return True

    def ensure_archive(
        self, name: str, cancel: threading.Event, report: Callable[[str], None]
    ) -> Path:
        """A private archive of the image under its alias, leaving Docker's list as it was."""
        path = self.archive_path(name)
        with self.exclusive(name, cancel):
            if self.archived(name):
                return path
            if self.directory.is_symlink() or path.is_symlink():
                raise RuntimeErrorBase("The private image cache is a symbolic link; preserved.")
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            borrowed = self.on_host(name)
            if not borrowed:
                self.pull(name, cancel, report)
            partial = path.with_suffix(".part")
            try:
                self.require(self.docker(["tag", PINNED[name], alias(name)], cancel=cancel))
                self.require(
                    self.docker(
                        ["image", "save", self.platform, "--output", str(partial), alias(name)],
                        timeout=300,
                        cancel=cancel,
                    )
                )
                partial.chmod(0o600)
                os.replace(partial, path)
            finally:
                partial.unlink(missing_ok=True)
                # Removing a name never removes an image that something else still uses.
                self.docker(["image", "rm", alias(name)], timeout=60)
                if not borrowed:
                    self.docker(["image", "rm", PINNED[name]], timeout=60)
            return path
