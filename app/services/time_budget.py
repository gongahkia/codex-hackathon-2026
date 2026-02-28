"""Time budgeting helpers."""

from __future__ import annotations

from typing import Dict


def time_budget_splitter(total_minutes: int) -> Dict[str, int]:
    """Split total minutes while reserving implementation/testing before research."""

    if total_minutes <= 0:
        raise ValueError("total_minutes must be positive")

    implementation = max(30, int(total_minutes * 0.45))
    testing = max(15, int(total_minutes * 0.20))
    video = max(10, int(total_minutes * 0.10))

    reserved = implementation + testing + video
    research = max(0, total_minutes - reserved)

    if reserved > total_minutes:
        overflow = reserved - total_minutes
        video = max(0, video - overflow)

    return {
        "research": research,
        "implementation": implementation,
        "testing": testing,
        "video": video,
    }
