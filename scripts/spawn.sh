#!/usr/bin/env bash
# spawn.sh — spawn a headless or persistent agent in the agent-farm tmux session.
#
# Usage:
#   bash spawn.sh <agent-name> [task-spec-json]
#
# Reads agents/<name>.yaml. Only handles kind=headless (subagents are spawned
# by the conductor via the Agent tool). For kind=headless persistent=true,
# delegates to scripts/services/<name>-supervisor.sh.
#
# Prints task_id on stdout. Exits non-zero on error.

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

AGENT="${1:-}"; SPEC="${2:-{}}"
[[ -z "$AGENT" ]] && die "usage: spawn.sh <agent-name> [task-spec-json]"

YAML=$(agent_file "$AGENT")
KIND=$(yaml_get "$YAML" "kind")
PERSISTENT=$(yaml_get "$YAML" "persistent")
MODEL=$(yaml_get "$YAML" "model")
PERMS=$(yaml_get "$YAML" "permissions")
PROMPT_FILE=$(yaml_get "$YAML" "system_prompt_file")
WT_BASE=$(yaml_get "$YAML" "worktree.base_branch")
WT_CLEANUP=$(yaml_get "$YAML" "worktree.cleanup")

[[ "$KIND" == "headless" ]] || die "spawn.sh handles kind=headless only; got '$KIND'. Use Agent tool for subagents."

PERSISTENT_INT=0
[[ "$PERSISTENT" == "True" || "$PERSISTENT" == "true" ]] && PERSISTENT_INT=1

TASK_ID=$(make_task_id "$AGENT")

# Ensure tmux session exists
if ! tmux has-session -t "$AGENT_FARM_TMUX_SESSION" 2>/dev/null; then
  tmux new-session -d -s "$AGENT_FARM_TMUX_SESSION" -n bootstrap -c "$HOME/Thesis"
fi

# Insert pending task
task_insert "$TASK_ID" "$AGENT" "$KIND" "$PERSISTENT_INT" "$MODEL" "$SPEC"
heartbeat "$TASK_ID" info "spawn requested; kind=$KIND persistent=$PERSISTENT_INT model=$MODEL"

# Two paths: persistent service vs one-shot batch
if [[ "$PERSISTENT_INT" -eq 1 ]]; then
  SUPERVISOR="$ROOT/scripts/services/${AGENT}-supervisor.sh"
  [[ -x "$SUPERVISOR" ]] || die "supervisor missing or not executable: $SUPERVISOR"
  WINDOW="$TASK_ID"
  tmux new-window -t "$AGENT_FARM_TMUX_SESSION" -n "$WINDOW" -c "$HOME/Thesis" \
    "TASK_ID='$TASK_ID' AGENT_FARM_ROOT='$ROOT' bash '$SUPERVISOR'; echo 'supervisor exited; press enter to close'; read"
  task_set_started "$TASK_ID" "" "$AGENT_FARM_TMUX_SESSION:$WINDOW" ""
  heartbeat "$TASK_ID" info "supervisor launched in tmux window $WINDOW"
else
  # One-shot batch: spawn `claude -p` headless with the agent prompt + spec.
  PROMPT_PATH="$ROOT/$PROMPT_FILE"
  [[ -f "$PROMPT_PATH" ]] || die "system_prompt_file missing: $PROMPT_PATH"

  # Per-task ephemeral worktree (if cleanup=ephemeral)
  WT_PATH=""
  if [[ "$WT_CLEANUP" == "ephemeral" ]]; then
    mkdir -p "$AGENT_FARM_WORKTREES"
    WT_PATH="$AGENT_FARM_WORKTREES/$TASK_ID"
    # NOTE: assumes a git repo exists at $HOME/Thesis or PROTEA. Caller's
    # responsibility to be in the right git context. For now we skip the
    # actual `git worktree add` here and let the agent do it if needed.
    # Future: make worktree creation declarative via spec.repo.
    heartbeat "$TASK_ID" info "ephemeral worktree planned at $WT_PATH (creation deferred)"
  fi

  WINDOW="$TASK_ID"
  CMD_PROMPT="$(cat "$PROMPT_PATH")"$'\n\nTask spec (JSON):\n'"$SPEC"
  PERM_FLAG=""
  case "$PERMS" in
    bypassPermissions) PERM_FLAG="--dangerously-skip-permissions" ;;
    acceptEdits)       PERM_FLAG="--permission-mode acceptEdits" ;;
    *)                 PERM_FLAG="" ;;
  esac

  tmux new-window -t "$AGENT_FARM_TMUX_SESSION" -n "$WINDOW" -c "$HOME/Thesis" \
    "claude -p \"$CMD_PROMPT\" $PERM_FLAG --output-format stream-json --verbose; echo 'exited; press enter'; read"
  task_set_started "$TASK_ID" "$WT_PATH" "$AGENT_FARM_TMUX_SESSION:$WINDOW" ""
  heartbeat "$TASK_ID" info "claude -p launched in tmux window $WINDOW"
fi

# Kill placeholder if present
tmux kill-window -t "$AGENT_FARM_TMUX_SESSION:bootstrap" 2>/dev/null || true

echo "$TASK_ID"
