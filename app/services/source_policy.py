"""Source usage policy helpers."""

from __future__ import annotations

REDDIT_DISCLAIMER = "I understand Reddit results may be noisy"


def validate_reddit_opt_in(include_reddit: bool, confirmation: str | None) -> bool:
    """Require explicit user confirmation before enabling Reddit results."""

    if not include_reddit:
        return False

    if (confirmation or "").strip() != REDDIT_DISCLAIMER:
        raise ValueError(
            "Reddit inclusion requires explicit confirmation: "
            f"{REDDIT_DISCLAIMER!r}"
        )
    return True
