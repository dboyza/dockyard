"""Process-scoped operation ownership that the OS releases after a crash."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dockyard.store import BusyError


@contextmanager
def operation_lock(directory: Path, unit_id: str) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"{unit_id}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise BusyError("This lab already has an operation in progress.") from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
