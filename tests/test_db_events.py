"""Tests for scripts/lib/db.py event-emission hooks (FARM-2.1).

Each lifecycle entrypoint that mutates the tasks table must append a row
to the events table inside the same transaction:

  insert-task    -> kind=spawn (payload mirrors spawn_args)
  set-started    -> kind=start
  set-ended      -> kind=end   (payload includes status, exit_code, summary[:200])
  heartbeat      -> kind=heartbeat
  mark-killed    -> kind=kill
  mark-crashed   -> kind=cleanup

The tests run db.py as a subprocess against a tmp database so the wiring
through the CLI (which is how bash callers invoke it) is exercised
end-to-end.
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
    """A tmpdir laid out like AGENT_FARM_ROOT (state/schema.sql + empty
    state/tasks.sqlite), with db.py copied so it operates on the tmp DB.
    """
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    return tmp_path


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    """Initialised tmp DB at farm_root/state/tasks.sqlite."""
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


def _events(db: Path, task_id: str | None = None) -> list[dict]:
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        if task_id:
            rows = conn.execute(
                "SELECT * FROM events WHERE task_id=? ORDER BY id", (task_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM events ORDER BY id").fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


class TestInsertTaskEmitsSpawn:
    def test_spawn_event_recorded(self, initdb: Path, farm_root: Path) -> None:
        res = _run(
            farm_root,
            "insert-task", "tid-1", "executor", "subagent", "0",
            "opus-4.7", '{"task": "FARM-2.1"}',
        )
        assert res.returncode == 0, res.stderr
        evs = _events(initdb, "tid-1")
        assert len(evs) == 1
        assert evs[0]["kind"] == "spawn"
        assert evs[0]["level"] == "info"
        payload = json.loads(evs[0]["payload_json"])
        assert payload["agent"] == "executor"
        assert payload["kind"] == "subagent"
        assert payload["model"] == "opus-4.7"
        assert payload["spawn_args"] == {"task": "FARM-2.1"}

    def test_malformed_args_tolerated(self, initdb: Path, farm_root: Path) -> None:
        # If spawn_args isn't valid JSON we still record the event with
        # the raw string under payload.spawn_args.
        res = _run(
            farm_root,
            "insert-task", "tid-bad", "executor", "subagent", "0",
            "opus-4.7", "not-json",
        )
        assert res.returncode == 0
        evs = _events(initdb, "tid-bad")
        payload = json.loads(evs[0]["payload_json"])
        assert payload["spawn_args"] == "not-json"


class TestStartedEmitsStart:
    def test_set_started_records_start_event(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t2", "executor", "subagent",
             "0", "opus-4.7", "{}")
        res = _run(farm_root, "set-started", "t2", "/tmp/wt", "agent-farm:t2", "1234")
        assert res.returncode == 0, res.stderr
        evs = _events(initdb, "t2")
        kinds = [e["kind"] for e in evs]
        assert kinds == ["spawn", "start"]
        start = evs[1]
        payload = json.loads(start["payload_json"])
        assert payload["worktree"] == "/tmp/wt"
        assert payload["tmux_window"] == "agent-farm:t2"
        assert payload["pid"] == 1234


class TestEndedEmitsEnd:
    def test_set_ended_records_end_event_with_summary(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t3", "executor", "subagent",
             "0", "opus-4.7", "{}")
        long_summary = "A" * 500
        res = _run(farm_root, "set-ended", "t3", "succeeded", "0", long_summary)
        assert res.returncode == 0, res.stderr
        evs = _events(initdb, "t3")
        end = [e for e in evs if e["kind"] == "end"]
        assert len(end) == 1
        payload = json.loads(end[0]["payload_json"])
        assert payload["status"] == "succeeded"
        assert payload["exit_code"] == 0
        assert payload["summary"] == "A" * 200  # truncated

    def test_set_ended_failed_uses_warn_level(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t-fail", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "set-ended", "t-fail", "failed", "1")
        evs = _events(initdb, "t-fail")
        end = [e for e in evs if e["kind"] == "end"][0]
        assert end["level"] == "warn"

    def test_set_ended_succeeded_uses_info_level(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t-ok", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "set-ended", "t-ok", "succeeded", "0")
        evs = _events(initdb, "t-ok")
        end = [e for e in evs if e["kind"] == "end"][0]
        assert end["level"] == "info"


class TestHeartbeatEmitsHeartbeat:
    def test_heartbeat_records_event_and_heartbeats_row(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t-hb", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "heartbeat", "t-hb", "warn", "something is off")
        evs = _events(initdb, "t-hb")
        hb_evs = [e for e in evs if e["kind"] == "heartbeat"]
        assert len(hb_evs) == 1
        assert hb_evs[0]["level"] == "warn"
        assert hb_evs[0]["message"] == "something is off"
        # And the original heartbeats table also got a row (we mirror, not replace).
        conn = sqlite3.connect(str(initdb))
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM heartbeats WHERE task_id='t-hb'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 1


class TestMarkKilledEmitsKill:
    def test_mark_killed_records_event(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t-kill", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "mark-killed", "t-kill", "user pressed ctrl-c")
        evs = _events(initdb, "t-kill")
        kill = [e for e in evs if e["kind"] == "kill"]
        assert len(kill) == 1
        assert kill[0]["level"] == "warn"
        assert kill[0]["message"] == "user pressed ctrl-c"
        payload = json.loads(kill[0]["payload_json"])
        assert payload["reason"] == "user pressed ctrl-c"


class TestMarkCrashedEmitsCleanup:
    def test_mark_crashed_records_cleanup_event(
        self, initdb: Path, farm_root: Path
    ) -> None:
        _run(farm_root, "insert-task", "t-crash", "executor", "subagent",
             "0", "opus-4.7", "{}")
        _run(farm_root, "mark-crashed", "t-crash", "tmux window vanished")
        evs = _events(initdb, "t-crash")
        cl = [e for e in evs if e["kind"] == "cleanup"]
        assert len(cl) == 1
        assert cl[0]["level"] == "warn"
        payload = json.loads(cl[0]["payload_json"])
        assert payload["reason"] == "tmux window vanished"


class TestAtomicity:
    def test_spawn_event_and_task_committed_together(
        self, initdb: Path, farm_root: Path
    ) -> None:
        """If anything would split the insert from the event row, this
        invariant breaks first.
        """
        _run(farm_root, "insert-task", "t-atom", "executor", "subagent",
             "0", "opus-4.7", "{}")
        conn = sqlite3.connect(str(initdb))
        try:
            task_count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE id='t-atom'"
            ).fetchone()[0]
            evt_count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE task_id='t-atom' AND kind='spawn'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert task_count == 1
        assert evt_count == 1
