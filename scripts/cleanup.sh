#!/usr/bin/env bash
# cleanup.sh — GC: detect crashed tasks, remove orphaned tmux windows + worktrees.
#
# Usage:
#   bash cleanup.sh           # report only
#   bash cleanup.sh --apply   # actually remove orphans

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

log "cleanup pass (apply=$APPLY)"

# 1. Tasks marked running whose tmux window is dead → mark crashed
db_query "SELECT id, tmux_window FROM tasks WHERE status='running' AND tmux_window IS NOT NULL;" \
| while IFS=$'\t' read -r id tw; do
    [[ -z "$tw" ]] && continue
    sess="${tw%%:*}"
    win="${tw##*:}"
    if ! tmux has-session -t "$sess" 2>/dev/null; then
      log "task $id: tmux session $sess gone → crashed"
      [[ "$APPLY" -eq 1 ]] && task_set_ended "$id" "crashed" "1"
      continue
    fi
    if ! tmux list-windows -t "$sess" -F '#W' | grep -qx "$win"; then
      log "task $id: tmux window $win gone → crashed"
      [[ "$APPLY" -eq 1 ]] && task_set_ended "$id" "crashed" "1"
    fi
  done

# 2. tmux windows in agent-farm session not referenced by any running task → kill
if tmux has-session -t "$AGENT_FARM_TMUX_SESSION" 2>/dev/null; then
  active_windows=$(db_query "SELECT tmux_window FROM tasks WHERE status='running' AND tmux_window LIKE '$AGENT_FARM_TMUX_SESSION:%';" \
                   | awk -F: '{print $2}' | sort -u)
  tmux list-windows -t "$AGENT_FARM_TMUX_SESSION" -F '#W' \
  | while read -r w; do
      [[ "$w" == "conductor" || "$w" == "bootstrap" ]] && continue
      if ! grep -qx "$w" <<<"$active_windows"; then
        log "orphan tmux window: $AGENT_FARM_TMUX_SESSION:$w"
        [[ "$APPLY" -eq 1 ]] && tmux kill-window -t "$AGENT_FARM_TMUX_SESSION:$w"
      fi
    done
fi

# 3. Worktrees under AGENT_FARM_WORKTREES not referenced by any running/pending task → remove
if [[ -d "$AGENT_FARM_WORKTREES" ]]; then
  active_wts=$(db_query "SELECT worktree FROM tasks WHERE status IN ('running','pending') AND worktree IS NOT NULL;" | sort -u)
  for d in "$AGENT_FARM_WORKTREES"/*/; do
    [[ -d "$d" ]] || continue
    d="${d%/}"
    if ! grep -qx "$d" <<<"$active_wts"; then
      log "orphan worktree: $d"
      if [[ "$APPLY" -eq 1 ]]; then
        # Try git worktree remove first (only works if registered)
        for repo in "$HOME/Thesis2/repositories/PROTEA" "$HOME/Thesis2"; do
          if git -C "$repo" worktree list --porcelain 2>/dev/null | grep -q "^worktree $d$"; then
            git -C "$repo" worktree remove --force "$d" 2>/dev/null && break
          fi
        done
        rm -rf "$d" 2>/dev/null || true
      fi
    fi
  done
fi

[[ "$APPLY" -eq 0 ]] && log "(report only — re-run with --apply to remove)"
log "cleanup done"
