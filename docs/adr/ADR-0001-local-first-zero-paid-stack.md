# ADR-0001: Local-first zero-paid stack

## Status

Accepted

## Context

The project must run fully locally with no paid APIs/services and no credit-card-gated dependencies.

## Decision

Adopt local-first stack:

- FastAPI backend
- React + TypeScript frontend
- Ollama for local LLM runtime
- Local embedding model/provider
- Qdrant local vector database
- SQLite for metadata/state
- Docker Compose for orchestration

## Consequences

- Strong cost control and reproducibility.
- Higher local resource requirements.
- Model quality depends on available hardware and selected local models.
