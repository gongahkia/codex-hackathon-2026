"""Evidence extraction utilities."""

from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse

from app.models.candidate import Candidate

CODE_HOST_HINTS = ("github.com", "gitlab.com", "bitbucket.org")
WRITEUP_HINTS = (
    "devpost.com",
    "medium.com",
    "hashnode.com",
    "notion.site",
    "substack.com",
)


def extract_code_artifact_links(candidate: Candidate) -> List[str]:
    """Detect likely code artifact URLs for a candidate."""

    links: List[str] = []
    for url in candidate.urls:
        domain = urlparse(url).netloc.lower()
        if any(hint in domain for hint in CODE_HOST_HINTS):
            links.append(url)
    return links


def extract_build_writeup_links(candidate: Candidate) -> List[str]:
    """Detect likely build-writeup URLs for a candidate."""

    links: List[str] = []
    for url in candidate.urls:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        if any(hint in domain for hint in WRITEUP_HINTS) or any(
            token in path for token in ("/blog", "/post", "/article", "/writeup")
        ):
            links.append(url)
    return links
