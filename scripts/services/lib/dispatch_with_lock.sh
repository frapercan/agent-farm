#!/usr/bin/env bash
# dispatch_with_lock.sh -- conductor-side wrapper for export dispatch (FARM-FEAT.13).
#
# Prevents the 2026-05-23 17:12 incident where bioinfo-quick called POST /v1/datasets
# without holding the stack-owner lock. Deploy-keeper saw owner=free, redeployed
# mid-export, and killed the in-flight EXP.13 training worker.
#
# Usage:
#   source dispatch_with_lock.sh          # use the function
#   dispatch_with_lock <task_id> <reason> -- <command...>
#
# CLI usage (also supported):
#   bash dispatch_with_lock.sh <task_id> <reason> -- <command...>
#
# Exit codes:
#   0   command succeeded; lock released.
#   1   bad arguments or lock acquire error (misconfigured).
#   2   lock already held by a different owner; command was NOT run.
#   N   any other exit: command exited with code N; lock STILL released.
#
# The trap-EXIT block guarantees release even if the wrapped command is
# killed by SIGTERM, SIGINT, or a shell error. Do NOT hold the lock
# indefinitely without re-running this wrapper (or calling stack_owner_release
# directly) if the process is killed without a clean EXIT.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=../../lib/stack_owner.sh
source "$ROOT/scripts/lib/stack_owner.sh"

# dispatch_with_lock <task_id> <reason> -- <command...>
#
# Acquires the stack-owner lock as owner=export under <task_id>, runs
# <command...>, then releases in a trap-EXIT so the lock is always freed.
# If the lock is already held by a different task_id, exits 2 with a
# diagnostic message that includes the current holder's task_id and
# acquired_at timestamp so the operator knows who to ask.
dispatch_with_lock() {
  local task_id="${1:-}"
  local reason="${2:-}"
  shift 2 || true

  # Consume the "--" separator.
  if [[ "${1:-}" == "--" ]]; then
    shift
  else
    printf 'dispatch_with_lock: expected "--" separator after reason; got %q\n' "${1:-}" >&2
    printf 'usage: dispatch_with_lock <task_id> <reason> -- <command...>\n' >&2
    return 1
  fi

  if [[ -z "$task_id" || -z "$reason" ]]; then
    printf 'dispatch_with_lock: task_id and reason are required\n' >&2
    printf 'usage: dispatch_with_lock <task_id> <reason> -- <command...>\n' >&2
    return 1
  fi

  if [[ $# -eq 0 ]]; then
    printf 'dispatch_with_lock: no command given after "--"\n' >&2
    return 1
  fi

  # Attempt acquire.
  local acquire_rc=0
  stack_owner_acquire export "$task_id" "$reason" || acquire_rc=$?

  if [[ "$acquire_rc" == "2" ]]; then
    # Contention: a different task holds the lock.
    local owner_task owner_at
    owner_task=$(_stack_owner_read_field task_id)
    owner_at=$(_stack_owner_read_field acquired_at)
    printf 'dispatch_with_lock: CANNOT dispatch -- stack lock held by task_id=%s (acquired_at=%s)\n' \
      "$owner_task" "$owner_at" >&2
    printf 'Wait for that task to finish and release, or run:\n' >&2
    printf '  bash %s/scripts/lib/stack_owner.sh release %s\n' "$ROOT" "$owner_task" >&2
    return 2
  fi

  if [[ "$acquire_rc" != "0" ]]; then
    printf 'dispatch_with_lock: stack_owner_acquire failed (exit %s); aborting dispatch\n' \
      "$acquire_rc" >&2
    return 1
  fi

  # Lock acquired. Register release on EXIT so it is always freed.
  _DWL_TASK_ID="$task_id"
  _DWL_ROOT="$ROOT"
  trap '_dispatch_with_lock_cleanup' EXIT

  local cmd_rc=0
  "$@" || cmd_rc=$?

  # EXIT trap fires here and calls _dispatch_with_lock_cleanup.
  return "$cmd_rc"
}

_dispatch_with_lock_cleanup() {
  local rc=$?
  stack_owner_release "${_DWL_TASK_ID:-}" 2>/dev/null || true
  exit "$rc"
}

# CLI dispatcher. When sourced, this block is a no-op.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  if [[ $# -lt 3 ]]; then
    cat <<EOF
dispatch_with_lock.sh -- conductor-side stack-lock wrapper (FARM-FEAT.13)

Usage:
  dispatch_with_lock.sh <task_id> <reason> -- <command...>

Arguments:
  task_id    unique identifier for this dispatch run (e.g. farm-exp-14)
  reason     short human-readable label (e.g. "FARM-EXP.14 24-cell sweep")
  command    the dispatch command to run (e.g. POST /v1/datasets ...)

Exit codes:
  0   command succeeded
  2   lock contended; command not run; check current owner with:
        bash scripts/lib/stack_owner.sh status
  N   command failed with code N; lock released
EOF
    exit 1
  fi
  dispatch_with_lock "$@"
  exit $?
fi
