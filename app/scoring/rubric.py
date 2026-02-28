"""Judging-rubric scoring weight adaptation."""

from __future__ import annotations

from typing import Mapping

from app.models.scoring import Weights

RUBRIC_KEYWORDS = {
    "relevance": ("impact", "user", "problem", "novel", "innovation", "original"),
    "feasibility": ("technical", "quality", "feasible", "architecture", "reliable"),
    "speed": ("execution", "ship", "delivery", "deadline", "prototype", "mvp"),
    "evidence": ("demo", "evidence", "validation", "metrics", "testing", "proof"),
}


def derive_judging_weights(
    base_weights: Weights | Mapping[str, float],
    rubric_text: str | None,
    blend_ratio: float = 0.35,
) -> Weights:
    """Blend user weights with rubric-derived emphasis when rubric is available."""

    base = base_weights if isinstance(base_weights, Weights) else Weights(**dict(base_weights))
    text = (rubric_text or "").lower().strip()
    if not text:
        return base

    counts: dict[str, int] = {key: 0 for key in RUBRIC_KEYWORDS}
    for factor, keywords in RUBRIC_KEYWORDS.items():
        counts[factor] = sum(text.count(keyword) for keyword in keywords)

    total = sum(counts.values())
    if total <= 0:
        return base

    rubric_distribution = {factor: counts[factor] / total for factor in RUBRIC_KEYWORDS}
    blend = max(0.0, min(1.0, blend_ratio))

    adjusted = {
        factor: (getattr(base, factor) * (1.0 - blend)) + (rubric_distribution[factor] * blend)
        for factor in RUBRIC_KEYWORDS
    }
    return Weights(**adjusted)
