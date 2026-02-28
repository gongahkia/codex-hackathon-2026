"""Candidate deduplication helpers."""

from __future__ import annotations

import hashlib
from difflib import SequenceMatcher
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


def dedupe_by_title_similarity(
    candidates: Iterable[Candidate], threshold: float = 0.88
) -> List[Candidate]:
    """Deduplicate candidates whose titles are semantically too similar."""

    unique: List[Candidate] = []
    for candidate in candidates:
        title = candidate.title.lower().strip()
        is_duplicate = False
        for existing in unique:
            existing_title = existing.title.lower().strip()
            similarity = SequenceMatcher(None, title, existing_title).ratio()
            if similarity >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(candidate)
    return unique
