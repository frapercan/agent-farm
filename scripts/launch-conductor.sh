#!/usr/bin/env bash
# launch-conductor.sh — boot the agent-farm conductor in a dedicated tmux session.
#
# Idempotent: if session 'agent-farm' already has a 'conductor' window, no-op
# unless AGENT_FARM_REPRIME=1 is set (re-pastes the bootstrap message into
# the existing window so a stale conductor can re-prime without losing the
# tmux session).
#
# Autoyes is ON by default (--dangerously-skip-permissions). Subagents
# spawned by the conductor inherit this mode, so the whole zoo runs without
# permission prompts. Hard constraints in each agent's system prompt are
# the safety net.
#
# Usage:
#   bash launch-conductor.sh                            # autoyes ON (default), autopaste ON
#   AGENT_FARM_AUTOYES=accept bash launch-conductor.sh  # acceptEdits mode (prompts on risky ops)
#   AGENT_FARM_AUTOYES=0 bash launch-conductor.sh       # OFF, full manual prompts
#   AGENT_FARM_AUTOBOOTSTRAP=0 bash launch-conductor.sh # skip the autopaste
#   AGENT_FARM_REPRIME=1 bash launch-conductor.sh       # re-paste into existing conductor window
#   tmux attach -t agent-farm

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
SESSION="${AGENT_FARM_TMUX_SESSION:-agent-farm}"
AUTOYES="${AGENT_FARM_AUTOYES:-1}"
AUTOBOOTSTRAP="${AGENT_FARM_AUTOBOOTSTRAP:-1}"
REPRIME="${AGENT_FARM_REPRIME:-0}"

# Single source of truth for the bootstrap message. Keep terse: the
# canonical procedure lives in prompts/bootstrap-autowork.md, which the
# conductor reads. The boot.sh diagnostic is the first thing it runs.
# Critical: tells the conductor NOT to spawn agents until the user OKs.
read -r -d '' BOOTSTRAP_MSG <<'EOF' || true
Lee ~/Thesis2/agent-farm/prompts/conductor.md y luego ~/Thesis2/agent-farm/prompts/bootstrap-autowork.md. Ejecutá el boot diagnóstico (scripts/boot.sh) y reportame. NO spawnees ningún agente hasta que te dé el visto bueno explícito.
EOF

# Resolve autoyes mode → claude flag
case "$AUTOYES" in
  1|on|yes|bypass) CLAUDE_FLAGS="--dangerously-skip-permissions"; MODE_DESC="bypass (autoyes ON)" ;;
  accept|edits)    CLAUDE_FLAGS="--permission-mode acceptEdits";   MODE_DESC="acceptEdits (auto on edits, prompts on risky)" ;;
  0|off|no|manual) CLAUDE_FLAGS="";                                 MODE_DESC="manual (every prompt asked)" ;;
  *) echo "ERROR: AGENT_FARM_AUTOYES must be one of: 1|accept|0 (got '$AUTOYES')" >&2; exit 2 ;;
esac

# 1. ensure DB
[[ -f "$ROOT/state/tasks.sqlite" ]] || bash "$ROOT/scripts/init.sh"

# 1b. install FARM-1.4 dev-clone guards (idempotent). boot.sh also re-runs
# this on every conductor boot; this early call protects the dev workspace
# before claude even starts.
if [[ -x "$ROOT/scripts/install-dev-hooks.sh" ]]; then
  bash "$ROOT/scripts/install-dev-hooks.sh" --all >/dev/null 2>&1 || \
    echo "launch-conductor: install-dev-hooks reported issues (non-fatal); re-run manually if needed." >&2
fi

# 2. ensure tmux session
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n bootstrap -c "$HOME/Thesis2"
  echo "Created tmux session '$SESSION'"
fi

# 3. ensure conductor window
SPAWNED_NEW=0
if tmux list-windows -t "$SESSION" -F '#W' | grep -qx 'conductor'; then
  if [[ "$REPRIME" == "1" ]]; then
    echo "Window '$SESSION:conductor' exists; AGENT_FARM_REPRIME=1 set → will re-paste bootstrap message."
  else
    echo "Window '$SESSION:conductor' already exists; skipping spawn."
    echo "(to re-paste the bootstrap message into the existing conductor:"
    echo "    AGENT_FARM_REPRIME=1 bash $ROOT/scripts/launch-conductor.sh)"
    echo "(to change autoyes mode: kill the window + relaunch)"
  fi
else
  tmux new-window -t "$SESSION" -n conductor -c "$HOME/Thesis2" "claude $CLAUDE_FLAGS"
  SPAWNED_NEW=1
  echo "Spawned 'conductor' window with claude (mode: $MODE_DESC)."
fi

# 4. drop bootstrap placeholder
tmux kill-window -t "$SESSION:bootstrap" 2>/dev/null || true

# 5. Wait for claude to be ready, then auto-paste the bootstrap message.
# Replaces the old hardcoded `sleep 8` with a poll that watches the pane
# for markers that indicate the REPL is interactive. Falls back to a
# 30s ceiling if no marker is matched (still pastes — claude usually
# tolerates early input, just buffers).
wait_for_claude_ready() {
  local target="$1" max=30 i
  for ((i=0; i<max; i++)); do
    if tmux capture-pane -t "$target" -p 2>/dev/null \
      | grep -qE '(claude\.ai/code|Welcome to Claude|Ready|How can I help|❯|^> |^│ > )'; then
      return 0
    fi
    sleep 1
  done
  return 1
}

should_paste=0
if [[ "$AUTOBOOTSTRAP" == "1" ]]; then
  if [[ "$SPAWNED_NEW" -eq 1 ]]; then
    should_paste=1
  elif [[ "$REPRIME" == "1" ]]; then
    should_paste=1
  fi
fi

if [[ "$should_paste" -eq 1 ]]; then
  echo "Waiting up to 30s for claude REPL to come up..."
  if wait_for_claude_ready "$SESSION:conductor"; then
    echo "claude REPL ready; pasting bootstrap message."
  else
    echo "claude REPL marker not detected within 30s; pasting anyway (claude usually buffers)."
  fi
  tmux send-keys -t "$SESSION:conductor" "$BOOTSTRAP_MSG" Enter
  echo "Bootstrap pasted. Attach with: tmux attach -t $SESSION"
fi

cat <<EOF

Conductor ready (autoyes: $MODE_DESC, autobootstrap: $AUTOBOOTSTRAP, reprime: $REPRIME).

  Attach:        tmux attach -t $SESSION
  List windows:  tmux list-windows -t $SESSION
  Status:        bash $ROOT/scripts/status.sh
  Boot audit:    bash $ROOT/scripts/boot.sh --audit-only
  Cleanup:       bash $ROOT/scripts/cleanup.sh

Change autoyes mode (kills + respawns conductor):
  tmux kill-window -t $SESSION:conductor
  AGENT_FARM_AUTOYES=accept bash $ROOT/scripts/launch-conductor.sh

Re-prime an existing conductor window (no kill):
  AGENT_FARM_REPRIME=1 bash $ROOT/scripts/launch-conductor.sh

Disable autobootstrap (manual paste):
  AGENT_FARM_AUTOBOOTSTRAP=0 bash $ROOT/scripts/launch-conductor.sh

Manual bootstrap (if you skipped autopaste or want to re-prime by hand):

  $BOOTSTRAP_MSG

EOF
