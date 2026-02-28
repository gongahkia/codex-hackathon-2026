"""Quality penalty scoring."""

from __future__ import annotations


def calculate_quality_penalty(
    *,
    stale_repo: bool,
    weak_evidence: bool,
    low_detail: bool = False,
) -> float:
    """Return additive penalty in range [0.0, 1.0]."""

    penalty = 0.0
    if stale_repo:
        penalty += 0.25
    if weak_evidence:
        penalty += 0.45
    if low_detail:
        penalty += 0.20
    return min(1.0, penalty)
