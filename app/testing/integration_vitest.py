"""Vitest integration runner adapter."""

from __future__ import annotations

from pathlib import Path

from app.runtime.command_runner import CommandResult, run_command_streamed


def run_vitest_integration(cwd: str | Path) -> CommandResult:
    """Execute Vitest integration test suite."""

    return run_command_streamed(["npm", "run", "test:integration"], cwd=cwd)
