from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.application.container import ProviderContainer
from app.application.services.security_guardrails import (
    validate_metadata_filter,
    validate_user_query,
)
from app.domain.models import DocumentChunk
from app.infrastructure.repositories.sqlite_metadata import SqliteMetadataRepository


@dataclass(frozen=True)
class HybridRetrievalConfig:
    semantic_top_k: int
    lexical_top_k: int
    final_top_k: int
    semantic_weight: float
    lexical_weight: float


class RetrievalService:
    def __init__(
        self,
        container: ProviderContainer,
        metadata_db_path: Path,
        config: HybridRetrievalConfig,
    ) -> None:
        self._container = container
        self._metadata_repo = SqliteMetadataRepository(metadata_db_path)
        self._config = config

    def retrieve(
        self,
        *,
        query: str,
        top_k: int | None = None,
        document_ids: Sequence[str] | None = None,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[DocumentChunk]:
        trimmed_query = validate_user_query(query)
        validate_metadata_filter(metadata_filter)

        effective_top_k = top_k if top_k is not None else self._config.final_top_k
        if effective_top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if effective_top_k > 20:
            raise ValueError("top_k exceeds max allowed value (20)")
        if document_ids and len(document_ids) > 50:
            raise ValueError("document_ids exceeds max allowed size (50)")

        query_vector = self._container.embedding_provider.embed_texts([trimmed_query])[0]
        semantic_candidates = self._container.vector_store.query(
            query_vector=query_vector,
            top_k=self._config.semantic_top_k,
            metadata_filter=metadata_filter,
        )
        lexical_candidates = self._metadata_repo.search_chunks_lexical(
            query=trimmed_query,
            top_k=self._config.lexical_top_k,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )

        filtered_semantic = self._apply_filters(
            chunks=semantic_candidates,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )
        filtered_lexical = self._apply_filters(
            chunks=lexical_candidates,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )

        fused = self._fuse_scores(
            semantic_chunks=filtered_semantic,
            lexical_chunks=filtered_lexical,
        )
        candidate_pool_size = max(effective_top_k * 3, effective_top_k)
        fused_ranked = sorted(
            fused,
            key=lambda chunk: chunk.score or 0.0,
            reverse=True,
        )
        fused = fused_ranked[:candidate_pool_size]
        reranked = self._container.reranker.rerank(trimmed_query, fused, top_k=effective_top_k)
        return reranked

    def _apply_filters(
        self,
        *,
        chunks: Sequence[DocumentChunk],
        document_ids: Sequence[str] | None,
        metadata_filter: Mapping[str, str] | None,
    ) -> list[DocumentChunk]:
        output: list[DocumentChunk] = []
        for chunk in chunks:
            if document_ids and chunk.document_id not in document_ids:
                continue
            if metadata_filter and not self._matches_metadata(chunk, metadata_filter):
                continue
            output.append(chunk)
        return output

    def _matches_metadata(self, chunk: DocumentChunk, metadata_filter: Mapping[str, str]) -> bool:
        for key, value in metadata_filter.items():
            if key == "document_id" and chunk.document_id != value:
                return False
            if key == "document_name" and chunk.document_name != value:
                return False
            if key not in {"document_id", "document_name"} and chunk.metadata.get(key) != value:
                return False
        return True

    def _fuse_scores(
        self,
        *,
        semantic_chunks: Sequence[DocumentChunk],
        lexical_chunks: Sequence[DocumentChunk],
    ) -> list[DocumentChunk]:
        semantic_norm = _min_max_normalize(semantic_chunks)
        lexical_norm = _min_max_normalize(lexical_chunks)

        all_chunk_ids = set(semantic_norm.keys()) | set(lexical_norm.keys())
        index: dict[str, DocumentChunk] = {
            chunk.chunk_id: chunk for chunk in [*semantic_chunks, *lexical_chunks]
        }

        fused: list[DocumentChunk] = []
        for chunk_id in all_chunk_ids:
            semantic_score = semantic_norm.get(chunk_id, 0.0)
            lexical_score = lexical_norm.get(chunk_id, 0.0)
            fused_score = (
                self._config.semantic_weight * semantic_score
                + self._config.lexical_weight * lexical_score
            )
            chunk = index[chunk_id]
            fused.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    text=chunk.text,
                    page_ref=chunk.page_ref,
                    metadata={
                        **chunk.metadata,
                        "semantic_score": f"{semantic_score:.6f}",
                        "lexical_score": f"{lexical_score:.6f}",
                        "fused_score": f"{fused_score:.6f}",
                    },
                    embedding=chunk.embedding,
                    score=fused_score,
                )
            )
        return fused


def _min_max_normalize(chunks: Sequence[DocumentChunk]) -> dict[str, float]:
    if not chunks:
        return {}
    raw_scores = [chunk.score or 0.0 for chunk in chunks]
    minimum = min(raw_scores)
    maximum = max(raw_scores)
    if maximum == minimum:
        return {chunk.chunk_id: 1.0 for chunk in chunks}
    return {
        chunk.chunk_id: ((chunk.score or 0.0) - minimum) / (maximum - minimum)
        for chunk in chunks
    }
