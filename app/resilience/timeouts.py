"""Timeout guards for source operations."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable, TypeVar

T = TypeVar("T")


def run_with_timeout(operation: Callable[[], T], timeout_seconds: float) -> T:
    """Run operation with timeout and raise TimeoutError when exceeded."""

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(operation)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"operation timed out after {timeout_seconds}s") from exc
