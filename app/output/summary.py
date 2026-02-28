"""Short recommendation summary renderer."""

from __future__ import annotations

from app.services.ranking import ScoredCandidate


def render_recommendation_summary(
    recommendation: ScoredCandidate,
    used_fallback: bool = False,
) -> str:
    """Render concise recommendation summary."""

    candidate = recommendation.candidate
    fallback_note = " (fallback path)" if used_fallback else ""
    return (
        f"Recommended: {candidate.title}{fallback_note}\n"
        f"Source: {candidate.source}\n"
        f"Score: {recommendation.total_score:.3f}\n"
        f"Why: {candidate.summary}"
    )
