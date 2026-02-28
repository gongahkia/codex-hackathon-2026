"""Run artifact registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class ArtifactRegistry:
    """Registry of generated artifact paths for one run."""

    paths: Dict[str, str] = field(default_factory=dict)

    def register(self, key: str, path: str | Path) -> None:
        self.paths[key] = str(path)

    def get(self, key: str) -> str | None:
        return self.paths.get(key)


def default_artifact_registry() -> ArtifactRegistry:
    """Create registry with expected artifact keys."""

    registry = ArtifactRegistry()
    for key in ("matrix", "project", "tests", "video"):
        registry.paths.setdefault(key, "")
    return registry
