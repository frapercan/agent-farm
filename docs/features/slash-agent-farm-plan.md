---
name: /agent-farm-plan
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-plan.md
runbook: docs/features/plan-progress.md
smoke: test -s commands/agent-farm-plan.md
---

# /agent-farm-plan

Slash command wrapper around `scripts/plan-progress.sh`. Used by the
conductor and operator to read the plan state and pick the next slice.

## Source coordinates

- `commands/agent-farm-plan.md`

## State

working.

## Smoke test

```bash
test -s commands/agent-farm-plan.md && echo OK
```

## Runbook

- `/agent-farm-plan` → all loops, all slices.
- `/agent-farm-plan --phase F-FEAT` → one phase.
- `/agent-farm-plan --next` → highest-priority pickable slice.

## Current owner

agent-farm conductor loop.
