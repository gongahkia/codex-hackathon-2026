"""Evidence extraction utilities."""

from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse

from app.models.candidate import Candidate

CODE_HOST_HINTS = ("github.com", "gitlab.com", "bitbucket.org")


def extract_code_artifact_links(candidate: Candidate) -> List[str]:
    """Detect likely code artifact URLs for a candidate."""

    links: List[str] = []
    for url in candidate.urls:
        domain = urlparse(url).netloc.lower()
        if any(hint in domain for hint in CODE_HOST_HINTS):
            links.append(url)
    return links
