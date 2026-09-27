"""Portable progress preserves historical evidence without restoring runtime ownership."""

import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from dockyard.models import Assessment, CheckStatus, ExamAttempt, Lab, Runtime
from dockyard.portfolio import checkpoint
from dockyard.progress_bundle import export_bundle, import_bundle, inspect_bundle, preview_import
from dockyard.service import Service
from dockyard.store import timestamp
from dockyard.workspace import snapshot, write_files


def source_profile(root):
    service = Service(root)
    now = timestamp()
    unit = service.catalog.get("m01-mission")
    workspace = root / "labs/portable/workspace"
    write_files(
        workspace,
        {
            "Dockerfile": "FROM supplied\n",
            "RUNBOOK.md": "My recovery observations.\n",
            ".env": "TOKEN=private-fixture-value\n",
        },
    )
    lab = Lab(
        id="portable",
        unit_id=unit.id,
        revision=unit.revision,
        runtime=Runtime.DOCKER,
        state="stopped",
        workspace=str(workspace),
        created_at=now,
        updated_at=now,
        resources={"db_password": "private-fixture-value"},
    )
    service.store.save_lab(lab)
    service.store.mark(unit.id, "viewed", unit.revision)
    service.store.save_note(unit.id, "Original note with private-fixture-value.")
    evidence = Assessment(
        id="portable-evidence",
        unit_id=unit.id,
        revision=unit.revision,
        lab_id=lab.id,
        status=CheckStatus.PASS,
        started_at=now,
        finished_at=now,
        file_digest=snapshot(workspace)[0],
        evidence=[],
        independent=True,
    )
    saved = checkpoint(root, lab, unit, evidence, service.store.note(unit.id))
    service.store.save_assessment(evidence, saved)
    exam = ExamAttempt(
        id="unfinished-exam",
        exam_id="ckad-release",
        unit_id="exam-ckad-a",
        lab_id="original-cluster",
        revision=1,
        state="active",
        started_at=now,
        deadline=now,
        selected_task=service.catalog.exams["ckad-release"].tasks[0].id,
    )
    with service.store.connection() as connection:
        connection.execute(
            "INSERT INTO exams(id,body) VALUES(?,?)", (exam.id, exam.model_dump_json())
        )
    return service


def test_round_trip_retains_evidence_checkpoints_and_drafts_with_safe_merge(tmp_path):
    original = source_profile(tmp_path / "source")
    body = export_bundle(original)
    records, files = inspect_bundle(original, body)
    assert len(records.attempts) == 1 and len(records.checkpoints) == 1
    assert not any(name.endswith(".env") for name in files)
    assert b"private-fixture-value" not in b"".join(
        value for key, value in files.items() if not key.endswith(".zip")
    )
    restored = Service(tmp_path / "destination")
    restored.store.save_note("m01-mission", "Keep my newer local note.")
    untouched = restored.directory / "labs/local/workspace"
    write_files(untouched, {"Dockerfile": "Never replace my working source.\n"})
    preview = preview_import(restored, body)
    assert preview["preserved_local_notes"] == 1
    receipt = import_bundle(restored, body, preview["digest"])
    assert restored.store.note("m01-mission") == "Keep my newer local note."
    assert (untouched / "Dockerfile").read_text() == "Never replace my working source.\n"
    assert restored.store.progress()["m01-mission"]["demonstrated"] == 1
    assert restored.store.attempts("m01-mission")[0].id == "portable-evidence"
    assert restored.store.labs() == []
    imported = Path(receipt["directory"])
    assert (imported / "drafts/m01-mission/Dockerfile").read_bytes() == b"FROM supplied\n"
    assert "redacted" in (imported / "notes/m01-mission.md").read_text()
    assert Path(receipt["backup"]).is_file()
    assert Path(receipt["backup"]).stat().st_mode & 0o777 == 0o600
    saved = restored.store.checkpoints()[0]
    assert (restored.directory / "checkpoints" / saved["archive"]).is_file()
    exam = restored.exams.get("unfinished-exam")
    assert exam.state == "invalidated" and exam.score is None
    assert import_bundle(restored, body, preview["digest"])["already_imported"] is True
    assert len(restored.store.attempts("m01-mission")) == 1


def rewritten(body, change, *, repair_hashes=False):
    with ZipFile(io.BytesIO(body)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    change(files)
    if repair_hashes:
        manifest = json.loads(files["manifest.json"])
        manifest["files"] = {
            name: hashlib.sha256(value).hexdigest()
            for name, value in files.items()
            if name != "manifest.json"
        }
        files["manifest.json"] = json.dumps(manifest).encode()
    out = io.BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    return out.getvalue()


def test_changed_payload_unknown_members_and_future_revisions_leave_profile_untouched(tmp_path):
    original = source_profile(tmp_path / "source")
    body = export_bundle(original)
    destination = Service(tmp_path / "destination")
    mutations = [
        (lambda files: files.update({"drafts/m01-mission/Dockerfile": b"Changed"}), False),
        (lambda files: files.update({"unrequested-file": b"Unexpected"}), True),
    ]

    def future(files):
        records = json.loads(files["records.json"])
        records["progress"][0]["revision"] = 1000
        files["records.json"] = json.dumps(records).encode()

    mutations.append((future, True))
    for change, repair in mutations:
        invalid = rewritten(body, change, repair_hashes=repair)
        with pytest.raises(ValueError):
            import_bundle(destination, invalid, hashlib.sha256(invalid).hexdigest())
        assert destination.store.progress() == {}
        assert not (destination.directory / "imports").exists()
    with pytest.raises(ValueError, match="changed after"):
        import_bundle(destination, body, "0" * 64)


def test_existing_checkpoint_conflict_is_preserved_before_import(tmp_path):
    source = source_profile(tmp_path / "source")
    body = export_bundle(source)
    destination = Service(tmp_path / "destination")
    entry = source.store.checkpoints()[0]
    target = destination.directory / "checkpoints" / entry["archive"]
    target.parent.mkdir()
    target.write_bytes(b"Do not replace this file.")
    with pytest.raises(ValueError, match="conflicts"):
        import_bundle(destination, body, hashlib.sha256(body).hexdigest())
    assert target.read_bytes() == b"Do not replace this file."
    assert destination.store.progress() == {}


@pytest.mark.parametrize(
    "mutation", ["checkpoint-date", "checkpoint-count", "exam-unit", "exam-task", "exam-evidence"]
)
def test_invalid_provenance_is_rejected_before_any_merge(tmp_path, mutation):
    original = source_profile(tmp_path / "source")
    body = export_bundle(original)

    def change(files):
        records = json.loads(files["records.json"])
        if mutation == "checkpoint-date":
            records["checkpoints"][0]["created_at"] = "not-a-date"
        elif mutation == "checkpoint-count":
            records["checkpoints"][0]["file_count"] += 1
        elif mutation == "exam-unit":
            records["exams"][0]["unit_id"] = "exam-ckad-b"
        elif mutation == "exam-task":
            records["exams"][0]["selected_task"] = "unknown-task"
        else:
            records["exams"][0]["state"] = "finished"
            records["exams"][0]["assessment_id"] = "portable-evidence"
        files["records.json"] = json.dumps(records).encode()

    invalid = rewritten(body, change, repair_hashes=True)
    destination = Service(tmp_path / "destination")
    with pytest.raises(ValueError):
        import_bundle(destination, invalid, hashlib.sha256(invalid).hexdigest())
    assert destination.store.progress() == {}
    assert not (destination.directory / "imports").exists()
