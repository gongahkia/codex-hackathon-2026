from __future__ import annotations

from app.models.candidate import Candidate
from app.services.evidence_verification import verify_candidate_evidence, verify_candidates_evidence


def _candidate() -> Candidate:
    return Candidate(
        title="AI Planner",
        summary="Planner project",
        urls=[
            "https://github.com/acme/ai-planner",
            "https://devpost.com/software/ai-planner",
        ],
        stack=[],
        signals={},
        source="github",
    )


def test_verify_candidate_evidence_returns_reachable_links_with_probe_stub() -> None:
    candidate = _candidate()

    def fake_probe(url: str, policy, timeout_seconds: float):
        _ = (policy, timeout_seconds)
        if "github.com" in url:
            return True, None
        return False, "unreachable"

    result = verify_candidate_evidence(candidate, probe_fn=fake_probe)
    assert result.verified_code_links == ["https://github.com/acme/ai-planner"]
    assert result.verified_writeup_links == []
    assert result.verification_errors


def test_verify_candidates_evidence_persists_verification_fields() -> None:
    candidates = [_candidate()]

    def always_ok(url: str, policy, timeout_seconds: float):
        _ = (url, policy, timeout_seconds)
        return True, None

    verified = verify_candidates_evidence(candidates, probe_fn=always_ok)
    assert verified[0].signals["verified_code_links"] == ["https://github.com/acme/ai-planner"]
    assert verified[0].signals["verified_writeup_links"] == ["https://devpost.com/software/ai-planner"]
    assert verified[0].signals["verification_errors"] == []
