---
name: deploy-keeper-tick
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/deploy-keeper-tick.sh
runbook: docs/features/deploy-keeper.md
smoke: bash -n scripts/services/deploy-keeper-tick.sh
---

# deploy-keeper-tick

One supervisor tick: fetch origin/develop, compare HEAD vs deployed SHA,
redeploy if different and the worker healthcheck passes. Exits non-zero
with a fail-kind code on escalation.

## Source coordinates

- `scripts/services/deploy-keeper-tick.sh`

## State

working. Tested via
`tests/test_deploy_keeper_worker_healthcheck.sh`,
`tests/test_deploy_keeper_backoff.sh`,
`tests/test_redeploy_self_heal.sh`.

## Smoke test

```bash
bash -n scripts/services/deploy-keeper-tick.sh
bash tests/test_deploy_keeper_worker_healthcheck.sh
```

## Runbook

- Triggered by the supervisor on each `poll_interval`.
- Fail-kinds: `worker_unhealthy`, `redeploy_failed`,
  `tunnel_down`, `disk_full`. Each maps to a different escalation prompt.

## Current owner

agent-farm conductor loop.
