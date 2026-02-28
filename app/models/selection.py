"""Selection artifacts."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.candidate import Candidate


class ChosenOption(BaseModel):
    """Selected candidate artifact."""

    selected_candidate: Candidate
    rationale: str
