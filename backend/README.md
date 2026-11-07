# Backend

FastAPI backend for the Enterprise RAG Assistant.

## Observability

- Every request is assigned/carries an `X-Request-Id` correlation ID.
- API responses include `X-Request-Id` so frontend/logs can correlate events.
- Structured JSON events are emitted for request lifecycle and key domain actions (`upload.*`, `retrieval.*`, `qa.*`) via logger `app.observability`.
