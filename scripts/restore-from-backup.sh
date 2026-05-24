#!/usr/bin/env bash
# restore-from-backup.sh -- FARM-INFRA.3
#
# Restore a protea-*.dump backup into the live protea-postgres-1 container
# and run `alembic upgrade head` to apply any migrations that landed after
# the backup was taken.
#
# SAFETY: by default, the script always requires an explicit --apply flag.
#         --dry-run (the default) prints the plan and exits 0 without
#         touching the database.
#
# Usage:
#   restore-from-backup.sh [OPTIONS]
#
# Options:
#   --dry-run          (default) print plan, exit 0 without touching DB
#   --apply            actually run pg_restore + alembic upgrade head
#   --yes              skip interactive confirmation prompt (use with --apply)
#   --dump PATH        path to a specific dump file (else newest auto-picked)
#   --jobs N           pg_restore parallelism (default: 4)
#   --protea-dir DIR   PROTEA checkout for alembic (default: ~/Thesis2/repositories/PROTEA)
#   -h | --help        print usage and exit 0
#
# Exit codes:
#   0  success (or safe dry-run)
#   1  generic failure (pre-flight, pg_restore, alembic)
#   2  no dump found matching DUMP_GLOB in BACKUP_DIR
#   3  smoke verification failed after restore
#
# Env overrides (all optional):
#   BACKUP_DIR         where to search for dumps  (default: ~/Thesis2/backups)
#   DUMP_GLOB          dump filename pattern       (default: protea-*.dump)
#   LIVE_CONTAINER     live postgres container     (default: protea-postgres-1)
#   DB_NAME            database name               (default: protea)
#   DB_USER            postgres user               (default: protea)
#   DB_HOST            postgres host (inside container is unneeded; used for
#                      pg_restore --host when connecting from the host)
#   DB_PORT            postgres port on the host   (default: 5432)
#   RESTORE_JOBS       pg_restore -j parallelism   (default: 4)
#   PROTEA_DIR         PROTEA checkout root        (default: ~/Thesis2/repositories/PROTEA)
#
# Memory: project_db_volume_landmine (2026-05-11 wipe, 28-min manual recovery).
# Plan slice: FARM-INFRA.3.

set -uo pipefail

# ---- defaults ----------------------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-$HOME/Thesis2/backups}"
DUMP_GLOB="${DUMP_GLOB:-protea-*.dump}"
LIVE_CONTAINER="${LIVE_CONTAINER:-protea-postgres-1}"
DB_NAME="${DB_NAME:-protea}"
DB_USER="${DB_USER:-protea}"
DB_PORT="${DB_PORT:-5432}"
RESTORE_JOBS="${RESTORE_JOBS:-4}"
PROTEA_DIR="${PROTEA_DIR:-$HOME/Thesis2/repositories/PROTEA}"

# ---- flags -------------------------------------------------------------------
MODE="dry-run"   # dry-run | apply
YES=0
EXPLICIT_DUMP=""
CLI_JOBS=""

print_usage() {
  cat <<'USAGE' >&2
restore-from-backup.sh -- FARM-INFRA.3

Restore a protea-*.dump into the live protea-postgres-1 container, then
run alembic upgrade head.

Usage:
  restore-from-backup.sh                  dry-run (safe, no DB changes)
  restore-from-backup.sh --apply          restore (prompts for confirmation)
  restore-from-backup.sh --apply --yes    restore non-interactively
  restore-from-backup.sh --dump PATH      use a specific dump file
  restore-from-backup.sh -h | --help      this message

Options:
  --dry-run       Print the plan and exit 0. Does NOT touch the database.
  --apply         Actually run pg_restore and alembic upgrade head.
  --yes           Skip the interactive confirmation prompt (for automation).
  --dump PATH     Path to a specific dump file (bypasses auto-selection).
  --jobs N        pg_restore parallelism (default: 4).
  --protea-dir D  PROTEA checkout root for alembic (default: ~/Thesis2/repositories/PROTEA).

Env: BACKUP_DIR DUMP_GLOB LIVE_CONTAINER DB_NAME DB_USER DB_PORT RESTORE_JOBS PROTEA_DIR.

If the live postgres container is not running, start it first:
  cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
USAGE
}

while (( $# > 0 )); do
  case "$1" in
    --dry-run)    MODE="dry-run"; shift ;;
    --apply)      MODE="apply"; shift ;;
    --yes)        YES=1; shift ;;
    --dump)
      [[ $# -ge 2 ]] || { echo "[restore] --dump needs PATH" >&2; exit 1; }
      EXPLICIT_DUMP="$2"; shift 2 ;;
    --dump=*)     EXPLICIT_DUMP="${1#--dump=}"; shift ;;
    --jobs)
      [[ $# -ge 2 ]] || { echo "[restore] --jobs needs N" >&2; exit 1; }
      CLI_JOBS="$2"; shift 2 ;;
    --jobs=*)     CLI_JOBS="${1#--jobs=}"; shift ;;
    --protea-dir)
      [[ $# -ge 2 ]] || { echo "[restore] --protea-dir needs DIR" >&2; exit 1; }
      PROTEA_DIR="$2"; shift 2 ;;
    --protea-dir=*) PROTEA_DIR="${1#--protea-dir=}"; shift ;;
    -h|--help)    print_usage; exit 0 ;;
    *)  echo "[restore] unknown argument: $1" >&2; print_usage; exit 1 ;;
  esac
done

[[ -n "$CLI_JOBS" ]] && RESTORE_JOBS="$CLI_JOBS"

# ---- helpers -----------------------------------------------------------------
log()  { printf '[restore] %s\n' "$*" >&2; }
die()  { log "ERROR: $*"; exit 1; }

# ---- pre-flight: find dump ---------------------------------------------------
if [[ -n "$EXPLICIT_DUMP" ]]; then
  [[ -f "$EXPLICIT_DUMP" ]] || die "--dump file missing: $EXPLICIT_DUMP"
  DUMP_FILE="$EXPLICIT_DUMP"
else
  [[ -d "$BACKUP_DIR" ]] || die "BACKUP_DIR missing: $BACKUP_DIR"
  DUMP_FILE=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "$DUMP_GLOB" -printf '%T@ %p\n' \
              2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)
  if [[ -z "$DUMP_FILE" ]]; then
    log "No dump matching '$DUMP_GLOB' found in $BACKUP_DIR"
    exit 2
  fi
fi

DUMP_BASENAME=$(basename "$DUMP_FILE")
DUMP_SIZE=$(du -h "$DUMP_FILE" 2>/dev/null | cut -f1 || echo "?")
DUMP_MTIME=$(stat -c '%y' "$DUMP_FILE" 2>/dev/null | cut -d'.' -f1 || echo "?")

# ---- dry-run path ------------------------------------------------------------
if [[ "$MODE" == "dry-run" ]]; then
  cat <<EOF
[restore] DRY-RUN plan (--apply to execute):

  dump file   : $DUMP_FILE
  dump size   : $DUMP_SIZE
  dump mtime  : $DUMP_MTIME
  container   : $LIVE_CONTAINER  (port $DB_PORT)
  database    : $DB_NAME (user=$DB_USER)
  pg_restore  : -j $RESTORE_JOBS --clean --if-exists --no-owner --no-acl
  alembic dir : $PROTEA_DIR
  step 1      : verify $LIVE_CONTAINER is running + pgvector extension present
  step 2      : DROP SCHEMA public CASCADE; CREATE SCHEMA public (inside container)
  step 3      : pg_restore -j $RESTORE_JOBS ... $DUMP_BASENAME
  step 4      : alembic upgrade head
  step 5      : smoke -- SELECT count(*) on sequence, protein, sequence_embedding
  on success  : elapsed + row counts printed; exit 0
  on failure  : error details printed; exit 1 or 3

To execute:
  bash scripts/restore-from-backup.sh --apply [--yes] [--dump PATH]
If postgres is not running:
  cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start
EOF
  exit 0
fi

# ---- apply path: extra pre-flights ------------------------------------------
command -v docker >/dev/null 2>&1 || die "docker not on PATH"

# Verify container is running.
if ! docker ps --format '{{.Names}}' | grep -qx "$LIVE_CONTAINER"; then
  log "Container '$LIVE_CONTAINER' is not running."
  log "Start it first: cd ~/Thesis2/protea-deploy && bash scripts/manage.sh start"
  exit 1
fi

# Helper: run SQL inside live container.
psql_live() {
  docker exec -i "$LIVE_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc "$1" 2>/dev/null \
    | tr -d '[:space:]'
}

# Verify pgvector extension is present.
VECTOR_EXT=$(psql_live "SELECT extname FROM pg_extension WHERE extname='vector'" || echo "")
if [[ "$VECTOR_EXT" != "vector" ]]; then
  log "WARNING: pgvector extension not detected in live container (may be restored by pg_restore)"
fi

# Verify alembic directory.
ALEMBIC_INI="$PROTEA_DIR/alembic.ini"
if [[ ! -f "$ALEMBIC_INI" ]]; then
  die "alembic.ini not found at $ALEMBIC_INI (set --protea-dir)"
fi

# ---- confirmation prompt ----------------------------------------------------
log "Selected dump  : $DUMP_FILE ($DUMP_SIZE, mtime $DUMP_MTIME)"
log "Target         : container=$LIVE_CONTAINER db=$DB_NAME user=$DB_USER port=$DB_PORT"
log "pg_restore jobs: $RESTORE_JOBS"
log "alembic dir    : $PROTEA_DIR"
log ""
log "WARNING: This will DROP and recreate the public schema in '$DB_NAME'."
log "         All existing data will be REPLACED by the dump."
log ""

if (( YES == 0 )); then
  printf '[restore] Type YES to confirm restore: ' >&2
  read -r CONFIRM
  if [[ "$CONFIRM" != "YES" ]]; then
    log "Aborted (user did not confirm)."
    exit 1
  fi
fi

# ---- execute ----------------------------------------------------------------
START_TS=$(date +%s)
log "Starting restore at $(date -Iseconds)"

# Step 1: Drop public schema and recreate to ensure a clean slate.
log "Step 1/4: dropping + recreating public schema..."
docker exec -i "$LIVE_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" 2>&1 \
  || die "Failed to reset public schema"

# Step 2: pg_restore.
log "Step 2/4: running pg_restore -j $RESTORE_JOBS (this may take 30-90 min)..."
RESTORE_START=$(date +%s)

# pg_restore exits non-zero on benign warnings (extension already exists,
# role ownership). Capture stderr and gate on smoke queries instead.
set +e
docker exec -i "$LIVE_CONTAINER" pg_restore \
  -U "$DB_USER" -d "$DB_NAME" \
  -j "$RESTORE_JOBS" \
  --clean --if-exists --no-owner --no-acl \
  < "$DUMP_FILE" 2>/tmp/restore-pgrestore.err
RESTORE_RC=$?
set -e

RESTORE_DUR=$(( $(date +%s) - RESTORE_START ))
if (( RESTORE_RC != 0 )); then
  ERR_LINES=$(wc -l < /tmp/restore-pgrestore.err 2>/dev/null || echo 0)
  log "pg_restore exit=$RESTORE_RC with $ERR_LINES warning line(s) (extension reload is benign)"
  if (( ERR_LINES > 0 )); then
    log "First 20 lines of stderr:"
    head -20 /tmp/restore-pgrestore.err >&2 || true
  fi
fi
log "pg_restore finished in ${RESTORE_DUR}s"

# Step 3: alembic upgrade head.
log "Step 3/4: running alembic upgrade head in $PROTEA_DIR..."
ALEMBIC_OUT=$(cd "$PROTEA_DIR" && poetry run alembic upgrade head 2>&1) || {
  log "alembic upgrade head failed:"
  printf '%s\n' "$ALEMBIC_OUT" >&2
  exit 1
}
log "alembic: $ALEMBIC_OUT"

# Step 4: smoke queries.
log "Step 4/4: smoke queries..."

smoke_count() {
  local tbl="$1"
  docker exec -i "$LIVE_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT count(*) FROM $tbl" 2>/dev/null | tr -d '[:space:]' || echo "?"
}

SEQ_ROWS=$(smoke_count sequence)
PROTEIN_ROWS=$(smoke_count protein)
EMB_ROWS=$(smoke_count sequence_embedding)
VECTOR_EXT_POST=$(psql_live "SELECT extname FROM pg_extension WHERE extname='vector'" || echo "missing")
[[ -z "$VECTOR_EXT_POST" ]] && VECTOR_EXT_POST="missing"
PG_TABLES=$(psql_live "SELECT count(*) FROM pg_tables WHERE schemaname='public'" || echo "?")

ELAPSED=$(( $(date +%s) - START_TS ))

echo ""
echo "================================================================"
printf "Restore complete in %ds\n" "$ELAPSED"
echo "----------------------------------------------------------------"
printf "%-25s %s\n" "dump file:"         "$DUMP_BASENAME ($DUMP_SIZE)"
printf "%-25s %s\n" "pg_restore exit:"   "$RESTORE_RC (non-zero may be benign)"
printf "%-25s %s\n" "public tables:"     "$PG_TABLES"
printf "%-25s %s\n" "pgvector ext:"      "$VECTOR_EXT_POST"
printf "%-25s %s\n" "sequence rows:"     "$SEQ_ROWS"
printf "%-25s %s\n" "protein rows:"      "$PROTEIN_ROWS"
printf "%-25s %s\n" "sequence_embedding:" "$EMB_ROWS"
echo "================================================================"
echo ""

# Fail if basic smoke checks are not met.
SMOKE_OK=1
if [[ -z "$PG_TABLES" || "$PG_TABLES" == "?" || "$PG_TABLES" -lt 5 ]]; then
  log "SMOKE FAIL: only $PG_TABLES public tables after restore (expected >=5)"
  SMOKE_OK=0
fi
if [[ -z "$PROTEIN_ROWS" || "$PROTEIN_ROWS" == "?" || "$PROTEIN_ROWS" -le 0 ]]; then
  log "SMOKE FAIL: protein table has $PROTEIN_ROWS rows (expected >0)"
  SMOKE_OK=0
fi
if [[ "$VECTOR_EXT_POST" != "vector" ]]; then
  log "SMOKE FAIL: pgvector extension missing after restore"
  SMOKE_OK=0
fi

if (( SMOKE_OK == 0 )); then
  log "Restore completed but smoke verification FAILED. Check the warnings above."
  exit 3
fi

log "All smoke checks passed. Restore successful."
exit 0
