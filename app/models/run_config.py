"""Runtime configuration model."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

DEFAULT_WEIGHTS: Dict[str, float] = {
    "relevance": 0.35,
    "feasibility": 0.30,
    "speed": 0.20,
    "evidence": 0.15,
}


class RunConfig(BaseModel):
    """User-provided configuration for a pipeline run."""

    problem_statement: str
    hackathon_url: Optional[str] = None
    similar_hackathons: List[str] = Field(default_factory=list)
    intake_notes: List[str] = Field(default_factory=list)
    judging_rubric_text: Optional[str] = None
    prize_tracks: List[str] = Field(default_factory=list)
    judging_notes: List[str] = Field(default_factory=list)
    deadline_hours: int
    mode: Literal["detailed-live", "fast"] = "detailed-live"
    option_count: int = 5
    weights: Dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    include_reddit: bool = False
    pause_for_feedback: bool = False
    selected_option: Optional[int] = None
    interactive_selection: bool = False
    preferred_stack: Optional[str] = None
    video_style: Literal["pitch", "walkthrough"] = "pitch"
    video_duration_sec: int = 60
    deployment_health_url: Optional[str] = None
    demo_route: str = "/demo"
    allow_local_health: bool = False

    @field_validator("deadline_hours")
    @classmethod
    def validate_deadline_hours(cls, value: int) -> int:
        if value < 1 or value > 24:
            raise ValueError("deadline_hours must be between 1 and 24")
        return value

    @field_validator("option_count")
    @classmethod
    def clamp_option_count(cls, value: int) -> int:
        return max(1, min(value, 10))

    @field_validator("problem_statement")
    @classmethod
    def validate_problem_statement(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("problem_statement must not be empty")
        return cleaned

    @field_validator("selected_option")
    @classmethod
    def validate_selected_option(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 1 or value > 10:
            raise ValueError("selected_option must be between 1 and 10")
        return value
