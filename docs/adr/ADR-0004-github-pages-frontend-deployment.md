# ADR-0004: GitHub Pages for frontend deployment

## Status

Accepted

## Context

The project must be portfolio-friendly, free, and reliably deployable on GitHub Pages. GitHub Pages supports static hosting only and cannot run Python APIs, Qdrant, or Ollama processes.

## Decision

- Deploy only the frontend static bundle to GitHub Pages.
- Keep FastAPI, Qdrant, and Ollama as a separate runtime plane (local-first baseline).
- Use environment-based API base URL in frontend so deployments can target local or future free-tier backend endpoints.

## Consequences

- Pages deployment remains free and stable.
- Full RAG functionality depends on backend availability outside GitHub Pages.
- Architecture remains compatible with future backend hosting changes without frontend rewrites.
