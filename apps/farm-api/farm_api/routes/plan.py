"""/plan endpoint.

Reads plans/<loop>/PLAN.md files via the existing plan_parser module
under scripts/lib/. The parser is imported lazily by injecting the
scripts/lib path so we do not promote it to a package dependency. If the
parser cannot be located we fall back to a tiny inline regex parser.

Query params:
  loop    optional loop name (e.g. "farm-platform"); when omitted, all
          loops are returned
  status  optional filter (pending / in_progress / done / blocked / deferred)
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from farm_api.config import Settings
from farm_api.schemas import PlanSlice

router = APIRouter(prefix="/plan", tags=["plan"])

# Fallback regex if plan_parser is not importable.
_SECTION_RX = re.compile(
    r"^### (.+?)\n```yaml\n(.+?)\n```\n(.*?)(?=^### |\Z)", re.M | re.S
)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _try_import_plan_parser(plans_path: Path) -> Any | None:
    """Try to import scripts/lib/plan_parser.py given the plans path's
    repo root. Returns the module or None if it's not present.
    """
    repo_root = plans_path.parent
    candidate = repo_root / "scripts" / "lib" / "plan_parser.py"
    if not candidate.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_farm_plan_parser", candidate)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_farm_plan_parser", mod)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def _fallback_parse(plans_path: Path) -> list[PlanSlice]:
    """Tiny regex-based parser for the case where scripts/lib/plan_parser
    cannot be imported (e.g. running the sidecar outside the agent-farm
    repo). Only extracts the fields the API exposes.
    """
    out: list[PlanSlice] = []
    if not plans_path.is_dir():
        return out
    for loop_dir in sorted(plans_path.iterdir()):
        if not loop_dir.is_dir():
            continue
        plan_md = loop_dir / "PLAN.md"
        if not plan_md.is_file():
            continue
        text = plan_md.read_text(encoding="utf-8")
        for m in _SECTION_RX.finditer(text):
            title = m.group(1).strip()
            try:
                frontmatter = yaml.safe_load(m.group(2)) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(frontmatter, dict):
                continue
            slice_id = str(frontmatter.get("id") or "").strip()
            if not slice_id:
                continue
            out.append(
                PlanSlice(
                    id=slice_id,
                    title=title,
                    loop=str(frontmatter.get("loop") or loop_dir.name),
                    phase=str(frontmatter.get("phase") or ""),
                    status=str(frontmatter.get("status") or "pending"),
                    deps=list(frontmatter.get("deps") or []),
                    priority=frontmatter.get("priority"),
                    estimated_hours=frontmatter.get("estimated_hours"),
                    tags=list(frontmatter.get("tags") or []),
                    requires_human=bool(frontmatter.get("requires_human") or False),
                    acceptance=frontmatter.get("acceptance"),
                )
            )
    return out


def _slices_from_parser(mod: Any, plans_path: Path) -> list[PlanSlice]:
    """Adapt scripts/lib/plan_parser output to PlanSlice. We tolerate
    several possible attribute names so the API does not break if the
    parser evolves: prefer parser.parse_all(plans_path) -> list of dicts
    or list of dataclass-shaped objects.
    """
    if hasattr(mod, "parse_all"):
        raw = mod.parse_all(plans_path)
    elif hasattr(mod, "load_slices"):
        raw = mod.load_slices(plans_path)
    else:
        return _fallback_parse(plans_path)
    out: list[PlanSlice] = []
    for item in raw:
        if isinstance(item, dict):
            d = item
        else:
            d = {
                k: getattr(item, k, None)
                for k in (
                    "id", "title", "loop", "phase", "status", "deps",
                    "priority", "estimated_hours", "tags", "requires_human",
                    "acceptance",
                )
            }
        try:
            out.append(
                PlanSlice(
                    id=str(d.get("id") or ""),
                    title=str(d.get("title") or ""),
                    loop=str(d.get("loop") or ""),
                    phase=str(d.get("phase") or ""),
                    status=str(d.get("status") or "pending"),
                    deps=list(d.get("deps") or []),
                    priority=d.get("priority"),
                    estimated_hours=d.get("estimated_hours"),
                    tags=list(d.get("tags") or []),
                    requires_human=bool(d.get("requires_human") or False),
                    acceptance=d.get("acceptance"),
                )
            )
        except Exception:
            # Drop malformed entries instead of failing the whole list;
            # the UI shows what is parseable.
            continue
    return out


@router.get("", response_model=list[PlanSlice], summary="List plan slices")
def list_plan(
    settings: Annotated[Settings, Depends(get_settings)],
    loop: str | None = Query(None, description="Restrict to a single loop"),
    status: str | None = Query(None, description="Filter by status"),
) -> list[PlanSlice]:
    if not settings.plans_path.is_dir():
        raise HTTPException(503, f"plans directory missing: {settings.plans_path}")
    parser = _try_import_plan_parser(settings.plans_path)
    slices = (
        _slices_from_parser(parser, settings.plans_path)
        if parser is not None
        else _fallback_parse(settings.plans_path)
    )
    if loop:
        slices = [s for s in slices if s.loop == loop]
    if status:
        slices = [s for s in slices if s.status == status]
    return slices
