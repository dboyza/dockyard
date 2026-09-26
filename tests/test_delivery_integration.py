"""Git and registry state must survive pause, preserve ports, and clean by identity."""

import json
import os
import time
from pathlib import Path

import pytest

from dockyard.process import run
from dockyard.service import Service
from dockyard.workspace import write_files

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real delivery"
    ),
]


def test_delivery_services_resume_with_the_same_commit_and_endpoints(tmp_path):
    service = Service(tmp_path)
    unit = "m16-gitops"
    inventory = []
    lab = None
    try:
        service.perform(unit, "prepare")
        lab = service.store.lab(unit)
        assert lab is not None
        workspace = Path(lab.workspace)
        write_files(workspace, service.catalog.get(unit).reference, overwrite=True)
        outcome = run(
            ["/bin/sh", "run.sh"], cwd=workspace, env=service.environment(lab), timeout=300
        )
        assert outcome.ok, outcome.stdout + outcome.stderr
        deadline = time.monotonic() + 30
        while True:
            assessment = service.perform(unit, "check")
            if assessment["status"] == "pass" or time.monotonic() > deadline:
                break
        assert assessment["status"] == "pass", json.dumps(assessment, indent=2)
        endpoints = {key: lab.resources[key] for key in ("git_url", "git_cluster_url", "registry")}
        inventory = service.docker(lab).discover()
        containers = [item for item in inventory if item["kind"] == "container"]
        assert len(containers) == 2
        service.perform(unit, "stop")
        for item in containers:
            assert not service.docker(lab).verify(item)["State"]["Running"]
        service.perform(unit, "resume")
        current = service.store.lab(unit)
        assert {key: current.resources[key] for key in endpoints} == endpoints
        deadline = time.monotonic() + 90
        while True:
            assessment = service.perform(unit, "check")
            if assessment["status"] == "pass" or time.monotonic() > deadline:
                break
            time.sleep(1)
        assert assessment["status"] == "pass", json.dumps(assessment, indent=2)
        for item in containers:
            assert service.docker(current).verify(item)["State"]["Running"]
    finally:
        service.perform(unit, "clean")
    for item in inventory:
        assert service.docker(lab).inspect(item["kind"], item["id"]) is None
