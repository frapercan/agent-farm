---
name: restore-drill
section: "11-backup-recovery"
state: working
owner: agent-farm conductor loop
source:
  - scripts/restore-drill.sh
  - scripts/install-restore-drill-cron.sh
runbook: docs/runbook-pg-volume-recovery.md
smoke: bash -n scripts/restore-drill.sh
---

# restore-drill

Weekly drill that restores the latest `pg_dump` into a throwaway
postgres container, runs `alembic upgrade head`, asserts a smoke query
returns >0 rows. Heartbeat on success, escalation on failure.

## Source coordinates

- `scripts/restore-drill.sh`
- `scripts/install-restore-drill-cron.sh`

## State

working. Tested via `tests/test_restore_drill.sh` +
`tests/test_restore_drill_pyshim.py`.

## Smoke test

```bash
bash -n scripts/restore-drill.sh
bash -n scripts/install-restore-drill-cron.sh
python3 -m pytest tests/test_restore_drill_pyshim.py -q
```

## Runbook

- Install drill cron: `bash scripts/install-restore-drill-cron.sh`.
- On drill failure → manual recovery via
  `docs/runbook-pg-volume-recovery.md`.

## Current owner

agent-farm conductor loop.
