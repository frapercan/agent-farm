---
name: init-sqlite
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/init.sh
  - state/schema.sql
runbook: docs/features/README.md
smoke: bash -n scripts/init.sh
---

# init-sqlite

Boots `state/tasks.sqlite` from `state/schema.sql`. Idempotent: WAL mode,
foreign keys on, `IF NOT EXISTS` everywhere. Also runs every pending
migration under `state/migrations/`.

## Source coordinates

- `scripts/init.sh`
- `state/schema.sql`
- `state/migrations/*.sql`
- `scripts/lib/apply_migrations.py`

## State

working.

## Smoke test

```bash
bash -n scripts/init.sh
python3 -c "from scripts.lib.db import init_schema; init_schema()"  # if importable
```

## Runbook

- Run once per workstation: `bash scripts/init.sh`.
- Re-run after pulling a new migration; idempotent.
- State + results dirs are gitignored.

## Current owner

agent-farm conductor loop.
