"""Pinned security tools copied into native guests without guest network access."""

from __future__ import annotations

import hashlib
import json
import os
import tarfile
import threading
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain, digest
from dockyard.workspace import atomic_write

if TYPE_CHECKING:
    from dockyard.runtimes.linux import LinuxRuntime

MANIFEST: dict[str, Any] = {
    name: entry
    for name, entry in json.loads((CONTENT / "runtime/linux/guest-tools.json").read_text()).items()
    if not name.startswith("_")
}
# Bound each extracted file so a corrupt archive cannot fill the cache.
MEMBER_LIMIT = 512 * 1024**2
# Part of each bundle's identity, so a change to how bundles are assembled replaces cached ones.
BUNDLE_FORMAT = 2


def archive_entries(names: list[str]) -> dict[str, dict[str, Any]]:
    """Describe each tool's verified archive as a toolchain download for this host."""
    architecture = host.architecture()
    entries = {}
    for name in names:
        tool = MANIFEST[name]
        archive = tool["archives"][architecture]
        filename = PurePosixPath(archive["url"]).name
        entries[filename] = {
            "version": tool["version"],
            "url": archive["url"],
            "sha256": archive["sha256"],
            "path": "native/guest-tools/" + filename,
            "max_download_bytes": archive["size"],
        }
    return entries


def destination(tool: dict[str, Any], member: str) -> str | None:
    """Map one archive member onto its guest path, or None when it is not needed."""
    for source, target in tool["map"].items():
        if source.endswith("/") and member.startswith(source) and member != source:
            relative = PurePosixPath(member[len(source) :])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeErrorBase("A pinned tool archive contains an unsafe path.")
            return str(target) + relative.as_posix()
        if member == source:
            return str(target)
    return None


def bundle(runtime: LinuxRuntime, names: list[str], cancel: threading.Event) -> Path:
    entries = archive_entries(names)
    tools = Toolchain(runtime.tools, entries)
    archives = {
        name: tools.ensure(
            PurePosixPath(MANIFEST[name]["archives"][host.architecture()]["url"]).name,
            cancel,
            runtime.report,
        )
        for name in names
    }
    identity = hashlib.sha256(
        json.dumps({"format": BUNDLE_FORMAT, "entries": entries}, sort_keys=True).encode()
    ).hexdigest()
    directory = runtime.tools / "native"
    output = directory / f"guest-tools-{identity[:16]}.tar"
    metadata = output.with_suffix(".json")
    with operation_lock(runtime.tools / "locks", "guest-tools-" + identity[:16]):
        if output.is_symlink() or metadata.is_symlink():
            raise RuntimeErrorBase("The guest tool bundle is a symbolic link; preserved.")
        if output.is_file() and metadata.is_file():
            try:
                saved = json.loads(metadata.read_text())
            except (ValueError, UnicodeError):
                saved = {}
            if isinstance(saved, dict) and saved.get("sha256") == digest(output):
                return output
        partial = output.with_suffix(".part")
        if partial.is_symlink():
            raise RuntimeErrorBase("The guest tool staging path is a symbolic link; preserved.")
        runtime.report("Assembling verified guest security tools")
        with tarfile.open(partial, "w") as bundled:
            for name in names:
                tool = MANIFEST[name]
                root = tool["archives"][host.architecture()]["root"]
                with tarfile.open(archives[name], "r:*") as source:
                    for member in source:
                        if not (member.isfile() or member.isdir()):
                            continue
                        if not member.name.startswith(root):
                            continue
                        target = destination(tool, member.name[len(root) :])
                        if target is None:
                            continue
                        if member.isdir():
                            # Keep empty folders the tool reads, such as Falco's rules.d.
                            folder = tarfile.TarInfo(target)
                            folder.type = tarfile.DIRTYPE
                            folder.mode = 0o755
                            folder.uid = folder.gid = 0
                            folder.mtime = 0
                            bundled.addfile(folder)
                            continue
                        if not 0 <= member.size <= MEMBER_LIMIT:
                            raise RuntimeErrorBase("A pinned tool file exceeds its size limit.")
                        content = source.extractfile(member)
                        if content is None:
                            raise RuntimeErrorBase("A pinned tool file could not be read.")
                        info = tarfile.TarInfo(target)
                        info.size = member.size
                        info.mode = 0o755 if member.mode & 0o111 else 0o644
                        info.uid = info.gid = 0
                        info.mtime = 0
                        with content:
                            bundled.addfile(info, content)
        partial.chmod(0o600)
        os.replace(partial, output)
        atomic_write(metadata, json.dumps({"tools": names, "sha256": digest(output)}).encode())
    return output


def install(runtime: LinuxRuntime, names: list[str], cancel: threading.Event) -> None:
    """Install the named tools once in every guest, refusing a changed tool profile."""
    if not names:
        return
    archive = bundle(runtime, sorted(names), cancel)
    identity = digest(archive)
    prepared = json.loads(runtime.lab.resources.get("vm_guest_tools", "{}"))
    for entry in runtime.discover():
        name = entry["name"]
        if prepared.get(name) == identity:
            continue
        if name in prepared:
            raise RuntimeErrorBase(
                "This guest's security tools changed. Reset the lab to apply them "
                "while preserving a workspace backup."
            )
        runtime.report("Installing verified security tools in " + name)
        directory = "/tmp/dockyard-" + runtime.lab.id + "-tools"
        runtime.require(runtime.guest(name, ["mkdir", "-p", "-m", "700", directory], cancel=cancel))
        runtime.copy_to(name, archive, directory + "/tools.tar", cancel=cancel)
        runtime.require(
            runtime.guest(
                name,
                ["sudo", "tar", "--no-overwrite-dir", "-xf", directory + "/tools.tar", "-C", "/"],
                cancel=cancel,
                timeout=120,
            )
        )
        runtime.require(runtime.guest(name, ["rm", "-rf", "--", directory], cancel=cancel))
        prepared[name] = identity
        runtime.lab.resources["vm_guest_tools"] = json.dumps(prepared)
        runtime.save(runtime.lab)
