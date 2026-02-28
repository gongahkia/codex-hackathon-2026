from __future__ import annotations

from typer.testing import CliRunner

from app.cli import app
from app.models.run_state import RunState
from app.services.source_policy import REDDIT_DISCLAIMER


runner = CliRunner()


def test_cli_reddit_optin_requires_explicit_disclaimer(monkeypatch) -> None:
    monkeypatch.setattr("app.cli.run_pipeline", lambda config: [RunState.INTAKE, RunState.DONE])

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Test",
            "--deadline-hours",
            "4",
            "--include-reddit",
        ],
    )

    assert result.exit_code != 0
    assert "requires explicit confirmation" in result.output


def test_cli_reddit_optin_succeeds_with_disclaimer(monkeypatch) -> None:
    monkeypatch.setattr("app.cli.run_pipeline", lambda config: [RunState.INTAKE, RunState.DONE])

    result = runner.invoke(
        app,
        [
            "run",
            "--problem-statement",
            "Test",
            "--deadline-hours",
            "4",
            "--include-reddit",
            "--reddit-confirmation",
            REDDIT_DISCLAIMER,
        ],
    )

    assert result.exit_code == 0
