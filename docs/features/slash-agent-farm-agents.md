---
name: /agent-farm-agents
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-agents.md
runbook: docs/features/README.md
smoke: test -s commands/agent-farm-agents.md
---

# /agent-farm-agents

Slash command that lists the registered agent types
(`ls agents/*.yaml`).

## Source coordinates

- `commands/agent-farm-agents.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-agents.md && echo OK
```

## Runbook

- `/agent-farm-agents` → tabla of agent types.

## Current owner

agent-farm conductor loop.
