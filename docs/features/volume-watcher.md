---
name: volume-watcher
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/volume-watcher.sh
runbook: docs/runbook-pg-volume-recovery.md
smoke: bash -n scripts/services/volume-watcher.sh
---

# volume-watcher

Bash watcher that polls the docker volume directory for the postgres
data path. Pairs with `volume-audit.service`. Emits warnings on
unexpected size drops.

## Source coordinates

- `scripts/services/volume-watcher.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/services/volume-watcher.sh
```

## Runbook

- Optional service; not in the default boot path.
- Memory `project_db_volume_landmine` motivates this watcher.

## Current owner

agent-farm conductor loop.
