"""Deployment health watch for flaky demo detection."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from urllib.error import URLError
from urllib.request import urlopen

from app.security.url_policy import UrlPolicy, validate_safe_url


@dataclass
class DeploymentHealthReport:
    """Deployment health watch result."""

    url: str | None
    checks: int
    successes: int
    success_ratio: float
    stable: bool
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def watch_deployment_health(
    url: str | None,
    *,
    checks: int = 6,
    interval_seconds: float = 1.0,
    timeout_seconds: float = 2.0,
    min_success_ratio: float = 0.8,
    policy: UrlPolicy | None = None,
) -> DeploymentHealthReport:
    """Probe deployed endpoint and compute short-window stability."""

    if not url:
        return DeploymentHealthReport(
            url=None,
            checks=0,
            successes=0,
            success_ratio=1.0,
            stable=True,
            errors=["Deployment watch skipped because no URL was supplied"],
        )

    effective_policy = policy or UrlPolicy()
    validate_safe_url(url, effective_policy)

    success_count = 0
    errors: List[str] = []

    for _ in range(max(1, checks)):
        try:
            with urlopen(url, timeout=timeout_seconds) as response:
                if 200 <= response.status < 400:
                    success_count += 1
                else:
                    errors.append(f"Unexpected HTTP status: {response.status}")
        except URLError as exc:
            errors.append(str(exc))
        time.sleep(max(0.0, interval_seconds))

    total = max(1, checks)
    ratio = success_count / total
    stable = ratio >= min_success_ratio

    return DeploymentHealthReport(
        url=url,
        checks=checks,
        successes=success_count,
        success_ratio=ratio,
        stable=stable,
        errors=errors,
    )


def enforce_deployment_health(
    url: str | None,
    *,
    policy: UrlPolicy | None = None,
) -> DeploymentHealthReport:
    """Run deployment watch and fail fast when deployment is flaky."""

    report = watch_deployment_health(url, policy=policy)
    if url and not report.stable:
        raise RuntimeError(
            f"Deployment health unstable for {url}: success_ratio={report.success_ratio:.2f}"
        )
    return report
