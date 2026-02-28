"""Pipeline orchestration."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from app.generation.api_app import APIAppGenerator
from app.generation.web_app import WebAppGenerator
from app.models.candidate import Candidate
from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.models.scoring import Weights
from app.output.qa_pack import generate_judge_qa_pack
from app.output.submission_artifacts import generate_submission_artifact
from app.planner.checkpoints import CheckpointDecision, run_milestone_checkpoints
from app.planner.project_spec import ProjectSpec
from app.runtime.command_runner import CommandResult
from app.runtime.demo_reliability import run_demo_reliability_mode
from app.runtime.deployment_watch import enforce_deployment_health, watch_deployment_health
from app.runtime.healthcheck import probe_dev_server
from app.runtime.install import run_dependency_install
from app.resilience.circuit_breaker import CircuitBreaker
from app.resilience.retry import retry_with_jitter
from app.resilience.timeouts import run_with_timeout
from app.security.redaction import redact_secrets
from app.security.url_policy import UrlPolicy
from app.services.dedupe import dedupe_by_title_similarity, dedupe_by_url_hash
from app.services.evidence_gate import passes_minimum_evidence
from app.services.evidence_verification import verify_candidates_evidence
from app.services.mode_policy import detailed_mode_source_limits, fast_mode_source_limits
from app.services.ranking import ScoredCandidate, rank_candidates
from app.services.recommendation import choose_recommendation_with_fallback
from app.services.selection import prompt_for_selection
from app.sources.registry import build_source_registry
from app.storage import RunStore, SafeArtifactWriter
from app.storage.cache import RunLocalSourceCache
from app.testing.e2e_playwright import run_playwright_e2e
from app.testing.fallback import run_tests_with_fallback
from app.testing.integration_pytest import run_pytest_integration
from app.testing.integration_vitest import run_vitest_integration
from app.testing.strategy import select_test_plan
from app.telemetry.timings import PhaseTimingCollector
from app.video.pitch_narrative import optimize_pitch_narrative
from app.video.project_bundle import ensure_remotion_bundle
from app.video.remotion_config import compose_remotion_config
from app.video.render_command import build_remotion_render_command
from app.video.render_executor import execute_render_with_fallback
from app.video.storyboards.pitch import generate_pitch_storyboard
from app.video.storyboards.walkthrough import generate_walkthrough_storyboard

PIPELINE_ORDER = [
    RunState.INTAKE,
    RunState.RESEARCH,
    RunState.RANKING,
    RunState.SELECTION,
    RunState.BUILD,
    RunState.TEST,
    RunState.VIDEO,
]


def run_pipeline(config: RunConfig) -> list[RunState]:
    """Run the pipeline and record state transitions."""

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    run_root = Path("runs") / run_id
    artifacts_dir = run_root / "artifacts"
    project_dir = run_root / "project"
    notes_path = run_root / "codex-notes.log"

    writer = SafeArtifactWriter(artifacts_dir)
    project_writer = SafeArtifactWriter(project_dir)

    _append_note(
        notes_path,
        "RUN_START",
        (
            f"problem={config.problem_statement!r} mode={config.mode} "
            f"pause_for_feedback={config.pause_for_feedback} strict_fail_fast={config.strict_fail_fast}"
        ),
    )

    store = RunStore(db_path="runs.db")
    store.save_config(run_id, config.model_dump())

    transitions: list[RunState] = []
    spec: ProjectSpec | None = None
    candidates: list[Candidate] = []
    ranked: list[ScoredCandidate] = []
    selected: ScoredCandidate | None = None
    generated_files: list[str] = []
    build_execution: Dict[str, Any] | None = None
    testing_report: Dict[str, Any] | None = None
    reliability_report: Dict[str, Any] | None = None
    deployment_health_report: Dict[str, Any] | None = None
    video_result: Dict[str, Any] | None = None
    warnings: list[str] = []
    recoveries: list[str] = []
    fatal_errors: list[str] = []
    phase_timings = PhaseTimingCollector()

    try:
        for state in PIPELINE_ORDER:
            transitions.append(state)
            store.append_transition(run_id, state.value)
            _append_note(notes_path, "STATE", state.value)
            _append_progress_event(notes_path, run_id=run_id, phase=state.value, message="entered")
            phase_timings.start(state.value)

            try:
                if state == RunState.INTAKE:
                    writer.write_json(
                        "intake-summary.json",
                        {
                            "problem_statement": config.problem_statement,
                            "hackathon_url": config.hackathon_url,
                            "similar_hackathons": config.similar_hackathons,
                            "intake_notes": config.intake_notes,
                            "judging_rubric_text": config.judging_rubric_text,
                            "prize_tracks": config.prize_tracks,
                            "judging_notes": config.judging_notes,
                            "selected_option": config.selected_option,
                            "interactive_selection": config.interactive_selection,
                            "pause_for_feedback": config.pause_for_feedback,
                            "strict_fail_fast": config.strict_fail_fast,
                            "allow_local_health": config.allow_local_health,
                            "run_log_path": str(notes_path.resolve()),
                        },
                    )

                if state == RunState.RESEARCH:
                    policy = UrlPolicy()
                    registry = build_source_registry(include_reddit=config.include_reddit, policy=policy)
                    source_limits = (
                        fast_mode_source_limits() if config.mode == "fast" else detailed_mode_source_limits()
                    )
                    source_cache = RunLocalSourceCache(run_root / "cache" / "sources")

                    gathered: list[Candidate] = []
                    per_source: dict[str, int] = {}
                    cache_hits = 0
                    cache_misses = 0
                    rows_by_source: dict[str, list[dict[str, Any]]] = {}
                    pending: dict[Future[list[dict[str, Any]]], tuple[str, int]] = {}
                    breakers = {source_name: CircuitBreaker() for source_name in registry}
                    max_workers = max(1, min(4, len(registry)))
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        for source_name, adapter in registry.items():
                            limit = source_limits.get(source_name, 3)
                            cached_rows = source_cache.get(source_name, config.problem_statement, limit)
                            if cached_rows is not None:
                                cache_hits += 1
                                rows_by_source[source_name] = cached_rows
                                continue

                            cache_misses += 1
                            breaker = breakers[source_name]
                            if not breaker.allow_request():
                                rows_by_source[source_name] = []
                                _append_note(
                                    notes_path,
                                    "WARNING",
                                    f"source={source_name} skipped_by_circuit_breaker",
                                )
                                continue
                            future = executor.submit(
                                _search_source_with_timeout,
                                adapter,
                                config.problem_statement,
                                limit,
                            )
                            pending[future] = (source_name, limit)

                        for future in as_completed(pending):
                            source_name, limit = pending[future]
                            breaker = breakers[source_name]
                            try:
                                rows = future.result()
                                breaker.record_success()
                            except Exception as exc:
                                breaker.record_failure()
                                rows = []
                                _append_note(
                                    notes_path,
                                    "WARNING",
                                    f"source={source_name} search_error={redact_secrets(str(exc))}",
                                )
                            rows_by_source[source_name] = rows
                            source_cache.set(source_name, config.problem_statement, limit, rows)

                    for source_name in registry:
                        rows = rows_by_source.get(source_name, [])
                        per_source[source_name] = len(rows)
                        for row in rows:
                            try:
                                candidate = Candidate(**row)
                                if candidate.fetched_at is None:
                                    candidate.fetched_at = datetime.now(UTC)
                                if not candidate.source_query:
                                    candidate.source_query = config.problem_statement
                                gathered.append(candidate)
                            except Exception:
                                continue

                    deduped = dedupe_by_url_hash(gathered)
                    deduped = dedupe_by_title_similarity(deduped)
                    candidates = deduped
                    used_research_fallback = False
                    if not candidates:
                        candidates = [_build_research_fallback_candidate(config.problem_statement)]
                        used_research_fallback = True
                    candidates = verify_candidates_evidence(candidates, policy=policy)

                    writer.write_json(
                        "research-summary.json",
                        {
                            "raw_candidate_count": len(gathered),
                            "deduped_candidate_count": len(candidates),
                            "per_source": per_source,
                            "used_fallback_candidate": used_research_fallback,
                            "fallback_provenance": (
                                candidates[0].signals.get("provenance") if used_research_fallback else None
                            ),
                            "source_cache_hits": cache_hits,
                            "source_cache_misses": cache_misses,
                            "verified_code_candidate_count": sum(
                                1 for candidate in candidates if candidate.signals.get("verified_code_links")
                            ),
                            "verified_writeup_candidate_count": sum(
                                1 for candidate in candidates if candidate.signals.get("verified_writeup_links")
                            ),
                        },
                    )
                    _append_note(
                        notes_path,
                        "RESEARCH",
                        f"raw={len(gathered)} deduped={len(candidates)} per_source={per_source}",
                    )

                if state == RunState.RANKING:
                    if not candidates:
                        raise RuntimeError("Cannot rank without research candidates")

                    weights = Weights(**config.weights)
                    ranked = rank_candidates(
                        candidates,
                        weights,
                        problem_statement=config.problem_statement,
                        rubric_text=config.judging_rubric_text,
                        prize_tracks=config.prize_tracks,
                    )
                    ranking_warnings: list[str] = []
                    used_ranking_fallback = False
                    if not ranked:
                        used_ranking_fallback = True
                        ranking_warnings.append(
                            "Ranking returned no options; injected deterministic fallback candidate."
                        )
                        ranked = [_build_ranking_fallback(candidates[0], weights)]
                    writer.write_json(
                        "ranking-preview.json",
                        {
                            "applied_rubric": bool(config.judging_rubric_text),
                            "prize_tracks": config.prize_tracks,
                            "used_ranking_fallback": used_ranking_fallback,
                            "ranking_warnings": ranking_warnings,
                            "ranked_candidates": [
                                {
                                    **_serialize_scored_candidate(item),
                                    "rank": index + 1,
                                    "fallback_injected": used_ranking_fallback and index == 0,
                                }
                                for index, item in enumerate(ranked[: config.option_count])
                            ],
                        },
                    )
                    _append_note(
                        notes_path,
                        "RANKING",
                        (
                            f"ranked_count={len(ranked)} "
                            f"top_title={(ranked[0].candidate.title if ranked else 'none')} "
                            f"fallback={used_ranking_fallback}"
                        ),
                    )

                if state == RunState.SELECTION:
                    if not ranked:
                        raise RuntimeError("Selection requires ranked candidates")

                    selected, selection_mode, selected_rank, evidence_gate_passed = _select_candidate(
                        config, ranked
                    )
                    writer.write_json(
                        "selection.json",
                        {
                            "selected_title": selected.candidate.title,
                            "selected_source": selected.candidate.source,
                            "total_score": selected.total_score,
                            "selected_urls": selected.candidate.urls,
                            "evidence_gate_passed": evidence_gate_passed,
                            "recommendation_fallback_used": not evidence_gate_passed,
                            "selection_mode": selection_mode,
                            "selected_rank": selected_rank,
                        },
                    )
                    _append_note(
                        notes_path,
                        "SELECTION",
                        (
                            f"mode={selection_mode} rank={selected_rank} "
                            f"title={selected.candidate.title} evidence_gate_passed={evidence_gate_passed}"
                        ),
                    )

                if state == RunState.BUILD:
                    spec = _default_build_spec(config, selected)
                    spec, decisions = run_milestone_checkpoints(
                        spec,
                        completed_by_checkpoint=_default_checkpoint_progress(config, spec),
                    )
                    writer.write_json(
                        "checkpoint-replan.json",
                        {
                            "project_spec": spec.model_dump(),
                            "decisions": [_serialize_checkpoint_decision(decision) for decision in decisions],
                        },
                    )

                    generator_name, files = _generate_project_files(spec)
                    for relative_path, content in files.items():
                        project_writer.write_text(relative_path, content)

                    build_execution = _run_build_execution(project_writer.root)
                    generated_files = sorted(files.keys())
                    writer.write_json(
                        "build-generation.json",
                        {
                            "generator": generator_name,
                            "project_root": str(project_writer.root),
                            "generated_files": generated_files,
                            "build_execution": build_execution,
                        },
                    )
                    _append_note(
                        notes_path,
                        "BUILD",
                        f"generator={generator_name} files={len(files)} install_status={build_execution.get('status')}",
                    )

                    submission = generate_submission_artifact(
                        problem_statement=config.problem_statement,
                        spec=spec,
                        deployment_target=config.deployment_health_url or "localhost fallback",
                    )
                    writer.write_text("submission.md", submission)

                    qa_pack = generate_judge_qa_pack(
                        problem_statement=config.problem_statement,
                        spec=spec,
                        rubric_text=config.judging_rubric_text,
                        prize_tracks=config.prize_tracks,
                    )
                    writer.write_text("judge-qa.md", qa_pack)

                if state == RunState.TEST:
                    if spec is None:
                        spec = _default_build_spec(config, selected)

                    reliability = run_demo_reliability_mode(
                        artifacts_dir=artifacts_dir,
                        health_url=config.deployment_health_url,
                        demo_route=config.demo_route,
                        allow_local_health=config.allow_local_health,
                    )
                    reliability_report = reliability.to_dict()
                    writer.write_json("demo-reliability.json", reliability_report)

                    health_warning: str | None = None
                    try:
                        if config.allow_local_health:
                            health_report = enforce_deployment_health(
                                config.deployment_health_url,
                                policy=_runtime_health_policy(True),
                            )
                        else:
                            health_report = enforce_deployment_health(config.deployment_health_url)
                    except Exception as exc:
                        if config.strict_fail_fast:
                            raise
                        health_warning = redact_secrets(str(exc))
                        _append_note(notes_path, "WARNING", f"deployment_health: {health_warning}")
                        warnings.append(f"TEST: deployment_health: {health_warning}")
                        recoveries.append("TEST")
                        try:
                            health_report = watch_deployment_health(
                                config.deployment_health_url,
                                policy=_runtime_health_policy(config.allow_local_health),
                            )
                        except Exception:
                            health_report = watch_deployment_health(None)
                    deployment_health_report = health_report.to_dict()
                    if health_warning:
                        deployment_health_report["warning"] = health_warning
                    writer.write_json("deployment-health.json", deployment_health_report)

                    testing_report = _execute_testing_fallback(
                        config=config,
                        project_root=project_writer.root,
                        health_url=config.deployment_health_url,
                    )
                    writer.write_json("testing-report.json", testing_report)
                    _append_note(
                        notes_path,
                        "TEST",
                        f"executed_suite={testing_report['executed_suite']} pass_rate={testing_report['pass_rate']}",
                    )

                if state == RunState.VIDEO:
                    video_result = _auto_generate_video(config, writer, run_root)
                    if spec is None:
                        spec = _default_build_spec(config, selected)

                    pitch_scripts = optimize_pitch_narrative(
                        project_title=spec.title,
                        problem_statement=config.problem_statement,
                        rubric_text=config.judging_rubric_text,
                        evidence_points=spec.features,
                    )
                    writer.write_json("pitch-narrative.json", pitch_scripts)
            except Exception as exc:
                message = redact_secrets(str(exc))
                writer.write_json(
                    f"phase-error-{state.value.lower()}.json",
                    {
                        "state": state.value,
                        "error": message,
                        "recovered": not config.strict_fail_fast,
                        "strict_fail_fast": config.strict_fail_fast,
                    },
                )
                _append_note(notes_path, "WARNING", f"state={state.value} error={message}")
                warnings.append(f"{state.value}: {message}")
                if config.strict_fail_fast:
                    raise
                recoveries.append(state.value)
                continue
            finally:
                phase_timings.stop(state.value)

        completion = _evaluate_completion_contract(
            artifacts_dir=artifacts_dir,
            selected=selected,
            generated_files=generated_files,
            build_execution=build_execution,
            testing_report=testing_report,
            reliability_report=reliability_report,
            deployment_health_report=deployment_health_report,
        )
        completion_warning: str | None = None
        if not completion["passed"]:
            failed = ", ".join(completion["failed_checks"])
            completion_warning = f"Completion contract failed: {failed}"
            completion["warning"] = completion_warning
            completion["strict_fail_fast"] = config.strict_fail_fast
        writer.write_json("completion-contract.json", completion)
        _append_note(
            notes_path,
            "COMPLETION",
            f"passed={completion['passed']} failed={len(completion['failed_checks'])}",
        )
        if completion_warning:
            if config.strict_fail_fast:
                raise RuntimeError(completion_warning)
            _append_note(notes_path, "WARNING", completion_warning)
            warnings.append(completion_warning)
            recoveries.append("COMPLETION")

        writer.write_json(
            "command-history.json",
            _build_command_history(
                build_execution=build_execution,
                testing_report=testing_report,
                video_result=video_result,
            ),
        )
        writer.write_json("phase-timings.json", phase_timings.as_dict())
        writer.write_json(
            "run-outcome.json",
            {
                "done": True,
                "warnings": warnings,
                "recoveries": recoveries,
                "fatal_errors": fatal_errors,
            },
        )

        transitions.append(RunState.DONE)
        store.append_transition(run_id, RunState.DONE.value)
        store.set_final_status(
            run_id,
            RunState.DONE.value,
            recommendation_title=selected.candidate.title if selected else "",
            warning_count=len(warnings),
            fatal_count=len(fatal_errors),
            last_error_code="",
        )
        _append_note(notes_path, "RUN_DONE", f"recommendation={(selected.candidate.title if selected else '')}")
    except Exception as exc:
        fatal_error = redact_secrets(str(exc))
        fatal_errors.append(fatal_error)
        writer.write_json("pipeline-error.json", {"error": fatal_error})
        writer.write_json(
            "command-history.json",
            _build_command_history(
                build_execution=build_execution,
                testing_report=testing_report,
                video_result=video_result,
            ),
        )
        writer.write_json("phase-timings.json", phase_timings.as_dict())
        writer.write_json(
            "run-outcome.json",
            {
                "done": False,
                "warnings": warnings,
                "recoveries": recoveries,
                "fatal_errors": fatal_errors,
            },
        )
        transitions.append(RunState.FAILED)
        store.append_transition(run_id, RunState.FAILED.value)
        store.set_final_status(
            run_id,
            RunState.FAILED.value,
            warning_count=len(warnings),
            fatal_count=len(fatal_errors),
            last_error_code=_derive_error_code(fatal_error),
        )
        _append_note(notes_path, "RUN_FAILED", fatal_error)

    return transitions


def _default_build_spec(config: RunConfig, selected: ScoredCandidate | None) -> ProjectSpec:
    selected_candidate = selected.candidate if selected is not None else None
    stack = [config.preferred_stack] if config.preferred_stack else None
    if not stack:
        stack = (
            selected_candidate.stack
            if selected_candidate and selected_candidate.stack
            else ["Next.js", "SQLite"]
        )

    title = selected_candidate.title if selected_candidate else config.problem_statement

    return ProjectSpec(
        title=title,
        features=[
            "Core user flow",
            "Submission-ready content",
            "Reliable demo route",
        ],
        stack=stack,
        milestones=[
            "Scaffold project",
            "Implement core flow",
            "Stabilize and test",
            "Prepare demo and submission artifacts",
        ],
    )


def _default_checkpoint_progress(config: RunConfig, spec: ProjectSpec) -> Dict[int, int]:
    if config.mode == "fast":
        return {25: 1, 50: 1, 75: 2}
    return {25: 1, 50: 2, 75: len(spec.milestones) - 1}


def _serialize_scored_candidate(item: ScoredCandidate) -> Dict[str, Any]:
    verified_code_links = item.candidate.signals.get("verified_code_links", [])
    verified_writeup_links = item.candidate.signals.get("verified_writeup_links", [])
    verification_errors = (
        item.candidate.verification_errors
        if item.candidate.verification_errors
        else item.candidate.signals.get("verification_errors", [])
    )
    return {
        "title": item.candidate.title,
        "source": item.candidate.source,
        "fetched_at": item.candidate.fetched_at.isoformat() if item.candidate.fetched_at else None,
        "verified_at": item.candidate.verified_at.isoformat() if item.candidate.verified_at else None,
        "source_query": item.candidate.source_query,
        "total_score": item.total_score,
        "factors": dict(item.factors),
        "applied_weights": dict(item.applied_weights),
        "verified_code_links": list(verified_code_links) if isinstance(verified_code_links, list) else [],
        "verified_writeup_links": (
            list(verified_writeup_links) if isinstance(verified_writeup_links, list) else []
        ),
        "verification_errors": list(verification_errors) if isinstance(verification_errors, list) else [],
        "track_fit": [
            {
                "track": rec.track,
                "fit_score": rec.fit_score,
                "competitiveness": rec.competitiveness,
                "rationale": rec.rationale,
            }
            for rec in item.track_fit
        ],
    }


def _runtime_health_policy(allow_local_health: bool) -> UrlPolicy:
    return UrlPolicy(
        allowed_schemes=("https", "http") if allow_local_health else ("https",),
        allow_localhost=allow_local_health,
    )


def _select_candidate(
    config: RunConfig,
    ranked: list[ScoredCandidate],
) -> tuple[ScoredCandidate, str, int, bool]:
    support = [item.candidate for item in ranked]

    if config.selected_option is not None:
        index = config.selected_option - 1
        if index < 0 or index >= len(ranked):
            raise ValueError(
                f"selected_option={config.selected_option} is out of range for {len(ranked)} ranked options"
            )
        selected = ranked[index]
        if not passes_minimum_evidence(selected.candidate, support):
            raise ValueError("Explicitly selected candidate failed evidence gate")
        return selected, "selected-option", index + 1, True

    if config.pause_for_feedback and config.interactive_selection:
        options = [f"{item.candidate.title} (score={item.total_score:.3f})" for item in ranked]
        index = prompt_for_selection(options)
        selected = ranked[index]
        if not passes_minimum_evidence(selected.candidate, support):
            raise ValueError("Interactively selected candidate failed evidence gate")
        return selected, "interactive", index + 1, True

    selected, used_fallback = choose_recommendation_with_fallback(ranked)
    index = ranked.index(selected)
    return (
        selected,
        "auto-fallback" if used_fallback else "auto-evidence",
        index + 1,
        not used_fallback,
    )


def _generate_project_files(spec: ProjectSpec) -> tuple[str, dict[str, str]]:
    joined = " ".join(spec.stack).lower()
    if any(token in joined for token in ("python", "fastapi", "flask", "django", "api")):
        generator = APIAppGenerator()
        return "api", generator.generate(spec)

    generator = WebAppGenerator()
    return "web", generator.generate(spec)


def _run_build_execution(project_root: Path) -> Dict[str, Any]:
    if (project_root / "package.json").exists():
        result = run_dependency_install(cwd=project_root, command=("npm", "install"), retries=1)
        return {
            "status": "executed",
            "command": ["npm", "install"],
            "cwd": str(project_root),
            "returncode": result.returncode,
            "timed_out": result.timed_out,
            "duration_ms": result.duration_ms,
            "stdout": redact_secrets(result.stdout),
            "stderr": redact_secrets(result.stderr),
        }

    if (project_root / "requirements.txt").exists():
        return {
            "status": "skipped",
            "reason": "python dependency install is not enabled by allowlist policy",
        }

    return {
        "status": "skipped",
        "reason": "no known build/install manifest found",
    }


def _execute_testing_fallback(
    *,
    config: RunConfig,
    project_root: Path,
    health_url: str | None,
) -> Dict[str, Any]:
    plan = select_test_plan(config.deadline_hours * 60)

    def smoke_runner() -> CommandResult:
        target = health_url
        if not target and config.allow_local_health:
            target = "http://localhost:3000/health"

        if not target:
            return CommandResult(
                returncode=1,
                stdout="",
                stderr="smoke skipped: no health url configured",
                timed_out=False,
            )

        ok = probe_dev_server(
            target,
            retries=3,
            delay_seconds=1.0,
            timeout_seconds=2.0,
            policy=_runtime_health_policy(config.allow_local_health),
        )
        return CommandResult(
            returncode=0 if ok else 1,
            stdout=f"smoke target: {target}",
            stderr="" if ok else f"smoke probe failed: {target}",
            timed_out=False,
        )

    runners: Dict[str, Callable[[], CommandResult]] = {
        "smoke": smoke_runner,
    }

    if (project_root / "package.json").exists():
        if _has_playwright_config(project_root):
            runners["e2e"] = lambda: run_playwright_e2e(project_root)
        runners["integration"] = lambda: run_vitest_integration(project_root)
    elif _looks_like_python_project(project_root):
        runners["integration"] = lambda: run_pytest_integration(project_root)

    fallback = run_tests_with_fallback(plan, runners)
    result_payload: Dict[str, Any] = {
        "executed_suite": fallback.executed_suite,
        "planned_suites": plan,
        "skipped_reasons": fallback.skipped_reasons,
        "pass_rate": 1.0
        if fallback.result is not None and fallback.result.returncode == 0 and not fallback.result.timed_out
        else 0.0,
    }

    if fallback.result is not None:
        result_payload["result"] = {
            "returncode": fallback.result.returncode,
            "stdout": redact_secrets(fallback.result.stdout),
            "stderr": redact_secrets(fallback.result.stderr),
            "timed_out": fallback.result.timed_out,
            "duration_ms": fallback.result.duration_ms,
        }

    return result_payload


def _has_playwright_config(project_root: Path) -> bool:
    return any(
        (project_root / candidate).exists()
        for candidate in ("playwright.config.ts", "playwright.config.js", "playwright.config.mjs")
    )


def _looks_like_python_project(project_root: Path) -> bool:
    if (project_root / "main.py").exists() or (project_root / "pytest.ini").exists():
        return True
    return any(project_root.glob("tests/test_*.py"))


def _build_execution_passed(build_execution: Dict[str, Any] | None) -> bool:
    if not build_execution:
        return False

    status = build_execution.get("status")
    if status == "executed":
        return (
            int(build_execution.get("returncode", 1)) == 0
            and not bool(build_execution.get("timed_out", False))
        )

    if status == "skipped":
        reason = str(build_execution.get("reason", ""))
        return reason in {
            "python dependency install is not enabled by allowlist policy",
            "no known build/install manifest found",
        }

    return False


def _search_source_with_timeout(
    adapter: Any,
    problem_statement: str,
    limit: int,
    timeout_seconds: float = 8.0,
    retries: int = 2,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    rows = retry_with_jitter(
        lambda: run_with_timeout(
            lambda: adapter.search(problem_statement, limit),
            timeout_seconds=timeout_seconds,
        ),
        retries=max(0, retries),
        base_delay_seconds=0.2,
        jitter_seconds=0.1,
    )
    return [row for row in rows if isinstance(row, dict)]


def _build_research_fallback_candidate(problem_statement: str) -> Candidate:
    title = f"{problem_statement.strip()} (deterministic fallback)"
    return Candidate(
        title=title,
        summary="Generated fallback candidate because live research returned no viable options.",
        urls=[],
        stack=["Next.js", "SQLite"],
        signals={
            "provenance": "deterministic-research-fallback",
            "fallback_reason": "no_research_candidates",
            "generated_from_problem_statement": problem_statement.strip(),
        },
        source="fallback",
        source_query=problem_statement.strip(),
        fetched_at=datetime.now(UTC),
    )


def _build_ranking_fallback(candidate: Candidate, weights: Weights) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=candidate,
        factors={
            "relevance": 0.0,
            "feasibility": 0.0,
            "speed": 0.0,
            "evidence": 0.0,
        },
        total_score=0.0,
        applied_weights=weights.model_dump(),
        track_fit=[],
    )


def _evaluate_completion_contract(
    *,
    artifacts_dir: Path,
    selected: ScoredCandidate | None,
    generated_files: list[str],
    build_execution: Dict[str, Any] | None,
    testing_report: Dict[str, Any] | None,
    reliability_report: Dict[str, Any] | None,
    deployment_health_report: Dict[str, Any] | None,
) -> Dict[str, Any]:
    required_artifacts = [
        "intake-summary.json",
        "research-summary.json",
        "ranking-preview.json",
        "selection.json",
        "checkpoint-replan.json",
        "build-generation.json",
        "testing-report.json",
        "demo-reliability.json",
        "deployment-health.json",
        "video-result.json",
        "pitch-narrative.json",
        "submission.md",
        "judge-qa.md",
    ]

    executed_suite = str((testing_report or {}).get("executed_suite", "none"))
    pass_rate = float((testing_report or {}).get("pass_rate", 0.0))

    checks = {
        "selection_present": selected is not None,
        "project_generated": bool(generated_files),
        "core_logic_generated": any(
            candidate in generated_files
            for candidate in ("src/core-logic.js", "main.py")
        ),
        "build_execution_ok": _build_execution_passed(build_execution),
        "tests_passed": executed_suite != "none" and pass_rate >= 1.0,
        "demo_reliability_stable": bool((reliability_report or {}).get("stable", False)),
        "deployment_health_stable": bool((deployment_health_report or {}).get("stable", False)),
        "required_artifacts_present": all((artifacts_dir / name).exists() for name in required_artifacts),
    }

    failed_checks = [name for name, passed in checks.items() if not passed]
    return {
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "executed_suite": executed_suite,
        "pass_rate": pass_rate,
        "generated_files": generated_files,
    }


def _build_storyboard(config: RunConfig):
    if config.video_style == "walkthrough":
        return generate_walkthrough_storyboard(
            project_title=config.problem_statement,
            duration_sec=config.video_duration_sec,
        )
    return generate_pitch_storyboard(
        project_title=config.problem_statement,
        duration_sec=config.video_duration_sec,
    )


def _serialize_render_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    serializable = dict(payload)
    result = serializable.get("result")
    if isinstance(result, CommandResult):
        serializable["result"] = {
            "returncode": result.returncode,
            "stdout": redact_secrets(result.stdout),
            "stderr": redact_secrets(result.stderr),
            "timed_out": result.timed_out,
            "duration_ms": result.duration_ms,
        }
    return serializable


def _serialize_checkpoint_decision(decision: CheckpointDecision) -> Dict[str, Any]:
    return {
        "checkpoint_percent": decision.checkpoint_percent,
        "expected_completed": decision.expected_completed,
        "actual_completed": decision.actual_completed,
        "behind_by": decision.behind_by,
        "forced_feature_cuts": decision.forced_feature_cuts,
    }


def _auto_generate_video(
    config: RunConfig,
    writer: SafeArtifactWriter,
    run_root: Path,
) -> Dict[str, Any]:
    scenes = _build_storyboard(config)
    config_json = compose_remotion_config(scenes)
    config_path = writer.write_text("remotion.config.json", config_json)
    video_workspace = run_root.resolve() / "video"
    entry_path = ensure_remotion_bundle(video_workspace)

    command = build_remotion_render_command(
        entry=entry_path,
        output=writer.root / "demo.mp4",
        props_file=config_path,
    )
    render_result = execute_render_with_fallback(
        command,
        config_json=config_json,
        cwd=video_workspace,
    )
    serialized = _serialize_render_result(render_result)
    writer.write_json("video-result.json", serialized)
    return serialized


def _append_note(path: Path, event: str, detail: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {event}: {detail}\n")


def _append_progress_event(path: Path, *, run_id: str, phase: str, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "phase": phase,
        "message": message,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _derive_error_code(message: str) -> str:
    head = (message or "").strip().split(":")[0].strip()
    if not head:
        return "UNSPECIFIED_ERROR"
    return "_".join(head.upper().split())[:80]


def _build_command_history(
    *,
    build_execution: Dict[str, Any] | None,
    testing_report: Dict[str, Any] | None,
    video_result: Dict[str, Any] | None,
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []

    if build_execution and build_execution.get("status") == "executed":
        command = build_execution.get("command", [])
        if isinstance(command, list):
            command_text = " ".join(str(item) for item in command)
        else:
            command_text = str(command)
        history.append(
            {
                "command": command_text,
                "cwd": str(build_execution.get("cwd", "")),
                "duration_ms": int(build_execution.get("duration_ms", 0) or 0),
                "returncode": int(build_execution.get("returncode", 1) or 1),
            }
        )

    test_result = (testing_report or {}).get("result", {})
    if isinstance(test_result, dict):
        command = test_result.get("command")
        if command:
            history.append(
                {
                    "command": str(command),
                    "cwd": str(test_result.get("cwd", "")),
                    "duration_ms": int(test_result.get("duration_ms", 0) or 0),
                    "returncode": int(test_result.get("returncode", 1) or 1),
                }
            )

    if isinstance(video_result, dict):
        command = video_result.get("command")
        result = video_result.get("result", {})
        if command:
            returncode = 0
            duration_ms = 0
            if isinstance(result, dict):
                returncode = int(result.get("returncode", 0) or 0)
                duration_ms = int(result.get("duration_ms", 0) or 0)
            history.append(
                {
                    "command": str(command),
                    "cwd": "",
                    "duration_ms": duration_ms,
                    "returncode": returncode,
                }
            )

    return history
