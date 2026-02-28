"""Weighted score aggregation."""

from __future__ import annotations

from typing import Mapping

from app.models.scoring import Weights


FEATURE_KEYS = ("relevance", "feasibility", "speed", "evidence")


def aggregate_weighted_score(features: Mapping[str, float], weights: Weights | Mapping[str, float]) -> float:
    """Aggregate factor scores using normalized user weights."""

    normalized = weights if isinstance(weights, Weights) else Weights(**dict(weights))

    score = 0.0
    for key in FEATURE_KEYS:
        score += float(features.get(key, 0.0)) * float(getattr(normalized, key))
    return max(0.0, min(1.0, score))
