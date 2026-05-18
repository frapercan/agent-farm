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
WT_REPO=$(yaml_get "$YAML" "worktree.repo")
WT_BASE=$(yaml_get "$YAML" "worktree.base_branch")
WT_CLEANUP=$(yaml_get "$YAML" "worktree.cleanup")

[[ "$KIND" == "headless" ]] || die "spawn.sh handles kind=headless only; got '$KIND'. Use Agent tool for subagents."

PERSISTENT_INT=0
[[ "$PERSISTENT" == "True" || "$PERSISTENT" == "true" ]] && PERSISTENT_INT=1

TASK_ID=$(make_task_id "$AGENT")

# Ensure tmux session exists
if ! tmux has-session -t "$AGENT_FARM_TMUX_SESSION" 2>/dev/null; then
  tmux new-session -d -s "$AGENT_FARM_TMUX_SESSION" -n bootstrap -c "$HOME/Thesis2"
fi

# Insert pending task
task_insert "$TASK_ID" "$AGENT" "$KIND" "$PERSISTENT_INT" "$MODEL" "$SPEC"
heartbeat "$TASK_ID" info "spawn requested; kind=$KIND persistent=$PERSISTENT_INT model=$MODEL"

# Two paths: persistent service vs one-shot batch
if [[ "$PERSISTENT_INT" -eq 1 ]]; then
  SUPERVISOR="$ROOT/scripts/services/${AGENT}-supervisor.sh"
  [[ -x "$SUPERVISOR" ]] || die "supervisor missing or not executable: $SUPERVISOR"
  WINDOW="$TASK_ID"
  tmux new-window -t "$AGENT_FARM_TMUX_SESSION" -n "$WINDOW" -c "$HOME/Thesis2" \
    "TASK_ID='$TASK_ID' AGENT_FARM_ROOT='$ROOT' bash '$SUPERVISOR'; echo 'supervisor exited; press enter to close'; read"
  task_set_started "$TASK_ID" "" "$AGENT_FARM_TMUX_SESSION:$WINDOW" ""
  heartbeat "$TASK_ID" info "supervisor launched in tmux window $WINDOW"
else
  # One-shot batch: spawn `claude -p` headless with the agent prompt + spec.
  PROMPT_PATH="$ROOT/$PROMPT_FILE"
  [[ -f "$PROMPT_PATH" ]] || die "system_prompt_file missing: $PROMPT_PATH"

  # FARM-FEAT.2: declarative ephemeral worktree for headless one-shots.
  # When the agent yaml declares `worktree.cleanup != none`, resolve repo +
  # base from the yaml (defaults: repo=PROTEA, base=origin/develop) and
  # create a real git worktree under $AGENT_FARM_WORKTREES/<task_id>. The
  # composed prompt below injects WORKTREE/REPO/RESULTS_DIR so the agent
  # finds the path through its launch prompt (same shape spawn-subagent.sh
  # uses for kind=subagent).
  WT_PATH=""
  WT_REPO_RESOLVED=""
  if [[ -n "$WT_CLEANUP" && "$WT_CLEANUP" != "none" ]]; then
    # Default repo = PROTEA; agent yamls override via worktree.repo.
    WT_REPO_RESOLVED="${WT_REPO:-$HOME/Thesis2/repositories/PROTEA}"
    WT_REPO_RESOLVED="${WT_REPO_RESOLVED/#\~/$HOME}"
    if [[ ! -d "$WT_REPO_RESOLVED/.git" ]]; then
      heartbeat "$TASK_ID" error "worktree.repo not a git dir: $WT_REPO_RESOLVED (set worktree.repo in $YAML)"
      task_set_ended "$TASK_ID" "failed" "1"
      die "worktree.repo not a git dir: $WT_REPO_RESOLVED"
    fi

    BASE="${WT_BASE:-origin/develop}"

    mkdir -p "$AGENT_FARM_WORKTREES"
    WT_PATH="$AGENT_FARM_WORKTREES/$TASK_ID"
    BRANCH="task/$TASK_ID"

    # Refresh base (best-effort; offline runs use local ref).
    git -C "$WT_REPO_RESOLVED" fetch --quiet origin "${BASE#origin/}" 2>/dev/null || \
      heartbeat "$TASK_ID" warn "git fetch failed (offline?); using local ref"

    if ! git -C "$WT_REPO_RESOLVED" worktree add -b "$BRANCH" "$WT_PATH" "$BASE" 2>/tmp/wt-err.log; then
      heartbeat "$TASK_ID" error "worktree creation failed: $(cat /tmp/wt-err.log)"
      task_set_ended "$TASK_ID" "failed" "1"
      die "git worktree add failed: $(cat /tmp/wt-err.log)"
    fi
    heartbeat "$TASK_ID" info "worktree created: $WT_PATH (branch $BRANCH, repo $WT_REPO_RESOLVED)"

    # FARM-2.3: record owning repo for O(1) teardown lookup in finalize/cleanup.
    if ! python3 "$ROOT/scripts/lib/db.py" set-worktree-owner-repo \
          "$TASK_ID" "$WT_REPO_RESOLVED" 2>/tmp/set-owner-repo.err; then
      heartbeat "$TASK_ID" warn "set-worktree-owner-repo failed: $(cat /tmp/set-owner-repo.err 2>/dev/null)"
    fi

    # FARM-2.4: capture sha_before for the executor audit trail.
    if SHA_BEFORE=$(git -C "$WT_PATH" rev-parse HEAD 2>/dev/null); then
      if ! python3 "$ROOT/scripts/lib/db.py" set-sha \
            "$TASK_ID" before "$SHA_BEFORE" 2>/tmp/set-sha-before.err; then
        heartbeat "$TASK_ID" warn "set-sha before failed: $(cat /tmp/set-sha-before.err 2>/dev/null)"
      fi
    else
      heartbeat "$TASK_ID" warn "git rev-parse HEAD failed in fresh worktree; sha_before not recorded"
    fi

    # FARM-1.1: install enforcement git-hooks bundle into the fresh worktree.
    INSTALL_HOOKS="$ROOT/scripts/lib/install-hooks.sh"
    if [[ -x "$INSTALL_HOOKS" ]]; then
      if bash "$INSTALL_HOOKS" "$WT_PATH" 2>>/tmp/install-hooks.log; then
        heartbeat "$TASK_ID" info "install-hooks: bundle installed into $WT_PATH"
      else
        heartbeat "$TASK_ID" warn "install-hooks failed (non-fatal): see /tmp/install-hooks.log"
      fi
    else
      heartbeat "$TASK_ID" warn "install-hooks.sh not found at $INSTALL_HOOKS; worktree has no enforcement hooks"
    fi
  fi

  WINDOW="$TASK_ID"

  # FARM-FEAT.2: compose the launch prompt with the same spawn-context block
  # spawn-subagent.sh writes for kind=subagent, so headless agents resolve
  # WORKTREE/REPO/RESULTS_DIR by reading the prompt. The block is omitted
  # when no worktree was created (cleanup=none HTTP-only agents).
  RESULTS_DIR="$ROOT/results/$TASK_ID"
  mkdir -p "$RESULTS_DIR"
  COMPOSED="$RESULTS_DIR/composed_prompt.md"
  {
    cat "$PROMPT_PATH"
    echo
    echo "---"
    echo
    echo "## Spawn context (auto-injected by spawn.sh)"
    echo
    echo "- TASK_ID: \`$TASK_ID\`"
    if [[ -n "$WT_PATH" ]]; then
      echo "- WORKTREE: \`$WT_PATH\`"
      echo "- REPO: \`$WT_REPO_RESOLVED\` (base: \`${WT_BASE:-origin/develop}\`)"
    fi
    echo "- AGENT_FARM_ROOT: \`$ROOT\`"
    echo "- RESULTS_DIR: \`$RESULTS_DIR\`"
    echo
    echo "## Task spec (JSON)"
    echo
    echo '```json'
    echo "$SPEC"
    echo '```'
  } > "$COMPOSED"

  CMD_PROMPT="$(cat "$COMPOSED")"
  PERM_FLAG=""
  case "$PERMS" in
    bypassPermissions) PERM_FLAG="--dangerously-skip-permissions" ;;
    acceptEdits)       PERM_FLAG="--permission-mode acceptEdits" ;;
    *)                 PERM_FLAG="" ;;
  esac

  # FARM-2.2: capture `claude -p` stdout to results/<task_id>/stream.jsonl
  # so the post-run hook can parse the final {"type":"result"} cost line.
  # We tee instead of redirect so the operator still sees output live in
  # the tmux window. The trailing `db.py set-metrics` call is best-effort:
  # parse_claude_cost.py is robust to partial / interleaved output.
  # RESULTS_DIR already created above when composing the prompt.
  STREAM_LOG="$RESULTS_DIR/stream.jsonl"

  POST_CMD="STREAM_LOG='$STREAM_LOG'; \
TASK_ID='$TASK_ID'; \
AGENT_FARM_ROOT='$ROOT'; \
METRICS=\$(python3 \"\$AGENT_FARM_ROOT/scripts/lib/parse_claude_cost.py\" \"\$STREAM_LOG\" 2>/dev/null); \
if [[ -n \"\$METRICS\" && \"\$METRICS\" != '{}' ]]; then \
  printf '%s' \"\$METRICS\" > \"$RESULTS_DIR/metrics.json\"; \
  python3 \"\$AGENT_FARM_ROOT/scripts/lib/db.py\" set-metrics \"\$TASK_ID\" \"\$METRICS\" >/dev/null 2>&1 || true; \
  python3 \"\$AGENT_FARM_ROOT/scripts/lib/db.py\" heartbeat \"\$TASK_ID\" info \"metrics recorded: \$METRICS\" >/dev/null 2>&1 || true; \
fi"

  tmux new-window -t "$AGENT_FARM_TMUX_SESSION" -n "$WINDOW" -c "$HOME/Thesis2" \
    "claude -p \"$CMD_PROMPT\" $PERM_FLAG --output-format stream-json --verbose 2>&1 | tee '$STREAM_LOG'; $POST_CMD; echo 'exited; press enter'; read"
  task_set_started "$TASK_ID" "$WT_PATH" "$AGENT_FARM_TMUX_SESSION:$WINDOW" ""
  heartbeat "$TASK_ID" info "claude -p launched in tmux window $WINDOW (stream.jsonl capture on)"
fi

# Kill placeholder if present
tmux kill-window -t "$AGENT_FARM_TMUX_SESSION:bootstrap" 2>/dev/null || true

echo "$TASK_ID"
