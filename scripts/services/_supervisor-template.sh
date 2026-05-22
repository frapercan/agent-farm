#!/usr/bin/env bash
# _supervisor-template.sh -- generic persistent-service supervisor.
#
# This file is NOT meant to be run on its own. A concrete service
# (deploy-keeper-supervisor.sh, examples/queue-watcher-supervisor.sh, ...)
# sets a handful of parameters and then `source`s this template; the
# template owns the persistent loop, the quick-retry ladder, the
# escalation-to-janitor path and the long cool-off pause.
#
# Required env / variables the caller MUST set before sourcing:
#   TASK_ID                 task UUID (set by spawn.sh)
#   TICK_SCRIPT             absolute path of the per-tick script to run
#   POLL_INTERVAL          seconds between successful ticks (>=1)
#   MAX_CONSECUTIVE_FAILURES  number of quick-retry rungs before escalate
#   PAUSE_AFTER_PAUSE_SEC  cool-off pause (seconds) after the ladder is
#                          exhausted and the janitor is escalated
#   FAIL_KIND_ENV_FILE     path of the K=V file the tick writes on failure
#                          (read into FAIL_KIND / FAIL_EXIT)
#
# Optional caller hooks (functions). The template calls them if they are
# already defined when it is sourced; otherwise it uses a default:
#   service_nap_between_ticks <seconds>
#       Inter-tick wait. Default: plain nap. deploy-keeper overrides this
#       with its trigger-aware nap so a configured trigger can short-
#       circuit the poll interval. Return 0 to force an early tick.
#   service_escalate <fail_kind>
#       Called once the ladder is exhausted (and FAIL_KIND is not a
#       prereq_fail). Default: spawn a janitor subagent. Override to
#       page a different recovery path.
#
# Optional caller variables:
#   QUICK_RETRY_LADDER_SEC  array of per-rung delays. If unset, the
#       template builds a MAX_CONSECUTIVE_FAILURES-long geometric ladder
#       (30, 120, 300, ... capped). Tests override via
#       QUICK_RETRY_LADDER_OVERRIDE (space-separated seconds).
#   TICK_CMD_OVERRIDE       shell command run instead of TICK_SCRIPT
#       (tests inject a scripted fail/ok stub here).
#   SUPERVISOR_NAP_CMD      shell command run instead of `sleep` (tests
#       inject a virtual-clock advance here). Receives seconds as argv-1.
#
# The template assumes the caller has already sourced lib/common.sh
# (heartbeat, task_set_ended) and set ROOT.

set -uo pipefail

: "${TASK_ID:?TASK_ID env required}"
: "${TICK_SCRIPT:?TICK_SCRIPT required (path of the per-tick script)}"
: "${POLL_INTERVAL:?POLL_INTERVAL required (seconds between ticks)}"
: "${MAX_CONSECUTIVE_FAILURES:?MAX_CONSECUTIVE_FAILURES required}"
: "${PAUSE_AFTER_PAUSE_SEC:?PAUSE_AFTER_PAUSE_SEC required}"
: "${FAIL_KIND_ENV_FILE:?FAIL_KIND_ENV_FILE required}"
ROOT="${ROOT:-${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}}"

# Build the quick-retry ladder if the caller did not supply one.
# QUICK_RETRY_LADDER_OVERRIDE (tests) wins, then a caller-set
# QUICK_RETRY_LADDER_SEC array, then a default geometric ladder sized to
# MAX_CONSECUTIVE_FAILURES (30, 120, 300, then 300 for each extra rung).
if [[ -n "${QUICK_RETRY_LADDER_OVERRIDE:-}" ]]; then
  # shellcheck disable=SC2206
  QUICK_RETRY_LADDER_SEC=($QUICK_RETRY_LADDER_OVERRIDE)
elif [[ -z "${QUICK_RETRY_LADDER_SEC+x}" ]]; then
  QUICK_RETRY_LADDER_SEC=()
  _default_rungs=(30 120 300)
  for ((i = 0; i < MAX_CONSECUTIVE_FAILURES; i++)); do
    if (( i < ${#_default_rungs[@]} )); then
      QUICK_RETRY_LADDER_SEC+=("${_default_rungs[$i]}")
    else
      QUICK_RETRY_LADDER_SEC+=(300)
    fi
  done
fi

heartbeat "$TASK_ID" info "supervisor up; poll_interval=${POLL_INTERVAL}s; quick_retry_ladder=${QUICK_RETRY_LADDER_SEC[*]}s; pause_after=${PAUSE_AFTER_PAUSE_SEC}s"

# Trap: on shutdown, mark task ended cleanly.
trap 'heartbeat "$TASK_ID" info "supervisor stopping (signal)"; task_set_ended "$TASK_ID" "killed" 130; exit 0' INT TERM

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

# run_tick: invoke TICK_SCRIPT. Tests can override TICK_CMD_OVERRIDE with
# a stub shell command without touching production tick logic.
run_tick() {
  if [[ -n "${TICK_CMD_OVERRIDE:-}" ]]; then
    bash -c "$TICK_CMD_OVERRIDE"
  else
    bash "$TICK_SCRIPT"
  fi
}

# read_fail_env: populate FAIL_KIND + FAIL_EXIT from FAIL_KIND_ENV_FILE
# (default unknown when absent).
read_fail_env() {
  FAIL_KIND="unknown"
  FAIL_EXIT="unknown"
  if [[ -f "$FAIL_KIND_ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$FAIL_KIND_ENV_FILE"
  fi
}

# Default escalation: spawn a janitor subagent (haiku) to investigate.
# A concrete service may define service_escalate before sourcing to
# override this. We do NOT block on the janitor.
default_escalate() {
  local fail_kind="$1"
  local spawn_args
  spawn_args=$(jq -Rn \
    --arg task "service-rescue" \
    --arg msg "service $fail_kind fail, see heartbeats for task $TASK_ID" \
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

# Default inter-tick wait: a plain nap. deploy-keeper overrides this with
# its trigger-aware nap. Return 0 to force an early tick.
default_nap_between_ticks() {
  nap "$1"
  return 1
}

# Resolve hooks: prefer a caller-defined function, else the default.
if ! declare -F service_escalate >/dev/null 2>&1; then
  service_escalate() { default_escalate "$@"; }
fi
if ! declare -F service_nap_between_ticks >/dev/null 2>&1; then
  service_nap_between_ticks() { default_nap_between_ticks "$@"; }
fi

# supervisor_main: the persistent loop. The caller sources the template
# and then calls this (or relies on the source running it; we call it at
# the end so a plain `source` starts the service).
supervisor_main() {
  while true; do
    TICK_START=$(date +%s)

    if run_tick; then
      # Happy path: wait till next tick (account for tick duration).
      TICK_DUR=$(($(date +%s) - TICK_START))
      SLEEP_FOR=$((POLL_INTERVAL - TICK_DUR))
      [[ "$SLEEP_FOR" -lt 30 ]] && SLEEP_FOR=30
      service_nap_between_ticks "$SLEEP_FOR" || true
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

    # Quick-retry ladder. Pure-bash ticks, no claude -p.
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
      # Resume the normal poll cadence (with inter-tick hook).
      TICK_DUR=$(($(date +%s) - TICK_START))
      SLEEP_FOR=$((POLL_INTERVAL - TICK_DUR))
      [[ "$SLEEP_FOR" -lt 30 ]] && SLEEP_FOR=30
      service_nap_between_ticks "$SLEEP_FOR" || true
      continue
    fi

    # All quick retries failed -> escalate + long pause.
    heartbeat "$TASK_ID" error "[escalate] ${#QUICK_RETRY_LADDER_SEC[@]} consecutive tick failures; invoking claude -p janitor + ${PAUSE_AFTER_PAUSE_SEC}s pause"
    if [[ "${FAIL_KIND:-unknown}" != "prereq_fail" ]]; then
      service_escalate "${FAIL_KIND:-unknown}" || true
    fi
    nap "$PAUSE_AFTER_PAUSE_SEC"
  done
}

# Start the loop unless the caller asked to defer (SUPERVISOR_DEFER_MAIN=1
# lets a caller add post-source setup before calling supervisor_main).
if [[ "${SUPERVISOR_DEFER_MAIN:-0}" != "1" ]]; then
  supervisor_main
fi
