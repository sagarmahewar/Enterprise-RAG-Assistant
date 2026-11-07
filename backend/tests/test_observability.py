from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_request_id_is_returned_in_response_header() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    assert response.headers["X-Request-Id"]


def test_request_id_preserves_incoming_header() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-Id": "custom-request-id"})
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "custom-request-id"
