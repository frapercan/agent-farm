---
name: /agent-farm-spawn
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-spawn.md
runbook: docs/features/spawn.md
smoke: test -s commands/agent-farm-spawn.md
---

# /agent-farm-spawn

Slash command wrapper around `scripts/spawn.sh` (headless agents) and the
Agent tool (subagents). Reads agent kind from yaml and routes correctly.

## Source coordinates

- `commands/agent-farm-spawn.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-spawn.md && echo OK
```

## Runbook

- `/agent-farm-spawn deploy-keeper`.
- `/agent-farm-spawn executor '{"slice":"FARM-X","phase":"F-X"}'`.

## Current owner

agent-farm conductor loop.
