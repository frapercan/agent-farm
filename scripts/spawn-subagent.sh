#!/usr/bin/env bash
# spawn-subagent.sh — prepare a subagent spawn for the conductor.
#
# Companion to spawn.sh (which only handles kind=headless). For kind=subagent,
# this script does ALL the boilerplate the conductor would otherwise do
# manually:
#
#   1. Validate agent yaml exists + kind=subagent
#   2. Resolve repo + base branch (from yaml; default repo = PROTEA)
#   3. Create ephemeral git worktree under ~/Thesis2/worktrees/<task_id>
#   4. Insert sqlite task row (status=pending)
#   5. mkdir results/<task_id>/
#   6. Compose final prompt (system_prompt_file + spec) into
#      results/<task_id>/composed_prompt.md
#   7. Print K=V env vars to stdout for the conductor to consume
#
# Usage (from conductor):
#   bash spawn-subagent.sh <agent-name> '<spec-json>'
#
# Output (stdout):
#   task_id=<id>
#   worktree=<abs path>
#   composed_prompt=<abs path to .md>
#   model=<haiku|sonnet|opus>
#   repo=<abs path>
#
# Conductor then calls Agent tool:
#   Agent(prompt=<file content>, model=<model>, isolation=null, ...)
# and updates the task row when Agent returns:
#   python3 lib/db.py set-ended <task_id> <succeeded|failed> <exit>
#
# Errors → exit 1, message to stderr.

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

AGENT="${1:-}"
SPEC="${2:-{}}"
[[ -z "$AGENT" ]] && die "usage: spawn-subagent.sh <agent-name> [spec-json]"

YAML=$(agent_file "$AGENT")
KIND=$(yaml_get "$YAML" "kind")
MODEL=$(yaml_get "$YAML" "model")
PROMPT_REL=$(yaml_get "$YAML" "system_prompt_file")
WT_BASE=$(yaml_get "$YAML" "worktree.base_branch")
WT_REPO=$(yaml_get "$YAML" "worktree.repo")
WT_CLEANUP=$(yaml_get "$YAML" "worktree.cleanup")

[[ "$KIND" == "subagent" ]] || die "spawn-subagent handles kind=subagent only; got '$KIND'. Use spawn.sh for headless."

# Default repo = PROTEA. Agent yamls override if needed (thesis, lab, etc).
REPO="${WT_REPO:-$HOME/Thesis2/repositories/PROTEA}"
REPO="${REPO/#\~/$HOME}"  # expand tilde
[[ -d "$REPO/.git" ]] || die "repo not a git dir: $REPO (set worktree.repo in $YAML)"

PROMPT_PATH="$ROOT/$PROMPT_REL"
[[ -f "$PROMPT_PATH" ]] || die "system_prompt_file missing: $PROMPT_PATH"

BASE="${WT_BASE:-origin/develop}"

# Generate task_id
TASK_ID=$(make_task_id "$AGENT")

# Insert pending task row
task_insert "$TASK_ID" "$AGENT" "subagent" 0 "$MODEL" "$SPEC"
heartbeat "$TASK_ID" info "spawn-subagent prep started: repo=$REPO base=$BASE"

# Create worktree (only if cleanup mode wants one)
WORKTREE=""
if [[ "$WT_CLEANUP" != "none" ]]; then
  mkdir -p "$AGENT_FARM_WORKTREES"
  WORKTREE="$AGENT_FARM_WORKTREES/$TASK_ID"
  BRANCH="task/$TASK_ID"

  # Refresh base
  git -C "$REPO" fetch --quiet origin "${BASE#origin/}" 2>/dev/null || \
    heartbeat "$TASK_ID" warn "git fetch failed (offline?); using local ref"

  if ! git -C "$REPO" worktree add -b "$BRANCH" "$WORKTREE" "$BASE" 2>/tmp/wt-err.log; then
    heartbeat "$TASK_ID" error "worktree creation failed: $(cat /tmp/wt-err.log)"
    task_set_ended "$TASK_ID" "failed" "1"
    die "git worktree add failed: $(cat /tmp/wt-err.log)"
  fi
  heartbeat "$TASK_ID" info "worktree created: $WORKTREE (branch $BRANCH)"
fi

# Pre-create results dir
RESULTS="$ROOT/results/$TASK_ID"
mkdir -p "$RESULTS"

# Compose final prompt: system_prompt + task spec context
COMPOSED="$RESULTS/composed_prompt.md"
{
  cat "$PROMPT_PATH"
  echo
  echo "---"
  echo
  echo "## Spawn context (auto-injected by spawn-subagent.sh)"
  echo
  echo "- TASK_ID: \`$TASK_ID\`"
  echo "- WORKTREE: \`$WORKTREE\`"
  echo "- REPO: \`$REPO\` (base: \`$BASE\`)"
  echo "- AGENT_FARM_ROOT: \`$ROOT\`"
  echo "- RESULTS_DIR: \`$RESULTS\`"
  echo
  echo "## Task spec (JSON)"
  echo
  echo '```json'
  echo "$SPEC"
  echo '```'
  echo
  echo "Operate inside WORKTREE. Heartbeats: \`python3 \$AGENT_FARM_ROOT/scripts/lib/db.py heartbeat \"\$TASK_ID\" <level> \"<msg>\"\`."
  echo "Final result: write \`results: <summary>\` row via db.py and return your summary to the conductor."
} > "$COMPOSED"

task_set_started "$TASK_ID" "$WORKTREE" "" ""
heartbeat "$TASK_ID" info "ready for Agent tool dispatch"

# Map model name to Claude Code's --model accepted values
case "$MODEL" in
  haiku-4.5*)  CLAUDE_MODEL="haiku" ;;
  sonnet-4.6*) CLAUDE_MODEL="sonnet" ;;
  opus-4.7*)   CLAUDE_MODEL="opus" ;;
  *)           CLAUDE_MODEL="$MODEL" ;;  # pass through
esac

# Output for conductor (eval-friendly K=V on stdout)
cat <<EOF
task_id=$TASK_ID
worktree=$WORKTREE
composed_prompt=$COMPOSED
model=$CLAUDE_MODEL
repo=$REPO
results_dir=$RESULTS
EOF
