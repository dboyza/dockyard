"""Shared fixtures for tests that create real practice environments."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from release_profile import release

from dockyard import host


@pytest.fixture
def lab_profile() -> Iterator[Path]:
    """A disposable profile whose labs are cleaned even when the test fails.

    The directory is short enough for native runtime sockets, and it is kept, with
    an error naming it, if any lab resource could not be confirmed removed.
    """
    directory = Path(tempfile.mkdtemp(prefix="dy-", dir=host.temporary_root()))
    yield directory
    release(directory)
