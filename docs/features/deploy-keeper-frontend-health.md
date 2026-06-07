---
name: deploy-keeper-frontend-health
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/lib/protea_redeploy.sh
related: docs/features/deploy-keeper-tick.md
---

# deploy-keeper frontend health gate (FARM-DEPLOY.1)

Detects and recovers a downed Next.js frontend (:3000) after a redeploy
or any other event that leaves the API and workers up but the frontend
process dead. Without this gate, `protea.ngrok.app` returns 502 while
`/health` returns 200.

## Problem (2026-06-07)

`protea_redeploy.sh` health-checks only the worker pid files and the
`/jobs` API endpoint. `deploy.sh` starts all processes including the
frontend, but the frontend Node process can crash or fail to start
independently. The existing code explicitly documented: "Does NOT touch
the API or frontend pid file." After a develop-merge-triggered redeploy,
API and workers came back but the frontend stayed down.

## Fix

Four functions added to `scripts/services/lib/protea_redeploy.sh`:

| Function | Role |
|---|---|
| `is_frontend_healthy()` | Probes `$PROTEA_FRONTEND_URL` (default `http://localhost:3000`); returns 0 on success |
| `frontend_healthcheck_failed_debounce()` | Persistent miss counter; returns 0 only when threshold is breached |
| `frontend_healthcheck_reset_debounce()` | Clears the miss counter on a successful probe |
| `recover_frontend()` | Starts the Next.js process the same way `manage.sh [9]` does: `node .next/standalone/server.js` when the standalone build exists, else `npm run start`. Writes the pid to `logs/pids/frontend.pid`. |
| `ensure_frontend_up()` | Orchestrates probe + debounce + recovery; emits heartbeat via `self_heal_heartbeat` |

`ensure_frontend_up` is called in two places in `protea_redeploy.sh`:
- After a successful `deploy.sh` run (exit code 10 path), after a 4-second wait.
- On the noop path (nothing changed, exit code 0), so even when PROTEA is
  already on tip the gate catches a frontend that went down between ticks.

## Debounce

Three env-configurable knobs (mirror the API debounce pattern):

| Variable | Default | Meaning |
|---|---|---|
| `PROTEA_FRONTEND_MISS_THRESHOLD` | `2` | Consecutive misses before recovery |
| `PROTEA_FRONTEND_MISS_STATE` | `$AGENT_FARM_ROOT/state/deploy_keeper_frontend_miss_count` | Persistent counter file |
| `PROTEA_FRONTEND_URL` | `http://localhost:3000` | URL to probe |

A single brief outage (e.g. during `manage.sh restart`) does not trigger
recovery; only two consecutive misses do. The counter resets on any
successful probe.

## Tests

`tests/test_deploy_keeper_frontend_health.sh` (25 assertions):

- `is_frontend_healthy` returns non-zero when nothing listens
- `is_frontend_healthy` returns 0 when mock server is up
- First miss stays in grace window (rc 1)
- Second consecutive miss breaches threshold (rc 0)
- `frontend_healthcheck_reset_debounce` clears counter
- `recover_frontend` writes pid file and returns 0
- `ensure_frontend_up` resets counter on healthy frontend
- `ensure_frontend_up` defers recovery in grace window
- `ensure_frontend_up` triggers recovery after threshold breach

`tests/test_deploy_keeper_frontend_health_pyshim.py` wraps the bash test
for the pytest sweep.
