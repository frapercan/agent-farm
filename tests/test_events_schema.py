"""Tests for state/migrations/001_events.sql + state/schema.sql (FARM-2.1).

Covers:
- The migration script applies cleanly to a fresh sqlite database that
  already has the base tasks/heartbeats/results tables.
- The migration is idempotent (running it twice does not error).
- After applying, the events table exists with the expected columns + CHECK
  constraint on `kind`.
- Both required indices (events.task_id, ts DESC) and (events.kind, ts DESC)
  are created.
- A fresh init from state/schema.sql produces the same events table shape
  (so init.sh and the migration stay in lockstep).
- Foreign-key cascade: deleting a task removes its events.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"
MIGRATION_SQL = REPO_ROOT / "state" / "migrations" / "001_events.sql"


def _exec_script(db_path: Path, sql_text: str) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(sql_text)
        conn.commit()
    finally:
        conn.close()


def _base_schema_without_events() -> str:
    """The schema.sql content with the events block stripped, so we can
    simulate the pre-migration shape of a live database.
    """
    txt = SCHEMA_SQL.read_text()
    marker = "-- FARM-2.1"
    if marker in txt:
        return txt.split(marker)[0]
    return txt


@pytest.fixture()
def base_db(tmp_path: Path) -> Path:
    """A database initialised with the pre-FARM-2.1 schema (no events)."""
    db = tmp_path / "tasks.sqlite"
    _exec_script(db, _base_schema_without_events())
    # Sanity: events table not yet present.
    conn = sqlite3.connect(str(db))
    try:
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    finally:
        conn.close()
    assert "events" not in names
    assert "tasks" in names
    return db


class TestMigrationApplies:
    def test_migration_creates_events_table(self, base_db: Path) -> None:
        _exec_script(base_db, MIGRATION_SQL.read_text())
        conn = sqlite3.connect(str(base_db))
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()}
        finally:
            conn.close()
        assert cols == {
            "id", "task_id", "ts", "kind", "level", "message", "payload_json"
        }

    def test_migration_is_idempotent(self, base_db: Path) -> None:
        sql = MIGRATION_SQL.read_text()
        _exec_script(base_db, sql)
        # Second run must not raise.
        _exec_script(base_db, sql)

    def test_indices_present(self, base_db: Path) -> None:
        _exec_script(base_db, MIGRATION_SQL.read_text())
        conn = sqlite3.connect(str(base_db))
        try:
            idx = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
            ).fetchall()}
        finally:
            conn.close()
        assert "idx_events_task_ts" in idx
        assert "idx_events_kind_ts" in idx

    def test_kind_check_constraint(self, base_db: Path) -> None:
        _exec_script(base_db, MIGRATION_SQL.read_text())
        conn = sqlite3.connect(str(base_db))
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute(
                "INSERT INTO tasks(id, agent_name, kind, status, created_at) "
                "VALUES('t1', 'a', 'subagent', 'pending', '2026-05-17T00:00:00Z')"
            )
            conn.commit()
            # Valid kinds insert fine.
            for k in ("spawn", "start", "end", "kill", "heartbeat", "cleanup"):
                conn.execute(
                    "INSERT INTO events(task_id, ts, kind) VALUES(?, ?, ?)",
                    ("t1", "2026-05-17T00:00:00Z", k),
                )
            conn.commit()
            # Invalid kind rejected.
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO events(task_id, ts, kind) VALUES('t1','2026-05-17T00:00:00Z','bogus')"
                )
        finally:
            conn.close()


class TestFreshInitMatchesMigration:
    def test_schema_sql_creates_events(self, tmp_path: Path) -> None:
        db = tmp_path / "fresh.sqlite"
        _exec_script(db, SCHEMA_SQL.read_text())
        conn = sqlite3.connect(str(db))
        try:
            cols = {r[1] for r in conn.execute(
                "PRAGMA table_info(events)"
            ).fetchall()}
            idx = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
            ).fetchall()}
        finally:
            conn.close()
        assert "events" in {r[0] for r in sqlite3.connect(str(db)).execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert cols == {
            "id", "task_id", "ts", "kind", "level", "message", "payload_json"
        }
        assert idx == {"idx_events_task_ts", "idx_events_kind_ts"}


class TestForeignKeyCascade:
    def test_task_delete_cascades_to_events(self, base_db: Path) -> None:
        _exec_script(base_db, MIGRATION_SQL.read_text())
        conn = sqlite3.connect(str(base_db))
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute(
                "INSERT INTO tasks(id, agent_name, kind, status, created_at) "
                "VALUES('t-cascade', 'a', 'subagent', 'pending', '2026-05-17T00:00:00Z')"
            )
            conn.execute(
                "INSERT INTO events(task_id, ts, kind) "
                "VALUES('t-cascade', '2026-05-17T00:00:00Z', 'spawn')"
            )
            conn.commit()
            assert conn.execute(
                "SELECT COUNT(*) FROM events WHERE task_id='t-cascade'"
            ).fetchone()[0] == 1
            conn.execute("DELETE FROM tasks WHERE id='t-cascade'")
            conn.commit()
            assert conn.execute(
                "SELECT COUNT(*) FROM events WHERE task_id='t-cascade'"
            ).fetchone()[0] == 0
        finally:
            conn.close()
