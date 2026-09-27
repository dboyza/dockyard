"""A per-user host lease prevents independent profiles from starting competing clusters."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dockyard.locking import operation_lock
from dockyard.models import Lab, Runtime
from dockyard.process import run
from dockyard.store import BusyError
from dockyard.workspace import atomic_write

if TYPE_CHECKING:
    from dockyard.service import Service


def registry_directory() -> Path:
    return Path("/private/tmp") / f"dockyard-capacity-{os.getuid()}"


def registry() -> Path:
    root = registry_directory()
    root.mkdir(mode=0o700, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("The host capacity registry is not a private owned directory; preserved.")
    return root


def host_readiness(directory: Path) -> dict[str, Any]:
    pressure = run(["/usr/bin/memory_pressure", "-Q"], timeout=5)
    available = re.search(r"memory free percentage:\s*(\d+)%", pressure.stdout)
    total = re.search(r"The system has (\d+)", pressure.stdout)
    return {
        "architecture": platform.machine(),
        "system": platform.system(),
        "host_memory_gib": round(int(total[1]) / 1024**3, 1) if total else None,
        "memory_free_percent": int(available[1]) if available else None,
        "free_disk_gib": round(shutil.disk_usage(directory).free / 1024**3, 1),
        "cluster_policy": "One active application cluster or native VM lab "
        "across Dockyard profiles.",
        "vm_budget_gib": 8,
        "cache_soft_budget_gib": 40,
    }


def preflight(service: Service, lab: Lab) -> None:
    unit = service.catalog.get(lab.unit_id)
    observed = host_readiness(service.directory)
    if observed["system"] != "Darwin" or observed["architecture"] != "arm64":
        raise ValueError("This release is validated for Apple Silicon macOS.")
    needed_disk = (
        20 if lab.runtime == Runtime.LINUX else 10 if lab.runtime == Runtime.KUBERNETES else 2
    )
    if observed["free_disk_gib"] < needed_disk:
        raise ValueError(f"Free at least {needed_disk} GiB of disk before preparing this lab.")
    if observed["memory_free_percent"] is not None and observed["memory_free_percent"] < 8:
        raise ValueError(
            "The host reports severe memory pressure. Stop an unused workload before retrying."
        )
    needed_memory = (
        unit.nodes * (2 if unit.nodes >= 3 else 3) if lab.runtime == Runtime.LINUX else 4
    )
    if observed["host_memory_gib"] is not None and observed["host_memory_gib"] < needed_memory + 4:
        raise ValueError(f"This lab needs {needed_memory} GiB plus 4 GiB of host headroom.")


def contenders(service: Service, root: Path) -> list[dict[str, str]]:
    active = []
    for path in root.glob("*.json"):
        if path.is_symlink() or path.stat().st_size > 4096:
            raise ValueError("The host capacity registry contains an invalid entry; preserved.")
        record = json.loads(path.read_text())
        profile = Path(record["profile"])
        if profile == service.directory:
            continue
        if not profile.exists():
            # An absent profile cannot be operated by this app; retain its record for diagnostics.
            continue
        database = profile / "progress.sqlite3"
        if profile.is_symlink() or database.is_symlink() or not database.is_file():
            raise ValueError(
                "A registered profile has moved or changed; "
                "inspect it before starting another cluster."
            )
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT body FROM labs WHERE unit_id=?", (record["unit_id"],)
            ).fetchone()
        lab = Lab.model_validate_json(row[0]) if row else None
        if lab is None or lab.id != record["lab_id"] or lab.state in {"absent", "stopped"}:
            continue
        active.append({"profile": str(profile), "unit_id": lab.unit_id, "state": lab.state})
    return active


@contextmanager
def cluster_lease(service: Service, lab: Lab) -> Iterator[None]:
    if lab.runtime not in {Runtime.KUBERNETES, Runtime.LINUX}:
        yield
        return
    root = registry()
    with operation_lock(root, "cluster-capacity"):
        occupied = contenders(service, root)
        if occupied:
            first = occupied[0]
            raise BusyError(
                f"Another Dockyard profile holds the cluster budget: {first['unit_id']} "
                f"({first['state']}) in {first['profile']}. Stop or clean that lab first."
            )
        identity = hashlib.sha256((str(service.directory) + "\0" + lab.id).encode()).hexdigest()
        atomic_write(
            root / (identity + ".json"),
            json.dumps(
                {
                    "profile": str(service.directory),
                    "unit_id": lab.unit_id,
                    "lab_id": lab.id,
                }
            ).encode(),
        )
        yield
