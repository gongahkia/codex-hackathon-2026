"""Repository freshness checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def is_repo_stale(
    last_commit_date: datetime | str | None,
    threshold_days: int = 180,
    now: datetime | None = None,
) -> bool:
    """Return True when repository commit age exceeds threshold."""

    if last_commit_date is None:
        return True

    if isinstance(last_commit_date, str):
        last_commit_date = datetime.fromisoformat(last_commit_date.replace("Z", "+00:00"))

    if last_commit_date.tzinfo is None:
        last_commit_date = last_commit_date.replace(tzinfo=UTC)

    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    return last_commit_date < reference - timedelta(days=threshold_days)
