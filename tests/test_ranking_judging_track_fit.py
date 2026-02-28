from __future__ import annotations

from app.models.candidate import Candidate
from app.models.scoring import Weights
from app.services.ranking import rank_candidates


def test_ranking_applies_judging_rubric_and_track_fit() -> None:
    candidates = [
        Candidate(
            title="AI Tutor",
            summary="Education AI coaching app",
            urls=["https://example.com"],
            stack=["Next.js"],
            signals={"complexity": "low", "setup_steps": 2},
            source="devpost",
        )
    ]

    ranked = rank_candidates(
        candidates,
        Weights(),
        problem_statement="Build education AI app",
        rubric_text="Innovation innovation innovation and impact",
        prize_tracks=["AI Track", "Education Prize"],
    )

    assert len(ranked) == 1
    assert ranked[0].applied_weights
    assert ranked[0].track_fit
    assert ranked[0].track_fit[0].track in {"AI Track", "Education Prize"}
