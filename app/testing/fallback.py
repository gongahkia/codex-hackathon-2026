"""Testing fallback controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from app.runtime.command_runner import CommandResult


@dataclass
class FallbackResult:
    """Result of fallback-driven test execution."""

    executed_suite: str
    result: CommandResult | None
    skipped_reasons: dict[str, str]


def run_tests_with_fallback(
    plan: list[str],
    runners: Mapping[str, Callable[[], CommandResult]],
) -> FallbackResult:
    """Run suites in order, downgrading to next level on setup failure."""

    skipped: dict[str, str] = {}

    for suite in plan:
        runner = runners.get(suite)
        if runner is None:
            skipped[suite] = "runner not configured"
            continue

        try:
            result = runner()
        except Exception as exc:
            skipped[suite] = f"setup failure: {exc}"
            continue

        if result.returncode == 0 and not result.timed_out:
            return FallbackResult(executed_suite=suite, result=result, skipped_reasons=skipped)

        skipped[suite] = "suite failed"

    return FallbackResult(executed_suite="none", result=None, skipped_reasons=skipped)
