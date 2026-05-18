---
name: launch-conductor
section: "2-conductor"
state: working
owner: agent-farm conductor loop
source:
  - scripts/launch-conductor.sh
runbook: docs/features/conductor.md
smoke: bash -n scripts/launch-conductor.sh
---

# launch-conductor

Boots the conductor in a dedicated tmux session (`agent-farm:conductor`).
Idempotent: if the window already exists, no-op. Sets autoyes mode from
`AGENT_FARM_AUTOYES` (default `1` = bypass).

## Source coordinates

- `scripts/launch-conductor.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/launch-conductor.sh
# Idempotency check
tmux list-windows -t agent-farm 2>/dev/null | grep -c conductor || echo 0
```

## Runbook

- Switch autoyes mode: `tmux kill-window -t agent-farm:conductor && AGENT_FARM_AUTOYES=accept bash scripts/launch-conductor.sh`.
- Subagents inherit the conductor's permission mode; headless agents
  always run with bypassPermissions per their yaml.

## Current owner

agent-farm conductor loop.
