from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated

from fastapi import Header

from app.application.services.security_guardrails import validate_metadata_filter
from app.domain.security import AccessContext

_MAX_FILENAME_CHARS = 255


def build_access_context(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    x_allowed_document_ids: Annotated[str | None, Header(alias="X-Allowed-Document-Ids")] = None,
) -> AccessContext:
    allowed: frozenset[str] | None = None
    if x_allowed_document_ids:
        values = [part.strip() for part in x_allowed_document_ids.split(",")]
        normalized = [value for value in values if value]
        allowed = frozenset(normalized)
    return AccessContext(user_id=x_user_id, allowed_document_ids=allowed)


def normalize_upload_filename(filename: str) -> str:
    normalized = Path(filename).name.strip()
    if not normalized:
        raise ValueError("filename is required")
    if len(normalized) > _MAX_FILENAME_CHARS:
        raise ValueError(f"filename exceeds max allowed length ({_MAX_FILENAME_CHARS})")
    return normalized


def validate_document_ids(document_ids: Sequence[str] | None) -> None:
    if document_ids is None:
        return
    if len(document_ids) > 50:
        raise ValueError("document_ids exceeds max allowed size (50)")
    for document_id in document_ids:
        normalized = document_id.strip()
        if not normalized:
            raise ValueError("document_ids contains empty value")
        if len(normalized) > 128:
            raise ValueError("document_ids contains invalid value")


def validate_request_filter(metadata_filter: Mapping[str, str] | None) -> None:
    validate_metadata_filter(metadata_filter)
