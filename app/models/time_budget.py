"""Time budget models."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class BudgetSnapshot(BaseModel):
    """Per-phase minute allocations for a run."""

    intake_minutes: int = 5
    research_minutes: int = 0
    ranking_minutes: int = 0
    selection_minutes: int = 5
    build_minutes: int = 0
    test_minutes: int = 0
    video_minutes: int = 0

    @field_validator(
        "intake_minutes",
        "research_minutes",
        "ranking_minutes",
        "selection_minutes",
        "build_minutes",
        "test_minutes",
        "video_minutes",
    )
    @classmethod
    def validate_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("budget minutes must be non-negative")
        return value

    @property
    def total_minutes(self) -> int:
        return (
            self.intake_minutes
            + self.research_minutes
            + self.ranking_minutes
            + self.selection_minutes
            + self.build_minutes
            + self.test_minutes
            + self.video_minutes
        )
