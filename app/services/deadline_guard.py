"""Deadline guard helpers."""

from __future__ import annotations

from typing import Iterable, List, Tuple

LOW_PRIORITY_PHASES = {"research", "ranking", "video"}


def apply_deadline_guard(remaining_minutes: int, phases: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Abort low-priority phases when no time remains."""

    phase_list = list(phases)
    if remaining_minutes > 0:
        return phase_list, []

    runnable = [phase for phase in phase_list if phase not in LOW_PRIORITY_PHASES]
    aborted = [phase for phase in phase_list if phase in LOW_PRIORITY_PHASES]
    return runnable, aborted
