---
name: farm-api
section: "13-apps"
state: working
owner: agent-farm conductor loop
source:
  - apps/farm-api/farm_api/
  - apps/farm-api/pyproject.toml
  - apps/farm-api/tests/
runbook: docs/runbook-farm-api.md
smoke: cd apps/farm-api && poetry run pytest -q
---

# farm-api

Read-only HTTP API over `state/tasks.sqlite`. Used by the PROTEA Next.js
app `/en/farm/` routes for the dashboard (timeline, jobs widget, status
pill). FastAPI under uvicorn.

## Source coordinates

- `apps/farm-api/farm_api/app.py`
- `apps/farm-api/farm_api/routes/`
- `apps/farm-api/farm_api/db.py`
- `apps/farm-api/farm_api/schemas.py`
- `apps/farm-api/pyproject.toml`
- `apps/farm-api/tests/`

## State

working.

## Smoke test

```bash
cd apps/farm-api && poetry install --no-root && poetry run pytest -q
# Or, just compile:
python3 -c "
import importlib.util, pathlib
p = pathlib.Path('apps/farm-api/farm_api/app.py')
spec = importlib.util.spec_from_file_location('app', p)
assert spec is not None
"
```

## Runbook

- `docs/runbook-farm-api.md` for boot / probe / debug.
- Writes go through `writes.py` only; the public surface stays read-only.

## Current owner

agent-farm conductor loop.
