from __future__ import annotations

import json
from pathlib import Path

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.orchestrator.pipeline import _search_source_with_timeout, run_pipeline


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
    assert (artifacts / "phase-timings.json").exists()
    assert (artifacts / "command-history.json").exists()
    assert (artifacts / "run-outcome.json").exists()
    assert (run_dirs[0] / "codex-notes.log").exists()

    ranking = json.loads((artifacts / "ranking-preview.json").read_text(encoding="utf-8"))
    titles = [item["title"] for item in ranking["ranked_candidates"]]
    assert not any(title.endswith("- primary path") for title in titles)
    research = json.loads((artifacts / "research-summary.json").read_text(encoding="utf-8"))
    assert "source_cache_hits" in research
    assert "source_cache_misses" in research

    completion = json.loads((artifacts / "completion-contract.json").read_text(encoding="utf-8"))
    assert completion["passed"] is True
    assert completion["checks"]["tests_passed"] is True
    run_outcome = json.loads((artifacts / "run-outcome.json").read_text(encoding="utf-8"))
    assert run_outcome["done"] is True
    assert run_outcome["fatal_errors"] == []
    phase_timings = json.loads((artifacts / "phase-timings.json").read_text(encoding="utf-8"))
    assert "INTAKE" in phase_timings
    command_history = json.loads((artifacts / "command-history.json").read_text(encoding="utf-8"))
    assert isinstance(command_history, list)
    assert all({"command", "cwd", "duration_ms", "returncode"} <= set(item) for item in command_history)
    note_lines = (run_dirs[0] / "codex-notes.log").read_text(encoding="utf-8").splitlines()
    progress_lines = [line for line in note_lines if line.startswith("{")]
    assert progress_lines
    progress_event = json.loads(progress_lines[0])
    assert {"run_id", "phase", "message"} <= set(progress_event)


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

    class _SupportSource:
        source_name = "support"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return [
                {
                    "title": "Support Candidate",
                    "summary": "Secondary candidate for source diversity.",
                    "urls": ["https://github.com/acme/support", "https://devpost.com/software/support"],
                    "stack": ["Django", "Redis", "Postgres", "Celery"],
                    "signals": {"complexity": "high", "setup_steps": 8},
                    "source": "support",
                }
            ]

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"single": _Source(), "support": _SupportSource()},
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


def test_selection_json_marks_evidence_gate_false_for_fallback_recommendation(
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
    selection = json.loads((run_dirs[0] / "artifacts" / "selection.json").read_text(encoding="utf-8"))
    assert selection["selection_mode"] == "auto-fallback"
    assert selection["evidence_gate_passed"] is False


def test_pipeline_creates_deterministic_candidate_when_research_is_empty(
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

    class _EmptySource:
        source_name = "empty"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return []

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"empty": _EmptySource()},
    )

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    ranking = json.loads(
        (run_dirs[0] / "artifacts" / "ranking-preview.json").read_text(encoding="utf-8")
    )
    top = ranking["ranked_candidates"][0]
    assert "verified_code_links" in top
    assert "verified_writeup_links" in top
    assert "verification_errors" in top

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"
    research = json.loads((artifacts / "research-summary.json").read_text(encoding="utf-8"))
    selection = json.loads((artifacts / "selection.json").read_text(encoding="utf-8"))

    assert research["raw_candidate_count"] == 0
    assert research["deduped_candidate_count"] == 1
    assert research["used_fallback_candidate"] is True
    assert research["fallback_provenance"] == "deterministic-research-fallback"
    assert selection["selected_source"] == "fallback"


def test_pipeline_injects_fallback_ranked_option_when_ranking_returns_empty(
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
    monkeypatch.setattr("app.orchestrator.pipeline.rank_candidates", lambda *args, **kwargs: [])

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    ranking = json.loads(
        (run_dirs[0] / "artifacts" / "ranking-preview.json").read_text(encoding="utf-8")
    )

    assert ranking["used_ranking_fallback"] is True
    assert ranking["ranking_warnings"]
    assert len(ranking["ranked_candidates"]) == 1
    assert ranking["ranked_candidates"][0]["fallback_injected"] is True


def test_pipeline_records_phase_errors_and_recovers_in_non_strict_mode(
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
        "app.orchestrator.pipeline.rank_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("rank exploded")),
    )

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    payload = json.loads(
        (run_dirs[0] / "artifacts" / "phase-error-ranking.json").read_text(encoding="utf-8")
    )
    assert payload["state"] == "RANKING"
    assert payload["recovered"] is True


def test_pipeline_verifies_candidate_links_before_ranking(monkeypatch, tmp_path: Path) -> None:
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
                    "title": "AI Planner",
                    "summary": "Planner",
                    "urls": [
                        "https://github.com/acme/planner",
                        "https://devpost.com/software/planner",
                    ],
                    "stack": ["Next.js"],
                    "signals": {"complexity": "low", "setup_steps": 2},
                    "source": "single",
                }
            ]

    class _SupportSource:
        source_name = "support"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return [
                {
                    "title": "Support Candidate",
                    "summary": "Secondary candidate for source diversity.",
                    "urls": ["https://github.com/acme/support", "https://devpost.com/software/support"],
                    "stack": ["Django", "Redis", "Postgres", "Celery"],
                    "signals": {"complexity": "high", "setup_steps": 8},
                    "source": "support",
                }
            ]

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"single": _Source(), "support": _SupportSource()},
    )

    def fake_verify(candidates, policy=None):
        _ = policy
        for candidate in candidates:
            candidate.signals["verified_code_links"] = ["https://github.com/acme/planner"]
            candidate.signals["verified_writeup_links"] = ["https://devpost.com/software/planner"]
            candidate.signals["verification_errors"] = []
        return candidates

    monkeypatch.setattr("app.orchestrator.pipeline.verify_candidates_evidence", fake_verify)

    def fake_rank(candidates, *args, **kwargs):
        _ = (args, kwargs)
        assert candidates[0].signals["verified_code_links"]
        assert candidates[0].signals["verified_writeup_links"]
        return []

    monkeypatch.setattr("app.orchestrator.pipeline.rank_candidates", fake_rank)

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE


def test_pipeline_recovers_when_one_source_times_out(monkeypatch, tmp_path: Path) -> None:
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

    class _FastSource:
        source_name = "fast"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return [
                {
                    "title": "Fast Source Project",
                    "summary": "Fast source",
                    "urls": ["https://github.com/acme/fast", "https://devpost.com/software/fast"],
                    "stack": ["Next.js"],
                    "signals": {"complexity": "low", "setup_steps": 2},
                    "source": "fast",
                }
            ]

    class _SlowSource:
        source_name = "slow"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return []

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"fast": _FastSource(), "slow": _SlowSource()},
    )

    def fake_search_with_timeout(adapter, problem_statement: str, limit: int, timeout_seconds: float = 8.0):
        _ = (problem_statement, limit, timeout_seconds)
        if getattr(adapter, "source_name", "") == "slow":
            raise TimeoutError("search timed out")
        return adapter.search(problem_statement, limit)

    monkeypatch.setattr("app.orchestrator.pipeline._search_source_with_timeout", fake_search_with_timeout)

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    research = json.loads((run_dirs[0] / "artifacts" / "research-summary.json").read_text(encoding="utf-8"))
    assert research["per_source"]["fast"] == 1
    assert research["per_source"]["slow"] == 0


def test_search_source_with_timeout_uses_timeout_guard(monkeypatch) -> None:
    class _Adapter:
        def search(self, problem: str, limit: int):
            _ = problem
            return [{"title": f"item-{limit}"}]

    called = {"timeout": None}

    def fake_run_with_timeout(operation, timeout_seconds: float):
        called["timeout"] = timeout_seconds
        return operation()

    monkeypatch.setattr("app.orchestrator.pipeline.run_with_timeout", fake_run_with_timeout)
    rows = _search_source_with_timeout(_Adapter(), "test", 2, timeout_seconds=3.0)

    assert called["timeout"] == 3.0
    assert rows == [{"title": "item-2"}]


def test_search_source_with_timeout_retries_transient_errors(monkeypatch) -> None:
    class _Adapter:
        def __init__(self) -> None:
            self.calls = 0

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient failure")
            return [{"title": "recovered"}]

    adapter = _Adapter()
    monkeypatch.setattr(
        "app.orchestrator.pipeline.run_with_timeout",
        lambda operation, timeout_seconds: operation(),
    )

    rows = _search_source_with_timeout(adapter, "test", 2, timeout_seconds=3.0, retries=2)
    assert rows == [{"title": "recovered"}]
    assert adapter.calls == 2


def test_pipeline_warns_when_completion_contract_is_not_met(monkeypatch, tmp_path: Path) -> None:
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
    assert transitions[-1] == RunState.DONE

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    artifacts = run_dirs[0] / "artifacts"

    completion = json.loads((artifacts / "completion-contract.json").read_text(encoding="utf-8"))
    assert completion["passed"] is False
    assert "tests_passed" in completion["failed_checks"]
    assert "warning" in completion
    assert completion["strict_fail_fast"] is False


def test_pipeline_fails_when_completion_contract_is_not_met_in_strict_mode(
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
        "app.orchestrator.pipeline._execute_testing_fallback",
        lambda **kwargs: {
            "executed_suite": "none",
            "planned_suites": ["integration", "smoke"],
            "skipped_reasons": {"integration": "suite failed", "smoke": "suite failed"},
            "pass_rate": 0.0,
        },
    )

    config = RunConfig(
        problem_statement="Build secure AI planner",
        deadline_hours=6,
        strict_fail_fast=True,
    )
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.FAILED

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    run_outcome = json.loads(
        (run_dirs[0] / "artifacts" / "run-outcome.json").read_text(encoding="utf-8")
    )
    assert run_outcome["done"] is False
    assert run_outcome["fatal_errors"]


def test_completion_contract_warning_vs_strict_failure_regression(
    monkeypatch, tmp_path: Path
) -> None:
    def fake_render(command, *, config_json, cwd, timeout_seconds=600):
        _ = (command, cwd, timeout_seconds)
        return {
            "rendered": False,
            "fallback": True,
            "reason": "no-remotion",
            "command": "stub",
            "config": config_json,
        }

    monkeypatch.setattr("app.orchestrator.pipeline.execute_render_with_fallback", fake_render)
    monkeypatch.setattr(
        "app.orchestrator.pipeline._execute_testing_fallback",
        lambda **kwargs: {
            "executed_suite": "none",
            "planned_suites": ["integration", "smoke"],
            "skipped_reasons": {"integration": "suite failed", "smoke": "suite failed"},
            "pass_rate": 0.0,
        },
    )

    non_strict_dir = tmp_path / "non-strict"
    non_strict_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(non_strict_dir)
    non_strict = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(non_strict)
    assert transitions[-1] == RunState.DONE

    strict_dir = tmp_path / "strict"
    strict_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(strict_dir)
    strict = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6, strict_fail_fast=True)
    transitions = run_pipeline(strict)
    assert transitions[-1] == RunState.FAILED


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
    assert selection["selection_mode"].startswith("auto-")


def test_default_run_never_requests_interactive_input(monkeypatch, tmp_path: Path) -> None:
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
        "app.orchestrator.pipeline.prompt_for_selection",
        lambda _options: (_ for _ in ()).throw(AssertionError("prompt_for_selection should not be called")),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("input should not be called")),
    )

    config = RunConfig(problem_statement="Build secure AI planner", deadline_hours=6)
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE


def test_pause_for_feedback_triggers_interactive_selection_prompt(
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
                    "title": "Feedback Candidate",
                    "summary": "Detailed project summary with reproducible setup and evidence.",
                    "urls": [
                        "https://github.com/acme/feedback-candidate",
                        "https://devpost.com/software/feedback-candidate",
                    ],
                    "stack": ["Next.js"],
                    "signals": {"complexity": "low", "setup_steps": 2},
                    "source": "single",
                }
            ]

    class _SupportSource:
        source_name = "support"

        def search(self, problem: str, limit: int):
            _ = (problem, limit)
            return [
                {
                    "title": "Support Candidate",
                    "summary": "Secondary candidate for source diversity.",
                    "urls": ["https://github.com/acme/support", "https://devpost.com/software/support"],
                    "stack": ["Django", "Redis", "Postgres", "Celery"],
                    "signals": {"complexity": "high", "setup_steps": 8},
                    "source": "support",
                }
            ]

    monkeypatch.setattr(
        "app.orchestrator.pipeline.build_source_registry",
        lambda include_reddit=False, policy=None: {"single": _Source(), "support": _SupportSource()},
    )
    monkeypatch.setattr(
        "app.orchestrator.pipeline.verify_candidates_evidence",
        lambda candidates, policy=None: candidates,
    )

    prompted = {"count": 0}

    def fake_prompt(_options):
        prompted["count"] += 1
        return 0

    monkeypatch.setattr("app.orchestrator.pipeline.prompt_for_selection", fake_prompt)

    config = RunConfig(
        problem_statement="Build secure AI planner",
        deadline_hours=6,
        pause_for_feedback=True,
        interactive_selection=True,
    )
    transitions = run_pipeline(config)
    assert transitions[-1] == RunState.DONE
    assert prompted["count"] == 1

    run_dirs = list((tmp_path / "runs").glob("*"))
    assert run_dirs
    selection = json.loads((run_dirs[0] / "artifacts" / "selection.json").read_text(encoding="utf-8"))
    assert selection["selection_mode"] == "interactive"
