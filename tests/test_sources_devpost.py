from __future__ import annotations

from app.sources.devpost import DevpostAdapter


def test_devpost_adapter_parses_live_results_html() -> None:
    html = (
        "<html><body>"
        '<a href="/software/alpha-app">Alpha App</a>'
        '<a href="https://devpost.com/software/beta-tool"><span>Beta Tool</span></a>'
        '<a href="/software/alpha-app">Alpha App Duplicate</a>'
        '<a href="/hackathons/example-event">Ignore Non-Software</a>'
        "</body></html>"
    )

    adapter = DevpostAdapter(fetch_html=lambda url, policy: html)
    rows = adapter.search("AI planner", limit=5)

    assert len(rows) == 2
    assert rows[0]["title"] == "Alpha App"
    assert rows[0]["urls"] == ["https://devpost.com/software/alpha-app"]
    assert rows[1]["title"] == "Beta Tool"
    assert rows[1]["urls"] == ["https://devpost.com/software/beta-tool"]
    assert rows[0]["signals"]["live_fetch"] is True


def test_devpost_adapter_returns_empty_on_fetch_failure() -> None:
    def failing_fetch(url, policy):
        raise RuntimeError("network blocked")

    adapter = DevpostAdapter(fetch_html=failing_fetch)
    assert adapter.search("AI planner", limit=3) == []
