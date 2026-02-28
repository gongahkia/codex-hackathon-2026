"""Playwright E2E runner adapter."""

from __future__ import annotations

from pathlib import Path

from app.runtime.command_runner import CommandResult, run_command_streamed


def run_playwright_e2e(cwd: str | Path) -> CommandResult:
    """Execute Playwright E2E test suite."""

    return run_command_streamed(["npx", "playwright", "test"], cwd=cwd)
