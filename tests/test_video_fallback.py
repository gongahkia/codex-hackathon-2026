from __future__ import annotations

from app.video.render_executor import execute_render_with_fallback


def test_video_render_fallback_when_renderer_unavailable(tmp_path) -> None:
    result = execute_render_with_fallback(
        ["missing-remotion-binary", "render"],
        config_json='{"fps":30,"scenes":[]}',
        cwd=tmp_path,
        timeout_seconds=1,
    )

    assert result["fallback"] is True
    assert result["rendered"] is False
    assert "command" in result
    assert "config" in result
