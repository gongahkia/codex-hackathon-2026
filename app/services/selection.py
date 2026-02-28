"""User selection services."""

from __future__ import annotations

from typing import Callable, Sequence


def prompt_for_selection(
    options: Sequence[str],
    input_fn: Callable[[str], str] = input,
) -> int:
    """Block until user selects a valid option index."""

    if not options:
        raise ValueError("No options available for selection")

    while True:
        raw = input_fn(f"Choose option index (1-{len(options)}): ").strip()
        if not raw.isdigit():
            continue
        index = int(raw)
        if 1 <= index <= len(options):
            return index - 1
