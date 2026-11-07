from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessContext:
    user_id: str | None
    allowed_document_ids: frozenset[str] | None
