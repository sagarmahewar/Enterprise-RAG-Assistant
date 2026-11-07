# Enterprise RAG Assistant

A production-minded Retrieval-Augmented Generation (RAG) assistant built with Python + FastAPI backend and React + TypeScript frontend, designed for a **GitHub Pages frontend deployment** plus a free/local backend runtime.

This project is designed as a portfolio-grade implementation for AI engineering, LLM application architecture, and practical RAG systems.

## Credit

Co-engineered with **Microsoft Tools** — a portfolio build by **Sagar Mahewar**.

## Objectives

- Upload and manage PDF, DOCX, and TXT documents.
- Parse and chunk documents with provenance metadata.
- Generate local embeddings and store vectors in a local vector DB.
- Ask grounded natural-language questions over uploaded knowledge.
- Return answers with citations (document, section/page where available).
- Inspect retrieved chunks and relevance rationale.
- Maintain conversation context.
- Apply security controls (prompt-injection protection, validation, authorization design).

## Deployment model (GitHub Pages compatible)

GitHub Pages can host only static assets, so the deployment is split:

- **Frontend (React + TypeScript):** hosted on GitHub Pages.
- **Backend API (FastAPI), Qdrant, and Ollama:** run locally via Docker Compose for full RAG functionality.

Optional future backend hosting can use free-tier platforms. This repository now includes environment hooks for Render + Qdrant Cloud + Groq deployment.

## Zero-cost stack (no paid services required)

- **Backend:** Python, FastAPI
- **Frontend:** React, TypeScript
- **LLM runtime:** Ollama (local models)
- **Embeddings:** local sentence-transformer class model via Ollama or local runtime
- **Vector DB:** Qdrant (local Docker container)
- **Metadata/app state:** SQLite
- **Document parsing:** PyMuPDF, python-docx
- **Orchestration:** Docker Compose (backend/runtime)
- **CI:** GitHub Actions

## Architecture and planning docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [docs/architecture/DIAGRAMS.md](./docs/architecture/DIAGRAMS.md)
- [docs/RUNBOOK.md](./docs/RUNBOOK.md)
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- [SECURITY.md](./SECURITY.md)
- [docs/adr](./docs/adr)
- [docs/evaluation](./docs/evaluation)
- [docs/portfolio/DEMO_SCRIPT.md](./docs/portfolio/DEMO_SCRIPT.md)
- [PROJECT_STATUS.md](./PROJECT_STATUS.md)

## Current status

Phases 0-9 are complete for the portfolio release baseline: local-first RAG implementation, security hardening, evaluation/observability, CI/CD, and release documentation.

## Local runtime with Docker Compose

Start backend + qdrant:

```bash
docker compose up -d backend qdrant
```

Start backend + qdrant + local Ollama container profile:

```bash
docker compose --profile local-llm up -d backend qdrant ollama
```

Check backend health:

```bash
curl http://localhost:8000/api/v1/health
```

Stop services:

```bash
docker compose down
```

### CI/CD workflows

- `CI` workflow runs backend checks (`ruff`, `mypy`, `pytest`) and frontend checks (`typecheck`, `test`, `build`) on PRs and pushes to `main`.
- `Deploy Frontend to GitHub Pages` builds `frontend/` and deploys static artifacts from `frontend/dist` on pushes to `main`.

## Cloud deployment (GitHub Pages + Render + Qdrant Cloud + Groq)

### 1) Backend on Render

- Create a Render web service with `rootDir=backend`.
- Build command:
  - `pip install ".[dev]"`
- Start command:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set environment variables (Render dashboard):

- `APP_ENV=production`
- `API_V1_PREFIX=/api/v1`
- `CORS_ORIGINS=https://sagarmahewar.github.io`
- `LLM_PROVIDER_BACKEND=groq`
- `EMBEDDING_PROVIDER_BACKEND=openai`
- `VECTOR_STORE_BACKEND=qdrant`
- `RERANKER_BACKEND=local-fake-reranker`
- `GROQ_API_KEY=<your-groq-key>`
- `GROQ_LLM_MODEL=llama-3.1-8b-instant`
- `OPENAI_API_KEY=<your-openai-key>`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `QDRANT_URL=<your-qdrant-cloud-url>`
- `QDRANT_API_KEY=<your-qdrant-cloud-api-key>`
- `QDRANT_COLLECTION_NAME=rag_chunks_prod`

### 2) Frontend on GitHub Pages (`sagarmahewar`)

- In GitHub repo settings, enable Pages from GitHub Actions.
- Add repository variables:
  - `VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api/v1`
  - optional `VITE_BASE_PATH` (leave empty for `sagarmahewar.github.io`, set for project-page repos)
- Push to `main` to trigger `.github/workflows/pages.yml`.

The Vite base path is auto-detected:
- user-site repo (`sagarmahewar.github.io`) => `/`
- project repo => `/<repo-name>/`

## Final capability snapshot

- Document ingestion for `PDF`, `DOCX`, and `TXT`.
- Hybrid retrieval (lexical + semantic) with reranking.
- Grounded QA responses with structured citations and chunk inspection.
- Prompt-injection guardrails, strict route validation, and safe error envelopes.
- Structured observability with request correlation IDs and key domain events.
- Benchmark/evaluation runner with retrieval and groundedness proxy metrics.

## Showcase visuals

Add screenshots under `docs/portfolio/screenshots/` with these filenames:

- `upload-flow.png`
- `document-management.png`
- `qa-with-citations.png`

Then render them in this section:

```markdown
![Upload flow](docs/portfolio/screenshots/upload-flow.png)
![Document management](docs/portfolio/screenshots/document-management.png)
![QA with citations](docs/portfolio/screenshots/qa-with-citations.png)
```

## Release readiness boundary

### Production-ready in this repo scope

- Clean architecture modularization and replaceable provider interfaces.
- End-to-end local runtime and deterministic CI quality gates.
- GitHub Pages-compatible frontend deployment workflow.
- Operator documentation (runbook + demo script + ADR history).

### Demo-scope / follow-up before enterprise production

- Vector backend path still uses a non-production baseline adapter in current implementation path.
- Authorization is policy-hook based; full enterprise identity and policy integration is pending.
- Evaluation dataset/metrics are starter-level and should be expanded for production confidence.
- GitHub Pages publishes frontend only; backend runtime is still operator-managed.
