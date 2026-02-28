"""Source query cache."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


def normalize_prompt(prompt: str) -> str:
    """Normalize prompt for stable cache keying."""

    return " ".join(prompt.lower().strip().split())


@dataclass
class SourceQueryCache:
    """In-memory cache for source query results."""

    entries: Dict[str, Any] = field(default_factory=dict)

    def set(self, prompt: str, value: Any) -> None:
        self.entries[normalize_prompt(prompt)] = value

    def get(self, prompt: str) -> Any | None:
        return self.entries.get(normalize_prompt(prompt))
