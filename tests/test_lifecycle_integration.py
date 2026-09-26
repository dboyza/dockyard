"""Real Docker journey, including the stopped-lab regression observed in the UI."""

import os
import time
from pathlib import Path

import pytest

from dockyard.process import run
from dockyard.service import Service

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real Docker"),
]


def test_stop_check_resume_and_reset_preserve_learner_work(tmp_path):
    service = Service(tmp_path)
    unit = "m01-processes"
    service.perform(unit, "prepare")
    lab = service.store.lab(unit)
    assert lab is not None
    workspace = Path(lab.workspace)
    try:
        # Empty environment is an actual learner failure, not an infrastructure blocker.
        assert service.perform(unit, "check")["status"] == "fail"
        reference = service.catalog.get(unit).reference["run.sh"]
        started = run(
            ["/bin/sh"], input_text=reference, cwd=workspace, env=service.environment(lab)
        )
        assert started.ok, started.stderr
        deadline = time.monotonic() + 20
        while True:
            result = service.perform(unit, "check")
            if result["status"] == "pass" or time.monotonic() > deadline:
                break
            time.sleep(0.2)
        assert result["status"] == "pass", result
        service.perform(unit, "stop")
        stopped = service.perform(unit, "check")
        assert stopped["status"] == "blocked"
        assert service.store.lab(unit).state == "stopped"
        service.perform(unit, "resume")
        assert service.store.lab(unit).state == "ready"
        # Reset preserves a complete draft and removes only the owned container.
        (workspace / "observations.txt").write_text("My own diagnosis\n")
        reset = service.perform(unit, "reset")
        assert (Path(reset["backup"]) / "observations.txt").read_text() == "My own diagnosis\n"
        assert not (workspace / "observations.txt").exists()
        assert service.perform(unit, "check")["status"] == "fail"
        assert len(service.store.attempts(unit)) >= 4
    finally:
        service.perform(unit, "clean")


def test_inventory_tracks_multiple_resources_and_preserves_unrelated_identity(tmp_path):
    service = Service(tmp_path)
    unit = "m01-processes"
    service.perform(unit, "prepare")
    lab = service.store.lab(unit)
    assert lab is not None
    runtime = service.docker(lab)
    env = service.environment(lab)
    name = env["DOCKYARD_CONTAINER"]
    network = env["DOCKYARD_NETWORK"]
    volume = env["DOCKYARD_VOLUME"]
    outsider = name + "-unlabeled"
    label = f"io.dockyard.lab={lab.id}"
    outsider_id = None
    try:
        for args in (
            ["network", "create", "--label", label, network],
            ["volume", "create", "--label", label, volume],
            [
                "run",
                "-d",
                "--name",
                name,
                "--label",
                label,
                "--network",
                network,
                "-v",
                f"{volume}:/data",
                env["DOCKYARD_PYTHON_IMAGE"],
                "sleep",
                "300",
            ],
            [
                "run",
                "-d",
                "--name",
                name + "-worker",
                "--label",
                label,
                env["DOCKYARD_PYTHON_IMAGE"],
                "sleep",
                "300",
            ],
        ):
            result = runtime.command(args)
            assert result.ok, result.stderr
        outsider_result = runtime.command(
            ["create", "--name", outsider, env["DOCKYARD_PYTHON_IMAGE"], "sleep", "300"]
        )
        assert outsider_result.ok, outsider_result.stderr
        outsider_id = outsider_result.stdout.strip()
        inventory = runtime.discover()
        assert len(inventory) == 4
        service.perform(unit, "stop")
        assert not runtime.inspect("container", name)["State"]["Running"]
        assert not runtime.inspect("container", name + "-worker")["State"]["Running"]
        service.perform(unit, "resume")
        assert runtime.inspect("container", name + "-worker")["State"]["Running"]
        service.perform(unit, "clean")
        assert runtime.inspect("container", name) is None
        assert runtime.inspect("network", network) is None
        assert runtime.inspect("volume", volume) is None
        assert runtime.inspect("container", outsider_id)["Id"] == outsider_id
    finally:
        service.perform(unit, "clean")
        if outsider_id:
            # This fixture created and recorded this ID itself; no broad cleanup.
            runtime.require(runtime.command(["container", "rm", "--force", outsider_id]))
