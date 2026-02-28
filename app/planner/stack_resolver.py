"""Stack resolution helpers."""

from __future__ import annotations

from typing import List, Sequence

FAST_DEFAULT_STACK = ["Next.js", "Supabase"]


def resolve_stack(preferred_stack: str | None, candidate_stack: Sequence[str] | None = None) -> List[str]:
    """Pick preferred stack, else candidate stack, else fastest default stack."""

    if preferred_stack:
        return [preferred_stack]
    if candidate_stack:
        return list(candidate_stack)
    return FAST_DEFAULT_STACK.copy()
