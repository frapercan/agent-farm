---
name: db.py
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/db.py
runbook: docs/features/README.md
smoke: python3 -c "import sys; sys.path.insert(0, 'scripts/lib'); import db"
---

# db.py

Single Python entry point for all sqlite reads + writes against
`state/tasks.sqlite`. Exposes `init`, `heartbeat`, `set_started`,
`set_ended`, `set_metrics`, `record_event`, `list_tasks`, etc. Used by
every script that touches state.

## Source coordinates

- `scripts/lib/db.py`

## State

working. Tested via `tests/test_db_events.py`,
`tests/test_db_set_metrics.py`, `tests/test_events_schema.py`.

## Smoke test

```bash
python3 scripts/lib/db.py --help 2>&1 | head -10
python3 -m pytest tests/test_db_events.py tests/test_db_set_metrics.py -q
```

## Runbook

- CLI: `python3 scripts/lib/db.py heartbeat <task_id> <level> <msg>`.
- Library: imported by `scripts/lib/events_view.py`, `scripts/cleanup.sh`,
  `scripts/finalize-subagent.sh`, etc.

## Current owner

agent-farm conductor loop.
