"""Tests for scripts/lib/cost_report.py + scripts/cost-report.sh (FARM-2.2).

Seeds a fixture DB with a handful of tasks + metrics_json rows, then
exercises both the Python aggregator (direct import) and the bash wrapper
(subprocess + AGENT_FARM_DB override).

Coverage:
- Aggregation groups by (date, agent, model)
- USD sums correctly across rows
- --agent / --model filters narrow the result set
- --days bound excludes tasks outside the window
- --json output is parseable and stable-sorted
- Empty DB / no matching tasks -> empty / "no cost data" message
- Tasks without metrics_json are silently skipped (historical tasks)
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import cost_report as cr  # noqa: E402

SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
COST_SH = REPO_ROOT / "scripts" / "cost-report.sh"


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


def _seed_task(
    db: Path,
    task_id: str,
    agent: str,
    metrics: dict | None,
    ended_at: str,
    status: str = "succeeded",
) -> None:
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            """INSERT INTO tasks(id, agent_name, kind, persistent, status,
                                 spawn_args, model, created_at, ended_at)
               VALUES(?, ?, 'subagent', 0, ?, '{}', ?, ?, ?)""",
            (task_id, agent, status, (metrics or {}).get("model"), ended_at, ended_at),
        )
        if metrics is not None:
            conn.execute(
                "INSERT INTO results(task_id, metrics_json) VALUES(?, ?)",
                (task_id, json.dumps(metrics, sort_keys=True)),
            )
        conn.commit()
    finally:
        conn.close()


def _today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _days_ago_iso(n: int) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(days=n)
    ).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Python aggregator
# ---------------------------------------------------------------------------


class TestAggregator:
    def _seed_three(self, db: Path) -> None:
        today = _today_iso()
        _seed_task(db, "t-opus-1", "executor", {
            "input_tokens": 100, "output_tokens": 50, "cache_tokens": 1000,
            "usd_estimate": 0.10, "model": "claude-opus-4-7",
        }, today)
        _seed_task(db, "t-opus-2", "executor", {
            "input_tokens": 200, "output_tokens": 100, "cache_tokens": 2000,
            "usd_estimate": 0.20, "model": "claude-opus-4-7",
        }, today)
        _seed_task(db, "t-haiku", "janitor", {
            "input_tokens": 50, "output_tokens": 25, "cache_tokens": 500,
            "usd_estimate": 0.01, "model": "claude-haiku-4-5",
        }, today)

    def test_groups_and_sums(self, initdb: Path) -> None:
        self._seed_three(initdb)
        rows = cr._load(initdb, _days_ago_iso(1))
        buckets = cr.aggregate(rows)
        # 2 buckets: (executor, opus) and (janitor, haiku) on today.
        assert len(buckets) == 2
        opus = next(b for b in buckets if b["agent"] == "executor")
        assert opus["tasks"] == 2
        assert opus["input_tokens"] == 300
        assert opus["output_tokens"] == 150
        assert opus["cache_tokens"] == 3000
        assert opus["usd"] == pytest.approx(0.30)

        haiku = next(b for b in buckets if b["agent"] == "janitor")
        assert haiku["tasks"] == 1
        assert haiku["usd"] == pytest.approx(0.01)

    def test_agent_filter(self, initdb: Path) -> None:
        self._seed_three(initdb)
        rows = cr._load(initdb, _days_ago_iso(1))
        buckets = cr.aggregate(rows, agent_filter="executor")
        assert len(buckets) == 1
        assert buckets[0]["agent"] == "executor"

    def test_model_filter(self, initdb: Path) -> None:
        self._seed_three(initdb)
        rows = cr._load(initdb, _days_ago_iso(1))
        buckets = cr.aggregate(rows, model_filter="claude-haiku-4-5")
        assert len(buckets) == 1
        assert buckets[0]["model"] == "claude-haiku-4-5"
        assert buckets[0]["tasks"] == 1

    def test_days_cutoff(self, initdb: Path) -> None:
        today = _today_iso()
        long_ago = _days_ago_iso(30)
        _seed_task(initdb, "t-recent", "executor", {
            "usd_estimate": 0.10, "model": "claude-opus-4-7",
        }, today)
        _seed_task(initdb, "t-old", "executor", {
            "usd_estimate": 99.0, "model": "claude-opus-4-7",
        }, long_ago)
        rows = cr._load(initdb, _days_ago_iso(7))
        buckets = cr.aggregate(rows)
        # 30-day-old task is outside the 7d window.
        assert len(buckets) == 1
        assert buckets[0]["usd"] == pytest.approx(0.10)

    def test_unknown_model_bucket(self, initdb: Path) -> None:
        today = _today_iso()
        _seed_task(initdb, "t-no-model", "executor", {
            "usd_estimate": 0.05,
            # no model key
        }, today)
        rows = cr._load(initdb, _days_ago_iso(1))
        buckets = cr.aggregate(rows)
        assert buckets[0]["model"] == "(unknown)"

    def test_skips_tasks_without_metrics(self, initdb: Path) -> None:
        today = _today_iso()
        _seed_task(initdb, "t-naked", "executor", None, today)
        rows = cr._load(initdb, _days_ago_iso(1))
        buckets = cr.aggregate(rows)
        assert buckets == []


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


class TestRender:
    SAMPLE = [
        {
            "date": "2026-05-17", "agent": "executor",
            "model": "claude-opus-4-7",
            "tasks": 2, "input_tokens": 300, "output_tokens": 150,
            "cache_tokens": 3000, "usd": 0.30,
        },
        {
            "date": "2026-05-17", "agent": "janitor",
            "model": "claude-haiku-4-5",
            "tasks": 1, "input_tokens": 50, "output_tokens": 25,
            "cache_tokens": 500, "usd": 0.01,
        },
    ]

    def test_table_sorts_by_usd_desc(self) -> None:
        out = cr.render_table(self.SAMPLE)
        lines = out.splitlines()
        # Header + separator on top.
        assert lines[0].startswith("date")
        # First data row is the more expensive bucket (executor / opus).
        assert "executor" in lines[2]
        assert "janitor" in lines[3]
        # Footer total.
        assert "$0.3100" in lines[-1]

    def test_table_empty(self) -> None:
        out = cr.render_table([])
        assert "no cost data" in out

    def test_json_stable_sort(self) -> None:
        out = cr.render_json(self.SAMPLE)
        parsed = json.loads(out)
        # JSON view sorts by (date, agent, model) ascending, so executor
        # (e < j) comes first.
        assert parsed[0]["agent"] == "executor"
        assert parsed[1]["agent"] == "janitor"


# ---------------------------------------------------------------------------
# Bash wrapper
# ---------------------------------------------------------------------------


class TestBashWrapper:
    def _run(self, farm_root: Path, *args: str) -> subprocess.CompletedProcess:
        # The bash wrapper sources $AGENT_FARM_ROOT/scripts/lib/common.sh,
        # so we point ROOT at the real repo and override the DB path with
        # AGENT_FARM_DB (honoured by cost_report.py).
        env = {
            **os.environ,
            "AGENT_FARM_ROOT": str(REPO_ROOT),
            "AGENT_FARM_DB": str(farm_root / "state" / "tasks.sqlite"),
        }
        return subprocess.run(
            ["bash", str(COST_SH), *args],
            check=False, capture_output=True, text=True, env=env,
        )

    def test_default_human(self, initdb: Path, farm_root: Path) -> None:
        today = _today_iso()
        _seed_task(initdb, "t-1", "executor", {
            "usd_estimate": 0.12, "model": "claude-opus-4-7",
            "input_tokens": 10, "output_tokens": 5, "cache_tokens": 100,
        }, today)
        res = self._run(farm_root)
        assert res.returncode == 0, res.stderr
        assert "executor" in res.stdout
        assert "$0.1200" in res.stdout
        assert "claude-opus-4-7" in res.stdout

    def test_json_flag(self, initdb: Path, farm_root: Path) -> None:
        today = _today_iso()
        _seed_task(initdb, "t-1", "executor", {
            "usd_estimate": 0.12, "model": "claude-opus-4-7",
        }, today)
        res = self._run(farm_root, "--json")
        assert res.returncode == 0, res.stderr
        parsed = json.loads(res.stdout)
        assert isinstance(parsed, list)
        assert parsed[0]["agent"] == "executor"
        assert parsed[0]["usd"] == pytest.approx(0.12)

    def test_agent_filter(self, initdb: Path, farm_root: Path) -> None:
        today = _today_iso()
        _seed_task(initdb, "t-1", "executor", {
            "usd_estimate": 0.10, "model": "claude-opus-4-7",
        }, today)
        _seed_task(initdb, "t-2", "janitor", {
            "usd_estimate": 0.01, "model": "claude-haiku-4-5",
        }, today)
        res = self._run(farm_root, "--agent", "executor", "--json")
        assert res.returncode == 0, res.stderr
        parsed = json.loads(res.stdout)
        assert len(parsed) == 1
        assert parsed[0]["agent"] == "executor"

    def test_empty_db(self, initdb: Path, farm_root: Path) -> None:
        res = self._run(farm_root)
        assert res.returncode == 0, res.stderr
        assert "no cost data" in res.stdout
