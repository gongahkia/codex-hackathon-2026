"""Pitch narrative optimization for multiple durations."""

from __future__ import annotations

from typing import Dict, Iterable


def _rubric_focus(rubric_text: str | None) -> str:
    text = (rubric_text or "").lower()
    if not text:
        return "impact and delivery"

    if "innovation" in text or "novel" in text:
        return "innovation"
    if "technical" in text or "feasible" in text:
        return "technical execution"
    if "impact" in text or "user" in text:
        return "user impact"
    return "impact and delivery"


def optimize_pitch_narrative(
    *,
    project_title: str,
    problem_statement: str,
    rubric_text: str | None = None,
    evidence_points: Iterable[str] | None = None,
) -> Dict[str, str]:
    """Generate pitch scripts for 60/90/120 second windows."""

    focus = _rubric_focus(rubric_text)
    evidence = list(evidence_points or ["working demo", "core flow implemented", "basic tests completed"])
    evidence_line = ", ".join(evidence[:3])

    return {
        "60": (
            f"Problem: {problem_statement}. "
            f"Solution: {project_title}. "
            f"We prioritized {focus} and validated with {evidence_line}. "
            "Next, we show the live core flow and outcome."
        ),
        "90": (
            f"{project_title} tackles: {problem_statement}. "
            f"Our build focuses on {focus} under tight hackathon constraints. "
            f"Evidence today includes {evidence_line}. "
            "The demo walks through setup, key user action, and result. "
            "We close with roadmap and known limitations."
        ),
        "120": (
            f"Context: {problem_statement}. "
            f"Approach: {project_title} with a scope-first architecture optimized for {focus}. "
            f"Proof points: {evidence_line}. "
            "In the walkthrough, we cover the problem, architecture choices, end-to-end demo, "
            "tradeoffs we made for deadline safety, and how we extend post-hackathon."
        ),
    }
