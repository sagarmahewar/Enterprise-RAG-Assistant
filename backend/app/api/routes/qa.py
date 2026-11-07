from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.security import build_access_context, validate_document_ids, validate_request_filter
from app.application.container import get_container
from app.application.services.citation_confidence import build_citation_confidence
from app.application.services.qa_service import QAConfig, QAService
from app.application.services.retrieval_service import HybridRetrievalConfig, RetrievalService
from app.application.services.security_guardrails import to_public_metadata
from app.core.observability import emit_event, get_request_id
from app.core.settings import settings
from app.domain.contracts import DocumentAccessPolicy
from app.domain.security import AccessContext

router = APIRouter()


class QAAskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[str] | None = Field(default=None, max_length=50)
    metadata_filter: dict[str, str] | None = Field(default=None, max_length=10)


def _retrieval_service() -> RetrievalService:
    return RetrievalService(
        container=get_container(),
        metadata_db_path=settings.metadata_db_path,
        config=HybridRetrievalConfig(
            semantic_top_k=settings.retrieval_semantic_top_k,
            lexical_top_k=settings.retrieval_lexical_top_k,
            final_top_k=settings.retrieval_final_top_k,
            semantic_weight=settings.retrieval_semantic_weight,
            lexical_weight=settings.retrieval_lexical_weight,
        ),
    )


def _qa_service() -> QAService:
    container = get_container()
    return QAService(
        retrieval_service=_retrieval_service(),
        llm_provider=container.llm_provider,
        config=QAConfig(
            min_context_chunks=settings.qa_min_context_chunks,
            min_fused_score=settings.qa_min_fused_score,
        ),
    )


def _document_access_policy() -> DocumentAccessPolicy:
    return get_container().document_access_policy


def _authorized_document_ids(
    context: AccessContext,
    requested_document_ids: list[str] | None,
) -> list[str] | None:
    validate_document_ids(requested_document_ids)
    return _document_access_policy().authorize_document_ids(context, requested_document_ids)


def _safe_metadata_filter(metadata_filter: dict[str, str] | None) -> dict[str, str] | None:
    validate_request_filter(metadata_filter)
    return metadata_filter


def _citation_payload(chunk_score: float | None, threshold: float) -> dict[str, object]:
    confidence = build_citation_confidence(chunk_score, threshold)
    return {
        "confidence_score": confidence.score,
        "confidence_label": confidence.label,
        "meets_confidence_threshold": confidence.meets_threshold,
    }


@router.post("/qa/ask")
def ask_question(
    request_http: Request,
    request: QAAskRequest,
    access_context: Annotated[AccessContext, Depends(build_access_context)],
) -> dict[str, object]:
    request_id = get_request_id(request_http)
    try:
        document_ids = _authorized_document_ids(access_context, request.document_ids)
        metadata_filter = _safe_metadata_filter(request.metadata_filter)
        result = _qa_service().ask(
            query=request.query,
            top_k=request.top_k,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )
    except PermissionError as error:
        emit_event("qa.denied", request_id=request_id)
        raise HTTPException(status_code=403, detail="Access denied") from error
    except ValueError as error:
        emit_event("qa.rejected", request_id=request_id)
        raise HTTPException(status_code=400, detail=str(error)) from error

    threshold = settings.retrieval_min_citation_confidence_score
    emit_event(
        "qa.completed",
        request_id=request_id,
        query_length=len(request.query),
        citation_count=len(result.citations),
        chunk_count=len(result.retrieved_chunks),
        insufficient_context=result.insufficient_context,
    )
    return {
        "query": result.query,
        "answer": result.answer,
        "insufficient_context": result.insufficient_context,
        "citation_confidence_threshold": threshold,
        "citations": [
            {
                "document_id": citation.document_id,
                "document_name": citation.document_name,
                "chunk_id": citation.chunk_id,
                "page_ref": citation.page_ref,
                "score": citation.score,
                **_citation_payload(citation.score, threshold),
            }
            for citation in result.citations
        ],
        "retrieved_chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_ref": chunk.page_ref,
                "text": chunk.text,
                "score": chunk.score,
                "metadata": to_public_metadata(chunk.metadata),
            }
            for chunk in result.retrieved_chunks
        ],
        "total_chunks": len(result.retrieved_chunks),
    }
