"""Retry policies with jitter."""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_jitter(
    operation: Callable[[], T],
    *,
    retries: int = 2,
    base_delay_seconds: float = 0.5,
    jitter_seconds: float = 0.25,
) -> T:
    """Execute operation with retry and jittered backoff."""

    last_exception: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - generic policy wrapper
            last_exception = exc
            if attempt == retries:
                break
            delay = base_delay_seconds * (2**attempt) + random.uniform(0, jitter_seconds)
            time.sleep(delay)

    assert last_exception is not None
    raise last_exception
