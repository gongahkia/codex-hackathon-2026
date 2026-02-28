from __future__ import annotations

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
    assert '"problem_statement":"Build AI todo app"' in result.output.replace(" ", "")
