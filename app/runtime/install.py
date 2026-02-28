"""Dependency installation runner."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from app.runtime.command_runner import CommandResult, run_command_streamed


def run_dependency_install(
    *,
    cwd: str | Path,
    command: Sequence[str] | None = None,
    retries: int = 2,
    backoff_seconds: float = 1.0,
) -> CommandResult:
    """Run dependency install command with retry/backoff."""

    cmd = list(command or ("npm", "install"))
    last_result = CommandResult(returncode=1, stdout="", stderr="install not started", timed_out=False)

    for attempt in range(retries + 1):
        result = run_command_streamed(cmd, cwd=cwd)
        last_result = result
        if result.returncode == 0 and not result.timed_out:
            return result

        if attempt < retries:
            delay = backoff_seconds * (2**attempt)
            time.sleep(delay)

    return last_result
