import httpx
import pytest

from app.infrastructure.providers.openai import OpenAIEmbeddingProvider


def _make_client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(base_url="https://api.openai.test/v1", transport=handler, timeout=10)


def test_openai_embedding_provider_parses_embeddings() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            status_code=200,
            json={"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]},
        )

    provider = OpenAIEmbeddingProvider(
        base_url="https://api.openai.test/v1",
        api_key="test-key",
        model_name="text-embedding-3-small",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    vectors = provider.embed_texts(["alpha", "beta"])
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_openai_embedding_provider_rejects_mismatched_count() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        return httpx.Response(status_code=200, json={"data": [{"embedding": [0.1, 0.2]}]})

    provider = OpenAIEmbeddingProvider(
        base_url="https://api.openai.test/v1",
        api_key="test-key",
        model_name="text-embedding-3-small",
        timeout_seconds=10,
        client=_make_client(httpx.MockTransport(handler)),
    )

    with pytest.raises(ValueError, match="count does not match"):
        provider.embed_texts(["alpha", "beta"])
