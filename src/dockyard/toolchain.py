"""Pinned, verified private tools; downloads never modify host package managers."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import threading
from collections.abc import Callable
from pathlib import Path
from urllib.request import Request, urlopen

from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.runtimes.docker import RuntimeErrorBase

MANIFEST = json.loads((CONTENT / "toolchain.json").read_text())


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


class Toolchain:
    def __init__(self, root: Path):
        self.root = root

    def ready(self, name: str) -> bool:
        entry = MANIFEST[name]
        destination: Path = self.root / str(entry["path"])
        return (
            destination.is_file()
            and not destination.is_symlink()
            and digest(destination) == entry["sha256"]
        )

    def ensure(self, name: str, cancel: threading.Event, report: Callable[[str], None]) -> Path:
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise RuntimeErrorBase("This toolchain is validated for Apple Silicon macOS.")
        entry = MANIFEST[name]
        destination: Path = self.root / str(entry["path"])
        with operation_lock(self.root / "locks", "tool-" + name):
            if self.ready(name):
                return destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            partial = destination.with_suffix(destination.suffix + ".part")
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
                    if total > 512 * 1024 * 1024:
                        raise RuntimeErrorBase("The tool download exceeds its size limit.")
                    with partial.open("ab" if resumed else "wb") as output:
                        while block := response.read(1024 * 1024):
                            if cancel.is_set():
                                raise RuntimeErrorBase(
                                    "Download canceled; its partial cache is preserved."
                                )
                            received += len(block)
                            if received > 512 * 1024 * 1024:
                                raise RuntimeErrorBase("The tool download exceeded its size limit.")
                            output.write(block)
                            report(
                                f"Downloading {name}: "
                                f"{received // 1024**2} / {total // 1024**2} MiB"
                            )
                        output.flush()
                        os.fsync(output.fileno())
                if digest(partial) != entry["sha256"]:
                    partial.unlink()
                    raise RuntimeErrorBase(
                        f"{name} failed its pinned integrity check; nothing was installed."
                    )
                partial.chmod(0o755 if entry["path"].startswith("bin/") else 0o600)
                os.replace(partial, destination)
                report(f"Verified {name} {entry['version']}")
                return destination
            except OSError as error:
                raise RuntimeErrorBase(
                    f"Cannot download {name}. Check connectivity and retry; "
                    "cached lessons remain available."
                ) from error
