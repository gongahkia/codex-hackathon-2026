"""Deadline-aware scope trimming."""

from __future__ import annotations

from app.planner.project_spec import ProjectSpec


def trim_scope_for_budget(spec: ProjectSpec, budget_risk: float) -> ProjectSpec:
    """Drop non-core features when risk of deadline overrun rises."""

    if budget_risk < 0.5:
        return spec

    trimmed_features = spec.features[:2] if len(spec.features) > 2 else spec.features
    trimmed_milestones = spec.milestones[:3] if len(spec.milestones) > 3 else spec.milestones
    return spec.model_copy(
        update={
            "features": trimmed_features,
            "milestones": trimmed_milestones,
        }
    )
