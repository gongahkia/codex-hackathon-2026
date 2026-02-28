"""Source query cache."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
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


@dataclass
class RunLocalSourceCache:
    """Run-local file cache for source query payloads."""

    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, source_name: str, query: str, limit: int) -> Path:
        digest = hashlib.sha256(
            f"{source_name}|{normalize_prompt(query)}|{limit}".encode("utf-8")
        ).hexdigest()
        source_dir = self.root / source_name
        source_dir.mkdir(parents=True, exist_ok=True)
        return source_dir / f"{digest}.json"

    def get(self, source_name: str, query: str, limit: int) -> list[dict[str, Any]] | None:
        path = self._cache_path(source_name, query, limit)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        rows = payload.get("rows")
        if not isinstance(rows, list):
            return None
        return [row for row in rows if isinstance(row, dict)]

    def set(self, source_name: str, query: str, limit: int, rows: list[dict[str, Any]]) -> None:
        path = self._cache_path(source_name, query, limit)
        payload = {
            "source": source_name,
            "query": normalize_prompt(query),
            "limit": limit,
            "rows": rows,
            "cached_at": int(time.time()),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
