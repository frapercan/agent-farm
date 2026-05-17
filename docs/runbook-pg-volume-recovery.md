# Runbook: Postgres volume wipe + recovery (FARM-1.7)

This runbook is the operational reference for the postgres data-volume
landmine first observed on 2026-05-11 (see
`context/memory/project_db_volume_landmine.md`). It covers:

1. Detection paths (preflight heartbeat, audit log, drill log).
2. Attribution (how to read `volume_audit.log` after a suspected wipe).
3. Manual install steps for the audit watcher + weekly drill cron
   (sudo-required pieces that the executor cannot self-install).
4. Recovery procedure once a wipe is confirmed.

## Detection

There are four signals to watch.

### deploy-keeper-tick preflight heartbeat

`scripts/services/deploy-keeper-tick.sh` runs every five minutes via the
deploy-keeper supervisor. It queries the live `protea-postgres-1`
container for the count of public tables. If the count drops to one
(typical aftermath of a wipe: only `alembic_version` survives the
Alembic stamp during postgres reinit) or zero, the tick emits a
`critical` heartbeat with the P0 prefix. The heartbeat surfaces in
`state/tasks.sqlite` and is what should page the human on call.

Sample heartbeat row:

```
P0: pg_tables(public)=1 (only alembic_version). Volume wipe suspected.
See agent-farm/state/logs/volume_audit.log and docs/runbook-pg-volume-recovery.md
```

### pg_table_history.log + 50%-drop guard

Every tick also appends `<iso8601>\t<count>` to
`state/logs/pg_table_history.log`. If the latest reading is below 50%
of the prior reading, the tick checks whether the PROTEA develop
branch has any Alembic migration commits since the prior reading:

  * no migration commits since prior -> P0 heartbeat
    ("pg_tables(public)=X dropped from Y with no migration on develop").
  * one or more migrations -> a `warn`-level heartbeat documenting the
    drop, but no page (the drop is assumed intentional).

This catches partial wipes (e.g. someone `DROP TABLE`'d half the
schema) that would slip past the 0/1 guard.

### volume_audit.log

If the audit watcher is installed (see install section below),
`state/logs/volume_audit.log` accumulates one JSON-Lines record per
inotify event on the postgres data volume. Each record carries the
inotifywait pid, its parent pid, its cwd, and a best-effort list of
processes whose cwd is currently inside the docker volumes root. Use
`jq` to slice:

```bash
# Every event in the last hour.
jq -c 'select((.ts // "") >= (now - 3600 | strftime("%Y-%m-%dT%H:%M:%S")))' \
  state/logs/volume_audit.log

# Every DELETE_SELF event (volume-removal candidates).
jq -c 'select(.event | test("DELETE_SELF|MOVE_SELF"))' \
  state/logs/volume_audit.log
```

The watcher cannot capture the *root* invoker for events that the
docker daemon executes from kernel context. What it can capture:

- The pid of any process whose cwd was inside `/var/lib/docker/volumes`
  at the moment of the event (e.g. an interactive shell that ran
  `docker volume rm` from there).
- The parent of inotifywait itself (the systemd unit), which lets us
  cross-check the watcher was actually running at the time.

For events that have no candidates, correlate with shell history,
`/var/log/audit/audit.log` (if auditd is installed), and the
deploy-keeper supervisor logs.

### volume_sizes.log (du-based watcher)

`scripts/services/volume-watcher.sh` runs as the user under cron (every
15 min recommended). Each tick measures the byte size of every watched
docker volume (`protea_postgres_data`, `protea_minio_data`,
`protea_rabbitmq_data` by default) via `du -sb` and appends one row
per volume to `state/logs/volume_sizes.log` in the format:

```
<iso8601>\t<volume>\t<bytes>\t<prev_bytes>\t<ratio>\t<status>
```

`status` is one of `first-reading`, `ok`, `shrink-alert`, `missing`,
`unreadable`. If the new reading is below `SHRINK_RATIO` (default
`0.10`, i.e. a >=90% shrink) the watcher also emits a critical
heartbeat. This is intentionally coarser than the inotify watcher
above but does not need root or `inotify-tools` and survives any
restart of the live postgres container.

Sample cron entry (not auto-installed):

```cron
# FARM-1.7 -- postgres / minio / rabbitmq volume size watcher.
*/15 * * * * cd $HOME/Thesis2/agent-farm && \
  AGENT_TASK_ID=volume-watcher \
  bash scripts/services/volume-watcher.sh \
  >> state/logs/volume_sizes.cron.log 2>&1
```

### restore_drill.log

`scripts/restore-drill.sh` writes one TSV summary line per drill run
to `state/logs/restore_drill.log`:

```
<iso8601-start>\t<duration_s>\t<dump-basename>\t<pg_tables>\t<protein_rows>\t<vector_ext>\t<status>
```

A drill is healthy when `status=ok` and `vector_ext=vector`. The cron
entry runs the drill weekly (Sun 04:30 by default).

## Install (manual)

The executor that landed FARM-1.7 could not auto-install the pieces
that need either `sudo` or interactive systemd manipulation. Run the
following from `~/Thesis2/agent-farm` once:

### inotify-tools

```bash
sudo apt update
sudo apt install -y inotify-tools
```

Without inotify-tools, `scripts/services/volume-audit-watch.sh` emits
a startup-warning record and exits 0 (so its supervising unit does
not crash-loop) but no events will be captured.

### Volume-audit systemd unit

`/var/lib/docker/volumes/<vol>/` is root-only, so the watcher must run
as root. Install it as a system unit:

```bash
sudo cp scripts/services/volume-audit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now volume-audit.service
sudo systemctl status volume-audit.service
```

The shipped unit hard-codes `AGENT_FARM_ROOT=/home/frapercan/Thesis2/agent-farm`.
If the checkout lives elsewhere, edit that line before
`systemctl daemon-reload`.

Verify it is writing:

```bash
tail -f state/logs/volume_audit.log
# Provoke a benign filesystem touch on the watched dir:
docker run --rm -v protea_postgres_data:/v alpine touch /v/audit-canary
```

If the watcher cannot read `/var/lib/docker/volumes/<vol>/` it logs a
`startup-warning` and exits 0 (the systemd unit will retry per
`Restart=on-failure`, so on a clean install with inotify-tools
present the next start succeeds).

### Restore-drill weekly cron

```bash
bash scripts/install-restore-drill-cron.sh           # install
bash scripts/install-restore-drill-cron.sh --dry-run # preview
bash scripts/install-restore-drill-cron.sh --remove  # uninstall
```

The installer writes to the user crontab (`crontab -e`), runs the
drill at Sun 04:30 by default, and appends results to
`state/logs/restore_drill.log`. Override the schedule with
`RESTORE_DRILL_SCHEDULE='30 4 * * 0' bash scripts/install-restore-drill-cron.sh`.

### Nightly pg_dump backup cron

The freshest backup on 2026-05-17 was from 2026-04-12 (35 days stale).
Nightly automated dumps ensure the recovery window is at most 24 hours.

Install the nightly pg_dump + 30-day retention sweep:

```bash
bash scripts/install-nightly-pgdump-cron.sh           # preview entries
bash scripts/install-nightly-pgdump-cron.sh --apply   # install to crontab
```

The installer is idempotent; it adds two lines to the user's crontab:

- **03:00 daily**: `pg_dump --format=custom --no-owner --file=<BACKUPS>/protea-YYYY-MM-DD.dump`
- **03:15 daily**: `find <BACKUPS> -name 'protea-*.dump' -mtime +30 -delete`

Verify the cron is running:

```bash
# Check crontab entry:
crontab -l | grep protea

# Check for new dumps (should grow daily):
ls -la ~/Thesis2/backups/protea-*.dump | wc -l

# Monitor the dump log:
tail -f ~/Thesis2/backups/pgdump.log
```

The dump will be named `protea-YYYY-MM-DD.dump` and matches the drill's
default `DUMP_GLOB` pattern, so the weekly restore drill will
automatically prefer the freshest dump.

## Drill operation

Manual one-shot:

```bash
cd ~/Thesis2/agent-farm
bash scripts/restore-drill.sh
```

Inspect the plan without running the drill:

```bash
bash scripts/restore-drill.sh --dry-run
```

Restore a specific dump (e.g. a forensic copy under a different
filename pattern):

```bash
bash scripts/restore-drill.sh --backup /path/to/protea-incident.dump
```

Defaults: container `protea-pg-drill`, host port 15433, pulls the
newest `~/Thesis2/backups/protea-*.dump`. The script never touches
the live `protea-postgres-1` container. Wall time for a 26 GB dump
is 60-90 minutes on the workstation as of 2026-05-12. The smoke gate
fails the drill if the restored DB has fewer than 29 public tables
(override with `DRILL_MIN_TABLES=N`).

Smoke checks performed on the restored DB:

- `count(public tables) > 1` (must have real schema, not just
  `alembic_version`).
- `count(protein) > 0` (must have actual data).
- `extname='vector'` in `pg_extension` (pgvector loaded).

The container is removed on success and on failure (trap). To keep it
around for forensics, run with `--keep-container` is NOT supported by
this lean drill script; use PROTEA's `scripts/disaster-recovery.sh
--restore-only` if you need that.

## Recovery procedure (wipe confirmed)

This is the proven recipe from the 2026-05-12 recovery (28 min on the
26 GB May-10 dump; estimate now 60-90 min on the grown 56 GB DB):

1. Stop the live uvicorn / agent-farm consumers that talk to postgres
   (so they do not write garbage during recovery).
2. Inside `protea-postgres-1`:

   ```sql
   DROP DATABASE protea WITH (FORCE);
   CREATE DATABASE protea;
   ```

3. Restore the latest dump:

   ```bash
   pg_restore -j 4 --no-owner --no-acl \
     -d protea \
     ~/Thesis2/backups/protea-2026-05-10.dump   # or whichever is newest
   ```

4. Apply migrations from the restored revision to head:

   ```bash
   cd ~/Thesis2/repositories/PROTEA
   alembic upgrade head
   ```

5. Restart uvicorn:

   ```bash
   setsid poetry run uvicorn ... --root-path /api-proxy
   ```

After recovery, file a short post-incident note (timestamp, suspected
trigger from `volume_audit.log`, recovery wall time) under
`agent-farm/state/logs/`. If the cron drill caught the wipe before a
human did, note that in the report.

## Cross-references

- Memory: `context/memory/project_db_volume_landmine.md`
- PROTEA runbook: `repositories/PROTEA/docs/source/runbooks/disaster-recovery.rst`
- PROTEA helper: `repositories/PROTEA/scripts/disaster-recovery.sh`
  (heavier; does a fresh pg_dump first; reuses the temp container
  pattern that this slim drill is a sibling of)
- Plan slice: `agent-farm/plans/farm-platform/PLAN.md` -> FARM-1.7
