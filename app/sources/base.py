"""Source adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SourceAdapter(ABC):
    """Abstract interface for external idea sources."""

    source_name: str

    @abstractmethod
    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        """Return normalized candidate records."""
        raise NotImplementedError
