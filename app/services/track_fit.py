"""Prize-track fit recommendations for ranked candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from app.models.candidate import Candidate


@dataclass
class TrackFitRecommendation:
    """Track recommendation with estimated fit and competitiveness."""

    track: str
    fit_score: float
    competitiveness: str
    rationale: str


HIGH_COMPETITION_HINTS = {"ai", "web3", "crypto", "fintech", "consumer", "social"}
MEDIUM_COMPETITION_HINTS = {"education", "health", "climate", "sustainability", "civic"}


def _competitiveness(track: str) -> str:
    lowered = track.lower()
    if any(keyword in lowered for keyword in HIGH_COMPETITION_HINTS):
        return "high"
    if any(keyword in lowered for keyword in MEDIUM_COMPETITION_HINTS):
        return "medium"
    return "low"


def recommend_track_fit(
    candidate: Candidate,
    prize_tracks: Sequence[str] | None,
    *,
    top_n: int = 3,
) -> List[TrackFitRecommendation]:
    """Recommend strongest prize tracks for a candidate."""

    if not prize_tracks:
        return []

    candidate_text = " ".join([candidate.title, candidate.summary, *candidate.stack]).lower()
    recommendations: List[TrackFitRecommendation] = []

    for track in prize_tracks:
        cleaned_track = track.strip()
        if not cleaned_track:
            continue

        tokens = [token for token in cleaned_track.lower().split() if len(token) > 2]
        if not tokens:
            fit_score = 0.2
            overlap: List[str] = []
        else:
            overlap = [token for token in tokens if token in candidate_text]
            fit_score = min(1.0, 0.2 + (len(overlap) / len(tokens)) * 0.8)

        if overlap:
            rationale = f"Matches track keywords: {', '.join(overlap[:3])}"
        else:
            rationale = "No direct keyword overlap; recommended as a broader-fit option"

        recommendations.append(
            TrackFitRecommendation(
                track=cleaned_track,
                fit_score=fit_score,
                competitiveness=_competitiveness(cleaned_track),
                rationale=rationale,
            )
        )

    recommendations.sort(key=lambda item: item.fit_score, reverse=True)
    return recommendations[: max(1, top_n)]
