"""Phase 0 settings scaffold.

This keeps configuration typed and centralized while avoiding framework coupling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _parse_csv(value: str) -> list[str]:
    items = [part.strip() for part in value.split(",")]
    return [item for item in items if item]


def _parse_positive_int(value: str, env_key: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{env_key} must be a positive integer")
    return parsed


def _parse_non_negative_float(value: str, env_key: str) -> float:
    parsed = float(value)
    if parsed < 0.0:
        raise ValueError(f"{env_key} must be non-negative")
    return parsed


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    api_v1_prefix: str
    cors_origins: tuple[str, ...]
    llm_provider_backend: str
    embedding_provider_backend: str
    vector_store_backend: str
    reranker_backend: str
    document_access_policy_backend: str
    ollama_base_url: str
    ollama_llm_model: str
    ollama_embedding_model: str
    ollama_request_timeout_seconds: int
    groq_base_url: str
    groq_api_key: str
    groq_llm_model: str
    groq_embedding_model: str
    groq_temperature: float
    groq_max_tokens: int
    groq_request_timeout_seconds: int
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str
    qdrant_timeout_seconds: int
    metadata_db_path: Path
    upload_dir: Path
    max_upload_size_bytes: int
    chunk_size_chars: int
    chunk_overlap_chars: int
    retrieval_semantic_top_k: int
    retrieval_lexical_top_k: int
    retrieval_final_top_k: int
    retrieval_semantic_weight: float
    retrieval_lexical_weight: float
    retrieval_min_citation_confidence_score: float
    qa_min_context_chunks: int
    qa_min_fused_score: float
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_request_timeout_seconds: int = 60

    @staticmethod
    def from_env() -> Settings:
        app_name = os.getenv("APP_NAME", "Enterprise RAG Assistant API")
        app_env = os.getenv("APP_ENV", "development")
        api_v1_prefix = os.getenv("API_V1_PREFIX", "/api/v1")
        cors_csv = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        cors_origins = tuple(_parse_csv(cors_csv))
        llm_provider_backend = os.getenv("LLM_PROVIDER_BACKEND", "ollama")
        embedding_provider_backend = os.getenv("EMBEDDING_PROVIDER_BACKEND", "ollama")
        vector_store_backend = os.getenv("VECTOR_STORE_BACKEND", "local-fake-vector-store")
        reranker_backend = os.getenv("RERANKER_BACKEND", "local-fake-reranker")
        document_access_policy_backend = os.getenv("DOCUMENT_ACCESS_POLICY_BACKEND", "allow-all")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_llm_model = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:14b")
        ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        ollama_request_timeout_seconds = _parse_positive_int(
            os.getenv("OLLAMA_REQUEST_TIMEOUT_SECONDS", "90"),
            "OLLAMA_REQUEST_TIMEOUT_SECONDS",
        )
        groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        groq_llm_model = os.getenv("GROQ_LLM_MODEL", "llama-3.1-8b-instant")
        groq_embedding_model = os.getenv(
            "GROQ_EMBEDDING_MODEL",
            "nomic-embed-text-v1.5",
        )
        groq_temperature = _parse_non_negative_float(
            os.getenv("GROQ_TEMPERATURE", "0.1"),
            "GROQ_TEMPERATURE",
        )
        if groq_temperature > 2:
            raise ValueError("GROQ_TEMPERATURE must be between 0 and 2")
        groq_max_tokens = _parse_positive_int(
            os.getenv("GROQ_MAX_TOKENS", "1024"),
            "GROQ_MAX_TOKENS",
        )
        groq_request_timeout_seconds = _parse_positive_int(
            os.getenv("GROQ_REQUEST_TIMEOUT_SECONDS", "60"),
            "GROQ_REQUEST_TIMEOUT_SECONDS",
        )
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        qdrant_collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_chunks_local")
        qdrant_timeout_seconds = _parse_positive_int(
            os.getenv("QDRANT_TIMEOUT_SECONDS", "30"),
            "QDRANT_TIMEOUT_SECONDS",
        )
        metadata_db_path = Path(os.getenv("METADATA_DB_PATH", "./data/metadata.db"))
        upload_dir = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
        max_upload_size_bytes = _parse_positive_int(
            os.getenv("MAX_UPLOAD_SIZE_BYTES", "10485760"),
            "MAX_UPLOAD_SIZE_BYTES",
        )
        chunk_size_chars = _parse_positive_int(
            os.getenv("CHUNK_SIZE_CHARS", "1200"),
            "CHUNK_SIZE_CHARS",
        )
        chunk_overlap_chars = _parse_positive_int(
            os.getenv("CHUNK_OVERLAP_CHARS", "200"),
            "CHUNK_OVERLAP_CHARS",
        )
        if chunk_overlap_chars >= chunk_size_chars:
            raise ValueError("CHUNK_OVERLAP_CHARS must be less than CHUNK_SIZE_CHARS")
        retrieval_semantic_top_k = _parse_positive_int(
            os.getenv("RETRIEVAL_SEMANTIC_TOP_K", "12"),
            "RETRIEVAL_SEMANTIC_TOP_K",
        )
        retrieval_lexical_top_k = _parse_positive_int(
            os.getenv("RETRIEVAL_LEXICAL_TOP_K", "12"),
            "RETRIEVAL_LEXICAL_TOP_K",
        )
        retrieval_final_top_k = _parse_positive_int(
            os.getenv("RETRIEVAL_FINAL_TOP_K", "6"),
            "RETRIEVAL_FINAL_TOP_K",
        )
        retrieval_semantic_weight = _parse_non_negative_float(
            os.getenv("RETRIEVAL_SEMANTIC_WEIGHT", "0.6"),
            "RETRIEVAL_SEMANTIC_WEIGHT",
        )
        retrieval_lexical_weight = _parse_non_negative_float(
            os.getenv("RETRIEVAL_LEXICAL_WEIGHT", "0.4"),
            "RETRIEVAL_LEXICAL_WEIGHT",
        )
        if retrieval_semantic_weight + retrieval_lexical_weight <= 0:
            raise ValueError(
                "RETRIEVAL_SEMANTIC_WEIGHT + RETRIEVAL_LEXICAL_WEIGHT must be greater than 0"
            )
        retrieval_min_citation_confidence_score = _parse_non_negative_float(
            os.getenv("RETRIEVAL_MIN_CITATION_CONFIDENCE_SCORE", "0.35"),
            "RETRIEVAL_MIN_CITATION_CONFIDENCE_SCORE",
        )
        if retrieval_min_citation_confidence_score > 1:
            raise ValueError("RETRIEVAL_MIN_CITATION_CONFIDENCE_SCORE must be between 0 and 1")
        qa_min_context_chunks = _parse_positive_int(
            os.getenv("QA_MIN_CONTEXT_CHUNKS", "1"),
            "QA_MIN_CONTEXT_CHUNKS",
        )
        qa_min_fused_score = _parse_non_negative_float(
            os.getenv("QA_MIN_FUSED_SCORE", "0.05"),
            "QA_MIN_FUSED_SCORE",
        )
        if qa_min_fused_score > 1:
            raise ValueError("QA_MIN_FUSED_SCORE must be between 0 and 1")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        openai_embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        openai_request_timeout_seconds = _parse_positive_int(
            os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "60"),
            "OPENAI_REQUEST_TIMEOUT_SECONDS",
        )

        return Settings(
            app_name=app_name,
            app_env=app_env,
            api_v1_prefix=api_v1_prefix,
            cors_origins=cors_origins,
            llm_provider_backend=llm_provider_backend,
            embedding_provider_backend=embedding_provider_backend,
            vector_store_backend=vector_store_backend,
            reranker_backend=reranker_backend,
            document_access_policy_backend=document_access_policy_backend,
            ollama_base_url=ollama_base_url,
            ollama_llm_model=ollama_llm_model,
            ollama_embedding_model=ollama_embedding_model,
            ollama_request_timeout_seconds=ollama_request_timeout_seconds,
            groq_base_url=groq_base_url,
            groq_api_key=groq_api_key,
            groq_llm_model=groq_llm_model,
            groq_embedding_model=groq_embedding_model,
            groq_temperature=groq_temperature,
            groq_max_tokens=groq_max_tokens,
            groq_request_timeout_seconds=groq_request_timeout_seconds,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            qdrant_collection_name=qdrant_collection_name,
            qdrant_timeout_seconds=qdrant_timeout_seconds,
            metadata_db_path=metadata_db_path,
            upload_dir=upload_dir,
            max_upload_size_bytes=max_upload_size_bytes,
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            retrieval_semantic_top_k=retrieval_semantic_top_k,
            retrieval_lexical_top_k=retrieval_lexical_top_k,
            retrieval_final_top_k=retrieval_final_top_k,
            retrieval_semantic_weight=retrieval_semantic_weight,
            retrieval_lexical_weight=retrieval_lexical_weight,
            retrieval_min_citation_confidence_score=retrieval_min_citation_confidence_score,
            qa_min_context_chunks=qa_min_context_chunks,
            qa_min_fused_score=qa_min_fused_score,
            openai_base_url=openai_base_url,
            openai_api_key=openai_api_key,
            openai_embedding_model=openai_embedding_model,
            openai_request_timeout_seconds=openai_request_timeout_seconds,
        )


settings = Settings.from_env()
