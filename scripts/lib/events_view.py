#!/usr/bin/env python3
"""scripts/lib/events_view.py — render the events table (FARM-2.1).

Invoked by `status.sh --events`. Produces a tabular view of the last 50
lifecycle events (or up to --limit), with optional filters:

  --kind <spawn|start|end|kill|heartbeat|cleanup>
  --since <iso-or-relative>
        Relative: 30m, 2h, 1d (suffix m/h/d, integer prefix).
        Absolute: any ISO-8601 string sqlite recognises (e.g. 2026-05-17T15:00:00Z).
  --task <task_id>
        Restrict to a single task.
  --limit <N>     (default 50)

Output columns (TSV-like, padded for human readability):
  ts | task_id | agent | kind | level | message_truncated

Exit code 0 always (empty result is not an error).
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_RELATIVE_RX = re.compile(r"^(\d+)([smhd])$")


def parse_since(value: str) -> str:
    """Convert a --since argument to an ISO-8601 UTC timestamp string.

    Accepts:
      * a relative offset like "30m", "2h", "1d" (s/m/h/d)
      * an ISO-8601 absolute timestamp (returned unchanged so sqlite can
        compare with the events.ts column as text — both sides are ISO).
    """
    if not value:
        raise ValueError("empty --since")
    m = _RELATIVE_RX.match(value.strip())
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {
            "s": timedelta(seconds=n),
            "m": timedelta(minutes=n),
            "h": timedelta(hours=n),
            "d": timedelta(days=n),
        }[unit]
        target = datetime.now(timezone.utc) - delta
        # Match the schema default's ISO format: %Y-%m-%dT%H:%M:%fZ
        return target.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"
    # Treat as absolute; trust the user and pass through.
    return value.strip()


def truncate(s: str | None, n: int = 80) -> str:
    if not s:
        return ""
    s = s.replace("\n", " ").replace("\r", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def render(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "(no events)\n"
    # Fixed column widths chosen for the typical terminal (~120 cols).
    header = ("ts", "task_id", "agent", "kind", "level", "message")
    fmt = "{:<26}  {:<30}  {:<18}  {:<9}  {:<6}  {}"
    out = [fmt.format(*header)]
    out.append("-" * 120)
    for r in rows:
        out.append(
            fmt.format(
                str(r["ts"])[:26],
                str(r["task_id"])[:30],
                (r["agent_name"] or "")[:18],
                str(r["kind"])[:9],
                (r["level"] or "")[:6],
                truncate(r["message"], 60),
            )
        )
    return "\n".join(out) + "\n"


def query_events(
    db_path: Path,
    *,
    kind: str | None,
    since: str | None,
    task_id: str | None,
    limit: int,
) -> list[sqlite3.Row]:
    where: list[str] = []
    params: list[object] = []
    if kind:
        where.append("e.kind = ?")
        params.append(kind)
    if since:
        where.append("e.ts >= ?")
        params.append(since)
    if task_id:
        where.append("e.task_id = ?")
        params.append(task_id)
    sql = (
        "SELECT e.ts, e.task_id, e.kind, e.level, e.message, "
        "       COALESCE(t.agent_name,'') AS agent_name "
        "FROM events e "
        "LEFT JOIN tasks t ON t.id = e.task_id "
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY e.ts DESC LIMIT ?"
    params.append(limit)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return list(conn.execute(sql, params).fetchall())
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="status.sh --events", add_help=True)
    p.add_argument("--db", required=True, type=Path,
                   help="path to tasks.sqlite")
    p.add_argument("--kind", choices=sorted(
        ["spawn", "start", "end", "kill", "heartbeat", "cleanup"]))
    p.add_argument("--since", help="ISO timestamp or relative offset (e.g. 1h, 30m, 2d)")
    p.add_argument("--task", dest="task_id", help="filter to a single task_id")
    p.add_argument("--limit", type=int, default=50)
    args = p.parse_args(argv)

    if not args.db.exists():
        print(f"events: database not found: {args.db}", file=sys.stderr)
        return 2

    since_iso: str | None = None
    if args.since:
        try:
            since_iso = parse_since(args.since)
        except ValueError as e:
            print(f"events: invalid --since value: {e}", file=sys.stderr)
            return 2

    rows = query_events(
        args.db,
        kind=args.kind,
        since=since_iso,
        task_id=args.task_id,
        limit=max(1, args.limit),
    )
    sys.stdout.write(render(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
