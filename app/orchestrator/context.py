"""Structured run context."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from app.models.run_config import RunConfig
from app.models.run_state import RunState
from app.models.time_budget import BudgetSnapshot


class RunContext(BaseModel):
    """In-memory run context shared by pipeline phases."""

    config: RunConfig
    budget: BudgetSnapshot | None = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    state: RunState = RunState.INTAKE

    def transition(self, state: RunState) -> None:
        self.state = state
