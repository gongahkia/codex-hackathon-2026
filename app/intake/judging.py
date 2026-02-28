"""Judging criteria and prize-track ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from typing import Callable, List, Sequence
from urllib.request import Request, urlopen

FetchHtml = Callable[[str], str]

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H_TAG_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)
LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
TEXT_RE = re.compile(r"<[^>]+>")
CRITERIA_HINT_RE = re.compile(
    r"(judging\s+criteria|evaluation\s+criteria|criteria|how\s+you\s+are\s+judged)",
    re.IGNORECASE,
)


@dataclass
class JudgingContext:
    """Extracted judging context for ranking adjustments."""

    rubric_text: str = ""
    prize_tracks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _default_fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "last-minute/0.1"})
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(TEXT_RE.sub(" ", value))).strip()


def _extract_prize_tracks(html: str, limit: int = 8) -> List[str]:
    tracks: List[str] = []

    for raw in H_TAG_RE.findall(html):
        cleaned = _clean(raw)
        lowered = cleaned.lower()
        if "track" in lowered or "prize" in lowered:
            tracks.append(cleaned)

    for raw in LI_RE.findall(html):
        cleaned = _clean(raw)
        lowered = cleaned.lower()
        if "track" in lowered or "prize" in lowered:
            tracks.append(cleaned)

    deduped: List[str] = []
    seen: set[str] = set()
    for track in tracks:
        key = track.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(track)
        if len(deduped) >= limit:
            break
    return deduped


def _extract_rubric_text(html: str) -> str:
    title_match = TITLE_RE.search(html)
    title = _clean(title_match.group(1)) if title_match else ""

    plain = _clean(html)
    if not plain:
        return title

    match = CRITERIA_HINT_RE.search(plain)
    if match:
        start = max(0, match.start() - 80)
        end = min(len(plain), match.end() + 500)
        snippet = plain[start:end]
    else:
        snippet = plain[:450]

    if title:
        return f"{title} -- {snippet}".strip()
    return snippet.strip()


def ingest_judging_context(
    *,
    hackathon_url: str | None,
    rubric_text: str | None = None,
    provided_prize_tracks: Sequence[str] | None = None,
    fetch_html: FetchHtml | None = None,
) -> JudgingContext:
    """Build judging context from explicit input and optional hackathon page ingestion.

    This function never raises on remote fetch failures; it records notes and returns
    the best available context.
    """

    context = JudgingContext(
        rubric_text=(rubric_text or "").strip(),
        prize_tracks=[track.strip() for track in (provided_prize_tracks or []) if track.strip()],
    )

    if not hackathon_url:
        return context

    fetch = fetch_html or _default_fetch_html
    try:
        html = fetch(hackathon_url)
    except Exception as exc:
        context.notes.append(f"Judging ingestion skipped; unable to fetch hackathon page: {exc}")
        return context

    if not context.rubric_text:
        derived_rubric = _extract_rubric_text(html)
        if derived_rubric:
            context.rubric_text = derived_rubric
        else:
            context.notes.append("Judging criteria were not clearly extractable from hackathon page")

    if not context.prize_tracks:
        derived_tracks = _extract_prize_tracks(html)
        if derived_tracks:
            context.prize_tracks = derived_tracks
        else:
            context.notes.append("Prize tracks were not clearly extractable from hackathon page")

    return context
