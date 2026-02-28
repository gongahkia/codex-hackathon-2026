from __future__ import annotations

import json

from typer.testing import CliRunner

from app.cli import app
from app.models.run_state import RunState


def test_cli_e2e_run_with_fixture_pipeline(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_pipeline(config):
        assert config.problem_statement == "Build AI todo app"
        return [
            RunState.INTAKE,
            RunState.RESEARCH,
            RunState.RANKING,
            RunState.SELECTION,
            RunState.BUILD,
            RunState.TEST,
            RunState.VIDEO,
            RunState.DONE,
        ]

    monkeypatch.setattr("app.cli.run_pipeline", fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--mode",
            "fast",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["problem_statement"] == "Build AI todo app"


def test_cli_maps_feedback_flags_into_run_config(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_pipeline(config):
        assert config.pause_for_feedback is True
        assert config.feedback_checkpoints == [30, 60]
        return [RunState.INTAKE, RunState.DONE]

    monkeypatch.setattr("app.cli.run_pipeline", fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--pause-for-feedback",
            "--feedback-checkpoints",
            "60,30,60",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["pause_for_feedback"] is True
    assert payload["feedback_checkpoints"] == [30, 60]


def test_cli_rejects_invalid_feedback_checkpoints(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr("app.cli.run_pipeline", lambda config: [RunState.INTAKE, RunState.DONE])

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--feedback-checkpoints",
            "bad,50",
        ],
    )

    assert result.exit_code != 0
    assert "feedback_checkpoints must contain integers only" in result.output


def test_cli_maps_strict_fail_fast_flag(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_pipeline(config):
        assert config.strict_fail_fast is True
        return [RunState.INTAKE, RunState.DONE]

    monkeypatch.setattr("app.cli.run_pipeline", fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--strict-fail-fast",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["strict_fail_fast"] is True


def test_cli_maps_resume_run_id(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_pipeline(config):
        assert config.resume_run_id == "run-123"
        return [RunState.INTAKE, RunState.DONE]

    monkeypatch.setattr("app.cli.run_pipeline", fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--resume-run-id",
            "run-123",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["resume_run_id"] == "run-123"


def test_cli_maps_retention_limit(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_pipeline(config):
        assert config.retention_limit == 12
        return [RunState.INTAKE, RunState.DONE]

    monkeypatch.setattr("app.cli.run_pipeline", fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Build AI todo app",
            "--deadline-hours",
            "6",
            "--retention-limit",
            "12",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["retention_limit"] == 12
