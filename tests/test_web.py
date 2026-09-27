import pytest
from fastapi.testclient import TestClient

from dockyard.service import Service
from dockyard.web import create_app

ORIGIN = "http://127.0.0.1:8768"
HEADERS = {"Origin": ORIGIN, "X-Dockyard": "1"}


@pytest.fixture
def connected(tmp_path):
    service = Service(tmp_path)
    app, nonce = create_app(service, ORIGIN)
    with TestClient(app) as client:
        assert (
            client.post("/api/session", json={"token": nonce}, headers=HEADERS).status_code == 200
        )
        yield client, service


def test_one_time_authentication_and_origin_boundary(tmp_path):
    app, nonce = create_app(Service(tmp_path), ORIGIN)
    with TestClient(app) as client:
        assert client.get("/api/catalog").status_code == 401
        assert client.post("/api/session", json={"token": nonce}).status_code == 403
        assert (
            client.post("/api/session", json={"token": nonce}, headers=HEADERS).status_code == 200
        )
        assert (
            client.post("/api/session", json={"token": nonce}, headers=HEADERS).status_code == 401
        )
        assert (
            client.get("/api/catalog", headers={"Origin": "https://unrelated.example"}).status_code
            == 403
        )
        assert client.get("/api/catalog").status_code == 200


def test_reading_a_unit_does_not_reveal_references_or_change_resume(connected):
    client, service = connected
    response = client.get("/api/units/m01-processes")
    assert response.status_code == 200
    assert "reference" not in response.json()
    assert "checks" not in response.json()
    assert service.store.setting("last_unit") is None
    client.post("/api/units/m01-processes/events", json={"event": "viewed"}, headers=HEADERS)
    assert service.store.setting("last_unit") == "m01-processes"


def test_mutations_and_reference_reveals_require_explicit_intent(connected):
    client, service = connected
    assert (
        client.post(
            "/api/units/m01-processes/lab", json={"action": "reset"}, headers=HEADERS
        ).status_code
        == 400
    )
    response = client.post(
        "/api/units/m01-processes/reference", json={"action": "reveal"}, headers=HEADERS
    )
    assert response.status_code == 400
    response = client.post(
        "/api/units/m01-processes/reference",
        json={"action": "reveal", "confirmed": True},
        headers=HEADERS,
    )
    assert "run.sh" in response.json()
    assert service.store.progress()["m01-processes"]["reference"] == 1


def test_unknown_api_paths_do_not_return_the_spa(connected):
    client, _ = connected
    assert client.get("/api/no-such-endpoint").status_code == 404


def test_progress_preview_is_bounded_and_requires_the_same_confirmed_archive(
    connected, monkeypatch
):
    import dockyard.archives as archives

    client, service = connected
    service.store.save_note("m01-processes", "Portable observation.")
    response = client.get("/api/progress/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    archive = response.content
    assert client.post("/api/progress/preview", content=archive).status_code == 403
    preview = client.post("/api/progress/preview", content=archive, headers=HEADERS)
    assert preview.status_code == 200
    digest = preview.json()["digest"]
    assert preview.json()["notes"] == 1
    assert (
        client.post("/api/progress/import", json={"digest": digest}, headers=HEADERS).status_code
        == 400
    )
    (service.directory / "imports/pending.zip").write_bytes(b"Changed after review")
    assert (
        client.post(
            "/api/progress/import", json={"digest": digest, "confirmed": True}, headers=HEADERS
        ).status_code
        == 400
    )
    assert service.store.note("m01-processes") == "Portable observation."
    assert client.post("/api/progress/preview", content=archive, headers=HEADERS).status_code == 200
    imported = client.post(
        "/api/progress/import", json={"digest": digest, "confirmed": True}, headers=HEADERS
    )
    assert imported.status_code == 200
    assert imported.json()["already_imported"] is False
    assert (
        client.post(
            "/api/progress/import", json={"digest": digest, "confirmed": True}, headers=HEADERS
        ).json()["already_imported"]
        is True
    )
    monkeypatch.setattr(archives, "MAX_ARCHIVE", 32)
    assert (
        client.post("/api/progress/preview", content=b"x" * 33, headers=HEADERS).status_code == 413
    )


def test_terminal_choices_cannot_execute_arbitrary_programs(connected, monkeypatch, tmp_path):
    from dockyard import terminals
    from dockyard.models import Lab, Runtime
    from dockyard.store import timestamp

    client, service = connected
    workspace = tmp_path / "lab workspace"
    workspace.mkdir()
    lab = Lab(
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
    service.store.save_lab(lab)
    monkeypatch.setattr(
        terminals, "available", lambda: [terminals.Terminal("xterm", "xterm", "/xterm")]
    )
    called = []
    monkeypatch.setattr(terminals, "launch", lambda *args: called.append(args))
    info = client.get("/api/units/m01-processes/terminal").json()
    assert info["options"] == [{"id": "xterm", "label": "xterm"}]
    assert "--data-dir" in info["command"] and "lab shell m01-processes" in info["command"]
    response = client.post(
        "/api/units/m01-processes/lab",
        json={"action": "terminal", "terminal": "/untrusted"},
        headers=HEADERS,
    )
    assert response.status_code == 400 and not called
    response = client.post(
        "/api/units/m01-processes/lab",
        json={"action": "terminal", "terminal": "xterm"},
        headers=HEADERS,
    )
    assert response.status_code == 200 and called[0][0].id == "xterm"
    assert service.store.setting("terminal") == "xterm"
    assert client.get("/api/units/m01-processes/terminal").json()["selected"] == "xterm"
    monkeypatch.setattr(terminals, "available", lambda: [])
    info = client.get("/api/units/m01-processes/terminal").json()
    assert info["options"] == [] and info["command"] and info["selected"] == "auto"
