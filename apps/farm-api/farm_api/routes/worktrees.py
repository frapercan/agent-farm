"""/worktrees endpoint.

Lists worktree directories under FARM_API_WORKTREES (default
~/Thesis2/worktrees) with their on-disk size. Sizes come from `du -sb`
because Python's os.walk + stat on a deep git-worktree tree is many
seconds slower than the C-implemented du. The result is cached for 30
seconds in-process to absorb dashboard polling.

If the worktrees dir is missing the endpoint returns an empty list (not
a 503). That makes the dashboard render gracefully on a fresh farm
that hasn't spawned anything yet.
"""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from farm_api.config import Settings
from farm_api.schemas import WorktreeInfo

router = APIRouter(prefix="/worktrees", tags=["worktrees"])

_CACHE_TTL_S = 30.0
_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, list[WorktreeInfo]]] = {}


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _du_bytes(path: Path) -> int | None:
    """Return the size of `path` in bytes via `du -sb`. Returns None if
    du is unavailable or the path vanished mid-run (race with cleanup).
    """
    try:
        result = subprocess.run(
            ["du", "-sb", str(path)],
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    first = result.stdout.split("\t", 1)[0].strip()
    if not first.isdigit():
        return None
    return int(first)


def _scan(worktrees_path: Path) -> list[WorktreeInfo]:
    if not worktrees_path.is_dir():
        return []
    out: list[WorktreeInfo] = []
    for entry in sorted(worktrees_path.iterdir()):
        if not entry.is_dir():
            continue
        size = _du_bytes(entry)
        out.append(
            WorktreeInfo(
                name=entry.name,
                path=str(entry),
                size_bytes=size,
                exists=entry.exists(),
            )
        )
    return out


@router.get("", response_model=list[WorktreeInfo], summary="List worktrees with size")
def list_worktrees(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[WorktreeInfo]:
    key = str(settings.worktrees_path)
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None and (now - cached[0]) < _CACHE_TTL_S:
            return cached[1]
    fresh = _scan(settings.worktrees_path)
    with _cache_lock:
        _cache[key] = (now, fresh)
    return fresh


def _clear_cache_for_tests() -> None:
    with _cache_lock:
        _cache.clear()
