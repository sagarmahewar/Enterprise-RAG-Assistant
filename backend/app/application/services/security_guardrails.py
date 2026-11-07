from __future__ import annotations

import re
from collections.abc import Mapping

from app.domain.models import DocumentChunk

_PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal system prompt",
    "show system prompt",
    "developer message",
    "act as system",
    "<system>",
    "</system>",
    "tool call",
    "jailbreak",
)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_WHITESPACE_RE = re.compile(r"\s+")


def validate_user_query(
    query: str,
    *,
    min_chars: int = 1,
    max_chars: int = 2000,
) -> str:
    normalized = normalize_text(query)
    if len(normalized) < min_chars:
        raise ValueError("Query text cannot be empty")
    if len(normalized) > max_chars:
        raise ValueError(f"Query text exceeds max allowed length ({max_chars})")
    lower = normalized.lower()
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern in lower:
            raise ValueError("Query rejected by security policy")
    return normalized


def normalize_text(value: str) -> str:
    without_controls = _CONTROL_CHARS_RE.sub(" ", value)
    return _WHITESPACE_RE.sub(" ", without_controls).strip()


def validate_metadata_filter(
    metadata_filter: Mapping[str, str] | None,
    *,
    max_items: int = 10,
    max_key_chars: int = 64,
    max_value_chars: int = 256,
) -> None:
    if metadata_filter is None:
        return
    if len(metadata_filter) > max_items:
        raise ValueError(f"metadata_filter exceeds max allowed size ({max_items})")
    for key, value in metadata_filter.items():
        if not key or len(key) > max_key_chars:
            raise ValueError("metadata_filter contains invalid key")
        if len(value) > max_value_chars:
            raise ValueError("metadata_filter contains invalid value")


def sanitize_chunk_for_prompt(chunk: DocumentChunk, *, max_chars: int = 1800) -> DocumentChunk:
    lowered = chunk.text.lower()
    redacted_text = chunk.text
    if any(pattern in lowered for pattern in _PROMPT_INJECTION_PATTERNS):
        redacted_text = "[redacted potential prompt-injection instructions from source document]"
    normalized = normalize_text(redacted_text)[:max_chars]
    return DocumentChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        document_name=chunk.document_name,
        text=normalized,
        page_ref=chunk.page_ref,
        metadata=dict(chunk.metadata),
        embedding=chunk.embedding,
        score=chunk.score,
    )


def to_public_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
    blocked_keys = {"stored_path", "file_sha256"}
    return {key: value for key, value in metadata.items() if key not in blocked_keys}
