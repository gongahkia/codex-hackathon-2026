from __future__ import annotations

import json
from pathlib import Path

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.orchestrator.pipeline import run_pipeline
from app.runtime.deployment_watch import DeploymentHealthReport


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


def test_pipeline_warns_on_flaky_deployment_watch_in_non_strict_mode(
    monkeypatch, tmp_path: Path
) -> None:
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
    monkeypatch.setattr(
        "app.orchestrator.pipeline.watch_deployment_health",
        lambda *_args, **_kwargs: DeploymentHealthReport(
            url="https://example.com/health",
            checks=0,
            successes=0,
            success_ratio=0.0,
            stable=False,
            errors=["unstable deployment"],
        ),
    )

    config = RunConfig(
        problem_statement="Build classroom AI app",
        deadline_hours=6,
        deployment_health_url="https://example.com/health",
    )
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    payload = json.loads((run_dirs[0] / "artifacts" / "deployment-health.json").read_text(encoding="utf-8"))
    assert "warning" in payload
    assert payload["stable"] is False


def test_pipeline_fails_fast_on_flaky_deployment_watch_in_strict_mode(
    monkeypatch, tmp_path: Path
) -> None:
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
    monkeypatch.setattr(
        "app.orchestrator.pipeline.enforce_deployment_health",
        lambda _url, policy=None: (_ for _ in ()).throw(RuntimeError("unstable deployment")),
    )

    config = RunConfig(
        problem_statement="Build classroom AI app",
        deadline_hours=6,
        deployment_health_url="https://example.com/health",
        strict_fail_fast=True,
    )
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.FAILED
