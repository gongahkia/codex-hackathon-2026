"""Milestone checkpoints and automatic replanning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.planner.project_spec import ProjectSpec
from app.planner.scope_trimmer import trim_scope_for_budget


@dataclass
class CheckpointDecision:
    """Decision outcome at a milestone checkpoint."""

    checkpoint_percent: int
    expected_completed: int
    actual_completed: int
    behind_by: int
    forced_feature_cuts: List[str] = field(default_factory=list)


def evaluate_checkpoint_and_replan(
    spec: ProjectSpec,
    *,
    checkpoint_percent: int,
    completed_milestones: int,
) -> tuple[ProjectSpec, CheckpointDecision]:
    """Replan scope when completed milestones are behind checkpoint expectations."""

    milestone_count = max(1, len(spec.milestones))
    expected_completed = int((checkpoint_percent / 100) * milestone_count)
    behind_by = max(0, expected_completed - max(0, completed_milestones))

    if behind_by == 0:
        return (
            spec,
            CheckpointDecision(
                checkpoint_percent=checkpoint_percent,
                expected_completed=expected_completed,
                actual_completed=completed_milestones,
                behind_by=0,
            ),
        )

    risk = min(1.0, 0.5 + (behind_by / milestone_count))
    trimmed = trim_scope_for_budget(spec, budget_risk=risk)
    removed_features = [feature for feature in spec.features if feature not in trimmed.features]

    decision = CheckpointDecision(
        checkpoint_percent=checkpoint_percent,
        expected_completed=expected_completed,
        actual_completed=completed_milestones,
        behind_by=behind_by,
        forced_feature_cuts=removed_features,
    )
    return trimmed, decision


def run_milestone_checkpoints(
    spec: ProjectSpec,
    *,
    completed_by_checkpoint: Dict[int, int] | None = None,
) -> tuple[ProjectSpec, List[CheckpointDecision]]:
    """Evaluate fixed checkpoints (25/50/75) and apply auto-replanning."""

    progress = completed_by_checkpoint or {}
    current = spec
    decisions: List[CheckpointDecision] = []

    for checkpoint in (25, 50, 75):
        completed = progress.get(checkpoint, 0)
        current, decision = evaluate_checkpoint_and_replan(
            current,
            checkpoint_percent=checkpoint,
            completed_milestones=completed,
        )
        decisions.append(decision)

    return current, decisions
