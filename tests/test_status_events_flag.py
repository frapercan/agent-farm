"""Tests for `status.sh --events` and the events_view.py helper (FARM-2.1).

Covers:
- The bash entrypoint `status.sh --events` runs and produces a table.
- --kind filter restricts results to one event kind.
- --since accepts relative offsets (`1h`, `30m`, `2d`) and ISO timestamps.
- --task filter restricts to one task_id.
- --limit caps the result count.
- parse_since correctly converts relative offsets to ISO strings.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_SH = REPO_ROOT / "scripts" / "status.sh"
EVENTS_VIEW = REPO_ROOT / "scripts" / "lib" / "events_view.py"
SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"

# Make scripts/lib/ importable so we can unit-test parse_since().
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
import events_view  # noqa: E402


def _iso(ts: datetime) -> str:
    """Match the schema default's ISO format: %Y-%m-%dT%H:%M:%fZ (ms+Z)."""
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    return tmp_path


@pytest.fixture()
def populated_db(farm_root: Path) -> Path:
    db = farm_root / "state" / "tasks.sqlite"
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(SCHEMA_SQL.read_text())
        # Seed 3 tasks with varied agents.
        conn.execute(
            "INSERT INTO tasks(id, agent_name, kind, status, created_at) "
            "VALUES('t-old','executor','subagent','succeeded','2026-05-17T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO tasks(id, agent_name, kind, status, created_at) "
            "VALUES('t-recent','janitor','subagent','running','2026-05-17T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO tasks(id, agent_name, kind, status, created_at) "
            "VALUES('t-other','deploy-keeper','headless','running','2026-05-17T00:00:00Z')"
        )

        now = datetime.now(timezone.utc)
        old = now - timedelta(days=2)
        # Old event (2 days ago, kind=spawn)
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-old", _iso(old), "spawn", "info", "old spawn"),
        )
        # Recent events for t-recent
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-recent", _iso(now - timedelta(minutes=5)),
             "spawn", "info", "recent spawn"),
        )
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-recent", _iso(now - timedelta(minutes=4)),
             "heartbeat", "info", "step 1"),
        )
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-recent", _iso(now - timedelta(minutes=3)),
             "heartbeat", "warn", "uh oh"),
        )
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-recent", _iso(now - timedelta(minutes=2)),
             "end", "info", "task ended succeeded"),
        )
        # An event for the other task too.
        conn.execute(
            "INSERT INTO events(task_id, ts, kind, level, message) VALUES(?,?,?,?,?)",
            ("t-other", _iso(now - timedelta(minutes=1)),
             "heartbeat", "info", "deploy tick"),
        )
        conn.commit()
    finally:
        conn.close()
    return db


def _run_status(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    # AGENT_FARM_ROOT must remain pointing at the real repo (status.sh and
    # common.sh live there); only AGENT_FARM_DB is overridden so the script
    # reads from the test fixture instead of the operator's live state.
    env = {
        **os.environ,
        "AGENT_FARM_ROOT": str(REPO_ROOT),
        "AGENT_FARM_DB": str(farm_root / "state" / "tasks.sqlite"),
    }
    return subprocess.run(
        ["bash", str(STATUS_SH), "--events", *args],
        env=env, capture_output=True, text=True, check=False,
    )


class TestParseSince:
    def test_relative_minutes(self) -> None:
        # parse_since returns a string; ensure it's earlier than now.
        s = events_view.parse_since("30m")
        assert s.endswith("Z")
        # And it does represent ~30m ago.
        parsed = datetime.strptime(
            s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        delta = datetime.now(timezone.utc) - parsed
        assert timedelta(minutes=29) < delta < timedelta(minutes=31)

    def test_relative_hours(self) -> None:
        s = events_view.parse_since("2h")
        parsed = datetime.strptime(
            s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        delta = datetime.now(timezone.utc) - parsed
        assert timedelta(hours=1, minutes=59) < delta < timedelta(hours=2, minutes=1)

    def test_relative_days(self) -> None:
        s = events_view.parse_since("1d")
        parsed = datetime.strptime(
            s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        delta = datetime.now(timezone.utc) - parsed
        assert timedelta(hours=23, minutes=59) < delta < timedelta(days=1, minutes=1)

    def test_absolute_passthrough(self) -> None:
        assert events_view.parse_since("2026-05-17T15:00:00Z") == "2026-05-17T15:00:00Z"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            events_view.parse_since("")


class TestStatusEventsCli:
    def test_smoke_runs(self, populated_db: Path, farm_root: Path) -> None:
        res = _run_status(farm_root)
        assert res.returncode == 0, res.stderr
        # Expect header + rows.
        assert "ts" in res.stdout
        assert "task_id" in res.stdout
        # At least one of our seeded task_ids appears.
        assert "t-recent" in res.stdout

    def test_kind_filter_restricts(
        self, populated_db: Path, farm_root: Path
    ) -> None:
        res = _run_status(farm_root, "--kind", "heartbeat", "--since", "1h")
        assert res.returncode == 0, res.stderr
        # Should include heartbeat-level events but not the spawn/end rows.
        lines = [line for line in res.stdout.splitlines()
                 if line and not line.startswith("ts") and not line.startswith("-")]
        # All non-header lines must have kind=heartbeat in the kind column.
        for line in lines:
            # kind column starts at offset 26+30+18+4 ≈ 78; be lenient: just
            # check it doesn't reference spawn/end/cleanup/kill.
            assert " heartbeat " in line + " "

    def test_since_filters_old_events(
        self, populated_db: Path, farm_root: Path
    ) -> None:
        res = _run_status(farm_root, "--since", "1h")
        assert res.returncode == 0, res.stderr
        # The 2-day-old spawn for t-old should NOT appear.
        assert "old spawn" not in res.stdout
        # The recent t-recent events SHOULD appear.
        assert "recent spawn" in res.stdout

    def test_task_filter(self, populated_db: Path, farm_root: Path) -> None:
        res = _run_status(farm_root, "--task", "t-other", "--since", "1h")
        assert res.returncode == 0, res.stderr
        # Only t-other events.
        assert "t-other" in res.stdout
        assert "t-recent" not in res.stdout
        assert "t-old" not in res.stdout

    def test_limit_caps(self, populated_db: Path, farm_root: Path) -> None:
        res = _run_status(farm_root, "--since", "1h", "--limit", "1")
        assert res.returncode == 0, res.stderr
        # Non-header rows: should be 1.
        data_lines = [
            ln for ln in res.stdout.splitlines()
            if ln and not ln.startswith("ts") and not ln.startswith("-")
        ]
        assert len(data_lines) == 1

    def test_combined_filters(
        self, populated_db: Path, farm_root: Path
    ) -> None:
        res = _run_status(
            farm_root,
            "--kind", "heartbeat",
            "--since", "1h",
            "--task", "t-recent",
        )
        assert res.returncode == 0, res.stderr
        assert "step 1" in res.stdout or "uh oh" in res.stdout
        assert "deploy tick" not in res.stdout  # different task
        assert "recent spawn" not in res.stdout  # different kind

    def test_invalid_kind_rejected(
        self, populated_db: Path, farm_root: Path
    ) -> None:
        res = _run_status(farm_root, "--kind", "bogus")
        assert res.returncode != 0

    def test_missing_db_fails(self, farm_root: Path) -> None:
        # No populated_db fixture this time. The DB simply doesn't exist.
        res = _run_status(farm_root)
        assert res.returncode == 2
        assert "database not found" in res.stderr
