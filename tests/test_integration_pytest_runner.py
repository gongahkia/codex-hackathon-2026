from __future__ import annotations

from app.runtime.command_runner import CommandResult
from app.testing.integration_pytest import run_pytest_integration


def test_run_pytest_integration_prefers_pytest_binary(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.testing.integration_pytest.shutil.which", lambda binary: "/usr/bin/pytest")
    seen = {"command": None}

    def fake_run(command, *, cwd):
        _ = cwd
        seen["command"] = command
        return CommandResult(returncode=0, stdout="", stderr="", timed_out=False, duration_ms=1)

    monkeypatch.setattr("app.testing.integration_pytest.run_command_streamed", fake_run)

    run_pytest_integration(tmp_path)
    assert seen["command"] == ["pytest", "-m", "integration"]


def test_run_pytest_integration_falls_back_to_python_module(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.testing.integration_pytest.shutil.which", lambda binary: None)
    seen = {"command": None}

    def fake_run(command, *, cwd):
        _ = cwd
        seen["command"] = command
        return CommandResult(returncode=0, stdout="", stderr="", timed_out=False, duration_ms=1)

    monkeypatch.setattr("app.testing.integration_pytest.run_command_streamed", fake_run)

    run_pytest_integration(tmp_path)
    assert seen["command"] == ["python3", "-m", "pytest", "-m", "integration"]
