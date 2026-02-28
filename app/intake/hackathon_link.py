"""Preprocess hackathon links into pipeline-ready intake data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from typing import Callable, List
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
HREF_RE = re.compile(r'href=["\'](.*?)["\']', re.IGNORECASE)

FetchHtml = Callable[[str], str]


@dataclass
class HackathonIntake:
    """Derived intake payload when a hackathon link is provided."""

    problem_statement: str
    similar_hackathons: List[str] = field(default_factory=list)
    source_url: str | None = None
    notes: List[str] = field(default_factory=list)


def _default_fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "last-minute/0.1"})
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", unescape(value)).strip()


def _extract_problem_statement(html: str, fallback: str) -> str:
    title_match = TITLE_RE.search(html)
    meta_match = META_DESC_RE.search(html) or OG_DESC_RE.search(html)

    title = _strip_tags(title_match.group(1)) if title_match else ""
    description = _strip_tags(meta_match.group(1)) if meta_match else ""

    chunks = [chunk for chunk in (title, description) if chunk]
    if chunks:
        return " -- ".join(chunks)[:400]
    return fallback


def _extract_links(html: str, domains: tuple[str, ...], skip_url: str, limit: int) -> List[str]:
    links: List[str] = []
    seen: set[str] = set()
    for match in HREF_RE.finditer(html):
        href = unescape(match.group(1)).strip()
        if not href.startswith("http"):
            continue
        if href == skip_url:
            continue
        domain = urlparse(href).netloc.lower()
        if not any(fragment in domain for fragment in domains):
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append(href)
        if len(links) >= limit:
            break
    return links


def _keywords_from_text(text: str) -> str:
    tokens = [token for token in re.split(r"\W+", text.lower()) if len(token) > 3]
    return " ".join(tokens[:6])


def _similar_search_urls(link: str, problem_statement: str) -> List[str]:
    domain = urlparse(link).netloc.lower()
    keywords = quote_plus(_keywords_from_text(problem_statement))

    if "devpost.com" in domain:
        return [f"https://devpost.com/hackathons?search={keywords}"]

    if "luma" in domain or "lu.ma" in domain:
        return [f"https://lu.ma/search?q={keywords}"]

    return []


def preprocess_hackathon_input(
    *,
    problem_statement: str | None,
    hackathon_url: str | None,
    similar_limit: int = 5,
    fetch_html: FetchHtml | None = None,
) -> HackathonIntake:
    """Resolve intake using problem text or a Luma/Devpost hackathon link."""

    fetch = fetch_html or _default_fetch_html
    cleaned_problem = (problem_statement or "").strip()

    if hackathon_url is None or hackathon_url.strip() == "":
        if not cleaned_problem:
            raise ValueError("Provide either problem_statement or hackathon_url")
        return HackathonIntake(problem_statement=cleaned_problem)

    link = hackathon_url.strip()
    domain = urlparse(link).netloc.lower()
    if "devpost.com" not in domain and "lu.ma" not in domain and "luma" not in domain:
        raise ValueError("hackathon_url must be a Devpost or Luma URL")

    notes: List[str] = []
    similar: List[str] = []

    try:
        html = fetch(link)
        inferred_problem = cleaned_problem or _extract_problem_statement(
            html,
            fallback="Hackathon challenge inferred from provided link",
        )
        similar.extend(
            _extract_links(
                html,
                domains=("devpost.com", "lu.ma", "luma"),
                skip_url=link,
                limit=similar_limit,
            )
        )
    except Exception as exc:
        inferred_problem = cleaned_problem or "Hackathon challenge inferred from provided link"
        notes.append(f"Unable to fetch hackathon page directly: {exc}")

    if len(similar) < similar_limit:
        for search_url in _similar_search_urls(link, inferred_problem):
            try:
                search_html = fetch(search_url)
            except Exception as exc:
                notes.append(f"Unable to fetch similar-hackathon search page: {exc}")
                continue

            for candidate in _extract_links(
                search_html,
                domains=("devpost.com", "lu.ma", "luma"),
                skip_url=link,
                limit=similar_limit,
            ):
                if candidate not in similar:
                    similar.append(candidate)
                if len(similar) >= similar_limit:
                    break

    if not similar:
        notes.append("No similar hackathons were confidently discovered from the supplied link")

    return HackathonIntake(
        problem_statement=inferred_problem,
        similar_hackathons=similar[:similar_limit],
        source_url=link,
        notes=notes,
    )
