"""Tests for state/migrations/002_task_metadata.sql + apply_migrations.py.

Covers FARM-2.3 (tasks.worktree_owner_repo column) + FARM-2.4 (results
columns already declared in schema.sql; this migration verifies them).

- Migration applies cleanly to a pre-FARM-2.3 schema (no worktree_owner_repo).
- Migration is idempotent: re-running via apply_migrations.py is a no-op.
- Fresh init from state/schema.sql produces the column with no migration.
- apply_migrations.py refuses to act when the DB file is missing.
- apply_migrations.py honours AGENT_FARM_DB env override.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"
MIGRATION_SQL = REPO_ROOT / "state" / "migrations" / "002_task_metadata.sql"
APPLY_PY = REPO_ROOT / "scripts" / "lib" / "apply_migrations.py"


def _strip_002_column(schema_text: str) -> str:
    """Return a pre-FARM-2.3 schema (without worktree_owner_repo)."""
    pre = re.sub(
        r",\s*\n  -- FARM-2.3:.*?\n  worktree_owner_repo TEXT",
        "",
        schema_text,
        count=1,
        flags=re.S,
    )
    assert "worktree_owner_repo" not in pre, (
        "stripping helper failed; update the regex when the schema changes"
    )
    return pre


def _table_cols(db: Path, table: str) -> set[str]:
    conn = sqlite3.connect(str(db))
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    finally:
        conn.close()


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """A faux AGENT_FARM_ROOT with state/ + migrations/ wired up."""
    state = tmp_path / "state"
    state.mkdir()
    migrations = state / "migrations"
    migrations.mkdir()
    for m in (REPO_ROOT / "state" / "migrations").glob("*.sql"):
        shutil.copy(m, migrations / m.name)
    return tmp_path


def _init_pre_002(farm_root: Path) -> Path:
    """Initialise a tasks.sqlite using the pre-FARM-2.3 schema."""
    db = farm_root / "state" / "tasks.sqlite"
    pre = _strip_002_column(SCHEMA_SQL.read_text())
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(pre)
        conn.commit()
    finally:
        conn.close()
    return db


def _apply(farm_root: Path, db: Path) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "AGENT_FARM_ROOT": str(farm_root),
        "AGENT_FARM_DB": str(db),
    }
    return subprocess.run(
        [sys.executable, str(APPLY_PY)],
        env=env, capture_output=True, text=True, check=False,
    )


class TestMigrationApplies:
    def test_pre_002_schema_lacks_column(self, farm_root: Path) -> None:
        db = _init_pre_002(farm_root)
        assert "worktree_owner_repo" not in _table_cols(db, "tasks")

    def test_apply_adds_column(self, farm_root: Path) -> None:
        db = _init_pre_002(farm_root)
        res = _apply(farm_root, db)
        assert res.returncode == 0, res.stderr
        assert "applied 002_task_metadata.sql" in res.stdout
        assert "worktree_owner_repo" in _table_cols(db, "tasks")

    def test_apply_idempotent(self, farm_root: Path) -> None:
        db = _init_pre_002(farm_root)
        _apply(farm_root, db)
        res = _apply(farm_root, db)
        assert res.returncode == 0, res.stderr
        assert "skip 002_task_metadata.sql" in res.stdout
        # Single column still present (no duplicate).
        cols = [
            r for r in
            sqlite3.connect(str(db)).execute("PRAGMA table_info(tasks)").fetchall()
            if r[1] == "worktree_owner_repo"
        ]
        assert len(cols) == 1

    def test_dry_run_makes_no_changes(self, farm_root: Path) -> None:
        db = _init_pre_002(farm_root)
        env = {
            **os.environ,
            "AGENT_FARM_ROOT": str(farm_root),
            "AGENT_FARM_DB": str(db),
        }
        res = subprocess.run(
            [sys.executable, str(APPLY_PY), "--dry-run"],
            env=env, capture_output=True, text=True, check=False,
        )
        assert res.returncode == 0, res.stderr
        assert "would apply 002_task_metadata.sql" in res.stdout
        assert "worktree_owner_repo" not in _table_cols(db, "tasks")


class TestFreshInitMatchesMigration:
    def test_schema_sql_creates_column(self, tmp_path: Path) -> None:
        db = tmp_path / "fresh.sqlite"
        conn = sqlite3.connect(str(db))
        try:
            conn.executescript(SCHEMA_SQL.read_text())
            conn.commit()
        finally:
            conn.close()
        assert "worktree_owner_repo" in _table_cols(db, "tasks")
        # sha_before / sha_after already declared on results; FARM-2.4 keeps them.
        results_cols = _table_cols(db, "results")
        assert "sha_before" in results_cols
        assert "sha_after" in results_cols


class TestApplyMigrationsErrors:
    def test_missing_db_exits_nonzero(self, tmp_path: Path) -> None:
        env = {
            **os.environ,
            "AGENT_FARM_ROOT": str(tmp_path),
            "AGENT_FARM_DB": str(tmp_path / "nope.sqlite"),
        }
        # Need a migrations dir to bypass the early-return on empty dir.
        (tmp_path / "state" / "migrations").mkdir(parents=True)
        res = subprocess.run(
            [sys.executable, str(APPLY_PY)],
            env=env, capture_output=True, text=True, check=False,
        )
        assert res.returncode != 0
        assert "database missing" in res.stderr
