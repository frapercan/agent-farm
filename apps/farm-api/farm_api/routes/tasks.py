"""/tasks endpoints — list, detail, heartbeats, results.

Query-param convention:
  status   exact match against tasks.status
  agent    exact match against tasks.agent_name
  since    relative offset (30m / 2h / 1d) OR ISO-8601 timestamp;
           filters on COALESCE(ended_at, started_at, created_at) so
           we surface tasks even when they have not yet ended
  limit    1..1000, default 200
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from farm_api.config import Settings
from farm_api.db import ro_connect
from farm_api.schemas import Heartbeat, Result, Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

_RELATIVE_RX = re.compile(r"^(\d+)([smhd])$")


def _parse_since(value: str) -> str:
    """Convert relative / absolute --since into ISO-8601. Mirrors
    scripts/lib/events_view.parse_since() so the API and the CLI accept
    the same vocabulary.
    """
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
        return target.astimezone().isoformat(timespec="seconds")
    return value.strip()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("", response_model=list[Task], summary="List tasks")
def list_tasks(
    settings: Annotated[Settings, Depends(get_settings)],
    status: str | None = Query(None, description="Exact status match"),
    agent: str | None = Query(None, description="Exact agent_name match"),
    since: str | None = Query(
        None,
        description="Relative offset (e.g. 1h, 24h, 7d) or ISO-8601 timestamp",
    ),
    limit: int = Query(200, ge=1, le=1000),
) -> list[Task]:
    where: list[str] = []
    params: list[object] = []
    if status:
        where.append("status = ?")
        params.append(status)
    if agent:
        where.append("agent_name = ?")
        params.append(agent)
    if since:
        try:
            since_iso = _parse_since(since)
        except (ValueError, KeyError) as e:
            raise HTTPException(400, f"invalid since: {e}") from e
        where.append("COALESCE(ended_at, started_at, created_at) >= ?")
        params.append(since_iso)
    sql = "SELECT * FROM tasks"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY COALESCE(started_at, created_at) DESC LIMIT ?"
    params.append(limit)
    try:
        with ro_connect(settings.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return [Task(**dict(r)) for r in rows]


@router.get("/{task_id}", response_model=Task, summary="Get task detail")
def get_task(
    task_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Task:
    try:
        with ro_connect(settings.db_path) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    if row is None:
        raise HTTPException(404, f"task not found: {task_id}")
    return Task(**dict(row))


@router.get(
    "/{task_id}/heartbeats",
    response_model=list[Heartbeat],
    summary="List heartbeats for a task",
)
def get_heartbeats(
    task_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    limit: int = Query(200, ge=1, le=2000),
) -> list[Heartbeat]:
    try:
        with ro_connect(settings.db_path) as conn:
            exists = conn.execute(
                "SELECT 1 FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
            if exists is None:
                raise HTTPException(404, f"task not found: {task_id}")
            rows = conn.execute(
                """SELECT id, task_id, ts, level, message
                   FROM heartbeats WHERE task_id=?
                   ORDER BY ts DESC LIMIT ?""",
                (task_id, limit),
            ).fetchall()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return [Heartbeat(**dict(r)) for r in rows]


@router.get(
    "/{task_id}/results",
    response_model=Result,
    summary="Get the results row for a task",
)
def get_results(
    task_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Result:
    try:
        with ro_connect(settings.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM results WHERE task_id=?", (task_id,)
            ).fetchone()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    if row is None:
        # A task can exist without a results row (it never reached
        # finalize). Surface that as a distinct 404 so the UI knows to
        # render "no results yet" instead of "task missing".
        raise HTTPException(404, f"no results row for task: {task_id}")
    return Result(**dict(row))
