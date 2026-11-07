from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    page_ref: str | None
    metadata: dict[str, str]
    embedding: list[float] | None = None
    score: float | None = None


@dataclass(frozen=True)
class ParsedTextBlock:
    text: str
    page_ref: str | None
    metadata: dict[str, str]


@dataclass(frozen=True)
class ParsedDocument:
    document_id: str
    document_name: str
    mime_type: str
    text: str
    blocks: list[ParsedTextBlock]
    metadata: dict[str, str]
