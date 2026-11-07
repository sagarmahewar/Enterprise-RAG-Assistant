# Architecture — Enterprise RAG Assistant

## 1. Architectural style

The system uses a **modular monolith** with **clean architecture** boundaries:

- **Interface layer:** REST API (FastAPI), frontend (React)
- **Application layer:** orchestration services and use-cases
- **Domain layer:** entities, value objects, policies, interfaces
- **Infrastructure layer:** concrete providers (Ollama, embeddings, Qdrant, SQLite, filesystem)

Provider abstractions isolate external dependencies so LLM, embedding model, and vector database can be swapped without rewriting business logic.

## 1.1 Deployment topology

Because GitHub Pages is static hosting only, this project uses a split topology:

- **Static Web UI:** deployed to GitHub Pages.
- **RAG Runtime Plane:** FastAPI + Qdrant + Ollama running outside Pages (local Docker Compose baseline).

The frontend calls backend APIs through a configurable base URL. This keeps Pages hosting free while preserving full RAG features.

## 2. High-level modules

1. **API layer**
   - HTTP endpoints, request/response schemas, input validation.
2. **Application services**
   - Ingestion workflows, QA orchestration, conversation commands, document lifecycle.
3. **Domain models**
   - Document, Chunk, Citation, RetrievalResult, Conversation, Message, UserContext.
4. **Document ingestion**
   - Upload, MIME/type validation, deduplication, queueing/state transitions.
5. **Document parsing**
   - PDF (PyMuPDF), DOCX (python-docx), TXT parsers to normalized text blocks.
6. **Chunking**
   - Token-aware semantic chunking with overlap and metadata propagation.
7. **Embedding providers**
   - Interface + local implementation(s) for embedding generation.
8. **LLM providers**
   - Interface + Ollama implementation for answer generation and optional query rewriting.
9. **Vector database**
   - Interface + Qdrant repository implementation.
10. **Retrieval**
   - Hybrid retrieval (BM25/keyword + vector similarity), metadata filters.
11. **Reranking**
   - Local reranker interface and implementation (initially lightweight local approach).
12. **Conversation management**
   - Session memory, summarization policy, context window management.
13. **Evaluation**
   - Offline benchmark runner, retrieval/answer metrics, regression checks.
14. **Configuration**
   - Environment-driven typed settings, model selection, limits, feature toggles.
15. **Observability**
   - Structured logging, trace IDs, latency/error metrics hooks.

## 3. Logical data flow

### 3.1 Ingestion flow

1. User uploads document.
2. File is validated (size/type), stored, and registered in SQLite.
3. Parser extracts text blocks with source references (page/section).
4. Chunker produces chunks + metadata (doc_id, page, headings, offsets, ACL tags).
5. Embedding provider creates vectors for chunks.
6. Vector repo writes vectors + payload to Qdrant.
7. SQLite stores ingestion state and document/chunk metadata.

### 3.2 Query flow

1. User asks question in conversation.
2. Input guard runs safety checks (prompt-injection heuristic/rules).
3. Query processor creates lexical and semantic retrieval plans.
4. Hybrid retriever fetches candidates (keyword + vector).
5. Reranker orders candidates.
6. Citation builder extracts provenance (document + page/reference).
7. LLM composes answer constrained to retrieved context.
8. Response returns: answer, citations, retrieved chunks, scores/rationale.
9. Conversation state stored in SQLite.

## 4. Storage design

### 4.1 SQLite (application metadata)

- users/sessions (local single-user baseline now, extensible later)
- documents (id, name, hash, type, status, created_at)
- chunks (id, doc_id, page_ref, text, token_count, metadata json)
- conversations/messages
- ingestion jobs and audit trail
- evaluation runs and metrics snapshots

### 4.2 Qdrant (vector storage)

- Collection per environment (e.g., `rag_chunks_local`)
- Vector payload includes:
  - `doc_id`, `doc_name`
  - `chunk_id`
  - `page`, `section`
  - `text`
  - `acl_tags`
  - `ingested_at`

## 5. Security and trust boundaries

- API input and file upload are untrusted.
- Parsed content is untrusted and must never execute.
- Prompt and context builder enforce instruction hierarchy:
  system/app policy > user query > document content.
- Document-level authorization enforced pre-retrieval and post-retrieval filtering.

## 6. Extensibility points

- `LLMProvider` interface
- `EmbeddingProvider` interface
- `VectorStore` interface
- `Reranker` interface
- `DocumentParser` registry by MIME type

## 7. Non-functional targets (initial)

- Local-first development, no paid dependencies.
- Deterministic CI for tests and linting.
- Explainable responses with source provenance.
- Replaceable providers without application rewrites.
- GitHub Pages-compatible frontend build and routing.

## 8. Diagram set

See [docs/architecture/DIAGRAMS.md](./docs/architecture/DIAGRAMS.md) for current-state topology, ingestion flow, query flow, and deployment model diagrams.
