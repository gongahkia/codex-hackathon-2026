from __future__ import annotations

from app.intake.judging import ingest_judging_context


def test_judging_ingestion_does_not_fail_when_unscrapable() -> None:
    def failing_fetch(url: str) -> str:
        raise RuntimeError("blocked")

    context = ingest_judging_context(
        hackathon_url="https://devpost.com/hackathons/test",
        fetch_html=failing_fetch,
    )

    assert context.rubric_text == ""
    assert context.prize_tracks == []
    assert context.notes


def test_judging_ingestion_extracts_rubric_and_tracks() -> None:
    html = (
        "<html><head><title>Hackathon X</title></head><body>"
        "<h2>Judging Criteria</h2>"
        "<p>Innovation, technical quality, and impact.</p>"
        "<h3>AI Track</h3>"
        "<li>Best Climate Prize</li>"
        "</body></html>"
    )

    context = ingest_judging_context(
        hackathon_url="https://devpost.com/hackathons/test",
        fetch_html=lambda _: html,
    )

    assert "Hackathon X" in context.rubric_text
    assert any("track" in track.lower() or "prize" in track.lower() for track in context.prize_tracks)
