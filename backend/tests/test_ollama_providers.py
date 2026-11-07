import httpx
import pytest

from app.domain.models import DocumentChunk
from app.infrastructure.providers.ollama import OllamaEmbeddingProvider, OllamaLLMProvider


def _make_client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(base_url="http://test-ollama", transport=handler, timeout=10)


def test_ollama_embedding_provider_parses_embeddings() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        return httpx.Response(
            status_code=200,
            json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]},
        )

    provider = OllamaEmbeddingProvider(
        base_url="http://unused",
        model_name="nomic-embed-text",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    vectors = provider.embed_texts(["alpha", "beta"])
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_ollama_embedding_provider_rejects_mismatched_count() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        return httpx.Response(status_code=200, json={"embeddings": [[0.1, 0.2]]})

    provider = OllamaEmbeddingProvider(
        base_url="http://unused",
        model_name="nomic-embed-text",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    with pytest.raises(ValueError, match="count does not match"):
        provider.embed_texts(["alpha", "beta"])


def test_ollama_llm_provider_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        body = request.content.decode("utf-8")
        assert "What is policy?" in body
        return httpx.Response(status_code=200, json={"response": "Grounded answer"})

    provider = OllamaLLMProvider(
        base_url="http://unused",
        model_name="qwen2.5:14b",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )
    chunks = [
        DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            document_name="Policy.pdf",
            text="Policy retention is 7 years.",
            page_ref="4",
            metadata={},
        )
    ]
    answer = provider.generate_answer("What is policy?", chunks)
    assert answer == "Grounded answer"

