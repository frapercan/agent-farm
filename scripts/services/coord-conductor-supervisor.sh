#!/usr/bin/env bash
# coord-conductor-supervisor.sh -- keeps coord-conductor-tick.sh ticking.
#
# Deliberately not built on _supervisor-template.sh: that template is written
# for services spawned by spawn.sh and expects TASK_ID and the farm's task
# bookkeeping. This one is started by systemd directly and owns nothing but a
# sleep. The tick is idempotent and holds its own lock, so the supervisor's only
# jobs are to keep calling it and to exit 78 on a misconfiguration that a retry
# cannot fix, matching the keeper's contract with systemd.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TICK="$ROOT/scripts/services/coord-conductor-tick.sh"
INTERVAL="${COORD_CONDUCTOR_INTERVAL:-20}"

# Exit 78 (EX_CONFIG) is the keeper's convention for "a restart will not help".
# RestartPreventExitStatus=78 in the unit turns this into a stop with a message
# rather than a loop, which is what the missing-clone case already does there.
[[ -f "$TICK" ]] || { echo "coord-conductor: tick script missing at $TICK" >&2; exit 78; }

echo "coord-conductor: supervising $TICK every ${INTERVAL}s"
while true; do
  out=$(bash "$TICK" 2>&1)
  rc=$?
  # 78 from the tick is also a misconfiguration (no claude binary); pass it up
  # rather than looping on something a retry cannot fix.
  [[ "$rc" = "78" ]] && { echo "coord-conductor: $out" >&2; exit 78; }
  # Silence on the routine cases keeps the journal readable: the interesting
  # lines are in the tick's own log, and "nothing pending" every 20 seconds
  # would bury them.
  case "$out" in
    "nothing pending"|"busy"|disabled*) : ;;
    *) [[ -n "$out" ]] && echo "coord-conductor: $out" ;;
  esac
  sleep "$INTERVAL"
done
