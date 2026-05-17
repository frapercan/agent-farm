"""Tests for scripts/lib/db.py set-metrics command (FARM-2.2).

Covers:
- Round-trip: set-metrics stores the JSON into results.metrics_json
- Idempotent on a second call (updates, not duplicates)
- Annotates the latest kind=end event payload with the metrics dict
- Refuses non-JSON / non-object input (exit non-zero)
- Refuses an unknown task_id (exit non-zero)
- Survives a missing results row (creates one)
"""

from __future__ import annotations

import json
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
        check=False, capture_output=True, text=True, env=env,
    )


def _seed_task(farm_root: Path, task_id: str = "t-1") -> None:
    res = _run(
        farm_root,
        "insert-task", task_id, "executor", "subagent", "0",
        "opus-4.7", "{}",
    )
    assert res.returncode == 0, res.stderr


def _results_metrics(db: Path, task_id: str) -> str | None:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT metrics_json FROM results WHERE task_id=?", (task_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def _end_event_payload(db: Path, task_id: str) -> dict | None:
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT payload_json FROM events WHERE task_id=? AND kind='end' "
            "ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or row[0] is None:
        return None
    return json.loads(row[0])


class TestSetMetricsRoundTrip:
    SAMPLE = {
        "input_tokens": 100,
        "output_tokens": 20,
        "cache_tokens": 500,
        "usd_estimate": 0.0123,
        "duration_seconds": 4.2,
        "model": "claude-opus-4-7",
    }

    def test_creates_results_row(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "t-1")
        res = _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        assert res.returncode == 0, res.stderr
        stored = _results_metrics(initdb, "t-1")
        assert stored is not None
        assert json.loads(stored) == self.SAMPLE

    def test_second_call_updates_in_place(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "t-1")
        _run(farm_root, "set-metrics", "t-1", json.dumps({"usd_estimate": 0.01}))
        _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        stored = _results_metrics(initdb, "t-1")
        assert json.loads(stored) == self.SAMPLE
        # Still exactly one row.
        conn = sqlite3.connect(str(initdb))
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM results WHERE task_id=?", ("t-1",)
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 1

    def test_preserves_existing_summary(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "t-1")
        # Simulate finalize-subagent.sh writing the summary FIRST.
        conn = sqlite3.connect(str(initdb))
        try:
            conn.execute(
                "INSERT INTO results(task_id, summary) VALUES(?, ?)",
                ("t-1", "did the thing"),
            )
            conn.commit()
        finally:
            conn.close()
        _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        conn = sqlite3.connect(str(initdb))
        try:
            row = conn.execute(
                "SELECT summary, metrics_json FROM results WHERE task_id=?",
                ("t-1",),
            ).fetchone()
        finally:
            conn.close()
        assert row[0] == "did the thing"
        assert json.loads(row[1]) == self.SAMPLE


class TestEndEventAnnotation:
    SAMPLE = {"usd_estimate": 0.05, "model": "claude-opus-4-7"}

    def test_end_event_payload_carries_metrics(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "t-1")
        _run(farm_root, "set-ended", "t-1", "succeeded", "0", "ok")
        _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        payload = _end_event_payload(initdb, "t-1")
        assert payload is not None
        # set-ended fields still there
        assert payload["status"] == "succeeded"
        assert payload["exit_code"] == 0
        # plus the new metrics
        assert payload["metrics"] == self.SAMPLE

    def test_no_end_event_yet_results_still_written(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _seed_task(farm_root, "t-1")
        # Note: set-ended NOT called yet.
        res = _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        assert res.returncode == 0, res.stderr
        stored = _results_metrics(initdb, "t-1")
        assert json.loads(stored) == self.SAMPLE
        # No spurious kind=end event was inserted.
        conn = sqlite3.connect(str(initdb))
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM events WHERE task_id=? AND kind='end'",
                ("t-1",),
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 0

    def test_annotates_latest_end_event_only(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # Two end events shouldn't both be annotated (only the latest).
        _seed_task(farm_root, "t-1")
        _run(farm_root, "set-ended", "t-1", "failed", "1", "first try")
        _run(farm_root, "set-ended", "t-1", "succeeded", "0", "retry ok")
        _run(farm_root, "set-metrics", "t-1", json.dumps(self.SAMPLE))
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT id, payload_json FROM events "
                "WHERE task_id=? AND kind='end' ORDER BY id",
                ("t-1",),
            ).fetchall()
        finally:
            conn.close()
        assert len(rows) == 2
        first = json.loads(rows[0][1])
        last = json.loads(rows[1][1])
        assert "metrics" not in first
        assert last["metrics"] == self.SAMPLE


class TestRejections:
    def test_unknown_task(self, initdb: Path, farm_root: Path) -> None:
        res = _run(farm_root, "set-metrics", "ghost", '{"usd_estimate": 0.1}')
        assert res.returncode != 0
        assert "unknown task_id" in res.stderr

    def test_invalid_json(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "t-1")
        res = _run(farm_root, "set-metrics", "t-1", "not json{")
        assert res.returncode != 0
        assert "invalid JSON" in res.stderr

    def test_non_object_json(self, initdb: Path, farm_root: Path) -> None:
        _seed_task(farm_root, "t-1")
        res = _run(farm_root, "set-metrics", "t-1", "[1,2,3]")
        assert res.returncode != 0
        assert "JSON object" in res.stderr

    def test_empty_string_is_empty_object(
        self, initdb: Path, farm_root: Path
    ) -> None:
        # Calling with "" → treated as {}; useful for first-pass writes.
        _seed_task(farm_root, "t-1")
        res = _run(farm_root, "set-metrics", "t-1", "")
        assert res.returncode == 0, res.stderr
        stored = _results_metrics(initdb, "t-1")
        assert json.loads(stored) == {}
