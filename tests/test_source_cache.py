from __future__ import annotations

import json

from app.storage.cache import RunLocalSourceCache


def test_run_local_source_cache_round_trip(tmp_path) -> None:
    cache = RunLocalSourceCache(tmp_path / "cache")
    rows = [{"title": "AI Planner", "urls": ["https://example.com"]}]

    cache.set("github", "AI planner", 5, rows)
    loaded = cache.get("github", "AI planner", 5)

    assert loaded == rows


def test_run_local_source_cache_returns_none_for_invalid_payload(tmp_path) -> None:
    cache = RunLocalSourceCache(tmp_path / "cache")
    path = cache._cache_path("github", "AI planner", 5)  # test helper access
    path.write_text(json.dumps({"rows": "invalid"}), encoding="utf-8")

    assert cache.get("github", "AI planner", 5) is None
