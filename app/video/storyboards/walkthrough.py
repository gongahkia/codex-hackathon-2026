"""Walkthrough storyboard generator."""

from __future__ import annotations

from app.models.video import SceneSpec


def generate_walkthrough_storyboard(project_title: str, duration_sec: int = 60) -> list[SceneSpec]:
    """Build walkthrough-oriented scene sequence."""

    per_scene = max(6, duration_sec // 5)
    return [
        SceneSpec(style="walkthrough", duration_sec=per_scene, title=f"{project_title}: Intro", narration="Show entry point."),
        SceneSpec(style="walkthrough", duration_sec=per_scene, title="Create", narration="Demonstrate creation flow."),
        SceneSpec(style="walkthrough", duration_sec=per_scene, title="Manage", narration="Demonstrate edit/update flow."),
        SceneSpec(style="walkthrough", duration_sec=per_scene, title="Review", narration="Show reporting/output.") ,
        SceneSpec(style="walkthrough", duration_sec=per_scene, title="Wrap", narration="Summarize delivery readiness."),
    ]
