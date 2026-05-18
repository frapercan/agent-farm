---
name: deploy-keeper-supervisor
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/deploy-keeper-supervisor.sh
  - scripts/services/deploy-keeper-tick.sh
  - scripts/services/deploy-keeper-trigger.sh
runbook: docs/features/deploy-keeper.md
smoke: bash -n scripts/services/deploy-keeper-supervisor.sh
---

# deploy-keeper-supervisor

Persistent bash supervisor that ticks at `service.poll_interval` from the
agent yaml. Each tick runs `deploy-keeper-tick.sh`, which decides whether
to redeploy. On fail-kind, the supervisor escalates by spawning a Claude
session.

Between ticks the supervisor evaluates the yaml `service.triggers` list
on a `TRIGGER_CHECK_INTERVAL_SEC` cadence (default 60s, independent of
`poll_interval`) and short-circuits the nap when a trigger fires:

- `new_commit_on:<ref>` (git fetch + rev-parse against the PROTEA
  repo, no polling of the deploy worktree). The first sighting arms;
  a subsequent SHA delta fires.
- `ngrok_tunnel_down` (curl -sfI against `NGROK_PROBE_URL`, default
  `https://protea.ngrok.app/`). A `NGROK_BACKOFF_SEC` floor between
  consecutive fires prevents a long outage from spamming ticks.
- `manual` (marker file at `MANUAL_TRIGGER_FILE`, default
  `/tmp/deploy-keeper-manual-trigger`). Conductor and the dashboard
  CommandPalette write this via `scripts/services/deploy-keeper-trigger.sh`.

## Source coordinates

- `scripts/services/deploy-keeper-supervisor.sh`
- `scripts/services/deploy-keeper-tick.sh`
- `scripts/services/deploy-keeper-trigger.sh`
- `scripts/lib/yaml_parse.sh` (parses service.poll_interval)
- `scripts/lib/common.sh` (yaml_get for service.triggers list)

## State

working. FARM-FEAT.4 (2026-05-18) made `service.triggers` load-bearing:
the field drives the trigger evaluator above. Out-of-scope (still): a
generic supervisor factory, tracked under FARM-FEAT.6.

## Smoke test

```bash
bash -n scripts/services/deploy-keeper-supervisor.sh
bash -n scripts/services/deploy-keeper-tick.sh
bash -n scripts/services/deploy-keeper-trigger.sh
python3 -m pytest tests/test_deploy_keeper_escalation.py -q
bash tests/test_deploy_keeper_triggers.sh
```

## Runbook

- Spawn: `bash scripts/spawn.sh deploy-keeper`.
- Logs: `state/logs/deploy-keeper.log`.
- Force a tick (manual trigger):
  `bash scripts/services/deploy-keeper-trigger.sh "<reason>"`.
- Memory: `project_deploy_keeper_hang_2026_05_18` (noop-on-SHA hang;
  kill+respawn pattern).

## Current owner

agent-farm conductor loop.
