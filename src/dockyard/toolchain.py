"""Pinned, verified private tools; downloads never modify host package managers."""

from __future__ import annotations

import hashlib
import json
import os
import tarfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.runtimes.docker import RuntimeErrorBase


def platform_manifest(key: str | None = None) -> dict[str, Any]:
    selected = key or host.platform_key()
    if selected not in {"darwin-arm64", "linux-arm64", "linux-amd64"}:
        raise ValueError("No pinned toolchain for this host platform.")
    entries: dict[str, Any] = json.loads((CONTENT / "toolchain.json").read_text())
    if selected != "darwin-arm64":
        entries.update(json.loads((CONTENT / f"toolchain-{selected}.json").read_text()))
    return entries


MANIFEST = platform_manifest()


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


class Toolchain:
    def __init__(self, root: Path, manifest: dict[str, Any] | None = None):
        self.root = root
        self.manifest = MANIFEST if manifest is None else manifest

    def ready(self, name: str) -> bool:
        entry = self.manifest[name]
        destination: Path = self.root / str(entry["path"])
        return (
            destination.is_file()
            and not destination.is_symlink()
            and digest(destination) == entry.get("installed_sha256", entry["sha256"])
        )

    @staticmethod
    def install_verified(partial: Path, destination: Path, entry: dict[str, str]) -> None:
        if digest(partial) != entry["sha256"]:
            partial.unlink()
            raise RuntimeErrorBase("The downloaded tool failed its pinned integrity check.")
        candidate = partial
        if member_name := entry.get("archive_member"):
            candidate = destination.with_suffix(destination.suffix + ".install")
            if candidate.is_symlink():
                raise RuntimeErrorBase("The private installation path is a symbolic link.")
            try:
                with tarfile.open(partial, "r:gz") as archive:
                    member = archive.getmember(member_name)
                    if not member.isfile() or not 0 < member.size <= 256 * 1024**2:
                        raise RuntimeErrorBase(
                            "The pinned archive member is not a bounded regular file."
                        )
                    source = archive.extractfile(member)
                    if source is None:
                        raise RuntimeErrorBase("The pinned tool was not found in its archive.")
                    with source, candidate.open("wb") as output:
                        while block := source.read(1024 * 1024):
                            output.write(block)
                        output.flush()
                        os.fsync(output.fileno())
                if digest(candidate) != entry["installed_sha256"]:
                    raise RuntimeErrorBase("The extracted tool failed its pinned integrity check.")
            except (tarfile.TarError, KeyError) as error:
                candidate.unlink(missing_ok=True)
                raise RuntimeErrorBase(
                    "The verified archive does not contain the expected tool."
                ) from error
            except BaseException:
                candidate.unlink(missing_ok=True)
                raise
        candidate.chmod(0o755 if entry["path"].startswith("bin/") else 0o600)
        os.replace(candidate, destination)
        partial.unlink(missing_ok=True)

    def ensure(self, name: str, cancel: threading.Event, report: Callable[[str], None]) -> Path:
        host.platform_key()
        entry = self.manifest[name]
        destination: Path = self.root / str(entry["path"])
        with operation_lock(self.root / "locks", "tool-" + name):
            if self.ready(name):
                return destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            partial = destination.with_suffix(destination.suffix + ".part")
            if partial.is_symlink():
                raise RuntimeErrorBase("The private download cache is a symbolic link.")
            if partial.is_file() and digest(partial) == entry["sha256"]:
                self.install_verified(partial, destination, entry)
                return destination
            maximum = int(entry.get("max_download_bytes", 512 * 1024 * 1024))
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            report(f"Downloading {name} {entry['version']}")
            try:
                with urlopen(Request(entry["url"], headers=headers), timeout=30) as response:
                    resumed = bool(offset and response.status == 206)
                    total = int(response.headers.get("Content-Length", "0")) + (
                        offset if resumed else 0
                    )
                    received = offset if resumed else 0
                    if total > maximum:
                        raise RuntimeErrorBase("The tool download exceeds its size limit.")
                    with partial.open("ab" if resumed else "wb") as output:
                        while block := response.read(1024 * 1024):
                            if cancel.is_set():
                                raise RuntimeErrorBase(
                                    "Download canceled; its partial cache is preserved."
                                )
                            received += len(block)
                            if received > maximum:
                                raise RuntimeErrorBase("The tool download exceeded its size limit.")
                            output.write(block)
                            report(
                                f"Downloading {name}: "
                                f"{received // 1024**2} / {total // 1024**2} MiB"
                            )
                        output.flush()
                        os.fsync(output.fileno())
                self.install_verified(partial, destination, entry)
                report(f"Verified {name} {entry['version']}")
                return destination
            except OSError as error:
                raise RuntimeErrorBase(
                    f"Cannot download {name}. Check connectivity and retry; "
                    "cached lessons remain available."
                ) from error
