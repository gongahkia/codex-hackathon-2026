from __future__ import annotations

import sqlite3

from app.storage.run_store import RunStore


def test_run_store_migrates_observability_columns(tmp_path) -> None:
    db_path = tmp_path / "runs.db"
    store = RunStore(db_path=db_path)
    _ = store

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()}

    assert {"warning_count", "fatal_count", "last_error_code"} <= columns


def test_run_store_persists_warning_and_fatal_counts(tmp_path) -> None:
    db_path = tmp_path / "runs.db"
    store = RunStore(db_path=db_path)
    store.save_config("run-1", {"problem_statement": "x"})
    store.set_final_status(
        "run-1",
        "FAILED",
        recommendation_title="demo",
        warning_count=2,
        fatal_count=1,
        last_error_code="TIMEOUT_ERROR",
    )

    payload = store.get_run("run-1")
    assert payload is not None
    assert payload["warning_count"] == 2
    assert payload["fatal_count"] == 1
    assert payload["last_error_code"] == "TIMEOUT_ERROR"
