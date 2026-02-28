"""GitHub source adapter."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from app.sources.base import SourceAdapter


class GitHubAdapter(SourceAdapter):
    """Adapter using GitHub search API with README-aware query matching."""

    source_name = "github"
    api_base = "https://api.github.com/search/repositories"

    def _build_query(self, problem: str) -> str:
        keywords = [token for token in problem.lower().split() if len(token) > 2]
        if not keywords:
            keywords = [problem.lower().strip()]
        return f"{' '.join(keywords)} in:name,description,readme"

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        query = self._build_query(normalized_problem)
        url = f"{self.api_base}?q={quote_plus(query)}&per_page={min(limit, 100)}"
        request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "last-minute"})

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []

        items = payload.get("items", []) if isinstance(payload, dict) else []
        results: List[Dict[str, Any]] = []
        for item in items[:limit]:
            results.append(
                {
                    "title": item.get("name", "Untitled repository"),
                    "summary": item.get("description") or "No description provided.",
                    "urls": [item.get("html_url", "")],
                    "stack": [],
                    "signals": {
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language"),
                    },
                    "source": self.source_name,
                }
            )
        return results
