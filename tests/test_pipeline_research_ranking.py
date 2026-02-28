from __future__ import annotations

from app.models.candidate import Candidate
from app.models.scoring import Weights
from app.services.ranking import rank_candidates, select_top_candidates
from app.sources.base import SourceAdapter


class MockSource(SourceAdapter):
    def __init__(self, source_name: str, payload: list[dict[str, object]]) -> None:
        self.source_name = source_name
        self._payload = payload

    def search(self, problem: str, limit: int) -> list[dict[str, object]]:
        _ = problem
        return self._payload[:limit]


def test_research_to_ranking_pipeline_with_mocked_sources() -> None:
    sources = [
        MockSource(
            "dorahacks",
            [
                {
                    "title": "AI Planner",
                    "summary": "AI planning assistant with quick setup",
                    "urls": ["https://github.com/acme/ai-planner", "https://devpost.com/software/ai-planner"],
                    "stack": ["Next.js", "SQLite"],
                    "signals": {"setup_steps": 2, "complexity": "low"},
                    "source": "dorahacks",
                }
            ],
        ),
        MockSource(
            "github",
            [
                {
                    "title": "Legacy Tracker",
                    "summary": "Large legacy stack with complicated bootstrap",
                    "urls": ["https://github.com/acme/legacy-tracker"],
                    "stack": ["Django", "Celery", "Redis", "Postgres", "React"],
                    "signals": {"setup_steps": 8, "complexity": "high"},
                    "source": "github",
                }
            ],
        ),
    ]

    candidates: list[Candidate] = []
    for source in sources:
        candidates.extend(Candidate(**row) for row in source.search("AI planning", limit=5))

    ranked = rank_candidates(candidates, Weights(), problem_statement="AI planning")
    top_two = select_top_candidates(ranked, option_count=2)

    assert len(top_two) == 2
    assert top_two[0].total_score >= top_two[1].total_score
    assert top_two[0].candidate.title == "AI Planner"


def test_ranking_downranks_candidates_with_unreachable_verified_evidence() -> None:
    unreachable = Candidate(
        title="Unreachable Evidence",
        summary="Looks promising",
        urls=["https://github.com/acme/unreachable", "https://devpost.com/software/unreachable"],
        stack=["Next.js"],
        signals={
            "setup_steps": 2,
            "complexity": "low",
            "verified_code_links": [],
            "verified_writeup_links": [],
            "verification_errors": ["https://github.com/acme/unreachable: timeout"],
        },
        source="github",
    )
    reachable = Candidate(
        title="Reachable Evidence",
        summary="Looks promising",
        urls=["https://github.com/acme/reachable", "https://devpost.com/software/reachable"],
        stack=["Next.js"],
        signals={
            "setup_steps": 2,
            "complexity": "low",
            "verified_code_links": ["https://github.com/acme/reachable"],
            "verified_writeup_links": ["https://devpost.com/software/reachable"],
            "verification_errors": [],
        },
        source="github",
    )

    ranked = rank_candidates(
        [unreachable, reachable],
        Weights(),
        problem_statement="Build AI planner",
    )

    assert ranked[0].candidate.title == "Reachable Evidence"
    assert "ranking_penalties" in unreachable.signals


def test_ranking_penalizes_stale_repositories() -> None:
    stale = Candidate(
        title="Stale Repo",
        summary="AI helper",
        urls=["https://github.com/acme/stale", "https://devpost.com/software/stale"],
        stack=["Next.js"],
        signals={
            "setup_steps": 2,
            "complexity": "low",
            "last_commit_date": "2020-01-01T00:00:00Z",
        },
        source="github",
    )
    fresh = Candidate(
        title="Fresh Repo",
        summary="AI helper",
        urls=["https://github.com/acme/fresh", "https://devpost.com/software/fresh"],
        stack=["Next.js"],
        signals={
            "setup_steps": 2,
            "complexity": "low",
            "last_commit_date": "2030-01-01T00:00:00Z",
        },
        source="github",
    )

    ranked = rank_candidates([stale, fresh], Weights(), problem_statement="Build AI helper")
    assert ranked[0].candidate.title == "Fresh Repo"
    assert "ranking_penalties" in stale.signals
