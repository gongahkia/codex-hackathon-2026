from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.run_config import RunConfig


def test_deadline_hours_accepts_boundaries() -> None:
    low = RunConfig(problem_statement="x", deadline_hours=1)
    high = RunConfig(problem_statement="x", deadline_hours=24)
    assert low.deadline_hours == 1
    assert high.deadline_hours == 24


@pytest.mark.parametrize("value", [0, 25])
def test_deadline_hours_rejects_out_of_bounds(value: int) -> None:
    with pytest.raises(ValidationError):
        RunConfig(problem_statement="x", deadline_hours=value)


def test_option_count_is_clamped() -> None:
    low = RunConfig(problem_statement="x", deadline_hours=4, option_count=0)
    high = RunConfig(problem_statement="x", deadline_hours=4, option_count=999)
    assert low.option_count == 1
    assert high.option_count == 10


def test_selected_option_accepts_valid_range() -> None:
    cfg = RunConfig(problem_statement="x", deadline_hours=4, selected_option=3)
    assert cfg.selected_option == 3


def test_pause_for_feedback_defaults_to_false() -> None:
    cfg = RunConfig(problem_statement="x", deadline_hours=4)
    assert cfg.pause_for_feedback is False
    assert cfg.strict_fail_fast is False
    assert cfg.resume_run_id is None


def test_feedback_checkpoints_are_unique_and_sorted() -> None:
    cfg = RunConfig(problem_statement="x", deadline_hours=4, feedback_checkpoints=[75, 25, 75, 50])
    assert cfg.feedback_checkpoints == [25, 50, 75]


@pytest.mark.parametrize("value", [0, 100])
def test_feedback_checkpoints_reject_out_of_bounds(value: int) -> None:
    with pytest.raises(ValidationError):
        RunConfig(problem_statement="x", deadline_hours=4, feedback_checkpoints=[value])


@pytest.mark.parametrize("value", [0, 11])
def test_selected_option_rejects_out_of_bounds(value: int) -> None:
    with pytest.raises(ValidationError):
        RunConfig(problem_statement="x", deadline_hours=4, selected_option=value)
