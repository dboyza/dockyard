"""Repository-pinned native prerequisites that install without guest network access."""

from __future__ import annotations

import hashlib
import json
import os
import tarfile
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import MANIFEST, Toolchain, digest
from dockyard.workspace import atomic_write

if TYPE_CHECKING:
    from dockyard.runtimes.linux import LinuxRuntime


def manifest(version: str) -> dict[str, Any]:
    if version not in {"1.35.8", "1.34.12"}:
        raise RuntimeErrorBase("The requested Kubernetes prerequisite version is not pinned.")
    suffix = "-amd64" if host.architecture() == "amd64" else ""
    record = dict(
        json.loads((CONTENT / f"runtime/linux/packages-{version}{suffix}.json").read_text())
    )
    if record.get("base_image_sha256") != MANIFEST["ubuntu-node"]["sha256"]:
        raise RuntimeErrorBase("The native packages do not match the pinned guest image.")
    return record


def bundle(runtime: LinuxRuntime, cancel: threading.Event, version: str = "1.35.8") -> Path:
    record = manifest(version)
    packages = record["packages"]
    tools = Toolchain(runtime.tools, packages)
    paths = []
    for name in sorted(packages):
        if Path(name).name != name or not name.endswith(".deb"):
            raise RuntimeErrorBase("The package manifest contains an invalid filename.")
        paths.append(tools.ensure(name, cancel, runtime.report))
    directory = runtime.tools / "native"
    output = directory / f"prerequisites-{version}.tar"
    metadata = output.with_suffix(".json")
    expected = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    with operation_lock(runtime.tools / "locks", "native-bundle-" + version):
        if output.is_symlink() or metadata.is_symlink():
            raise RuntimeErrorBase("The native prerequisite bundle is a symbolic link; preserved.")
        if output.is_file() and metadata.is_file():
            try:
                saved = json.loads(metadata.read_text())
            except (ValueError, UnicodeError):
                saved = {}
            if not isinstance(saved, dict):
                saved = {}
            if saved.get("manifest") == expected and saved.get("sha256") == digest(output):
                return output
        partial = output.with_suffix(".part")
        if partial.is_symlink():
            raise RuntimeErrorBase("The prerequisite staging path is a symbolic link; preserved.")
        runtime.report("Assembling verified offline node prerequisites")
        with tarfile.open(partial, "w") as archive:
            for path in paths:
                # Only pinned regular package files are included, never cache directory contents.
                def canonical(info: tarfile.TarInfo) -> tarfile.TarInfo:
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    info.mode = 0o600
                    info.pax_headers = {}
                    return info

                archive.add(path, arcname=path.name, recursive=False, filter=canonical)
        partial.chmod(0o600)
        os.replace(partial, output)
        atomic_write(
            metadata, json.dumps({"manifest": expected, "sha256": digest(output)}).encode()
        )
    return output


def install(runtime: LinuxRuntime, cancel: threading.Event, version: str = "1.35.8") -> None:
    archive = bundle(runtime, cancel, version)
    prepared = json.loads(runtime.lab.resources.get("vm_packages", "{}"))
    if isinstance(prepared, list):
        # Earlier development records did not include artifact identities or the explicit CRI tool.
        prepared = {}
    record = manifest(version)
    identity = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    script = (CONTENT / "runtime/linux/prepare-node.sh").read_text()
    for entry in runtime.discover():
        name = entry["name"]
        if prepared.get(name) == identity:
            continue
        if name in prepared:
            raise RuntimeErrorBase(
                "This guest's prerequisite profile changed. Reset the lab to apply it "
                "while preserving a workspace backup."
            )
        runtime.report("Installing verified offline prerequisites in " + name)
        directory = "/tmp/dockyard-" + runtime.lab.id + "-packages"
        runtime.require(runtime.guest(name, ["mkdir", "-p", "-m", "700", directory], cancel=cancel))
        runtime.copy_to(name, archive, directory + "/packages.tar", cancel=cancel)
        runtime.require(
            runtime.guest(
                name,
                ["tar", "--no-same-owner", "-xf", directory + "/packages.tar", "-C", directory],
                cancel=cancel,
                timeout=60,
            )
        )
        runtime.require(
            runtime.guest(
                name,
                [
                    "sudo",
                    "env",
                    "DOCKYARD_GUEST=lima-" + name,
                    "DOCKYARD_PACKAGE_DIR=" + directory,
                    "/bin/bash",
                    "-s",
                ],
                timeout=300,
                cancel=cancel,
                input_text=script,
            )
        )
        runtime.require(runtime.guest(name, ["rm", "-rf", "--", directory], cancel=cancel))
        prepared[name] = identity
        runtime.lab.resources["vm_packages"] = json.dumps(prepared)
        runtime.save(runtime.lab)
