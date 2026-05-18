---
name: deploy-keeper
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/deploy-keeper.yaml
  - prompts/deploy-keeper.md
  - scripts/services/deploy-keeper-supervisor.sh
  - scripts/services/deploy-keeper-tick.sh
runbook: docs/features/deploy-keeper-supervisor.md
smoke: bash scripts/services/deploy-keeper-tick.sh --dry-run
---

# deploy-keeper

Persistent headless agent that keeps `origin/develop` deployed on the
configured tunnel. Bash supervisor + tick model: the supervisor polls;
Claude is invoked only on a fail-kind escalation. Haiku because the
escalations are short.

## Source coordinates

- `agents/deploy-keeper.yaml` (kind: headless, persistent: true)
- `prompts/deploy-keeper.md`
- `scripts/services/deploy-keeper-supervisor.sh`
- `scripts/services/deploy-keeper-tick.sh`
- `state/logs/deploy-keeper.log`

## State

working. Operational landmines tracked in memory
`project_deploy_keeper_hang_2026_05_18` (noop-on-SHA hang) and
`feedback_deploy_keeper_bootstrap` (missing worktree bootstrap).

## Smoke test

```bash
# Verify the supervisor parses its yaml cleanly
bash scripts/lib/yaml_parse.sh agents/deploy-keeper.yaml service.poll_interval

# Tick dry-run (does not deploy)
DEPLOY_KEEPER_DRY_RUN=1 bash scripts/services/deploy-keeper-tick.sh
```

## Runbook

- `docs/runbook-branch-protection.md` for the surrounding deploy rules.
- Kill + respawn pattern: `bash scripts/kill.sh <task_id> && bash scripts/spawn.sh deploy-keeper`.

## Current owner

agent-farm conductor loop. Stack is process-based (uvicorn + workers +
next + ngrok), NOT docker compose.
