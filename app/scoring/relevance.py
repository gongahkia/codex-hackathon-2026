"""Relevance scoring features."""

from __future__ import annotations

from app.models.candidate import Candidate


def relevance_score(candidate: Candidate, problem_statement: str) -> float:
    """Score relevance by keyword overlap between problem and candidate content."""

    problem_tokens = {token for token in problem_statement.lower().split() if len(token) > 2}
    if not problem_tokens:
        return 0.0

    content = f"{candidate.title} {candidate.summary}".lower()
    overlap = sum(1 for token in problem_tokens if token in content)
    return min(1.0, overlap / len(problem_tokens))
