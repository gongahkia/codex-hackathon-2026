from __future__ import annotations

from app.runtime.command_runner import run_command_streamed


def test_run_command_streamed_sets_explicit_timeout_metadata() -> None:
    result = run_command_streamed(
        [
            "python3",
            "-m",
            "pytest",
            "-q",
            "tests/test_pipeline_source_of_truth.py::test_pipeline_writes_research_and_selection_artifacts",
        ],
        timeout_seconds=1,
    )

    assert result.timed_out is True
    assert result.returncode == 124
    assert result.duration_ms >= 1000
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)
