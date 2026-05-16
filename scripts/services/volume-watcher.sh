#!/usr/bin/env bash
# volume-watcher.sh -- FARM-1.7
#
# Size-based watcher for the postgres / minio / rabbitmq docker volumes.
# Designed to be cron'd every 15 minutes. Compares the current `du -sb`
# of each watched volume against the previous reading recorded in
# state/logs/volume_sizes.log and emits a critical heartbeat if the
# new reading is below 10% of the prior reading (i.e. a >=90% shrink,
# which is the signature of a wipe -- see project_db_volume_landmine).
#
# This watcher is intentionally orthogonal to the inotify-based
# volume-audit-watch.sh:
#   - volume-audit-watch.sh captures event-level forensics (what fs op,
#     by whom) but requires inotify-tools + a long-running root process.
#   - volume-watcher.sh is a coarse statistical heartbeat: a wiped
#     volume always shrinks. It runs as the user, needs no root, and
#     piggybacks on cron.
#
# Exit codes:
#   0  ran cleanly (regardless of whether alert fired)
#   1  fatal setup error (du missing, log dir unwritable, etc.)
#
# Output:
#   - one TSV line per watched volume appended to state/logs/volume_sizes.log
#       <iso8601-now>\t<volume>\t<bytes>\t<prev_bytes>\t<ratio_or_NA>\t<status>
#     status is one of: ok, shrink-alert, first-reading, missing
#   - one critical heartbeat per shrink-alert via the canonical
#     scripts/lib/db.py helper (if AGENT_TASK_ID is set; if not, a
#     warning is written to stderr only).
#
# Env overrides:
#   AGENT_FARM_ROOT       repo root                 (default: ~/Thesis2/agent-farm)
#   VOLUME_SIZES_LOG      target log file           (default: $ROOT/state/logs/volume_sizes.log)
#   AGENT_TASK_ID         task id for heartbeats    (default: volume-watcher)
#   VOLUMES_ROOT          docker volumes root       (default: /var/lib/docker/volumes)
#   SHRINK_RATIO          alert threshold           (default: 0.10 i.e. 10%)
#   WATCHED_VOLUMES       space-sep list            (default: see DEFAULT_VOLUMES)

set -uo pipefail

# Force a POSIX decimal point ("." not ",") so the ratio field stays
# machine-readable regardless of the cron locale.
export LC_ALL=C

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
LOG_FILE="${VOLUME_SIZES_LOG:-$ROOT/state/logs/volume_sizes.log}"
VOLUMES_ROOT="${VOLUMES_ROOT:-/var/lib/docker/volumes}"
SHRINK_RATIO="${SHRINK_RATIO:-0.10}"
TASK_ID="${AGENT_TASK_ID:-volume-watcher}"

DEFAULT_VOLUMES="protea_postgres_data protea_minio_data protea_rabbitmq_data"
WATCHED_VOLUMES="${WATCHED_VOLUMES:-$DEFAULT_VOLUMES}"

mkdir -p "$(dirname "$LOG_FILE")" || {
  echo "[volume-watcher] FATAL: cannot create log dir $(dirname "$LOG_FILE")" >&2
  exit 1
}

command -v du >/dev/null 2>&1 || {
  echo "[volume-watcher] FATAL: du not on PATH" >&2
  exit 1
}

NOW_ISO=$(date -Iseconds)

# Resolve a volume name to a path. Prefer the bare _data dir; fall back
# via docker volume inspect for unprivileged callers.
resolve_path() {
  local vol="$1"
  local cand="$VOLUMES_ROOT/$vol/_data"
  if [[ -d "$cand" ]]; then
    printf '%s\n' "$cand"
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    local mp
    mp=$(docker volume inspect "$vol" --format '{{.Mountpoint}}' 2>/dev/null || true)
    if [[ -n "$mp" && -d "$mp" ]]; then
      printf '%s\n' "$mp"
      return 0
    fi
  fi
  return 1
}

# Read the most recent prior reading for a given volume out of the log.
# Returns the bytes column or empty if no prior reading exists.
prev_reading_for() {
  local vol="$1"
  [[ -f "$LOG_FILE" ]] || return 0
  # Walk the log backwards; first match wins.
  tac "$LOG_FILE" 2>/dev/null | awk -F'\t' -v v="$vol" '
    $2 == v && $3 ~ /^[0-9]+$/ { print $3; exit }
  '
}

# Heartbeat helper. Falls back to stderr if AGENT_TASK_ID is unset and
# the caller did not pass one explicitly.
emit_heartbeat() {
  local level="$1" msg="$2"
  if [[ -x "$(command -v python3)" && -f "$ROOT/scripts/lib/db.py" ]]; then
    python3 "$ROOT/scripts/lib/db.py" heartbeat "$TASK_ID" "$level" "$msg" \
      >/dev/null 2>&1 || echo "[volume-watcher] WARN: heartbeat call failed: $msg" >&2
  else
    echo "[volume-watcher] $level: $msg" >&2
  fi
}

# Compute new_bytes / prev_bytes using awk (avoids bc dependency).
ratio_lt_threshold() {
  local new="$1" prev="$2" thresh="$3"
  awk -v n="$new" -v p="$prev" -v t="$thresh" \
    'BEGIN { if (p+0 == 0) { exit 1 } if ((n+0)/(p+0) < t+0) exit 0; else exit 1 }'
}

format_ratio() {
  local new="$1" prev="$2"
  awk -v n="$new" -v p="$prev" 'BEGIN {
    if (p+0 == 0) { print "NA" } else { printf "%.4f", (n+0)/(p+0) }
  }'
}

write_log_line() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$NOW_ISO" "$1" "$2" "$3" "$4" "$5" >> "$LOG_FILE"
}

for vol in $WATCHED_VOLUMES; do
  path=$(resolve_path "$vol" || true)
  if [[ -z "$path" ]]; then
    write_log_line "$vol" "" "" "NA" "missing"
    continue
  fi

  # `du -sb` requires read on every entry. If the volumes root is
  # root-only and we lack permission, log and skip rather than crash
  # the cron job.
  if ! bytes=$(du -sb "$path" 2>/dev/null | awk '{print $1}'); then
    write_log_line "$vol" "" "" "NA" "unreadable"
    continue
  fi
  if [[ -z "$bytes" || ! "$bytes" =~ ^[0-9]+$ ]]; then
    write_log_line "$vol" "" "" "NA" "unreadable"
    continue
  fi

  prev=$(prev_reading_for "$vol")
  if [[ -z "$prev" ]]; then
    write_log_line "$vol" "$bytes" "" "NA" "first-reading"
    continue
  fi

  ratio=$(format_ratio "$bytes" "$prev")
  if ratio_lt_threshold "$bytes" "$prev" "$SHRINK_RATIO"; then
    write_log_line "$vol" "$bytes" "$prev" "$ratio" "shrink-alert"
    emit_heartbeat critical \
      "P0: volume $vol shrank from $prev to $bytes bytes (ratio=$ratio, threshold=$SHRINK_RATIO). See state/logs/volume_sizes.log + docs/runbook-pg-volume-recovery.md"
  else
    write_log_line "$vol" "$bytes" "$prev" "$ratio" "ok"
  fi
done

exit 0
