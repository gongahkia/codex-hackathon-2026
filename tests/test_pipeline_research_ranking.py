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
