"""Fixtures for farm-api tests.

Each test gets a fresh tmp_path-rooted agent-farm tree:
  <tmp>/state/schema.sql              copied from repo
  <tmp>/state/tasks.sqlite            initialised via the real db.py
  <tmp>/plans/farm-platform/PLAN.md   small fixture plan
  <tmp>/worktrees/                    empty or seeded by individual tests
  <tmp>/scripts/lib/cost_report.py    copied so /cost imports it

The fixture seeds enough rows for the assertions of every endpoint
test: 3 tasks (1 running / 1 succeeded / 1 failed), heartbeats on the
running task, a results row + metrics on the succeeded task, and
matching events for each.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Repo layout: this file lives at apps/farm-api/tests/conftest.py
TESTS_DIR = Path(__file__).resolve().parent
APP_ROOT = TESTS_DIR.parent
REPO_ROOT = APP_ROOT.parent.parent

sys.path.insert(0, str(APP_ROOT))

SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"
COST_REPORT = REPO_ROOT / "scripts" / "lib" / "cost_report.py"
PLAN_PARSER = REPO_ROOT / "scripts" / "lib" / "plan_parser.py"


def _iso(dt: datetime) -> str:
    return dt.astimezone().isoformat(timespec="seconds")


@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """Build a minimal agent-farm tree under tmp_path and return the root."""
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())

    # Initialise the sqlite DB through the real db.py so the schema
    # matches what production farm-api will see in the field.
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True,
        env={**os.environ, "AGENT_FARM_ROOT": str(tmp_path)},
    )

    # Copy cost_report.py + plan_parser.py into the tmp tree so the
    # API's importlib lookup finds them at <root>/scripts/lib/.
    scripts_lib = tmp_path / "scripts" / "lib"
    scripts_lib.mkdir(parents=True)
    shutil.copyfile(COST_REPORT, scripts_lib / "cost_report.py")
    if PLAN_PARSER.is_file():
        shutil.copyfile(PLAN_PARSER, scripts_lib / "plan_parser.py")

    # Plans directory with a couple of fixture slices.
    plans = tmp_path / "plans" / "farm-platform"
    plans.mkdir(parents=True)
    (plans / "PLAN.md").write_text(
        "# farm-platform — Plan\n\n"
        "## F-UI — UI slices\n\n"
        "### FARM-UI.1 — farm-api sidecar\n"
        "```yaml\n"
        "id: FARM-UI.1\n"
        "phase: F-UI\n"
        "loop: farm-platform\n"
        "status: done\n"
        "deps: [FARM-2.1, FARM-2.2]\n"
        "priority: P1\n"
        "estimated_hours: 10\n"
        "tags: [ui, api]\n"
        "requires_human: false\n"
        "acceptance: |-\n"
        "  apps/farm-api/ FastAPI service\n"
        "```\n\n"
        "Body text.\n\n"
        "### FARM-UI.2 — frontend\n"
        "```yaml\n"
        "id: FARM-UI.2\n"
        "phase: F-UI\n"
        "loop: farm-platform\n"
        "status: pending\n"
        "deps: [FARM-UI.1]\n"
        "priority: P1\n"
        "estimated_hours: 8\n"
        "tags: [ui, frontend]\n"
        "requires_human: false\n"
        "```\n\n"
        "Body text.\n"
    )

    # Worktrees directory (empty by default; some tests will seed).
    (tmp_path / "worktrees").mkdir()

    return tmp_path


@pytest.fixture()
def seeded_db(farm_root: Path) -> Path:
    """Populate tasks.sqlite with deterministic rows."""
    db = farm_root / "state" / "tasks.sqlite"
    now = datetime.now(timezone.utc)
    rows_tasks = [
        # id, agent, kind, status, model, created_at, started_at, ended_at, exit_code
        ("exec-001", "executor", "subagent", "running", "opus-4.7",
         _iso(now - timedelta(minutes=10)), _iso(now - timedelta(minutes=9)), None, None),
        ("exec-002", "executor", "subagent", "succeeded", "opus-4.7",
         _iso(now - timedelta(hours=2)), _iso(now - timedelta(hours=2)),
         _iso(now - timedelta(hours=1, minutes=30)), 0),
        ("janitor-003", "janitor", "subagent", "failed", "haiku-4.5",
         _iso(now - timedelta(days=2)), _iso(now - timedelta(days=2)),
         _iso(now - timedelta(days=2)), 1),
    ]
    conn = sqlite3.connect(str(db))
    try:
        for row in rows_tasks:
            conn.execute(
                """INSERT INTO tasks(id, agent_name, kind, persistent, status,
                                     spawn_args, model, created_at, started_at,
                                     ended_at, exit_code)
                   VALUES(?, ?, ?, 0, ?, '{}', ?, ?, ?, ?, ?)""",
                row,
            )
        # Heartbeats on the running task.
        for i in range(3):
            conn.execute(
                "INSERT INTO heartbeats(task_id, ts, level, message) VALUES(?,?,?,?)",
                ("exec-001",
                 _iso(now - timedelta(minutes=9 - i)),
                 "info",
                 f"step {i}"),
            )
        # Heartbeat on the failed one (an error message).
        conn.execute(
            "INSERT INTO heartbeats(task_id, ts, level, message) VALUES(?,?,?,?)",
            ("janitor-003",
             _iso(now - timedelta(days=2)),
             "error",
             "boom"),
        )
        # Results + metrics for the succeeded task.
        conn.execute(
            "INSERT INTO results(task_id, summary, metrics_json) VALUES(?,?,?)",
            ("exec-002", "ok",
             json.dumps({
                 "model": "opus-4.7",
                 "input_tokens": 1000,
                 "output_tokens": 500,
                 "cache_tokens": 0,
                 "usd_estimate": 0.0125,
             }, sort_keys=True)),
        )
        # A few events covering each kind we expose.
        events = [
            ("exec-001", _iso(now - timedelta(minutes=10)), "spawn", "info", "spawned exec"),
            ("exec-001", _iso(now - timedelta(minutes=9)), "start", "info", "started"),
            ("exec-001", _iso(now - timedelta(minutes=8)), "heartbeat", "info", "step 0"),
            ("exec-002", _iso(now - timedelta(hours=1, minutes=30)), "end", "info", "task ended"),
            ("janitor-003", _iso(now - timedelta(days=2)), "end", "warn", "failed"),
        ]
        for ev in events:
            conn.execute(
                """INSERT INTO events(task_id, ts, kind, level, message)
                   VALUES(?, ?, ?, ?, ?)""",
                ev,
            )
        conn.commit()
    finally:
        conn.close()
    return db


@pytest.fixture()
def settings_env(farm_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Wire env vars so create_app() reads from the temp farm tree."""
    monkeypatch.setenv("AGENT_FARM_ROOT", str(farm_root))
    monkeypatch.setenv("FARM_API_DB", str(farm_root / "state" / "tasks.sqlite"))
    monkeypatch.setenv("FARM_API_WORKTREES", str(farm_root / "worktrees"))
    monkeypatch.setenv("FARM_API_PLANS", str(farm_root / "plans"))
    monkeypatch.delenv("FARM_API_WRITE", raising=False)
    monkeypatch.delenv("FARM_API_AUTH_TOKEN", raising=False)
    return farm_root


@pytest.fixture()
def client(settings_env: Path, seeded_db: Path) -> TestClient:
    # Late import so env is set first.
    from farm_api.app import create_app  # noqa: PLC0415

    # Reset the /worktrees in-process cache so tests do not see leftover
    # data from sibling tests.
    from farm_api.routes import worktrees as worktrees_route  # noqa: PLC0415
    worktrees_route._clear_cache_for_tests()

    return TestClient(create_app())


@pytest.fixture()
def write_client(
    settings_env: Path,
    seeded_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setenv("FARM_API_WRITE", "1")
    monkeypatch.setenv("FARM_API_AUTH_TOKEN", "test-token-abc")
    from farm_api.app import create_app  # noqa: PLC0415
    return TestClient(create_app())
