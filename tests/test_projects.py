import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from dockyard.models import Assessment, CheckStatus, Lab, Runtime
from dockyard.portfolio import checkpoint
from dockyard.projects import continuation_preview, continue_project, export_portfolio
from dockyard.service import Service
from dockyard.store import timestamp
from dockyard.workspace import snapshot, write_files


def saved_project(root, *, independent=True):
    service = Service(root)
    unit = service.catalog.get("m01-mission")
    workspace = root / "labs/original/workspace"
    write_files(workspace, {**unit.starter, "RUNBOOK.md": "My authored container handoff.\n"})
    now = timestamp()
    lab = Lab(
        id="original",
        unit_id=unit.id,
        revision=unit.revision,
        runtime=Runtime.DOCKER,
        state="absent",
        workspace=str(workspace),
        created_at=now,
        updated_at=now,
    )
    service.store.save_lab(lab)
    evidence = Assessment(
        id="original-check",
        unit_id=unit.id,
        revision=unit.revision,
        lab_id=lab.id,
        status=CheckStatus.PASS,
        started_at=now,
        finished_at=now,
        file_digest=snapshot(workspace)[0],
        evidence=[],
        independent=independent,
    )
    entry = checkpoint(root, lab, unit, evidence, "Original observations.")
    service.store.save_assessment(evidence, entry)
    return service, entry, workspace


def test_selected_continuation_preserves_scaffold_and_old_workspace(tmp_path, monkeypatch):
    service, entry, original = saved_project(tmp_path)
    monkeypatch.setattr(service, "_docker_endpoint", lambda: "unix:///unused-test-endpoint")
    before = snapshot(original)
    preview = continuation_preview(service, entry["id"], "m02-mission")
    assert {f["path"] for f in preview["files"]} == {"app.py", "RUNBOOK.md"}
    result = continue_project(
        service,
        entry["id"],
        "m02-mission",
        preview["checkpoint_digest"],
        preview["target_revision"],
        ["RUNBOOK.md"],
    )
    workspace = Path(result["lab"]["workspace"])
    assert (workspace / "RUNBOOK.md").read_text() == "My authored container handoff.\n"
    assert (workspace / "app.py").read_text() == service.catalog.get("m02-mission").starter[
        "app.py"
    ]
    assert (workspace / "Dockerfile").exists()
    assert snapshot(original) == before
    assert result["lab"]["state"] == "absent"
    assert "m02-mission" not in service.store.progress()
    assert json.loads((workspace.parent / "continuation.json").read_text())["selected"] == [
        "RUNBOOK.md"
    ]
    with pytest.raises(ValueError, match="already has a workspace"):
        continuation_preview(service, entry["id"], "m02-mission")


def test_stale_or_unreviewed_source_does_not_allocate_a_lab(tmp_path, monkeypatch):
    service, entry, _ = saved_project(tmp_path, independent=False)
    monkeypatch.setattr(service, "_docker_endpoint", lambda: "unix:///unused-test-endpoint")
    preview = continuation_preview(service, entry["id"], "m02-mission")
    for digest, revision, names in [
        ("changed", 1, ["RUNBOOK.md"]),
        (preview["checkpoint_digest"], 99, ["RUNBOOK.md"]),
        (preview["checkpoint_digest"], 1, ["../outside"]),
        (preview["checkpoint_digest"], 1, []),
    ]:
        with pytest.raises(ValueError):
            continue_project(service, entry["id"], "m02-mission", digest, revision, names)
        assert service.store.lab("m02-mission") is None
    continue_project(
        service, entry["id"], "m02-mission", preview["checkpoint_digest"], 1, ["RUNBOOK.md"]
    )
    assert service.store.progress()["m02-mission"]["reference"] == 1


def test_readable_portfolio_has_hashes_source_and_provenance(tmp_path):
    service, entry, _ = saved_project(tmp_path)
    with ZipFile(io.BytesIO(export_portfolio(service))) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files.pop("manifest.json"))
    assert manifest["missions"] == 1
    assert manifest["files"] == {
        name: hashlib.sha256(body).hexdigest() for name, body in files.items()
    }
    assert b"independent demonstration" in files["README.md"]
    assert files["missions/m01-mission/source/RUNBOOK.md"] == b"My authored container handoff.\n"
    assert json.loads(files["missions/m01-mission/manifest.json"])["id"] == entry["id"]
    assert "missions/m01-mission/evidence.json" in files
