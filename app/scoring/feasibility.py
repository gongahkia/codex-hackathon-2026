"""Feasibility scoring features."""

from __future__ import annotations

from app.models.candidate import Candidate

COMPLEXITY_PENALTIES = {
    "low": 0.0,
    "medium": 0.15,
    "high": 0.35,
}


def feasibility_score(candidate: Candidate) -> float:
    """Score feasibility from complexity and estimated stack footprint."""

    complexity = str(candidate.signals.get("complexity", "medium")).lower()
    penalty = COMPLEXITY_PENALTIES.get(complexity, 0.2)
    stack_penalty = max(0, len(candidate.stack) - 3) * 0.05
    score = 1.0 - penalty - stack_penalty
    return max(0.0, min(1.0, score))
