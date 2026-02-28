"""Phase timing collectors."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PhaseTimingCollector:
    """Collect execution timings for pipeline phases."""

    _phase_starts: Dict[str, float] = field(default_factory=dict)
    _durations: Dict[str, float] = field(default_factory=dict)

    def start(self, phase: str) -> None:
        self._phase_starts[phase] = time.monotonic()

    def stop(self, phase: str) -> None:
        start = self._phase_starts.get(phase)
        if start is None:
            return
        self._durations[phase] = time.monotonic() - start

    def as_dict(self) -> Dict[str, float]:
        return dict(self._durations)
