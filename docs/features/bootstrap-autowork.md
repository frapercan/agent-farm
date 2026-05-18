---
name: bootstrap-autowork
section: "2-conductor"
state: working
owner: agent-farm conductor loop
source:
  - prompts/bootstrap-autowork.md
runbook: docs/features/conductor.md
smoke: test -s prompts/bootstrap-autowork.md
---

# bootstrap-autowork

Boot-time loop the conductor follows after loading its system prompt:
read farm state, parse plan progress, pick the next pickable slice across
loops, spawn the appropriate agent. The loop is non-interactive: the
operator only intervenes on policy decisions.

## Source coordinates

- `prompts/bootstrap-autowork.md`

## State

working.

## Smoke test

```bash
test -s prompts/bootstrap-autowork.md && echo OK
```

## Runbook

- Loaded automatically by `/agent-farm-conductor`.
- Pairs with `plan-progress.sh --next` to surface the next slice.

## Current owner

agent-farm conductor loop.
