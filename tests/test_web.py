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
