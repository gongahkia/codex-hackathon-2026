"""Smoke test runner."""

from __future__ import annotations

from app.runtime.healthcheck import probe_dev_server


def run_smoke_test(health_url: str = "http://localhost:3000/health") -> bool:
    """Verify app boot and key endpoint response."""

    return probe_dev_server(health_url, retries=5, delay_seconds=1.0, timeout_seconds=2.0)
