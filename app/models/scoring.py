"""Scoring-related models."""

from pydantic import BaseModel


class Weights(BaseModel):
    """User-adjustable scoring weights."""

    relevance: float = 0.35
    feasibility: float = 0.30
    speed: float = 0.20
    evidence: float = 0.15
