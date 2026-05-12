#!/usr/bin/env bash
# cleanup.sh — GC: detect crashed tasks, remove orphaned tmux windows + worktrees.
#
# Usage:
#   bash cleanup.sh           # report only
#   bash cleanup.sh --apply   # actually remove orphans
#
# Worktree scanning: iterates ALL repos under ~/Thesis2/repositories/ plus
# ~/Thesis2/thesis so any sibling-repo worktree gets removed from the correct
# registry. Protected paths (declared via worktree.path in agents/*.yaml with
# cleanup: none) are never touched.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

log "cleanup pass (apply=$APPLY)"

# Build list of repos to consult when removing worktrees: all subdirs of
# repositories/ that look like git repos, plus thesis.
REPO_LIST=()
for d in "$HOME/Thesis2/repositories"/*; do
  [[ -d "$d/.git" ]] && REPO_LIST+=("$d")
done
[[ -d "$HOME/Thesis2/thesis/.git" ]] && REPO_LIST+=("$HOME/Thesis2/thesis")

# Build protected-paths set from agents/*.yaml. Any yaml with cleanup: none
# AND a declared worktree.path expands to an absolute path that cleanup
# refuses to touch.
PROTECTED_PATHS=()
for y in "$ROOT/agents"/*.yaml; do
  [[ -f "$y" ]] || continue
  name=$(basename "$y" .yaml)
  [[ "$name" == "_template" ]] && continue
  c=$(yaml_get "$y" "worktree.cleanup")
  p=$(yaml_get "$y" "worktree.path")
  if [[ "$c" == "none" && -n "$p" ]]; then
    # expand ~ if present
    p="${p/#\~/$HOME}"
    PROTECTED_PATHS+=("$p")
  fi
done

is_protected() {
  local path="$1"
  for p in "${PROTECTED_PATHS[@]:-}"; do
    [[ "$path" == "$p" ]] && return 0
  done
  return 1
}

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

# 3. Worktrees under AGENT_FARM_WORKTREES not referenced by any running/pending
#    task AND not in PROTECTED_PATHS → remove. Iterates all REPO_LIST entries
#    to find the worktree's owning repo and deregisters before rm.
if [[ -d "$AGENT_FARM_WORKTREES" ]]; then
  active_wts=$(db_query "SELECT worktree FROM tasks WHERE status IN ('running','pending') AND worktree IS NOT NULL;" | sort -u)
  for d in "$AGENT_FARM_WORKTREES"/*/; do
    [[ -d "$d" ]] || continue
    d="${d%/}"
    if grep -qx "$d" <<<"$active_wts"; then
      continue
    fi
    if is_protected "$d"; then
      log "protected (skipped): $d"
      continue
    fi
    log "orphan worktree: $d"
    if [[ "$APPLY" -eq 1 ]]; then
      removed=0
      for repo in "${REPO_LIST[@]}"; do
        if git -C "$repo" worktree list --porcelain 2>/dev/null | grep -q "^worktree $d$"; then
          git -C "$repo" worktree remove --force "$d" 2>/dev/null && removed=1 && break
        fi
      done
      [[ "$removed" -eq 0 ]] && rm -rf "$d" 2>/dev/null || true
    fi
  done
  # Also clean stray top-level dirs left from sibling-bundle agents
  # (e.g. _siblings/) after their sub-worktrees were removed.
  for d in "$AGENT_FARM_WORKTREES"/*/; do
    [[ -d "$d" ]] || continue
    d="${d%/}"
    is_protected "$d" && continue
    # If empty dir and not referenced, remove
    if [[ -z "$(ls -A "$d" 2>/dev/null)" ]]; then
      if ! grep -qx "$d" <<<"$active_wts"; then
        log "empty orphan dir: $d"
        [[ "$APPLY" -eq 1 ]] && rmdir "$d" 2>/dev/null || true
      fi
    fi
  done
fi

# 4. Prune dangling worktree registry entries in all known repos
#    (catches paths the harness removed but didn't deregister).
if [[ "$APPLY" -eq 1 ]]; then
  for repo in "${REPO_LIST[@]}"; do
    git -C "$repo" worktree prune 2>/dev/null || true
  done
fi

[[ "$APPLY" -eq 0 ]] && log "(report only — re-run with --apply to remove)"
log "cleanup done"
