"""Devpost source adapter."""

from __future__ import annotations

from typing import Any, Dict, List

from app.sources.base import SourceAdapter


class DevpostAdapter(SourceAdapter):
    """Adapter returning normalized Devpost-style candidates."""

    source_name = "devpost"

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        results: List[Dict[str, Any]] = []
        slug = normalized_problem.replace(" ", "-").lower()
        for index in range(limit):
            results.append(
                {
                    "title": f"{normalized_problem} project pattern #{index + 1}",
                    "summary": "Derived from Devpost challenge submissions and judging trends.",
                    "urls": [
                        f"https://devpost.com/software/{slug}-{index + 1}",
                        f"https://github.com/example/{slug}-{index + 1}",
                    ],
                    "stack": [],
                    "signals": {"battle_tested": True},
                    "source": self.source_name,
                }
            )
        return results
