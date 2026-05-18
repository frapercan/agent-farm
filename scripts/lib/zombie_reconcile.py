#!/usr/bin/env python3
"""scripts/lib/zombie_reconcile.py — detect and reconcile zombie running tasks.

A task is considered a zombie if:
  - It has status='running'
  - For headless tasks: no tmux window exists matching its tmux_window field
  - For subagent tasks: it's been running for >2 hours (finalize should have run)

Usage:
    python3 ~/Thesis2/agent-farm/scripts/lib/zombie_reconcile.py [--dry-run] [--quiet]

Exit codes:
    0: success (may have found and fixed zombies)
    1: error

Environment:
    FARM_SKIP_ZOMBIE_RECONCILE=1  — skip reconciliation entirely
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from subprocess import run, PIPE

ROOT = Path(os.environ.get("AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")))
DB_PATH = ROOT / "state" / "tasks.sqlite"
WORKTREES_DIR = Path(os.environ.get("AGENT_FARM_WORKTREES", str(Path.home() / "Thesis2" / "worktrees")))


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), timeout=10)
    c.execute("PRAGMA foreign_keys = ON;")
    return c


def get_tmux_windows() -> set[str]:
    """Return set of all active tmux window names (full names, not just IDs).

    tmux list-windows -a outputs lines like:
      agent-farm:0: deploy-keeper-1779061698-60a2- (1 panes) [80x23]

    We extract the window name (after the colon and index).
    """
    try:
        result = run(["tmux", "list-windows", "-a"], stdout=PIPE, stderr=PIPE, text=True)
        windows = set()
        for line in result.stdout.splitlines():
            # Parse "agent-farm:0: deploy-keeper-1779061698-60a2- (1 panes) [80x23]"
            if ":" in line:
                # Split on first colon to get session:window_index
                colon_idx = line.find(":")
                after_colon = line[colon_idx + 1:]

                # Find the window name (between the index and the first paren)
                # Format: "<index>: <name> (<panes>)"
                parts = after_colon.split()
                if len(parts) >= 2:
                    # Second part is the window name (may have trailing -, *, etc.)
                    window_name = parts[1].rstrip("*-")
                    windows.add(window_name)
        return windows
    except Exception:
        return set()


def is_zombie_task(task_id: str, agent_name: str, kind: str, started_at: str) -> bool:
    """Determine if a task is a zombie."""

    # Headless tasks: check tmux window
    if kind == "headless":
        # For headless (e.g. deploy-keeper), check if tmux window exists
        # Get the tmux_window field from DB
        with conn() as c:
            row = c.execute(
                "SELECT tmux_window FROM tasks WHERE id=?",
                (task_id,)
            ).fetchone()
            if row and row[0]:
                tmux_window = row[0]
                # tmux_window is stored as "session:window_name"
                # We need to check if the window_name exists in active windows
                active_windows = get_tmux_windows()
                window_name = tmux_window.split(":")[-1]  # Extract window name after colon
                if window_name not in active_windows:
                    return True  # Window not found, it's a zombie
        return False

    # Subagent tasks: check age (>2 hours = zombie)
    if kind == "subagent":
        try:
            start_dt = datetime.fromisoformat(started_at)
            now_dt = datetime.now(timezone.utc).astimezone()
            age = now_dt - start_dt
            return age > timedelta(hours=2)
        except Exception:
            return False

    return False


def reconcile_zombies(dry_run: bool = False, quiet: bool = False) -> int:
    """Find and reconcile zombie tasks."""

    if os.environ.get("FARM_SKIP_ZOMBIE_RECONCILE") == "1":
        if not quiet:
            print("Skipping zombie reconciliation (FARM_SKIP_ZOMBIE_RECONCILE=1)")
        return 0

    zombies = []

    with conn() as c:
        rows = c.execute(
            """SELECT id, agent_name, kind, started_at
               FROM tasks
               WHERE status = 'running'
               ORDER BY created_at DESC"""
        ).fetchall()

    # Identify zombies
    for task_id, agent_name, kind, started_at in rows:
        if is_zombie_task(task_id, agent_name, kind, started_at):
            zombies.append((task_id, agent_name, kind, started_at))

    # Report and optionally fix
    if not quiet:
        if dry_run:
            print(f"[DRY-RUN] Found {len(zombies)} zombie task(s):")
        else:
            print(f"Reconciling {len(zombies)} zombie task(s)...")

    for task_id, agent_name, kind, started_at in zombies:
        if not quiet:
            print(f"  {task_id} ({agent_name}, {kind}, started {started_at})")

        if not dry_run:
            with conn() as c:
                c.execute(
                    """UPDATE tasks
                       SET status='failed', ended_at=?
                       WHERE id=?""",
                    (now(), task_id)
                )

    return 0


def cleanup_orphaned_worktrees(dry_run: bool = False, quiet: bool = False) -> int:
    """Remove orphaned ephemeral worktrees that don't have corresponding task_ids."""

    if os.environ.get("FARM_SKIP_ZOMBIE_RECONCILE") == "1":
        return 0

    # Get all task_ids currently in the DB
    with conn() as c:
        rows = c.execute("SELECT id FROM tasks").fetchall()
    task_ids = {row[0] for row in rows}

    # Find ephemeral worktrees (pattern: <agent>-<unix>-<rand4>)
    # and skip protea-deploy
    orphaned = []

    if WORKTREES_DIR.exists():
        for item in WORKTREES_DIR.iterdir():
            if not item.is_dir():
                continue
            name = item.name

            # Skip protea-deploy (hard constraint)
            if name == "protea-deploy":
                continue

            # Check if name matches ephemeral task pattern: ^[a-z]+-[0-9]+-[a-f0-9]+$
            parts = name.split("-")
            if len(parts) >= 3:
                try:
                    # Check if second-to-last part is a unix timestamp
                    int(parts[-2])
                    # Check if last part is hex
                    int(parts[-1], 16)

                    # Reconstruct task_id (take first 3 parts)
                    task_id = "-".join(parts[:3])

                    if task_id not in task_ids:
                        orphaned.append(item)
                except (ValueError, IndexError):
                    pass

    if not quiet:
        if dry_run:
            print(f"[DRY-RUN] Found {len(orphaned)} orphaned worktree(s):")
        else:
            print(f"Removing {len(orphaned)} orphaned worktree(s)...")

    for worktree_path in orphaned:
        if not quiet:
            print(f"  {worktree_path.name}")

        if not dry_run:
            try:
                # Use git worktree remove
                run(
                    ["git", "-C", str(ROOT), "worktree", "remove", "-f", str(worktree_path)],
                    stdout=PIPE,
                    stderr=PIPE,
                    timeout=10
                )
            except Exception as e:
                if not quiet:
                    print(f"    WARNING: failed to remove: {e}")

    return 0


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    quiet = "--quiet" in argv

    try:
        # Reconcile zombie tasks
        reconcile_zombies(dry_run=dry_run, quiet=quiet)

        # Clean up orphaned worktrees
        cleanup_orphaned_worktrees(dry_run=dry_run, quiet=quiet)

        return 0
    except sqlite3.Error as e:
        print(f"sqlite error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
