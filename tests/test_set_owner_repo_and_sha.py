"""Tests for db.py set-worktree-owner-repo and set-sha (FARM-2.3 + FARM-2.4).

Covers:
- Round-trip: column / sha values land in their intended row.
- set-sha upserts the results row when it doesn't exist yet.
- set-sha preserves the sibling column (writing 'after' doesn't blank 'before').
- Rejects unknown task_id, bad which-arg, empty repo/sha.
- No events row is emitted by either command (plumbing, not lifecycle).
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
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    return tmp_path


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True, env=env,
    )
    return farm_root / "state" / "tasks.sqlite"


def _run(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    return subprocess.run(
        [sys.executable, str(DB_PY), *args],
        env=env, capture_output=True, text=True, check=False,
    )


def _seed_task(farm_root: Path, task_id: str = "t-1") -> None:
    res = _run(farm_root, "insert-task", task_id, "executor", "subagent",
               "0", "opus-4.7", "{}")
    assert res.returncode == 0, res.stderr


def _owner_repo(db: Path, task_id: str) -> str | None:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT worktree_owner_repo FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def _shas(db: Path, task_id: str) -> tuple[str | None, str | None]:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT sha_before, sha_after FROM results WHERE task_id=?",
            (task_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return (None, None)
    return row


class TestSetWorktreeOwnerRepo:
    def test_round_trip(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        res = _run(farm_root, "set-worktree-owner-repo", "t-1", "/repo/foo")
        assert res.returncode == 0, res.stderr
        assert _owner_repo(initdb, "t-1") == "/repo/foo"

    def test_second_call_overwrites(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        _run(farm_root, "set-worktree-owner-repo", "t-1", "/repo/foo")
        _run(farm_root, "set-worktree-owner-repo", "t-1", "/repo/bar")
        assert _owner_repo(initdb, "t-1") == "/repo/bar"

    def test_rejects_unknown_task(self, initdb: Path, farm_root: Path) -> None:
        res = _run(farm_root, "set-worktree-owner-repo", "ghost", "/repo")
        assert res.returncode != 0
        assert "unknown task_id" in res.stderr

    def test_rejects_empty_repo(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        res = _run(farm_root, "set-worktree-owner-repo", "t-1", "")
        assert res.returncode != 0
        assert "non-empty" in res.stderr

    def test_emits_no_event(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        before_n = sqlite3.connect(str(initdb)).execute(
            "SELECT COUNT(*) FROM events WHERE task_id=?", ("t-1",)
        ).fetchone()[0]
        _run(farm_root, "set-worktree-owner-repo", "t-1", "/repo/foo")
        after_n = sqlite3.connect(str(initdb)).execute(
            "SELECT COUNT(*) FROM events WHERE task_id=?", ("t-1",)
        ).fetchone()[0]
        assert before_n == after_n


class TestSetSha:
    def test_writes_before_creates_results_row(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root)
        # No results row yet — set-sha must upsert one.
        assert _shas(initdb, "t-1") == (None, None)
        res = _run(farm_root, "set-sha", "t-1", "before", "abc1234")
        assert res.returncode == 0, res.stderr
        assert _shas(initdb, "t-1") == ("abc1234", None)

    def test_writes_after_preserves_before(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root)
        _run(farm_root, "set-sha", "t-1", "before", "abc1234")
        _run(farm_root, "set-sha", "t-1", "after", "def5678")
        assert _shas(initdb, "t-1") == ("abc1234", "def5678")

    def test_writes_after_first(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # Reverse order: finalize wrote sha_after before spawn ever wrote
        # sha_before (degenerate; still must upsert correctly).
        _seed_task(farm_root)
        res = _run(farm_root, "set-sha", "t-1", "after", "def5678")
        assert res.returncode == 0, res.stderr
        assert _shas(initdb, "t-1") == (None, "def5678")

    def test_rejects_bad_which(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        res = _run(farm_root, "set-sha", "t-1", "middle", "abc")
        assert res.returncode != 0
        assert "before" in res.stderr  # "must be 'before' or 'after'..."

    def test_rejects_unknown_task(self, initdb: Path, farm_root: Path) -> None:
        res = _run(farm_root, "set-sha", "ghost", "before", "abc")
        assert res.returncode != 0
        assert "unknown task_id" in res.stderr

    def test_rejects_empty_sha(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        res = _run(farm_root, "set-sha", "t-1", "before", "")
        assert res.returncode != 0
        assert "non-empty" in res.stderr

    def test_emits_no_event(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root)
        before_n = sqlite3.connect(str(initdb)).execute(
            "SELECT COUNT(*) FROM events WHERE task_id=?", ("t-1",)
        ).fetchone()[0]
        _run(farm_root, "set-sha", "t-1", "before", "abc1234")
        _run(farm_root, "set-sha", "t-1", "after", "def5678")
        after_n = sqlite3.connect(str(initdb)).execute(
            "SELECT COUNT(*) FROM events WHERE task_id=?", ("t-1",)
        ).fetchone()[0]
        assert before_n == after_n

    def test_preserves_summary_and_metrics(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # Real-life ordering: finalize writes summary + sha_after + metrics.
        # None of those columns should clobber each other.
        _seed_task(farm_root)
        conn = sqlite3.connect(str(initdb))
        try:
            conn.execute(
                "INSERT INTO results(task_id, summary) VALUES(?, ?)",
                ("t-1", "did the thing"),
            )
            conn.commit()
        finally:
            conn.close()
        _run(farm_root, "set-sha", "t-1", "before", "abc1234")
        _run(farm_root, "set-sha", "t-1", "after", "def5678")
        _run(farm_root, "set-metrics", "t-1", '{"usd_estimate": 0.01}')
        conn = sqlite3.connect(str(initdb))
        try:
            row = conn.execute(
                "SELECT summary, sha_before, sha_after, metrics_json "
                "FROM results WHERE task_id=?",
                ("t-1",),
            ).fetchone()
        finally:
            conn.close()
        assert row[0] == "did the thing"
        assert row[1] == "abc1234"
        assert row[2] == "def5678"
        assert "usd_estimate" in row[3]
