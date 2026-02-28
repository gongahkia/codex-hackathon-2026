"""Remotion render execution."""

from __future__ import annotations

import shutil
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


def execute_render_with_fallback(
    command: list[str],
    *,
    config_json: str,
    cwd: str | Path,
    timeout_seconds: int = 600,
) -> dict[str, object]:
    """Fallback to config + command output when render dependencies are unavailable."""

    executable = command[0] if command else ""
    if not executable or shutil.which(executable) is None:
        return {
            "rendered": False,
            "fallback": True,
            "reason": "missing render dependency",
            "command": " ".join(command),
            "config": config_json,
        }

    result = execute_render(command, cwd=cwd, timeout_seconds=timeout_seconds)
    if result.returncode == 0 and not result.timed_out:
        return {"rendered": True, "fallback": False, "result": result}

    return {
        "rendered": False,
        "fallback": True,
        "reason": "render failed",
        "command": " ".join(command),
        "config": config_json,
        "result": result,
    }
