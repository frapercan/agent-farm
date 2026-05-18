#!/usr/bin/env bash
# deploy-keeper-trigger.sh — fire the manual trigger of a running
# deploy-keeper supervisor.
#
# FARM-FEAT.4: the conductor (and, once FARM-UI.6 ships, the dashboard
# CommandPalette `farm: deploy-keeper trigger` verb) shells out to
# this script to request an out-of-band tick. The supervisor watches
# MANUAL_TRIGGER_FILE on its nap_with_triggers loop and runs a tick
# at the next TRIGGER_CHECK_INTERVAL_SEC (default 60s) boundary.
#
# Two surfaces:
#   1. Marker file (default /tmp/deploy-keeper-manual-trigger). Always
#      written: this is the primary mechanism, robust across tmux/no-tmux
#      and survives the conductor not being in the same shell.
#   2. tmux send-keys (best effort): if the deploy-keeper tmux window is
#      attached and a TASK_ID is provided, also nudge it via send-keys
#      so an operator watching the window sees the trigger reflected.
#      We send a comment-prefixed string so it never executes anything
#      even if the window happens to be in a shell instead of running
#      the supervisor.
#
# Usage:
#   bash scripts/services/deploy-keeper-trigger.sh [reason...]
#
# Reads:
#   MANUAL_TRIGGER_FILE       (override marker path)
#   AGENT_FARM_TMUX_SESSION   (override tmux session name)
#   DEPLOY_KEEPER_TASK_ID     (optional; resolved via sqlite tasks table
#                              when unset and AGENT_FARM_DB is reachable)
#
# Exits 0 on marker-write success (tmux nudge is always best-effort).

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh" 2>/dev/null || true

MANUAL_TRIGGER_FILE="${MANUAL_TRIGGER_FILE:-/tmp/deploy-keeper-manual-trigger}"
REASON="${*:-manual}"

# 1. Write the marker file. atomic-ish: tmpfile + rename, so the
# supervisor never sees a half-written reason string.
tmpfile=$(mktemp "${MANUAL_TRIGGER_FILE}.XXXXXX") || {
  printf 'deploy-keeper-trigger: mktemp failed near %s\n' "$MANUAL_TRIGGER_FILE" >&2
  exit 1
}
printf '%s\n' "$REASON" > "$tmpfile"
mv -f "$tmpfile" "$MANUAL_TRIGGER_FILE"
printf 'deploy-keeper-trigger: marker written to %s (%s)\n' \
  "$MANUAL_TRIGGER_FILE" "$REASON"

# 2. tmux nudge (best effort). Try to look up the running deploy-keeper
# tmux window from the sqlite tasks table; on any failure just exit 0.
# The session env var is read by tmux send-keys via the tmux_window
# column (which already includes the session prefix), so it is parsed
# defensively but not directly used in send-keys.
: "${AGENT_FARM_TMUX_SESSION:=agent-farm}"
export AGENT_FARM_TMUX_SESSION
TASK_ID_HINT="${DEPLOY_KEEPER_TASK_ID:-}"
WINDOW=""

if [[ -z "$TASK_ID_HINT" ]] && command -v python3 >/dev/null 2>&1 && [[ -f "${AGENT_FARM_DB:-/nonexistent}" ]]; then
  WINDOW=$(python3 "$ROOT/scripts/lib/db.py" query \
    "SELECT tmux_window FROM tasks
     WHERE agent='deploy-keeper' AND status='running'
     ORDER BY started_at DESC LIMIT 1;" 2>/dev/null \
    | awk -F'|' 'NR==1 {print $1}' || true)
fi

if [[ -n "$TASK_ID_HINT" && -z "$WINDOW" ]] && command -v python3 >/dev/null 2>&1 && [[ -f "${AGENT_FARM_DB:-/nonexistent}" ]]; then
  WINDOW=$(python3 "$ROOT/scripts/lib/db.py" query \
    "SELECT tmux_window FROM tasks WHERE id='$TASK_ID_HINT' LIMIT 1;" 2>/dev/null \
    | awk -F'|' 'NR==1 {print $1}' || true)
fi

if [[ -n "$WINDOW" ]] && command -v tmux >/dev/null 2>&1; then
  # The supervisor process owns this window; send-keys lands in the
  # foreground process's stdin only if the supervisor is suspended,
  # so we send a harmless commented-out string. The real wakeup is
  # the marker file written above.
  tmux send-keys -t "$WINDOW" "# deploy-keeper-trigger: $REASON" Enter 2>/dev/null \
    && printf 'deploy-keeper-trigger: nudged tmux window %s\n' "$WINDOW" \
    || printf 'deploy-keeper-trigger: tmux nudge skipped (%s unreachable)\n' "$WINDOW"
fi

exit 0
