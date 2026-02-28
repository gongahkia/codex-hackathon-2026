"""Build planning models."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class BuildTask(BaseModel):
    """One ordered implementation task."""

    name: str
    estimate_minutes: int


class BuildPlan(BaseModel):
    """Ordered build task plan with estimates."""

    tasks: List[BuildTask] = Field(default_factory=list)

    @property
    def total_estimate_minutes(self) -> int:
        return sum(task.estimate_minutes for task in self.tasks)
