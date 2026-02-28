"""Source adapter registry."""

from __future__ import annotations

from typing import Dict

from app.sources.base import SourceAdapter
from app.sources.devpost import DevpostAdapter
from app.sources.dorahacks import DoraHacksAdapter
from app.sources.github import GitHubAdapter
from app.sources.reddit import RedditAdapter


def build_source_registry(include_reddit: bool = False) -> Dict[str, SourceAdapter]:
    """Build adapter registry with required defaults."""

    registry: Dict[str, SourceAdapter] = {
        "dorahacks": DoraHacksAdapter(),
        "devpost": DevpostAdapter(),
        "github": GitHubAdapter(),
    }
    if include_reddit:
        registry["reddit"] = RedditAdapter(include_reddit=True)
    return registry
