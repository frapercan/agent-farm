#!/usr/bin/env bash
# deploy-keeper-supervisor.sh — persistent loop that runs deploy-keeper-tick.sh
# every poll_interval. On tick failure (FAIL_KIND != prereq_fail) the
# supervisor first runs a quick-retry ladder (FARM-1.11) of pure-bash
# ticks; only after the ladder is exhausted does it escalate to a
# janitor subagent via spawn-subagent.sh and enter the long cool-off
# pause. prereq_fail failures are logged + the supervisor backs off;
# the user is the recovery path for daemon-level issues.
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
# shellcheck source=../lib/yaml_parse.sh
source "$ROOT/scripts/lib/yaml_parse.sh"

# FARM-2.5: read poll_interval from agents/deploy-keeper.yaml. Fall back
# to 300 if the yaml is missing or unparseable.
DEPLOY_KEEPER_YAML="${DEPLOY_KEEPER_YAML:-$ROOT/agents/deploy-keeper.yaml}"
POLL_INTERVAL_DEFAULT=300
POLL_INTERVAL_SEC=$(parse_yaml_duration "$DEPLOY_KEEPER_YAML" service.poll_interval "$POLL_INTERVAL_DEFAULT")
POLL_INTERVAL_RC=$?
if [[ "$POLL_INTERVAL_RC" -ne 0 ]]; then
  heartbeat "$TASK_ID" warn "yaml poll_interval missing/unparseable in $DEPLOY_KEEPER_YAML, defaulting to ${POLL_INTERVAL_DEFAULT}s"
fi

# FARM-1.11: quick-retry ladder run before the 30-min cool-off pause.
# Each retry is a pure-bash tick (no claude -p), so it costs ~$0.
# Tunable for tests via QUICK_RETRY_LADDER_OVERRIDE (space-separated
# seconds list; supervisor tests use shorter delays to keep wall time
# reasonable).
if [[ -n "${QUICK_RETRY_LADDER_OVERRIDE:-}" ]]; then
  # shellcheck disable=SC2206
  QUICK_RETRY_LADDER_SEC=($QUICK_RETRY_LADDER_OVERRIDE)
else
  QUICK_RETRY_LADDER_SEC=(30 120 300)
fi
PAUSE_AFTER_PAUSE_SEC=1800  # 30 min cool-off after the ladder is exhausted

heartbeat "$TASK_ID" info "supervisor up; poll_interval=${POLL_INTERVAL_SEC}s; quick_retry_ladder=${QUICK_RETRY_LADDER_SEC[*]}s; pause_after=${PAUSE_AFTER_PAUSE_SEC}s"

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

# read_fail_env: populate FAIL_KIND + FAIL_EXIT from
# /tmp/deploy-keeper-last-fail.env (default unknown when absent).
read_fail_env() {
  FAIL_KIND="unknown"
  FAIL_EXIT="unknown"
  local fail_env="/tmp/deploy-keeper-last-fail.env"
  if [[ -f "$fail_env" ]]; then
    # shellcheck disable=SC1090
    source "$fail_env"
  fi
}

# run_tick: invoke deploy-keeper-tick.sh. Tests can override
# DEPLOY_KEEPER_TICK_CMD with a stub shell command (e.g. a fail/success
# scripted shim) without touching production tick logic.
run_tick() {
  if [[ -n "${DEPLOY_KEEPER_TICK_CMD:-}" ]]; then
    bash -c "$DEPLOY_KEEPER_TICK_CMD"
  else
    bash "$ROOT/scripts/services/deploy-keeper-tick.sh"
  fi
}

# nap <seconds>: sleep, overridable for tests via SUPERVISOR_NAP_CMD
# (a shell command that receives the seconds as argv-1 and is expected
# to skip the wait quickly).
nap() {
  if [[ -n "${SUPERVISOR_NAP_CMD:-}" ]]; then
    bash -c "$SUPERVISOR_NAP_CMD $1"
  else
    sleep "$1"
  fi
}

while true; do
  TICK_START=$(date +%s)

  if run_tick; then
    # Happy path: sleep till next tick (account for tick duration).
    TICK_DUR=$(($(date +%s) - TICK_START))
    SLEEP_FOR=$((POLL_INTERVAL_SEC - TICK_DUR))
    [[ "$SLEEP_FOR" -lt 30 ]] && SLEEP_FOR=30
    nap "$SLEEP_FOR"
    continue
  fi

  # First failure: capture FAIL_KIND, decide whether to enter the ladder.
  read_fail_env
  heartbeat "$TASK_ID" warn "tick failed (FAIL_KIND=${FAIL_KIND:-unknown})"

  if [[ "${FAIL_KIND:-unknown}" == "prereq_fail" ]]; then
    # Daemon-level prereq fail (docker down etc.). The user is the
    # recovery path; quick retries on a daemon-down condition are
    # cheap-but-useless to escalate, so we still run the ladder (it
    # may catch the daemon coming back) but never spawn a janitor.
    heartbeat "$TASK_ID" error "prereq_fail (FAIL_EXIT=${FAIL_EXIT:-?}); ladder will retry but no janitor escalation"
  fi

  # FARM-1.11 quick-retry ladder. Pure bash ticks, no claude -p.
  recovered=0
  for delay in "${QUICK_RETRY_LADDER_SEC[@]}"; do
    heartbeat "$TASK_ID" warn "[backoff] tick failed, quick-retry in ${delay}s"
    nap "$delay"
    if run_tick; then
      heartbeat "$TASK_ID" info "[backoff-recovery] tick succeeded after quick-retry delay=${delay}s"
      recovered=1
      break
    fi
    # Refresh FAIL_KIND for next iteration (tick may have updated it).
    read_fail_env
  done

  if [[ "$recovered" -eq 1 ]]; then
    # Resume the normal poll cadence.
    TICK_DUR=$(($(date +%s) - TICK_START))
    SLEEP_FOR=$((POLL_INTERVAL_SEC - TICK_DUR))
    [[ "$SLEEP_FOR" -lt 30 ]] && SLEEP_FOR=30
    nap "$SLEEP_FOR"
    continue
  fi

  # All quick retries failed → escalate + long pause.
  heartbeat "$TASK_ID" error "[escalate] ${#QUICK_RETRY_LADDER_SEC[@]} consecutive tick failures; invoking claude -p janitor + ${PAUSE_AFTER_PAUSE_SEC}s pause"
  if [[ "${FAIL_KIND:-unknown}" != "prereq_fail" ]]; then
    escalate_to_janitor "${FAIL_KIND:-unknown}" || true
  fi
  nap "$PAUSE_AFTER_PAUSE_SEC"
done
