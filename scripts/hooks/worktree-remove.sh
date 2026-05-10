#!/usr/bin/env bash
# worktree-remove.sh — WorktreeRemove hook for Claude Code.
#
# Fires when a session/subagent worktree (created by WorktreeCreate hook
# or by the harness itself) is being torn down.
#
# Input (stdin JSON):
#   { "session_id": "...", "worktree_path": "...",
#     "hook_event_name": "WorktreeRemove" }
#
# Behavior: remove the git worktree from PROTEA repo (or whatever repo
# registered it). Failures only logged in debug mode; cannot block.

set -uo pipefail  # NOT -e: we want to attempt cleanup even if one step fails

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

STDIN_JSON=$(cat)
WT=$(printf '%s' "$STDIN_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('worktree_path',''))" 2>/dev/null || true)
[[ -z "$WT" ]] && { echo "WorktreeRemove hook: no worktree_path in input" >&2; exit 0; }
[[ ! -d "$WT" ]] && exit 0  # already gone

# Identify which repo owns this worktree
OWNER=""
for r in "$HOME/Thesis/repositories/PROTEA" "$HOME/Thesis/repositories/protea-reranker-lab" "$HOME/Thesis/thesis"; do
  if git -C "$r" worktree list --porcelain 2>/dev/null | grep -q "^worktree $WT$"; then
    OWNER="$r"
    break
  fi
done

if [[ -n "$OWNER" ]]; then
  git -C "$OWNER" worktree remove --force "$WT" 2>/dev/null || true
fi
rm -rf "$WT" 2>/dev/null || true
exit 0
