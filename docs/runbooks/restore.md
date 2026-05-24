# Runbook: Postgres recovery with restore-from-backup.sh (FARM-INFRA.3)

This runbook covers both the dry-run inspection path and the live apply
path for `scripts/restore-from-backup.sh`. It documents the procedure
that was previously manual (2026-05-11 incident, 28 min wall time) and
is now encoded in the script.

Related document: `docs/runbook-pg-volume-recovery.md` covers detection,
audit log interpretation, and the weekly drill. This runbook focuses on
executing the production restore once a wipe is confirmed.

## Quick decision tree

```
pg_tables(public) < 2 or volume wipe confirmed?
  -> YES: follow this runbook
  -> NO : no restore needed
```

## Prerequisites

1. A dump file exists under `~/Thesis2/backups/protea-*.dump`. The
   nightly pg_dump cron (installed by `scripts/install-nightly-pgdump-cron.sh`)
   produces one per day.
2. The live `protea-postgres-1` container is running. If not:
   ```bash
   cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
   ```
3. The PROTEA checkout is present at `~/Thesis2/repositories/PROTEA`
   (or override with `--protea-dir`).

## Step 1: dry-run inspection

Always run the dry-run first. It is safe, prints the plan, and exits 0
without touching the database.

```bash
cd ~/Thesis2/agent-farm

# Inspect what the script would do:
bash scripts/restore-from-backup.sh --dry-run

# Inspect with a specific dump:
bash scripts/restore-from-backup.sh --dry-run \
  --dump ~/Thesis2/backups/protea-2026-05-11.dump
```

The dry-run output shows:
- The selected dump file (name, size, mtime).
- The target container and database.
- The pg_restore flags (`-j 4 --clean --if-exists --no-owner --no-acl`).
- The alembic checkout that will be used.
- The smoke queries to be run after restore.

If the dump file path or container name is wrong, correct it before
proceeding to the apply step.

## Step 2: stop dependent services

Stop the PROTEA API workers and any agent-farm consumers that write to
postgres. This prevents dirty writes during the restore window.

```bash
cd ~/Thesis2/protea-deploy && bash scripts/manage.sh stop-workers
```

If deploy-keeper is running, stop it too:

```bash
bash ~/Thesis2/agent-farm/scripts/kill.sh deploy-keeper
```

## Step 3: apply the restore

The `--apply` flag runs the restore in three phases:
1. Drops and recreates the public schema inside the container.
2. Runs `pg_restore -j 4 --clean --if-exists --no-owner --no-acl`.
3. Runs `alembic upgrade head` in the PROTEA checkout.
4. Runs smoke queries (sequence, protein, sequence_embedding row counts).

Interactive (prompts "Type YES to confirm"):

```bash
bash scripts/restore-from-backup.sh --apply
```

Non-interactive (automation, Makefile target):

```bash
bash scripts/restore-from-backup.sh --apply --yes
```

Or via Makefile:

```bash
make restore-latest
```

The script prints elapsed time and key row counts on exit. A non-zero
exit code means at least one smoke check failed; see the error output.

## Step 4: verify and restart

After a successful restore:

```bash
# Quick sanity check in the container:
docker exec protea-postgres-1 psql -U protea -d protea -tAc \
  "SELECT count(*) FROM protein"

# Restart workers:
cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
```

Re-enable deploy-keeper once the stack is stable.

## Estimated wall time

| Dump size | pg_restore (-j 4) | alembic | Total estimate |
|-----------|-------------------|---------|---------------|
| 26 GB     | ~20-30 min        | <1 min  | ~25-35 min    |
| 56 GB     | ~50-80 min        | <1 min  | ~55-85 min    |

The 2026-05-11 manual recovery (26 GB, single-threaded) took 28 min.
With `-j 4` the expected time is lower.

## Troubleshooting

### "Container not running" error

The script exits 1 with the hint:
```
cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
```

Start the stack and re-run.

### pg_restore warnings (non-zero exit)

`pg_restore` exits non-zero on benign warnings such as extension-already-exists
errors. The script logs the warning line count and delegates the success
gate to the smoke queries. If the smoke queries pass, the restore is
considered successful.

### alembic upgrade fails

If alembic fails, the DB schema may be at the dump's revision but missing
migrations that landed after the backup date. Check:
```bash
cd ~/Thesis2/repositories/PROTEA
poetry run alembic current
poetry run alembic history --verbose | head -20
```

Then fix the migration issue and re-run `alembic upgrade head` manually.

### Smoke check fails (exit 3)

The restore completed but the row counts or pgvector extension are
missing. Likely causes: corrupt dump, out-of-space during restore, or
wrong database targeted. Check the pg_restore warning output and the
container logs.

## Makefile target

`make restore-latest` delegates to:
```bash
bash scripts/restore-from-backup.sh --apply
```

The Makefile target is defined in `agent-farm/Makefile`.

## Cross-references

- Memory: `context/memory/project_db_volume_landmine.md`
- Detection + audit log: `docs/runbook-pg-volume-recovery.md`
- Weekly drill (safe, throwaway container): `scripts/restore-drill.sh`
- PROTEA disaster recovery (heavier, dumps live DB first): `repositories/PROTEA/scripts/disaster-recovery.sh`
- Plan slice: `plans/farm-platform/PLAN.md` section FARM-INFRA.3
