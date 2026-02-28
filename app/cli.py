"""CLI entrypoint for last-minute."""

from __future__ import annotations

from typing import Optional

import typer

from app.intake.hackathon_link import preprocess_hackathon_input
from app.intake.judging import ingest_judging_context
from app.models.run_config import DEFAULT_WEIGHTS, RunConfig
from app.models.run_state import RunState
from app.models.scoring import Weights
from app.orchestrator.pipeline import run_pipeline
from app.security.url_policy import UrlPolicy
from app.services.mode import parse_mode
from app.services.source_policy import validate_reddit_opt_in

app = typer.Typer(name="last-minute")


@app.callback()
def main() -> None:
    """last-minute CLI root command group."""


@app.command("run")
def run_command(
    problem_statement: Optional[str] = typer.Option(None, "--problem-statement", "-p"),
    hackathon_url: Optional[str] = typer.Option(None, "--hackathon-url"),
    judging_rubric: Optional[str] = typer.Option(None, "--judging-rubric"),
    prize_tracks: Optional[str] = typer.Option(
        None,
        "--prize-tracks",
        help="Comma-separated prize tracks (optional).",
    ),
    deadline_hours: Optional[int] = typer.Option(None, "--deadline-hours", "-d"),
    mode: str = typer.Option("detailed-live", "--mode"),
    option_count: int = typer.Option(5, "--option-count"),
    relevance_weight: float = typer.Option(DEFAULT_WEIGHTS["relevance"], "--relevance-weight"),
    feasibility_weight: float = typer.Option(DEFAULT_WEIGHTS["feasibility"], "--feasibility-weight"),
    speed_weight: float = typer.Option(DEFAULT_WEIGHTS["speed"], "--speed-weight"),
    evidence_weight: float = typer.Option(DEFAULT_WEIGHTS["evidence"], "--evidence-weight"),
    include_reddit: bool = typer.Option(False, "--include-reddit"),
    reddit_confirmation: Optional[str] = typer.Option(None, "--reddit-confirmation"),
    preferred_stack: Optional[str] = typer.Option(None, "--preferred-stack"),
    deployment_health_url: Optional[str] = typer.Option(None, "--deployment-health-url"),
    demo_route: str = typer.Option("/demo", "--demo-route"),
    video_style: str = typer.Option("pitch", "--video-style"),
    video_duration_sec: int = typer.Option(60, "--video-duration-sec"),
) -> None:
    """Run one last-minute pipeline configuration cycle."""

    if not problem_statement and not hackathon_url:
        problem_statement = typer.prompt("Problem statement").strip()

    if deadline_hours is None:
        deadline_hours = int(typer.prompt("Deadline (hours)", type=int))

    try:
        validate_reddit_opt_in(include_reddit, reddit_confirmation)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    try:
        policy = UrlPolicy()
        intake = preprocess_hackathon_input(
            problem_statement=problem_statement,
            hackathon_url=hackathon_url,
            policy=policy,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    provided_tracks = []
    if prize_tracks:
        provided_tracks = [track.strip() for track in prize_tracks.split(",") if track.strip()]

    judging_context = ingest_judging_context(
        hackathon_url=intake.source_url,
        rubric_text=judging_rubric,
        provided_prize_tracks=provided_tracks,
        policy=policy,
    )

    normalized_weights = Weights(
        relevance=relevance_weight,
        feasibility=feasibility_weight,
        speed=speed_weight,
        evidence=evidence_weight,
    )
    config = RunConfig(
        problem_statement=intake.problem_statement,
        hackathon_url=intake.source_url,
        similar_hackathons=intake.similar_hackathons,
        intake_notes=intake.notes,
        judging_rubric_text=judging_context.rubric_text or None,
        prize_tracks=judging_context.prize_tracks,
        judging_notes=judging_context.notes,
        deadline_hours=deadline_hours,
        mode=parse_mode(mode),
        option_count=option_count,
        weights=normalized_weights.model_dump(),
        include_reddit=include_reddit,
        preferred_stack=preferred_stack,
        deployment_health_url=deployment_health_url,
        demo_route=demo_route,
        video_style=video_style,
        video_duration_sec=video_duration_sec,
    )
    transitions = run_pipeline(config)
    terminal_state = transitions[-1] if transitions else RunState.FAILED

    if terminal_state == RunState.FAILED:
        typer.echo("Run failed", err=True)
        raise typer.Exit(code=1)

    typer.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
