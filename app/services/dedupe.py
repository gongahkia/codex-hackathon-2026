"""Candidate deduplication helpers."""

from __future__ import annotations

import hashlib
from typing import Iterable, List

from app.models.candidate import Candidate
from app.services.url_tools import canonicalize_url


def _url_digest(candidate: Candidate) -> str:
    canonical_urls = [canonicalize_url(url) for url in candidate.urls if url]
    joined = "|".join(sorted(canonical_urls))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def dedupe_by_url_hash(candidates: Iterable[Candidate]) -> List[Candidate]:
    """Deduplicate candidates by canonical URL hash."""

    seen: set[str] = set()
    unique: List[Candidate] = []
    for candidate in candidates:
        digest = _url_digest(candidate)
        if digest in seen:
            continue
        seen.add(digest)
        unique.append(candidate)
    return unique
