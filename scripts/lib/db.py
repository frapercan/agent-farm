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
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-ended <task_id> <status> [exit_code]

All commands print nothing on success unless they're a query. Exit non-zero on error.
"""

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
    with conn() as c:
        c.execute(
            """INSERT INTO tasks(id, agent_name, kind, persistent, status,
                                 spawn_args, model, created_at)
               VALUES(?, ?, ?, ?, 'pending', ?, ?, ?)""",
            (task_id, agent, kind, int(persistent), args_json or "{}",
             model or None, now()),
        )
    return 0


def cmd_heartbeat(task_id: str, level: str, message: str) -> int:
    with conn() as c:
        c.execute(
            "INSERT INTO heartbeats(task_id, ts, level, message) VALUES(?,?,?,?)",
            (task_id, now(), level, message),
        )
    return 0


def cmd_set_status(task_id: str, status: str) -> int:
    with conn() as c:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    return 0


def cmd_set_started(task_id: str, worktree: str = "", tmux: str = "",
                    pid: str = "") -> int:
    with conn() as c:
        c.execute(
            """UPDATE tasks
               SET status='running', started_at=?,
                   worktree=NULLIF(?,''), tmux_window=NULLIF(?,''),
                   pid=CASE WHEN ?='' THEN NULL ELSE CAST(? AS INTEGER) END
               WHERE id=?""",
            (now(), worktree, tmux, pid, pid, task_id),
        )
    return 0


def cmd_set_ended(task_id: str, status: str, exit_code: str = "0") -> int:
    with conn() as c:
        c.execute(
            "UPDATE tasks SET status=?, ended_at=?, exit_code=? WHERE id=?",
            (status, now(), int(exit_code), task_id),
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
