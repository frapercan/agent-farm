#!/usr/bin/env bash
# restore-drill.sh -- FARM-1.7
#
# Restore the latest ~/Thesis2/backups/protea-*.dump into a throwaway
# postgres container on host port 15433, run a smoke query, then tear
# the container down. The live protea-postgres-1 container is never
# touched (no pg_dump, no compose mutations).
#
# Exit codes:
#   0  drill OK (restore + smoke queries pass)
#   1  generic failure (docker, missing dump, container did not start)
#   3  smoke-query verification failed (restore completed but data
#      looks wrong: no tables, no rows, missing pgvector extension)
#
# Output:
#   - human-readable progress to stderr
#   - one TSV summary line appended to state/logs/restore_drill.log
#     with format:
#       <iso8601-start>\t<duration_s>\t<dump-basename>\t<pg_tables>\t<protein_rows>\t<vector_ext>\t<status>
#
# Env overrides (all optional):
#   DRILL_CONTAINER  throwaway container name  (default: protea-pg-drill)
#   DRILL_PORT       host port                  (default: 15433)
#   PG_IMAGE         postgres image             (default: pgvector/pgvector:pg16)
#   DB_NAME          db inside drill            (default: protea)
#   DB_USER          db user inside drill       (default: protea)
#   DB_PASS          db password inside drill   (default: protea)
#   BACKUP_DIR       where to find dumps        (default: ~/Thesis2/backups)
#   DUMP_GLOB        dump filename glob         (default: protea-*.dump)
#   LOG_FILE         summary log target         (default: $ROOT/state/logs/restore_drill.log)

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

DRILL_CONTAINER="${DRILL_CONTAINER:-protea-pg-drill}"
DRILL_PORT="${DRILL_PORT:-15433}"
PG_IMAGE="${PG_IMAGE:-pgvector/pgvector:pg16}"
DB_NAME="${DB_NAME:-protea}"
DB_USER="${DB_USER:-protea}"
DB_PASS="${DB_PASS:-protea}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/Thesis2/backups}"
DUMP_GLOB="${DUMP_GLOB:-protea-*.dump}"
LOG_FILE="${LOG_FILE:-$ROOT/state/logs/restore_drill.log}"

# CLI flags (FARM-1.7 v2).
#
#   --dry-run            describe the drill plan without launching docker
#                        or touching the backup. Exits 0 if a candidate
#                        dump exists, 2 if no dump matches DUMP_GLOB.
#   --backup PATH        bypass DUMP_GLOB / BACKUP_DIR and use the given
#                        dump file. Fails fast if the file is missing.
#   -h | --help          print usage and exit 0.
DRY_RUN=0
EXPLICIT_BACKUP=""

print_usage() {
  cat <<'USAGE' >&2
restore-drill.sh -- spins a throwaway postgres container, pg_restore's
the latest ~/Thesis2/backups/protea-*.dump, verifies pg_tables >=29,
then cleans up. Designed to cron weekly.

Usage:
  restore-drill.sh                    full drill (default behaviour)
  restore-drill.sh --dry-run          print the drill plan only
  restore-drill.sh --backup PATH      restore from an explicit dump
  restore-drill.sh -h | --help        this message

Env overrides: DRILL_CONTAINER DRILL_PORT PG_IMAGE DB_NAME DB_USER
DB_PASS BACKUP_DIR DUMP_GLOB LOG_FILE  (see header comment for defaults).
USAGE
}

while (( $# > 0 )); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --backup)
      [[ $# -ge 2 ]] || { echo "[restore-drill] --backup needs PATH" >&2; exit 1; }
      EXPLICIT_BACKUP="$2"; shift 2 ;;
    --backup=*) EXPLICIT_BACKUP="${1#--backup=}"; shift ;;
    -h|--help) print_usage; exit 0 ;;
    *) echo "[restore-drill] unknown arg: $1" >&2; print_usage; exit 1 ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")"

log() { printf '[restore-drill] %s\n' "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# --- pre-flight ------------------------------------------------------------
# docker is required for a real drill but NOT for --dry-run.
if (( DRY_RUN == 0 )); then
  command -v docker >/dev/null 2>&1 || die "docker not on PATH"
fi

# Resolve the dump file. --backup wins; otherwise BACKUP_DIR + DUMP_GLOB.
if [[ -n "$EXPLICIT_BACKUP" ]]; then
  [[ -f "$EXPLICIT_BACKUP" ]] || die "--backup file missing: $EXPLICIT_BACKUP"
  LATEST_DUMP="$EXPLICIT_BACKUP"
else
  [[ -d "$BACKUP_DIR" ]] || die "backup dir missing: $BACKUP_DIR"
  # Locate latest dump matching DUMP_GLOB (mtime, newest first).
  LATEST_DUMP=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "$DUMP_GLOB" -printf '%T@ %p\n' \
                | sort -nr | head -n1 | cut -d' ' -f2-)
  if [[ -z "$LATEST_DUMP" ]]; then
    if (( DRY_RUN == 1 )); then
      log "DRY-RUN: no dump matching $DUMP_GLOB in $BACKUP_DIR"
      exit 2
    fi
    die "no dump matching $DUMP_GLOB in $BACKUP_DIR"
  fi
fi
DUMP_BASENAME=$(basename "$LATEST_DUMP")
DUMP_SIZE=$(du -h "$LATEST_DUMP" 2>/dev/null | cut -f1 || echo "?")
log "selected dump: $LATEST_DUMP ($DUMP_SIZE)"

if (( DRY_RUN == 1 )); then
  cat <<EOF >&2
[restore-drill] DRY-RUN plan:
  container : $DRILL_CONTAINER
  port      : $DRILL_PORT
  image     : $PG_IMAGE
  database  : $DB_NAME (user=$DB_USER)
  dump      : $LATEST_DUMP ($DUMP_SIZE)
  log file  : $LOG_FILE
  smoke     : pg_tables(public) >= 29, count(protein) > 0, vector ext present
  on success: container removed, "ok" row written to log
  on failure: container removed, "smoke-failed" or "failed" row written
EOF
  exit 0
fi

# Refuse to clash with a real postgres on the same port.
if ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE ":${DRILL_PORT}\$"; then
  die "host port $DRILL_PORT already in use; set DRILL_PORT to a free port"
fi

# Refuse to clash with the live container name (defence in depth).
case "$DRILL_CONTAINER" in
  protea-postgres-1) die "DRILL_CONTAINER must NOT be protea-postgres-1 (would target live)";;
esac

# --- drill -----------------------------------------------------------------
START_ISO=$(date -Iseconds)
START_TS=$(date +%s)
STATUS="failed"
PG_TABLES="?"
PROTEIN_ROWS="?"
VECTOR_EXT="?"

# shellcheck disable=SC2329  # invoked via trap
teardown() {
  if docker ps -a --format '{{.Names}}' | grep -qx "$DRILL_CONTAINER"; then
    log "tearing down drill container $DRILL_CONTAINER"
    docker rm -f "$DRILL_CONTAINER" >/dev/null 2>&1 || true
  fi
}

write_log_line() {
  local dur=$1 status=$2
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$START_ISO" "$dur" "$DUMP_BASENAME" \
    "$PG_TABLES" "$PROTEIN_ROWS" "$VECTOR_EXT" "$status" \
    >> "$LOG_FILE"
}

# shellcheck disable=SC2329  # invoked via trap
on_exit() {
  local rc=$?
  local dur=$(( $(date +%s) - START_TS ))
  teardown
  if [[ "$STATUS" == "failed" ]]; then
    write_log_line "$dur" "failed(rc=$rc)"
  fi
  exit "$rc"
}
trap on_exit EXIT

# Remove a stale drill container if a previous run was killed mid-flight.
if docker ps -a --format '{{.Names}}' | grep -qx "$DRILL_CONTAINER"; then
  log "removing stale drill container"
  docker rm -f "$DRILL_CONTAINER" >/dev/null
fi

log "starting drill container $DRILL_CONTAINER on :$DRILL_PORT ($PG_IMAGE)"
docker run -d \
  --name "$DRILL_CONTAINER" \
  -e POSTGRES_USER="$DB_USER" \
  -e POSTGRES_PASSWORD="$DB_PASS" \
  -e POSTGRES_DB="$DB_NAME" \
  -p "${DRILL_PORT}:5432" \
  "$PG_IMAGE" >/dev/null \
  || die "docker run failed"

# Wait for pg_isready.
tries=0
until docker exec "$DRILL_CONTAINER" pg_isready -U "$DB_USER" >/dev/null 2>&1; do
  tries=$((tries + 1))
  if (( tries > 60 )); then
    docker logs --tail 80 "$DRILL_CONTAINER" >&2 || true
    die "drill container did not become ready within 60s"
  fi
  sleep 1
done
log "drill container ready after ${tries}s"

log "restoring $DUMP_BASENAME (this can take 60-90 min for the full 26 GB dump)"
RESTORE_START=$(date +%s)
# pg_restore exits non-zero on benign warnings (extension already exists,
# role 'protea' already owns objects). Defer the real gate to the smoke
# queries below.
set +e
docker exec -i "$DRILL_CONTAINER" pg_restore -U "$DB_USER" -d "$DB_NAME" \
  --no-owner --no-acl \
  < "$LATEST_DUMP" 2> /tmp/restore-drill-pgrestore.err
RESTORE_RC=$?
set -e
RESTORE_DUR=$(( $(date +%s) - RESTORE_START ))
if (( RESTORE_RC != 0 )); then
  WARN_LINES=$(wc -l < /tmp/restore-drill-pgrestore.err || echo 0)
  log "pg_restore exit=$RESTORE_RC, ${WARN_LINES} warning lines (benign extension reload is normal)"
fi
log "restore finished in ${RESTORE_DUR}s"

# --- smoke queries ---------------------------------------------------------
psql_scalar() {
  local sql="$1"
  docker exec "$DRILL_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc "$sql" 2>/dev/null \
    | tr -d '[:space:]'
}

PG_TABLES=$(psql_scalar "SELECT count(*) FROM pg_tables WHERE schemaname='public'")
PROTEIN_ROWS=$(psql_scalar "SELECT count(*) FROM protein" || echo "?")
VECTOR_EXT=$(psql_scalar "SELECT extname FROM pg_extension WHERE extname='vector'")
[[ -z "$VECTOR_EXT" ]] && VECTOR_EXT="missing"

log "smoke: pg_tables=$PG_TABLES protein_rows=$PROTEIN_ROWS vector_ext=$VECTOR_EXT"

OK=1
# Threshold derived from FARM-1.7 spec (>=29 tables in a healthy restore).
MIN_TABLES="${DRILL_MIN_TABLES:-29}"
if [[ -z "$PG_TABLES" || "$PG_TABLES" == "?" || "$PG_TABLES" -lt "$MIN_TABLES" ]]; then
  log "FAIL: only $PG_TABLES public table(s) restored (expected >=$MIN_TABLES)"
  OK=0
fi
if [[ -z "$PROTEIN_ROWS" || "$PROTEIN_ROWS" == "?" || "$PROTEIN_ROWS" -le 0 ]]; then
  log "FAIL: protein table has $PROTEIN_ROWS rows (expected >0)"
  OK=0
fi
if [[ "$VECTOR_EXT" != "vector" ]]; then
  log "FAIL: pgvector extension not present in restored DB"
  OK=0
fi

DUR=$(( $(date +%s) - START_TS ))
if (( OK == 1 )); then
  STATUS="ok"
  log "DRILL OK (${DUR}s)"
  write_log_line "$DUR" "ok"
  exit 0
else
  STATUS="smoke-failed"
  write_log_line "$DUR" "smoke-failed"
  exit 3
fi
