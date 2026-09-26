"""Pinned vulnerability data and local-only scan defaults, without telemetry."""

from __future__ import annotations

import json
import os
import shutil
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from dockyard.catalog import CONTENT
from dockyard.locking import operation_lock
from dockyard.process import run
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain, digest
from dockyard.workspace import atomic_write

if TYPE_CHECKING:
    from dockyard.runtimes.kubernetes import KubernetesRuntime

SCANNER = json.loads((CONTENT / "scanner.json").read_text())


def ready(cache: Path) -> bool:
    directory = cache / "db"
    database = directory / "trivy.db"
    metadata = directory / "metadata.json"
    if any(path.is_symlink() for path in (cache, directory, database, metadata)):
        raise RuntimeErrorBase("The scanner cache contains a symbolic link; preserved.")
    if not database.is_file() or not metadata.is_file() or metadata.stat().st_size > 65536:
        return False
    try:
        record = json.loads(metadata.read_text())
        return bool(
            record["Version"] == SCANNER["database"]["schema"]
            and record["UpdatedAt"] == SCANNER["database"]["updated_at"]
            and digest(database) == SCANNER["database"]["sha256"]
        )
    except (ValueError, KeyError, OSError):
        return False


def install(runtime: KubernetesRuntime, cancel: threading.Event) -> None:
    def report(message: str) -> None:
        runtime.lab.resources["stage"] = message
        runtime.save(runtime.lab)

    tools = Toolchain(runtime.tools)
    scanner = tools.ensure("trivy", cancel, report)
    cache = runtime.tools / "trivy"
    with operation_lock(runtime.tools / "locks", "scanner-database"):
        report("Verifying the pinned vulnerability database")
        if not ready(cache):
            report("Downloading the pinned vulnerability database")
            temporary = runtime.tools / ("trivy-preparing-" + uuid.uuid4().hex)
            temporary.mkdir(mode=0o700)
            try:
                outcome = run(
                    [
                        str(scanner),
                        "image",
                        "--disable-telemetry",
                        "--skip-version-check",
                        "--cache-dir",
                        str(temporary),
                        "--db-repository",
                        SCANNER["database"]["repository"],
                        "--download-db-only",
                        "--skip-db-update=false",
                    ],
                    env=runtime.env,
                    timeout=600,
                    cancel=cancel,
                )
                runtime.docker.require(outcome)
                if not ready(temporary):
                    raise RuntimeErrorBase(
                        "The scanner database failed its pinned integrity check."
                    )
                (cache / "db").mkdir(parents=True, exist_ok=True)
                os.replace(temporary / "db/trivy.db", cache / "db/trivy.db")
                atomic_write(
                    cache / "db/metadata.json", (temporary / "db/metadata.json").read_bytes()
                )
            finally:
                shutil.rmtree(temporary)
    fixture = tools.ensure(SCANNER["fixture"]["toolchain_key"], cancel, report)
    directory = Path(runtime.env["DOCKYARD_STORAGE"]) / "packages"
    if any(p.is_symlink() for p in (directory.parent, directory, directory / fixture.name)):
        raise RuntimeErrorBase("The private fixture path is a symbolic link; preserved.")
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.resolve().is_relative_to(runtime.root.resolve()):
        raise RuntimeErrorBase("The private fixture path is a symbolic link; preserved.")
    atomic_write(directory / fixture.name, fixture.read_bytes())
    runtime.lab.resources["scanner_database_updated_at"] = SCANNER["database"]["updated_at"]
    runtime.save(runtime.lab)
