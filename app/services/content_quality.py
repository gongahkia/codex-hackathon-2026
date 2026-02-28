"""Content quality heuristics."""

from __future__ import annotations

SPAM_HINTS = {"airdrop", "giveaway", "click here", "free money", "100x"}


def is_low_detail_description(summary: str, min_words: int = 20) -> bool:
    """Flag short or spam-like descriptions as low detail."""

    normalized = summary.strip().lower()
    if not normalized:
        return True

    words = [token for token in normalized.split() if token]
    if len(words) < min_words:
        return True

    if any(token in normalized for token in SPAM_HINTS):
        return True

    return False
