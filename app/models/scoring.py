"""Scoring-related models."""

from pydantic import BaseModel, model_validator


class Weights(BaseModel):
    """User-adjustable scoring weights."""

    relevance: float = 0.35
    feasibility: float = 0.30
    speed: float = 0.20
    evidence: float = 0.15

    @model_validator(mode="after")
    def validate_non_negative(self) -> "Weights":
        fields = ("relevance", "feasibility", "speed", "evidence")
        for field in fields:
            if getattr(self, field) < 0:
                raise ValueError(f"{field} must be non-negative")
        return self

    @model_validator(mode="after")
    def normalize_non_zero_weights(self) -> "Weights":
        fields = ("relevance", "feasibility", "speed", "evidence")
        total = sum(getattr(self, field) for field in fields if getattr(self, field) != 0)
        if total == 0:
            return self

        for field in fields:
            value = getattr(self, field)
            if value != 0:
                setattr(self, field, value / total)
        return self
