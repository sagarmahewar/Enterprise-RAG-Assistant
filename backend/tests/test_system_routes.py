from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["service"] == "Enterprise RAG Assistant API"


def test_ready_endpoint_provider_snapshot() -> None:
    response = client.get("/api/v1/ready")
    payload = response.json()

    assert response.status_code == 200
    assert payload["ready"] is True
    assert payload["providers"]["llm"] == "ollama-llm:qwen2.5:14b"
    assert payload["providers"]["embedding"] == "ollama-embeddings:nomic-embed-text"
    assert payload["providers"]["document_access_policy"] == "allow-all-document-access"
    assert "application/pdf" in payload["supported_document_mime_types"]
    assert "text/plain" in payload["supported_document_mime_types"]
