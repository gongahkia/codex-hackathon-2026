"""Structured JSON logging utilities."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Format logs as JSON with run_id correlation."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", None),
            "logger": record.name,
        }
        return json.dumps(payload)


def get_run_logger(run_id: str) -> logging.Logger:
    """Create logger that injects run_id in every log record."""

    logger = logging.getLogger(f"last-minute.{run_id}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logging.LoggerAdapter(logger, {"run_id": run_id})  # type: ignore[return-value]
