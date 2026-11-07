from pathlib import Path

import pytest

from app.application.container import ProviderContainer, build_container
from app.core.settings import Settings
from app.domain.contracts import (
    DocumentParser,
    EmbeddingProvider,
    LLMProvider,
    Reranker,
    VectorStore,
)
from app.infrastructure.providers.ollama import OllamaEmbeddingProvider, OllamaLLMProvider


def _test_settings() -> Settings:
    return Settings(
        app_name="Enterprise RAG Assistant API",
        app_env="test",
        api_v1_prefix="/api/v1",
        cors_origins=("http://localhost:5173",),
        llm_provider_backend="ollama",
        embedding_provider_backend="ollama",
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
        metadata_db_path=Path("./data/test-metadata.db"),
        upload_dir=Path("./data/test-uploads"),
        max_upload_size_bytes=10485760,
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )


def test_build_container_contract_types() -> None:
    container = build_container(_test_settings())
    assert isinstance(container, ProviderContainer)
    assert isinstance(container.llm_provider, LLMProvider)
    assert isinstance(container.embedding_provider, EmbeddingProvider)
    assert isinstance(container.vector_store, VectorStore)
    assert isinstance(container.reranker, Reranker)
    assert isinstance(container.llm_provider, OllamaLLMProvider)
    assert isinstance(container.embedding_provider, OllamaEmbeddingProvider)


def test_parser_registry_contains_required_document_types() -> None:
    container = build_container(_test_settings())
    pdf_parser = container.parser_for_mime("application/pdf")
    docx_parser = container.parser_for_mime(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    txt_parser = container.parser_for_mime("text/plain")

    assert isinstance(pdf_parser, DocumentParser)
    assert isinstance(docx_parser, DocumentParser)
    assert isinstance(txt_parser, DocumentParser)


def test_build_container_supports_fake_provider_fallbacks() -> None:
    fake_settings = Settings(
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
        metadata_db_path=Path("./data/test-metadata.db"),
        upload_dir=Path("./data/test-uploads"),
        max_upload_size_bytes=10485760,
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )
    container = build_container(fake_settings)
    assert container.llm_provider.provider_name == "local-fake-llm"
    assert container.embedding_provider.provider_name == "local-fake-embeddings"


def test_build_container_supports_groq_and_qdrant_backends() -> None:
    cloud_settings = Settings(
        app_name="Enterprise RAG Assistant API",
        app_env="test",
        api_v1_prefix="/api/v1",
        cors_origins=("http://localhost:5173",),
        llm_provider_backend="groq",
        embedding_provider_backend="groq",
        vector_store_backend="qdrant",
        reranker_backend="local-fake-reranker",
        document_access_policy_backend="allow-all",
        ollama_base_url="http://localhost:11434",
        ollama_llm_model="qwen2.5:14b",
        ollama_embedding_model="nomic-embed-text",
        ollama_request_timeout_seconds=90,
        groq_base_url="https://api.groq.com/openai/v1",
        groq_api_key="test-key",
        groq_llm_model="llama-3.1-8b-instant",
        groq_embedding_model="nomic-embed-text-v1.5",
        groq_temperature=0.1,
        groq_max_tokens=1024,
        groq_request_timeout_seconds=60,
        qdrant_url="http://localhost:6333",
        qdrant_api_key="",
        qdrant_collection_name="rag_chunks_local",
        qdrant_timeout_seconds=30,
        metadata_db_path=Path("./data/test-metadata.db"),
        upload_dir=Path("./data/test-uploads"),
        max_upload_size_bytes=10485760,
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )
    container = build_container(cloud_settings)
    assert container.llm_provider.provider_name == "groq-llm:llama-3.1-8b-instant"
    assert container.embedding_provider.provider_name == "groq-embeddings:nomic-embed-text-v1.5"
    assert container.vector_store.provider_name == "qdrant:rag_chunks_local"


def test_build_container_rejects_unknown_llm_backend() -> None:
    unknown_settings = Settings(
        app_name="Enterprise RAG Assistant API",
        app_env="test",
        api_v1_prefix="/api/v1",
        cors_origins=("http://localhost:5173",),
        llm_provider_backend="unknown-provider",
        embedding_provider_backend="ollama",
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
        metadata_db_path=Path("./data/test-metadata.db"),
        upload_dir=Path("./data/test-uploads"),
        max_upload_size_bytes=10485760,
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER_BACKEND"):
        build_container(unknown_settings)


def test_build_container_rejects_unknown_document_access_backend() -> None:
    unknown_settings = Settings(
        app_name="Enterprise RAG Assistant API",
        app_env="test",
        api_v1_prefix="/api/v1",
        cors_origins=("http://localhost:5173",),
        llm_provider_backend="ollama",
        embedding_provider_backend="ollama",
        vector_store_backend="local-fake-vector-store",
        reranker_backend="local-fake-reranker",
        document_access_policy_backend="unknown-policy",
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
        metadata_db_path=Path("./data/test-metadata.db"),
        upload_dir=Path("./data/test-uploads"),
        max_upload_size_bytes=10485760,
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        retrieval_semantic_top_k=12,
        retrieval_lexical_top_k=12,
        retrieval_final_top_k=6,
        retrieval_semantic_weight=0.6,
        retrieval_lexical_weight=0.4,
        retrieval_min_citation_confidence_score=0.35,
        qa_min_context_chunks=1,
        qa_min_fused_score=0.05,
    )
    with pytest.raises(ValueError, match="Unsupported DOCUMENT_ACCESS_POLICY_BACKEND"):
        build_container(unknown_settings)
