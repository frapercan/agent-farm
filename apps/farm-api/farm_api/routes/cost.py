"""/cost endpoint.

Wraps scripts/lib/cost_report.py to share the aggregation logic with
the CLI runner. We import the module via importlib so farm-api doesn't
need cost_report as a python package; the file is loaded from the
repo path inferred from the db path.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from farm_api.config import Settings
from farm_api.schemas import CostBucket

router = APIRouter(prefix="/cost", tags=["cost"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _load_cost_report(db_path: Path) -> Any | None:
    """Import scripts/lib/cost_report.py from the agent-farm repo whose
    state/tasks.sqlite is db_path. Returns None if the file is not
    reachable (e.g. running the sidecar against a copy of the DB
    outside the farm tree).
    """
    repo_root = db_path.parent.parent  # state/tasks.sqlite -> root
    candidate = repo_root / "scripts" / "lib" / "cost_report.py"
    if not candidate.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_farm_cost_report", candidate)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_farm_cost_report", mod)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


@router.get("", response_model=list[CostBucket], summary="Cost rollup by (date, agent, model)")
def cost_rollup(
    settings: Annotated[Settings, Depends(get_settings)],
    days: int = Query(7, ge=0, le=365),
    agent: str | None = Query(None),
    model: str | None = Query(None),
) -> list[CostBucket]:
    if not settings.db_path.is_file():
        raise HTTPException(503, f"db missing: {settings.db_path}")
    mod = _load_cost_report(settings.db_path)
    if mod is None:
        raise HTTPException(503, "cost_report module not reachable")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.astimezone().isoformat(timespec="seconds")
    rows = mod._load(settings.db_path, cutoff_iso)
    buckets = mod.aggregate(rows, agent_filter=agent, model_filter=model)
    return [CostBucket(**b) for b in buckets]
