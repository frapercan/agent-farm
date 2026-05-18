"""Write endpoints (spawn, kill, cleanup).

These are only registered when `FARM_API_WRITE=1` AND
`FARM_API_AUTH_TOKEN` is set in the environment. Both conditions are
required so a misconfigured deployment cannot accidentally expose
unauthenticated mutating verbs.

Each verb shells out to the canonical agent-farm bash script so the
behaviour is identical to what the operator gets at the terminal:

  POST /spawn               -> scripts/spawn-subagent.sh <agent> <spec>
  POST /tasks/{id}/kill     -> scripts/kill.sh <task_id>
  POST /cleanup             -> scripts/cleanup.sh [--apply]

The /spawn endpoint also supports a `next_pickable` mode which first
resolves the highest-priority pickable slice via plan-progress.sh
--next --json, then dispatches the configured default agent for that
loop. This collapses the operator's "open palette + select agent +
paste slice id" loop into one click from the FARM-UI dashboard.

Operational note: spawn-subagent.sh only prepares the task row and the
composed prompt file. The actual `Agent(...)` dispatch is the
conductor's job (it tails the new pending row in its tmux loop). The
API surfaces the task_id immediately so the UI can route to the detail
page, where the next heartbeat lands within seconds.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from farm_api.config import Settings

router = APIRouter(tags=["writes"])

# Timeouts (seconds). Spawn includes a worktree creation + remote fetch,
# so we give it a generous budget; kill and cleanup are local-only.
_SPAWN_TIMEOUT_S = 90
_KILL_TIMEOUT_S = 30
_CLEANUP_TIMEOUT_S = 120


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
    # Either pick the next slice from the plan...
    next_pickable: bool = Field(
        default=False,
        description="When true, resolve the next pickable slice via "
        "plan-progress.sh --next and dispatch the loop's default agent.",
    )
    # ...or explicitly name the agent + task spec.
    agent: str | None = Field(
        default=None,
        description="Agent yaml name (e.g. 'executor'). Required when "
        "next_pickable=false.",
    )
    task: str | None = Field(
        default=None,
        description="Slice id passed as 'task' inside the spec JSON. "
        "Used when next_pickable=false.",
    )
    args: dict[str, Any] | None = Field(
        default=None,
        description="Extra fields merged into the spec JSON. The 'task' "
        "key takes precedence over a duplicate inside args.",
    )


class SpawnResponse(BaseModel):
    task_id: str
    worktree: str | None = None
    repo: str | None = None
    model: str | None = None
    composed_prompt: str | None = None
    results_dir: str | None = None
    slice_id: str | None = None
    loop: str | None = None
    agent: str


class KillResponse(BaseModel):
    task_id: str
    killed: bool
    stdout: str


class CleanupRequest(BaseModel):
    apply: bool = Field(
        default=False,
        description="False (default) runs cleanup.sh in report-only mode. "
        "True passes --apply to actually remove orphan worktrees / "
        "tmux windows.",
    )


class CleanupResponse(BaseModel):
    apply: bool
    stdout: str


# Loop -> default agent. Matches the conductor's convention: each loop
# has one "lead" agent for the most common slice family. Operators who
# need a different agent for a specific slice still drive it explicitly
# (next_pickable=false + agent=<name> + task=<slice id>).
_DEFAULT_AGENT_FOR_LOOP: dict[str, str] = {
    "farm-platform": "executor",
    "bioinfo-quick": "executor",
    "executor": "executor",
    "thesis-writer": "thesis-writer",
    "doc-writer": "doc-writer",
}


def _run_script(
    settings: Settings,
    script_name: str,
    argv: list[str],
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    """Run a bash script under scripts_path with AGENT_FARM_ROOT wired in.

    Returns the CompletedProcess so callers can inspect stdout / stderr
    / returncode. Raises HTTPException(503) when the script file is
    missing (deployment misconfig) and HTTPException(504) on timeout.
    """
    script_path = settings.scripts_path / script_name
    if not script_path.is_file():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"script not found: {script_path}",
        )
    env = {**os.environ, "AGENT_FARM_ROOT": str(settings.farm_root)}
    try:
        return subprocess.run(  # noqa: S603  (argv is constructed locally)
            ["bash", str(script_path), *argv],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT,
            f"{script_name} timed out after {timeout_s}s",
        ) from e


def _parse_spawn_stdout(stdout: str) -> dict[str, str]:
    """Parse spawn-subagent.sh K=V stdout lines into a dict.

    The script emits one ``key=value`` per line. Lines without ``=`` are
    silently ignored so log-style chatter does not break the parser.
    """
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            out[key] = value.strip()
    return out


def _resolve_next_pickable(
    settings: Settings,
) -> tuple[str, str, str]:
    """Return (agent, slice_id, loop) for the next pickable slice.

    Uses plan-progress.sh --next --json so the resolver is identical to
    the conductor's. Raises HTTPException(404) when no slice is pickable.
    """
    res = _run_script(
        settings,
        "plan-progress.sh",
        ["--next", "--json"],
        _SPAWN_TIMEOUT_S,
    )
    if res.returncode != 0:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"plan-progress.sh failed (rc={res.returncode}): "
            f"{(res.stderr or res.stdout).strip()[:400]}",
        )
    try:
        payload = json.loads(res.stdout or "null")
    except json.JSONDecodeError as e:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"plan-progress.sh --json returned non-JSON: {e}",
        ) from e
    if not payload:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "no pickable slice; every loop has blocked / done / "
            "human-required slices only",
        )
    slice_id = str(payload.get("id") or "").strip()
    loop = str(payload.get("loop") or "").strip()
    if not slice_id or not loop:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"plan-progress.sh --next returned malformed payload: {payload!r}",
        )
    agent = _DEFAULT_AGENT_FOR_LOOP.get(loop, "executor")
    return agent, slice_id, loop


@router.post(
    "/spawn",
    response_model=SpawnResponse,
    summary="Spawn a subagent (next pickable or explicit)",
)
def spawn(
    body: SpawnRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(require_auth)],
) -> SpawnResponse:
    slice_id: str | None = None
    loop: str | None = None
    if body.next_pickable:
        agent, slice_id, loop = _resolve_next_pickable(settings)
        task = slice_id
    else:
        if not body.agent:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "agent is required when next_pickable is false",
            )
        if not body.task:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "task is required when next_pickable is false",
            )
        agent = body.agent
        task = body.task

    spec: dict[str, Any] = {}
    if body.args:
        spec.update(body.args)
    spec["task"] = task

    spec_json = json.dumps(spec, sort_keys=True)
    res = _run_script(
        settings,
        "spawn-subagent.sh",
        [agent, spec_json],
        _SPAWN_TIMEOUT_S,
    )
    if res.returncode != 0:
        # spawn-subagent.sh prints diagnostic info to stderr; surface
        # it verbatim so the UI can display a real reason.
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"spawn-subagent.sh failed (rc={res.returncode}): "
            f"{(res.stderr or res.stdout).strip()[:400]}",
        )
    parsed = _parse_spawn_stdout(res.stdout)
    task_id = parsed.get("task_id")
    if not task_id:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"spawn-subagent.sh produced no task_id; stdout={res.stdout!r}",
        )
    return SpawnResponse(
        task_id=task_id,
        worktree=parsed.get("worktree") or None,
        repo=parsed.get("repo") or None,
        model=parsed.get("model") or None,
        composed_prompt=parsed.get("composed_prompt") or None,
        results_dir=parsed.get("results_dir") or None,
        slice_id=slice_id,
        loop=loop,
        agent=agent,
    )


# Task ids are conductor-generated and shaped like
# ``<agent>-<unix-ts>-<hex4>``. The shell allowlist is strict so an
# unsanitised id can never escape into a shell argument.
_TASK_ID_OK_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def _safe_task_id(task_id: str) -> str:
    if not task_id or len(task_id) > 128:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid task_id")
    if any(c not in _TASK_ID_OK_CHARS for c in task_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid task_id")
    return task_id


@router.post(
    "/tasks/{task_id}/kill",
    response_model=KillResponse,
    summary="Kill a running task",
)
def kill_task(
    task_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(require_auth)],
) -> KillResponse:
    tid = _safe_task_id(task_id)
    res = _run_script(settings, "kill.sh", [tid], _KILL_TIMEOUT_S)
    if res.returncode != 0:
        # kill.sh exits non-zero on "task not found" (die ...). Map to 404.
        msg = (res.stderr or res.stdout).strip()
        if "task not found" in msg.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, msg[:400])
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"kill.sh failed (rc={res.returncode}): {msg[:400]}",
        )
    return KillResponse(task_id=tid, killed=True, stdout=res.stdout)


@router.post(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Run the cleanup sweep (orphan worktrees + crashed tasks)",
)
def cleanup(
    body: CleanupRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(require_auth)],
) -> CleanupResponse:
    argv: list[str] = ["--apply"] if body.apply else []
    res = _run_script(settings, "cleanup.sh", argv, _CLEANUP_TIMEOUT_S)
    if res.returncode != 0:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"cleanup.sh failed (rc={res.returncode}): "
            f"{(res.stderr or res.stdout).strip()[:400]}",
        )
    return CleanupResponse(apply=body.apply, stdout=res.stdout)
