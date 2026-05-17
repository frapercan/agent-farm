# Runbook: farm-api sidecar

`apps/farm-api/` is a FastAPI service that exposes read-only views over
`agent-farm/state/tasks.sqlite`. It is the HTTP backend the Next.js
dashboard (FARM-UI.2+) calls. This runbook covers operations: start,
stop, env, auth, troubleshooting.

## Why a sidecar?

The dashboard could shell out to `status.sh` and `cost-report.sh` from
the Next.js server-side handlers, but that path:

1. Couples the UI build to the agent-farm checkout layout.
2. Spawns a Python process per request (cold start about 200 ms).
3. Forces JSON re-parsing of the text-table output.

A long-lived FastAPI process amortises imports, returns clean JSON, and
gives the dashboard a stable OpenAPI contract auto-discoverable at
`/openapi.json`.

## Start

```
cd ~/Thesis2/agent-farm/apps/farm-api
poetry install
poetry run uvicorn farm_api:app `--port 8801`
```

`poetry run python -m farm_api` is the convenience entry-point.

By default uvicorn binds to `127.0.0.1`. To expose through the existing
PROTEA ngrok tunnel set `FARM_API_HOST=0.0.0.0`. The tunnel itself is
configured in PROTEA's `docker-compose.yml`; the sidecar should be
added as an additional `expose` entry there (out of scope for the
FARM-UI.1 slice).

## Verify it's up

```
curl http://localhost:8801/healthz | jq .
```

Expected body keys: `ok` (boolean), `db_path`, `db_present`,
`worktrees_path`, `plans_path`, `writes` (object with `enabled` and
`reason`), and `version`.

## Auth model

The API is split into two tiers:

1. **Read endpoints** (`/tasks`, `/events`, `/plan`, `/cost`,
   `/worktrees`, `/healthz`) are open. The dashboard polls them from
   the browser; no credential required.

2. **Write endpoints** (`/spawn`, `/tasks/{id}/kill`, `/cleanup`)
   require BOTH:
   - `FARM_API_WRITE=1` in the service's environment, AND
   - a non-empty `FARM_API_AUTH_TOKEN` in the same environment.

   Clients must send `X-Farm-Token: <token>` on every write call.
   Missing or wrong token returns **403** (not 401): the routes are
   intentionally indistinguishable from "does not exist" to unauth'd
   callers.

   If only `FARM_API_WRITE=1` is set (no token), the routes are
   **not registered** and `/healthz` reports the misconfig. This is
   defence in depth: forgetting the token cannot accidentally open the
   service.

### Generating a token

```
export FARM_API_AUTH_TOKEN="$(head -c 24 /dev/urandom | base64)"
echo "$FARM_API_AUTH_TOKEN" > ~/.config/farm-api.token
chmod 600 ~/.config/farm-api.token
```

Copy the same value into the Next.js dashboard's `.env.local` as
`FARM_API_TOKEN` so its server-side handlers can forward it.

## v1 write behaviour

Write endpoints are **scaffolded but not implemented** in v1. They
return:

```
HTTP/1.1 501 Not Implemented
Content-Type: application/json

{
  "detail": {
    "error": "not_implemented",
    "runbook": "docs/runbook-farm-api.md",
    "detail": "spawn is scaffolded; v1 returns 501. ...",
    "payload_echo": { ... }
  }
}
```

The 501 with the echoed payload exists so the future Next.js dashboard
team can wire end-to-end forms and assert the round-trip works before
the bodies plug in shell-outs to `scripts/spawn-subagent.sh`,
`scripts/kill.sh`, and `scripts/cleanup.sh`. That plumbing is tracked
under FARM-UI.6 (or its successor) and is intentionally out of scope
for FARM-UI.1 because it pulls in a tmux session, an authz audit log,
and a kill-confirmation flow that deserve their own slice.

## Environment reference

- `AGENT_FARM_ROOT`: defaults to `~/Thesis2/agent-farm`; base for DB plus plans paths.
- `FARM_API_DB`: defaults to `$AGENT_FARM_ROOT/state/tasks.sqlite` (read-only).
- `FARM_API_PLANS`: defaults to `$AGENT_FARM_ROOT/plans`.
- `FARM_API_WORKTREES`: defaults to `~/Thesis2/worktrees`.
- `FARM_API_WRITE`: unset by default; `1` enables scaffolded writes.
- `FARM_API_AUTH_TOKEN`: unset by default; required when writes are enabled.
- `FARM_API_HOST`: defaults to `127.0.0.1` (only used by `python -m farm_api`).
- `FARM_API_PORT`: defaults to `8801` (only used by `python -m farm_api`).

## Troubleshooting

### `/tasks` returns 503

The sqlite file is not present at `FARM_API_DB`. Run
`scripts/init.sh` from the agent-farm root, or point `FARM_API_DB` at
the right path.

### `/cost` returns 503 "cost_report module not reachable"

`scripts/lib/cost_report.py` is not at the expected relative location
(it must sit at `<repo-root>/scripts/lib/cost_report.py` where the
parent of `state/` is `<repo-root>`). This usually means `FARM_API_DB`
is pointing at a copy of the sqlite file outside the agent-farm tree.
Either point at the canonical DB or copy `cost_report.py` to a matching
layout.

### `/worktrees` returns sizes as `null`

`du` is not on `PATH`, or the worktree was removed between the listing
and the size lookup (race with `cleanup.sh`). The endpoint is
intentionally tolerant: `size_bytes: null` means "unknown" rather than
"empty".

### Reads succeed but the dashboard reports stale data

The sidecar opens a fresh sqlite connection per request, so there is
no caching on the read side. The only cache is `/worktrees` (30 s). If
the dashboard is stale, check the dashboard's own SWR / React-Query
revalidation policy, not the API.

## Future Next.js integration

The dashboard repo (PROTEA `apps/web`) should pull `/openapi.json` at
build time and run `openapi-typescript` to generate a typed client:

```
npx openapi-typescript http://localhost:8801/openapi.json -o app/lib/farm-api.d.ts
```

A small wrapper exposes `farmApi.tasks.list({status:"running"})` and
similar helpers. This wrapper is implemented under FARM-UI.2 (the
dashboard slice); the sidecar's contract is the OpenAPI document.

## Limitations

1. **Read-only by default.** Writes are scaffolded but return 501. Full
   write support tracked under FARM-UI.6.
2. **No SSE or WebSocket.** The dashboard polls `/events?since=...`. A
   live-streaming surface is a follow-on.
3. **Single shared-secret auth.** No JWT, no OAuth, no per-user RBAC.
   Adequate for the local-dashboard use case; revisit if the sidecar
   is ever exposed beyond the operator's machine.
4. **No rate limiting.** Polling cost is bounded by the dashboard's
   query interval. Revisit if the API is ever multi-tenant.
5. **No systemd unit.** The runbook intentionally keeps invocation
   manual (`poetry run uvicorn ...`) so the operator notices when the
   sidecar isn't running. A systemd user unit can be added later if
   the dashboard becomes a daily-driver.
