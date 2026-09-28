import threading

import pytest

from dockyard.capacity import cluster_lease
from dockyard.models import Lab, Runtime
from dockyard.service import LabError, Service
from dockyard.store import BusyError, timestamp


def lab(service, identity, unit="m07-declarative", state="ready"):
    now = timestamp()
    result = Lab(
        id=identity,
        unit_id=unit,
        revision=1,
        runtime=Runtime.KUBERNETES,
        state=state,
        workspace=str(service.directory / identity / "workspace"),
        created_at=now,
        updated_at=now,
    )
    service.store.save_lab(result)
    return result


def test_host_budget_is_exclusive_across_profiles_until_recorded_lab_stops(tmp_path, monkeypatch):
    monkeypatch.setattr("dockyard.capacity.registry_directory", lambda: tmp_path / "registry")
    first, second = Service(tmp_path / "first"), Service(tmp_path / "second")
    active, waiting = lab(first, "one"), lab(second, "two", state="absent")
    with cluster_lease(first, active):
        with pytest.raises(BusyError):
            with cluster_lease(second, waiting):
                pytest.fail("A simultaneous second cluster acquired the host lock")
    with pytest.raises(BusyError, match="Another Dockyard profile"):
        with cluster_lease(second, waiting):
            pytest.fail("A running cluster lost its lease after preparation completed")
    active.state = "stopped"
    first.store.save_lab(active)
    with cluster_lease(second, waiting):
        waiting.state = "ready"
        second.store.save_lab(waiting)
    with pytest.raises(BusyError, match="Another Dockyard profile"):
        with cluster_lease(first, active):
            pytest.fail("Resume bypassed the active cluster budget")
    assert first.store.lab(active.unit_id).state == "stopped"


def test_switching_within_a_profile_stops_only_ready_owned_cluster(tmp_path, monkeypatch):
    service = Service(tmp_path)
    previous = lab(service, "old")
    target = lab(service, "new", unit="m08-probes", state="absent")
    calls = []

    class RecordedRuntime:
        def change(self, action, cancel):
            calls.append(action)

    monkeypatch.setattr(service, "runtime", lambda record: RecordedRuntime())
    service._make_cluster_room(target, threading.Event())
    assert calls == ["stop"]
    assert service.store.lab(previous.unit_id).state == "stopped"
    previous.state = "failed"
    service.store.save_lab(previous)
    with pytest.raises(LabError, match="Inspect and stop or clean"):
        service._make_cluster_room(target, threading.Event())
    assert calls == ["stop"]


def test_exhausted_address_pools_reclaim_only_the_oldest_stopped_lab(tmp_path, monkeypatch):
    service = Service(tmp_path)
    oldest = lab(service, "oldest", unit="m07-inspection", state="stopped")
    newer = lab(service, "newer", unit="m07-mission", state="stopped")
    running = lab(service, "running", unit="m08-jobs", state="ready")
    target = lab(service, "target", unit="m09-secrets", state="absent")
    newer.updated_at = "9999-01-01T00:00:00+00:00"
    service.store.save_lab(newer)
    attempts, cleaned = [], []

    def prepare(record, cancel):
        attempts.append(record.unit_id)
        if len(attempts) == 1:
            raise LabError(
                "Error response from daemon: all predefined address pools have been fully subnetted"
            )

    class RecordedRuntime:
        def __init__(self, record):
            self.record = record

        def change(self, action, cancel):
            cleaned.append((self.record.unit_id, action))

    monkeypatch.setattr(service, "_prepare", prepare)
    monkeypatch.setattr(service, "runtime", RecordedRuntime)
    service._prepare_reclaiming(target, threading.Event())
    assert attempts == ["m09-secrets", "m09-secrets"]
    assert cleaned == [("m07-inspection", "clean")]
    reclaimed = service.store.lab(oldest.unit_id)
    assert reclaimed.state == "absent"
    assert "Your files and progress are kept" in reclaimed.error
    assert service.store.lab(newer.unit_id).state == "stopped"
    assert service.store.lab(running.unit_id).state == "ready"


def test_exhausted_address_pools_without_stopped_labs_explain_the_fix(tmp_path, monkeypatch):
    service = Service(tmp_path)
    lab(service, "running", unit="m08-jobs", state="ready")
    target = lab(service, "target", unit="m09-secrets", state="absent")

    def prepare(record, cancel):
        raise LabError("all predefined address pools have been fully subnetted")

    monkeypatch.setattr(service, "_prepare", prepare)
    with pytest.raises(LabError, match="no free network address ranges"):
        service._prepare_reclaiming(target, threading.Event())


def test_other_preparation_errors_are_not_retried(tmp_path, monkeypatch):
    service = Service(tmp_path)
    lab(service, "old", unit="m07-inspection", state="stopped")
    target = lab(service, "target", unit="m09-secrets", state="absent")
    attempts = []

    def prepare(record, cancel):
        attempts.append(record.unit_id)
        raise LabError("image pull failed")

    monkeypatch.setattr(service, "_prepare", prepare)
    with pytest.raises(LabError, match="image pull failed"):
        service._prepare_reclaiming(target, threading.Event())
    assert attempts == ["m09-secrets"]
