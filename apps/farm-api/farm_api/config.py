"""Runtime configuration for farm-api.

Settings are read from env vars at create_app() time. The config object
is intentionally tiny: there is no secret store, no profile system, just
a frozen dataclass that the rest of the app reads from.

Env vars:
  FARM_API_DB           Path to the tasks.sqlite file. Defaults to
                        $AGENT_FARM_ROOT/state/tasks.sqlite, or
                        ~/Thesis2/agent-farm/state/tasks.sqlite if neither
                        is set.
  FARM_API_WRITE        "1" enables the (scaffolded) write endpoints.
                        Anything else keeps them off (404 not exposed).
  FARM_API_AUTH_TOKEN   Shared-secret matched against the X-Farm-Token
                        header on write endpoints. Mandatory when writes
                        are enabled; the app refuses to register write
                        routes if it is unset.
  FARM_API_WORKTREES    Path to the worktrees directory. Defaults to
                        ~/Thesis2/worktrees.
  FARM_API_PLANS        Path to the plans directory. Defaults to
                        $AGENT_FARM_ROOT/plans.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_farm_root() -> Path:
    raw = os.environ.get("AGENT_FARM_ROOT")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "Thesis2" / "agent-farm"


@dataclass(frozen=True)
class Settings:
    db_path: Path
    worktrees_path: Path
    plans_path: Path
    write_enabled: bool
    auth_token: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        root = _default_farm_root()
        db_env = os.environ.get("FARM_API_DB")
        db_path = Path(db_env).expanduser() if db_env else root / "state" / "tasks.sqlite"

        wt_env = os.environ.get("FARM_API_WORKTREES")
        worktrees_path = (
            Path(wt_env).expanduser() if wt_env
            else Path.home() / "Thesis2" / "worktrees"
        )

        plans_env = os.environ.get("FARM_API_PLANS")
        plans_path = Path(plans_env).expanduser() if plans_env else root / "plans"

        write_enabled = os.environ.get("FARM_API_WRITE", "") == "1"
        auth_token = os.environ.get("FARM_API_AUTH_TOKEN") or None

        return cls(
            db_path=db_path,
            worktrees_path=worktrees_path,
            plans_path=plans_path,
            write_enabled=write_enabled,
            auth_token=auth_token,
        )
