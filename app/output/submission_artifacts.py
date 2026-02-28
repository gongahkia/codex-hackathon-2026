"""Submission-ready artifact generation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.planner.project_spec import ProjectSpec


def generate_submission_artifact(
    *,
    problem_statement: str,
    spec: ProjectSpec,
    deployment_target: str | None = None,
    limitations: Iterable[str] | None = None,
) -> str:
    """Generate submission-ready markdown artifact for hackathon portals."""

    feature_bullets = "\n".join(f"- {feature}" for feature in spec.features)
    setup = "\n".join(
        [
            "1. Install dependencies.",
            "2. Run the development server.",
            "3. Verify health endpoint and demo route.",
        ]
    )
    architecture = f"Core stack: {', '.join(spec.stack) if spec.stack else 'TBD'}"
    limitation_lines = list(limitations or ["Scoped for hackathon timeline; non-core features deferred."])
    limitations_md = "\n".join(f"- {line}" for line in limitation_lines)

    deploy_line = deployment_target or "localhost fallback"

    return (
        f"# {spec.title}\n\n"
        f"## Problem Statement\n{problem_statement}\n\n"
        "## Feature Highlights\n"
        f"{feature_bullets}\n\n"
        "## Setup Instructions\n"
        f"{setup}\n\n"
        "## Architecture Summary\n"
        f"{architecture}\n\n"
        "## Deployment\n"
        f"- Target: {deploy_line}\n\n"
        "## Known Limitations\n"
        f"{limitations_md}\n"
    )


def write_submission_artifact(path: str | Path, content: str) -> Path:
    """Write submission artifact markdown to disk."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output
