"""Release a disposable test profile without ever orphaning its lab resources.

Every lab this profile created is cleaned through Dockyard's own ownership records.
The profile is deleted only once its runtimes report nothing left; otherwise it is
kept, because its records are the only safe way to find and remove what remains.

Usage: python tests/release_profile.py PROFILE [--keep]
"""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from dockyard.service import Service

ATTEMPTS = 3


def remaining(service: Service) -> list[str]:
    """Describe lab resources that still exist, found only by recorded ownership."""
    found = []
    for lab in service.store.labs():
        try:
            runtime = service.runtime(lab)
            alive = [entry for entry in runtime.discover() if runtime.verify(entry) is not None]
        except Exception as error:  # noqa: BLE001 - any doubt keeps the records
            found.append(f"{lab.unit_id}: could not confirm removal ({error})")
            continue
        found += [
            f"{lab.unit_id}: {entry.get('kind', 'node')} {entry.get('id') or entry.get('name')}"
            for entry in alive
        ]
    return found


def release(directory: Path, *, remove: bool = True) -> None:
    if not (directory / "progress.sqlite3").exists():
        # Nothing was ever recorded here, so nothing can have been created.
        if remove:
            shutil.rmtree(directory, ignore_errors=True)
        return
    service = Service(directory)
    try:
        # A timed attempt left running by a failed test blocks cleanup by design.
        for attempt in service.exams.all():
            if attempt.state in {"active", "grading"}:
                service.exams.invalidate(attempt.id, "Ended by test teardown.")
        failures = []
        for lab in service.store.labs():
            for number in range(ATTEMPTS):
                try:
                    service.perform(lab.unit_id, "clean")
                    break
                except Exception as error:  # noqa: BLE001 - reported below with the profile kept
                    if number == ATTEMPTS - 1:
                        failures.append(f"{lab.unit_id}: {error}")
                    else:
                        time.sleep(2)
        left = remaining(service)
    finally:
        service.shutdown()
    if failures or left:
        details = "\n  ".join(failures + left)
        raise RuntimeError(
            f"Kept the test profile {directory} because lab resources may remain:\n  {details}\n"
            f"Remove them with: dockyard --data-dir {directory} lab clean --all --yes"
        )
    if remove:
        shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or sys.argv[2:] not in ([], ["--keep"]):
        sys.exit(__doc__)
    try:
        release(Path(sys.argv[1]), remove=sys.argv[2:] != ["--keep"])
    except RuntimeError as error:
        sys.exit(str(error))
