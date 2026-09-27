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


def test_interrupted_cli_reports_interruption_and_recovers_on_retry():
    import signal
    import socket
    import subprocess
    import sys
    import tempfile

    with tempfile.TemporaryDirectory(prefix="dy-interrupt-", dir="/private/tmp") as temporary:
        profile = Path(temporary)
        service = Service(profile)
        endpoint = service._docker_endpoint()
        proxy = profile / "docker.sock"
        proxy.symlink_to(endpoint.removeprefix("unix://"))
        env = dict(os.environ, DOCKER_HOST="unix://" + str(proxy))
        base = [sys.executable, "-m", "dockyard", "--data-dir", str(profile), "lab"]

        def execute(action):
            args = [*base, action, "m01-processes"]
            if action == "clean":
                args.append("--yes")
            return subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)

        child = None
        try:
            result = execute("prepare")
            assert result.returncode == 0, result.stderr
            draft = Path(service.store.lab("m01-processes").workspace) / "my-runbook.md"
            draft.write_text("Preserve this diagnosis.\n")
            assert execute("clean").returncode == 0
            proxy.unlink()
            with socket.socket(socket.AF_UNIX) as listener:
                listener.bind(str(proxy))
                listener.listen()
                listener.settimeout(15)
                child = subprocess.Popen(
                    [*base, "prepare", "m01-processes"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                connection, _ = listener.accept()
                with connection:
                    child.send_signal(signal.SIGINT)
                    output, _ = child.communicate(timeout=15)
                assert child.returncode == 130
                assert b"preserved" in output
            assert any(item["state"] == "running" for item in service.store.operations())
            proxy.unlink()
            proxy.symlink_to(endpoint.removeprefix("unix://"))
            result = execute("prepare")
            assert result.returncode == 0, result.stderr
            assert draft.read_text() == "Preserve this diagnosis.\n"
            operations = service.store.operations()
            assert not any(
                item["state"] in {"running", "queued", "canceling"} for item in operations
            )
            assert any(item["state"] == "failed" for item in operations)
        finally:
            if child and child.poll() is None:
                child.send_signal(signal.SIGINT)
                child.communicate(timeout=15)
            proxy.unlink(missing_ok=True)
            proxy.symlink_to(endpoint.removeprefix("unix://"))
            result = execute("clean")
            assert result.returncode == 0, result.stderr
