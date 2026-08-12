#!/usr/bin/env bash
# coord-keeper-supervisor.sh -- persistent loop that runs coord-tick.sh.
#
# FARM-COORD V0, item 5. Structurally the deploy keeper: this file owns only
# the coord-specific parameters and the two service hooks, then sources
# _supervisor-template.sh, which owns the loop, the quick-retry ladder, the
# escalation and the cool-off pause. Do not copy the loop.
#
# The trigger is the ledger branch moving. The probe is `git ls-remote`, one
# round trip with no object transfer, measured on this desktop at 0.61 to 0.82
# seconds; a fetch happens inside the tick and only when the sha changed.
#
# The tick's side of the fail contract (docs/runbook-persistent-service.md):
# write FAIL_KIND and FAIL_EXIT to FAIL_KIND_ENV_FILE before exiting non-zero.
# A remote that cannot be reached MUST be reported as FAIL_KIND=prereq_fail. A
# WAN outage is failure mode 1 of the design, it is not something a janitor can
# fix, and spawning one per outage burns tokens on a router.
#
# Launched by systemd (scripts/services/coord-keeper.service) or by spawn.sh in
# tmux. Reads:
#   TASK_ID          task id; minted here when systemd is the launcher
#   AGENT_FARM_ROOT  default ~/Thesis2/agent-farm
#   COORD_REPO       the KEEPER's own clone, default ~/Thesis2/farm-coord-keeper.
#                    NOT the shared ~/Thesis2/farm-coord a human sends from and
#                    a finishing agent writes its outcome entry in: the tick
#                    resets and cleans this one. See coord-tick.sh's header.
#   COORD_BRANCH     ledger branch name, default 'ledger'

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"

COORD_REPO="${COORD_REPO:-$HOME/Thesis2/farm-coord-keeper}"
COORD_BRANCH="${COORD_BRANCH:-ledger}"
# The tick lives under scripts/coord/, next to the sender and the fence, not
# under scripts/services/ next to this file. Named once, here, and checked
# below, because a wrong path here is invisible: `bash <missing>` exits 127
# without writing the fail-kind file, the template reads FAIL_KIND=unknown,
# unknown is not prereq_fail, and the service escalates a janitor on a ladder
# forever while nothing at all is wrong.
COORD_TICK_SCRIPT="${COORD_TICK_SCRIPT:-$ROOT/scripts/coord/coord-tick.sh}"

# Configuration checks before any state is written. Neither of these fixes
# itself, so exit 78 (EX_CONFIG) and let RestartPreventExitStatus stop the unit
# rather than loop every thirty seconds. Ordered ahead of the task row so a
# refusal to start leaves no row stuck in 'running'.
if [[ ! -d "$COORD_REPO/.git" ]]; then
  echo "coord-keeper: no keeper clone at $COORD_REPO" >&2
  echo "coord-keeper: create it with 'git clone <farm-coord remote> $COORD_REPO'," >&2
  echo "coord-keeper: or set COORD_REPO in the unit's Environment. It must be the" >&2
  echo "coord-keeper: keeper's OWN clone, never the one you run coord-send.sh in." >&2
  exit 78
fi
if [[ ! -f "$COORD_TICK_SCRIPT" ]]; then
  echo "coord-keeper: no tick script at $COORD_TICK_SCRIPT" >&2
  exit 78
fi
# The machine name, checked HERE and not left to the tick. The tick does check
# it, but the template treats only prereq_fail specially: a config_fail goes
# down the quick-retry ladder and escalates a janitor after seven minutes, so
# the unit sits there reporting 'active' while being permanently misconfigured.
# Measured on the first install on 2026-08-12: the service ran for three minutes
# in that state with an empty journal, because heartbeats go to the state
# database and nothing was reaching stderr. A name that will never appear on its
# own is a configuration error, and a configuration error should stop the unit
# loudly on the first pass.
COORD_MACHINE_FILE="${COORD_MACHINE_FILE:-$ROOT/state/coord-machine}"
COORD_MACHINE_NAME="${COORD_MACHINE:-$(cat "$COORD_MACHINE_FILE" 2>/dev/null || true)}"
COORD_MACHINE_NAME="${COORD_MACHINE_NAME//[[:space:]]/}"
if [[ ! "$COORD_MACHINE_NAME" =~ ^[a-z][a-z0-9-]{0,31}$ ]]; then
  echo "coord-keeper: this machine has no usable coordination name." >&2
  echo "coord-keeper: got '${COORD_MACHINE_NAME:-<empty>}' from $COORD_MACHINE_FILE" >&2
  echo "coord-keeper: write one plain lower-case word there, for example:" >&2
  echo "coord-keeper:   echo desktop > $COORD_MACHINE_FILE" >&2
  echo "coord-keeper: the hostname is deliberately NOT a fallback: it routes every" >&2
  echo "coord-keeper: claim, so it is declared rather than guessed." >&2
  exit 78
fi

# spawn.sh sets TASK_ID; systemd does not, and heartbeats carry a foreign key
# onto tasks, so under systemd we mint the row ourselves rather than write
# heartbeats that the insert would reject.
if [[ -z "${TASK_ID:-}" ]]; then
  TASK_ID="$(make_task_id coord-keeper)"
  task_insert "$TASK_ID" coord-keeper headless 1 "" '{"launched_by":"systemd"}'
  task_set_started "$TASK_ID" "" "" "$$"
fi
# EXPORTED, not just set: the template runs the tick as `bash "$TICK_SCRIPT"`,
# a child process, and the tick's first act is TASK_ID="${TASK_ID:?...}". Under
# spawn.sh the variable arrives already in the environment and this is a no-op;
# under systemd it is the difference between a working service and a tick that
# dies on line one of every pass.
export TASK_ID

COORD_LSREMOTE_TIMEOUT_SEC="${COORD_LSREMOTE_TIMEOUT_SEC:-30}"
# Cadence of the ls-remote probe inside the inter-tick nap. At the 15s poll
# this fires once per nap; it exists so the interval can be raised (the design
# says 60s on a machine with no capacity) without losing the fast path.
COORD_PROBE_INTERVAL_SEC="${COORD_PROBE_INTERVAL_SEC:-15}"
# Last-seen ledger sha, one file, kept under state/ so it survives a restart.
COORD_STATE_DIR="${COORD_STATE_DIR:-$ROOT/state/coord-keeper}"
mkdir -p "$COORD_STATE_DIR" 2>/dev/null || true
COORD_SHA_FILE="$COORD_STATE_DIR/sha_${COORD_BRANCH//\//_}"

POLL_INTERVAL_SEC="${COORD_POLL_INTERVAL_SEC:-15}"

if [[ -n "${QUICK_RETRY_LADDER_OVERRIDE:-}" ]]; then
  # shellcheck disable=SC2206
  QUICK_RETRY_LADDER_SEC=($QUICK_RETRY_LADDER_OVERRIDE)
else
  QUICK_RETRY_LADDER_SEC=(30 120 300)
fi

# coord_ledger_moved: 0 when the remote ledger tip differs from the last one we
# recorded. Side effect: records the new tip.
#
# First sighting arms without firing, exactly as the deploy keeper does: at boot
# every sha is new and the first tick has already read the inbox, so firing here
# would tick twice on every restart.
#
# A failed probe is a skip and not a failure. The supervisor stays up through a
# WAN outage and the poll interval still ticks; only the fast path is lost.
#
# Recording the sha before the tick runs cannot lose a message: the sha decides
# only WHEN to tick, and every tick rescans the whole inbox regardless.
coord_ledger_moved() {
  local sha prev=""
  # shellcheck disable=SC2086
  sha=$(GIT_TERMINAL_PROMPT=0 timeout "$COORD_LSREMOTE_TIMEOUT_SEC" \
        ${COORD_GIT_CMD:-git} -C "$COORD_REPO" ls-remote origin \
        "refs/heads/$COORD_BRANCH" 2>/dev/null | awk 'NR==1{print $1}')
  [[ -z "$sha" ]] && return 1
  [[ -f "$COORD_SHA_FILE" ]] && prev=$(<"$COORD_SHA_FILE")
  printf '%s' "$sha" > "$COORD_SHA_FILE"
  [[ -z "$prev" ]] && return 1
  [[ "$prev" == "$sha" ]] && return 1
  heartbeat "$TASK_ID" info "[trigger] new_commit_on origin/$COORD_BRANCH: ${prev:0:7} -> ${sha:0:7}"
  return 0
}

# Template hook. Two jobs: probe the ledger between sleep chunks so a message
# lands within one probe interval, and cap the wait at the poll interval,
# because the template floors its own SLEEP_FOR at 30 seconds and this service
# polls at 15.
service_nap_between_ticks() {
  local remaining="$1"
  (( remaining > POLL_INTERVAL_SEC )) && remaining="$POLL_INTERVAL_SEC"
  local chunk
  while (( remaining > 0 )); do
    if coord_ledger_moved; then
      return 0
    fi
    chunk="$COORD_PROBE_INTERVAL_SEC"
    (( chunk > remaining )) && chunk="$remaining"
    nap "$chunk"
    remaining=$((remaining - chunk))
  done
  coord_ledger_moved
}

heartbeat "$TASK_ID" info "coord-keeper up; repo=$COORD_REPO branch=$COORD_BRANCH poll=${POLL_INTERVAL_SEC}s"

# Template parameters. shellcheck cannot see through the dynamic source below,
# so it flags these as unused; the template consumes them all.
# shellcheck disable=SC2034
{
TICK_SCRIPT="$COORD_TICK_SCRIPT"
TICK_CMD_OVERRIDE="${COORD_KEEPER_TICK_CMD:-}"
POLL_INTERVAL="$POLL_INTERVAL_SEC"
MAX_CONSECUTIVE_FAILURES="${#QUICK_RETRY_LADDER_SEC[@]}"
# Ten minutes, not the deploy keeper's thirty. After the ladder the fault is
# almost always the WAN hop, a retry is one round trip and costs nothing, and
# every minute of cool-off is a minute in which neither machine can be reached.
PAUSE_AFTER_PAUSE_SEC="${COORD_PAUSE_AFTER_SEC:-600}"
# Under the state directory, not /tmp. The template SOURCES this file, so a
# world-writable location is a shell injection into a service that runs as the
# user. The tick writes the same default.
FAIL_KIND_ENV_FILE="${COORD_KEEPER_FAIL_ENV:-$COORD_STATE_DIR/last-fail.env}"
}

# Source the template relative to THIS script, not $ROOT, so a test that points
# AGENT_FARM_ROOT at a fake scaffold still loads the real loop.
SUPERVISOR_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_supervisor-template.sh
source "$SUPERVISOR_SELF_DIR/_supervisor-template.sh"
