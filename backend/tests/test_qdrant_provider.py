import httpx

from app.domain.models import DocumentChunk
from app.infrastructure.providers.qdrant import QdrantVectorStore


def test_qdrant_vector_store_upsert_and_query() -> None:
    put_points_called = {"value": False}
    put_collection_called = {"value": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/collections":
            return httpx.Response(status_code=200, json={"result": {"collections": []}})

        if request.method == "PUT" and request.url.path == "/collections/rag_chunks":
            put_collection_called["value"] = True
            return httpx.Response(status_code=200, json={"result": True})

        if request.method == "PUT" and request.url.path == "/collections/rag_chunks/points":
            put_points_called["value"] = True
            return httpx.Response(status_code=200, json={"result": {"status": "ok"}})

        if request.method == "POST" and request.url.path == "/collections/rag_chunks/points/search":
            return httpx.Response(
                status_code=200,
                json={
                    "result": [
                        {
                            "score": 0.91,
                            "payload": {
                                "chunk_id": "chunk-1",
                                "document_id": "doc-1",
                                "document_name": "policy.txt",
                                "text": "Retention policy is seven years.",
                                "page_ref": "1",
                                "metadata": {"fused_score": "0.85"},
                            },
                        }
                    ]
                },
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(
        base_url="http://qdrant.test:6333",
        transport=httpx.MockTransport(handler),
    )
    store = QdrantVectorStore(
        base_url="http://qdrant.test:6333",
        api_key=None,
        collection_name="rag_chunks",
        timeout_seconds=10,
        client=client,
    )

    store.upsert_chunks(
        [
            DocumentChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_name="policy.txt",
                text="Retention policy is seven years.",
                page_ref="1",
                metadata={"source": "policy"},
                embedding=[0.1, 0.2, 0.3],
            )
        ]
    )

    assert put_collection_called["value"] is True
    assert put_points_called["value"] is True

    results = store.query(query_vector=[0.2, 0.1, 0.4], top_k=3)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"
    assert results[0].score == 0.91
    assert results[0].metadata["fused_score"] == "0.85"
