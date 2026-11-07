from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.domain.models import DocumentChunk


def _extract_response_text(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Ollama generate response payload must be an object")
    response = payload.get("response")
    if not isinstance(response, str):
        raise ValueError("Ollama generate response missing 'response' text")
    return response


def _extract_embeddings(payload: object) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise ValueError("Ollama embed response payload must be an object")
    raw_embeddings = payload.get("embeddings")
    if not isinstance(raw_embeddings, list):
        raise ValueError("Ollama embed response missing 'embeddings'")

    vectors: list[list[float]] = []
    for row in raw_embeddings:
        if not isinstance(row, list):
            raise ValueError("Ollama embed response contains non-vector entry")
        vector: list[float] = []
        for value in row:
            if not isinstance(value, (int, float)):
                raise ValueError("Ollama embed response contains non-numeric vector value")
            vector.append(float(value))
        vectors.append(vector)
    return vectors


def _build_context_block(chunks: Sequence[DocumentChunk]) -> str:
    lines: list[str] = []
    for chunk in chunks:
        ref = chunk.page_ref or "n/a"
        lines.append(f"[{chunk.document_name} | page={ref}] {chunk.text}")
    return "\n".join(lines)


class OllamaEmbeddingProvider:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout_seconds: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"ollama-embeddings:{model_name}"
        self._model_name = model_name
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout_seconds)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.post(
            "/api/embed",
            json={"model": self._model_name, "input": list(texts)},
        )
        response.raise_for_status()
        vectors = _extract_embeddings(response.json())
        if len(vectors) != len(texts):
            raise ValueError("Ollama embed response count does not match input text count")
        return vectors


class OllamaLLMProvider:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout_seconds: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"ollama-llm:{model_name}"
        self._model_name = model_name
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout_seconds)

    def generate_answer(self, query: str, context_chunks: Sequence[DocumentChunk]) -> str:
        context = _build_context_block(context_chunks)
        prompt = (
            "You are an enterprise RAG assistant. Answer only using the provided context.\n\n"
            f"Question:\n{query}\n\n"
            f"Context:\n{context}\n\n"
            "If the context is insufficient, say so clearly."
        )
        response = self._client.post(
            "/api/generate",
            json={"model": self._model_name, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return _extract_response_text(response.json())

