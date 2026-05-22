#!/usr/bin/env bash
# kill.sh — cancel a running task: kill tmux window + cleanup worktree + mark killed.
#
# Usage:
#   bash kill.sh <task_id>

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"
# shellcheck source=lib/worktree.sh
source "$ROOT/scripts/lib/worktree.sh"

TASK_ID="${1:-}"
[[ -z "$TASK_ID" ]] && die "usage: kill.sh <task_id>"

# Read state. FARM-2.3 adds worktree_owner_repo for O(1) teardown lookup.
ROW=$(db_query "SELECT status, tmux_window, worktree, COALESCE(worktree_owner_repo,'') FROM tasks WHERE id='$TASK_ID';")
[[ -z "$ROW" ]] && die "task not found: $TASK_ID"

STATUS=$(echo "$ROW" | cut -f1)
TMUX_WIN=$(echo "$ROW" | cut -f2)
WT=$(echo "$ROW" | cut -f3)
OWNER_REPO=$(echo "$ROW" | cut -f4)

if [[ "$STATUS" =~ ^(succeeded|failed|killed|crashed)$ ]]; then
  log "task $TASK_ID already terminal ($STATUS); cleaning leftover state only"
fi

# Kill tmux window if present
if [[ -n "$TMUX_WIN" ]]; then
  if tmux has-session -t "${TMUX_WIN%%:*}" 2>/dev/null; then
    tmux kill-window -t "$TMUX_WIN" 2>/dev/null && log "killed tmux window $TMUX_WIN" || true
  fi
fi

# Remove worktree if ephemeral and exists
if [[ -n "$WT" && -d "$WT" ]]; then
  # Be careful: only remove if path is under our managed dir
  if [[ "$WT" == "$AGENT_FARM_WORKTREES"/* ]]; then
    # FARM-2.3: pass owner_repo as hint for O(1) fast path; wt_remove falls
    # back to a full repo scan when the hint is absent or stale.
    wt_remove "$WT" "$OWNER_REPO"
    log "removed worktree $WT"
  else
    log "WARN: worktree $WT outside managed dir $AGENT_FARM_WORKTREES; not removing"
  fi
fi

heartbeat "$TASK_ID" warn "killed by user"
# FARM-2.1: distinct kind=kill events row so the audit trail separates
# operator-initiated kills from natural ends. The set-ended call below
# still emits a kind=end row; both share the same task_id.
task_mark_killed "$TASK_ID" "killed by user (kill.sh)"
task_set_ended "$TASK_ID" "killed" "130"
echo "killed: $TASK_ID"
