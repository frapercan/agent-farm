"""Read-only sqlite access for farm-api.

The connection is opened with `?mode=ro` so the writer (db.py heartbeat /
finalize / cleanup paths) is never blocked by readers. WAL mode is set by
the writer's init.sh; we just open the file and rely on sqlite's
journal_mode=WAL contract that readers and writers do not contend.

Each request opens a new connection (sqlite3 connect is cheap on a local
file). FastAPI dependency-injection scopes the lifetime to the request.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _ro_uri(path: Path) -> str:
    # sqlite3 needs URI form for mode=ro. Using nolock=0 because the WAL
    # writer relies on the lock byte for the WAL header; mode=ro by
    # itself prevents accidental writes without disabling lock IPC.
    return f"file:{path}?mode=ro"


@contextmanager
def ro_connect(path: Path) -> Iterator[sqlite3.Connection]:
    """Open a read-only sqlite connection.

    Raises FileNotFoundError before the connection attempt so callers
    surface a clean 503 instead of sqlite's "unable to open database file"
    when the operator points FARM_API_DB at a path the farm has not yet
    initialised.
    """
    if not path.is_file():
        raise FileNotFoundError(f"farm-api db missing: {path}")
    conn = sqlite3.connect(_ro_uri(path), uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]
