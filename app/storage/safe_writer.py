"""Safe artifact writer with path traversal protection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SafeArtifactWriter:
    """Write files under one resolved root only."""

    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, relative_path: str | Path) -> Path:
        rel = Path(relative_path)
        if rel.is_absolute():
            raise ValueError("absolute paths are not allowed")

        target = (self.root / rel).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError(f"path traversal detected: {relative_path}")
        return target

    def write_text(self, relative_path: str | Path, content: str) -> Path:
        target = self._resolve_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def write_json(self, relative_path: str | Path, payload: Any) -> Path:
        return self.write_text(relative_path, json.dumps(payload, indent=2))
