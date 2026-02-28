from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.models.scoring import Weights


def test_weights_normalize_non_zero_values_to_one() -> None:
    weights = Weights(relevance=2.0, feasibility=2.0, speed=0.0, evidence=1.0)
    total = weights.relevance + weights.feasibility + weights.speed + weights.evidence
    assert math.isclose(total, 1.0, rel_tol=1e-9)
    assert weights.speed == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"relevance": -0.1},
        {"feasibility": -1.0},
        {"speed": -0.01},
        {"evidence": -5.0},
    ],
)
def test_weights_reject_negative_values(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        Weights(**kwargs)
