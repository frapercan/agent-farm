# farm-api

FastAPI sidecar exposing read-only views over `agent-farm/state/tasks.sqlite`.
Powers the future Next.js dashboard (FARM-UI.2+).

## Quick start

Install + run:

```
cd apps/farm-api
poetry install
poetry run uvicorn farm_api:app `--port 8801`
```

(`poetry run python -m farm_api` is equivalent.)

Then:

```
curl http://localhost:8801/tasks?status=running
curl http://localhost:8801/events?kind=heartbeat
curl http://localhost:8801/openapi.json
open http://localhost:8801/docs
```

The last URL renders the Swagger UI.

## Tests

```
cd apps/farm-api
poetry run pytest `-q`
```

The suite uses a `tmp_path` sqlite seeded via the real `scripts/lib/db.py`
so the schema cannot drift.

## Endpoints (read-only)

- `GET /tasks` (filters: `status`, `agent`, `since`, `limit`)
- `GET /tasks/{id}` (task detail)
- `GET /tasks/{id}/heartbeats` (newest first)
- `GET /tasks/{id}/results` (404 if not finalised)
- `GET /events` (filters: `kind`, `level`, `task_id`, `since`)
- `GET /plan` (filters: `loop`, `status`)
- `GET /cost` (filters: `days`, `agent`, `model`; reuses `scripts/lib/cost_report.py`)
- `GET /worktrees` (du-aware, 30 s in-process cache)
- `GET /healthz` (liveness plus write-gate status)
- `GET /openapi.json`, `GET /docs` (OpenAPI spec plus Swagger UI)

## Endpoints (write, scaffolded)

Disabled by default. Enable both env vars together:

```
export FARM_API_WRITE=1
export FARM_API_AUTH_TOKEN="$(head -c 24 /dev/urandom | base64)"
```

When enabled, three routes register but currently return **501**:

- `POST /spawn` (will wrap `scripts/spawn-subagent.sh`)
- `POST /tasks/{id}/kill` (will wrap `scripts/kill.sh`)
- `POST /cleanup` (will wrap `scripts/cleanup.sh`)

All write endpoints require the `X-Farm-Token` header to match
`FARM_API_AUTH_TOKEN`. Missing or wrong token returns **403** (not 401):
the routes are intentionally indistinguishable from "does not exist" to
unauthenticated callers.

Full bodies land in the FARM-UI.6 follow-up slice. See
`docs/runbook-farm-api.md` for the migration plan.

## Env vars

- `AGENT_FARM_ROOT`: defaults to `~/Thesis2/agent-farm`; derives DB and plans paths.
- `FARM_API_DB`: defaults to `$AGENT_FARM_ROOT/state/tasks.sqlite` (read-only).
- `FARM_API_PLANS`: defaults to `$AGENT_FARM_ROOT/plans`.
- `FARM_API_WORKTREES`: defaults to `~/Thesis2/worktrees`.
- `FARM_API_WRITE`: unset by default; set to `1` to enable scaffolded writes.
- `FARM_API_AUTH_TOKEN`: unset by default; required when writes are enabled.
- `FARM_API_HOST`: defaults to `127.0.0.1` (used by `python -m farm_api`).
- `FARM_API_PORT`: defaults to `8801` (used by `python -m farm_api`).

## Architecture notes

- The sqlite connection is opened **read-only** (`?mode=ro`) via the URI
  form so the writer (heartbeat / finalize / cleanup) is never blocked.
  WAL mode is set at init time in `scripts/init.sh`.
- `/cost` reuses `scripts/lib/cost_report.py` via `importlib`; the
  rollup math has exactly one implementation.
- `/plan` reuses `scripts/lib/plan_parser.py` when available, with an
  inline regex fallback for the case where the parser is not on disk.
- `/worktrees` shells out to `du `-sb`` (cached 30 s) because pure-Python
  recursive sizing is much slower on git-worktrees with full object DBs.
