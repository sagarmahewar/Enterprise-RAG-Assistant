from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.api.security import (
    build_access_context,
    normalize_upload_filename,
    validate_document_ids,
    validate_request_filter,
)
from app.application.container import get_container
from app.application.services.citation_confidence import build_citation_confidence
from app.application.services.ingestion_service import IngestionService
from app.application.services.retrieval_service import HybridRetrievalConfig, RetrievalService
from app.application.services.security_guardrails import to_public_metadata
from app.core.observability import emit_event, get_request_id
from app.core.settings import settings
from app.domain.contracts import DocumentAccessPolicy
from app.domain.models import DocumentChunk
from app.domain.security import AccessContext

router = APIRouter()

_MIME_BY_EXTENSION = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _detect_mime(filename: str, declared_mime: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    expected_mime = _MIME_BY_EXTENSION.get(suffix)
    if expected_mime is None:
        raise ValueError("Unsupported file extension")
    if (
        declared_mime
        and declared_mime in _MIME_BY_EXTENSION.values()
        and declared_mime != expected_mime
    ):
        raise ValueError("Declared mime type does not match file extension")
    if declared_mime and declared_mime not in _MIME_BY_EXTENSION.values():
        raise ValueError("Unsupported declared mime type")
    return expected_mime


def _ingestion_service() -> IngestionService:
    return IngestionService(
        container=get_container(),
        metadata_db_path=settings.metadata_db_path,
        upload_directory=settings.upload_dir,
        max_upload_size_bytes=settings.max_upload_size_bytes,
        chunk_size_chars=settings.chunk_size_chars,
        chunk_overlap_chars=settings.chunk_overlap_chars,
    )


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


def _citation_payload(chunk_score: float | None, threshold: float) -> dict[str, object]:
    confidence = build_citation_confidence(chunk_score, threshold)
    return {
        "confidence_score": confidence.score,
        "confidence_label": confidence.label,
        "meets_confidence_threshold": confidence.meets_threshold,
    }


def _document_access_policy() -> DocumentAccessPolicy:
    return get_container().document_access_policy


def _authorized_document_ids(
    context: AccessContext,
    requested_document_ids: list[str] | None,
) -> list[str] | None:
    validate_document_ids(requested_document_ids)
    return _document_access_policy().authorize_document_ids(context, requested_document_ids)


def _safe_query_text(query: str) -> str:
    if len(query) > 2000:
        raise ValueError("Query text exceeds max allowed length (2000)")
    return query


def _safe_metadata_filter(metadata_filter: dict[str, str] | None) -> dict[str, str] | None:
    validate_request_filter(metadata_filter)
    return metadata_filter


def _safe_top_k(top_k: int | None) -> int | None:
    if top_k is not None and top_k > 20:
        raise ValueError("top_k exceeds max allowed value (20)")
    return top_k


def _public_document_rows(documents: list[dict[str, object]]) -> list[dict[str, object]]:
    return documents


def _public_chunk_payload(chunk: DocumentChunk) -> dict[str, object]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_name": chunk.document_name,
        "page_ref": chunk.page_ref,
        "text": chunk.text,
        "score": chunk.score,
        "metadata": to_public_metadata(chunk.metadata),
    }


def _safe_upload_filename(filename: str) -> str:
    return normalize_upload_filename(filename)


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[str] | None = Field(default=None, max_length=50)
    metadata_filter: dict[str, str] | None = Field(default=None, max_length=10)


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    access_context: Annotated[AccessContext, Depends(build_access_context)],
) -> dict[str, object]:
    request_id = get_request_id(request)
    try:
        safe_filename = _safe_upload_filename(file.filename or "")
        _document_access_policy().authorize_upload(access_context, safe_filename)
    except PermissionError as error:
        emit_event("upload.denied", request_id=request_id)
        raise HTTPException(status_code=403, detail="Access denied") from error
    except ValueError as error:
        emit_event("upload.rejected", request_id=request_id)
        raise HTTPException(status_code=400, detail=str(error)) from error

    raw_content = await file.read()

    try:
        mime_type = _detect_mime(safe_filename, file.content_type)
        result = _ingestion_service().ingest(
            document_name=safe_filename,
            mime_type=mime_type,
            content=raw_content,
        )
    except ValueError as error:
        emit_event("upload.failed", request_id=request_id)
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()

    emit_event(
        "upload.completed",
        request_id=request_id,
        document_id=result.document_id,
        filename=result.document_name,
        mime_type=result.mime_type,
        chunk_count=result.chunk_count,
    )
    return {
        "document_id": result.document_id,
        "document_name": result.document_name,
        "mime_type": result.mime_type,
        "size_bytes": result.size_bytes,
        "chunk_count": result.chunk_count,
        "parser_name": result.parser_name,
    }


@router.get("/documents")
def list_documents(
    request: Request,
    access_context: Annotated[AccessContext, Depends(build_access_context)],
) -> dict[str, object]:
    request_id = get_request_id(request)
    documents = _ingestion_service().list_documents()
    visible_documents = _document_access_policy().filter_visible_documents(
        access_context,
        documents,
    )
    emit_event(
        "documents.listed",
        request_id=request_id,
        total_documents=len(documents),
        visible_documents=len(visible_documents),
    )
    return {"documents": _public_document_rows(visible_documents)}


@router.post("/retrieval/search")
def retrieval_search(
    request_http: Request,
    request: RetrievalRequest,
    access_context: Annotated[AccessContext, Depends(build_access_context)],
) -> dict[str, object]:
    request_id = get_request_id(request_http)
    try:
        top_k = _safe_top_k(request.top_k)
        query = _safe_query_text(request.query)
        metadata_filter = _safe_metadata_filter(request.metadata_filter)
        document_ids = _authorized_document_ids(access_context, request.document_ids)
        chunks = _retrieval_service().retrieve(
            query=query,
            top_k=top_k,
            document_ids=document_ids,
            metadata_filter=metadata_filter,
        )
    except PermissionError as error:
        emit_event("retrieval.denied", request_id=request_id)
        raise HTTPException(status_code=403, detail="Access denied") from error
    except ValueError as error:
        emit_event("retrieval.rejected", request_id=request_id)
        raise HTTPException(status_code=400, detail=str(error)) from error

    threshold = settings.retrieval_min_citation_confidence_score
    emit_event(
        "retrieval.completed",
        request_id=request_id,
        query_length=len(request.query),
        top_k=top_k,
        result_count=len(chunks),
    )
    return {
        "query": request.query,
        "citation_confidence_threshold": threshold,
        "results": [
            {
                **_public_chunk_payload(chunk),
                "citation": {
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                    "page_ref": chunk.page_ref,
                    "chunk_id": chunk.chunk_id,
                    **_citation_payload(chunk.score, threshold),
                },
            }
            for chunk in chunks
        ],
        "total_results": len(chunks),
    }
