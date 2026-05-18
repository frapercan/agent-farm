"""Tests for FARM-FEAT.2 — declarative ephemeral worktree in spawn.sh.

The slice swaps spawn.sh's deferred ("Future: make worktree creation
declarative via spec.repo") branch for a real `git worktree add` that
mirrors spawn-subagent.sh:73-87. The test checks:

- spawn.sh creates ~/Thesis2/worktrees/<task_id>/ when the agent yaml
  declares worktree.cleanup != none.
- The worktree exists during the run window and is recorded in sqlite
  (status=running, worktree column populated, owner_repo column set).
- The launch prompt (composed_prompt.md) carries WORKTREE / REPO /
  RESULTS_DIR lines so the agent finds the path via the same mechanism
  spawn-subagent.sh uses for kind=subagent.
- finalize-subagent.sh removes the worktree afterwards.
- spawn.sh still works for cleanup=none agents (no worktree created,
  no composed_prompt worktree line).

tmux and claude are stubbed via PATH so the script exits without
spawning a real LLM. We only validate the worktree management
contract, not the LLM dispatch.
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
SPAWN_SH = REPO_ROOT / "scripts" / "spawn.sh"
FINALIZE_SH = REPO_ROOT / "scripts" / "finalize-subagent.sh"
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"


def _git(*args: str, cwd: Path) -> str:
    res = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True,
        capture_output=True, text=True,
    )
    return res.stdout.strip()


def _make_repo(parent: Path, name: str, branch: str = "main") -> Path:
    """Init a tiny git repo with one commit so worktrees can branch off it."""
    repo = parent / name
    repo.mkdir()
    _git("init", "-q", "-b", branch, cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "README.md").write_text("hello\n")
    _git("add", "README.md", cwd=repo)
    _git("commit", "-q", "-m", "init", cwd=repo)
    return repo


def _stub_path(tmp_path: Path) -> Path:
    """PATH dir with no-op tmux and claude stubs."""
    binroot = tmp_path / "stubbin"
    binroot.mkdir()
    for name in ("tmux", "claude"):
        p = binroot / name
        p.write_text("#!/usr/bin/env bash\nexit 0\n")
        p.chmod(0o755)
    return binroot


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """Pretend AGENT_FARM_ROOT mirroring real layout but isolated under tmp."""
    root = tmp_path / "agent-farm"
    (root / "state").mkdir(parents=True)
    (root / "state" / "schema.sql").write_text(SCHEMA_SQL.read_text())
    # Symlink scripts/ so spawn.sh + finalize-subagent.sh load real code.
    (root / "scripts").symlink_to(REPO_ROOT / "scripts")
    (root / "agents").mkdir()
    (root / "prompts").mkdir()
    (root / "results").mkdir()
    return root


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True, env=env,
    )
    return farm_root / "state" / "tasks.sqlite"


def _write_agent_yaml(
    farm_root: Path,
    name: str,
    *,
    repo: str | None,
    base: str = "main",
    cleanup: str,
) -> None:
    body = [
        f"name: {name}",
        "kind: headless",
        "persistent: false",
        "model: haiku-4.5",
        "permissions: bypassPermissions",
        "worktree:",
    ]
    if repo is not None:
        body.append(f"  repo: {repo}")
    body.append(f"  base_branch: {base}")
    body.append(f"  cleanup: {cleanup}")
    body.append("tools_allowed: [Bash, Read, Write]")
    body.append("timeout_hours: 1")
    body.append(f"system_prompt_file: prompts/{name}.md")
    body.append("cost_budget:")
    body.append("  expected_tokens: 1000")
    body.append("  max_usd_per_day: 0.5")
    (farm_root / "agents" / f"{name}.yaml").write_text("\n".join(body) + "\n")
    (farm_root / "prompts" / f"{name}.md").write_text(
        f"# {name}\n\nThis is the launch prompt body.\n"
    )


def _run_spawn(
    farm_root: Path, worktrees_dir: Path, stub_bin: Path,
    agent: str, spec: str = "{}",
) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "AGENT_FARM_ROOT": str(farm_root),
        "AGENT_FARM_WORKTREES": str(worktrees_dir),
        "AGENT_FARM_TMUX_SESSION": "agent-farm-test",
        "PATH": f"{stub_bin}:{os.environ.get('PATH', '')}",
    }
    return subprocess.run(
        ["bash", str(SPAWN_SH), agent, spec],
        env=env, capture_output=True, text=True, check=False,
    )


def _run_finalize(
    farm_root: Path, stub_bin: Path, *args: str,
) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "AGENT_FARM_ROOT": str(farm_root),
        "PATH": f"{stub_bin}:{os.environ.get('PATH', '')}",
    }
    return subprocess.run(
        ["bash", str(FINALIZE_SH), *args],
        env=env, capture_output=True, text=True, check=False,
    )


def _task_row(db: Path, task_id: str) -> tuple[str | None, str | None, str | None]:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT status, worktree, worktree_owner_repo "
            "FROM tasks WHERE id=?", (task_id,),
        ).fetchone()
    finally:
        conn.close()
    return row if row else (None, None, None)


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


class TestDeclarativeWorktreeCreation:
    def test_ephemeral_creates_worktree(
        self,
        initdb: Path,
        farm_root: Path,
        tmp_path: Path,
    ) -> None:
        repo = _make_repo(tmp_path, "repo")
        wt_dir = tmp_path / "worktrees"
        stub = _stub_path(tmp_path)
        _write_agent_yaml(
            farm_root, "embeddings-runner",
            repo=str(repo), base="main", cleanup="ephemeral",
        )

        res = _run_spawn(farm_root, wt_dir, stub, "embeddings-runner")
        assert res.returncode == 0, res.stderr
        task_id = res.stdout.strip().splitlines()[-1]
        assert task_id.startswith("embeddings-runner-"), task_id

        # Worktree directory exists on disk.
        wt_path = wt_dir / task_id
        assert wt_path.is_dir(), f"worktree not created at {wt_path}"
        assert (wt_path / "README.md").exists()

        # The owning repo lists it as a worktree.
        listing = _git("worktree", "list", "--porcelain", cwd=repo)
        assert str(wt_path) in listing

        # sqlite: status=running, worktree column populated, owner_repo
        # column populated (FARM-2.3 plumbing).
        status, db_wt, owner_repo = _task_row(initdb, task_id)
        assert status == "running"
        assert db_wt == str(wt_path)
        assert owner_repo == str(repo)

        # Heartbeat trail mentions the new worktree.
        hbs = _heartbeats(initdb, task_id)
        assert any("worktree created" in m for m in hbs), hbs
        assert not any("creation deferred" in m for m in hbs), hbs

        # composed_prompt.md carries the WORKTREE / REPO context block.
        composed = farm_root / "results" / task_id / "composed_prompt.md"
        assert composed.is_file()
        body = composed.read_text()
        assert f"WORKTREE: `{wt_path}`" in body
        assert f"REPO: `{repo}`" in body
        assert "Spawn context" in body

    def test_finalize_removes_worktree(
        self,
        initdb: Path,
        farm_root: Path,
        tmp_path: Path,
    ) -> None:
        repo = _make_repo(tmp_path, "repo")
        wt_dir = tmp_path / "worktrees"
        stub = _stub_path(tmp_path)
        _write_agent_yaml(
            farm_root, "embeddings-runner",
            repo=str(repo), base="main", cleanup="ephemeral",
        )

        res = _run_spawn(farm_root, wt_dir, stub, "embeddings-runner")
        assert res.returncode == 0, res.stderr
        task_id = res.stdout.strip().splitlines()[-1]
        wt_path = wt_dir / task_id
        assert wt_path.exists()

        fin = _run_finalize(
            farm_root, stub, task_id, "succeeded", "0", "ok",
        )
        assert fin.returncode == 0, fin.stderr
        assert "worktree_removed=1" in fin.stdout, fin.stdout
        assert not wt_path.exists()
        # And the owner_repo lookup path was taken (not the scan fallback).
        hbs = _heartbeats(initdb, task_id)
        assert any("via owner_repo column" in m for m in hbs), hbs

    def test_cleanup_none_skips_worktree(
        self,
        initdb: Path,
        farm_root: Path,
        tmp_path: Path,
    ) -> None:
        wt_dir = tmp_path / "worktrees"
        stub = _stub_path(tmp_path)
        _write_agent_yaml(
            farm_root, "embeddings-runner",
            repo=None, base="main", cleanup="none",
        )

        res = _run_spawn(farm_root, wt_dir, stub, "embeddings-runner")
        assert res.returncode == 0, res.stderr
        task_id = res.stdout.strip().splitlines()[-1]

        # No worktree dir created.
        assert not (wt_dir / task_id).exists()

        # composed_prompt has no WORKTREE / REPO line.
        composed = farm_root / "results" / task_id / "composed_prompt.md"
        assert composed.is_file()
        body = composed.read_text()
        assert "WORKTREE:" not in body
        assert "REPO:" not in body

        # owner_repo column stays null.
        _, _, owner_repo = _task_row(initdb, task_id)
        assert owner_repo in (None, "")

    def test_missing_repo_fails_with_clear_error(
        self,
        initdb: Path,
        farm_root: Path,
        tmp_path: Path,
    ) -> None:
        wt_dir = tmp_path / "worktrees"
        stub = _stub_path(tmp_path)
        _write_agent_yaml(
            farm_root, "embeddings-runner",
            repo=str(tmp_path / "does-not-exist"),
            base="main", cleanup="ephemeral",
        )

        res = _run_spawn(farm_root, wt_dir, stub, "embeddings-runner")
        assert res.returncode != 0
        assert "not a git dir" in res.stderr, res.stderr

    def test_custom_repo_yaml_is_honoured(
        self,
        initdb: Path,
        farm_root: Path,
        tmp_path: Path,
    ) -> None:
        # Two repos: spawn from the lab-like one declared in yaml,
        # NOT the PROTEA default.
        lab = _make_repo(tmp_path, "lab")
        wt_dir = tmp_path / "worktrees"
        stub = _stub_path(tmp_path)
        _write_agent_yaml(
            farm_root, "embeddings-runner",
            repo=str(lab), base="main", cleanup="ephemeral",
        )

        res = _run_spawn(farm_root, wt_dir, stub, "embeddings-runner")
        assert res.returncode == 0, res.stderr
        task_id = res.stdout.strip().splitlines()[-1]
        wt_path = wt_dir / task_id
        # The lab repo registers the worktree, not PROTEA.
        listing = _git("worktree", "list", "--porcelain", cwd=lab)
        assert str(wt_path) in listing
