from __future__ import annotations

from app.sources.dorahacks import DoraHacksAdapter


def test_dorahacks_adapter_parses_live_results_html() -> None:
    html = (
        "<html><body>"
        '<a href="/project/green-ai">Green AI</a>'
        '<a href="https://dorahacks.io/buidl/rapid-prototype"><span>Rapid Prototype</span></a>'
        '<a href="/project/green-ai">Green AI Duplicate</a>'
        '<a href="/hackathon/abc">Ignore Non-Project</a>'
        "</body></html>"
    )

    adapter = DoraHacksAdapter(fetch_html=lambda url, policy: html)
    rows = adapter.search("AI planner", limit=5)

    assert len(rows) == 2
    assert rows[0]["title"] == "Green AI"
    assert rows[0]["urls"] == ["https://dorahacks.io/project/green-ai"]
    assert rows[1]["title"] == "Rapid Prototype"
    assert rows[1]["urls"] == ["https://dorahacks.io/buidl/rapid-prototype"]
    assert rows[0]["signals"]["live_fetch"] is True


def test_dorahacks_adapter_returns_empty_on_fetch_failure() -> None:
    def failing_fetch(url, policy):
        raise RuntimeError("network blocked")

    adapter = DoraHacksAdapter(fetch_html=failing_fetch)
    assert adapter.search("AI planner", limit=3) == []
