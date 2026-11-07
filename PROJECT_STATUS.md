# Project Status

## Phase

Phase 9 - Documentation + portfolio release

## Completed

- Environment inspection baseline captured.
- Local-first, zero-paid architecture defined.
- GitHub Pages deployment constraint incorporated into architecture.
- Security baseline defined.
- ADR set initialized.
- Evaluation planning initialized.
- Milestone roadmap created.
- Backend scaffold created (FastAPI app structure, settings module, health route).
- Frontend scaffold created (React + TypeScript + Vite, GitHub Pages base-path support).
- Baseline CI workflows created (backend and frontend checks, Pages deployment workflow).
- Docker Compose baseline created for backend, Qdrant, and optional Ollama profile.
- Environment templates and repository-level `.gitignore` added.
- Core backend domain contracts added (`LLMProvider`, `EmbeddingProvider`, `VectorStore`, `Reranker`, `DocumentParser`).
- Dependency container and provider wiring added with local fake provider implementations.
- Readiness route added (`/api/v1/ready`) exposing provider snapshot and supported MIME contract.
- Contract tests added for settings defaults, container wiring, parser registry, and health/readiness endpoints.
- Ollama-backed providers added for generation and embeddings (`/api/generate` and `/api/embed`).
- Provider container now supports config-driven selection between Ollama and local fake backends.
- Backend settings expanded with Ollama URL, model selection, and request timeout controls.
- Tests added for Ollama provider response parsing, validation, and container selection behavior.
- Added real document parsers for PDF (PyMuPDF), DOCX (python-docx), and TXT.
- Added ingestion service workflow: upload validation, parser selection, chunking, embeddings, vector upsert, and metadata persistence.
- Added SQLite metadata repository for document and chunk tracking.
- Added ingestion API routes: `POST /api/v1/documents/upload` and `GET /api/v1/documents`.
- Added ingestion-focused tests for parsers, upload route behavior, settings validation, and service-level ingestion flow.
- Added hybrid retrieval service with semantic + lexical candidate gathering, score normalization/fusion, and reranking.
- Added retrieval API route: `POST /api/v1/retrieval/search` with citation-friendly result payload.
- Added explicit citation-confidence contract (`confidence_score`, `confidence_label`, threshold pass/fail) for retrieval and QA responses.
- Added lexical chunk search in SQLite metadata repository for keyword retrieval baseline.
- Extended fake vector store with scored semantic query output and richer metadata filtering.
- Added retrieval tuning settings and environment variables for candidate limits and fusion weights.
- Added retrieval-focused tests for service behavior and API route contract.
- Added QA service that invokes retrieval, enforces grounded-answer policy, and returns explicit insufficient-context fallback.
- Added QA API route: `POST /api/v1/qa/ask` with structured citations and retrieved chunk inspection payload.
- Added QA tuning settings and environment variables for minimum context thresholds.
- Added QA-focused tests for service behavior (grounded flow + fallback) and QA route contract.
- Implemented production-style React UI for upload, document management, QA chat, citations panel, and retrieved chunk viewer.
- Added upload progress UX and drag-drop/file-picker support for PDF, DOCX, and TXT ingestion.
- Added document list search/selection controls for scoped QA over selected docs.
- Added citation confidence rendering (`low/medium/high` + threshold pass/fail) in UI.
- Added frontend API client layer and typed response models for documents/upload/qa routes.
- Added frontend tests covering upload flow, QA flow, citation/chunk rendering, and key error states.
- Added prompt-injection guardrails in retrieval/QA flow with query rejection and context sanitization before LLM prompt assembly.
- Added strict request validation and bounds for upload filename, query length, top_k, document IDs, and metadata filter payload size.
- Added document-level authorization hook contract (`DocumentAccessPolicy`) and container wiring with allow-all/header-allowlist policy implementations.
- Added route-level access-context dependency (`X-User-Id`, `X-Allowed-Document-Ids`) for upload/list/retrieval/qa authorization hooks.
- Added safe error handling for request validation and unhandled exceptions to avoid leaking internal stack details.
- Removed sensitive chunk metadata fields (stored path and file hash) from public retrieval/QA response payloads.
- Added structured observability middleware with request lifecycle events and correlation IDs (`X-Request-Id`) on all API responses.
- Added key domain event logs for upload, retrieval, and QA flows with traceable request IDs.
- Added evaluation runner CLI (`python -m app.evaluation.runner`) that executes retrieval/QA benchmark cases and emits metric reports.
- Added evaluation dataset schema and starter dataset under `docs/evaluation/`.
- Added evaluation and observability tests (dataset parsing/metrics and request-id propagation).
- Hardened Docker Compose runtime with restart policy, backend healthcheck, persistent data mount, and local-LLM profile wiring.
- Improved CI workflow with backend/frontend path-aware triggers, manual dispatch, dependency caching, and deterministic npm installs.
- Improved GitHub Pages workflow with npm cache, deterministic install, pages configuration step, and scoped concurrency.
- Updated root README with local Docker runtime commands and CI/CD workflow behavior.
- Added operations runbook with setup/run/troubleshoot/evaluation/deploy guidance (`docs/RUNBOOK.md`).
- Added architecture diagram set for current-state topology, ingestion, query, and deploy model (`docs/architecture/DIAGRAMS.md`).
- Added portfolio demo script with walkthrough and talking points (`docs/portfolio/DEMO_SCRIPT.md`).
- Extended ADR set with final implementation tradeoff record for security/observability/evaluation baseline (`docs/adr/ADR-0005-security-observability-evaluation-baseline.md`).
- Aligned README with final capability snapshot and explicit production-ready vs demo-scope boundaries.

## Pending

- Initial 0-9 roadmap complete.

## Next-step risks

- Vector store remains a fake in-memory implementation; semantic retrieval quality and persistence are still non-production until a real Qdrant adapter is introduced.
- Document-level authorization is currently hook-based (allow-all by default); tenant-specific policy and identity provider integration remain pending.
- Evaluation metrics are proxy-level and rely on curated expected answers/chunk IDs; broader benchmark coverage is still needed for production confidence.
- GitHub Pages deployment covers only static frontend artifacts; backend runtime remains local/developer-operated.
