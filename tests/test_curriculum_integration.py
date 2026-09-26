"""Authoring gate: fail the intended starter, run the reference, observe actual behavior."""

import os
import time
from pathlib import Path

import pytest

from dockyard.catalog import Catalog
from dockyard.process import run
from dockyard.service import Service
from dockyard.workspace import write_files

UNITS = list(Catalog().units)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real runtimes"
    ),
]


@pytest.mark.parametrize("unit_id", UNITS, ids=UNITS)
def test_authored_reference_repairs_its_actual_starter(tmp_path, unit_id):
    service = Service(tmp_path)
    unit = service.catalog.get(unit_id)
    try:
        service.perform(unit_id, "prepare")
        deadline = time.monotonic() + 30
        while True:
            starter = service.perform(unit_id, "check")
            if starter["status"] != "stale" or time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        assert starter["status"] == "fail", starter
        for criterion_id in unit.starter_failure_checks:
            observation = next(
                item for item in starter["evidence"] if item["criterion"] == criterion_id
            )
            assert observation["status"] == "fail", observation
            assert observation["observed"].strip() == "false", observation
        lab = service.store.lab(unit_id)
        assert lab is not None
        workspace = Path(lab.workspace)
        write_files(workspace, unit.reference, overwrite=True)
        solution = run(
            ["/bin/sh", "run.sh"], cwd=workspace, env=service.environment(lab), timeout=600
        )
        assert solution.ok, solution.stdout + solution.stderr
        deadline = time.monotonic() + 30
        while True:
            observed = service.perform(unit_id, "check")
            if observed["status"] == "pass" or time.monotonic() > deadline:
                break
            time.sleep(0.25)
        assert observed["status"] == "pass", observed
        assert observed["independent"] == (unit.kind != "lesson")
        assert service.store.progress()[unit_id]["practiced"] == 1
    finally:
        service.perform(unit_id, "clean")
