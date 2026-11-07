# ADR-0003: Hybrid retrieval with explicit citation provenance

## Status

Accepted

## Context

Pure semantic retrieval can miss exact terms; pure keyword retrieval can miss conceptual matches. The assistant must explain sources and provenance.

## Decision

- Implement hybrid retrieval (keyword + semantic vector search).
- Apply reranking before answer generation.
- Require citation payload in responses with document and page/reference metadata.

## Consequences

- Better retrieval robustness.
- More transparent and auditable answers.
- Additional implementation complexity and tuning overhead.
