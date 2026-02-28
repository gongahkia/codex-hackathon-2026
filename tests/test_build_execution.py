from __future__ import annotations

from app.orchestrator.pipeline import _run_build_execution
from app.runtime.command_runner import CommandResult


def test_run_build_execution_uses_npm_ci_when_lockfile_exists(monkeypatch, tmp_path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")

    seen = {"command": None}

    def fake_install(*, cwd, command, retries):
        _ = (cwd, retries)
        seen["command"] = list(command)
        return CommandResult(returncode=0, stdout="", stderr="", timed_out=False, duration_ms=10)

    monkeypatch.setattr("app.orchestrator.pipeline.run_dependency_install", fake_install)

    payload = _run_build_execution(tmp_path)
    assert payload["command"] == ["npm", "ci"]
    assert seen["command"] == ["npm", "ci"]
