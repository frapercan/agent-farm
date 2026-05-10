#!/usr/bin/env bash
# deploy-keeper-supervisor.sh — persistent loop that runs deploy-keeper-tick.sh
# every poll_interval. On tick failure, escalate to `claude -p` with the
# deploy-keeper.md prompt (haiku, bounded recovery).
#
# Spawned by spawn.sh in tmux session. Reads:
#   TASK_ID   — task UUID (set by spawn.sh)
#   AGENT_FARM_ROOT (default ~/Thesis2/agent-farm)
#
# Termination: Ctrl-C in tmux, or `kill.sh <task_id>`.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"

POLL_INTERVAL_SEC=300       # 5 min, matches deploy-keeper.yaml service.poll_interval
MAX_CONSECUTIVE_FAILURES=2  # after this many fails in a row, pause (don't burn $)
PAUSE_AFTER_PAUSE_SEC=1800  # 30 min cool-off after consecutive-fail trip

heartbeat "$TASK_ID" info "supervisor up; poll_interval=${POLL_INTERVAL_SEC}s"

# Trap: on shutdown, mark task ended cleanly
trap 'heartbeat "$TASK_ID" info "supervisor stopping (signal)"; task_set_ended "$TASK_ID" "killed" 130; exit 0' INT TERM

CONSECUTIVE_FAILS=0

while true; do
  TICK_START=$(date +%s)

  # Run a tick
  if bash "$ROOT/scripts/services/deploy-keeper-tick.sh"; then
    CONSECUTIVE_FAILS=0
  else
    CONSECUTIVE_FAILS=$((CONSECUTIVE_FAILS + 1))
    heartbeat "$TASK_ID" warn "tick failed (consecutive=$CONSECUTIVE_FAILS)"

    # Escalate to claude -p for failure analysis (haiku, bounded)
    if [[ "$CONSECUTIVE_FAILS" -le "$MAX_CONSECUTIVE_FAILURES" ]]; then
      FAIL_ENV="/tmp/deploy-keeper-last-fail.env"
      if [[ -f "$FAIL_ENV" ]]; then
        # shellcheck disable=SC1090
        source "$FAIL_ENV"
        heartbeat "$TASK_ID" info "escalating to claude -p; FAIL_KIND=${FAIL_KIND:-?} FAIL_EXIT=${FAIL_EXIT:-?}"

        PROMPT="$(cat "$ROOT/prompts/deploy-keeper.md")
---
Current failure context:
- TASK_ID=$TASK_ID
- FAILURE_KIND=${FAIL_KIND:-unknown}
- FAILURE_EXIT=${FAIL_EXIT:-unknown}
- AGENT_FARM_ROOT=$ROOT

Investigate and apply at most ONE bounded recovery as per the table.
Then heartbeat the outcome and exit 0 (recovered) or 1 (notified human).
"

        # Run claude headless. --dangerously-skip-permissions because deploy-keeper
        # is sandboxed and trusted. Output captured to log for forensics.
        LOGDIR="$ROOT/results/$TASK_ID"
        mkdir -p "$LOGDIR"
        ANALYSIS_LOG="$LOGDIR/analysis-$(date +%s).log"
        if claude -p "$PROMPT" \
            --dangerously-skip-permissions \
            --model haiku-4.5 \
            > "$ANALYSIS_LOG" 2>&1; then
          heartbeat "$TASK_ID" info "claude recovery succeeded (see $ANALYSIS_LOG)"
          CONSECUTIVE_FAILS=0
        else
          heartbeat "$TASK_ID" error "claude recovery failed (see $ANALYSIS_LOG)"
        fi
      else
        heartbeat "$TASK_ID" warn "no fail env at $FAIL_ENV, skipping escalation"
      fi
    else
      heartbeat "$TASK_ID" error "consecutive failures >= $MAX_CONSECUTIVE_FAILURES; pausing ${PAUSE_AFTER_PAUSE_SEC}s"
      sleep "$PAUSE_AFTER_PAUSE_SEC"
      CONSECUTIVE_FAILS=0
    fi
  fi

  # Sleep till next tick (account for tick duration)
  TICK_DUR=$(($(date +%s) - TICK_START))
  SLEEP_FOR=$((POLL_INTERVAL_SEC - TICK_DUR))
  [[ "$SLEEP_FOR" -lt 30 ]] && SLEEP_FOR=30
  sleep "$SLEEP_FOR"
done
