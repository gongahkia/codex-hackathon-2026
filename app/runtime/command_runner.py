"""Command execution with timeout and streamed logs."""

from __future__ import annotations

import os
import selectors
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from app.security.command_policy import enforce_allowed_command
from app.security.redaction import redact_secrets


@dataclass
class CommandResult:
    """Command execution result payload."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_ms: int = 0


def run_command_streamed(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: int = 600,
    env: Mapping[str, str] | None = None,
    on_output: Callable[[str], None] | None = None,
) -> CommandResult:
    """Run command with timeout and stream stdout/stderr lines."""

    enforce_allowed_command(command)

    process = subprocess.Popen(
        list(command),
        cwd=str(cwd) if cwd else None,
        env={**os.environ, **dict(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    assert process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")

    start = time.monotonic()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    timed_out = False

    while selector.get_map():
        if time.monotonic() - start > timeout_seconds:
            process.kill()
            timed_out = True
            break

        for key, _ in selector.select(timeout=0.2):
            line = key.fileobj.readline()
            if not line:
                selector.unregister(key.fileobj)
                continue
            stripped = redact_secrets(line.rstrip("\n"))
            if key.data == "stdout":
                stdout_lines.append(stripped)
            else:
                stderr_lines.append(stripped)
            if on_output:
                on_output(stripped)

    process.wait()
    if timed_out:
        if process.stdout is not None:
            remainder = process.stdout.read()
            if remainder:
                for line in remainder.splitlines():
                    stdout_lines.append(redact_secrets(line))
        if process.stderr is not None:
            remainder = process.stderr.read()
            if remainder:
                for line in remainder.splitlines():
                    stderr_lines.append(redact_secrets(line))

    returncode = 124 if timed_out else process.returncode
    duration_ms = int((time.monotonic() - start) * 1000)
    return CommandResult(
        returncode=returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
        timed_out=timed_out,
        duration_ms=duration_ms,
    )
