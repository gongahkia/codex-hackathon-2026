from __future__ import annotations

import json
from pathlib import Path

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.orchestrator.pipeline import run_pipeline


def test_pipeline_writes_research_and_selection_artifacts(monkeypatch, tmp_path: Path) -> None:
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

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)

    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"

    assert (artifacts / "research-summary.json").exists()
    assert (artifacts / "selection.json").exists()
    assert (artifacts / "build-generation.json").exists()
    assert (artifacts / "testing-report.json").exists()
    assert (artifacts / "completion-contract.json").exists()
    assert (run_dirs[0] / "codex-notes.log").exists()

    ranking = json.loads((artifacts / "ranking-preview.json").read_text(encoding="utf-8"))
    titles = [item["title"] for item in ranking["ranked_candidates"]]
    assert not any(title.endswith("- primary path") for title in titles)

    completion = json.loads((artifacts / "completion-contract.json").read_text(encoding="utf-8"))
    assert completion["passed"] is True
    assert completion["checks"]["tests_passed"] is True


def test_pipeline_auto_falls_back_to_top_candidate_when_evidence_gate_fails(
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

    class _Source:
        source_name = "single"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return [
                {
                    "title": "Code-only idea",
                    "summary": "Only code URL present",
                    "urls": ["https://github.com/acme/code-only"],
                    "stack": ["Next.js"],
                    "signals": {"complexity": "low", "setup_steps": 2},
                    "source": "single",
                }
            ]

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"single": _Source()},
    )

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)

    assert transitions[-1] == RunState.DONE
    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"
    selection = json.loads((artifacts / "selection.json").read_text(encoding="utf-8"))
    assert selection["selection_mode"] == "auto-fallback"
    assert selection["evidence_gate_passed"] is False
    assert selection["recommendation_fallback_used"] is True


def test_pipeline_fails_when_completion_contract_is_not_met(monkeypatch, tmp_path: Path) -> None:
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
        "app.orchestrator.pipeline._execute_testing_fallback",
        lambda **kwargs: {
            "executed_suite": "none",
            "planned_suites": ["integration", "smoke"],
            "skipped_reasons": {"integration": "suite failed", "smoke": "suite failed"},
            "pass_rate": 0.0,
        },
    )

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.FAILED

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"

    completion = json.loads((artifacts / "completion-contract.json").read_text(encoding="utf-8"))
    assert completion["passed"] is False
    assert "tests_passed" in completion["failed_checks"]


def test_pipeline_skips_interactive_prompt_when_pause_for_feedback_is_disabled(
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

    def fail_if_prompted(_options):
        raise AssertionError("interactive prompt should be skipped in one-shot mode")

    monkeypatch.setattr("app.orchestrator.pipeline.prompt_for_selection", fail_if_prompted)

    config = RunConfig(
        problem_statement="Build secure AI planner",
        deadline_hours=6,
        interactive_selection=True,
        pause_for_feedback=False,
    )
    transitions = run_pipeline(config)

    assert transitions[-1] == RunState.DONE
    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    selection = json.loads((run_dirs[0] / "artifacts" / "selection.json").read_text(encoding="utf-8"))
    assert selection["selection_mode"] == "auto-evidence"
