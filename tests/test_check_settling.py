"""A check observes again while the runtime settles, instead of reporting stale at once."""

import threading

from dockyard import service as service_module
from dockyard.models import CheckStatus, Command, Criterion, Lab, Runtime
from dockyard.process import ProcessResult
from dockyard.service import Service
from dockyard.store import timestamp


class ChangingRuntime:
    """A runtime whose fingerprint changes a set number of times, then holds still."""

    def __init__(self, changes: int):
        self.changes = changes
        self.reads = 0

    def fingerprint(self) -> str:
        self.reads += 1
        return str(min(self.reads // 2, self.changes))

    def discover(self) -> list:
        return []


def checked(tmp_path, monkeypatch, runtime):
    service = Service(tmp_path)
    unit = service.catalog.get("m00-first-container")
    criterion = Criterion(
        id="observed",
        title="Observed",
        explanation="Observes the lab.",
        command=Command(args=["observe"]),
        expected="ok",
        diagnostic="Look again.",
    )
    service.catalog.units[unit.id] = unit.model_copy(update={"checks": [criterion]})
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    lab = Lab(
        id="settling",
        unit_id=unit.id,
        revision=unit.revision,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(workspace),
        created_at=timestamp(),
        updated_at=timestamp(),
        resources={"port": "1", "docker_endpoint": "unix:///unused"},
    )
    service.store.save_lab(lab)
    monkeypatch.setattr(
        service_module, "run", lambda args, **_: ProcessResult(tuple(args), 0, "ok", "", 0)
    )
    monkeypatch.setattr(service_module.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(service, "runtime", lambda lab: runtime)
    return service._check(lab, threading.Event())


def test_a_runtime_that_settles_during_the_check_passes(tmp_path, monkeypatch):
    runtime = ChangingRuntime(changes=2)
    assert checked(tmp_path, monkeypatch, runtime).status == CheckStatus.PASS
    assert runtime.reads > 4


def test_a_runtime_that_never_settles_is_still_reported_stale(tmp_path, monkeypatch):
    class Restless(ChangingRuntime):
        def fingerprint(self) -> str:
            self.reads += 1
            return str(self.reads)

    clock = iter(range(0, 1000, 10))
    monkeypatch.setattr(service_module.time, "monotonic", lambda: next(clock))
    assert checked(tmp_path, monkeypatch, Restless(0)).status == CheckStatus.STALE
