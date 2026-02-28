"""Reddit source adapter."""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus

from app.security.url_policy import UrlPolicy, fetch_json
from app.sources.base import SourceAdapter


class RedditAdapter(SourceAdapter):
    """Optional Reddit adapter gated by explicit include_reddit opt-in."""

    source_name = "reddit"

    def __init__(self, include_reddit: bool = False, policy: UrlPolicy | None = None) -> None:
        self.include_reddit = include_reddit
        self._policy = policy or UrlPolicy()

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        if not self.include_reddit:
            return []

        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        url = f"https://www.reddit.com/search.json?q={quote_plus(normalized_problem)}&limit={min(limit, 100)}"

        try:
            payload = fetch_json(
                url,
                policy=self._policy,
                expected_content_types=("application/json", "text/json"),
                user_agent="last-minute/0.2",
            )
        except Exception:
            return []

        children = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
        results: List[Dict[str, Any]] = []
        for item in children[:limit]:
            data = item.get("data", {})
            permalink = data.get("permalink", "")
            url_value = f"https://www.reddit.com{permalink}" if permalink else ""
            results.append(
                {
                    "title": data.get("title", "Untitled Reddit thread"),
                    "summary": data.get("selftext", "")[:280],
                    "urls": [url_value],
                    "stack": [],
                    "signals": {
                        "score": data.get("score", 0),
                        "comments": data.get("num_comments", 0),
                    },
                    "source": self.source_name,
                    "source_query": normalized_problem,
                }
            )
        return results
