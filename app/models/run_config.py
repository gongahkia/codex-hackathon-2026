"""Runtime configuration model."""

from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

DEFAULT_WEIGHTS: Dict[str, float] = {
    "relevance": 0.35,
    "feasibility": 0.30,
    "speed": 0.20,
    "evidence": 0.15,
}


class RunConfig(BaseModel):
    """User-provided configuration for a pipeline run."""

    problem_statement: str
    deadline_hours: int
    mode: Literal["detailed-live", "fast"] = "detailed-live"
    option_count: int = 5
    weights: Dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    include_reddit: bool = False
    preferred_stack: Optional[str] = None
    video_style: Literal["pitch", "walkthrough"] = "pitch"
    video_duration_sec: int = 60
