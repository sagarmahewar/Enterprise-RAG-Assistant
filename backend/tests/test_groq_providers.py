import httpx
import pytest

from app.domain.models import DocumentChunk
from app.infrastructure.providers.groq import GroqEmbeddingProvider, GroqLLMProvider


def _make_client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(base_url="https://api.groq.test/openai/v1", transport=handler, timeout=10)


def test_groq_embedding_provider_parses_embeddings() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/openai/v1/embeddings"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            status_code=200,
            json={"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]},
        )

    provider = GroqEmbeddingProvider(
        base_url="https://api.groq.test/openai/v1",
        api_key="test-key",
        model_name="nomic-embed-text-v1.5",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    vectors = provider.embed_texts(["alpha", "beta"])
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_groq_embedding_provider_rejects_mismatched_count() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/openai/v1/embeddings"
        return httpx.Response(status_code=200, json={"data": [{"embedding": [0.1, 0.2]}]})

    provider = GroqEmbeddingProvider(
        base_url="https://api.groq.test/openai/v1",
        api_key="test-key",
        model_name="nomic-embed-text-v1.5",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    with pytest.raises(ValueError, match="count does not match"):
        provider.embed_texts(["alpha", "beta"])


def test_groq_llm_provider_parses_response_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/openai/v1/chat/completions"
        body = request.content.decode("utf-8")
        assert "What is retention policy?" in body
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "Retention is seven years."}}]},
        )

    provider = GroqLLMProvider(
        base_url="https://api.groq.test/openai/v1",
        api_key="test-key",
        model_name="llama-3.1-8b-instant",
        timeout_seconds=10,
        temperature=0.1,
        max_tokens=256,
        client=_make_client(httpx.MockTransport(handler)),
    )
    chunks = [
        DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            document_name="Policy.pdf",
            text="Retention policy is seven years.",
            page_ref="4",
            metadata={},
        )
    ]
    answer = provider.generate_answer("What is retention policy?", chunks)
    assert answer == "Retention is seven years."
