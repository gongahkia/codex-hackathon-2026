"""Candidate ranking services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping

from app.models.candidate import Candidate
from app.models.scoring import Weights
from app.scoring.aggregate import aggregate_weighted_score
from app.scoring.evidence_quality import evidence_quality_score
from app.scoring.feasibility import feasibility_score
from app.scoring.relevance import relevance_score
from app.scoring.rubric import derive_judging_weights
from app.scoring.speed import speed_to_build_score
from app.services.content_quality import is_low_detail_description
from app.services.repo_freshness import is_repo_stale
from app.services.track_fit import TrackFitRecommendation, recommend_track_fit


@dataclass
class ScoredCandidate:
    """Ranked candidate with factor-level details."""

    candidate: Candidate
    factors: Mapping[str, float]
    total_score: float
    applied_weights: Mapping[str, float] = field(default_factory=dict)
    track_fit: List[TrackFitRecommendation] = field(default_factory=list)


def rank_candidates(
    candidates: Iterable[Candidate],
    weights: Weights | Mapping[str, float],
    problem_statement: str = "",
    rubric_text: str | None = None,
    prize_tracks: List[str] | None = None,
) -> List[ScoredCandidate]:
    """Score and sort candidates by weighted total score."""

    candidate_list = list(candidates)
    effective_weights = derive_judging_weights(weights, rubric_text)
    scored: List[ScoredCandidate] = []
    for candidate in candidate_list:
        factors = {
            "relevance": relevance_score(candidate, problem_statement),
            "feasibility": feasibility_score(candidate),
            "speed": speed_to_build_score(candidate),
            "evidence": evidence_quality_score(candidate, candidate_list),
        }
        _apply_unreachable_evidence_penalty(candidate, factors)
        _apply_repo_freshness_penalty(candidate, factors)
        _apply_low_detail_penalty(candidate, factors)
        total = aggregate_weighted_score(factors, effective_weights)
        scored.append(
            ScoredCandidate(
                candidate=candidate,
                factors=factors,
                total_score=total,
                applied_weights=effective_weights.model_dump(),
                track_fit=recommend_track_fit(candidate, prize_tracks),
            )
        )

    return sorted(scored, key=lambda item: item.total_score, reverse=True)


def _apply_unreachable_evidence_penalty(
    candidate: Candidate,
    factors: dict[str, float],
) -> None:
    verified_code = candidate.signals.get("verified_code_links", [])
    verified_writeup = candidate.signals.get("verified_writeup_links", [])
    verification_errors = candidate.signals.get("verification_errors", [])

    has_verified = bool(verified_code) or bool(verified_writeup)
    has_errors = bool(verification_errors)
    if has_verified or not has_errors:
        return

    factors["evidence"] = 0.0
    reasons = candidate.signals.setdefault("ranking_penalties", [])
    if isinstance(reasons, list):
        reasons.append("Unreachable evidence URLs; evidence score forced to zero")


def _apply_repo_freshness_penalty(
    candidate: Candidate,
    factors: dict[str, float],
) -> None:
    last_commit_date = candidate.signals.get("last_commit_date")
    if not last_commit_date:
        return
    if not is_repo_stale(last_commit_date):
        return

    penalty = 0.2
    factors["feasibility"] = max(0.0, factors["feasibility"] - penalty)
    factors["freshness_penalty"] = penalty
    reasons = candidate.signals.setdefault("ranking_penalties", [])
    if isinstance(reasons, list):
        reasons.append("Repository is stale; feasibility score penalized")


def _apply_low_detail_penalty(
    candidate: Candidate,
    factors: dict[str, float],
) -> None:
    if not is_low_detail_description(candidate.summary):
        return

    penalty = 0.15
    factors["relevance"] = max(0.0, factors["relevance"] - penalty)
    factors["content_detail_penalty"] = penalty
    reasons = candidate.signals.setdefault("ranking_penalties", [])
    if isinstance(reasons, list):
        reasons.append("Low-detail summary; relevance score penalized")


def select_top_candidates(
    ranked_candidates: Iterable[ScoredCandidate], option_count: int = 5
) -> List[ScoredCandidate]:
    """Return top-N ranked candidates with sane bounds."""

    bounded = max(1, option_count)
    return list(ranked_candidates)[:bounded]
