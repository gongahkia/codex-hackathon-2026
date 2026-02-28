"""Detailed ranking matrix renderer."""

from __future__ import annotations

from typing import Iterable

from app.services.ranking import ScoredCandidate


def render_ranked_matrix(ranked_candidates: Iterable[ScoredCandidate]) -> str:
    """Render markdown matrix with factor scores and source links."""

    rows = [
        "| Rank | Title | Source | Relevance | Feasibility | Speed | Evidence | Total | Link |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]

    for idx, item in enumerate(ranked_candidates, start=1):
        candidate = item.candidate
        link = candidate.urls[0] if candidate.urls else ""
        rows.append(
            "| {rank} | {title} | {source} | {rel:.2f} | {fea:.2f} | {spd:.2f} | {evi:.2f} | {total:.2f} | {link} |".format(
                rank=idx,
                title=candidate.title.replace("|", "\\|"),
                source=candidate.source,
                rel=item.factors.get("relevance", 0.0),
                fea=item.factors.get("feasibility", 0.0),
                spd=item.factors.get("speed", 0.0),
                evi=item.factors.get("evidence", 0.0),
                total=item.total_score,
                link=link,
            )
        )

    return "\n".join(rows)
