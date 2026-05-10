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

# Read state
ROW=$(db_query "SELECT status, tmux_window, worktree FROM tasks WHERE id='$TASK_ID';")
[[ -z "$ROW" ]] && die "task not found: $TASK_ID"

STATUS=$(echo "$ROW" | cut -f1)
TMUX_WIN=$(echo "$ROW" | cut -f2)
WT=$(echo "$ROW" | cut -f3)

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
    if git -C "$HOME/Thesis/repositories/PROTEA" worktree list --porcelain 2>/dev/null \
        | grep -q "^worktree $WT$"; then
      git -C "$HOME/Thesis/repositories/PROTEA" worktree remove --force "$WT" 2>/dev/null || true
    fi
    rm -rf "$WT" 2>/dev/null || true
    log "removed worktree $WT"
  else
    log "WARN: worktree $WT outside managed dir $AGENT_FARM_WORKTREES; not removing"
  fi
fi

heartbeat "$TASK_ID" warn "killed by user"
task_set_ended "$TASK_ID" "killed" "130"
echo "killed: $TASK_ID"
