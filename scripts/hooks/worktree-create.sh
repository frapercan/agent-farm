#!/usr/bin/env bash
# worktree-create.sh — WorktreeCreate hook for Claude Code.
#
# Fires when Agent(isolation: "worktree") is called from a non-git cwd
# (which is our case — conductor runs in ~/Thesis2/ which is not a git repo).
#
# Strategy: create the worktree under PROTEA repo (the canonical git repo
# for the project) at ~/Thesis2/worktrees/<session-id>.
#
# Input (stdin JSON):
#   { "session_id": "...", "cwd": "...", "source_worktree_path": "...",
#     "hook_event_name": "WorktreeCreate", "isolation_type": "worktree" }
#
# Required output (stdout): absolute path to the created worktree
# Exit: 0 on success; non-zero aborts worktree creation

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
REPO="${AGENT_FARM_DEFAULT_REPO:-$HOME/Thesis2/repositories/PROTEA}"
BASE="${AGENT_FARM_DEFAULT_BASE:-origin/develop}"
WORKTREES_BASE="${AGENT_FARM_WORKTREES:-$HOME/Thesis2/worktrees}"

mkdir -p "$WORKTREES_BASE"

# Read stdin JSON to extract session_id (for unique naming)
STDIN_JSON=$(cat)
SESSION_ID=$(printf '%s' "$STDIN_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
[[ -z "$SESSION_ID" ]] && SESSION_ID="hook-$(date +%s)-$RANDOM"

NAME="hook-${SESSION_ID:0:8}-$(date +%s)"
WT="$WORKTREES_BASE/$NAME"
BRANCH="hookwt/$NAME"

# Refresh base (best effort)
git -C "$REPO" fetch --quiet origin "${BASE#origin/}" 2>/dev/null || true

# Create worktree; surface failure to stderr so the user sees why it aborted
if ! git -C "$REPO" worktree add -b "$BRANCH" "$WT" "$BASE" 2>&1 1>/dev/null; then
  echo "WorktreeCreate hook: git worktree add failed (repo=$REPO base=$BASE)" >&2
  exit 1
fi

# Required: print absolute path on stdout
printf '%s\n' "$WT"
exit 0
