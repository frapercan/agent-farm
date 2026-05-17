#!/usr/bin/env python3
"""scripts/lib/cost_report.py — FARM-2.2 cost-report aggregator backend.

Reads results.metrics_json + the join to tasks(agent_name, ended_at, ...)
and aggregates per (date, agent, model) over a rolling window. Used by
the bash wrapper scripts/cost-report.sh.

Output:
  - Human table (default): date | agent | model | tasks | input | output |
                           cache | usd, sorted by usd descending.
  - JSON (`--json`): array of objects with the same keys, sorted by
    (date, agent, model) ascending for stable diffing.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")))
DB_PATH = Path(os.environ.get("AGENT_FARM_DB", str(ROOT / "state" / "tasks.sqlite")))


def _iso_day(ts: str) -> str:
    """Best-effort day-bucket from an ISO timestamp. Falls back to the
    string's first 10 chars (which works for both ISO-8601 dates and the
    UTC `YYYY-MM-DDTHH:MM:SS...` shape db.py emits).
    """
    if not ts:
        return ""
    return ts[:10]


def _load(db_path: Path, cutoff_iso: str) -> list[dict[str, Any]]:
    """Join tasks + results, filter by ended_at >= cutoff (NULL ended_at
    fall back to created_at so killed/crashed tasks still appear with
    their last known timestamp).
    """
    if not db_path.is_file():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """SELECT t.id AS task_id,
                      t.agent_name AS agent,
                      COALESCE(t.ended_at, t.started_at, t.created_at) AS ts,
                      r.metrics_json AS metrics_json
               FROM tasks t
               JOIN results r ON r.task_id = t.id
               WHERE r.metrics_json IS NOT NULL
                 AND COALESCE(t.ended_at, t.started_at, t.created_at) >= ?""",
            (cutoff_iso,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _coerce_int(v: Any) -> int:
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0


def _coerce_float(v: Any) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def aggregate(
    rows: list[dict[str, Any]],
    agent_filter: str | None = None,
    model_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Group rows by (date, agent, model) and sum the cost columns."""
    buckets: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "tasks": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "usd": 0.0,
        }
    )
    for r in rows:
        agent = r.get("agent") or ""
        if agent_filter and agent != agent_filter:
            continue
        day = _iso_day(r.get("ts") or "")
        try:
            m = json.loads(r.get("metrics_json") or "{}")
        except (TypeError, ValueError):
            m = {}
        if not isinstance(m, dict):
            m = {}
        model = m.get("model") or "(unknown)"
        if model_filter and model != model_filter:
            continue
        key = (day, agent, model)
        b = buckets[key]
        b["tasks"] += 1
        b["input_tokens"] += _coerce_int(m.get("input_tokens"))
        b["output_tokens"] += _coerce_int(m.get("output_tokens"))
        b["cache_tokens"] += _coerce_int(m.get("cache_tokens"))
        b["usd"] += _coerce_float(m.get("usd_estimate"))

    return [
        {"date": d, "agent": a, "model": mo, **b}
        for (d, a, mo), b in buckets.items()
    ]


def _fmt_tok(n: int) -> str:
    """Compact token formatter: 1234567 -> '1.2M', 1234 -> '1.2k'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def render_table(buckets: list[dict[str, Any]]) -> str:
    if not buckets:
        return "(no cost data in window)"
    # Sort by usd descending so the operator sees the most expensive
    # (agent, model, day) first.
    rows = sorted(buckets, key=lambda r: r["usd"], reverse=True)
    headers = ["date", "agent", "model", "tasks", "input", "output", "cache", "usd"]
    lines = [headers]
    for r in rows:
        lines.append([
            r["date"],
            r["agent"],
            r["model"],
            str(r["tasks"]),
            _fmt_tok(r["input_tokens"]),
            _fmt_tok(r["output_tokens"]),
            _fmt_tok(r["cache_tokens"]),
            f"${r['usd']:.4f}",
        ])
    widths = [max(len(row[i]) for row in lines) for i in range(len(headers))]
    out: list[str] = []
    for i, row in enumerate(lines):
        out.append("  ".join(c.ljust(widths[j]) for j, c in enumerate(row)))
        if i == 0:
            out.append("  ".join("-" * w for w in widths))
    total = sum(r["usd"] for r in rows)
    out.append("")
    out.append(f"Total: ${total:.4f} across {sum(r['tasks'] for r in rows)} task(s)")
    return "\n".join(out)


def render_json(buckets: list[dict[str, Any]]) -> str:
    rows = sorted(buckets, key=lambda r: (r["date"], r["agent"], r["model"]))
    return json.dumps(rows, indent=2, sort_keys=True)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="agent-farm cost report")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--agent", default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--db", default=str(DB_PATH),
        help=argparse.SUPPRESS,  # internal: tests override this
    )
    ns = p.parse_args(argv[1:])

    if ns.days < 0:
        print("--days must be >= 0", file=sys.stderr)
        return 2

    cutoff = datetime.now(timezone.utc) - timedelta(days=ns.days)
    cutoff_iso = cutoff.astimezone().isoformat(timespec="seconds")
    rows = _load(Path(ns.db), cutoff_iso)
    buckets = aggregate(rows, agent_filter=ns.agent, model_filter=ns.model)
    if ns.json:
        print(render_json(buckets))
    else:
        print(render_table(buckets))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
