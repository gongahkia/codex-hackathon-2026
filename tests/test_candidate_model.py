from __future__ import annotations

from app.models.candidate import Candidate


def test_candidate_provenance_fields_normalize_input() -> None:
    candidate = Candidate(
        title="AI Planner",
        summary="Planner",
        urls=["https://github.com/acme/planner"],
        stack=[],
        signals={},
        source="github",
        source_query="  Build AI planner  ",
        verification_errors=[" timeout ", "", "dns failure"],
        fetched_at="2026-02-28T00:00:00Z",
        verified_at="2026-02-28T00:05:00Z",
    )

    assert candidate.source_query == "Build AI planner"
    assert candidate.verification_errors == ["timeout", "dns failure"]
    assert candidate.fetched_at is not None
    assert candidate.verified_at is not None


def test_candidate_empty_source_query_becomes_none() -> None:
    candidate = Candidate(
        title="AI Planner",
        summary="Planner",
        urls=["https://github.com/acme/planner"],
        stack=[],
        signals={},
        source="github",
        source_query="   ",
    )

    assert candidate.source_query is None
