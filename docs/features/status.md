---
name: status
section: "4-lifecycle"
state: working
owner: agent-farm conductor loop
source:
  - scripts/status.sh
  - scripts/lib/events_view.py
runbook: docs/features/README.md
smoke: bash scripts/status.sh --help 2>&1 | head -5
---

# status

Prints the live farm state: running tasks, their heartbeats, recent
events. `--events` joins the events table (FARM-2.1); `--all` shows the
last 24h history; `<task_id>` zooms into one task.

## Source coordinates

- `scripts/status.sh`
- `scripts/lib/db.py` (read path)
- `scripts/lib/events_view.py`

## State

working.

## Smoke test

```bash
bash -n scripts/status.sh
bash scripts/status.sh 2>&1 | head -3
python3 -m pytest tests/test_status_events_flag.py -q
```

## Runbook

- `bash scripts/status.sh` → live tasks tabla.
- `bash scripts/status.sh --events` → recent events.
- `bash scripts/status.sh <task_id>` → detail.
- `bash scripts/status.sh --all` → 24h history.

## Current owner

agent-farm conductor loop.
