---
name: /agent-farm-status
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-status.md
runbook: docs/features/status.md
smoke: test -s commands/agent-farm-status.md
---

# /agent-farm-status

Slash command wrapper around `scripts/status.sh`.

## Source coordinates

- `commands/agent-farm-status.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-status.md && echo OK
```

## Runbook

- `/agent-farm-status` → live tasks.
- `/agent-farm-status <task_id>` → detail.
- `/agent-farm-status --all` → 24h history.

## Current owner

agent-farm conductor loop.
