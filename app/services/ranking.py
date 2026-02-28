"""Candidate ranking services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

from app.models.candidate import Candidate
from app.models.scoring import Weights
from app.scoring.aggregate import aggregate_weighted_score
from app.scoring.evidence_quality import evidence_quality_score
from app.scoring.feasibility import feasibility_score
from app.scoring.relevance import relevance_score
from app.scoring.speed import speed_to_build_score


@dataclass
class ScoredCandidate:
    """Ranked candidate with factor-level details."""

    candidate: Candidate
    factors: Mapping[str, float]
    total_score: float


def rank_candidates(
    candidates: Iterable[Candidate],
    weights: Weights | Mapping[str, float],
    problem_statement: str = "",
) -> List[ScoredCandidate]:
    """Score and sort candidates by weighted total score."""

    candidate_list = list(candidates)
    scored: List[ScoredCandidate] = []
    for candidate in candidate_list:
        factors = {
            "relevance": relevance_score(candidate, problem_statement),
            "feasibility": feasibility_score(candidate),
            "speed": speed_to_build_score(candidate),
            "evidence": evidence_quality_score(candidate, candidate_list),
        }
        total = aggregate_weighted_score(factors, weights)
        scored.append(ScoredCandidate(candidate=candidate, factors=factors, total_score=total))

    return sorted(scored, key=lambda item: item.total_score, reverse=True)


def select_top_candidates(
    ranked_candidates: Iterable[ScoredCandidate], option_count: int = 5
) -> List[ScoredCandidate]:
    """Return top-N ranked candidates with sane bounds."""

    bounded = max(1, option_count)
    return list(ranked_candidates)[:bounded]
