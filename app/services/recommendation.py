"""Recommendation selection services."""

from __future__ import annotations

from app.models.candidate import Candidate
from app.services.evidence_gate import passes_minimum_evidence
from app.services.ranking import ScoredCandidate


def choose_recommendation(ranked_candidates: list[ScoredCandidate]) -> ScoredCandidate:
    """Select highest-scored candidate that passes evidence requirements."""

    support: list[Candidate] = [item.candidate for item in ranked_candidates]
    for item in ranked_candidates:
        if item.total_score <= 0:
            continue
        if passes_minimum_evidence(item.candidate, support):
            return item
    raise ValueError("No candidate passed evidence gate")


def choose_recommendation_with_fallback(
    ranked_candidates: list[ScoredCandidate],
) -> tuple[ScoredCandidate, bool]:
    """Choose valid recommendation, fallback to top score when gate blocks all options."""

    try:
        return choose_recommendation(ranked_candidates), False
    except ValueError:
        if not ranked_candidates:
            raise
        return ranked_candidates[0], True
