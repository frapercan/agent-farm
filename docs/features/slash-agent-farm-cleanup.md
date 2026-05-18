---
name: /agent-farm-cleanup
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-cleanup.md
runbook: docs/features/cleanup.md
smoke: test -s commands/agent-farm-cleanup.md
---

# /agent-farm-cleanup

Slash command wrapper around `scripts/cleanup.sh --apply`.

## Source coordinates

- `commands/agent-farm-cleanup.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-cleanup.md && echo OK
```

## Runbook

- `/agent-farm-cleanup` → GC orphans.

## Current owner

agent-farm conductor loop.
