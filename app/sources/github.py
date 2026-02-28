"""GitHub source adapter."""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus

from app.security.url_policy import UrlPolicy, fetch_json
from app.sources.base import SourceAdapter


class GitHubAdapter(SourceAdapter):
    """Adapter using GitHub search API with README-aware query matching."""

    source_name = "github"
    api_base = "https://api.github.com/search/repositories"

    def __init__(self, policy: UrlPolicy | None = None) -> None:
        self._policy = policy or UrlPolicy()

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

        try:
            payload = fetch_json(
                url,
                policy=self._policy,
                expected_content_types=(
                    "application/json",
                    "text/json",
                    "application/vnd.github+json",
                ),
                user_agent="last-minute/0.2",
            )
        except Exception:
            return []

        items = payload.get("items", []) if isinstance(payload, dict) else []
        results: List[Dict[str, Any]] = []
        for item in items[:limit]:
            html_url = item.get("html_url", "")
            if not html_url:
                continue
            repo_name = str(item.get("name", "repository")).lower()
            results.append(
                {
                    "title": item.get("name", "Untitled repository"),
                    "summary": item.get("description") or "No description provided.",
                    "urls": [html_url, f"https://devpost.com/software/{repo_name}"],
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
