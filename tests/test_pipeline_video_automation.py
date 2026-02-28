from __future__ import annotations

import json
from pathlib import Path

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.orchestrator.pipeline import run_pipeline


def test_pipeline_auto_generates_video_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    def fake_execute_render_with_fallback(command, *, config_json, cwd, timeout_seconds=600):
        assert command[:7] == [
            "npm",
            "exec",
            "--yes",
            "--package=@remotion/cli@4.0.429",
            "--",
            "remotion",
            "render",
        ]
        assert command[7].endswith("/remotion/index.jsx")
        assert "scenes" in config_json
        assert Path(cwd).name == "video"
        assert Path(cwd).exists()
        return {
            "rendered": False,
            "fallback": True,
            "reason": "test-double",
            "command": " ".join(command),
            "config": config_json,
        }

    monkeypatch.setattr(
        "app.orchestrator.pipeline.execute_render_with_fallback",
        fake_execute_render_with_fallback,
    )

    config = RunConfig(problem_statement="Build a game", deadline_hours=6, video_style="pitch")
    transitions = run_pipeline(config)

    assert transitions[-1] == RunState.DONE

    run_roots = list((tmp_path / "runs").glob("*"))
    assert run_roots, "Expected run artifacts directory to be created"

    artifacts_dir = run_roots[0] / "artifacts"
    config_path = artifacts_dir / "remotion.config.json"
    result_path = artifacts_dir / "video-result.json"
    video_entry = run_roots[0] / "video" / "remotion" / "index.jsx"

    assert config_path.exists()
    assert result_path.exists()
    assert video_entry.exists()

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["fallback"] is True
    assert payload["rendered"] is False
