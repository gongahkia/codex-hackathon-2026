"""Time-aware test strategy selection."""

from __future__ import annotations

from typing import List


def select_test_plan(remaining_minutes: int) -> List[str]:
    """Select test execution order by remaining time budget."""

    if remaining_minutes >= 30:
        return ["e2e", "integration", "smoke"]
    if remaining_minutes >= 15:
        return ["integration", "smoke"]
    return ["smoke"]
