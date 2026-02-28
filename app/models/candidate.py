"""Candidate models from research phase."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """Normalized candidate schema across all research adapters."""

    title: str
    summary: str
    urls: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    source: str
