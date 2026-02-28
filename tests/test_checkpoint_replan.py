from __future__ import annotations

from app.planner.checkpoints import run_milestone_checkpoints
from app.planner.project_spec import ProjectSpec


def test_checkpoint_replan_forces_scope_cuts_when_behind() -> None:
    spec = ProjectSpec(
        title="Test",
        features=["Core flow", "Auth", "Analytics"],
        stack=["Next.js"],
        milestones=["m1", "m2", "m3", "m4"],
    )

    updated, decisions = run_milestone_checkpoints(
        spec,
        completed_by_checkpoint={25: 0, 50: 0, 75: 1},
    )

    assert len(decisions) == 3
    assert any(decision.behind_by > 0 for decision in decisions)
    assert len(updated.features) <= len(spec.features)
