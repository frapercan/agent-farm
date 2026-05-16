#!/usr/bin/env bash
# volume-audit-watch.sh -- FARM-1.7
#
# Long-running watcher that emits one JSON-Lines record to
# agent-farm/state/logs/volume_audit.log on every inotify event under
# the postgres docker volume. Each record carries:
#   ts        ISO8601 timestamp
#   event     inotify event name(s)
#   path      full path the event fired on
#   inotify_pid   pid of the inotifywait child
#   inotify_ppid  parent pid (likely the launcher / systemd unit)
#   inotify_cwd   cwd of inotifywait at moment of event
#   candidates    array of {pid, comm, cwd, cmdline} for processes
#                 whose /proc/<pid>/cwd is inside the docker volumes
#                 root at the moment we sampled. Best-effort: docker
#                 daemon often serves these events from kernel space,
#                 so candidates may be empty.
#
# Watched path defaults to
# /var/lib/docker/volumes/protea_postgres_data/. The slice spec calls
# the volume `postgres_data`; the actual name on this host is
# `protea_postgres_data` (docker compose namespaces the project). We
# watch both candidates and log the chosen one on startup.
#
# Dependencies:
#   - inotifywait (apt: inotify-tools). If absent, the script emits a
#     single startup warning record and exits 0 so its supervising
#     unit does not flap.
#
# Supervision:
#   - Intended to run under `systemctl --user`. Install instructions
#     live in docs/runbook-pg-volume-recovery.md. The unit file is
#     stored alongside the script (volume-audit.service) but is NOT
#     automatically installed (user systemd manipulation needs the
#     user's explicit consent).

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
LOG_FILE="${VOLUME_AUDIT_LOG:-$ROOT/state/logs/volume_audit.log}"
VOLUMES_ROOT="${VOLUMES_ROOT:-/var/lib/docker/volumes}"

mkdir -p "$(dirname "$LOG_FILE")"

# Pick a watch root: prefer the project-namespaced volume; fall back to
# the bare name from PLAN.md if that one is what actually exists.
# /var/lib/docker/volumes is typically root-only, so a probe via the
# docker daemon is more reliable than a direct stat from the user-space
# context this script may inherit. We accept both.
WATCH_CANDIDATES=(
  "$VOLUMES_ROOT/protea_postgres_data"
  "$VOLUMES_ROOT/postgres_data"
)
WATCH_DIR=""
for cand in "${WATCH_CANDIDATES[@]}"; do
  if [[ -d "$cand" ]]; then
    WATCH_DIR="$cand"
    break
  fi
done
# Fallback for unprivileged invocations: ask docker.
if [[ -z "$WATCH_DIR" ]] && command -v docker >/dev/null 2>&1; then
  for vol in protea_postgres_data postgres_data; do
    mp=$(docker volume inspect "$vol" --format '{{.Mountpoint}}' 2>/dev/null || true)
    if [[ -n "$mp" ]]; then
      # Mountpoint is .../volumes/<name>/_data; the parent is what we want.
      WATCH_DIR="$(dirname "$mp")"
      break
    fi
  done
fi

emit_jsonl() {
  # Append a JSON-Lines record to the audit log. All argv items are
  # treated as key=value pairs whose values are JSON-escaped via
  # python.
  python3 - "$@" <<'PY' >> "$LOG_FILE"
import json, sys, datetime
rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}
for arg in sys.argv[1:]:
    if "=" not in arg:
        continue
    k, v = arg.split("=", 1)
    rec[k] = v
print(json.dumps(rec, ensure_ascii=False))
PY
}

if ! command -v inotifywait >/dev/null 2>&1; then
  emit_jsonl event=startup-warning \
    msg="inotifywait not on PATH; install apt:inotify-tools" \
    watch_dir="${WATCH_DIR:-<none>}"
  # Exit 0 (success) so the supervising unit treats this as a clean
  # no-op rather than crash-looping. The runbook documents the manual
  # install step.
  exit 0
fi

if [[ -z "$WATCH_DIR" ]]; then
  emit_jsonl event=startup-warning \
    msg="no postgres data volume directory found under $VOLUMES_ROOT" \
    candidates="${WATCH_CANDIDATES[*]}"
  # The volume may not be created yet (fresh docker install) or may
  # have just been wiped. Either way, exit 0 and let a future restart
  # pick it up.
  exit 0
fi

# Best-effort: also watch the _data subdir so we see file-level events
# (e.g. PG_VERSION reappearing after a wipe-reinit). Use --no-newline
# so the parsed line below is stable.
WATCH_TARGETS=("$WATCH_DIR")
if [[ -d "$WATCH_DIR/_data" ]]; then
  WATCH_TARGETS+=("$WATCH_DIR/_data")
fi

emit_jsonl event=startup msg="watcher up" \
  watch_dir="$WATCH_DIR" \
  watch_targets="${WATCH_TARGETS[*]}" \
  pid="$$" cwd="$PWD"

# Collect candidate processes whose cwd is inside the docker volumes
# root. Best-effort: kernel-side actors (the docker daemon, mount
# helpers) often have cwd=/ or are otherwise opaque.
collect_candidates() {
  local pid comm cwd cmdline
  for pid_dir in /proc/[0-9]*; do
    pid=${pid_dir##*/}
    cwd=$(readlink "$pid_dir/cwd" 2>/dev/null || true)
    [[ -z "$cwd" ]] && continue
    case "$cwd" in
      "$VOLUMES_ROOT"*)
        comm=$(tr -d '\0' < "$pid_dir/comm" 2>/dev/null || echo "?")
        cmdline=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null || echo "?")
        printf '%s\t%s\t%s\t%s\n' "$pid" "$comm" "$cwd" "$cmdline"
        ;;
    esac
  done
}

# inotifywait emits one line per event: "<dir> <events> <filename>"
# (with -m --format we control the layout exactly).
INOTIFY_PID=""
trap 'if [[ -n "$INOTIFY_PID" ]]; then kill "$INOTIFY_PID" 2>/dev/null; fi; emit_jsonl event=shutdown pid="$$"; exit 0' INT TERM

# Use a process substitution so we can capture inotifywait's own pid.
inotifywait -m \
  --event create,delete,delete_self,move,move_self,attrib,modify \
  --format '%w|%e|%f' \
  "${WATCH_TARGETS[@]}" \
  > /tmp/volume-audit-pipe.$$ 2>/tmp/volume-audit-pipe.$$.err &
INOTIFY_PID=$!

cleanup_pipes() {
  rm -f "/tmp/volume-audit-pipe.$$" "/tmp/volume-audit-pipe.$$.err" 2>/dev/null || true
}
# shellcheck disable=SC2329  # invoked via trap
on_exit_inotify() {
  if [[ -n "$INOTIFY_PID" ]]; then
    kill "$INOTIFY_PID" 2>/dev/null || true
    wait "$INOTIFY_PID" 2>/dev/null || true
  fi
  cleanup_pipes
}
trap on_exit_inotify EXIT

# Wait briefly for inotifywait to settle; if it dies immediately, log
# the error and exit so systemd records the failure.
sleep 1
if ! kill -0 "$INOTIFY_PID" 2>/dev/null; then
  ERR=$(cat /tmp/volume-audit-pipe.$$.err 2>/dev/null || echo "?")
  emit_jsonl event=fatal msg="inotifywait died on startup" err="$ERR"
  exit 1
fi

# Stream events.
while IFS='|' read -r dir events fname; do
  full_path="$dir"
  [[ -n "$fname" ]] && full_path="${dir}${fname}"

  # Snapshot inotifywait's own cwd at this instant (in case it
  # changed; should not for a typical run).
  IW_CWD=$(readlink "/proc/$INOTIFY_PID/cwd" 2>/dev/null || echo "?")
  IW_PPID=$(awk '{print $4}' "/proc/$INOTIFY_PID/stat" 2>/dev/null || echo "?")

  CANDS=$(collect_candidates | head -n 10)
  # Encode candidates as a single newline-escaped value so the JSONL
  # row stays one physical line.
  CANDS_FLAT=$(printf '%s' "$CANDS" | tr '\n' ';')

  emit_jsonl event="$events" path="$full_path" \
    inotify_pid="$INOTIFY_PID" inotify_ppid="$IW_PPID" \
    inotify_cwd="$IW_CWD" candidates="$CANDS_FLAT"
done < /tmp/volume-audit-pipe.$$
