"""Evidence quality scoring features."""

from __future__ import annotations

from typing import Iterable

from app.models.candidate import Candidate
from app.services.evidence import (
    count_independent_source_domains,
    extract_build_writeup_links,
    extract_code_artifact_links,
)


def evidence_quality_score(
    candidate: Candidate, supporting_candidates: Iterable[Candidate] | None = None
) -> float:
    """Score evidence quality from available implementation signals."""

    support = list(supporting_candidates) if supporting_candidates is not None else [candidate]

    score = 0.0
    if extract_code_artifact_links(candidate):
        score += 0.4
    if extract_build_writeup_links(candidate):
        score += 0.3

    domain_count = count_independent_source_domains(support)
    if domain_count >= 2:
        score += 0.3
    elif domain_count == 1:
        score += 0.15

    return min(1.0, score)
