# Operations Runbook

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose plugin
- Ollama installed locally (if using host Ollama runtime)

## 2. Local setup

### 2.1 Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ".[dev]"
```

### 2.2 Frontend

```bash
cd frontend
npm ci
```

## 3. Run locally (recommended)

### 3.1 Start backend services with Docker Compose

```bash
docker compose up -d backend qdrant
```

Optional Ollama container profile:

```bash
docker compose --profile local-llm up -d backend qdrant ollama
```

### 3.2 Start frontend dev server

```bash
cd frontend
npm run dev
```

### 3.3 Health checks

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

## 4. Local preview (pre-release verification)

```bash
cd frontend
npm run build
npm run preview -- --host 0.0.0.0 --port 4173
```

If uploads fail from preview UI, ensure backend CORS includes `http://localhost:4173`.

## 5. Quality gates

### 5.1 Backend

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/pytest -q
```

### 5.2 Frontend

```bash
cd frontend
npm run typecheck
npm run test
npm run build
```

## 6. Evaluation run

```bash
cd backend
python -m app.evaluation.runner \
  --dataset ../docs/evaluation/starter-dataset.jsonl \
  --base-url http://127.0.0.1:8000/api/v1 \
  --top-k 6 \
  --output ./data/eval-last-run.json
```

## 7. Observability

- Every response includes `X-Request-Id`.
- Structured JSON logs are emitted through logger `app.observability`.
- Core events:
  - `request.started|completed|failed`
  - `upload.*`
  - `documents.listed`
  - `retrieval.*`
  - `qa.*`

## 8. Troubleshooting quick reference

1. **Upload network error**
   - Confirm backend is up on `:8000`.
   - Confirm CORS allows current frontend origin.
2. **Empty retrieval / insufficient context**
   - Verify documents were uploaded and chunked.
   - Verify document filters are correct.
3. **Permission denied on retrieval/qa**
   - Check `X-Allowed-Document-Ids` behavior with current policy backend.
4. **Evaluation script fails**
   - Ensure backend is running and dataset path is correct.

## 9. Deployment notes

- Frontend deploys to GitHub Pages via `.github/workflows/pages.yml`.
- Backend runtime remains local/self-hosted in this release model.
