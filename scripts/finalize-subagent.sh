#!/usr/bin/env bash
# finalize-subagent.sh — close out a subagent task atomically.
#
# Companion to spawn-subagent.sh. Call from the conductor right after the
# Agent tool returns (or fails). Does all the cleanup the conductor was
# previously doing inline:
#
#   1. Mark task ended in sqlite (status + exit code)
#   2. Optionally store a results row with the agent's summary
#   3. Remove the ephemeral worktree from its owning repo
#      (skipped if the agent's worktree.cleanup == none, or the worktree
#       path is in the agents/*.yaml protected set)
#
# Usage:
#   bash finalize-subagent.sh <task_id> <succeeded|failed> [exit_code] [summary]
#
# Output: K=V on stdout (final task state for the conductor to surface).
#
# The conductor MUST call this — it replaces the manual `db.py set-ended`
# pattern. Forgetting to call it leaves worktrees orphan, which is the
# bug that produced the _siblings/* leak in the previous session.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

TASK_ID="${1:-}"
STATUS="${2:-succeeded}"
EXIT="${3:-0}"
SUMMARY="${4:-}"

[[ -z "$TASK_ID" ]] && die "usage: finalize-subagent.sh <task_id> <succeeded|failed> [exit] [summary]"

case "$STATUS" in
  succeeded|failed|crashed) ;;
  *) die "status must be succeeded|failed|crashed (got '$STATUS')" ;;
esac

# Read task metadata we need
ROW=$(db_query "SELECT agent_name, worktree FROM tasks WHERE id='$TASK_ID' LIMIT 1;" || true)
[[ -z "$ROW" ]] && die "task not found in sqlite: $TASK_ID"

AGENT_NAME=$(printf '%s' "$ROW" | awk -F'\t' '{print $1}')
WORKTREE=$(printf '%s' "$ROW" | awk -F'\t' '{print $2}')

# Mark task ended in sqlite
task_set_ended "$TASK_ID" "$STATUS" "$EXIT"

# Optional summary row
if [[ -n "$SUMMARY" ]]; then
  ESCAPED=$(printf '%s' "$SUMMARY" | sed "s/'/''/g")
  db_exec "INSERT OR REPLACE INTO results(task_id, summary) VALUES('$TASK_ID', '$ESCAPED');"
fi

# Worktree cleanup, gated by yaml policy
REMOVED=0
SKIP_REASON=""

if [[ -z "$WORKTREE" ]]; then
  SKIP_REASON="no worktree recorded"
elif [[ ! -d "$WORKTREE" ]]; then
  SKIP_REASON="worktree dir already gone"
else
  YAML="$ROOT/agents/${AGENT_NAME}.yaml"
  if [[ -f "$YAML" ]]; then
    CLEANUP=$(yaml_get "$YAML" "worktree.cleanup")
    PROTECTED_PATH=$(yaml_get "$YAML" "worktree.path")
    PROTECTED_PATH="${PROTECTED_PATH/#\~/$HOME}"

    if [[ "$CLEANUP" == "none" ]]; then
      SKIP_REASON="agent yaml cleanup=none (stable worktree, not touched)"
    elif [[ -n "$PROTECTED_PATH" && "$WORKTREE" == "$PROTECTED_PATH" ]]; then
      SKIP_REASON="worktree matches protected path in yaml"
    else
      # Find the owning repo and deregister
      CANDIDATES=()
      for d in "$HOME/Thesis2/repositories"/*; do
        [[ -d "$d/.git" ]] && CANDIDATES+=("$d")
      done
      [[ -d "$HOME/Thesis2/thesis/.git" ]] && CANDIDATES+=("$HOME/Thesis2/thesis")

      for repo in "${CANDIDATES[@]}"; do
        if git -C "$repo" worktree list --porcelain 2>/dev/null | grep -q "^worktree $WORKTREE$"; then
          if git -C "$repo" worktree remove --force "$WORKTREE" 2>/dev/null; then
            REMOVED=1
            heartbeat "$TASK_ID" info "worktree removed from $repo"
          fi
          break
        fi
      done

      if [[ "$REMOVED" -eq 0 ]]; then
        # Fallback: nuke the dir and prune dangling registry
        rm -rf "$WORKTREE" 2>/dev/null && REMOVED=1
        for repo in "${CANDIDATES[@]}"; do
          git -C "$repo" worktree prune 2>/dev/null || true
        done
        heartbeat "$TASK_ID" warn "worktree removed by rm -rf fallback (no owning repo found)"
      fi
    fi
  else
    SKIP_REASON="agent yaml missing: $YAML"
  fi
fi

cat <<EOF
task_id=$TASK_ID
status=$STATUS
exit=$EXIT
worktree_removed=$REMOVED
${SKIP_REASON:+skip_reason=$SKIP_REASON}
EOF
