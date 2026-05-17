"""Micro-benchmark for FARM-2.3 owner_repo lookup vs the scan fallback.

Constructs 3 fake git repos with 5 worktrees apiece and times the cost
of finding a worktree's owning repo two ways:

1. Scan: walk every repo, run `git worktree list --porcelain`, grep.
   This is the legacy O(repos x worktrees) algorithm finalize-subagent.sh
   used before this slice.
2. Column lookup: a single sqlite SELECT returning the owner repo path
   recorded at spawn time. O(1) in the number of repos / worktrees.

The test asserts the column lookup is strictly faster on this fixture
(it's tens of microseconds vs hundreds of milliseconds — git fork+exec
dominates the scan case). It also prints both timings so a `-s` run
surfaces the speedup in the executor summary.

Not a regression guard for absolute wall-clock — only for ordering.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"


def _git(*args: str, cwd: Path) -> str:
    res = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True,
        capture_output=True, text=True,
    )
    return res.stdout.strip()


def _make_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "README.md").write_text(f"{name}\n")
    _git("add", "README.md", cwd=repo)
    _git("commit", "-q", "-m", "init", cwd=repo)
    return repo


@pytest.fixture()
def fixture(tmp_path: Path) -> dict:
    """3 repos x 5 worktrees + a sqlite with owner_repo populated."""
    # State + schema
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    env = {**os.environ, "AGENT_FARM_ROOT": str(tmp_path)}
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True, env=env,
    )
    db = state / "tasks.sqlite"

    repos: list[Path] = []
    worktrees: list[tuple[str, Path, Path]] = []  # (task_id, worktree, owner_repo)
    for i in range(3):
        r = _make_repo(tmp_path / "repos", f"r{i}")
        repos.append(r)
        for j in range(5):
            wt = tmp_path / "wts" / f"t-{i}-{j}"
            wt.parent.mkdir(parents=True, exist_ok=True)
            _git("worktree", "add", "-q", "-b", f"task/t-{i}-{j}",
                 str(wt), "main", cwd=r)
            task_id = f"t-{i}-{j}"
            subprocess.run(
                [sys.executable, str(DB_PY), "insert-task",
                 task_id, "executor", "subagent", "0", "opus-4.7", "{}"],
                check=True, capture_output=True, env=env,
            )
            subprocess.run(
                [sys.executable, str(DB_PY), "set-started",
                 task_id, str(wt)],
                check=True, capture_output=True, env=env,
            )
            subprocess.run(
                [sys.executable, str(DB_PY), "set-worktree-owner-repo",
                 task_id, str(r)],
                check=True, capture_output=True, env=env,
            )
            worktrees.append((task_id, wt, r))
    return {"repos": repos, "wts": worktrees, "db": db, "root": tmp_path}


def _scan_lookup(repos: list[Path], target: Path) -> Path | None:
    """The legacy algorithm: scan every repo for the target worktree."""
    needle = f"worktree {target}"
    for r in repos:
        res = subprocess.run(
            ["git", "-C", str(r), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
        if needle in res.stdout:
            return r
    return None


def _column_lookup(db: Path, target: Path) -> Path | None:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT worktree_owner_repo FROM tasks WHERE worktree=?",
            (str(target),),
        ).fetchone()
    finally:
        conn.close()
    return Path(row[0]) if row and row[0] else None


def test_column_lookup_is_faster(fixture: dict, capsys) -> None:
    repos: list[Path] = fixture["repos"]
    worktrees = fixture["wts"]
    db: Path = fixture["db"]

    # Warm up: one scan + one query (Python imports, sqlite open).
    _scan_lookup(repos, worktrees[0][1])
    _column_lookup(db, worktrees[0][1])

    # Time the scan path across all 15 worktrees.
    t0 = time.perf_counter()
    for _, wt, expected in worktrees:
        assert _scan_lookup(repos, wt) == expected
    scan_total = time.perf_counter() - t0

    # Time the column path.
    t0 = time.perf_counter()
    for _, wt, expected in worktrees:
        assert _column_lookup(db, wt) == expected
    col_total = time.perf_counter() - t0

    with capsys.disabled():
        print(
            f"\nFARM-2.3 lookup benchmark "
            f"(3 repos x 5 worktrees = 15 lookups):\n"
            f"  scan   O(repos x worktrees): {scan_total*1000:.1f} ms\n"
            f"  column O(1):                 {col_total*1000:.1f} ms\n"
            f"  speedup: {scan_total/max(col_total, 1e-9):.0f}x"
        )

    # Column lookup must beat scan. On any reasonable machine the ratio
    # is >50x; we assert a conservative 5x to avoid CI flakiness on
    # cold-cache containers.
    assert col_total * 5 < scan_total, (
        f"column lookup not faster: scan={scan_total*1000:.2f}ms "
        f"col={col_total*1000:.2f}ms"
    )
