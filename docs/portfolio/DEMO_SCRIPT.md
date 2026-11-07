# Portfolio Demo Script

## 1. Demo goal (30 seconds)

Show a local-first, zero-paid Enterprise RAG assistant that:
- ingests enterprise docs,
- performs grounded QA with citations,
- exposes retrieval transparency,
- and ships a GitHub Pages-compatible frontend with CI/CD.

## 2. Demo setup checklist

1. Start backend runtime (`docker compose up -d backend qdrant`).
2. Confirm health (`/api/v1/health`) and readiness (`/api/v1/ready`).
3. Start frontend (`npm run dev` or `npm run preview`).

## 3. Live walkthrough (8–10 minutes)

### Step A: Upload
- Upload one PDF/DOCX/TXT file from UI.
- Narration: strict validation and parser pipeline with metadata/chunking.

### Step B: Document management
- Show searchable document list and scoped selection.
- Narration: supports targeted retrieval scope by document IDs.

### Step C: Ask grounded question
- Ask a specific policy question.
- Narration: hybrid retrieval + reranking + grounded answer policy.

### Step D: Show citations
- Open citations panel.
- Highlight confidence label (`low/medium/high`) and threshold pass/fail.

### Step E: Show retrieved chunks
- Open retrieved chunk viewer and metadata.
- Narration: transparent evidence path for auditing.

### Step F: Security + observability quick proof
- Mention prompt-injection guardrails and safe error envelopes.
- Show `X-Request-Id` in network response headers.

### Step G: Evaluation + CI/CD
- Run evaluation command and show metric output summary.
- Point to CI workflow and GitHub Pages deploy workflow.

## 4. Talking points (what this demonstrates)

- Clean architecture with provider interfaces and modular backend.
- Local-first cost model suitable for constrained budgets.
- Explainability via citations/chunk inspection.
- Engineering rigor: tests, CI, structured observability.

## 5. Known limitations to state transparently

- Vector runtime is still evolving to full production persistence behavior.
- Authorization policy is hook-based; enterprise identity integration is pending.
- Evaluation dataset is a starter baseline and should be expanded.
