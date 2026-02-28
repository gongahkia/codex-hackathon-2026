from __future__ import annotations

from app.services.time_budget import time_budget_splitter


def test_time_budget_splitter_reserves_build_and_testing() -> None:
    split = time_budget_splitter(180)
    assert split["implementation"] >= 30
    assert split["testing"] >= 15
    assert split["research"] == 180 - (
        split["implementation"] + split["testing"] + split["video"]
    )


def test_time_budget_splitter_never_returns_negative_minutes() -> None:
    split = time_budget_splitter(60)
    assert all(value >= 0 for value in split.values())
