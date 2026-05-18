---
name: pgdump-nightly
section: "11-backup-recovery"
state: working
owner: agent-farm conductor loop
source:
  - scripts/install-nightly-pgdump-cron.sh
runbook: docs/runbook-pg-volume-recovery.md
smoke: bash -n scripts/install-nightly-pgdump-cron.sh
---

# pgdump-nightly

Installs the nightly `pg_dump` cron that writes timestamped dumps to
`~/Thesis2/backups/`. Pairs with `volume-audit` (observe the wipe) and
`restore-drill` (verify the dumps are restorable).

## Source coordinates

- `scripts/install-nightly-pgdump-cron.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/install-nightly-pgdump-cron.sh
# Verify cron line installed (idempotent)
crontab -l 2>/dev/null | grep -c pg_dump || echo "not-installed"
```

## Runbook

- One-shot installer: `bash scripts/install-nightly-pgdump-cron.sh`.
- Recovery uses the latest dump under `~/Thesis2/backups/protea-*.dump`
  (~28 min restore + alembic upgrade head).

## Current owner

agent-farm conductor loop.
