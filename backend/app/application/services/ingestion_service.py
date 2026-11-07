from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.application.container import ProviderContainer
from app.application.services.chunking_service import ChunkingConfig, ChunkingService
from app.domain.models import DocumentChunk
from app.infrastructure.repositories.sqlite_metadata import SqliteMetadataRepository


@dataclass(frozen=True)
class IngestionResult:
    document_id: str
    document_name: str
    mime_type: str
    size_bytes: int
    chunk_count: int
    parser_name: str


class IngestionService:
    def __init__(
        self,
        container: ProviderContainer,
        metadata_db_path: Path,
        upload_directory: Path,
        max_upload_size_bytes: int,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> None:
        self._container = container
        self._metadata_repo = SqliteMetadataRepository(metadata_db_path)
        self._upload_directory = upload_directory
        self._upload_directory.mkdir(parents=True, exist_ok=True)
        self._max_upload_size_bytes = max_upload_size_bytes
        self._chunking_service = ChunkingService(
            ChunkingConfig(
                chunk_size_chars=chunk_size_chars,
                chunk_overlap_chars=chunk_overlap_chars,
            )
        )

    def ingest(
        self,
        *,
        document_name: str,
        mime_type: str,
        content: bytes,
    ) -> IngestionResult:
        byte_size = len(content)
        if byte_size == 0:
            raise ValueError("Uploaded file is empty")
        if byte_size > self._max_upload_size_bytes:
            raise ValueError("Uploaded file exceeds max allowed size")

        parser = self._container.parser_for_mime(mime_type)
        if not parser:
            raise ValueError(f"Unsupported mime type: {mime_type}")

        document_id = str(uuid4())
        stored_filename = f"{document_id}-{document_name}"
        stored_path = self._upload_directory / stored_filename
        stored_path.write_bytes(content)

        parsed = parser.parse(
            document_id=document_id,
            document_name=document_name,
            content=content,
        )

        chunks = self._chunking_service.chunk_document(parsed)
        if not chunks:
            raise ValueError("No text could be extracted from document")
        vectors = self._container.embedding_provider.embed_texts([chunk.text for chunk in chunks])
        if len(vectors) != len(chunks):
            raise ValueError("Embedding provider returned mismatched vector count")
        file_hash = hashlib.sha256(content).hexdigest()
        chunks_with_vectors = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunks_with_vectors.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    text=chunk.text,
                    page_ref=chunk.page_ref,
                    metadata={
                        **chunk.metadata,
                        "file_sha256": file_hash,
                        "stored_path": str(stored_path),
                    },
                    embedding=vector,
                )
            )

        self._container.vector_store.upsert_chunks(chunks_with_vectors)
        self._metadata_repo.save_document(parsed, byte_size=byte_size)
        self._metadata_repo.save_chunks(chunks_with_vectors)

        return IngestionResult(
            document_id=document_id,
            document_name=document_name,
            mime_type=mime_type,
            size_bytes=byte_size,
            chunk_count=len(chunks_with_vectors),
            parser_name=parser.provider_name,
        )

    def list_documents(self) -> list[dict[str, object]]:
        return self._metadata_repo.list_documents()
