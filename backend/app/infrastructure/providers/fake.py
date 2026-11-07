from collections.abc import Mapping, Sequence

from app.domain.models import DocumentChunk, ParsedDocument, ParsedTextBlock


def _safe_float(value: int) -> float:
    return float(value) / 1000.0


class FakeEmbeddingProvider:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            text_len = len(text)
            ascii_mod = sum(ord(character) for character in text) % 1000
            vectors.append([_safe_float(text_len), _safe_float(ascii_mod)])
        return vectors


class FakeLLMProvider:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def generate_answer(self, query: str, context_chunks: Sequence[DocumentChunk]) -> str:
        if not context_chunks:
            return f"[{self.provider_name}] No context available for query: {query}"
        return (
            f"[{self.provider_name}] Draft answer for query '{query}' "
            f"using {len(context_chunks)} retrieved chunk(s)."
        )


class FakeVectorStore:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self._chunks: list[DocumentChunk] = []

    def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        chunk_ids = {chunk.chunk_id for chunk in chunks}
        self._chunks = [chunk for chunk in self._chunks if chunk.chunk_id not in chunk_ids]
        self._chunks.extend(chunks)

    def query(
        self,
        query_vector: Sequence[float],
        top_k: int,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[DocumentChunk]:
        candidates = self._chunks
        if metadata_filter:
            candidates = [
                chunk
                for chunk in candidates
                if _chunk_matches_filter(chunk=chunk, metadata_filter=metadata_filter)
            ]

        scored: list[DocumentChunk] = []
        for chunk in candidates:
            similarity = _cosine_similarity(query_vector, chunk.embedding or [])
            scored.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    text=chunk.text,
                    page_ref=chunk.page_ref,
                    metadata=dict(chunk.metadata),
                    embedding=chunk.embedding,
                    score=similarity,
                )
            )
        ranked = sorted(scored, key=lambda chunk: chunk.score or 0.0, reverse=True)
        return ranked[:top_k]


class FakeReranker:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def rerank(
        self, query: str, candidates: Sequence[DocumentChunk], top_k: int
    ) -> list[DocumentChunk]:
        del query
        ranked = sorted(
            candidates,
            key=lambda chunk: len(chunk.text),
            reverse=True,
        )
        return ranked[:top_k]


class FakeDocumentParser:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def supported_mime_types(self) -> set[str]:
        return {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        }

    def parse(self, document_id: str, document_name: str, content: bytes) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        block = ParsedTextBlock(
            text=text,
            page_ref=None,
            metadata={"parser": self.provider_name},
        )
        return ParsedDocument(
            document_id=document_id,
            document_name=document_name,
            mime_type="text/plain",
            text=text,
            blocks=[block],
            metadata={"parser": self.provider_name},
        )


def _chunk_matches_filter(chunk: DocumentChunk, metadata_filter: Mapping[str, str]) -> bool:
    for key, value in metadata_filter.items():
        if key == "document_id" and chunk.document_id != value:
            return False
        if key == "document_name" and chunk.document_name != value:
            return False
        if key not in {"document_id", "document_name"} and chunk.metadata.get(key) != value:
            return False
    return True


def _cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    if len(vector_a) != len(vector_b) or not vector_a:
        return 0.0
    dot = float(sum(float(a) * float(b) for a, b in zip(vector_a, vector_b, strict=True)))
    mag_a = float(sum(float(a) * float(a) for a in vector_a) ** 0.5)
    mag_b = float(sum(float(b) * float(b) for b in vector_b) ** 0.5)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
