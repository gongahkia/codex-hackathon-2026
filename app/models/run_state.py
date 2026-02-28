"""Run state machine values."""

from enum import Enum


class RunState(str, Enum):
    """Pipeline states for one run."""

    INTAKE = "INTAKE"
    RESEARCH = "RESEARCH"
    RANKING = "RANKING"
    SELECTION = "SELECTION"
    BUILD = "BUILD"
    TEST = "TEST"
    VIDEO = "VIDEO"
    DONE = "DONE"
    FAILED = "FAILED"
