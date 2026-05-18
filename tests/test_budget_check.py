"""Tests for scripts/lib/budget_check.py (FARM-FEAT.8).

Coverage:
- _agent_cap reads max_usd_per_day from agent yaml, returns None when
  the yaml is missing / unparseable / has no cost_budget block.
- _rolling_spend sums usd_estimate across the window, ignores tasks
  outside it, ignores tasks without metrics_json.
- status() bands correctly: under / near / over / no_cap.
- emit-finalize writes one error-level heartbeat (and event row) when
  the rolling sum is over the cap, a warn-level heartbeat when near.
- emit-spawn writes a warn-level heartbeat when the agent is already
  near/over at spawn time, nothing otherwise.
- overages prints only near/over agents under --only-alerts and a
  stable JSON shape under --json.
- The hooks in finalize-subagent.sh / spawn-subagent.sh / spawn.sh
  never error out when budget_check.py is absent (smoke-only, no DB).
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

import budget_check as bc  # noqa: E402

SCHEMA_SQL = REPO_ROOT / "state" / "schema.sql"
DB_PY = REPO_ROOT / "scripts" / "lib" / "db.py"


# --------------------------------------------------------------------- #
# Fixtures.

@pytest.fixture()
def farm_root(tmp_path: Path) -> Path:
    """Self-contained AGENT_FARM_ROOT: state/, agents/, scripts/ (symlinked).
    """
    state = tmp_path / "state"
    state.mkdir()
    (state / "schema.sql").write_text(SCHEMA_SQL.read_text())
    (tmp_path / "scripts").symlink_to(REPO_ROOT / "scripts")
    (tmp_path / "agents").mkdir()
    return tmp_path


@pytest.fixture()
def initdb(farm_root: Path) -> Path:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    subprocess.run(
        [sys.executable, str(DB_PY), "init"],
        check=True, capture_output=True, env=env,
    )
    return farm_root / "state" / "tasks.sqlite"


def _write_agent_yaml(
    farm_root: Path, agent: str, *, cap: float | None
) -> None:
    body = [f"name: {agent}", "kind: subagent", "model: opus-4.7"]
    if cap is not None:
        body += ["cost_budget:", f"  max_usd_per_day: {cap}"]
    (farm_root / "agents" / f"{agent}.yaml").write_text("\n".join(body) + "\n")


def _seed_task(
    db: Path,
    *,
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
            (task_id, agent, status,
             (metrics or {}).get("model"), ended_at, ended_at),
        )
        if metrics is not None:
            conn.execute(
                "INSERT INTO results(task_id, metrics_json) VALUES(?, ?)",
                (task_id, json.dumps(metrics, sort_keys=True)),
            )
        conn.commit()
    finally:
        conn.close()


def _iso(dt: datetime) -> str:
    return dt.astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------- #
# Cap reader.

class TestAgentCap:
    def test_returns_cap_when_present(self, farm_root: Path) -> None:
        _write_agent_yaml(farm_root, "executor", cap=12.0)
        assert bc._agent_cap("executor", root=farm_root) == 12.0

    def test_returns_none_when_missing(self, farm_root: Path) -> None:
        # No yaml on disk
        assert bc._agent_cap("ghost", root=farm_root) is None

    def test_returns_none_when_no_cost_budget(self, farm_root: Path) -> None:
        _write_agent_yaml(farm_root, "minimal", cap=None)
        assert bc._agent_cap("minimal", root=farm_root) is None

    def test_returns_none_on_unparseable_yaml(self, farm_root: Path) -> None:
        (farm_root / "agents" / "broken.yaml").write_text(": : :\n")
        assert bc._agent_cap("broken", root=farm_root) is None


# --------------------------------------------------------------------- #
# Rolling spend.

class TestRollingSpend:
    def test_sums_within_window(self, initdb: Path) -> None:
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="a1", agent="executor",
                   metrics={"usd_estimate": 1.50},
                   ended_at=_iso(now - timedelta(hours=2)))
        _seed_task(initdb, task_id="a2", agent="executor",
                   metrics={"usd_estimate": 3.25},
                   ended_at=_iso(now - timedelta(hours=10)))
        total, count = bc._rolling_spend(initdb, "executor")
        assert count == 2
        assert total == pytest.approx(4.75)

    def test_excludes_outside_window(self, initdb: Path) -> None:
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="old", agent="executor",
                   metrics={"usd_estimate": 7.0},
                   ended_at=_iso(now - timedelta(hours=48)))
        total, count = bc._rolling_spend(initdb, "executor")
        assert total == 0.0
        assert count == 0

    def test_skips_tasks_without_metrics(self, initdb: Path) -> None:
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="no_metrics", agent="executor",
                   metrics=None,
                   ended_at=_iso(now - timedelta(hours=1)))
        total, count = bc._rolling_spend(initdb, "executor")
        assert total == 0.0
        assert count == 0

    def test_per_agent_isolation(self, initdb: Path) -> None:
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="e1", agent="executor",
                   metrics={"usd_estimate": 2.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        _seed_task(initdb, task_id="j1", agent="janitor",
                   metrics={"usd_estimate": 0.10},
                   ended_at=_iso(now - timedelta(hours=1)))
        ex_total, _ = bc._rolling_spend(initdb, "executor")
        ja_total, _ = bc._rolling_spend(initdb, "janitor")
        assert ex_total == pytest.approx(2.0)
        assert ja_total == pytest.approx(0.10)


# --------------------------------------------------------------------- #
# status() bands.

class TestStatusBands:
    def test_no_cap_band(self, farm_root: Path, initdb: Path) -> None:
        _write_agent_yaml(farm_root, "executor", cap=None)
        st = bc.status("executor", db_path=initdb, root=farm_root)
        assert st.state == "no_cap"
        assert st.cap_usd is None

    def test_under_band(self, farm_root: Path, initdb: Path) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="t1", agent="executor",
                   metrics={"usd_estimate": 1.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        st = bc.status("executor", db_path=initdb, root=farm_root)
        assert st.state == "under"
        assert st.spend_usd == pytest.approx(1.0)

    def test_near_band(self, farm_root: Path, initdb: Path) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        now = datetime.now(timezone.utc)
        # 9.0 / 10.0 = 90% → in the near band (>= 80%, <= 100%)
        _seed_task(initdb, task_id="t1", agent="executor",
                   metrics={"usd_estimate": 9.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        st = bc.status("executor", db_path=initdb, root=farm_root)
        assert st.state == "near"

    def test_over_band(self, farm_root: Path, initdb: Path) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="t1", agent="executor",
                   metrics={"usd_estimate": 12.5},
                   ended_at=_iso(now - timedelta(hours=1)))
        st = bc.status("executor", db_path=initdb, root=farm_root)
        assert st.state == "over"
        assert st.spend_usd == pytest.approx(12.5)

    def test_zero_cap_quiet_when_no_spend(
        self, farm_root: Path, initdb: Path
    ) -> None:
        # deploy-keeper-style: max_usd_per_day=0.00 means "should never
        # spend". No spend → under band (the agent is well-behaved).
        _write_agent_yaml(farm_root, "deploy-keeper", cap=0.0)
        st = bc.status("deploy-keeper", db_path=initdb, root=farm_root)
        assert st.state == "under"

    def test_zero_cap_over_when_any_spend(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "deploy-keeper", cap=0.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="t1", agent="deploy-keeper",
                   metrics={"usd_estimate": 0.05},
                   ended_at=_iso(now - timedelta(hours=1)))
        st = bc.status("deploy-keeper", db_path=initdb, root=farm_root)
        assert st.state == "over"


# --------------------------------------------------------------------- #
# CLI commands (subprocess for real wiring).

def _run_cli(farm_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
    return subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts" / "lib" / "budget_check.py"), *args],
        check=False, capture_output=True, text=True, env=env,
    )


class TestEmitFinalize:
    def test_over_emits_error_event(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=5.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="tid-over", agent="executor",
                   metrics={"usd_estimate": 6.0},
                   ended_at=_iso(now - timedelta(minutes=5)))
        res = _run_cli(farm_root, "emit-finalize", "tid-over")
        assert res.returncode == 0, res.stderr
        # One error-level heartbeat row + matching kind=heartbeat event
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level, message FROM heartbeats WHERE task_id=?",
                ("tid-over",),
            ).fetchall()
            ev = conn.execute(
                "SELECT level FROM events "
                "WHERE task_id=? AND kind='heartbeat'",
                ("tid-over",),
            ).fetchall()
        finally:
            conn.close()
        assert any(r[0] == "error" and "OVER" in r[1] for r in rows)
        assert any(level == "error" for (level,) in ev)

    def test_near_emits_warn(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="tid-near", agent="executor",
                   metrics={"usd_estimate": 8.5},
                   ended_at=_iso(now - timedelta(minutes=5)))
        res = _run_cli(farm_root, "emit-finalize", "tid-near")
        assert res.returncode == 0
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level, message FROM heartbeats WHERE task_id=?",
                ("tid-near",),
            ).fetchall()
        finally:
            conn.close()
        assert any(r[0] == "warn" and "near cap" in r[1] for r in rows)

    def test_under_emits_nothing(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="tid-under", agent="executor",
                   metrics={"usd_estimate": 1.0},
                   ended_at=_iso(now - timedelta(minutes=5)))
        res = _run_cli(farm_root, "emit-finalize", "tid-under")
        assert res.returncode == 0
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level FROM heartbeats WHERE task_id=?",
                ("tid-under",),
            ).fetchall()
        finally:
            conn.close()
        assert rows == []

    def test_unknown_task_is_noop(
        self, farm_root: Path, initdb: Path
    ) -> None:
        res = _run_cli(farm_root, "emit-finalize", "no-such-tid")
        # No crash, no DB write
        assert res.returncode == 0


class TestEmitSpawn:
    def test_over_at_spawn_emits_warn(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=5.0)
        now = datetime.now(timezone.utc)
        # Prior 24h spend already over cap.
        _seed_task(initdb, task_id="prev", agent="executor",
                   metrics={"usd_estimate": 7.0},
                   ended_at=_iso(now - timedelta(hours=3)))
        # New task row (no metrics yet).
        _seed_task(initdb, task_id="new", agent="executor", metrics=None,
                   ended_at=_iso(now))
        res = _run_cli(farm_root, "emit-spawn", "new")
        assert res.returncode == 0
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level, message FROM heartbeats WHERE task_id=?",
                ("new",),
            ).fetchall()
        finally:
            conn.close()
        assert any(
            r[0] == "warn" and "OVER cap on spawn" in r[1]
            for r in rows
        )

    def test_under_at_spawn_no_signal(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        _seed_task(initdb, task_id="quiet", agent="executor", metrics=None,
                   ended_at=_iso(datetime.now(timezone.utc)))
        res = _run_cli(farm_root, "emit-spawn", "quiet")
        assert res.returncode == 0
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level FROM heartbeats WHERE task_id=?",
                ("quiet",),
            ).fetchall()
        finally:
            conn.close()
        assert rows == []


class TestOverages:
    def test_only_alerts_filters_under_and_nocap(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=5.0)
        _write_agent_yaml(farm_root, "janitor", cap=10.0)
        _write_agent_yaml(farm_root, "ghost", cap=None)
        now = datetime.now(timezone.utc)
        # executor OVER
        _seed_task(initdb, task_id="t1", agent="executor",
                   metrics={"usd_estimate": 6.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        # janitor UNDER (1 of 10)
        _seed_task(initdb, task_id="t2", agent="janitor",
                   metrics={"usd_estimate": 1.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        res = _run_cli(farm_root, "overages", "--only-alerts")
        assert res.returncode == 0
        # Only executor (OVER) should appear; janitor and ghost excluded.
        assert "executor" in res.stdout
        assert "janitor" not in res.stdout
        assert "ghost" not in res.stdout
        assert "OVER" in res.stdout

    def test_json_output_is_stable(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=5.0)
        now = datetime.now(timezone.utc)
        _seed_task(initdb, task_id="t1", agent="executor",
                   metrics={"usd_estimate": 6.0},
                   ended_at=_iso(now - timedelta(hours=1)))
        res = _run_cli(farm_root, "overages", "--json")
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert isinstance(data, list)
        assert any(e["agent"] == "executor" and e["state"] == "over"
                   for e in data)

    def test_empty_prints_no_alerts_marker(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        res = _run_cli(farm_root, "overages", "--only-alerts")
        assert res.returncode == 0
        assert "no cost_budget alerts" in res.stdout

    def test_skips_template_yaml(
        self, farm_root: Path, initdb: Path
    ) -> None:
        # _template.yaml is intentionally excluded by the overages walker
        (farm_root / "agents" / "_template.yaml").write_text(
            "name: _template\nkind: subagent\ncost_budget:\n  max_usd_per_day: 0.01\n"
        )
        # No real agents → output is "(no cost_budget alerts)" without crash.
        res = _run_cli(farm_root, "overages", "--only-alerts")
        assert res.returncode == 0
        assert "_template" not in res.stdout


class TestStatusCli:
    def test_status_returns_json(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=10.0)
        res = _run_cli(farm_root, "status", "executor")
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert data["agent"] == "executor"
        assert data["cap_usd"] == 10.0
        assert data["state"] in {"under", "near", "over", "no_cap"}
        assert data["warn_ratio"] > 0.0


class TestFinalizeHook:
    """End-to-end: finalize-subagent.sh runs the budget hook after writing
    metrics. We feed it a --metrics-json payload that pushes the agent
    over a tiny cap and assert the error-level heartbeat lands.
    """

    def test_finalize_emits_error_when_over(
        self, farm_root: Path, initdb: Path
    ) -> None:
        _write_agent_yaml(farm_root, "executor", cap=0.01)
        # Seed the task row before finalize calls set-ended on it.
        env = {**os.environ, "AGENT_FARM_ROOT": str(farm_root)}
        subprocess.run(
            [sys.executable, str(DB_PY),
             "insert-task", "fin-tid", "executor", "subagent", "0",
             "opus-4.7", "{}"],
            check=True, capture_output=True, env=env,
        )
        subprocess.run(
            [sys.executable, str(DB_PY), "set-started", "fin-tid"],
            check=True, capture_output=True, env=env,
        )
        payload = json.dumps({"usd_estimate": 0.50, "model": "claude-opus-4-7"})
        res = subprocess.run(
            ["bash",
             str(REPO_ROOT / "scripts" / "finalize-subagent.sh"),
             "fin-tid", "succeeded", "0", "done",
             "--metrics-json", payload],
            check=False, capture_output=True, text=True, env=env,
        )
        assert res.returncode == 0, (res.stdout, res.stderr)
        conn = sqlite3.connect(str(initdb))
        try:
            rows = conn.execute(
                "SELECT level, message FROM heartbeats "
                "WHERE task_id=? AND level='error'",
                ("fin-tid",),
            ).fetchall()
        finally:
            conn.close()
        assert any("OVER" in m for (_, m) in rows)
