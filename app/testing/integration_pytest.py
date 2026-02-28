"""Pytest integration runner adapter."""

from __future__ import annotations

from pathlib import Path

from app.runtime.command_runner import CommandResult, run_command_streamed


def run_pytest_integration(cwd: str | Path) -> CommandResult:
    """Execute pytest integration test suite."""

    return run_command_streamed(["pytest", "-m", "integration"], cwd=cwd)
