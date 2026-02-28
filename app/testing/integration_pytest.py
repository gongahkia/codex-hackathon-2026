"""Pytest integration runner adapter."""

from __future__ import annotations

from pathlib import Path
import shutil

from app.runtime.command_runner import CommandResult, run_command_streamed


def run_pytest_integration(cwd: str | Path) -> CommandResult:
    """Execute pytest integration test suite."""

    command = ["pytest", "-m", "integration"]
    if shutil.which("pytest") is None:
        command = ["python3", "-m", "pytest", "-m", "integration"]
    return run_command_streamed(command, cwd=cwd)
