"""Integration test for finalize-subagent.sh's FARM-2.2 metrics-capture
wiring.

Exercises three input modes:
1. --metrics-json (pre-parsed JSON object on the CLI)
2. --metrics-file (stream.jsonl path; we feed a stream-json fixture)
3. Default capture (results/<task_id>/stream.jsonl autodiscovered)

We don't drive the worktree-removal path here because that requires a
real git worktree; we just bypass it by NOT setting up an agent yaml +
worktree, which makes finalize emit `skip_reason`. The metrics-writing
code path runs unconditionally on the way out, which is what matters.
"""

from __future__ import annotations

import json
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
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "parse_claude_cost"


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """A self-contained AGENT_FARM_ROOT layout: state/, agents/, scripts/.
    scripts/ symlinks to the real repo so finalize-subagent.sh + its
    helpers resolve.
    """
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    # Symlink the scripts and results paths so all helper resolution works.
    (tmp_path / "scripts").symlink_to(REPO_ROOT / "scripts")
    (tmp_path / "agents").mkdir()
    # Minimal yaml for an executor: cleanup=ephemeral, no path.
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


def _seed_task(farm_root: Path, task_id: str = "tid-fin") -> None:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY),
         "insert-task", task_id, "executor", "subagent", "0",
         "opus-4.7", "{}"],
        check=True, capture_output=True, env=env,
    )
    # set-started so the row has a worktree-less running state
    subprocess.run(
        [sys.executable, str(DB_PY), "set-started", task_id],
        check=True, capture_output=True, env=env,
    )


def _run_finalize(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    return subprocess.run(
        ["bash", str(FINALIZE_SH), *args],
        check=False, capture_output=True, text=True, env=env,
    )


def _read_metrics(db: Path, task_id: str) -> dict | None:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT metrics_json FROM results WHERE task_id=?", (task_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None or row[0] is None:
        return None
    return json.loads(row[0])


class TestMetricsCapture:
    def test_metrics_json_flag(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "tid-1")
        payload = {"usd_estimate": 0.05, "model": "claude-opus-4-7",
                   "input_tokens": 10, "output_tokens": 5, "cache_tokens": 100}
        res = _run_finalize(
            farm_root,
            "tid-1", "succeeded", "0", "ok",
            "--metrics-json", json.dumps(payload),
        )
        assert res.returncode == 0, (res.stdout, res.stderr)
        assert "metrics=" in res.stdout
        assert _read_metrics(initdb, "tid-1") == payload
        # results/<task_id>/metrics.json mirror
        mirror = farm_root / "results" / "tid-1" / "metrics.json"
        assert mirror.is_file()
        assert json.loads(mirror.read_text()) == payload

    def test_metrics_file_flag(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "tid-2")
        # Copy the real stream-json fixture in
        src = FIXTURES / "stream_json_minimal.jsonl"
        local = farm_root / "stream.jsonl"
        shutil.copy(src, local)
        res = _run_finalize(
            farm_root,
            "tid-2", "succeeded", "0", "ok",
            "--metrics-file", str(local),
        )
        assert res.returncode == 0, (res.stdout, res.stderr)
        metrics = _read_metrics(initdb, "tid-2")
        assert metrics is not None
        assert metrics["model"] == "claude-opus-4-7"
        assert metrics["usd_estimate"] == 0.05

    def test_default_capture_path(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "tid-3")
        # finalize will auto-discover results/<task_id>/stream.jsonl
        results = farm_root / "results" / "tid-3"
        results.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURES / "stream_json_minimal.jsonl",
                    results / "stream.jsonl")
        res = _run_finalize(farm_root, "tid-3", "succeeded", "0", "ok")
        assert res.returncode == 0, (res.stdout, res.stderr)
        metrics = _read_metrics(initdb, "tid-3")
        assert metrics is not None
        assert metrics["usd_estimate"] == 0.05

    def test_no_metrics_source_is_fine(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "tid-4")
        res = _run_finalize(farm_root, "tid-4", "succeeded", "0", "ok")
        assert res.returncode == 0, (res.stdout, res.stderr)
        # No metrics row written.
        assert _read_metrics(initdb, "tid-4") is None
        # The end event was still emitted by set-ended.
        conn = sqlite3.connect(str(initdb))
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM events WHERE task_id=? AND kind='end'",
                ("tid-4",),
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 1

    def test_garbage_metrics_file_is_silent(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "tid-5")
        local = farm_root / "junk.txt"
        local.write_text("not claude output at all\n")
        res = _run_finalize(
            farm_root,
            "tid-5", "succeeded", "0", "ok",
            "--metrics-file", str(local),
        )
        # Parser returns {} for garbage -> we skip set-metrics; never crash.
        assert res.returncode == 0, (res.stdout, res.stderr)
        assert _read_metrics(initdb, "tid-5") is None
