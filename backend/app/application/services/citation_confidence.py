from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CitationConfidence:
    score: float
    label: str
    meets_threshold: bool


def build_citation_confidence(score: float | None, threshold: float) -> CitationConfidence:
    bounded_score = _bound(score or 0.0)
    if bounded_score >= 0.75:
        label = "high"
    elif bounded_score >= 0.45:
        label = "medium"
    else:
        label = "low"
    return CitationConfidence(
        score=bounded_score,
        label=label,
        meets_threshold=bounded_score >= threshold,
    )


def _bound(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
