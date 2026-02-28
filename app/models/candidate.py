"""Candidate models from research phase."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class Candidate(BaseModel):
    """Normalized candidate schema across all research adapters."""

    title: str
    summary: str
    urls: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    source: str
    fetched_at: datetime | None = None
    verified_at: datetime | None = None
    source_query: str | None = None
    verification_errors: List[str] = Field(default_factory=list)

    @field_validator("source_query")
    @classmethod
    def validate_source_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("verification_errors")
    @classmethod
    def normalize_verification_errors(cls, value: List[str]) -> List[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        return normalized
