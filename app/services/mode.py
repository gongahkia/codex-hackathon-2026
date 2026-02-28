"""Mode parsing helpers."""

from __future__ import annotations

from typing import Literal

Mode = Literal["detailed-live", "fast"]


def parse_mode(mode: str | None) -> Mode:
    """Parse run mode and return supported values only."""

    if mode is None or mode.strip() == "":
        return "detailed-live"

    normalized = mode.strip().lower()
    if normalized not in {"detailed-live", "fast"}:
        raise ValueError("mode must be 'detailed-live' or 'fast'")
    return normalized  # type: ignore[return-value]
