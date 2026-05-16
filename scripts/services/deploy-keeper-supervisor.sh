#!/usr/bin/env bash
# deploy-keeper-supervisor.sh — persistent loop that runs deploy-keeper-tick.sh
# every poll_interval. On tick failure (FAIL_KIND != prereq_fail) the
# supervisor escalates to a janitor subagent via spawn-subagent.sh and
# keeps polling (it does NOT block on the janitor). prereq_fail failures
# are logged + the supervisor backs off; the user is the recovery path
# for daemon-level issues.
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

# escalate_to_janitor <fail_kind> — spawn a janitor subagent (haiku, via
# scripts/spawn-subagent.sh) to investigate the failure. We do NOT block
# on the janitor; spawn-subagent.sh inserts a pending task row and prints
# K=V env so we can record the janitor's task_id back into our own
# heartbeats. The janitor's own task spec will steer it to read the
# deploy-keeper heartbeats and act (PR fix, rerun, notify).
escalate_to_janitor() {
  local fail_kind="$1"
  local spawn_args
  spawn_args=$(jq -Rn \
    --arg task "deploy-keeper-rescue" \
    --arg msg "deploy-keeper $fail_kind fail, see heartbeats for task $TASK_ID" \
    --arg src_task "$TASK_ID" \
    '{task: $task, failure_kind: $msg, source_task_id: $src_task}')
  local spawn_out
  if ! spawn_out=$(bash "$ROOT/scripts/spawn-subagent.sh" janitor "$spawn_args" 2>&1); then
    heartbeat "$TASK_ID" error "janitor spawn failed: $spawn_out"
    return 1
  fi
  local janitor_task
  janitor_task=$(printf '%s\n' "$spawn_out" | grep -oP '^task_id=\K\S+' | head -1)
  heartbeat "$TASK_ID" info "escalated to janitor task_id=${janitor_task:-unknown} fail_kind=$fail_kind"
  return 0
}

CONSECUTIVE_FAILS=0

while true; do
  TICK_START=$(date +%s)

  # Run a tick
  if bash "$ROOT/scripts/services/deploy-keeper-tick.sh"; then
    CONSECUTIVE_FAILS=0
  else
    CONSECUTIVE_FAILS=$((CONSECUTIVE_FAILS + 1))
    heartbeat "$TASK_ID" warn "tick failed (consecutive=$CONSECUTIVE_FAILS)"

    FAIL_ENV="/tmp/deploy-keeper-last-fail.env"
    FAIL_KIND="unknown"
    FAIL_EXIT="unknown"
    if [[ -f "$FAIL_ENV" ]]; then
      # shellcheck disable=SC1090
      source "$FAIL_ENV"
    fi

    if [[ "$CONSECUTIVE_FAILS" -le "$MAX_CONSECUTIVE_FAILURES" ]]; then
      if [[ "${FAIL_KIND:-unknown}" == "prereq_fail" ]]; then
        # Daemon-level prereq fail (docker down etc); the user is the
        # recovery path. Do NOT spawn a janitor for these — there is
        # nothing a janitor can safely do at the daemon layer.
        heartbeat "$TASK_ID" error "prereq_fail (FAIL_EXIT=${FAIL_EXIT:-?}); no janitor escalation"
      else
        escalate_to_janitor "${FAIL_KIND:-unknown}" || true
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
