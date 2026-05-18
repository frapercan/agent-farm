#!/usr/bin/env python3
"""scripts/lib/budget_check.py — FARM-FEAT.8 advisory cost-budget enforcement.

Sums each agent's `results.metrics_json -> usd_estimate` over the rolling
24h window and compares the total to the agent yaml's
`cost_budget.max_usd_per_day`. Reports the resulting state without
hard-gating anything: callers decide what level of heartbeat / event to
emit. Per FARM-FEAT.8 acceptance:

    Today's value is advisory (read by /agents/budgets). This helper
    flips it to a warn-level signal at spawn time, plus an error-level
    event at finalize time when the just-finished task pushed the
    rolling sum over budget.

Commands:

    budget_check.py status <agent>
        Print the current rolling spend, the cap, and the state band
        (under | near | over) as JSON to stdout. Exit 0 in every case
        the data is readable; non-zero only on usage errors / DB
        unreachable. Designed for piping into heartbeats / boot reports.

    budget_check.py emit-finalize <task_id>
        Resolve the task's agent, run `status`, and emit:
          - one error-level event row (kind=heartbeat, level=error) on the
            task when the rolling sum strictly exceeds the cap;
          - one warn-level event row when the rolling sum is in the "near"
            band (>= 80% of cap, still <= cap).
        Never raises. Used by finalize-subagent.sh as a fire-and-forget hook.

    budget_check.py emit-spawn <task_id>
        Resolve the task's agent, run `status`, and emit a warn-level
        heartbeat on the just-spawned task when the agent's previous
        24h rolling spend was already over budget (i.e. the operator
        is starting another task while last-day spend already breached
        the cap). Used by spawn-subagent.sh / spawn.sh.

    budget_check.py overages
        Iterate every agent yaml and print one line per agent currently
        in "over" or "near" state. The conductor's bootstrap routine
        reads this for its ≤8-line boot report.

Design notes:

    - The aggregator query is intentionally close to cost_report.py's
      `_load` so the two stay coherent. We don't import cost_report
      to keep the helper standalone and testable in isolation.
    - The "near" band is 80% of the cap by default. Tunable via
      AGENT_FARM_BUDGET_WARN_RATIO (env var, float in (0, 1]).
    - Per acceptance text, this is NOT a hard gate. The emit-* commands
      record signals; they never refuse a spawn or block a finalize.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(os.environ.get(
    "AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")
))
DB_PATH = Path(os.environ.get(
    "AGENT_FARM_DB", str(ROOT / "state" / "tasks.sqlite")
))

# Default ratio at which we flip from "under" to "near". Overridable so
# tests don't have to hit 80% to exercise the near band.
DEFAULT_WARN_RATIO = 0.8


def _warn_ratio() -> float:
    raw = os.environ.get("AGENT_FARM_BUDGET_WARN_RATIO")
    if raw is None:
        return DEFAULT_WARN_RATIO
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_WARN_RATIO
    if not (0.0 < val <= 1.0):
        return DEFAULT_WARN_RATIO
    return val


@dataclass
class BudgetState:
    """Per-agent state returned by `status`.

    state band:
      - "no_cap"  → agent yaml has no max_usd_per_day (advisory-only)
      - "under"   → spend < warn_ratio * cap
      - "near"    → warn_ratio * cap <= spend <= cap
      - "over"    → spend > cap
    """

    agent: str
    window_hours: int
    cap_usd: float | None
    spend_usd: float
    state: str
    warn_ratio: float
    task_count: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def _coerce_float(v: Any) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _agent_yaml(agent: str, root: Path = ROOT) -> Path | None:
    cand = root / "agents" / f"{agent}.yaml"
    return cand if cand.is_file() else None


def _agent_cap(agent: str, root: Path = ROOT) -> float | None:
    """Read max_usd_per_day from the agent yaml. None when missing /
    unparseable so callers render "(no cap)" rather than blowing up.
    """
    path = _agent_yaml(agent, root)
    if path is None:
        return None
    try:
        raw = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    cb = raw.get("cost_budget") or {}
    if not isinstance(cb, dict):
        return None
    cap = cb.get("max_usd_per_day")
    if cap is None:
        return None
    try:
        return float(cap)
    except (TypeError, ValueError):
        return None


def _rolling_spend(
    db_path: Path, agent: str, window_hours: int = 24
) -> tuple[float, int]:
    """Return (sum_usd, task_count) for the agent over the rolling window.

    Mirrors cost_report._load's join. Tasks without a metrics_json row
    contribute zero (not an error).
    """
    if not db_path.is_file():
        return (0.0, 0)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    cutoff_iso = cutoff.astimezone().isoformat(timespec="seconds")
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            """SELECT r.metrics_json
                 FROM tasks t
                 JOIN results r ON r.task_id = t.id
                WHERE t.agent_name = ?
                  AND r.metrics_json IS NOT NULL
                  AND COALESCE(t.ended_at, t.started_at, t.created_at) >= ?""",
            (agent, cutoff_iso),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    total = 0.0
    count = 0
    for (metrics_json,) in rows:
        try:
            m = json.loads(metrics_json or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(m, dict):
            continue
        total += _coerce_float(m.get("usd_estimate"))
        count += 1
    return (total, count)


def status(
    agent: str,
    *,
    db_path: Path = DB_PATH,
    root: Path = ROOT,
    window_hours: int = 24,
) -> BudgetState:
    """Compute the budget state for one agent."""
    cap = _agent_cap(agent, root)
    spend, count = _rolling_spend(db_path, agent, window_hours=window_hours)
    ratio = _warn_ratio()
    if cap is None:
        # No max_usd_per_day declared at all → advisory only, no signal.
        band = "no_cap"
    elif cap == 0.0:
        # cap=0 (e.g. deploy-keeper) means "should never spend". Any spend
        # is OVER; zero spend is UNDER (the agent is behaving).
        band = "over" if spend > 0.0 else "under"
    elif spend > cap:
        band = "over"
    elif spend >= cap * ratio:
        band = "near"
    else:
        band = "under"
    return BudgetState(
        agent=agent,
        window_hours=window_hours,
        cap_usd=cap,
        spend_usd=round(spend, 6),
        state=band,
        warn_ratio=ratio,
        task_count=count,
    )


# --------------------------------------------------------------------- #
# Command implementations.

def _emit_heartbeat(
    task_id: str, level: str, message: str, root: Path = ROOT
) -> None:
    """Wrap scripts/lib/db.py heartbeat so emit-* never raises out."""
    import subprocess

    db_py = root / "scripts" / "lib" / "db.py"
    try:
        subprocess.run(
            [sys.executable, str(db_py), "heartbeat", task_id, level, message],
            check=False, capture_output=True,
        )
    except OSError:
        # heartbeat is best-effort — never block finalize/spawn
        return


def _resolve_agent(task_id: str, db_path: Path) -> str | None:
    if not db_path.is_file():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT agent_name FROM tasks WHERE id=?", (task_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return row[0]


def cmd_status(args: argparse.Namespace) -> int:
    st = status(
        args.agent,
        db_path=Path(args.db),
        root=Path(args.root),
        window_hours=args.window_hours,
    )
    print(st.to_json())
    return 0


def cmd_emit_finalize(args: argparse.Namespace) -> int:
    """Called from finalize-subagent.sh after metrics are written.

    Emits at most ONE heartbeat per call (error if over, warn if near,
    nothing otherwise). The heartbeat insertion also produces a kind=
    heartbeat event row carrying the level, which satisfies the
    acceptance bullet "emit an error-level event" without needing a
    second db.py command.
    """
    db_path = Path(args.db)
    root = Path(args.root)
    agent = _resolve_agent(args.task_id, db_path)
    if agent is None:
        # Task not found / DB missing → silent no-op
        return 0
    st = status(agent, db_path=db_path, root=root, window_hours=args.window_hours)
    if st.state == "over":
        msg = (
            f"cost_budget: {agent} OVER cap "
            f"${st.spend_usd:.4f} / ${st.cap_usd:.2f} "
            f"(24h, {st.task_count} task(s))"
        )
        _emit_heartbeat(args.task_id, "error", msg, root=root)
    elif st.state == "near":
        msg = (
            f"cost_budget: {agent} near cap "
            f"${st.spend_usd:.4f} / ${st.cap_usd:.2f} "
            f"(24h, {st.task_count} task(s))"
        )
        _emit_heartbeat(args.task_id, "warn", msg, root=root)
    # under / no_cap → silent
    if args.verbose:
        print(st.to_json())
    return 0


def cmd_emit_spawn(args: argparse.Namespace) -> int:
    """Called from spawn-subagent.sh / spawn.sh right after the new task
    row exists. Emits a warn-level heartbeat on the JUST-spawned task
    when the agent was already over (or near) budget over the last 24h.

    The new task itself does not yet contribute spend; this heartbeat is
    advisory only and tells the operator "you started another run while
    the day's spend already breached the cap".
    """
    db_path = Path(args.db)
    root = Path(args.root)
    agent = _resolve_agent(args.task_id, db_path)
    if agent is None:
        return 0
    st = status(agent, db_path=db_path, root=root, window_hours=args.window_hours)
    if st.state in {"over", "near"}:
        prefix = "OVER" if st.state == "over" else "near"
        msg = (
            f"cost_budget: {agent} {prefix} cap on spawn "
            f"${st.spend_usd:.4f} / ${st.cap_usd:.2f} "
            f"(prior 24h, {st.task_count} task(s)); proceeding (advisory)"
        )
        _emit_heartbeat(args.task_id, "warn", msg, root=root)
    if args.verbose:
        print(st.to_json())
    return 0


def cmd_overages(args: argparse.Namespace) -> int:
    """Print per-agent state, optionally filtered to those near/over the
    cap, in either human or JSON form. Used by the conductor bootstrap
    to surface budget overages in its 8-line boot report.
    """
    db_path = Path(args.db)
    root = Path(args.root)
    agents_dir = root / "agents"
    out: list[BudgetState] = []
    if agents_dir.is_dir():
        for entry in sorted(agents_dir.iterdir()):
            if entry.suffix.lower() not in {".yaml", ".yml"}:
                continue
            if entry.name == "_template.yaml":
                continue
            try:
                raw = yaml.safe_load(entry.read_text())
            except (OSError, yaml.YAMLError):
                continue
            if not isinstance(raw, dict):
                continue
            name = raw.get("name") or entry.stem
            if not isinstance(name, str):
                continue
            out.append(
                status(name, db_path=db_path, root=root,
                       window_hours=args.window_hours)
            )

    if args.only_alerts:
        out = [s for s in out if s.state in {"over", "near"}]

    if args.json:
        print(json.dumps([asdict(s) for s in out], indent=2, sort_keys=True))
        return 0

    if not out:
        print("(no cost_budget alerts)")
        return 0
    # Human form: one line per agent, sorted over → near → under so the
    # boot report's first lines are the actionable ones.
    order = {"over": 0, "near": 1, "under": 2, "no_cap": 3}
    out_sorted = sorted(out, key=lambda s: (order.get(s.state, 9), s.agent))
    for s in out_sorted:
        cap = f"${s.cap_usd:.2f}" if s.cap_usd is not None else "(no cap)"
        print(
            f"{s.state.upper():<5}  {s.agent:<22}  "
            f"${s.spend_usd:.4f} / {cap}  "
            f"({s.task_count} task(s) in last {s.window_hours}h)"
        )
    return 0


# --------------------------------------------------------------------- #
# CLI plumbing.

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="advisory cost_budget enforcement (FARM-FEAT.8)"
    )
    p.add_argument("--db", default=str(DB_PATH), help=argparse.SUPPRESS)
    p.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    p.add_argument("--window-hours", type=int, default=24,
                   help="rolling window (default 24h)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("status", help="print one agent's budget state")
    sp.add_argument("agent")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("emit-finalize",
                        help="hook for finalize-subagent.sh")
    sp.add_argument("task_id")
    sp.add_argument("--verbose", action="store_true")
    sp.set_defaults(func=cmd_emit_finalize)

    sp = sub.add_parser("emit-spawn",
                        help="hook for spawn-subagent.sh / spawn.sh")
    sp.add_argument("task_id")
    sp.add_argument("--verbose", action="store_true")
    sp.set_defaults(func=cmd_emit_spawn)

    sp = sub.add_parser("overages",
                        help="rollup across all agents (for boot report)")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--only-alerts", action="store_true",
                    help="only show agents in near/over state")
    sp.set_defaults(func=cmd_overages)

    return p


def main(argv: list[str]) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv[1:])
    return int(ns.func(ns))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
