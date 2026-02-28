"""Demo reliability mode for pre-submission stabilization."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from app.runtime.healthcheck import probe_dev_server
from app.security.url_policy import UrlPolicy


@dataclass
class DemoReliabilityReport:
    """Report for demo lock/readiness checks."""

    deterministic_seed_path: str
    boot_command: str
    fallback_demo_route: str
    health_url: str | None
    health_ok: bool | None
    stable: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_demo_reliability_mode(
    *,
    artifacts_dir: str | Path,
    health_url: str | None = None,
    demo_route: str = "/demo",
    boot_command: str = "npm run dev",
    allow_local_health: bool = False,
) -> DemoReliabilityReport:
    """Create deterministic seed plan and verify demo reliability signals."""

    output_dir = Path(artifacts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_payload = {
        "seed": "last-minute-deterministic-seed",
        "fixtures": [
            {"id": "demo-user-1", "name": "Demo User", "status": "active"},
            {"id": "demo-item-1", "title": "Primary flow sample", "state": "ready"},
        ],
    }
    seed_path = output_dir / "demo-seed.json"
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    notes: List[str] = []
    health_ok: bool | None = None
    if health_url:
        policy = UrlPolicy(
            allowed_schemes=("https", "http") if allow_local_health else ("https",),
            allow_localhost=allow_local_health,
        )
        health_ok = probe_dev_server(
            health_url,
            retries=3,
            delay_seconds=1.0,
            timeout_seconds=2.0,
            policy=policy,
        )
        if not health_ok:
            notes.append("Health probe did not stabilize during demo reliability mode")
    else:
        notes.append("Health check skipped because no health_url was supplied")

    stable = True if health_ok is None else health_ok

    return DemoReliabilityReport(
        deterministic_seed_path=str(seed_path),
        boot_command=boot_command,
        fallback_demo_route=demo_route,
        health_url=health_url,
        health_ok=health_ok,
        stable=stable,
        notes=notes,
    )
