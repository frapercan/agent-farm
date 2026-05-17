#!/usr/bin/env python3
"""scripts/lib/apply_migrations.py — idempotent migration runner.

Walks state/migrations/*.sql in lexical order and applies each one against
state/tasks.sqlite. Idempotency is enforced per-migration via known
preconditions (table/column existence) so re-running this script is a no-op
on an up-to-date database.

Sqlite has no `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, so the runner
inspects `PRAGMA table_info()` before executing each migration. Migrations
that are already inert (their declared columns/tables exist) are skipped
with a one-line log.

Usage:
    python3 scripts/lib/apply_migrations.py             # apply against $AGENT_FARM_DB
    python3 scripts/lib/apply_migrations.py --db PATH   # custom database
    python3 scripts/lib/apply_migrations.py --dry-run   # report only

Exit 0 on success (including no-ops), non-zero on failure.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(os.environ.get("AGENT_FARM_ROOT", str(Path.home() / "Thesis2" / "agent-farm")))
DEFAULT_DB = Path(os.environ.get("AGENT_FARM_DB", str(ROOT / "state" / "tasks.sqlite")))
MIGRATIONS_DIR = ROOT / "state" / "migrations"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _already_applied(conn: sqlite3.Connection, migration: Path) -> bool:
    """Detect whether a migration is already in place using cheap probes."""
    name = migration.name
    if name == "001_events.sql":
        return _table_exists(conn, "events")
    if name == "002_task_metadata.sql":
        return _column_exists(conn, "tasks", "worktree_owner_repo")
    # Unknown migration — assume not applied so we attempt it.
    return False


def apply_one(conn: sqlite3.Connection, migration: Path, dry_run: bool = False) -> str:
    """Apply a single migration. Returns a one-line status string."""
    if _already_applied(conn, migration):
        return f"skip {migration.name} (already applied)"
    if dry_run:
        return f"would apply {migration.name}"
    sql = migration.read_text()
    conn.executescript(sql)
    conn.commit()
    return f"applied {migration.name}"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=str(DEFAULT_DB),
                   help="path to tasks.sqlite (default: $AGENT_FARM_DB or canonical location)")
    p.add_argument("--dry-run", action="store_true",
                   help="report what would be applied without writing")
    p.add_argument("--migrations-dir", default=str(MIGRATIONS_DIR),
                   help="override migrations directory (mostly for tests)")
    args = p.parse_args(argv)

    mig_dir = Path(args.migrations_dir)
    if not mig_dir.is_dir():
        print(f"migrations dir missing: {mig_dir}", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"database missing: {db_path} (run init.sh first)", file=sys.stderr)
        return 1

    migrations = sorted(mig_dir.glob("*.sql"))
    if not migrations:
        print("no migrations found", file=sys.stderr)
        return 0

    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        for m in migrations:
            print(apply_one(conn, m, dry_run=args.dry_run))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
