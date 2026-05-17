"""/events endpoint.

Reuses the SQL shape of scripts/lib/events_view.query_events without
importing it directly: that module is a CLI runner with its own
argparse / rendering surface, and pulling it in would force the API to
ship its terminal padding code. The duplicated SELECT is six lines.

Filters:
  kind     exact match against events.kind
  level    exact match against events.level (heartbeat events surface
           info/warn/error here)
  task_id  exact match against events.task_id
  since    relative or ISO-8601 (same parser as /tasks)
  limit    1..2000, default 200
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from farm_api.config import Settings
from farm_api.db import ro_connect
from farm_api.schemas import Event

router = APIRouter(prefix="/events", tags=["events"])

_RELATIVE_RX = re.compile(r"^(\d+)([smhd])$")

VALID_KINDS = {"spawn", "start", "end", "kill", "heartbeat", "cleanup"}


def _parse_since(value: str) -> str:
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


@router.get("", response_model=list[Event], summary="List lifecycle events")
def list_events(
    settings: Annotated[Settings, Depends(get_settings)],
    kind: str | None = Query(None, description="Filter by kind"),
    level: str | None = Query(None, description="Filter by level"),
    task_id: str | None = Query(None),
    since: str | None = Query(
        None,
        description="Relative offset (e.g. 30m) or ISO-8601 timestamp",
    ),
    limit: int = Query(200, ge=1, le=2000),
) -> list[Event]:
    if kind is not None and kind not in VALID_KINDS:
        raise HTTPException(400, f"invalid kind: {kind}")
    where: list[str] = []
    params: list[object] = []
    if kind:
        where.append("e.kind = ?")
        params.append(kind)
    if level:
        where.append("e.level = ?")
        params.append(level)
    if task_id:
        where.append("e.task_id = ?")
        params.append(task_id)
    if since:
        try:
            since_iso = _parse_since(since)
        except (ValueError, KeyError) as e:
            raise HTTPException(400, f"invalid since: {e}") from e
        where.append("e.ts >= ?")
        params.append(since_iso)
    sql = (
        "SELECT e.id, e.task_id, e.ts, e.kind, e.level, e.message, "
        "e.payload_json, COALESCE(t.agent_name,'') AS agent_name "
        "FROM events e "
        "LEFT JOIN tasks t ON t.id = e.task_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY e.ts DESC, e.id DESC LIMIT ?"
    params.append(limit)
    try:
        with ro_connect(settings.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return [Event(**dict(r)) for r in rows]
