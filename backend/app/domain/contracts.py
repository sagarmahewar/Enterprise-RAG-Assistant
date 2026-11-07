from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from app.domain.models import DocumentChunk, ParsedDocument
from app.domain.security import AccessContext


@runtime_checkable
class EmbeddingProvider(Protocol):
    provider_name: str

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...


@runtime_checkable
class LLMProvider(Protocol):
    provider_name: str

    def generate_answer(self, query: str, context_chunks: Sequence[DocumentChunk]) -> str:
        ...


@runtime_checkable
class VectorStore(Protocol):
    provider_name: str

    def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        ...

    def query(
        self,
        query_vector: Sequence[float],
        top_k: int,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[DocumentChunk]:
        ...


@runtime_checkable
class Reranker(Protocol):
    provider_name: str

    def rerank(
        self, query: str, candidates: Sequence[DocumentChunk], top_k: int
    ) -> list[DocumentChunk]:
        ...


@runtime_checkable
class DocumentParser(Protocol):
    provider_name: str

    def supported_mime_types(self) -> set[str]:
        ...

    def parse(self, document_id: str, document_name: str, content: bytes) -> ParsedDocument:
        ...


@runtime_checkable
class DocumentAccessPolicy(Protocol):
    provider_name: str

    def authorize_upload(self, context: AccessContext, document_name: str) -> None:
        ...

    def authorize_document_ids(
        self,
        context: AccessContext,
        requested_document_ids: Sequence[str] | None,
    ) -> list[str] | None:
        ...

    def filter_visible_documents(
        self,
        context: AccessContext,
        documents: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        ...
