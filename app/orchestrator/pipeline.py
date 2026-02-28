"""Pipeline orchestration."""

from __future__ import annotations

from app.models.run_config import RunConfig
from app.models.run_state import RunState

PIPELINE_ORDER = [
    RunState.INTAKE,
    RunState.RESEARCH,
    RunState.RANKING,
    RunState.SELECTION,
    RunState.BUILD,
    RunState.TEST,
    RunState.VIDEO,
]


def run_pipeline(config: RunConfig) -> list[RunState]:
    """Run the pipeline and record state transitions."""

    _ = config
    transitions: list[RunState] = []
    try:
        for state in PIPELINE_ORDER:
            transitions.append(state)
        transitions.append(RunState.DONE)
    except Exception:
        transitions.append(RunState.FAILED)
    return transitions
