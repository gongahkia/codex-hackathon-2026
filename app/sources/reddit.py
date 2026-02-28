"""Reddit source adapter."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from app.sources.base import SourceAdapter


class RedditAdapter(SourceAdapter):
    """Optional Reddit adapter gated by explicit include_reddit opt-in."""

    source_name = "reddit"

    def __init__(self, include_reddit: bool = False) -> None:
        self.include_reddit = include_reddit

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        if not self.include_reddit:
            return []

        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        url = f"https://www.reddit.com/search.json?q={quote_plus(normalized_problem)}&limit={min(limit, 100)}"
        request = Request(url, headers={"User-Agent": "last-minute/0.1"})

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
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
                }
            )
        return results
