"""Deployment command execution."""

from __future__ import annotations

from pathlib import Path

from app.runtime.command_runner import CommandResult, run_command_streamed

DEPLOY_COMMANDS = {
    "vercel": ["vercel", "deploy", "--yes"],
    "render": ["render", "deploy"],
}


def execute_one_click_deploy(provider: str, cwd: str | Path) -> CommandResult:
    """Execute deploy command for supported one-click providers."""

    normalized = provider.strip().lower()
    if normalized not in DEPLOY_COMMANDS:
        raise ValueError(f"Unsupported deploy provider: {provider}")
    return run_command_streamed(DEPLOY_COMMANDS[normalized], cwd=cwd)
