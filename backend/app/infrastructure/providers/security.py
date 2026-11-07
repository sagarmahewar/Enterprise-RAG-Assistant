from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.domain.security import AccessContext


class AllowAllDocumentAccessPolicy:
    def __init__(self, provider_name: str = "allow-all-document-access") -> None:
        self.provider_name = provider_name

    def authorize_upload(self, context: AccessContext, document_name: str) -> None:
        del context, document_name

    def authorize_document_ids(
        self,
        context: AccessContext,
        requested_document_ids: Sequence[str] | None,
    ) -> list[str] | None:
        del context
        if requested_document_ids is None:
            return None
        return list(requested_document_ids)

    def filter_visible_documents(
        self,
        context: AccessContext,
        documents: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        del context
        return [dict(document) for document in documents]


class HeaderAllowlistDocumentAccessPolicy:
    def __init__(self, provider_name: str = "header-allowlist-document-access") -> None:
        self.provider_name = provider_name

    def authorize_upload(self, context: AccessContext, document_name: str) -> None:
        del context, document_name

    def authorize_document_ids(
        self,
        context: AccessContext,
        requested_document_ids: Sequence[str] | None,
    ) -> list[str] | None:
        allowed = context.allowed_document_ids
        if requested_document_ids is None:
            return None
        requested = list(requested_document_ids)
        if not allowed:
            return requested
        for document_id in requested:
            if document_id not in allowed:
                raise PermissionError("requested document is not allowed for this caller")
        return requested

    def filter_visible_documents(
        self,
        context: AccessContext,
        documents: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        allowed = context.allowed_document_ids
        if not allowed:
            return [dict(document) for document in documents]

        visible: list[dict[str, object]] = []
        for document in documents:
            document_id = document.get("document_id")
            if isinstance(document_id, str) and document_id in allowed:
                visible.append(dict(document))
        return visible
