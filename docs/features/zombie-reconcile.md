---
name: zombie-reconcile
section: "4-lifecycle"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/zombie_reconcile.py
  - tests/test_zombie_reconcile.py
runbook: docs/features/cleanup.md
smoke: python3 -m pytest tests/test_zombie_reconcile.py -q
---

# zombie-reconcile

Reconciles sqlite task state with reality: tasks whose `status=running`
but whose tmux window + supervisor pid are both gone are flagged as
`crashed` so cleanup can GC them. Called by `cleanup.sh`.

## Source coordinates

- `scripts/lib/zombie_reconcile.py`

## State

working.

## Smoke test

```bash
python3 -m pytest tests/test_zombie_reconcile.py -q
```

## Runbook

- Invoked by `cleanup.sh`; not usually called directly.

## Current owner

agent-farm conductor loop.
