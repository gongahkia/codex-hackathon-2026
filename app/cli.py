"""CLI entrypoint for last-minute."""

from __future__ import annotations

from typing import Optional

import typer

from app.models.run_config import DEFAULT_WEIGHTS, RunConfig
from app.models.scoring import Weights

app = typer.Typer(name="last-minute")


@app.command("run")
def run_command(
    problem_statement: Optional[str] = typer.Option(None, "--problem-statement", "-p"),
    deadline_hours: Optional[int] = typer.Option(None, "--deadline-hours", "-d"),
    mode: str = typer.Option("detailed-live", "--mode"),
    option_count: int = typer.Option(5, "--option-count"),
    relevance_weight: float = typer.Option(DEFAULT_WEIGHTS["relevance"], "--relevance-weight"),
    feasibility_weight: float = typer.Option(DEFAULT_WEIGHTS["feasibility"], "--feasibility-weight"),
    speed_weight: float = typer.Option(DEFAULT_WEIGHTS["speed"], "--speed-weight"),
    evidence_weight: float = typer.Option(DEFAULT_WEIGHTS["evidence"], "--evidence-weight"),
    include_reddit: bool = typer.Option(False, "--include-reddit"),
    preferred_stack: Optional[str] = typer.Option(None, "--preferred-stack"),
    video_style: str = typer.Option("pitch", "--video-style"),
    video_duration_sec: int = typer.Option(60, "--video-duration-sec"),
) -> None:
    """Run one last-minute pipeline configuration cycle."""

    if not problem_statement:
        problem_statement = typer.prompt("Problem statement").strip()

    if deadline_hours is None:
        deadline_hours = int(typer.prompt("Deadline (hours)", type=int))

    normalized_weights = Weights(
        relevance=relevance_weight,
        feasibility=feasibility_weight,
        speed=speed_weight,
        evidence=evidence_weight,
    )
    config = RunConfig(
        problem_statement=problem_statement,
        deadline_hours=deadline_hours,
        mode=mode,
        option_count=option_count,
        weights=normalized_weights.model_dump(),
        include_reddit=include_reddit,
        preferred_stack=preferred_stack,
        video_style=video_style,
        video_duration_sec=video_duration_sec,
    )
    typer.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
