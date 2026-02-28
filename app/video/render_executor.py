"""Remotion render execution."""

from __future__ import annotations

from pathlib import Path

from app.runtime.command_runner import CommandResult, run_command_streamed


def execute_render(
    command: list[str],
    *,
    cwd: str | Path,
    timeout_seconds: int = 600,
) -> CommandResult:
    """Execute MP4 render command with timeout guard."""

    return run_command_streamed(command, cwd=cwd, timeout_seconds=timeout_seconds)
