"""Starting fresh erases learning data only after every owned lab is cleaned."""

import pytest

from dockyard.models import Lab, Runtime
from dockyard.profile_reset import reset_profile, summary
from dockyard.service import Service
from dockyard.store import BusyError, timestamp


def profile(tmp_path):
    service = Service(tmp_path)
    workspace = tmp_path / "labs" / "owned" / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "notes.md").write_text("draft")
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "tools" / "bin").mkdir(parents=True)
    (tmp_path / "tools" / "bin" / "kind").write_text("downloaded")
    service.store.save_lab(
        Lab(
            id="owned",
            unit_id="m01-processes",
            revision=1,
            runtime=Runtime.DOCKER,
            state="ready",
            workspace=str(workspace),
            created_at=timestamp(),
            updated_at=timestamp(),
        )
    )
    service.store.mark("m01-processes", "viewed", 1)
    service.store.save_note("m01-processes", "private diagnosis")
    service.store.set_setting("theme", "light")
    service.store.set_setting("last_unit", "m01-processes")
    return service


def test_reset_cleans_labs_then_erases_learning_data_but_keeps_theme_and_tools(
    tmp_path, monkeypatch
):
    service = profile(tmp_path)
    cleaned = []
    monkeypatch.setattr(service, "perform", lambda unit, action: cleaned.append((unit, action)))
    assert summary(service)["labs"] == ["m01-processes"]
    assert summary(service)["notes"] == 1

    result = reset_profile(service)

    assert cleaned == [("m01-processes", "clean")]
    assert result == {"cleaned_labs": ["m01-processes"], "remaining": []}
    assert service.store.progress() == {}
    assert service.store.labs() == []
    assert service.store.note("m01-processes") == ""
    assert service.store.setting("last_unit") is None
    assert service.store.setting("theme") == "light"
    assert not (tmp_path / "labs").exists() and not (tmp_path / "checkpoints").exists()
    assert (tmp_path / "tools" / "bin" / "kind").read_text() == "downloaded"
    assert b"private diagnosis" not in (tmp_path / "progress.sqlite3").read_bytes()


def test_a_failed_clean_erases_nothing(tmp_path, monkeypatch):
    service = profile(tmp_path)

    def refuse(unit, action):
        raise RuntimeError("The cluster was changed outside Dockyard.")

    monkeypatch.setattr(service, "perform", refuse)
    with pytest.raises(BusyError, match="nothing was reset"):
        reset_profile(service)
    assert service.store.note("m01-processes") == "private diagnosis"
    assert (tmp_path / "labs" / "owned" / "workspace" / "notes.md").exists()
    assert not service.resetting.is_set()


def test_reset_waits_for_running_operations(tmp_path):
    service = profile(tmp_path)
    service.store.begin_operation("owned", "prepare")
    with pytest.raises(BusyError, match="running lab operation"):
        reset_profile(service)
    assert service.store.note("m01-processes") == "private diagnosis"


def test_new_lab_work_waits_while_resetting(tmp_path):
    service = Service(tmp_path)
    service.resetting.set()
    with pytest.raises(BusyError, match="resetting"):
        service.perform("m01-processes", "prepare")
    with pytest.raises(BusyError, match="resetting"):
        service.exams.start("ckad-release")
