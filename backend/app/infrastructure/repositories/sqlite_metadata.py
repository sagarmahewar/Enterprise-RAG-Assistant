from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.domain.models import DocumentChunk, ParsedDocument


class SqliteMetadataRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    parser_name TEXT NOT NULL,
                    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    page_ref TEXT,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id)
                )
                """
            )

    def save_document(self, parsed: ParsedDocument, byte_size: int) -> None:
        parser_name = parsed.metadata.get("parser", "unknown")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents(document_id, document_name, mime_type, byte_size, parser_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    parsed.document_id,
                    parsed.document_name,
                    parsed.mime_type,
                    byte_size,
                    parser_name,
                ),
            )

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO chunks(
                    chunk_id,
                    document_id,
                    document_name,
                    page_ref,
                    text,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.document_name,
                        chunk.page_ref,
                        chunk.text,
                        json.dumps(chunk.metadata),
                    )
                    for chunk in chunks
                ],
            )

    def list_documents(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT document_id, document_name, mime_type, byte_size, parser_name, ingested_at
                FROM documents
                ORDER BY ingested_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def search_chunks_lexical(
        self,
        query: str,
        top_k: int,
        document_ids: Sequence[str] | None = None,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[DocumentChunk]:
        tokens = [token for token in re.findall(r"[a-z0-9]+", query.lower()) if token]
        if not tokens:
            return []

        where_clauses: list[str] = []
        params: list[object] = []
        if document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            where_clauses.append(f"document_id IN ({placeholders})")
            params.extend(document_ids)
        token_like = " OR ".join("LOWER(text) LIKE ?" for _ in tokens)
        where_clauses.append(f"({token_like})")
        params.extend(f"%{token}%" for token in tokens)

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT chunk_id, document_id, document_name, page_ref, text, metadata_json
            FROM chunks
            WHERE {where_sql}
            LIMIT ?
        """
        params.append(max(top_k * 5, top_k))

        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()

        candidates: list[DocumentChunk] = []
        for row in rows:
            metadata = json.loads(row["metadata_json"])
            metadata_matches = True
            if metadata_filter:
                metadata_matches = all(
                    metadata.get(key) == value for key, value in metadata_filter.items()
                )
            if not metadata_matches:
                continue
            text_lower = row["text"].lower()
            lexical_score = float(sum(text_lower.count(token) for token in tokens))
            if lexical_score == 0.0:
                continue
            candidates.append(
                DocumentChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    page_ref=row["page_ref"],
                    text=row["text"],
                    metadata=metadata,
                    score=lexical_score,
                )
            )

        ranked = sorted(candidates, key=lambda chunk: chunk.score or 0.0, reverse=True)
        return ranked[:top_k]
