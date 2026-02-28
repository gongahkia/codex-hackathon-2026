"""Evidence gate policy."""

from __future__ import annotations

from typing import Iterable

from app.models.candidate import Candidate
from app.services.evidence import extract_build_writeup_links, extract_code_artifact_links


def passes_minimum_evidence(
    candidate: Candidate, supporting_candidates: Iterable[Candidate] | None = None
) -> bool:
    """Require code + writeup evidence and at least two source types."""

    code_links = extract_code_artifact_links(candidate)
    writeup_links = extract_build_writeup_links(candidate)

    support = list(supporting_candidates) if supporting_candidates is not None else [candidate]
    source_types = {item.source for item in support if item.source}

    return bool(code_links) and bool(writeup_links) and len(source_types) >= 2
