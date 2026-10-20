import os
import sys
import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from dockyard import consoles
from dockyard.consoles import ConsoleError, Consoles, trim
from dockyard.models import Lab, Runtime
from dockyard.service import Service
from dockyard.store import timestamp
from dockyard.web import CONSOLE_ENDED, create_app

ORIGIN = "http://127.0.0.1:8768"
HEADERS = {"Origin": ORIGIN, "X-Dockyard": "1"}


def wait_for(predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for the shell.")


def collect(manager, console_id):
    received = bytearray()
    ended = []
    history, live = manager.attach(
        console_id, lambda data: received.extend(data) if data else ended.append(True)
    )
    received[:0] = history
    return received, ended, live


def test_a_console_is_a_real_pty_with_size_input_and_exit_code(tmp_path):
    manager = Consoles()
    script = "stty size; read line; echo got:$line; exit 3"
    console = manager.open(
        "m01-processes", "f" * 32, ["/bin/sh", "-c", script], str(tmp_path), dict(os.environ),
        (91, 27),
    )  # fmt: skip
    received, ended, live = collect(manager, console["id"])
    assert live
    wait_for(lambda: b"27 91" in received)
    manager.resize(console["id"], 120, 40)
    manager.write(console["id"], b"hello\n")
    wait_for(lambda: ended)
    assert b"got:hello" in received
    state = manager.public()[0]
    assert state["alive"] is False and state["exit_code"] == 3 and state["number"] == 1
    # Ended shells keep their scrollback so a reconnecting browser can show the last output.
    history, live = manager.attach(console["id"], lambda data: None)
    assert b"got:hello" in history and not live


def test_ending_a_lab_hangs_up_its_shells_and_records_why(tmp_path):
    manager = Consoles()
    command = ["/bin/sh", "-c", "while true; do sleep 1; done"]
    mine = manager.open("m01-processes", "a" * 32, command, str(tmp_path), {}, (80, 24))
    other = manager.open("m02-images", "b" * 32, command, str(tmp_path), {}, (80, 24))
    manager.end_lab("a" * 32, "The lab was reset, so this shell closed.")
    wait_for(lambda: not next(i for i in manager.public() if i["id"] == mine["id"])["alive"])
    states = {item["id"]: item for item in manager.public()}
    assert states[mine["id"]]["ended_by"] == "The lab was reset, so this shell closed."
    assert states[other["id"]]["alive"]
    manager.remove(other["id"])
    assert [item["id"] for item in manager.public()] == [mine["id"]]
    with pytest.raises(ConsoleError):
        manager.write(other["id"], b"x")


def test_shell_numbers_fill_gaps_and_each_lab_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(consoles, "PER_UNIT", 2)
    manager = Consoles()
    command = ["/bin/sh", "-c", "sleep 30"]
    first = manager.open("m01-processes", "a" * 32, command, str(tmp_path), {}, (80, 24))
    second = manager.open("m01-processes", "a" * 32, command, str(tmp_path), {}, (80, 24))
    assert (first["number"], second["number"]) == (1, 2)
    with pytest.raises(ConsoleError, match="already has 2 shells"):
        manager.open("m01-processes", "a" * 32, command, str(tmp_path), {}, (80, 24))
    manager.remove(first["id"])
    third = manager.open("m01-processes", "a" * 32, command, str(tmp_path), {}, (80, 24))
    assert third["number"] == 1
    manager.shutdown()


def test_the_shell_sees_a_modern_terminal_not_the_backend_terminal():
    env = consoles.terminal_environment(
        {"TERM": "dumb", "ITERM_SESSION_ID": "x", "TMUX": "/tmp/t", "LANG": "", "HOME": "/h"}
    )
    assert env["TERM"] == "xterm-256color" and env["COLORTERM"] == "truecolor"
    assert env["DOCKYARD_TERMINAL"] == "embedded" and env["HOME"] == "/h"
    assert "ITERM_SESSION_ID" not in env and "TMUX" not in env
    assert "UTF-8" in env["LC_CTYPE"]


def test_scrollback_drops_whole_old_lines():
    buffer = bytearray(b"old line\n" + b"x" * consoles.SCROLLBACK)
    trim(buffer)
    assert buffer == b"x" * consoles.SCROLLBACK
    short = bytearray(b"abc")
    trim(short)
    assert short == b"abc"


@pytest.fixture
def lab_client(tmp_path):
    service = Service(tmp_path / "profile")
    workspace = tmp_path / "lab workspace"
    workspace.mkdir()
    service.store.save_lab(
        Lab(
            id="f" * 32,
            unit_id="m01-processes",
            revision=1,
            runtime=Runtime.DOCKER,
            state="ready",
            workspace=str(workspace),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={"port": "32123", "docker_endpoint": "unix:///owned.sock"},
        )
    )
    app, nonce = create_app(service, ORIGIN)
    with TestClient(app) as client:
        client.post("/api/session", json={"token": nonce}, headers=HEADERS)
        yield client, service, workspace
    service.consoles.shutdown()


@pytest.mark.skipif(sys.platform == "win32", reason="lab shells need a POSIX host")
def test_the_browser_streams_a_real_lab_shell(lab_client):
    client, service, workspace = lab_client
    response = client.post(
        "/api/units/m01-processes/consoles", json={"cols": 100, "rows": 30}, headers=HEADERS
    )
    assert response.status_code == 200
    console = response.json()
    assert console["lab_id"] == "f" * 32
    assert client.get("/api/state").json()["consoles"][0]["id"] == console["id"]
    with client.websocket_connect(
        f"/api/consoles/{console['id']}/stream", headers={"Origin": ORIGIN}
    ) as socket:
        socket.send_text('{"cols": 132, "rows": 41}')
        socket.send_bytes(b"echo unit=$DOCKYARD_UNIT; stty size; pwd; exit\n")
        output = b""
        with pytest.raises(WebSocketDisconnect) as closed:
            while True:
                output += socket.receive_bytes()
        assert closed.value.code == CONSOLE_ENDED
    assert b"unit=m01-processes" in output
    assert b"41 132" in output
    assert str(workspace).encode() in output
    assert b"Meet Dispatch" in output


def test_console_streams_require_the_workbench_origin_and_session(lab_client):
    client, service, _ = lab_client
    console = client.post(
        "/api/units/m01-processes/consoles", json={"cols": 80, "rows": 24}, headers=HEADERS
    ).json()
    path = f"/api/consoles/{console['id']}/stream"
    for headers in ({}, {"Origin": "https://unrelated.example"}):
        with (
            pytest.raises(WebSocketDisconnect) as refused,
            client.websocket_connect(path, headers=headers),
        ):
            pass
        assert refused.value.code == 1008
    client.cookies.clear()
    with (
        pytest.raises(WebSocketDisconnect) as refused,
        client.websocket_connect(path, headers={"Origin": ORIGIN}),
    ):
        pass
    assert refused.value.code == 1008


def test_consoles_need_a_prepared_lab_and_a_confirmed_request(lab_client):
    client, service, _ = lab_client
    assert client.post("/api/units/m01-processes/consoles", json={}).status_code == 403
    missing = client.post("/api/units/m02-cache/consoles", json={}, headers=HEADERS)
    assert missing.status_code == 400
    lab = service.store.lab("m01-processes")
    lab.state = "preparing"
    service.store.save_lab(lab)
    busy = client.post("/api/units/m01-processes/consoles", json={}, headers=HEADERS)
    assert busy.status_code == 400 and "ready" in busy.json()["detail"]
