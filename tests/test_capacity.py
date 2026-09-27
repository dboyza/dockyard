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
