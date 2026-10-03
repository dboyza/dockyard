"""Foundations checks accept documented alternatives and reject the failure modes they teach."""

import os
import time
from pathlib import Path

import pytest

from dockyard.process import run
from dockyard.service import Service

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real runtimes"
    ),
]

REPLACE = 'docker rm -f "$DOCKYARD_CONTAINER" >/dev/null 2>&1 || true\n'
LABEL = '--name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB"'

# Each case is (unit, shell script, criteria expected to fail; empty means a pass).
CASES = {
    "first-container-create-and-start": (
        "m00-first-container",
        f'docker create {LABEL} "$DOCKYARD_PYTHON_IMAGE" '
        "python -c \"print('Hello from inside a container')\"\n"
        'docker start -a "$DOCKYARD_CONTAINER"\n',
        set(),
    ),
    "first-container-removed-by-rm": (
        "m00-first-container",
        f'docker run --rm {LABEL} "$DOCKYARD_PYTHON_IMAGE" '
        "python -c \"print('Hello from inside a container')\"\n",
        {"lab-identity", "python-image", "program-finished", "clean-exit", "program-output"},
    ),
    "first-container-python-error": (
        "m00-first-container",
        f'docker run {LABEL} "$DOCKYARD_PYTHON_IMAGE" '
        "python -c \"print('Hello from inside a container'\" || true\n",
        {"clean-exit"},
    ),
    "layers-other-process-and-copy": (
        "m00-layers",
        f'docker run -d {LABEL} "$DOCKYARD_PYTHON_IMAGE" tail -f /dev/null\n'
        'printf "copied in\\n" > note.txt\n'
        'docker cp note.txt "$DOCKYARD_CONTAINER":/tmp/note.txt\n',
        set(),
    ),
    "layers-default-command-exits": (
        "m00-layers",
        f'docker run -d {LABEL} "$DOCKYARD_PYTHON_IMAGE"\n',
        {"still-running", "note-in-writable-layer"},
    ),
    "web-server-mount-flag-and-directory": (
        "m00-web-server",
        f'docker run -d {LABEL} -p "127.0.0.1:$DOCKYARD_PORT:8000" '
        '--mount "type=bind,src=$DOCKYARD_WORKSPACE/site,dst=/srv/page,readonly" '
        '"$DOCKYARD_PYTHON_IMAGE" python -m http.server 8000 --directory /srv/page\n',
        set(),
    ),
    "web-server-every-network": (
        "m00-web-server",
        f'docker run -d {LABEL} -p "$DOCKYARD_PORT:8000" '
        '-v "$DOCKYARD_WORKSPACE/site:/site:ro" -w /site '
        '"$DOCKYARD_PYTHON_IMAGE" python -m http.server 8000\n',
        {"loopback-binding"},
    ),
    "web-server-writable-mount": (
        "m00-web-server",
        f'docker run -d {LABEL} -p "127.0.0.1:$DOCKYARD_PORT:8000" '
        '-v "$DOCKYARD_WORKSPACE/site:/site" -w /site '
        '"$DOCKYARD_PYTHON_IMAGE" python -m http.server 8000\n',
        {"read-only-mount"},
    ),
    "mission-server-on-port-80": (
        "m00-mission",
        f'docker run -d {LABEL} -p "127.0.0.1:$DOCKYARD_PORT:80" '
        '-v "$DOCKYARD_WORKSPACE/welcome:/usr/share/welcome:ro" '
        '"$DOCKYARD_PYTHON_IMAGE" python -m http.server 80 --directory /usr/share/welcome\n',
        set(),
    ),
    "mission-restart-keeps-the-fault": (
        "m00-mission",
        None,
        {"page-response", "read-only-mount"},
    ),
    "mission-every-network": (
        "m00-mission",
        f'docker run -d {LABEL} -p "$DOCKYARD_PORT:8000" '
        '-v "$DOCKYARD_WORKSPACE/welcome:/srv:ro" -w /srv '
        '"$DOCKYARD_PYTHON_IMAGE" python -m http.server 8000\n',
        {"assigned-port", "loopback-only"},
    ),
}


def settled_check(service, unit_id, expect_pass):
    deadline = time.monotonic() + 20
    while True:
        observed = service.perform(unit_id, "check")
        if (observed["status"] == "pass") == expect_pass or time.monotonic() > deadline:
            return observed
        time.sleep(0.5)


@pytest.mark.parametrize("case", CASES, ids=list(CASES))
def test_foundations_check_contract(lab_profile, case):
    unit_id, script, failing = CASES[case]
    service = Service(lab_profile)
    try:
        service.perform(unit_id, "prepare")
        lab = service.store.lab(unit_id)
        assert lab is not None
        env = service.environment(lab)
        if script is None:
            restart = run(["docker", "restart", env["DOCKYARD_CONTAINER"]], env=env)
            assert restart.ok, restart.stderr
        else:
            result = run(
                ["/bin/sh", "-c", "set -eu\n" + REPLACE + script],
                cwd=Path(lab.workspace),
                env=env,
                timeout=120,
            )
            assert result.ok, result.stdout + result.stderr
        observed = settled_check(service, unit_id, expect_pass=not failing)
        failed = {item["criterion"] for item in observed["evidence"] if item["status"] != "pass"}
        assert failed == failing, observed
    finally:
        service.perform(unit_id, "clean")
