"""Pitch-style storyboard generator."""

from __future__ import annotations

from app.models.video import SceneSpec


def generate_pitch_storyboard(project_title: str, duration_sec: int = 60) -> list[SceneSpec]:
    """Build pitch-oriented scene sequence."""

    per_scene = max(8, duration_sec // 4)
    return [
        SceneSpec(style="pitch", duration_sec=per_scene, title="Problem", narration="State the user pain quickly."),
        SceneSpec(style="pitch", duration_sec=per_scene, title="Solution", narration=f"Introduce {project_title}."),
        SceneSpec(style="pitch", duration_sec=per_scene, title="Demo", narration="Show the core workflow."),
        SceneSpec(style="pitch", duration_sec=per_scene, title="Outcome", narration="Highlight speed and impact."),
    ]
