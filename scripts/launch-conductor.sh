#!/usr/bin/env bash
# launch-conductor.sh — boot the agent-farm conductor in a dedicated tmux session.
#
# Idempotent: if session 'agent-farm' already has a 'conductor' window, no-op.
#
# Autoyes is ON by default (--dangerously-skip-permissions). Subagents
# spawned by the conductor inherit this mode, so the whole zoo runs without
# permission prompts. Hard constraints in each agent's system prompt are
# the safety net..
#
# Usage:
#   bash launch-conductor.sh                 # autoyes ON (default)
#   AGENT_FARM_AUTOYES=accept bash launch-conductor.sh  # acceptEdits mode (prompts on risky ops)
#   AGENT_FARM_AUTOYES=0 bash launch-conductor.sh       # OFF, full manual prompts
#   tmux attach -t agent-farm

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
SESSION="${AGENT_FARM_TMUX_SESSION:-agent-farm}"
AUTOYES="${AGENT_FARM_AUTOYES:-1}"

# Resolve autoyes mode → claude flag
case "$AUTOYES" in
  1|on|yes|bypass) CLAUDE_FLAGS="--dangerously-skip-permissions"; MODE_DESC="bypass (autoyes ON)" ;;
  accept|edits)    CLAUDE_FLAGS="--permission-mode acceptEdits";   MODE_DESC="acceptEdits (auto on edits, prompts on risky)" ;;
  0|off|no|manual) CLAUDE_FLAGS="";                                 MODE_DESC="manual (every prompt asked)" ;;
  *) echo "ERROR: AGENT_FARM_AUTOYES must be one of: 1|accept|0 (got '$AUTOYES')" >&2; exit 2 ;;
esac

# 1. ensure DB
[[ -f "$ROOT/state/tasks.sqlite" ]] || bash "$ROOT/scripts/init.sh"

# 2. ensure tmux session
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n bootstrap -c "$HOME/Thesis2"
  echo "Created tmux session '$SESSION'"
fi

# 3. ensure conductor window
SPAWNED_NEW=0
if tmux list-windows -t "$SESSION" -F '#W' | grep -qx 'conductor'; then
  echo "Window '$SESSION:conductor' already exists; skipping spawn."
  echo "(to change autoyes mode: kill the window + relaunch)"
else
  tmux new-window -t "$SESSION" -n conductor -c "$HOME/Thesis2" "claude $CLAUDE_FLAGS"
  SPAWNED_NEW=1
  echo "Spawned 'conductor' window with claude (mode: $MODE_DESC)."
fi

# 4. drop bootstrap placeholder
tmux kill-window -t "$SESSION:bootstrap" 2>/dev/null || true

# 5. auto-paste the bootstrap prompt into a freshly spawned conductor.
# Skipped for already-existing windows so we don't double-paste.
# AGENT_FARM_AUTOBOOTSTRAP=0 disables this if you want manual control.
AUTOBOOTSTRAP="${AGENT_FARM_AUTOBOOTSTRAP:-1}"
if [[ "$SPAWNED_NEW" -eq 1 && "$AUTOBOOTSTRAP" == "1" ]]; then
  echo "Waiting 8s for claude to come up, then auto-pasting bootstrap-autowork..."
  sleep 8
  # send-keys can't pass a multiline message reliably; instead, tell claude
  # to read the file. The conductor.md + bootstrap-autowork.md both live in
  # known paths.
  BOOTSTRAP_MSG='Lee ~/Thesis2/agent-farm/prompts/conductor.md y luego ~/Thesis2/agent-farm/prompts/bootstrap-autowork.md. Operá como conductor de agent-farm siguiendo la rutina de 4 threads. Ejecutá el boot sequence ahora y reportame al final.'
  tmux send-keys -t "$SESSION:conductor" "$BOOTSTRAP_MSG" Enter
  echo "Bootstrap pasted. Attach with: tmux attach -t $SESSION"
fi

cat <<EOF

Conductor ready (autoyes: $MODE_DESC, autobootstrap: $AUTOBOOTSTRAP).

  Attach:        tmux attach -t $SESSION
  List windows:  tmux list-windows -t $SESSION
  Status:        bash $ROOT/scripts/status.sh
  Cleanup:       bash $ROOT/scripts/cleanup.sh

Change autoyes mode (kills + respawns conductor):
  tmux kill-window -t $SESSION:conductor
  AGENT_FARM_AUTOYES=accept bash $ROOT/scripts/launch-conductor.sh

Disable autobootstrap (manual paste):
  AGENT_FARM_AUTOBOOTSTRAP=0 bash $ROOT/scripts/launch-conductor.sh

Manual bootstrap (if you skipped autopaste or want to re-prime):

  Lee ~/Thesis2/agent-farm/prompts/conductor.md y luego ~/Thesis2/agent-farm/prompts/bootstrap-autowork.md. Operá como conductor de agent-farm siguiendo la rutina de 4 threads. Ejecutá el boot sequence ahora y reportame al final.

EOF
