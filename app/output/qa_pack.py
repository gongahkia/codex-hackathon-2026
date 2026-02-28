"""Mentor and judge Q&A pack generation."""

from __future__ import annotations

from typing import Iterable

from app.planner.project_spec import ProjectSpec


def generate_judge_qa_pack(
    *,
    problem_statement: str,
    spec: ProjectSpec,
    rubric_text: str | None = None,
    prize_tracks: Iterable[str] | None = None,
) -> str:
    """Generate a concise Q&A pack for mentor/judge discussions."""

    tracks = list(prize_tracks or [])
    focus = "delivery quality"
    rubric_lower = (rubric_text or "").lower()
    if "innovation" in rubric_lower:
        focus = "innovation"
    elif "impact" in rubric_lower:
        focus = "user impact"
    elif "technical" in rubric_lower:
        focus = "technical execution"

    track_line = ", ".join(tracks[:3]) if tracks else "general track"
    stack_line = ", ".join(spec.stack) if spec.stack else "lean web stack"

    qa = [
        (
            "What problem are you solving?",
            f"We are addressing: {problem_statement}. The implementation is scoped for a reliable hackathon demo.",
        ),
        (
            "Why this architecture?",
            f"We selected {stack_line} to maximize shipping speed while preserving extensibility.",
        ),
        (
            "How does this align with judging?",
            f"We prioritized {focus} based on the available judging context and optimized feature scope accordingly.",
        ),
        (
            "Which prize tracks are you targeting?",
            f"Primary focus: {track_line}. Track fit is estimated from candidate/problem overlap.",
        ),
        (
            "What was cut due to time?",
            "Non-core features were deferred through checkpoint replanning to preserve end-to-end reliability.",
        ),
        (
            "How did you ensure demo reliability?",
            "We prepared deterministic seed data, a one-command boot path, and a fallback demo route.",
        ),
        (
            "What evidence proves execution quality?",
            "We provide live demo flow, test outcomes, and artifact-backed implementation notes.",
        ),
        (
            "What is next after the hackathon?",
            "Expand deferred features, strengthen automated tests, and harden deployment observability.",
        ),
    ]

    lines = ["# Mentor/Judge Q&A Pack", ""]
    for question, answer in qa:
        lines.append(f"## Q: {question}")
        lines.append(answer)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
