#!/usr/bin/env python3
"""scripts/lib/db.py — sqlite helpers for bash scripts.

Usage from bash:
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py init
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py exec "SQL ..."
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py query "SELECT ..."   # tab-separated
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py insert-task <id> <agent> <kind> <persistent> <model> <args_json>
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py heartbeat <task_id> <level> <message>
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-status <task_id> <status>
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-started <task_id> [worktree] [tmux_window] [pid]
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-ended <task_id> <status> [exit_code] [summary]
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py mark-killed <task_id> [reason]
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py mark-crashed <task_id> [reason]

FARM-2.1: every lifecycle entrypoint also appends a row to the events
table inside the same transaction (so a task move to a terminal state and
the matching audit row are committed atomically).

All commands print nothing on success unless they're a query. Exit non-zero on error.
"""

import json
import os
import sys
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")))
DB_PATH = ROOT / "state" / "tasks.sqlite"
SCHEMA_PATH = ROOT / "state" / "schema.sql"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), timeout=10)
    c.execute("PRAGMA foreign_keys = ON;")
    return c


# ---------------------------------------------------------------------------
# events emission (FARM-2.1)
# ---------------------------------------------------------------------------

VALID_KINDS = {"spawn", "start", "end", "kill", "heartbeat", "cleanup"}


def _emit_event(
    cursor: sqlite3.Cursor,
    task_id: str,
    kind: str,
    level: str | None = None,
    message: str | None = None,
    payload: dict | None = None,
) -> None:
    """Append an events row using an existing cursor (so the parent
    transaction stays atomic). Caller MUST be inside a `with conn()` block.
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"invalid event kind: {kind!r}")
    payload_json = json.dumps(payload, sort_keys=True) if payload is not None else None
    cursor.execute(
        """INSERT INTO events(task_id, ts, kind, level, message, payload_json)
           VALUES(?, ?, ?, ?, ?, ?)""",
        (task_id, now(), kind, level, message, payload_json),
    )


# ---------------------------------------------------------------------------
# command implementations
# ---------------------------------------------------------------------------


def cmd_init() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text()
    with conn() as c:
        c.executescript(schema)
    print(f"DB ready at {DB_PATH}")
    return 0


def cmd_exec(sql: str) -> int:
    with conn() as c:
        c.execute(sql)
    return 0


def cmd_query(sql: str) -> int:
    with conn() as c:
        cur = c.execute(sql)
        for row in cur.fetchall():
            print("\t".join("" if v is None else str(v) for v in row))
    return 0


def cmd_insert_task(task_id: str, agent: str, kind: str, persistent: str,
                    model: str, args_json: str) -> int:
    spawn_args = args_json or "{}"
    # Decode the spawn args so the event payload mirrors them as structured
    # JSON instead of an opaque string; tolerate malformed input.
    try:
        spawn_args_decoded: object = json.loads(spawn_args)
    except (TypeError, ValueError):
        spawn_args_decoded = spawn_args
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            """INSERT INTO tasks(id, agent_name, kind, persistent, status,
                                 spawn_args, model, created_at)
               VALUES(?, ?, ?, ?, 'pending', ?, ?, ?)""",
            (task_id, agent, kind, int(persistent), spawn_args,
             model or None, now()),
        )
        _emit_event(
            cur,
            task_id,
            "spawn",
            level="info",
            message=f"task spawned: agent={agent} kind={kind} model={model or ''}",
            payload={
                "agent": agent,
                "kind": kind,
                "persistent": int(persistent),
                "model": model or None,
                "spawn_args": spawn_args_decoded,
            },
        )
    return 0


def cmd_heartbeat(task_id: str, level: str, message: str) -> int:
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO heartbeats(task_id, ts, level, message) VALUES(?,?,?,?)",
            (task_id, now(), level, message),
        )
        _emit_event(cur, task_id, "heartbeat", level=level, message=message)
    return 0


def cmd_set_status(task_id: str, status: str) -> int:
    with conn() as c:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    return 0


def cmd_set_started(task_id: str, worktree: str = "", tmux: str = "",
                    pid: str = "") -> int:
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            """UPDATE tasks
               SET status='running', started_at=?,
                   worktree=NULLIF(?,''), tmux_window=NULLIF(?,''),
                   pid=CASE WHEN ?='' THEN NULL ELSE CAST(? AS INTEGER) END
               WHERE id=?""",
            (now(), worktree, tmux, pid, pid, task_id),
        )
        _emit_event(
            cur,
            task_id,
            "start",
            level="info",
            message="task started",
            payload={
                "worktree": worktree or None,
                "tmux_window": tmux or None,
                "pid": int(pid) if pid else None,
            },
        )
    return 0


def cmd_set_ended(task_id: str, status: str, exit_code: str = "0",
                  summary: str = "") -> int:
    try:
        exit_int: int | None = int(exit_code)
    except (TypeError, ValueError):
        exit_int = None
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "UPDATE tasks SET status=?, ended_at=?, exit_code=? WHERE id=?",
            (status, now(), exit_int, task_id),
        )
        payload: dict = {"status": status, "exit_code": exit_int}
        # Summary first 200 chars as required by the spec.
        if summary:
            payload["summary"] = summary[:200]
        _emit_event(
            cur,
            task_id,
            "end",
            level="info" if status == "succeeded" else "warn",
            message=f"task ended: status={status} exit={exit_int}",
            payload=payload,
        )
    return 0


def cmd_mark_killed(task_id: str, reason: str = "") -> int:
    """Record an explicit kill event. Used by scripts/kill.sh which still
    calls set-ended (status=killed) afterward; the kind=kill row lets the
    audit trail distinguish operator-initiated kills from natural task ends.
    """
    with conn() as c:
        cur = c.cursor()
        _emit_event(
            cur,
            task_id,
            "kill",
            level="warn",
            message=reason or "killed by operator",
            payload={"reason": reason or None},
        )
    return 0


def cmd_mark_crashed(task_id: str, reason: str = "") -> int:
    """Record a cleanup-detected crash. The companion set-ended call moves
    the task to status=crashed; this kind=cleanup event documents that
    cleanup.sh was the actor.
    """
    with conn() as c:
        cur = c.cursor()
        _emit_event(
            cur,
            task_id,
            "cleanup",
            level="warn",
            message=reason or "cleanup marked task crashed",
            payload={"reason": reason or None},
        )
    return 0


COMMANDS = {
    "init": cmd_init,
    "exec": cmd_exec,
    "query": cmd_query,
    "insert-task": cmd_insert_task,
    "heartbeat": cmd_heartbeat,
    "set-status": cmd_set_status,
    "set-started": cmd_set_started,
    "set-ended": cmd_set_ended,
    "mark-killed": cmd_mark_killed,
    "mark-crashed": cmd_mark_crashed,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    fn = COMMANDS[argv[1]]
    try:
        return fn(*argv[2:])
    except TypeError as e:
        print(f"argument error for '{argv[1]}': {e}", file=sys.stderr)
        return 2
    except sqlite3.Error as e:
        print(f"sqlite error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
