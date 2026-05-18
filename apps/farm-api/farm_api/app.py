"""FastAPI app construction for farm-api.

`create_app()` returns a fully wired app and is the only public
constructor. Tests build a fresh instance per fixture (overriding
settings via env vars before the call) while the uvicorn entry-point
goes through the module-level singleton in __init__.py.

Write endpoints are only registered when BOTH `FARM_API_WRITE=1` and
`FARM_API_AUTH_TOKEN` are set. Either alone is treated as a misconfig:
the routes stay unregistered, the rest of the API still works, and the
operator sees a warning on the /healthz response.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from farm_api.config import Settings
from farm_api.routes import agents, cost, events, plan, tasks, worktrees

log = logging.getLogger("farm_api")

API_TITLE = "agent-farm API"
API_DESCRIPTION = (
    "Read-only HTTP surface over agent-farm state.sqlite. Powers the "
    "Next.js dashboard (FARM-UI.2+). Write endpoints are scaffolded "
    "and return 501 in v1; enable them with FARM_API_WRITE=1 + "
    "FARM_API_AUTH_TOKEN for forward-compatibility testing."
)
API_VERSION = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
    )
    app.state.settings = settings

    # Read-only routes are always mounted.
    app.include_router(tasks.router)
    app.include_router(events.router)
    app.include_router(plan.router)
    app.include_router(cost.router)
    app.include_router(worktrees.router)
    app.include_router(agents.router)

    # Write routes: only attached when fully configured. A bare
    # FARM_API_WRITE=1 without a token is treated as misconfig.
    writes_status: dict[str, Any] = {"enabled": False, "reason": "FARM_API_WRITE not set"}
    if settings.write_enabled:
        if not settings.auth_token:
            writes_status = {
                "enabled": False,
                "reason": "FARM_API_WRITE=1 but FARM_API_AUTH_TOKEN unset; "
                          "write routes refused for safety",
            }
            log.warning(writes_status["reason"])
        else:
            from farm_api.writes import router as writes_router  # noqa: PLC0415

            app.include_router(writes_router)
            writes_status = {"enabled": True, "reason": None}

    @app.get("/healthz", tags=["meta"], summary="Liveness probe")
    def healthz() -> dict:
        return {
            "ok": True,
            "db_path": str(settings.db_path),
            "db_present": settings.db_path.is_file(),
            "worktrees_path": str(settings.worktrees_path),
            "plans_path": str(settings.plans_path),
            "writes": writes_status,
            "version": API_VERSION,
        }

    return app
