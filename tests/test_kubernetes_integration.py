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
        network = service.docker(lab).inspect("network", lab.resources["kind_network"])
        assert network["Labels"]["io.dockyard.lab"] == lab.id
        network_id = network["Id"]
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
        # Behaviorally equivalent manifests must pass, not just the authored YAML.
        runtime = service.runtime(lab)
        alternative = run(
            [
                "kubectl",
                "patch",
                "deployment",
                "dispatch",
                "--type=strategic",
                "-p",
                '{"spec":{"template":{"metadata":{"labels":{"tier":"api"}},'
                '"spec":{"containers":[{"name":"api","ports":[{"containerPort":8080,'
                '"name":"http"}]}]}}}}',
            ],
            env=service.environment(lab),
            timeout=30,
        )
        assert alternative.ok, alternative.stderr
        alternative = run(
            [
                "kubectl",
                "patch",
                "service",
                "dispatch",
                "--type=merge",
                "-p",
                '{"spec":{"selector":{"app":"dispatch","tier":"api"},'
                '"ports":[{"port":8080,"targetPort":"http"}]}}',
            ],
            env=service.environment(lab),
            timeout=30,
        )
        assert alternative.ok, alternative.stderr
        ready = run(
            ["kubectl", "rollout", "status", "deployment/dispatch", "--timeout=60s"],
            env=service.environment(lab),
            timeout=70,
        )
        assert ready.ok, ready.stderr
        deadline = time.monotonic() + 30
        while True:
            assessment = service.perform(unit_id, "check")
            if assessment["status"] != "stale" or time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        assert assessment["status"] == "pass", assessment
        # An edit outside the default namespace must invalidate captured evidence.
        created = run(
            ["kubectl", "create", "namespace", "preview"], env=service.environment(lab), timeout=30
        )
        assert created.ok, created.stderr
        before = runtime.fingerprint()
        changed = run(
            [
                "kubectl",
                "create",
                "configmap",
                "fingerprint-proof",
                "-n",
                "preview",
                "--from-literal=mode=changed",
            ],
            env=service.environment(lab),
            timeout=30,
        )
        assert changed.ok, changed.stderr
        assert runtime.fingerprint() != before
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
    assert service.docker(lab).inspect("network", network_id) is None
