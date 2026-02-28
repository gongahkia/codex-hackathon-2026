"""Testing report model."""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field, field_validator


class TestingReport(BaseModel):
    """Testing execution summary."""

    executed_suite: str
    pass_rate: float
    skipped_reasons: Dict[str, str] = Field(default_factory=dict)

    @field_validator("pass_rate")
    @classmethod
    def validate_pass_rate(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("pass_rate must be between 0 and 1")
        return value
