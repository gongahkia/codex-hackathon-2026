from __future__ import annotations

from app.models.candidate import Candidate
from app.services.evidence_gate import passes_minimum_evidence


def _candidate(urls: list[str], source: str) -> Candidate:
    return Candidate(
        title="Test",
        summary="summary",
        urls=urls,
        stack=[],
        signals={},
        source=source,
    )


def test_evidence_gate_passes_with_code_writeup_and_two_sources() -> None:
    primary = _candidate(
        urls=[
            "https://github.com/acme/project",
            "https://devpost.com/software/acme-project",
        ],
        source="github",
    )
    support = [primary, _candidate(urls=["https://example.com/writeup"], source="devpost")]
    assert passes_minimum_evidence(primary, support)


def test_evidence_gate_fails_without_writeup_link() -> None:
    primary = _candidate(urls=["https://github.com/acme/project"], source="github")
    support = [primary, _candidate(urls=["https://github.com/acme/other"], source="devpost")]
    assert not passes_minimum_evidence(primary, support)
