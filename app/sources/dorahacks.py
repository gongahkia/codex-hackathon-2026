"""DoraHacks source adapter."""

from __future__ import annotations

import re
from html import unescape
from typing import Callable
from typing import Any, Dict, List
from urllib.parse import quote_plus, urljoin, urlparse

from app.security.url_policy import UrlPolicy, fetch_text
from app.sources.base import SourceAdapter

ANCHOR_RE = re.compile(
    r'<a[^>]+href=["\'](?P<href>/buidl/[^"\']+|/project/[^"\']+|https://dorahacks\.io/(?:buidl|project)/[^"\']+)["\'][^>]*>(?P<label>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")

FetchHtml = Callable[[str, UrlPolicy], str]


def _default_fetch_html(url: str, policy: UrlPolicy) -> str:
    return fetch_text(
        url,
        policy=policy,
        expected_content_types=("text/html", "text/plain"),
        user_agent="last-minute/0.2",
    )


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", text))).strip()


def _title_from_url(url: str) -> str:
    path = urlparse(url).path
    slug = path.strip("/").split("/")[-1].replace("-", " ")
    return slug.title() if slug else "DoraHacks project"


class DoraHacksAdapter(SourceAdapter):
    """Adapter returning normalized DoraHacks candidates from live HTML search results."""

    source_name = "dorahacks"
    search_base = "https://dorahacks.io/search?query={query}"

    def __init__(
        self,
        policy: UrlPolicy | None = None,
        fetch_html: FetchHtml | None = None,
    ) -> None:
        self._policy = policy or UrlPolicy()
        self._fetch_html = fetch_html or _default_fetch_html

    def search(self, problem: str, limit: int) -> List[Dict[str, Any]]:
        normalized_problem = problem.strip()
        if not normalized_problem or limit <= 0:
            return []

        query = quote_plus(normalized_problem)
        url = self.search_base.format(query=query)

        try:
            html = self._fetch_html(url, self._policy)
        except Exception:
            return []

        results: List[Dict[str, Any]] = []
        seen_urls: set[str] = set()
        for match in ANCHOR_RE.finditer(html):
            href = match.group("href").strip()
            absolute_url = urljoin("https://dorahacks.io", href)
            path = urlparse(absolute_url).path
            if not (path.startswith("/buidl/") or path.startswith("/project/")):
                continue
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)
            if len(results) >= limit:
                break

            title = _clean(match.group("label")) or _title_from_url(absolute_url)
            results.append(
                {
                    "title": title,
                    "summary": "Live DoraHacks project result.",
                    "urls": [absolute_url],
                    "stack": [],
                    "signals": {
                        "query": normalized_problem,
                        "live_fetch": True,
                    },
                    "source": self.source_name,
                }
            )
        return results
