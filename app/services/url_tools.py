"""URL normalization helpers."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def canonicalize_url(url: str) -> str:
    """Normalize query parameter ordering and trailing slashes."""

    parsed = urlparse(url.strip())
    query_items = sorted(parse_qsl(parsed.query, keep_blank_values=False))
    query = urlencode(query_items, doseq=True)

    normalized_path = parsed.path.rstrip("/")
    if not normalized_path and parsed.scheme and parsed.netloc:
        normalized_path = ""

    canonical = parsed._replace(path=normalized_path, query=query, fragment="")
    return urlunparse(canonical)
