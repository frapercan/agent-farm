"""/agents endpoint.

Reads the agent specs from ``<AGENT_FARM_ROOT>/agents/*.yaml`` and surfaces
the per-agent cost budget so the dashboard can overlay an actual-vs-budget
view next to the spend rollup served by /cost.

The catalog under agents/ is the source of truth for advisory daily spend
caps (``cost_budget.max_usd_per_day``). Reading it from the sidecar keeps
the dashboard decoupled from the bash launchers that act on the same
budgets.

The endpoint silently skips files that do not parse as YAML mapping (the
``_template.yaml`` placeholder is included by name so the operator can
inspect the default budget directly).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Depends, Request

from farm_api.config import Settings
from farm_api.schemas import AgentBudget

router = APIRouter(prefix="/agents", tags=["agents"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _coerce_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _coerce_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _parse_agent(path: Path) -> AgentBudget | None:
    """Parse a single agent yaml. Returns None when the file is unreadable
    or its top-level is not a mapping. Missing fields fall back to None
    so the dashboard can render "(no cap)" without surfacing an error.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    name = raw.get("name") or path.stem
    if not isinstance(name, str):
        return None
    cost_budget = raw.get("cost_budget") or {}
    if not isinstance(cost_budget, dict):
        cost_budget = {}
    return AgentBudget(
        name=name,
        kind=raw.get("kind") if isinstance(raw.get("kind"), str) else None,
        model=raw.get("model") if isinstance(raw.get("model"), str) else None,
        expected_tokens=_coerce_int(cost_budget.get("expected_tokens")),
        max_usd_per_day=_coerce_float(cost_budget.get("max_usd_per_day")),
    )


def _agents_dir(settings: Settings) -> Path:
    """Resolve the agents directory next to the plans directory.

    Both plans and agents live at the farm-root level; deriving agents
    from ``farm_root`` keeps the wiring tight even if the operator
    overrides FARM_API_PLANS to a non-default path.
    """
    return settings.farm_root / "agents"


@router.get(
    "/budgets",
    response_model=list[AgentBudget],
    summary="Per-agent advisory cost budgets",
)
def list_agent_budgets(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[AgentBudget]:
    agents_dir = _agents_dir(settings)
    if not agents_dir.is_dir():
        return []
    out: list[AgentBudget] = []
    for entry in sorted(agents_dir.iterdir()):
        if entry.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if not entry.is_file():
            continue
        parsed = _parse_agent(entry)
        if parsed is not None:
            out.append(parsed)
    return out
