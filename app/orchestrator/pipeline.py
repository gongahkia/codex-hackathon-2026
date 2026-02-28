"""Pipeline orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from app.models.candidate import Candidate
from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.models.scoring import Weights
from app.output.qa_pack import generate_judge_qa_pack
from app.output.submission_artifacts import generate_submission_artifact, write_submission_artifact
from app.planner.checkpoints import CheckpointDecision, run_milestone_checkpoints
from app.planner.project_spec import ProjectSpec
from app.runtime.command_runner import CommandResult
from app.runtime.demo_reliability import run_demo_reliability_mode
from app.runtime.deployment_watch import enforce_deployment_health
from app.services.ranking import ScoredCandidate, rank_candidates
from app.video.pitch_narrative import optimize_pitch_narrative
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
    artifacts_dir = Path("runs") / run_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    transitions: list[RunState] = []
    spec: ProjectSpec | None = None

    try:
        for state in PIPELINE_ORDER:
            transitions.append(state)

            if state == RunState.INTAKE:
                _write_json(
                    artifacts_dir / "intake-summary.json",
                    {
                        "problem_statement": config.problem_statement,
                        "hackathon_url": config.hackathon_url,
                        "similar_hackathons": config.similar_hackathons,
                        "intake_notes": config.intake_notes,
                        "judging_rubric_text": config.judging_rubric_text,
                        "prize_tracks": config.prize_tracks,
                        "judging_notes": config.judging_notes,
                    },
                )

            if state == RunState.RANKING:
                preview = _generate_ranking_preview(config)
                _write_json(
                    artifacts_dir / "ranking-preview.json",
                    {
                        "applied_rubric": bool(config.judging_rubric_text),
                        "prize_tracks": config.prize_tracks,
                        "ranked_candidates": preview,
                    },
                )

            if state == RunState.BUILD:
                spec = _default_build_spec(config)
                spec, decisions = run_milestone_checkpoints(
                    spec,
                    completed_by_checkpoint=_default_checkpoint_progress(config, spec),
                )
                _write_json(
                    artifacts_dir / "checkpoint-replan.json",
                    {
                        "project_spec": spec.model_dump(),
                        "decisions": [
                            _serialize_checkpoint_decision(decision) for decision in decisions
                        ],
                    },
                )

            if state == RunState.TEST:
                if spec is None:
                    spec = _default_build_spec(config)

                reliability = run_demo_reliability_mode(
                    artifacts_dir=artifacts_dir,
                    health_url=config.deployment_health_url,
                    demo_route=config.demo_route,
                )
                _write_json(artifacts_dir / "demo-reliability.json", reliability.to_dict())

                health_report = enforce_deployment_health(config.deployment_health_url)
                _write_json(
                    artifacts_dir / "deployment-health.json",
                    health_report.to_dict(),
                )

            if state == RunState.VIDEO:
                _auto_generate_video(config, artifacts_dir)
                if spec is None:
                    spec = _default_build_spec(config)

                pitch_scripts = optimize_pitch_narrative(
                    project_title=spec.title,
                    problem_statement=config.problem_statement,
                    rubric_text=config.judging_rubric_text,
                    evidence_points=spec.features,
                )
                _write_json(artifacts_dir / "pitch-narrative.json", pitch_scripts)

        if spec is None:
            spec = _default_build_spec(config)

        submission = generate_submission_artifact(
            problem_statement=config.problem_statement,
            spec=spec,
            deployment_target=config.deployment_health_url or "localhost fallback",
        )
        write_submission_artifact(artifacts_dir / "submission.md", submission)

        qa_pack = generate_judge_qa_pack(
            problem_statement=config.problem_statement,
            spec=spec,
            rubric_text=config.judging_rubric_text,
            prize_tracks=config.prize_tracks,
        )
        (artifacts_dir / "judge-qa.md").write_text(qa_pack, encoding="utf-8")

        transitions.append(RunState.DONE)
    except Exception as exc:
        _write_json(artifacts_dir / "pipeline-error.json", {"error": str(exc)})
        transitions.append(RunState.FAILED)

    return transitions


def _default_build_spec(config: RunConfig) -> ProjectSpec:
    stack = [config.preferred_stack] if config.preferred_stack else ["Next.js", "SQLite"]
    return ProjectSpec(
        title=config.problem_statement,
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


def _default_checkpoint_progress(
    config: RunConfig,
    spec: ProjectSpec,
) -> Dict[int, int]:
    if config.mode == "fast":
        return {25: 1, 50: 1, 75: 2}
    return {25: 1, 50: 2, 75: len(spec.milestones) - 1}


def _generate_ranking_preview(config: RunConfig) -> List[Dict[str, Any]]:
    candidates = [
        Candidate(
            title=f"{config.problem_statement} - primary path",
            summary="Rapid MVP path optimized for demo readiness.",
            urls=[config.hackathon_url] if config.hackathon_url else [],
            stack=[config.preferred_stack] if config.preferred_stack else ["Next.js"],
            signals={"complexity": "medium", "setup_steps": 3},
            source="intake",
        ),
        Candidate(
            title=f"{config.problem_statement} - extended path",
            summary="Feature-richer path with moderate delivery risk.",
            urls=config.similar_hackathons[:1],
            stack=["Next.js", "Postgres", "Redis"],
            signals={"complexity": "high", "setup_steps": 6},
            source="intake",
        ),
    ]

    ranked = rank_candidates(
        candidates,
        Weights(**config.weights),
        problem_statement=config.problem_statement,
        rubric_text=config.judging_rubric_text,
        prize_tracks=config.prize_tracks,
    )
    return [_serialize_scored_candidate(item) for item in ranked]


def _serialize_scored_candidate(item: ScoredCandidate) -> Dict[str, Any]:
    return {
        "title": item.candidate.title,
        "source": item.candidate.source,
        "total_score": item.total_score,
        "factors": dict(item.factors),
        "applied_weights": dict(item.applied_weights),
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
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
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


def _auto_generate_video(config: RunConfig, artifacts_dir: Path) -> None:
    scenes = _build_storyboard(config)
    config_json = compose_remotion_config(scenes)
    config_path = artifacts_dir / "remotion.config.json"
    config_path.write_text(config_json, encoding="utf-8")

    command = build_remotion_render_command(
        output=artifacts_dir / "demo.mp4",
        props_file=config_path,
    )
    render_result = execute_render_with_fallback(
        command,
        config_json=config_json,
        cwd=Path.cwd(),
    )
    report_path = artifacts_dir / "video-result.json"
    report_path.write_text(
        json.dumps(_serialize_render_result(render_result), indent=2),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
