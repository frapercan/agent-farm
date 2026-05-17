"""Scaffolded write endpoints.

These are only registered when `FARM_API_WRITE=1` AND
`FARM_API_AUTH_TOKEN` is set in the environment. Both conditions are
required so a misconfigured deployment cannot accidentally expose
unauthenticated mutating verbs.

Each endpoint currently returns 501 Not Implemented with a body that
echoes the request payload and points operators at the runbook. The
follow-up slice (FARM-UI.6 or similar) plugs in calls to
scripts/spawn-subagent.sh, scripts/kill.sh, and scripts/cleanup.sh.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from farm_api.config import Settings
from farm_api.schemas import WriteScaffold

router = APIRouter(tags=["writes"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def require_auth(
    settings: Annotated[Settings, Depends(get_settings)],
    x_farm_token: Annotated[str | None, Header()] = None,
) -> None:
    """FastAPI dependency that enforces the shared-secret header.

    The 403 is intentional even when the header is missing: a 401 would
    advertise that the endpoint exists and just needs a credential,
    whereas write paths should look like they do not exist to the
    unauthenticated public.
    """
    if not settings.auth_token:
        # Should not happen: app.py refuses to register writes when
        # auth_token is unset. Defence in depth.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "auth disabled")
    if not x_farm_token or x_farm_token != settings.auth_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid token")


class SpawnRequest(BaseModel):
    agent: str
    task: str
    model: str | None = None
    args: dict[str, Any] | None = None


class CleanupRequest(BaseModel):
    older_than_hours: int | None = None
    dry_run: bool = True


def _not_implemented(detail: str, payload: dict[str, Any] | None = None) -> HTTPException:
    body = WriteScaffold(detail=detail, payload_echo=payload).model_dump()
    return HTTPException(status.HTTP_501_NOT_IMPLEMENTED, body)


@router.post("/spawn", summary="Spawn a subagent (501 in v1)")
def spawn(
    body: SpawnRequest,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    raise _not_implemented(
        "spawn is scaffolded; v1 returns 501. Use scripts/spawn-subagent.sh"
        " from a terminal. Full body support lands in the FARM-UI follow-up.",
        body.model_dump(),
    )


@router.post("/tasks/{task_id}/kill", summary="Kill a task (501 in v1)")
def kill_task(
    task_id: str,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    raise _not_implemented(
        "kill is scaffolded; v1 returns 501. Use scripts/kill.sh "
        "<task_id> from a terminal.",
        {"task_id": task_id},
    )


@router.post("/cleanup", summary="Run cleanup sweep (501 in v1)")
def cleanup(
    body: CleanupRequest,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    raise _not_implemented(
        "cleanup is scaffolded; v1 returns 501. Use scripts/cleanup.sh "
        "from a terminal.",
        body.model_dump(),
    )
