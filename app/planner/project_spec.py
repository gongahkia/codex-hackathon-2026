"""Project specification generator."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.models.selection import ChosenOption


class ProjectSpec(BaseModel):
    """Build-ready project specification."""

    title: str
    features: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)


def generate_project_spec(selected: ChosenOption, preferred_stack: str | None = None) -> ProjectSpec:
    """Generate a scoped project spec from selected candidate and rationale."""

    candidate = selected.selected_candidate
    features = [
        "Core user flow",
        "Basic persistence",
        "Error handling for primary path",
    ]

    stack = candidate.stack.copy() if candidate.stack else []
    if preferred_stack:
        stack = [preferred_stack]
    elif not stack:
        stack = ["Next.js", "SQLite"]

    milestones = [
        "Set up project scaffold",
        "Implement core workflow",
        "Add validation and errors",
        "Run tests and smoke verification",
    ]

    return ProjectSpec(
        title=candidate.title,
        features=features,
        stack=stack,
        milestones=milestones,
    )
