"""Progress event emission utilities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Callable


def emit_progress(
    *,
    run_id: str,
    phase: str,
    message: str,
    emit_fn: Callable[[str], None] = print,
) -> None:
    """Emit structured progress events suitable for CLI updates."""

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "phase": phase,
        "message": message,
    }
    emit_fn(json.dumps(payload))
