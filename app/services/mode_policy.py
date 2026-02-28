"""Mode-specific source policies."""

from __future__ import annotations

from typing import Dict


def fast_mode_source_limits() -> Dict[str, int]:
    """Reduce per-source query depth for fast mode."""

    return {
        "dorahacks": 3,
        "devpost": 3,
        "github": 3,
        "reddit": 2,
    }
