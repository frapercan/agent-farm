---
name: deploy-keeper-supervisor
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/deploy-keeper-supervisor.sh
  - scripts/services/deploy-keeper-tick.sh
runbook: docs/features/deploy-keeper.md
smoke: bash -n scripts/services/deploy-keeper-supervisor.sh
---

# deploy-keeper-supervisor

Persistent bash supervisor that ticks at `service.poll_interval` from the
agent yaml. Each tick runs `deploy-keeper-tick.sh`, which decides whether
to redeploy. On fail-kind, the supervisor escalates by spawning a Claude
session.

## Source coordinates

- `scripts/services/deploy-keeper-supervisor.sh`
- `scripts/services/deploy-keeper-tick.sh`
- `scripts/lib/yaml_parse.sh` (parses service.poll_interval)

## State

working. Service.triggers field is currently human-readable only;
FARM-FEAT.4 wires it to be load-bearing (new_commit_on:origin/develop +
ngrok_tunnel_down + manual). The generic supervisor factory is
FARM-FEAT.6.

## Smoke test

```bash
bash -n scripts/services/deploy-keeper-supervisor.sh
bash -n scripts/services/deploy-keeper-tick.sh
python3 -m pytest tests/test_deploy_keeper_escalation.py -q
```

## Runbook

- Spawn: `bash scripts/spawn.sh deploy-keeper`.
- Logs: `state/logs/deploy-keeper.log`.
- Memory: `project_deploy_keeper_hang_2026_05_18` (noop-on-SHA hang;
  kill+respawn pattern).

## Current owner

agent-farm conductor loop.
