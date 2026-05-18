---
name: events-view
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/events_view.py
  - state/migrations/001_events.sql
runbook: docs/features/status.md
smoke: python3 -c "import sys; sys.path.insert(0, 'scripts/lib'); import events_view"
---

# events-view

Append-only event log over `tasks.sqlite`: every lifecycle transition
(spawn, finalize, kill, redeploy, escalation) writes one row. Powers
`status.sh --events` and the dashboard timeline.

## Source coordinates

- `scripts/lib/events_view.py`
- `state/migrations/001_events.sql`

## State

working. Tested via `tests/test_db_events.py`,
`tests/test_status_events_flag.py`.

## Smoke test

```bash
python3 -m pytest tests/test_db_events.py tests/test_status_events_flag.py -q
```

## Runbook

- `bash scripts/status.sh --events` for human view.
- Library access: `from events_view import recent_events`.

## Current owner

agent-farm conductor loop.
