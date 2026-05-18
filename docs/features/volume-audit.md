---
name: volume-audit
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/volume-audit.service
  - scripts/services/volume-audit-watch.sh
runbook: docs/runbook-pg-volume-recovery.md
smoke: bash -n scripts/services/volume-audit-watch.sh
---

# volume-audit

Systemd-style watcher around the postgres `postgres_data` volume. Logs
any external mutation so the postgres-wipe landmine (memory
`project_db_volume_landmine`) is at least observable post-hoc.

## Source coordinates

- `scripts/services/volume-audit.service` (systemd unit, optional)
- `scripts/services/volume-audit-watch.sh`

## State

working but optional. Companion test: `tests/test_volume_watcher.py`.

## Smoke test

```bash
bash -n scripts/services/volume-audit-watch.sh
python3 -m pytest tests/test_volume_watcher.py -q
```

## Runbook

- `docs/runbook-pg-volume-recovery.md` documents the recovery path
  (pg_restore from latest backup + alembic upgrade head, ~28min).

## Current owner

agent-farm conductor loop.
