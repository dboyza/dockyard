import json
from zipfile import ZipFile

from dockyard.catalog import Catalog
from dockyard.models import Assessment, CheckStatus, Lab, Runtime
from dockyard.portfolio import checkpoint
from dockyard.workspace import snapshot, write_files


def test_checkpoint_preserves_source_and_evidence_without_credentials_or_runtime_data(tmp_path):
    workspace = tmp_path / "workspace"
    write_files(
        workspace,
        {
            "Dockerfile": "FROM example\n",
            ".env": "PASSWORD=private-value\n",
            "unsafe.yaml": "password: private-value\n",
            "secret.yaml": "kind: Secret\n",
            "RUNBOOK.md": "A useful handoff.\n",
            "backup.sql": "Private application data",
        },
    )
    lab = Lab(
        id="owned",
        unit_id="m01-mission",
        revision=1,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(workspace),
        created_at="2026-09-26T00:00:00+00:00",
        updated_at="2026-09-26T00:00:00+00:00",
        resources={"db_password": "private-value"},
    )
    assessment = Assessment(
        id="attempt",
        unit_id=lab.unit_id,
        revision=1,
        lab_id=lab.id,
        status=CheckStatus.PASS,
        started_at=lab.created_at,
        finished_at=lab.updated_at,
        file_digest=snapshot(workspace)[0],
        evidence=[],
        independent=True,
    )
    saved = checkpoint(
        tmp_path, lab, Catalog().get(lab.unit_id), assessment, "Do not leak private-value."
    )
    with ZipFile(tmp_path / "checkpoints" / saved["archive"]) as archive:
        assert archive.read("source/Dockerfile") == b"FROM example\n"
        assert archive.read("source/RUNBOOK.md") == b"A useful handoff.\n"
        assert b"private-value" not in archive.read("observations.md")
        manifest = json.loads(archive.read("manifest.json"))
        assert set(manifest["excluded"]) == {".env", "unsafe.yaml", "secret.yaml", "backup.sql"}
        assert manifest["independent"] is True
        assert saved["file_count"] == 2
    (workspace / "Dockerfile").write_text("Changed afterward\n")
    with ZipFile(tmp_path / "checkpoints" / saved["archive"]) as archive:
        assert archive.read("source/Dockerfile") == b"FROM example\n"
