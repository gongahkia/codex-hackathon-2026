"""Video rendering models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class SceneSpec(BaseModel):
    """Scene definition for Remotion renders."""

    style: Literal["pitch", "walkthrough"]
    duration_sec: int
    title: str
    narration: str = ""

    @field_validator("duration_sec")
    @classmethod
    def validate_duration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("duration_sec must be positive")
        return value
