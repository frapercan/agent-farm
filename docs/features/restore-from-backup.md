---
name: restore-from-backup
section: "11-backup-recovery"
state: working
owner: agent-farm conductor loop
source:
  - scripts/restore-from-backup.sh
runbook: docs/runbooks/restore.md
smoke: bash -n scripts/restore-from-backup.sh
---

# restore-from-backup

Production restore script (FARM-INFRA.3) that recovers a live PROTEA
postgres database from a `~/Thesis2/backups/protea-*.dump` file.
Codifies the 2026-05-11 manual recovery procedure (28 min, copy-paste
prone) as a single executable with a safe `--dry-run` mode and a
non-interactive `--apply --yes` path for automation.

## Source coordinates

- `scripts/restore-from-backup.sh`

## State

working. Tested via `tests/test_restore_from_backup.sh` +
`tests/test_restore_from_backup_pyshim.py`.

## Smoke test

```bash
bash -n scripts/restore-from-backup.sh
bash tests/test_restore_from_backup.sh
python3 -m pytest tests/test_restore_from_backup_pyshim.py -q
```

## Runbook

See `docs/runbooks/restore.md` for the full dry-run and apply paths.

Quick reference:

```bash
# Inspect what would be restored (safe, no DB changes):
bash scripts/restore-from-backup.sh --dry-run

# Restore the newest dump with confirmation prompt:
bash scripts/restore-from-backup.sh --apply

# Non-interactive (automation / Makefile):
bash scripts/restore-from-backup.sh --apply --yes

# Restore a specific dump file:
bash scripts/restore-from-backup.sh --apply --dump ~/Thesis2/backups/protea-2026-05-11.dump

# Makefile shortcut (delegates to --apply):
make restore-latest
```

If postgres is not running when `--apply` is invoked, the script prints:

```
cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
```

and exits 1.

## Current owner

agent-farm conductor loop.
