"""Measured diagnostics remain explanatory, bounded, and credential-free."""

import json
import threading
from pathlib import Path

import pytest

from dockyard.models import CheckStatus, Command, Criterion, Lab, Runtime
from dockyard.process import ProcessResult
from dockyard.service import Service


@pytest.mark.parametrize(
    "measurements",
    [None, [], "malformed", {"scaling": {"replicas": 4, "credential": "private-lab-password"}}],
)
def test_json_evidence_redacts_measurements_without_changing_the_verdict(tmp_path, measurements):
    service = Service(tmp_path)
    lab = Lab(
        id="owned-lab",
        unit_id="m13-mission",
        revision=1,
        runtime=Runtime.KUBERNETES,
        state="ready",
        workspace=str(tmp_path),
        created_at="now",
        updated_at="now",
        resources={"db_password": "private-lab-password", "port": "12345"},
    )
    command = Command(args=["unused-cached-observation"])
    criterion = Criterion(
        id="capacity-scaling",
        title="Measured scaling",
        explanation="Read actual metrics",
        command=command,
        expectation="json",
        json_path=["scaling"],
        expected="true",
        diagnostic="Inspect the measurements",
    )
    observation = ProcessResult(
        args=tuple(command.args),
        returncode=0,
        stdout=json.dumps({"scaling": True, "_details": measurements}),
        stderr="",
        duration=0.1,
    )
    evidence = service._criterion(
        criterion, lab, threading.Event(), {command.model_dump_json(): observation}
    )
    assert evidence.status == CheckStatus.PASS
    assert evidence.observed == "true"
    assert "private-lab-password" not in evidence.details
    if isinstance(measurements, dict):
        assert '"replicas": 4' in evidence.details
    else:
        assert evidence.details == ""


def test_helm_environment_is_private_and_does_not_inherit_user_options(tmp_path, monkeypatch):
    monkeypatch.setenv("HELM_KUBECONTEXT", "unrelated-context")
    monkeypatch.setenv("HELM_KUBEAPISERVER", "https://unrelated.example")
    monkeypatch.setenv("HELM_PLUGINS", "/unrelated/plugins")
    service = Service(tmp_path)
    lab = Lab(
        id="owned-lab",
        unit_id="m14-helm",
        revision=1,
        runtime=Runtime.KUBERNETES,
        state="ready",
        workspace=str(tmp_path / "workspace"),
        created_at="now",
        updated_at="now",
        resources={
            "port": "12345",
            "registry_port": "12346",
            "db_password": "private",
            "docker_endpoint": "unix:///private/owned.sock",
        },
    )
    env = service.environment(lab)
    assert "HELM_KUBECONTEXT" not in env
    assert "HELM_KUBEAPISERVER" not in env
    for key in ("HELM_CACHE_HOME", "HELM_CONFIG_HOME", "HELM_DATA_HOME", "HELM_PLUGINS"):
        assert Path(env[key]).is_relative_to(tmp_path)
    assert env["HELM_DRIVER"] == "secret"
