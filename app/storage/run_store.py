"""SQLite-backed run store."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class RunStore:
    """Persist run configs, transitions, and status in SQLite."""

    def __init__(self, db_path: str | Path = "runs.db") -> None:
        self.db_path = str(db_path)
        db_parent = Path(self.db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    transitions_json TEXT NOT NULL,
                    final_status TEXT,
                    recommendation_title TEXT,
                    warning_count INTEGER DEFAULT 0,
                    fatal_count INTEGER DEFAULT 0,
                    last_error_code TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()
            }
            if "warning_count" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN warning_count INTEGER DEFAULT 0")
            if "fatal_count" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN fatal_count INTEGER DEFAULT 0")
            if "last_error_code" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN last_error_code TEXT")

    def save_config(self, run_id: str, config: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, config_json, transitions_json, final_status, recommendation_title)
                VALUES (?, ?, ?, NULL, NULL)
                ON CONFLICT(run_id) DO UPDATE SET config_json=excluded.config_json
                """,
                (run_id, json.dumps(config), json.dumps([])),
            )

    def append_transition(self, run_id: str, state: str) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT transitions_json FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            transitions: List[str] = []
            if row and row[0]:
                transitions = json.loads(row[0])
            transitions.append(state)
            conn.execute(
                "UPDATE runs SET transitions_json = ?, updated_at = CURRENT_TIMESTAMP WHERE run_id = ?",
                (json.dumps(transitions), run_id),
            )

    def set_final_status(
        self,
        run_id: str,
        status: str,
        recommendation_title: str = "",
        warning_count: int = 0,
        fatal_count: int = 0,
        last_error_code: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET final_status = ?,
                    recommendation_title = ?,
                    warning_count = ?,
                    fatal_count = ?,
                    last_error_code = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ?
                """,
                (status, recommendation_title, warning_count, fatal_count, last_error_code, run_id),
            )

    def get_run(self, run_id: str) -> Dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    config_json,
                    transitions_json,
                    final_status,
                    recommendation_title,
                    warning_count,
                    fatal_count,
                    last_error_code
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "config": json.loads(row[0]),
                "transitions": json.loads(row[1]),
                "final_status": row[2],
                "recommendation_title": row[3],
                "warning_count": row[4],
                "fatal_count": row[5],
                "last_error_code": row[6],
            }
