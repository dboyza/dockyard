"""Return a profile to its first-launch state after cleaning every lab it owns."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dockyard.locking import operation_lock
from dockyard.store import BusyError

if TYPE_CHECKING:
    from dockyard.service import Service

# Learner data. Downloaded tools, VM provider settings, and lock files are kept.
DIRECTORIES = ("labs", "backups", "checkpoints", "imports", "staging")
TABLES = ("progress", "attempts", "notes", "checkpoints", "exams", "labs", "operations")
KEPT_SETTINGS = ("theme",)
ACTIVE = {"running", "queued", "canceling"}


def summary(service: Service) -> dict[str, Any]:
    """Describe what a reset would remove."""
    with service.store.connection() as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
            for table in ("progress", "attempts", "notes", "checkpoints", "exams")
        }
    return {
        "labs": [lab.unit_id for lab in service.store.labs() if lab.state != "absent"],
        "activities": counts["progress"],
        "assessments": counts["attempts"],
        "notes": counts["notes"],
        "checkpoints": counts["checkpoints"],
        "exams": counts["exams"],
    }


def reset_profile(service: Service) -> dict[str, Any]:
    """Clean every owned lab, then erase learning data. Nothing is erased if a clean fails."""
    with operation_lock(service.directory / "locks", "progress-transfer"):
        if any(item["state"] in ACTIVE for item in service.store.operations()):
            raise BusyError("Wait for the running lab operation to finish, then reset.")
        if any(attempt.state in {"active", "grading"} for attempt in service.exams.all()):
            raise BusyError("Finish or abandon the timed exam before resetting.")
        service.resetting.set()
        try:
            cleaned = []
            for lab in service.store.labs():
                if lab.state == "absent":
                    continue
                try:
                    service.perform(lab.unit_id, "clean")
                except Exception as error:
                    raise BusyError(
                        f"Dockyard could not clean up {lab.unit_id}, so nothing was reset. {error}"
                    ) from error
                cleaned.append(lab.unit_id)
            erase_records(service)
            remaining = [
                str(service.directory / name)
                for name in DIRECTORIES
                if not remove(service.directory / name)
            ]
        finally:
            service.resetting.clear()
    return {"cleaned_labs": cleaned, "remaining": remaining}


def erase_records(service: Service) -> None:
    with service.store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for table in TABLES:
            connection.execute(f"DELETE FROM {table}")  # noqa: S608
        placeholders = ",".join("?" for _ in KEPT_SETTINGS)
        connection.execute(
            f"DELETE FROM settings WHERE key NOT IN ({placeholders})",  # noqa: S608
            KEPT_SETTINGS,
        )
    # Deleted rows stay readable in free pages and the write-ahead log until rewritten.
    with service.store.connection() as connection:
        connection.execute("VACUUM")
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def remove(path: Path) -> bool:
    """Delete one profile directory without following links; report whether it is gone."""
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    return not path.exists() and not path.is_symlink()
