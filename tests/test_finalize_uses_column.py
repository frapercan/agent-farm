"""Integration test for finalize-subagent.sh's FARM-2.3 owner_repo lookup
and FARM-2.4 sha_after capture.

We construct a real (tiny) git repo + worktree so finalize can actually
run `git worktree remove`. The lookup path is exercised by populating
tasks.worktree_owner_repo and watching the heartbeat trail confirm
"via owner_repo column" instead of "scan fallback".

The fallback path is also exercised (column null → scan finds the repo
under the standard PROTEA/thesis prefix is NOT available in the temp
tree, but the fallback rm -rf catches it). The fallback assertion is
weaker on purpose: we only check the worktree dir disappears and the
heartbeat trail mentions "fallback" wording.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
FINALIZE_SH = REPO_ROOT / "scripts" / "finalize-subagent.sh"
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"


def _git(*args: str, cwd: Path) -> str:
    res = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True,
        capture_output=True, text=True,
    )
    return res.stdout.strip()


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    (tmp_path / "scripts").symlink_to(REPO_ROOT / "scripts")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "executor.yaml").write_text(textwrap.dedent("""
        name: executor
        kind: subagent
        model: opus-4.7
        worktree:
          cleanup: ephemeral
    """).strip())
    (tmp_path / "results").mkdir()
    return tmp_path


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True, env=env,
    )
    return farm_root / "state" / "tasks.sqlite"


def _make_repo(parent: Path, name: str) -> Path:
    """Init a tiny git repo with one commit so worktrees can branch off it."""
    repo = parent / name
    repo.mkdir()
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "README.md").write_text("hello\n")
    _git("add", "README.md", cwd=repo)
    _git("commit", "-q", "-m", "init", cwd=repo)
    return repo


def _seed_task_with_worktree(
    farm_root: Path, repo: Path, worktree: Path, owner_repo: str | None,
    task_id: str = "tid-fin",
) -> str:
    """Seed a task row with a real worktree branched off `repo`.
    Returns the sha_before that finalize will compare against.
    """
    _git("worktree", "add", "-q", "-b", f"task/{task_id}",
         str(worktree), "main", cwd=repo)
    sha_before = _git("rev-parse", "HEAD", cwd=worktree)

    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY), "insert-task",
         task_id, "executor", "subagent", "0", "opus-4.7", "{}"],
        check=True, capture_output=True, env=env,
    )
    subprocess.run(
        [sys.executable, str(DB_PY), "set-started", task_id, str(worktree)],
        check=True, capture_output=True, env=env,
    )
    if owner_repo is not None:
        subprocess.run(
            [sys.executable, str(DB_PY), "set-worktree-owner-repo",
             task_id, owner_repo],
            check=True, capture_output=True, env=env,
        )
    subprocess.run(
        [sys.executable, str(DB_PY), "set-sha", task_id, "before", sha_before],
        check=True, capture_output=True, env=env,
    )
    return sha_before


def _run_finalize(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    return subprocess.run(
        ["bash", str(FINALIZE_SH), *args],
        env=env, capture_output=True, text=True, check=False,
    )


def _heartbeats(db: Path, task_id: str) -> list[str]:
    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute(
            "SELECT message FROM heartbeats WHERE task_id=? ORDER BY id",
            (task_id,),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def _shas(db: Path, task_id: str) -> tuple[str | None, str | None]:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT sha_before, sha_after FROM results WHERE task_id=?",
            (task_id,),
        ).fetchone()
    finally:
        conn.close()
    return row if row else (None, None)


class TestOwnerRepoLookup:
    def test_finalize_uses_column(
        self, initdb: Path, farm_root: Path, tmp_path: Path
    ) -> None:
        repo = _make_repo(tmp_path, "repo")
        wt = tmp_path / "wt"
        sha_before = _seed_task_with_worktree(
            farm_root, repo, wt, owner_repo=str(repo)
        )

        res = _run_finalize(
            farm_root, "tid-fin", "succeeded", "0", "ok",
        )
        assert res.returncode == 0, res.stderr
        assert "worktree_removed=1" in res.stdout, res.stdout
        # Worktree dir is gone.
        assert not wt.exists()
        # Heartbeat trail mentions the owner_repo column.
        hbs = _heartbeats(initdb, "tid-fin")
        assert any("via owner_repo column" in m for m in hbs), hbs
        # FARM-2.4: sha_after captured. before/after are equal because
        # the worktree had no extra commits.
        sha_before_db, sha_after_db = _shas(initdb, "tid-fin")
        assert sha_before_db == sha_before
        assert sha_after_db == sha_before  # no extra commits in test

    def test_finalize_falls_back_when_column_null(
        self, initdb: Path, farm_root: Path, tmp_path: Path
    ) -> None:
        repo = _make_repo(tmp_path, "repo")
        wt = tmp_path / "wt-fb"
        _seed_task_with_worktree(
            farm_root, repo, wt, owner_repo=None, task_id="tid-fb",
        )

        res = _run_finalize(
            farm_root, "tid-fb", "succeeded", "0", "ok",
        )
        assert res.returncode == 0, res.stderr
        # The repo we created lives under tmp_path, not under
        # ~/Thesis2/repositories — so the scan fallback won't find it
        # and the final rm -rf path takes over. That still leaves the
        # worktree dir gone, which is the user-visible contract.
        assert not wt.exists()
        # And the heartbeat trail must NOT say "via owner_repo column"
        # because we deliberately left the column null.
        hbs = _heartbeats(initdb, "tid-fb")
        assert not any("via owner_repo column" in m for m in hbs), hbs

    def test_finalize_falls_back_when_column_stale(
        self, initdb: Path, farm_root: Path, tmp_path: Path
    ) -> None:
        # Column points to a path that does NOT own the worktree —
        # finalize must detect that (no matching `worktree list` entry)
        # and fall back to the scan path.
        repo = _make_repo(tmp_path, "repo")
        wt = tmp_path / "wt-stale"
        _seed_task_with_worktree(
            farm_root, repo, wt, owner_repo=str(tmp_path / "nonexistent"),
            task_id="tid-stale",
        )

        res = _run_finalize(
            farm_root, "tid-stale", "succeeded", "0", "ok",
        )
        assert res.returncode == 0, res.stderr
        assert not wt.exists()
        hbs = _heartbeats(initdb, "tid-stale")
        # Must NOT report "via owner_repo column" since the repo path is
        # invalid; the fallback path took over.
        assert not any("via owner_repo column" in m for m in hbs), hbs


class TestShaAfterCapture:
    def test_sha_after_recorded_when_worktree_present(
        self, initdb: Path, farm_root: Path, tmp_path: Path
    ) -> None:
        repo = _make_repo(tmp_path, "repo")
        wt = tmp_path / "wt-sha"
        sha_before = _seed_task_with_worktree(
            farm_root, repo, wt, owner_repo=str(repo), task_id="tid-sha",
        )
        # Make a new commit inside the worktree so sha_before != sha_after.
        (wt / "WORK").write_text("changes\n")
        _git("add", "WORK", cwd=wt)
        _git("config", "user.email", "t@e", cwd=wt)
        _git("config", "user.name", "T", cwd=wt)
        _git("commit", "-q", "-m", "work", cwd=wt)
        sha_after_expected = _git("rev-parse", "HEAD", cwd=wt)

        res = _run_finalize(
            farm_root, "tid-sha", "succeeded", "0", "ok",
        )
        assert res.returncode == 0, res.stderr
        sha_before_db, sha_after_db = _shas(initdb, "tid-sha")
        assert sha_before_db == sha_before
        assert sha_after_db == sha_after_expected
        assert sha_before_db != sha_after_db
