"""A guided mission can become independent without losing earlier work or evidence."""

import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from dockyard.process import run
from dockyard.service import Service
from dockyard.workspace import write_files

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real Docker"),
]


def test_guided_mission_can_be_independently_retaken(tmp_path):
    service = Service(tmp_path)
    unit_id = "m01-mission"
    unit = service.catalog.get(unit_id)

    def solve():
        lab = service.store.lab(unit_id)
        write_files(Path(lab.workspace), unit.reference, overwrite=True)
        result = run(
            ["/bin/sh", "run.sh"], cwd=Path(lab.workspace), env=service.environment(lab), timeout=60
        )
        assert result.ok, result.stderr
        # docker run returns before Python binds its listener, especially on native Linux.
        deadline = time.monotonic() + 10
        while True:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{lab.resources['port']}/healthz", timeout=1
                ) as response:
                    assert response.status == 200
                break
            except (OSError, urllib.error.URLError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
        return service.perform(unit_id, "check")

    try:
        service.perform(unit_id, "prepare")
        service.store.mark(unit_id, "hints", unit.revision)
        service.store.mark(unit_id, "reference", unit.revision)
        first = solve()
        assert first["status"] == "pass" and not first["independent"]
        assert first["attempt"] == 1
        workspace = Path(service.store.lab(unit_id).workspace)
        (workspace / "my-observation.txt").write_text("Keep my original evidence.")
        restarted = service.perform(unit_id, "retake")
        assert (Path(restarted["backup"]) / "my-observation.txt").is_file()
        assert not (workspace / "my-observation.txt").exists()
        assert service.store.progress()[unit_id]["hints"] == 0
        assert service.perform(unit_id, "check")["status"] == "fail"
        second = solve()
        assert second["status"] == "pass" and second["independent"]
        assert second["attempt"] == 2
        assert service.store.progress()[unit_id]["demonstrated"]
        history = service.store.attempts(unit_id)
        old = next(item for item in history if item.id == first["id"])
        assert old.reference_revealed and old.hints_used == 1 and not old.independent
        assert len(service.store.checkpoints()) == 2
    finally:
        service.perform(unit_id, "clean")
