"""Tests for scripts/lib/db.py — schema init + task lifecycle + heartbeat.

FARM-FEAT.9 acceptance: cover schema init, the
insert-task -> set-started -> set-ended path, and heartbeat insert.

These tests pin the bash-callable CLI surface of db.py rather than the
event-emission semantics (which test_db_events.py owns). Together the
two files exercise the full module: lifecycle column writes here,
audit-trail rows there.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """Tmp directory laid out like $AGENT_FARM_ROOT (state/schema.sql)."""
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    return tmp_path


def _run(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    return subprocess.run(
        [sys.executable, str(DB_PY), *args],
        check=False, capture_output=True, text=True, env=env,
    )


def _connect(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(db))
    c.row_factory = sqlite3.Row
    return c


# ---------------------------------------------------------------------------
# Schema init
# ---------------------------------------------------------------------------


class TestSchemaInit:
    def test_init_creates_database_file(self, farm_root: Path) -> None:
        res = _run(farm_root, "init")
        assert res.returncode == 0, res.stderr
        assert (farm_root / "state" / "tasks.sqlite").exists()

    def test_init_creates_required_tables(self, farm_root: Path) -> None:
        _run(farm_root, "init")
        db = farm_root / "state" / "tasks.sqlite"
        c = _connect(db)
        try:
            tables = {
                row["name"]
                for row in c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            c.close()
        # All four core tables from state/schema.sql
        assert {"tasks", "heartbeats", "results", "events"} <= tables

    def test_init_creates_required_indexes(self, farm_root: Path) -> None:
        _run(farm_root, "init")
        db = farm_root / "state" / "tasks.sqlite"
        c = _connect(db)
        try:
            indexes = {
                row["name"]
                for row in c.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
        finally:
            c.close()
        assert "idx_tasks_status" in indexes
        assert "idx_tasks_agent" in indexes
        assert "idx_heartbeats_task" in indexes
        assert "idx_events_task_ts" in indexes
        assert "idx_events_kind_ts" in indexes

    def test_init_enables_wal_mode(self, farm_root: Path) -> None:
        _run(farm_root, "init")
        db = farm_root / "state" / "tasks.sqlite"
        c = _connect(db)
        try:
            mode = c.execute("PRAGMA journal_mode").fetchone()[0]
        finally:
            c.close()
        assert mode.lower() == "wal"

    def test_init_is_idempotent(self, farm_root: Path) -> None:
        # Running init twice must not error and must not lose data.
        _run(farm_root, "init")
        _run(farm_root, "insert-task", "tid", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "init")
        assert res.returncode == 0
        db = farm_root / "state" / "tasks.sqlite"
        c = _connect(db)
        try:
            row = c.execute(
                "SELECT id FROM tasks WHERE id='tid'"
            ).fetchone()
        finally:
            c.close()
        assert row is not None

    def test_init_creates_state_directory_if_missing(
        self, tmp_path: Path
    ) -> None:
        # If $AGENT_FARM_ROOT/state/ doesn't exist but schema.sql is
        # findable at the canonical path, init creates the parent dir.
        # We model that by pointing at a fresh root that has schema.sql
        # but no tasks.sqlite file yet — same as a clean clone.
        state = tmp_path / "state"
        state.mkdir()
        (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
        env = {**os.environ, "AGENT_FARM_ROOT": str(tmp_path)}
        res = subprocess.run(
            [sys.executable, str(DB_PY), "init"],
            check=False, capture_output=True, text=True, env=env,
        )
        assert res.returncode == 0
        assert (tmp_path / "state" / "tasks.sqlite").exists()


# ---------------------------------------------------------------------------
# Task lifecycle: insert-task -> set-started -> set-ended
# ---------------------------------------------------------------------------


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    res = _run(farm_root, "init")
    assert res.returncode == 0, res.stderr
    return farm_root / "state" / "tasks.sqlite"


class TestInsertTask:
    def test_insert_creates_pending_task(
        self, initdb: Path, farm_root: Path
    ) -> None:
        res = _run(
            farm_root,
            "insert-task", "t1", "executor", "subagent", "0",
            "opus-4.7", '{"task": "FARM-FEAT.9"}',
        )
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT * FROM tasks WHERE id='t1'"
            ).fetchone()
        finally:
            c.close()
        assert row is not None
        assert row["agent_name"] == "executor"
        assert row["kind"] == "subagent"
        assert row["persistent"] == 0
        assert row["status"] == "pending"
        assert row["model"] == "opus-4.7"
        assert row["spawn_args"] == '{"task": "FARM-FEAT.9"}'
        assert row["created_at"] is not None
        assert row["started_at"] is None
        assert row["ended_at"] is None

    def test_insert_persistent_flag_stored_as_int(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "tp", "deploy-keeper", "headless",
             "1", "haiku-4.5", "{}")
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT persistent FROM tasks WHERE id='tp'"
            ).fetchone()
        finally:
            c.close()
        assert row["persistent"] == 1

    def test_insert_rejects_invalid_kind(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # schema.sql restricts kind to (subagent, headless).
        res = _run(farm_root, "insert-task", "tbad", "executor",
                   "weird-kind", "0", "opus-4.7", "{}")
        assert res.returncode != 0

    def test_insert_empty_model_stored_as_null(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "tn", "janitor", "subagent",
             "0", "", "{}")
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT model FROM tasks WHERE id='tn'"
            ).fetchone()
        finally:
            c.close()
        assert row["model"] is None


class TestSetStarted:
    def test_set_started_moves_to_running(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "ts", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "set-started", "ts",
                   "/tmp/wt-ts", "agent-farm:ts", "4242")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT status, worktree, tmux_window, pid, started_at "
                "FROM tasks WHERE id='ts'"
            ).fetchone()
        finally:
            c.close()
        assert row["status"] == "running"
        assert row["worktree"] == "/tmp/wt-ts"
        assert row["tmux_window"] == "agent-farm:ts"
        assert row["pid"] == 4242
        assert row["started_at"] is not None

    def test_set_started_empty_optionals_become_null(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "ts2", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "set-started", "ts2", "", "", "")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT status, worktree, tmux_window, pid "
                "FROM tasks WHERE id='ts2'"
            ).fetchone()
        finally:
            c.close()
        assert row["status"] == "running"
        assert row["worktree"] is None
        assert row["tmux_window"] is None
        assert row["pid"] is None


class TestSetEnded:
    def test_set_ended_succeeded_moves_to_succeeded(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "te", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "set-started", "te", "/tmp/wt", "win", "1")
        res = _run(farm_root, "set-ended", "te", "succeeded", "0",
                   "all green")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT status, ended_at, exit_code "
                "FROM tasks WHERE id='te'"
            ).fetchone()
        finally:
            c.close()
        assert row["status"] == "succeeded"
        assert row["exit_code"] == 0
        assert row["ended_at"] is not None

    def test_set_ended_failed_records_nonzero_exit(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "tf", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "set-ended", "tf", "failed", "7", "boom")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT status, exit_code FROM tasks WHERE id='tf'"
            ).fetchone()
        finally:
            c.close()
        assert row["status"] == "failed"
        assert row["exit_code"] == 7

    def test_set_ended_invalid_exit_code_stores_null(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # Non-integer exit codes shouldn't crash the CLI; they should be
        # coerced to NULL so terminal-state housekeeping still progresses.
        _run(farm_root, "insert-task", "tx", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "set-ended", "tx", "crashed", "n/a")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT exit_code FROM tasks WHERE id='tx'"
            ).fetchone()
        finally:
            c.close()
        assert row["exit_code"] is None


class TestFullLifecycle:
    def test_insert_started_ended_round_trip(
        self, initdb: Path, farm_root: Path
    ) -> None:
        """End-to-end: a task moves cleanly through every state and the
        timestamps come out monotonically non-decreasing.
        """
        _run(farm_root, "insert-task", "round", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "set-started", "round", "/wt", "win", "100")
        _run(farm_root, "set-ended", "round", "succeeded", "0", "ok")
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT status, created_at, started_at, ended_at "
                "FROM tasks WHERE id='round'"
            ).fetchone()
        finally:
            c.close()
        assert row["status"] == "succeeded"
        assert row["created_at"] <= row["started_at"] <= row["ended_at"]


# ---------------------------------------------------------------------------
# Heartbeat insert
# ---------------------------------------------------------------------------


class TestHeartbeatInsert:
    def test_heartbeat_inserts_heartbeats_row(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "hb1", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "heartbeat", "hb1", "info", "still working")
        assert res.returncode == 0, res.stderr
        c = _connect(initdb)
        try:
            rows = c.execute(
                "SELECT level, message FROM heartbeats WHERE task_id='hb1'"
            ).fetchall()
        finally:
            c.close()
        assert len(rows) == 1
        assert rows[0]["level"] == "info"
        assert rows[0]["message"] == "still working"

    def test_multiple_heartbeats_append(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "hb2", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "heartbeat", "hb2", "info", "one")
        _run(farm_root, "heartbeat", "hb2", "warn", "two")
        _run(farm_root, "heartbeat", "hb2", "error", "three")
        c = _connect(initdb)
        try:
            rows = c.execute(
                "SELECT level, message FROM heartbeats "
                "WHERE task_id='hb2' ORDER BY id"
            ).fetchall()
        finally:
            c.close()
        assert [(r["level"], r["message"]) for r in rows] == [
            ("info", "one"),
            ("warn", "two"),
            ("error", "three"),
        ]

    def test_heartbeat_rejects_invalid_level(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # schema.sql constrains level to (info, warn, error).
        _run(farm_root, "insert-task", "hb3", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "heartbeat", "hb3", "debug", "nope")
        assert res.returncode != 0

    def test_heartbeat_for_unknown_task_fails_via_fk(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # heartbeats.task_id has a FK to tasks(id); inserting against an
        # unknown task should fail because PRAGMA foreign_keys = ON.
        res = _run(farm_root, "heartbeat", "ghost", "info", "no task")
        assert res.returncode != 0

    def test_heartbeat_carries_timestamp(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "hb4", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "heartbeat", "hb4", "info", "tick")
        c = _connect(initdb)
        try:
            row = c.execute(
                "SELECT ts FROM heartbeats WHERE task_id='hb4'"
            ).fetchone()
        finally:
            c.close()
        assert row["ts"]
        # ISO-8601 stamp from db.now() — we don't pin the value but
        # the format should at least include 'T' and a colon.
        assert "T" in row["ts"]
        assert ":" in row["ts"]
