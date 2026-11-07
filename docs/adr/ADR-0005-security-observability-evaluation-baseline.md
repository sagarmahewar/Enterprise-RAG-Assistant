# ADR-0005: Security guardrails and observability/evaluation baseline

## Status

Accepted

## Context

As implementation matured, the project needed a minimum trustworthy baseline for:

- prompt-injection resistance,
- strict API input validation and safe error behavior,
- request-level traceability,
- measurable retrieval/groundedness quality trends.

## Decision

- Add retrieval/QA guardrails that reject known malicious prompt-injection patterns and sanitize risky retrieved context.
- Enforce strict validation constraints on upload/retrieval/qa route inputs.
- Introduce document-level access policy interface and route wiring with local policy backends.
- Standardize structured request/application logs with request correlation (`X-Request-Id`).
- Add a dataset-driven evaluation runner with retrieval and groundedness proxy metrics.

## Consequences

- Better operational safety and auditability for a local-first RAG baseline.
- Faster diagnosis via request correlation and structured events.
- Quantitative quality tracking is now possible across iterations.
- Enterprise-grade IAM and larger benchmark coverage remain follow-up work.
