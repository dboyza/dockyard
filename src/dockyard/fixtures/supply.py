"""A lab-owned image registry holding the Dispatch release, for signing and admission labs."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from dockyard.models import Runtime
from dockyard.runtimes.kubernetes import KubernetesRuntime
from dockyard.runtimes.registry_publish import publish, trust_on_nodes
from dockyard.service import Service
from dockyard.workspace import atomic_write


def current() -> KubernetesRuntime:
    service = Service(Path(os.environ["DOCKYARD_DATA"]))
    lab = service.store.lab(os.environ["DOCKYARD_UNIT"])
    if (
        lab is None
        or lab.id != os.environ["DOCKYARD_LAB"]
        or lab.runtime != Runtime.KUBERNETES
        or Path(lab.workspace).resolve() != Path.cwd().resolve()
    ):
        raise RuntimeError("This shell no longer identifies the current Kubernetes lab.")
    return KubernetesRuntime(lab, service.environment(lab), service.store.save_lab, service.tools)


def registry() -> None:
    r = current()
    lab = r.lab
    name = "dockyard-" + lab.id[:12] + "-release-registry"
    volume = name + "-data"
    for kind, value in (("container", name), ("volume", volume)):
        if r.docker.inspect(kind, value) is not None:
            raise RuntimeError("A release registry resource name is occupied; preserved.")
    try:
        r.docker.require(
            r.docker.command(["volume", "create", "--label", "io.dockyard.lab=" + lab.id, volume])
        )
        created = r.docker.command(
            [
                "run",
                "-d",
                "--name",
                name,
                "--label",
                "io.dockyard.lab=" + lab.id,
                "--network",
                os.environ["DOCKYARD_NETWORK"],
                "--publish",
                # A fixed assigned port survives stop and start, keeping image names valid.
                f"127.0.0.1:{lab.resources['api_port']}:5000",
                "--memory",
                "128m",
                "--cpus",
                "0.5",
                "--volume",
                volume + ":/var/lib/registry",
                "--env",
                "REGISTRY_LOG_LEVEL=error",
                "--env",
                "OTEL_TRACES_EXPORTER=none",
                os.environ["DOCKYARD_REGISTRY_IMAGE"],
            ]
        )
        r.docker.require(created)
    finally:
        r.docker.discover()
    address = "127.0.0.1:" + lab.resources["api_port"]
    deadline = time.monotonic() + 30
    while True:
        try:
            with urlopen("http://" + address + "/v2/", timeout=2):
                break
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError("The release registry did not become reachable.") from None
            time.sleep(0.5)
    archive = r.root / "data/publish-image.tar"
    archive.parent.mkdir(parents=True, exist_ok=True)
    r.docker.require(
        r.docker.command(["save", "-o", str(archive), os.environ["DOCKYARD_IMAGE"]], timeout=120)
    )
    try:
        # The registry needs no credentials; the publisher's header is simply ignored.
        digest = publish(archive, address, "unused", tag="1.0")
    finally:
        archive.unlink(missing_ok=True)
    atomic_write(
        r.root / "data/release.json", json.dumps({"registry": address, "digest": digest}).encode()
    )
    atomic_write(Path("registry.txt"), (address + "\n").encode())
    trust_on_nodes(r, address, name)


if __name__ == "__main__":
    {"registry": registry}[sys.argv[1]]()
