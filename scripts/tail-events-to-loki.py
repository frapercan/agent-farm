#!/usr/bin/env python3
"""tail-events-to-loki — ship agent-farm events to Loki for FARM-UI.7.

The agent-farm tmux session does not run inside docker compose, so the
`loki-docker-driver` plugin that PROTEA api / workers use does not apply
here. Instead this sidecar polls the `events` and `heartbeats` tables in
`state/tasks.sqlite` (both populated by `scripts/lib/db.py`), batches
new rows into Loki's HTTP push API as JSON streams, and remembers its
high-water mark in a tiny sidecar file so it resumes cleanly across
restarts.

Each emitted Loki stream carries the labels expected by the
`agent-farm-heartbeats` Grafana dashboard and the
`agent-farm-error-burst` unified-alerting rule provisioned in PROTEA:

    {
        "compose_project": "agent-farm",
        "agent_name": "<row.agent_name>",
        "task_id":    "<row.task_id>",
        "source":     "events" | "heartbeats",
    }

The line body is a JSON object exposing `level`, `kind` (events only),
`message`, and `payload` (events only). The dashboard parses these with
the `| json` filter; the alert rule reads the promoted `level` label.

This script is intentionally dependency-light: only `requests` (already
in the agent-farm runtime). Tests inject a fake push endpoint via the
`LOKI_PUSH_URL` env var.

CLI usage:

    AGENT_FARM_ROOT=~/Thesis2/agent-farm \
    LOKI_PUSH_URL=http://localhost:3100/loki/api/v1/push \
    python3 scripts/tail-events-to-loki.py             # run forever
    python3 scripts/tail-events-to-loki.py --once      # one drain pass
    python3 scripts/tail-events-to-loki.py --interval 5  # poll every 5s

Returns nonzero only on unrecoverable startup failure (missing DB,
unreachable schema). Transient Loki push failures are logged to stderr
and retried on the next poll without losing the high-water mark (the
mark advances only after a 2xx response).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

try:
    import requests  # type: ignore[import-not-found]
except ImportError:
    requests = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Paths and config
# ---------------------------------------------------------------------------


def _farm_root() -> Path:
    return Path(
        os.environ.get(
            "AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")
        )
    )


def _db_path() -> Path:
    return _farm_root() / "state" / "tasks.sqlite"


def _cursor_path() -> Path:
    """Sidecar file holding the (events_id, heartbeats_id) high-water mark.

    Lives next to the sqlite DB so it shares the state/ dir's lifecycle
    with the rest of the runtime state. Format is a single JSON object
    written atomically (write to .tmp then rename).
    """
    return _farm_root() / "state" / "loki-tail-cursor.json"


def _loki_push_url() -> str:
    return os.environ.get(
        "LOKI_PUSH_URL", "http://localhost:3100/loki/api/v1/push"
    )


# ---------------------------------------------------------------------------
# Cursor persistence
# ---------------------------------------------------------------------------


@dataclass
class TailCursor:
    """High-water marks for the events and heartbeats tables.

    The DB schema gives both tables monotonically-increasing autoincrement
    `id` columns; we never delete rows mid-tail, so a single integer per
    table is enough to skip rows we have already shipped.
    """

    events_id: int = 0
    heartbeats_id: int = 0

    @classmethod
    def load(cls, path: Path) -> "TailCursor":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            # Corrupt cursor: rewind to zero. The duplicate-shipment cost
            # is one full table replay (cheap; Loki dedupes on ts+labels
            # for streams with identical labels and timestamps).
            return cls()
        return cls(
            events_id=int(data.get("events_id", 0) or 0),
            heartbeats_id=int(data.get("heartbeats_id", 0) or 0),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {"events_id": self.events_id, "heartbeats_id": self.heartbeats_id},
                sort_keys=True,
            )
        )
        tmp.replace(path)


# ---------------------------------------------------------------------------
# DB readers
# ---------------------------------------------------------------------------


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _iso_to_loki_ns(ts: str) -> str:
    """Convert ISO-8601 timestamp to a Loki nanosecond string.

    Loki's push API wants nanosecond precision as a string. The
    `events.ts` default is `strftime('%Y-%m-%dT%H:%M:%fZ','now')` (UTC,
    millisecond precision); `heartbeats.ts` is whatever `db.py.now()`
    produces (`datetime.now().astimezone().isoformat(timespec='seconds')`,
    second precision with timezone). Both round-trip through
    `datetime.fromisoformat` cleanly.
    """
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        # Bad ts on disk: fall back to "now" so the line still ships
        # rather than getting silently dropped.
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    epoch_ns = int(dt.timestamp() * 1_000_000_000)
    return str(epoch_ns)


def _read_new_events(
    conn: sqlite3.Connection, after_id: int
) -> Iterator[dict]:
    """Yield Loki-ready dicts for every events row strictly after_id."""
    cur = conn.execute(
        """
        SELECT e.id, e.task_id, e.ts, e.kind, e.level, e.message, e.payload_json,
               t.agent_name
          FROM events AS e
          JOIN tasks  AS t ON t.id = e.task_id
         WHERE e.id > ?
         ORDER BY e.id ASC
        """,
        (after_id,),
    )
    for row in cur.fetchall():
        body = {
            "level": row["level"] or "info",
            "kind": row["kind"],
            "message": row["message"] or "",
        }
        if row["payload_json"]:
            try:
                body["payload"] = json.loads(row["payload_json"])
            except (TypeError, json.JSONDecodeError):
                body["payload_raw"] = row["payload_json"]
        yield {
            "id": int(row["id"]),
            "source": "events",
            "task_id": row["task_id"],
            "agent_name": row["agent_name"] or "unknown",
            "ts_ns": _iso_to_loki_ns(row["ts"]),
            "body": body,
        }


def _read_new_heartbeats(
    conn: sqlite3.Connection, after_id: int
) -> Iterator[dict]:
    """Yield Loki-ready dicts for every heartbeats row strictly after_id."""
    cur = conn.execute(
        """
        SELECT h.id, h.task_id, h.ts, h.level, h.message,
               t.agent_name
          FROM heartbeats AS h
          JOIN tasks      AS t ON t.id = h.task_id
         WHERE h.id > ?
         ORDER BY h.id ASC
        """,
        (after_id,),
    )
    for row in cur.fetchall():
        yield {
            "id": int(row["id"]),
            "source": "heartbeats",
            "task_id": row["task_id"],
            "agent_name": row["agent_name"] or "unknown",
            "ts_ns": _iso_to_loki_ns(row["ts"]),
            "body": {
                "level": row["level"] or "info",
                "message": row["message"] or "",
            },
        }


# ---------------------------------------------------------------------------
# Loki push
# ---------------------------------------------------------------------------


def _build_payload(rows: Iterable[dict]) -> dict:
    """Group rows into Loki streams by (compose_project, agent_name, task_id, source).

    Loki's push API accepts multiple streams per request; grouping by
    label-set lets the alert rule's `sum by (task_id, agent_name)` over
    `level="error"` line up cleanly. Each stream's `values` list is
    [[timestamp_ns_str, json_body_str], ...].
    """
    streams: dict[tuple[str, str, str, str], list[list[str]]] = {}
    for row in rows:
        key = (
            "agent-farm",
            row["agent_name"],
            row["task_id"],
            row["source"],
        )
        body_json = json.dumps(row["body"], sort_keys=True)
        streams.setdefault(key, []).append([row["ts_ns"], body_json])
    return {
        "streams": [
            {
                "stream": {
                    "compose_project": key[0],
                    "agent_name": key[1],
                    "task_id": key[2],
                    "source": key[3],
                },
                "values": values,
            }
            for key, values in streams.items()
        ]
    }


def _push_to_loki(payload: dict, url: str, timeout: float = 5.0) -> bool:
    """POST payload to Loki. Return True on 2xx, False otherwise."""
    if not payload["streams"]:
        return True  # nothing to do is success
    if requests is None:
        # Fallback path so the sidecar still works on a minimal Python
        # install: use urllib instead of requiring `requests`. Tests
        # cover the requests branch; this branch is exercised when the
        # operator runs the script from a system python.
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 300
        except (urllib.error.URLError, OSError) as exc:
            print(f"loki push failed (urllib): {exc}", file=sys.stderr)
            return False
    try:
        resp = requests.post(
            url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
    except requests.RequestException as exc:  # type: ignore[union-attr]
        print(f"loki push failed (requests): {exc}", file=sys.stderr)
        return False
    if not 200 <= resp.status_code < 300:
        print(
            f"loki push rejected: {resp.status_code} {resp.text[:200]}",
            file=sys.stderr,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Drain loop
# ---------------------------------------------------------------------------


def drain_once(
    db_path: Path,
    cursor_path: Path,
    loki_url: str,
) -> int:
    """One poll pass. Return the number of rows shipped.

    The cursor advances only after a successful Loki push so a transient
    failure replays on the next iteration. We push events and
    heartbeats in a single batch since the alert rule queries both via
    `{compose_project="agent-farm"}` without filtering on `source`.
    """
    if not db_path.exists():
        print(f"db not found: {db_path}", file=sys.stderr)
        return 0
    cursor = TailCursor.load(cursor_path)
    with _connect(db_path) as conn:
        events = list(_read_new_events(conn, cursor.events_id))
        heartbeats = list(_read_new_heartbeats(conn, cursor.heartbeats_id))
    all_rows = events + heartbeats
    if not all_rows:
        return 0
    payload = _build_payload(all_rows)
    ok = _push_to_loki(payload, loki_url)
    if not ok:
        return 0
    if events:
        cursor.events_id = max(r["id"] for r in events)
    if heartbeats:
        cursor.heartbeats_id = max(r["id"] for r in heartbeats)
    cursor.save(cursor_path)
    return len(all_rows)


def drain_forever(
    db_path: Path,
    cursor_path: Path,
    loki_url: str,
    interval_seconds: float,
) -> None:
    """Poll the DB every interval_seconds, shipping new rows each pass."""
    while True:
        try:
            shipped = drain_once(db_path, cursor_path, loki_url)
            if shipped:
                print(f"shipped {shipped} rows to {loki_url}", file=sys.stderr)
        except KeyboardInterrupt:
            return
        except Exception as exc:  # pragma: no cover - safety net only
            # Never let a bug here take down the sidecar; log and retry.
            print(f"drain pass failed: {exc!r}", file=sys.stderr)
        time.sleep(interval_seconds)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--once",
        action="store_true",
        help="Drain once and exit (useful for tests and the synthetic-alert acceptance check).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Poll interval in seconds when running forever (default: 2.0).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Override the sqlite DB path (default: $AGENT_FARM_ROOT/state/tasks.sqlite).",
    )
    parser.add_argument(
        "--cursor",
        type=Path,
        default=None,
        help="Override the cursor file path (default: $AGENT_FARM_ROOT/state/loki-tail-cursor.json).",
    )
    parser.add_argument(
        "--loki-url",
        default=None,
        help="Override the Loki push URL (default: $LOKI_PUSH_URL or http://localhost:3100/loki/api/v1/push).",
    )
    args = parser.parse_args(argv)

    db_path = args.db if args.db is not None else _db_path()
    cursor_path = args.cursor if args.cursor is not None else _cursor_path()
    loki_url = args.loki_url if args.loki_url is not None else _loki_push_url()

    if args.once:
        shipped = drain_once(db_path, cursor_path, loki_url)
        print(f"shipped {shipped} rows", file=sys.stderr)
        return 0

    drain_forever(db_path, cursor_path, loki_url, args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
