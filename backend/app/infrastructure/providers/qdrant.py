from __future__ import annotations

from collections.abc import Mapping, Sequence

import httpx

from app.domain.models import DocumentChunk


def _coerce_metadata(raw_metadata: object) -> dict[str, str]:
    if not isinstance(raw_metadata, dict):
        return {}
    output: dict[str, str] = {}
    for key, value in raw_metadata.items():
        if isinstance(key, str) and isinstance(value, str):
            output[key] = value
    return output


def _extract_result(payload: object) -> object:
    if not isinstance(payload, dict):
        raise ValueError("Qdrant response payload must be an object")
    return payload.get("result")


class QdrantVectorStore:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        collection_name: str,
        timeout_seconds: int,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = f"qdrant:{collection_name}"
        self._collection_name = collection_name
        headers = {"api-key": api_key} if api_key else None
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout_seconds,
            headers=headers,
        )

    def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        if not chunks:
            return

        first_embedding = chunks[0].embedding
        if first_embedding is None or len(first_embedding) == 0:
            raise ValueError("Cannot upsert chunk without embedding vector")
        vector_size = len(first_embedding)
        self._ensure_collection(vector_size=vector_size)

        points: list[dict[str, object]] = []
        for chunk in chunks:
            if chunk.embedding is None or len(chunk.embedding) != vector_size:
                raise ValueError("Inconsistent or missing embedding vector for Qdrant upsert")
            points.append(
                {
                    "id": chunk.chunk_id,
                    "vector": list(chunk.embedding),
                    "payload": {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "document_name": chunk.document_name,
                        "text": chunk.text,
                        "page_ref": chunk.page_ref,
                        "metadata": chunk.metadata,
                    },
                }
            )

        response = self._client.put(
            f"/collections/{self._collection_name}/points",
            json={"points": points},
        )
        response.raise_for_status()

    def query(
        self,
        query_vector: Sequence[float],
        top_k: int,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[DocumentChunk]:
        if top_k <= 0 or not query_vector:
            return []
        response = self._client.post(
            f"/collections/{self._collection_name}/points/search",
            json={
                "vector": list(query_vector),
                "limit": top_k,
                "filter": _to_qdrant_filter(metadata_filter),
            },
        )
        response.raise_for_status()
        result = _extract_result(response.json())
        if not isinstance(result, list):
            return []

        output: list[DocumentChunk] = []
        for hit in result:
            if not isinstance(hit, dict):
                continue
            payload = hit.get("payload")
            if not isinstance(payload, dict):
                continue
            chunk_id = payload.get("chunk_id")
            document_id = payload.get("document_id")
            document_name = payload.get("document_name")
            text = payload.get("text")
            if not all(
                isinstance(value, str) for value in (chunk_id, document_id, document_name, text)
            ):
                continue
            chunk_id_str = str(chunk_id)
            document_id_str = str(document_id)
            document_name_str = str(document_name)
            text_str = str(text)
            page_ref = payload.get("page_ref")
            score = hit.get("score")
            output.append(
                DocumentChunk(
                    chunk_id=chunk_id_str,
                    document_id=document_id_str,
                    document_name=document_name_str,
                    text=text_str,
                    page_ref=page_ref if isinstance(page_ref, str) else None,
                    metadata=_coerce_metadata(payload.get("metadata")),
                    embedding=None,
                    score=float(score) if isinstance(score, (int, float)) else None,
                )
            )
        return output

    def _ensure_collection(self, *, vector_size: int) -> None:
        response = self._client.get("/collections")
        response.raise_for_status()
        collections_result = _extract_result(response.json())
        if isinstance(collections_result, dict):
            raw_collections = collections_result.get("collections")
        else:
            raw_collections = None
        existing_names: set[str] = set()
        if isinstance(raw_collections, list):
            for item in raw_collections:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str):
                        existing_names.add(name)
        if self._collection_name in existing_names:
            return
        create_response = self._client.put(
            f"/collections/{self._collection_name}",
            json={"vectors": {"size": vector_size, "distance": "Cosine"}},
        )
        create_response.raise_for_status()


def _to_qdrant_filter(metadata_filter: Mapping[str, str] | None) -> dict[str, object] | None:
    if not metadata_filter:
        return None
    must: list[dict[str, object]] = []
    for key, value in metadata_filter.items():
        field_name = key if key in {"document_id", "document_name"} else f"metadata.{key}"
        must.append({"key": field_name, "match": {"value": value}})
    return {"must": must} if must else None
