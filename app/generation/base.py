"""Code generation interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from app.planner.project_spec import ProjectSpec


class CodeGenerator(ABC):
    """Interface for project code generation adapters."""

    @abstractmethod
    def generate(self, spec: ProjectSpec) -> Dict[str, str]:
        """Return file map (relative path -> file content)."""
        raise NotImplementedError
