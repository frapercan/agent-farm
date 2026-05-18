---
name: /agent-farm-kill
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-kill.md
runbook: docs/features/kill.md
smoke: test -s commands/agent-farm-kill.md
---

# /agent-farm-kill

Slash command wrapper around `scripts/kill.sh`.

## Source coordinates

- `commands/agent-farm-kill.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-kill.md && echo OK
```

## Runbook

- `/agent-farm-kill <task_id>`.

## Current owner

agent-farm conductor loop.
