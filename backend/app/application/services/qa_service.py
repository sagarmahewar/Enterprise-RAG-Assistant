from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.application.services.retrieval_service import RetrievalService
from app.application.services.security_guardrails import (
    sanitize_chunk_for_prompt,
    validate_user_query,
)
from app.domain.contracts import LLMProvider
from app.domain.models import DocumentChunk

INSUFFICIENT_CONTEXT_FALLBACK = (
    "I don't have enough grounded context to answer this confidently from the uploaded documents."
)


@dataclass(frozen=True)
class QAConfig:
    min_context_chunks: int
    min_fused_score: float


@dataclass(frozen=True)
class QACitation:
    document_id: str
    document_name: str
    chunk_id: str
    page_ref: str | None
    score: float | None


@dataclass(frozen=True)
class QAResult:
    query: str
    answer: str
    insufficient_context: bool
    citations: list[QACitation]
    retrieved_chunks: list[DocumentChunk]


class QAService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: LLMProvider,
        config: QAConfig,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._llm_provider = llm_provider
        self._config = config

    def ask(
        self,
        *,
        query: str,
        top_k: int | None = None,
        document_ids: Sequence[str] | None = None,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> QAResult:
        guarded_query = validate_user_query(query)
        chunks = self._retrieval_service.retrieve(
            query=guarded_query,
            top_k=top_k,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )

        if self._is_insufficient_context(chunks):
            return QAResult(
                query=query,
                answer=INSUFFICIENT_CONTEXT_FALLBACK,
                insufficient_context=True,
                citations=[],
                retrieved_chunks=list(chunks),
            )

        grounded_query = _build_grounded_query(guarded_query)
        safe_prompt_chunks = [sanitize_chunk_for_prompt(chunk) for chunk in chunks]
        answer = self._llm_provider.generate_answer(grounded_query, safe_prompt_chunks)
        citations = [
            QACitation(
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                chunk_id=chunk.chunk_id,
                page_ref=chunk.page_ref,
                score=chunk.score,
            )
            for chunk in chunks
        ]
        return QAResult(
            query=query,
            answer=answer,
            insufficient_context=False,
            citations=citations,
            retrieved_chunks=list(chunks),
        )

    def _is_insufficient_context(self, chunks: Sequence[DocumentChunk]) -> bool:
        if len(chunks) < self._config.min_context_chunks:
            return True
        best_score = max((chunk.score or 0.0) for chunk in chunks)
        return best_score < self._config.min_fused_score


def _build_grounded_query(query: str) -> str:
    return (
        "Grounded-answer policy:\n"
        "1) Use only the provided context chunks.\n"
        "2) Do not invent facts.\n"
        "3) If context is missing, explicitly say it is insufficient.\n\n"
        f"User question:\n{query}"
    )
