#!/usr/bin/env bash
# kill.sh — cancel a running task: kill tmux window + cleanup worktree + mark killed.
#
# Usage:
#   bash kill.sh <task_id>

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

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
    removed=0
    # FARM-2.3: O(1) lookup via owner_repo when present. The legacy path
    # below scans every repo as a fallback so historical tasks (column
    # null) still get cleaned up correctly.
    if [[ -n "$OWNER_REPO" && -d "$OWNER_REPO/.git" ]]; then
      if git -C "$OWNER_REPO" worktree list --porcelain 2>/dev/null \
          | grep -q "^worktree $WT$"; then
        git -C "$OWNER_REPO" worktree remove --force "$WT" 2>/dev/null && removed=1
      fi
    fi
    if [[ "$removed" -eq 0 ]]; then
      for repo in "$HOME/Thesis2/repositories"/*; do
        [[ -d "$repo/.git" ]] || continue
        if git -C "$repo" worktree list --porcelain 2>/dev/null \
            | grep -q "^worktree $WT$"; then
          git -C "$repo" worktree remove --force "$WT" 2>/dev/null && removed=1 && break
        fi
      done
      if [[ "$removed" -eq 0 && -d "$HOME/Thesis2/thesis/.git" ]]; then
        if git -C "$HOME/Thesis2/thesis" worktree list --porcelain 2>/dev/null \
            | grep -q "^worktree $WT$"; then
          git -C "$HOME/Thesis2/thesis" worktree remove --force "$WT" 2>/dev/null && removed=1
        fi
      fi
    fi
    rm -rf "$WT" 2>/dev/null || true
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
