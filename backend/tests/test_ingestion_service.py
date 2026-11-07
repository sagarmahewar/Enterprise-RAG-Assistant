from __future__ import annotations

from pathlib import Path

import pytest

from app.application.container import build_container
from app.application.services.ingestion_service import IngestionService
from app.core.settings import Settings


def _fake_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="Enterprise RAG Assistant API",
        app_env="test",
        api_v1_prefix="/api/v1",
        cors_origins=("http://localhost:5173",),
        llm_provider_backend="local-fake-llm",
        embedding_provider_backend="local-fake-embeddings",
        vector_store_backend="local-fake-vector-store",
        reranker_backend="local-fake-reranker",
        document_access_policy_backend="allow-all",
        ollama_base_url="http://localhost:11434",
        ollama_llm_model="qwen2.5:14b",
        ollama_embedding_model="nomic-embed-text",
        ollama_request_timeout_seconds=90,
        groq_base_url="https://api.groq.com/openai/v1",
        groq_api_key="",
        groq_llm_model="llama-3.1-8b-instant",
        groq_embedding_model="nomic-embed-text-v1.5",
        groq_temperature=0.1,
        groq_max_tokens=1024,
        groq_request_timeout_seconds=60,
        qdrant_url="http://localhost:6333",
        qdrant_api_key="",
        qdrant_collection_name="rag_chunks_local",
        qdrant_timeout_seconds=30,
        metadata_db_path=tmp_path / "metadata.db",
        upload_dir=tmp_path / "uploads",
        max_upload_size_bytes=1024 * 1024,
        chunk_size_chars=120,
        chunk_overlap_chars=20,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )


def test_ingestion_pipeline_for_text_document(tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    container = build_container(settings)
    service = IngestionService(
        container=container,
        metadata_db_path=settings.metadata_db_path,
        upload_directory=settings.upload_dir,
        max_upload_size_bytes=settings.max_upload_size_bytes,
        chunk_size_chars=settings.chunk_size_chars,
        chunk_overlap_chars=settings.chunk_overlap_chars,
    )

    content = b"This is a test document.\n\nIt has two short paragraphs."
    result = service.ingest(
        document_name="sample.txt",
        mime_type="text/plain",
        content=content,
    )
    assert result.document_name == "sample.txt"
    assert result.chunk_count >= 1
    documents = service.list_documents()
    assert len(documents) == 1
    assert documents[0]["document_name"] == "sample.txt"


def test_ingestion_rejects_unsupported_mime_type(tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    container = build_container(settings)
    service = IngestionService(
        container=container,
        metadata_db_path=settings.metadata_db_path,
        upload_directory=settings.upload_dir,
        max_upload_size_bytes=settings.max_upload_size_bytes,
        chunk_size_chars=settings.chunk_size_chars,
        chunk_overlap_chars=settings.chunk_overlap_chars,
    )

    with pytest.raises(ValueError, match="Unsupported mime type"):
        service.ingest(
            document_name="sample.csv",
            mime_type="text/csv",
            content=b"a,b\n1,2",
        )
