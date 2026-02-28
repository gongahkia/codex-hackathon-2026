from __future__ import annotations

from app.orchestrator.pipeline import _enforce_run_retention
from app.storage.run_store import RunStore


def test_enforce_run_retention_prunes_old_directories_and_db_rows(tmp_path) -> None:
    runs_root = tmp_path / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    for run_id in ("run-1", "run-2", "run-3"):
        run_dir = runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "marker.txt").write_text(run_id, encoding="utf-8")

    store = RunStore(db_path=tmp_path / "runs.db")
    store.save_config("run-1", {"problem_statement": "x"})
    store.save_config("run-2", {"problem_statement": "x"})
    store.save_config("run-3", {"problem_statement": "x"})

    _enforce_run_retention(store, runs_root=runs_root, keep_latest=2)

    assert (runs_root / "run-3").exists()
    assert (runs_root / "run-2").exists()
    assert not (runs_root / "run-1").exists()

    assert store.get_run("run-3") is not None
    assert store.get_run("run-2") is not None
    assert store.get_run("run-1") is None
