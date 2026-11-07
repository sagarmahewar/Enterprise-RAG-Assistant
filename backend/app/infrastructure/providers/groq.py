from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.domain.models import DocumentChunk


def _extract_chat_response_text(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Groq chat response payload must be an object")
    raw_choices = payload.get("choices")
    if not isinstance(raw_choices, list) or not raw_choices:
        raise ValueError("Groq chat response missing 'choices'")
    first_choice = raw_choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("Groq chat response contains invalid choice")
    raw_message = first_choice.get("message")
    if not isinstance(raw_message, dict):
        raise ValueError("Groq chat response choice missing 'message'")
    content = raw_message.get("content")
    if not isinstance(content, str):
        raise ValueError("Groq chat response message missing text content")
    return content


def _extract_embeddings(payload: object) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise ValueError("Groq embeddings response payload must be an object")
    raw_data = payload.get("data")
    if not isinstance(raw_data, list):
        raise ValueError("Groq embeddings response missing 'data'")

    vectors: list[list[float]] = []
    for item in raw_data:
        if not isinstance(item, dict):
            raise ValueError("Groq embeddings response contains invalid data entry")
        raw_embedding = item.get("embedding")
        if not isinstance(raw_embedding, list):
            raise ValueError("Groq embeddings response contains missing embedding vector")
        vector: list[float] = []
        for value in raw_embedding:
            if not isinstance(value, (int, float)):
                raise ValueError("Groq embeddings response contains non-numeric vector value")
            vector.append(float(value))
        vectors.append(vector)
    return vectors


def _build_context_block(chunks: Sequence[DocumentChunk]) -> str:
    lines: list[str] = []
    for chunk in chunks:
        ref = chunk.page_ref or "n/a"
        lines.append(f"[{chunk.document_name} | page={ref}] {chunk.text}")
    return "\n".join(lines)


class GroqEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"groq-embeddings:{model_name}"
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
            raise ValueError("Groq embeddings response count does not match input text count")
        return vectors


class GroqLLMProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        temperature: float,
        max_tokens: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"groq-llm:{model_name}"
        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout_seconds,
            headers=self._headers,
        )

    def generate_answer(self, query: str, context_chunks: Sequence[DocumentChunk]) -> str:
        context = _build_context_block(context_chunks)
        response = self._client.post(
            "/chat/completions",
            json={
                "model": self._model_name,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an enterprise RAG assistant. "
                            "Answer only using the provided context. "
                            "If the context is insufficient, say so clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question:\n{query}\n\nContext:\n{context}",
                    },
                ],
            },
            headers=self._headers,
        )
        response.raise_for_status()
        return _extract_chat_response_text(response.json())
