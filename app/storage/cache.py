"""Source query cache."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


def normalize_prompt(prompt: str) -> str:
    """Normalize prompt for stable cache keying."""

    return " ".join(prompt.lower().strip().split())


@dataclass
class SourceQueryCache:
    """In-memory cache for source query results."""

    ttl_seconds: int = 900
    entries: Dict[str, tuple[float, Any]] = field(default_factory=dict)

    def set(self, prompt: str, value: Any) -> None:
        self.entries[normalize_prompt(prompt)] = (time.time(), value)

    def get(self, prompt: str) -> Any | None:
        key = normalize_prompt(prompt)
        cached = self.entries.get(key)
        if cached is None:
            return None

        created_at, value = cached
        if time.time() - created_at > self.ttl_seconds:
            self.entries.pop(key, None)
            return None
        return value
