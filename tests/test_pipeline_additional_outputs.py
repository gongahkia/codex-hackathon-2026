from __future__ import annotations

import json
from pathlib import Path

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.orchestrator.pipeline import run_pipeline


def test_pipeline_generates_submission_pitch_and_qa(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "app.orchestrator.pipeline.execute_render_with_fallback",
        lambda command, *, config_json, cwd, timeout_seconds=600: {
            "rendered": False,
            "fallback": True,
            "reason": "no-remotion",
            "command": " ".join(command),
            "config": config_json,
        },
    )

    config = RunConfig(problem_statement="Build classroom AI app", deadline_hours=6)
    transitions = run_pipeline(config)

    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"

    assert (artifacts / "submission.md").exists()
    assert (artifacts / "judge-qa.md").exists()
    assert (artifacts / "pitch-narrative.json").exists()

    pitch = json.loads((artifacts / "pitch-narrative.json").read_text(encoding="utf-8"))
    assert set(pitch.keys()) == {"60", "90", "120"}


def test_pipeline_fails_fast_on_flaky_deployment_watch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "app.orchestrator.pipeline.execute_render_with_fallback",
        lambda command, *, config_json, cwd, timeout_seconds=600: {
            "rendered": False,
            "fallback": True,
            "reason": "no-remotion",
            "command": " ".join(command),
            "config": config_json,
        },
    )

    def fail_watch(_url):
        raise RuntimeError("unstable deployment")

    monkeypatch.setattr("app.orchestrator.pipeline.enforce_deployment_health", fail_watch)

    config = RunConfig(
        problem_statement="Build classroom AI app",
        deadline_hours=6,
        deployment_health_url="https://example.invalid/health",
    )
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.FAILED
