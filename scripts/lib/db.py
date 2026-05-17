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
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-metrics <task_id> <metrics_json_str>
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-worktree-owner-repo <task_id> <repo_path>
    python3 ~/Thesis2/agent-farm/scripts/lib/db.py set-sha <task_id> before|after <sha>

FARM-2.1: every lifecycle entrypoint also appends a row to the events
table inside the same transaction (so a task move to a terminal state and
the matching audit row are committed atomically).

FARM-2.2: set-metrics upserts the results.metrics_json column (creating
the results row if missing) and annotates the most recent kind=end event
for the task with the parsed metrics under payload.metrics. If no end
event exists yet (set-metrics called before set-ended) a kind=end row is
NOT inserted; we just stamp the results column.

FARM-2.3: set-worktree-owner-repo records the owning repo at spawn time
so finalize/cleanup/kill skip the O(repos x worktrees) scan. No event
row is emitted; the column is plumbing, not lifecycle.

FARM-2.4: set-sha writes results.sha_before (right after worktree
creation) or results.sha_after (right before teardown). Upserts the
results row when needed; emits no event.

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


def cmd_set_metrics(task_id: str, metrics_json: str) -> int:
    """Upsert results.metrics_json for the task and annotate the latest
    kind=end event with the parsed metrics (so the audit trail surfaces
    cost without a second join).

    The input must be a valid JSON object; an invalid blob exits non-zero
    so callers notice malformed parser output instead of silently dropping
    cost data.
    """
    try:
        parsed = json.loads(metrics_json or "{}")
    except (TypeError, ValueError) as e:
        print(f"set-metrics: invalid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(parsed, dict):
        print("set-metrics: metrics_json must be a JSON object", file=sys.stderr)
        return 2
    # Re-serialise with canonical ordering so downstream consumers see a
    # stable string (handy for assertions + cache keys).
    canonical = json.dumps(parsed, sort_keys=True)
    with conn() as c:
        cur = c.cursor()
        # Verify the task exists so we don't accidentally orphan a results row.
        row = cur.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            print(f"set-metrics: unknown task_id: {task_id}", file=sys.stderr)
            return 1
        # Upsert the results row.
        cur.execute(
            """INSERT INTO results(task_id, metrics_json)
               VALUES(?, ?)
               ON CONFLICT(task_id) DO UPDATE SET metrics_json=excluded.metrics_json""",
            (task_id, canonical),
        )
        # If a kind=end event already exists, fold the metrics into its
        # payload (preserves the original status/exit_code/summary
        # fields). Otherwise leave events alone — the next set-ended will
        # emit a fresh end event and the caller can re-run set-metrics
        # afterwards if order matters.
        end_row = cur.execute(
            """SELECT id, payload_json FROM events
               WHERE task_id=? AND kind='end'
               ORDER BY id DESC LIMIT 1""",
            (task_id,),
        ).fetchone()
        if end_row is not None:
            ev_id, ev_payload = end_row
            try:
                ev_obj: dict = json.loads(ev_payload) if ev_payload else {}
            except (TypeError, ValueError):
                ev_obj = {}
            if not isinstance(ev_obj, dict):
                ev_obj = {}
            ev_obj["metrics"] = parsed
            cur.execute(
                "UPDATE events SET payload_json=? WHERE id=?",
                (json.dumps(ev_obj, sort_keys=True), ev_id),
            )
    return 0


def cmd_set_worktree_owner_repo(task_id: str, repo: str) -> int:
    """Record the owning repo of the task's worktree (FARM-2.3).

    Called by spawn-subagent.sh immediately after `git worktree add` so the
    finalize/cleanup/kill teardown path can look the column up instead of
    scanning every repo under ~/Thesis2/repositories.

    No event is emitted; this is plumbing, not lifecycle.
    """
    if not repo:
        print("set-worktree-owner-repo: repo must be non-empty", file=sys.stderr)
        return 2
    with conn() as c:
        cur = c.cursor()
        row = cur.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            print(f"set-worktree-owner-repo: unknown task_id: {task_id}", file=sys.stderr)
            return 1
        cur.execute(
            "UPDATE tasks SET worktree_owner_repo=? WHERE id=?",
            (repo, task_id),
        )
    return 0


def cmd_set_sha(task_id: str, which: str, sha: str) -> int:
    """Write results.sha_before or results.sha_after (FARM-2.4).

    `which` must be 'before' or 'after'. Upserts the results row when it
    doesn't yet exist so callers don't have to special-case the first write.
    No event is emitted.
    """
    if which not in ("before", "after"):
        print(f"set-sha: which must be 'before' or 'after', got {which!r}", file=sys.stderr)
        return 2
    if not sha:
        print("set-sha: sha must be non-empty", file=sys.stderr)
        return 2
    column = "sha_before" if which == "before" else "sha_after"
    with conn() as c:
        cur = c.cursor()
        row = cur.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            print(f"set-sha: unknown task_id: {task_id}", file=sys.stderr)
            return 1
        # Upsert; preserves whichever sibling column already holds a value.
        cur.execute(
            f"""INSERT INTO results(task_id, {column})
                VALUES(?, ?)
                ON CONFLICT(task_id) DO UPDATE SET {column}=excluded.{column}""",
            (task_id, sha),
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
    "set-metrics": cmd_set_metrics,
    "set-worktree-owner-repo": cmd_set_worktree_owner_repo,
    "set-sha": cmd_set_sha,
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
