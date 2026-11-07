from __future__ import annotations

import json
from pathlib import Path

from app.evaluation.runner import evaluate_case, load_dataset, summarize_results


def test_load_dataset_and_parse(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id":"case-1","question":"Q","expected_answer":"A","relevant_chunk_ids":["c1"],'
        '"expected_citations":[{"document":"doc.pdf","page":"1"}],"tags":["policy"],'
        '"document_ids":["d1"]}\n',
        encoding="utf-8",
    )
    cases = load_dataset(dataset)
    assert len(cases) == 1
    assert cases[0].id == "case-1"
    assert cases[0].document_ids == ["d1"]


def test_evaluate_case_and_summary_metrics(tmp_path: Path) -> None:
    case_payload = {
        "id": "case-1",
        "question": "What is policy?",
        "expected_answer": "Policy is seven years",
        "relevant_chunk_ids": ["c1"],
        "expected_citations": [{"document": "policy.pdf", "page": "4"}],
        "tags": ["policy"],
        "document_ids": [],
    }
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(f"{json.dumps(case_payload)}\n", encoding="utf-8")
    cases = load_dataset(dataset)
    case = cases[0]

    retrieval_payload = {"results": [{"chunk_id": "c2"}, {"chunk_id": "c1"}]}
    qa_payload = {
        "answer": "Policy is seven years for records.",
        "insufficient_context": False,
        "citations": [
            {"document_name": "policy.pdf", "page_ref": "4"},
            {"document_name": "other.pdf", "page_ref": "1"},
        ],
    }
    result = evaluate_case(case, retrieval_payload, qa_payload)
    assert result.retrieval_hit is True
    assert result.reciprocal_rank == 0.5
    assert result.citation_coverage == 1.0
    assert result.citation_precision == 0.5
    assert result.groundedness_proxy is True

    summary = summarize_results([result])
    assert summary["retrieval_at_k"] == 1.0
    assert summary["mrr"] == 0.5
    assert summary["citation_coverage"] == 1.0
    assert summary["citation_precision"] == 0.5
    assert summary["groundedness_proxy_rate"] == 1.0
