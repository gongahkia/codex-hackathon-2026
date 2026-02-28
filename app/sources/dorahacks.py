"""DoraHacks source adapter."""

from __future__ import annotations

from typing import Any, Dict, List

from app.sources.base import SourceAdapter


class DoraHacksAdapter(SourceAdapter):
    """Adapter returning normalized DoraHacks-style candidates."""

    source_name = "dorahacks"

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        results: List[Dict[str, Any]] = []
        for index in range(limit):
            results.append(
                {
                    "title": f"{normalized_problem} accelerator #{index + 1}",
                    "summary": "Inspired by DoraHacks submissions with practical MVP scope.",
                    "urls": [f"https://dorahacks.io/project/{normalized_problem.replace(' ', '-').lower()}-{index + 1}"],
                    "stack": [],
                    "signals": {"hackathon_ready": True},
                    "source": self.source_name,
                }
            )
        return results
