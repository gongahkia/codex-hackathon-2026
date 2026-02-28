from __future__ import annotations

import pytest

from app.intake.hackathon_link import preprocess_hackathon_input


def test_preprocess_from_devpost_link_extracts_problem_and_similar() -> None:
    main_url = "https://devpost.com/hackathons/sample-event"

    def fake_fetch(url: str) -> str:
        if url == main_url:
            return (
                "<html><head>"
                "<title>Sample AI Hackathon | Devpost</title>"
                '<meta name="description" content="Build an AI-powered game for students." />'
                "</head><body>"
                '<a href="https://devpost.com/hackathons/another-ai-hackathon">Another</a>'
                "</body></html>"
            )
        if "devpost.com/hackathons?search=" in url:
            return (
                "<html><body>"
                '<a href="https://devpost.com/hackathons/edu-ai-hack">Edu AI</a>'
                '<a href="https://devpost.com/hackathons/rapid-build">Rapid Build</a>'
                "</body></html>"
            )
        raise AssertionError(f"Unexpected URL: {url}")

    intake = preprocess_hackathon_input(
        problem_statement=None,
        hackathon_url=main_url,
        similar_limit=3,
        fetch_html=fake_fetch,
    )

    assert "Sample AI Hackathon" in intake.problem_statement
    assert "Build an AI-powered game" in intake.problem_statement
    assert intake.source_url == main_url
    assert len(intake.similar_hackathons) == 3


def test_preprocess_rejects_non_luma_devpost_links() -> None:
    with pytest.raises(ValueError):
        preprocess_hackathon_input(
            problem_statement=None,
            hackathon_url="https://example.com/hackathon",
        )


def test_preprocess_keeps_manual_problem_statement() -> None:
    intake = preprocess_hackathon_input(
        problem_statement="Build a multiplayer puzzle game",
        hackathon_url=None,
    )
    assert intake.problem_statement == "Build a multiplayer puzzle game"
    assert intake.similar_hackathons == []
