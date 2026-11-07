# Implementation Plan

This roadmap is staged into **independently testable milestones**. Each milestone has explicit deliverables and validation scope.

## Milestone 0 — Foundation and scaffolding

- Create backend and frontend project skeletons.
- Establish directory/module structure per architecture.
- Add formatting, linting, typing, and test tooling.
- Add Docker Compose baseline (app, qdrant, optional ollama profile).
- Configure frontend for GitHub Pages static deployment (`base` path, SPA fallback strategy, env-based API URL).

**Validation:** backend starts, frontend starts, CI lint/test placeholder passes.

## Milestone 1 — Configuration and provider abstractions

- Implement typed config system.
- Define interfaces:
  - `LLMProvider`
  - `EmbeddingProvider`
  - `VectorStore`
  - `Reranker`
  - `DocumentParser`
- Implement dependency wiring in application container.

**Validation:** contract tests with fake providers.

## Milestone 2 — Document ingestion pipeline

- Upload endpoints for PDF/DOCX/TXT.
- File validation, checksuming, storage, SQLite metadata.
- Parsers for PDF (PyMuPDF), DOCX (python-docx), TXT.
- Chunking service with overlap and metadata propagation.

**Validation:** ingestion integration tests for each supported format.

## Milestone 3 — Embeddings and vector indexing

- Local embedding provider implementation.
- Qdrant adapter for upsert/search/delete.
- Index lifecycle and collection management.
- Re-ingestion and dedupe policy.

**Validation:** integration tests against local Qdrant container.

## Milestone 4 — Hybrid retrieval and reranking

- Keyword retrieval index (SQLite FTS or dedicated lexical index strategy).
- Semantic retrieval via Qdrant.
- Score normalization and fusion strategy.
- Metadata filters (doc IDs, tags, time, ACL metadata).
- Reranking layer.

**Validation:** retrieval relevance tests on seeded corpus.

## Milestone 5 — Grounded QA and citations

- Ollama LLM provider integration.
- Prompt templates for grounded answering.
- Citation composer (doc name + page/ref).
- Answer API with retrieved chunk inspection payload.

**Validation:** end-to-end QA tests with expected citation outputs.

## Milestone 6 — Conversation management

- Conversation/session APIs.
- Short-term memory + bounded context assembly.
- Optional conversation summarization policy.

**Validation:** multi-turn tests showing context continuity.

## Milestone 7 — Security hardening

- Prompt-injection guardrails and policy filters.
- Document-level authorization enforcement hooks.
- Input sanitization and strict validation.
- Safe error handling and secure defaults.

**Validation:** security-focused tests for prompt and upload abuse cases.

## Milestone 8 — Observability and operations

- Structured logs and request correlation IDs.
- Basic health/readiness endpoints.
- Operational dashboards/log schema docs.

**Validation:** smoke tests and log contract checks.

## Milestone 9 — Evaluation framework

- Evaluation dataset schema and starter dataset.
- Metrics: retrieval@k, MRR, citation accuracy, groundedness proxy.
- CLI/script for repeatable benchmark runs.
- Baseline report generation.

**Validation:** repeatable evaluation run producing metrics artifacts.

## Milestone 10 — Frontend productization

- Upload UI, document management, QA chat, citation panel.
- Retrieved chunk inspector with relevance signals.
- Error states, loading states, and UX polish.
- GitHub Pages deployment workflow and static build verification.

**Validation:** frontend integration tests and end-to-end happy path.

## Milestone 11 — CI/CD and developer experience

- GitHub Actions for lint, type-check, tests.
- Docker Compose workflow and local setup scripts/docs.
- Contribution and operational runbooks.
- Dedicated workflow for GitHub Pages deployment of frontend artifacts.

**Validation:** CI passing on clean clone with local commands documented.

## Exit criteria for initial release

- Fully local end-to-end workflow (ingest → retrieve → answer with citations).
- Hybrid retrieval functioning with metadata filters.
- Document management and conversation context implemented.
- Security baseline and automated tests in CI.
- Evaluation pipeline with baseline metrics committed.
