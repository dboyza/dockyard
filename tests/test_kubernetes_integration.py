"""Exercise cluster lifecycle and guard the private kubeconfig boundary."""

import os
import time
from pathlib import Path

import pytest
import yaml

from dockyard.process import run
from dockyard.service import LabError, Service
from dockyard.workspace import write_files

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real Kubernetes"
    ),
]


def test_cluster_pause_resume_and_changed_credentials_are_guarded(tmp_path):
    service = Service(tmp_path)
    unit_id = "m07-reconciliation"
    try:
        service.perform(unit_id, "prepare")
        lab = service.store.lab(unit_id)
        assert lab is not None
        kubeconfig = Path(service.environment(lab)["KUBECONFIG"])
        original = kubeconfig.read_bytes()
        write_files(Path(lab.workspace), service.catalog.get(unit_id).reference, overwrite=True)
        result = run(
            ["/bin/sh", "run.sh"],
            cwd=Path(lab.workspace),
            env=service.environment(lab),
            timeout=150,
        )
        assert result.ok, result.stderr
        assert service.perform(unit_id, "check")["status"] == "pass"
        service.perform(unit_id, "stop")
        assert service.perform(unit_id, "check")["status"] == "blocked"
        service.perform(unit_id, "resume")
        deadline = time.monotonic() + 45
        while True:
            assessment = service.perform(unit_id, "check")
            if assessment["status"] == "pass" or time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        assert assessment["status"] == "pass", assessment
        modified = yaml.safe_load(original)
        modified["users"][0]["user"]["exec"] = {"command": "/usr/bin/false"}
        kubeconfig.write_text(yaml.safe_dump(modified))
        with pytest.raises(LabError, match="authentication boundary"):
            service.perform(unit_id, "check")
        kubeconfig.write_bytes(original)
    finally:
        service.perform(unit_id, "clean")
