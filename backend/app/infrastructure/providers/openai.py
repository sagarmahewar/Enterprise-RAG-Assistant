from __future__ import annotations

from collections.abc import Sequence

import httpx


def _extract_embeddings(payload: object) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise ValueError("OpenAI embeddings response payload must be an object")
    raw_data = payload.get("data")
    if not isinstance(raw_data, list):
        raise ValueError("OpenAI embeddings response missing 'data'")

    vectors: list[list[float]] = []
    for item in raw_data:
        if not isinstance(item, dict):
            raise ValueError("OpenAI embeddings response contains invalid data entry")
        raw_embedding = item.get("embedding")
        if not isinstance(raw_embedding, list):
            raise ValueError("OpenAI embeddings response contains missing embedding vector")
        vector: list[float] = []
        for value in raw_embedding:
            if not isinstance(value, (int, float)):
                raise ValueError("OpenAI embeddings response contains non-numeric vector value")
            vector.append(float(value))
        vectors.append(vector)
    return vectors


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"openai-embeddings:{model_name}"
        self._model_name = model_name
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout_seconds,
            headers=self._headers,
        )

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.post(
            "/embeddings",
            json={"model": self._model_name, "input": list(texts)},
            headers=self._headers,
        )
        response.raise_for_status()
        vectors = _extract_embeddings(response.json())
        if len(vectors) != len(texts):
            raise ValueError("OpenAI embeddings response count does not match input text count")
        return vectors
