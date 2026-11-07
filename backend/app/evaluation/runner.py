from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx


@dataclass(frozen=True)
class ExpectedCitation:
    document: str
    page: str


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    expected_answer: str
    relevant_chunk_ids: list[str]
    expected_citations: list[ExpectedCitation]
    tags: list[str]
    document_ids: list[str] | None


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    retrieval_hit: bool
    reciprocal_rank: float
    citation_coverage: float
    citation_precision: float
    groundedness_proxy: bool
    retrieved_count: int
    citations_count: int


def parse_eval_case(payload: dict[str, Any]) -> EvalCase:
    case_id = _as_non_empty_string(payload.get("id"), "id")
    question = _as_non_empty_string(payload.get("question"), "question")
    expected_answer = _as_non_empty_string(payload.get("expected_answer"), "expected_answer")
    relevant_chunk_ids = _as_string_list(payload.get("relevant_chunk_ids"), "relevant_chunk_ids")
    raw_expected_citations = payload.get("expected_citations")
    if not isinstance(raw_expected_citations, list):
        raise ValueError("expected_citations must be a list")
    expected_citations = [
        ExpectedCitation(
            document=_as_non_empty_string(entry.get("document"), "expected_citations.document"),
            page=str(entry.get("page", "")).strip(),
        )
        for entry in raw_expected_citations
        if isinstance(entry, dict)
    ]
    tags = _as_string_list(payload.get("tags"), "tags")
    raw_document_ids = payload.get("document_ids")
    document_ids = None
    if raw_document_ids is not None:
        document_ids = _as_string_list(raw_document_ids, "document_ids")
    return EvalCase(
        id=case_id,
        question=question,
        expected_answer=expected_answer,
        relevant_chunk_ids=relevant_chunk_ids,
        expected_citations=expected_citations,
        tags=tags,
        document_ids=document_ids,
    )


def load_dataset(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"Dataset line {line_no} must be a JSON object")
        cases.append(parse_eval_case(payload))
    if not cases:
        raise ValueError("Dataset is empty")
    return cases


def evaluate_case(
    case: EvalCase,
    retrieval_payload: dict[str, Any],
    qa_payload: dict[str, Any],
) -> EvalCaseResult:
    retrieved_chunk_ids: list[str] = []
    for item in retrieval_payload.get("results", []):
        if isinstance(item, dict):
            chunk_id = item.get("chunk_id")
            if isinstance(chunk_id, str):
                retrieved_chunk_ids.append(chunk_id)
    reciprocal_rank = _compute_reciprocal_rank(retrieved_chunk_ids, case.relevant_chunk_ids)
    retrieval_hit = reciprocal_rank > 0

    expected_citations = {
        _citation_key(citation.document, citation.page) for citation in case.expected_citations
    }
    predicted_citations = {
        _citation_key(
            _as_non_empty_string_or_default(citation.get("document_name"), "unknown"),
            str(citation.get("page_ref") or "").strip(),
        )
        for citation in qa_payload.get("citations", [])
        if isinstance(citation, dict)
    }

    matched = expected_citations & predicted_citations
    citation_coverage = 1.0 if not expected_citations else len(matched) / len(expected_citations)
    if not predicted_citations:
        citation_precision = 1.0 if not expected_citations else 0.0
    else:
        citation_precision = len(matched) / len(predicted_citations)

    groundedness_proxy = _groundedness_proxy(
        answer=_as_non_empty_string_or_default(qa_payload.get("answer"), ""),
        expected_answer=case.expected_answer,
        insufficient_context=bool(qa_payload.get("insufficient_context")),
        citation_count=len(predicted_citations),
    )
    return EvalCaseResult(
        case_id=case.id,
        retrieval_hit=retrieval_hit,
        reciprocal_rank=reciprocal_rank,
        citation_coverage=citation_coverage,
        citation_precision=citation_precision,
        groundedness_proxy=groundedness_proxy,
        retrieved_count=len(retrieved_chunk_ids),
        citations_count=len(predicted_citations),
    )


def summarize_results(results: list[EvalCaseResult]) -> dict[str, Any]:
    if not results:
        raise ValueError("No evaluation results to summarize")
    total = len(results)
    retrieval_at_k = sum(1 for result in results if result.retrieval_hit) / total
    mrr = sum(result.reciprocal_rank for result in results) / total
    citation_coverage = sum(result.citation_coverage for result in results) / total
    citation_precision = sum(result.citation_precision for result in results) / total
    groundedness = sum(1 for result in results if result.groundedness_proxy) / total
    return {
        "total_cases": total,
        "retrieval_at_k": round(retrieval_at_k, 4),
        "mrr": round(mrr, 4),
        "citation_coverage": round(citation_coverage, 4),
        "citation_precision": round(citation_precision, 4),
        "groundedness_proxy_rate": round(groundedness, 4),
    }


def run_evaluation(
    *,
    dataset_path: Path,
    base_url: str,
    top_k: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    cases = load_dataset(dataset_path)
    with httpx.Client(base_url=base_url, timeout=timeout_seconds) as client:
        ready_response = client.get("/ready")
        ready_response.raise_for_status()
        ready_payload = ready_response.json()

        results: list[EvalCaseResult] = []
        for case in cases:
            retrieval_response = client.post(
                "/retrieval/search",
                json={
                    "query": case.question,
                    "top_k": top_k,
                    "document_ids": case.document_ids,
                },
            )
            retrieval_response.raise_for_status()
            retrieval_payload = retrieval_response.json()

            qa_response = client.post(
                "/qa/ask",
                json={
                    "query": case.question,
                    "top_k": top_k,
                    "document_ids": case.document_ids,
                },
            )
            qa_response.raise_for_status()
            qa_payload = qa_response.json()
            results.append(evaluate_case(case, retrieval_payload, qa_payload))

    summary = summarize_results(results)
    return {
        "run_metadata": {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "dataset_path": str(dataset_path),
            "api_base_url": base_url,
            "top_k": top_k,
            "providers": ready_payload.get("providers", {}),
        },
        "summary": summary,
        "cases": [
            {
                "case_id": result.case_id,
                "retrieval_hit": result.retrieval_hit,
                "reciprocal_rank": round(result.reciprocal_rank, 4),
                "citation_coverage": round(result.citation_coverage, 4),
                "citation_precision": round(result.citation_precision, 4),
                "groundedness_proxy": result.groundedness_proxy,
                "retrieved_count": result.retrieved_count,
                "citations_count": result.citations_count,
            }
            for result in results
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local retrieval/QA evaluation benchmark")
    parser.add_argument(
        "--dataset",
        default="../docs/evaluation/starter-dataset.jsonl",
        help="Path to eval dataset jsonl",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/api/v1",
        help="Backend API base URL",
    )
    parser.add_argument("--top-k", type=int, default=6, help="top_k for retrieval and qa requests")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="HTTP timeout for each API call",
    )
    parser.add_argument(
        "--output",
        default="./data/eval-last-run.json",
        help="Output report JSON path",
    )
    args = parser.parse_args()

    report = run_evaluation(
        dataset_path=Path(args.dataset),
        base_url=args.base_url,
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved report to {output_path}")


def _as_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _as_non_empty_string_or_default(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _as_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{field_name} contains invalid entry")
        normalized.append(entry.strip())
    return normalized


def _compute_reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    relevant_set = set(relevant)
    for index, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant_set:
            return 1.0 / index
    return 0.0


def _groundedness_proxy(
    *,
    answer: str,
    expected_answer: str,
    insufficient_context: bool,
    citation_count: int,
) -> bool:
    if insufficient_context or citation_count == 0:
        return False
    answer_tokens = set(_tokenize(answer))
    expected_tokens = set(_tokenize(expected_answer))
    if not expected_tokens:
        return False
    overlap = len(answer_tokens & expected_tokens) / len(expected_tokens)
    return overlap >= 0.3


def _citation_key(document: str, page: str) -> str:
    return f"{document.strip().lower()}::{page.strip().lower()}"


def _tokenize(value: str) -> list[str]:
    return [token for token in value.lower().split() if token]


if __name__ == "__main__":
    main()
