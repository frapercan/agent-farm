#!/usr/bin/env bash
# worktree.sh — ephemeral worktree helpers for agent-farm agents.
# Source from spawn.sh or per-agent scripts.
#
# Usage:
#   source $AGENT_FARM_ROOT/scripts/lib/worktree.sh
#   wt_create <task_id> <repo_path> <base_branch>   # echoes worktree path
#   wt_remove <worktree_path> <repo_path>           # removes (force)
#   wt_changed <worktree_path>                      # exits 0 if dirty/has commits
#   wt_cleanup_orphans                              # removes worktrees not in db

# Requires AGENT_FARM_WORKTREES + AGENT_FARM_ROOT from common.sh.

wt_create() {
  local task_id="$1" repo="$2" base="${3:-origin/develop}"
  [[ -d "$repo/.git" ]] || { echo "wt_create: not a git repo: $repo" >&2; return 1; }

  mkdir -p "$AGENT_FARM_WORKTREES"
  local wt="$AGENT_FARM_WORKTREES/$task_id"
  local branch="task/$task_id"

  # Create from base branch (fetch first to be sure)
  git -C "$repo" fetch --quiet origin "${base#origin/}" 2>/dev/null || true
  if ! git -C "$repo" worktree add -b "$branch" "$wt" "$base" >/dev/null 2>&1; then
    echo "wt_create: git worktree add failed" >&2
    return 1
  fi
  echo "$wt"
}

wt_remove() {
  local wt="$1" repo="${2:-}"
  [[ -d "$wt" ]] || return 0

  # Find which repo registered this worktree if not provided
  if [[ -z "$repo" ]]; then
    for r in "$HOME/Thesis/repositories/PROTEA" "$HOME/Thesis"; do
      if git -C "$r" worktree list --porcelain 2>/dev/null | grep -q "^worktree $wt$"; then
        repo="$r"; break
      fi
    done
  fi

  if [[ -n "$repo" ]] && [[ -d "$repo/.git" ]]; then
    git -C "$repo" worktree remove --force "$wt" 2>/dev/null || true
  fi
  rm -rf "$wt" 2>/dev/null || true
}

# Returns 0 if worktree has uncommitted changes OR commits ahead of base.
wt_changed() {
  local wt="$1"
  [[ -d "$wt" ]] || return 1
  local dirty
  dirty=$(git -C "$wt" status --porcelain | head -c 1)
  [[ -n "$dirty" ]] && return 0
  # commits ahead of upstream?
  local ahead
  ahead=$(git -C "$wt" rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)
  [[ "$ahead" -gt 0 ]]
}

# Garbage collect worktrees under AGENT_FARM_WORKTREES not referenced by any
# pending/running task in sqlite. Honors wt_changed: refuses to remove dirty ones
# unless --force is passed via env AGENT_FARM_WT_FORCE=1.
wt_cleanup_orphans() {
  [[ -d "$AGENT_FARM_WORKTREES" ]] || return 0
  local active_wts
  active_wts=$(python3 "$AGENT_FARM_ROOT/scripts/lib/db.py" query \
    "SELECT worktree FROM tasks WHERE status IN ('running','pending') AND worktree IS NOT NULL;" \
    | sort -u)

  for d in "$AGENT_FARM_WORKTREES"/*/; do
    [[ -d "$d" ]] || continue
    d="${d%/}"
    if ! grep -qx "$d" <<<"$active_wts"; then
      if wt_changed "$d" && [[ "${AGENT_FARM_WT_FORCE:-0}" -ne 1 ]]; then
        echo "wt_cleanup: SKIP dirty $d (commit/push first or AGENT_FARM_WT_FORCE=1 to discard)" >&2
        continue
      fi
      echo "wt_cleanup: removing orphan $d"
      wt_remove "$d"
    fi
  done
}
