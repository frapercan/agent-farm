---
name: schema.sql
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - state/schema.sql
  - state/migrations/001_events.sql
  - state/migrations/002_task_metadata.sql
runbook: docs/features/README.md
smoke: test -s state/schema.sql
---

# schema.sql

Single source of truth for the runtime state schema. Tables: `tasks`,
`heartbeats`, `results`. Migrations live under `state/migrations/` and
are applied by `apply_migrations.py`.

## Source coordinates

- `state/schema.sql`
- `state/migrations/001_events.sql` (events table, FARM-2.1)
- `state/migrations/002_task_metadata.sql` (worktree_owner_repo +
  sha_before/after, FARM-2.3 + FARM-2.4)

## State

working.

## Smoke test

```bash
test -s state/schema.sql && echo OK
python3 -m pytest tests/test_events_schema.py tests/test_migration_002.py -q
```

## Runbook

- Edit `state/schema.sql` only for genuinely new tables; otherwise add a
  numbered migration under `state/migrations/`.

## Current owner

agent-farm conductor loop.
