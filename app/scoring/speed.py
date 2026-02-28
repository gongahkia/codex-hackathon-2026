"""Speed-to-build scoring features."""

from __future__ import annotations

from app.models.candidate import Candidate


def speed_to_build_score(candidate: Candidate) -> float:
    """Estimate speed-to-build with simple complexity heuristics."""

    setup_steps = int(candidate.signals.get("setup_steps", 3) or 3)
    stack_size = len(candidate.stack)
    penalty = min(0.8, (max(0, setup_steps - 2) * 0.1) + (max(0, stack_size - 2) * 0.07))
    score = 1.0 - penalty
    return max(0.0, min(1.0, score))
