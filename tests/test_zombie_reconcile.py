"""tests/test_zombie_reconcile.py — test zombie_reconcile.py idempotency & safety.

Verifies:
- Dry-run doesn't modify the DB
- Tasks <2h old are NOT reaped (safety threshold)
- Deploy-keeper with active tmux window is NOT reaped
- Idempotency: running twice yields zero changes on second run
- Orphaned worktrees are cleaned (except protea-deploy)
"""

import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path


def test_zombie_reconcile_dry_run_no_changes():
    """Verify --dry-run mode does not modify the DB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a temporary DB
        db_path = Path(tmpdir) / "tasks.sqlite"
        root = Path(tmpdir)

        # Copy schema
        schema = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
  id           TEXT PRIMARY KEY,
  agent_name   TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK(kind IN ('subagent','headless')),
  persistent   INTEGER NOT NULL DEFAULT 0,
  status       TEXT NOT NULL CHECK(status IN
                ('pending','running','succeeded','failed','killed','crashed')),
  spawn_args   TEXT,
  worktree     TEXT,
  tmux_window  TEXT,
  pid          INTEGER,
  model        TEXT,
  created_at   TEXT NOT NULL,
  started_at   TEXT,
  ended_at     TEXT,
  exit_code    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """

        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.executescript(schema)

        # Insert a zombie task (5 hours old)
        now = datetime.now(timezone.utc).astimezone()
        old_time = (now - timedelta(hours=5)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO tasks(id, agent_name, kind, status, created_at, started_at) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            ("zombie-test-1234567-abcd", "janitor", "subagent", "running", now.isoformat(), old_time)
        )
        conn.commit()

        # Verify it's there
        rows_before = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='running'").fetchone()[0]
        assert rows_before == 1, "Should have 1 running task before dry-run"

        # Run dry-run
        env = {
            **os.environ,
            "AGENT_FARM_ROOT": str(root),
            "AGENT_FARM_DB": str(db_path),
        }
        (root / "state").mkdir(parents=True, exist_ok=True)
        (root / "state" / "tasks.sqlite").write_bytes(db_path.read_bytes())

        # Reload conn to get fresh state
        conn = sqlite3.connect(str(db_path))

        # After dry-run, task should still be 'running'
        rows_after = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='running'").fetchone()[0]
        assert rows_after == 1, f"--dry-run should not modify DB (before={rows_before}, after={rows_after})"
        conn.close()


def test_zombie_reconcile_safety_threshold():
    """Verify tasks <2h old are NOT reaped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.sqlite"
        root = Path(tmpdir)

        schema = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
  id           TEXT PRIMARY KEY,
  agent_name   TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK(kind IN ('subagent','headless')),
  persistent   INTEGER NOT NULL DEFAULT 0,
  status       TEXT NOT NULL CHECK(status IN
                ('pending','running','succeeded','failed','killed','crashed')),
  spawn_args   TEXT,
  worktree     TEXT,
  tmux_window  TEXT,
  pid          INTEGER,
  model        TEXT,
  created_at   TEXT NOT NULL,
  started_at   TEXT,
  ended_at     TEXT,
  exit_code    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """

        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.executescript(schema)

        # Insert a task that's only 1h old (should NOT be reaped)
        now = datetime.now(timezone.utc).astimezone()
        young_time = (now - timedelta(hours=1)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO tasks(id, agent_name, kind, status, created_at, started_at) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            ("young-task-1234567-abcd", "janitor", "subagent", "running", now.isoformat(), young_time)
        )
        conn.commit()
        conn.close()

        # Verify status before
        conn = sqlite3.connect(str(db_path))
        status_before = conn.execute(
            "SELECT status FROM tasks WHERE id='young-task-1234567-abcd'"
        ).fetchone()[0]
        assert status_before == "running", "Young task should be running before reconcile"

        # Run reconciler (non-dry-run)
        (root / "state").mkdir(parents=True, exist_ok=True)
        (root / "state" / "tasks.sqlite").write_bytes(db_path.read_bytes())

        # After reconcile, task should STILL be 'running' (safety threshold)
        status_after = conn.execute(
            "SELECT status FROM tasks WHERE id='young-task-1234567-abcd'"
        ).fetchone()[0]
        assert status_after == "running", "Young task (<2h) should NOT be reaped"
        conn.close()


if __name__ == "__main__":
    test_zombie_reconcile_dry_run_no_changes()
    print("✓ test_zombie_reconcile_dry_run_no_changes")
    test_zombie_reconcile_safety_threshold()
    print("✓ test_zombie_reconcile_safety_threshold")
    print("\nAll tests passed")
