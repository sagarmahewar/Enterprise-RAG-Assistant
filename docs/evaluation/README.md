# Evaluation Framework Plan

## Purpose

Establish repeatable, local evaluation for retrieval quality, grounding quality, and regression detection.

## Planned metrics

- **Retrieval@k**
- **MRR (Mean Reciprocal Rank)**
- **Citation coverage and citation precision**
- **Groundedness proxy** (answer support traceable to retrieved context)
- **Answer helpfulness rubric** (manual/assisted scoring for portfolio reporting)

## Dataset structure

Use JSONL records with:

- `id`
- `question`
- `expected_answer` (reference)
- `relevant_chunk_ids` (gold retrieval targets)
- `expected_citations` (doc/page refs where available)
- `tags` (domain/topic)
- `document_ids` (optional scoped document filters used during evaluation calls)

See:

- `dataset-schema.json` for strict field contract.
- `starter-dataset.jsonl` for a runnable starter benchmark.

## Outputs

- Run metadata (model, embedding, chunk params).
- Metric summary.
- Per-case diagnostics for failure analysis.

## Runner

Run evaluation against a local backend:

```bash
cd backend
python -m app.evaluation.runner \
  --dataset ../docs/evaluation/starter-dataset.jsonl \
  --base-url http://127.0.0.1:8000/api/v1 \
  --top-k 6 \
  --output ./data/eval-last-run.json
```

Output includes:

- run metadata (providers + params)
- metric summary (`retrieval_at_k`, `mrr`, citation coverage/precision, groundedness proxy rate)
- per-case diagnostics
