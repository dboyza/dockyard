import multiprocessing

import pytest

from dockyard.locking import operation_lock
from dockyard.store import BusyError, Store


def hold_lock(directory, started):
    with operation_lock(directory, "test-unit"):
        started.set()
        started.wait(60)
        # Block independently of the event, until the parent terminates the process.
        multiprocessing.Event().wait(60)


def test_process_death_releases_operation_ownership(tmp_path):
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    process = context.Process(target=hold_lock, args=(tmp_path, started))
    process.start()
    try:
        assert started.wait(10)
        with pytest.raises(BusyError), operation_lock(tmp_path, "test-unit"):
            pass
    finally:
        process.terminate()
        process.join(10)
    with operation_lock(tmp_path, "test-unit"):
        store = Store(tmp_path / "profile")
        operation = store.begin_operation("owned-lab", "prepare")
        store.recover_operations("owned-lab")
        assert store.operations()[0]["id"] == operation
        assert store.operations()[0]["state"] == "failed"
        store.begin_operation("owned-lab", "prepare")
