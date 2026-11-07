from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.domain.models import DocumentChunk, ParsedDocument, ParsedTextBlock


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size_chars: int
    chunk_overlap_chars: int


class ChunkingService:
    def __init__(self, config: ChunkingConfig) -> None:
        if config.chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars must be positive")
        if config.chunk_overlap_chars < 0:
            raise ValueError("chunk_overlap_chars must be non-negative")
        if config.chunk_overlap_chars >= config.chunk_size_chars:
            raise ValueError("chunk_overlap_chars must be less than chunk_size_chars")
        self._config = config

    def chunk_document(self, parsed_document: ParsedDocument) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        text_buffer = ""
        block_refs: list[ParsedTextBlock] = []

        for block in parsed_document.blocks:
            candidates = self._split_block_text(block)
            for segment in candidates:
                segment_text = segment.text.strip()
                if not segment_text:
                    continue
                tentative = segment_text if not text_buffer else f"{text_buffer}\n\n{segment_text}"
                if len(tentative) <= self._config.chunk_size_chars:
                    text_buffer = tentative
                    block_refs.append(segment)
                else:
                    if text_buffer:
                        chunks.append(self._build_chunk(parsed_document, text_buffer, block_refs))
                        overlap = text_buffer[-self._config.chunk_overlap_chars :]
                        text_buffer = overlap.strip()
                        block_refs = block_refs[-1:] if block_refs else []

                    if len(segment_text) > self._config.chunk_size_chars:
                        chunks.extend(self._split_long_segment(parsed_document, segment))
                        text_buffer = ""
                        block_refs = []
                    else:
                        text_buffer = segment_text
                        block_refs = [segment]

        if text_buffer:
            chunks.append(self._build_chunk(parsed_document, text_buffer, block_refs))

        return chunks

    def _split_block_text(self, block: ParsedTextBlock) -> list[ParsedTextBlock]:
        parts = [part.strip() for part in block.text.split("\n\n") if part.strip()]
        if not parts:
            return []
        return [
            ParsedTextBlock(
                text=part,
                page_ref=block.page_ref,
                metadata=dict(block.metadata),
            )
            for part in parts
        ]

    def _split_long_segment(
        self,
        parsed_document: ParsedDocument,
        segment: ParsedTextBlock,
    ) -> list[DocumentChunk]:
        text = segment.text
        start = 0
        output: list[DocumentChunk] = []

        while start < len(text):
            end = min(start + self._config.chunk_size_chars, len(text))
            slice_text = text[start:end].strip()
            if slice_text:
                output.append(
                    self._build_chunk(
                        parsed_document=parsed_document,
                        chunk_text=slice_text,
                        blocks=[segment],
                    )
                )
            if end == len(text):
                break
            start = max(end - self._config.chunk_overlap_chars, start + 1)
        return output

    def _build_chunk(
        self,
        parsed_document: ParsedDocument,
        chunk_text: str,
        blocks: list[ParsedTextBlock],
    ) -> DocumentChunk:
        page_ref = blocks[0].page_ref if blocks else None
        metadata = {
            "parser": parsed_document.metadata.get("parser", "unknown"),
            "block_count": str(len(blocks)),
            "char_length": str(len(chunk_text)),
        }
        if page_ref:
            metadata["page_ref"] = page_ref
        return DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=parsed_document.document_id,
            document_name=parsed_document.document_name,
            text=chunk_text,
            page_ref=page_ref,
            metadata=metadata,
        )

