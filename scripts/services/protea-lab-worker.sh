#!/usr/bin/env bash
# Start one PROTEA queue worker on the compute node.
#
# The compute node holds no state. It joins the persistent server's queues,
# computes, and publishes results back. Everything it needs to know is the
# broker and database of the server, which come from the node's environment
# file, and the name of the queue to consume, which is this script's argument.
#
# Run through systemd rather than by hand: see protea-lab-worker@.service in
# this directory. Started by hand a worker dies with the terminal that started
# it, and a machine that is also used for other things will be rebooted.
#
# Usage:
#   bash protea-lab-worker.sh protea.embeddings.batch
#
# Overridable for testing:
#   PROTEA_LAB_ENV         path to the node's environment file
#   PROTEA_REPO            path to the PROTEA checkout
#   POETRY_BIN             path to the poetry executable
#   PROTEA_LAB_CLOCK_WAIT  seconds to wait for a synchronised clock, default 120,
#                          capped at 600, 0 disables the wait
set -euo pipefail

QUEUE="${1:?usage: protea-lab-worker.sh <queue-name>}"

ENV_FILE="${PROTEA_LAB_ENV:-${HOME}/.secrets/protea-lab.env}"
if [[ ! -r "${ENV_FILE}" ]]; then
  echo "protea-lab-worker: cannot read environment file ${ENV_FILE}" >&2
  echo "protea-lab-worker: it must define PROTEA_DB_URL and PROTEA_AMQP_URL" >&2
  exit 78   # EX_CONFIG: a configuration problem, not a transient failure
fi

# The file is shell, with `export` prefixes, so it is sourced rather than
# handed to systemd's EnvironmentFile, which does not accept them.
set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a

: "${PROTEA_DB_URL:?the environment file does not define PROTEA_DB_URL}"
: "${PROTEA_AMQP_URL:?the environment file does not define PROTEA_AMQP_URL}"

# The tree this worker RUNS. It defaults to the deploy slot and not to the
# developer workspace, and the difference is not cosmetic.
#
# WHAT THIS DEFAULT USED TO BE, AND WHAT IT COST. Until 2026-09-02 it was
# ${HOME}/Thesis2/repositories/PROTEA, the developer workspace, while
# protea-node-sync.sh read the SAME variable with a DIFFERENT default,
# ${HOME}/Thesis2/worktrees/protea-deploy. Neither the unit nor the environment
# file set the variable, so the two scripts silently disagreed: the sync guard
# checked out, verified and reported the declared revision on a tree that no
# process ever executed, while the worker ran whatever the developer workspace
# happened to be checked out at. On the morning of 2026-09-02 that was #801,
# three months behind, and it does not contain code_revision.py, so the worker
# had no revision guard at all. It completed seven of seven batches of a
# declared experiment and the record says they succeeded.
#
# One name with two defaults is the same defect this project has already found
# in a `depth` column that fused three quantities. The fix is not a better
# default: it is that the process refuses when it cannot show that it is running
# what the server declared.
REPO="${PROTEA_REPO:-${HOME}/Thesis2/worktrees/protea-deploy}"
if [[ ! -d "${REPO}" ]]; then
  echo "protea-lab-worker: no PROTEA checkout at ${REPO}" >&2
  exit 78
fi
cd "${REPO}"

# --- refuse to consume from a tree the server did not declare ----------------
#
# A guard that does not share a tree with the process it guards is not a guard,
# it is a report about something else. This is the same comparison
# protea-node-sync.sh makes before it syncs, made again here by the process that
# will actually execute the code, because the sync running is not evidence that
# the worker inherited it.
#
# It does NOT fetch. The timer keeps origin/main fresh; a network round trip on
# every worker start would make the queue depend on the link being up. Reading a
# slightly stale declaration and refusing is safe. Reading none is not.
FARM="${PROTEA_FARM:-${HOME}/Thesis2/agent-farm}"
DECL_PATH="${PROTEA_DECL_PATH:-plans/DECLARED-REVISION.txt}"
if [[ -d "${FARM}/.git" ]]; then
  DECL="$(git -C "${FARM}" show "origin/main:${DECL_PATH}" 2>/dev/null \
          | awk '$1 == "coordinator" { print $2; exit }')"
  if [[ -z "${DECL}" ]]; then
    echo "protea-lab-worker: ${DECL_PATH} on agent-farm origin/main names no coordinator; refusing to consume" >&2
    exit 78
  fi
  HEAD_SHA="$(git -C "${REPO}" rev-parse HEAD 2>/dev/null || true)"
  if [[ "${HEAD_SHA}" != "${DECL}" ]]; then
    echo "protea-lab-worker: this tree is ${HEAD_SHA:0:12} and the server declares ${DECL:0:12}; refusing to consume" >&2
    echo "protea-lab-worker: tree=${REPO}. Let protea-node-sync follow the declaration, or fix PROTEA_REPO." >&2
    exit 78
  fi
else
  echo "protea-lab-worker: no agent-farm clone at ${FARM}, so the declaration cannot be read; refusing to consume" >&2
  exit 78
fi

POETRY="${POETRY_BIN:-${HOME}/.local/bin/poetry}"
if [[ ! -x "${POETRY}" ]]; then
  echo "protea-lab-worker: poetry not executable at ${POETRY}" >&2
  exit 78
fi

# The clock gate.
#
# This desktop dual-boots, and Windows writes LOCAL time to the hardware clock.
# After a Windows session the Linux kernel reads that RTC as UTC, so the system
# clock comes up exactly two hours fast and stays that way until chronyd steps
# it. Measured here on 2026-08-29: the kernel set the clock from the RTC at
# 05:46:04, systemd started this unit at 05:46:11, the worker consumed a job and
# wrote three events at 05:46:20, and chronyd stepped the clock by -7199.5
# seconds at 05:46:23. Those three rows are stamped two hours in the future and
# nothing downstream can tell them from real ones. Two episodes in 798,081
# events, both on this node, both about two hours wide.
#
# The gate lives here and not in the unit file because that is a USER unit, and
# a user manager has no time-sync.target to order against: `systemctl --user
# show time-sync.target -p LoadState` reports not-found on this machine. An
# `After=time-sync.target` there would order against nothing while reading to
# every future maintainer as a gate that runs.
#
# NTPSynchronized is the kernel's own STA_UNSYNC bit read through adjtimex, not
# anything chrony-specific, so this is the same clock the worker will stamp its
# events with and it keeps working if the node ever changes NTP client.
# `timedatectl timesync-status` is NOT usable here: it requires
# systemd-timesyncd, and this machine runs chrony.
#
# THE GATE NEVER REFUSES TO START, and in particular it never exits 78. A node
# that is up, looks healthy and consumes nothing is the failure this project has
# actually paid for; three events with a skewed timestamp, twice in 798,081, is
# not. Exit 78 would stop the unit until a human noticed, and any other non-zero
# exit would restart into the same wait every thirty seconds forever while the
# queue sat without a consumer. So every path below ends with the worker
# running, and a permanently broken NTP degrades to exactly the behaviour of the
# day before this gate existed, loudly. If you are tempted to add an exit here,
# that is the trade you would be making.
#
# The budget is 120 seconds against a measured exposure of 12 to 19, so about
# six times the fast path. On a cold boot chronyd needs an address, a resolver
# and possibly a key exchange before it has a single sample, and the user
# manager waits for none of that. It costs nothing when the clock is already
# good, and it does not interact with TimeoutStartSec because Type=simple makes
# the unit active the moment bash is forked. If the unit ever becomes
# Type=notify or Type=forking, revisit that.
CLOCK_WAIT_SECONDS="${PROTEA_LAB_CLOCK_WAIT:-120}"
# Validated because the environment file was sourced above and can set this. An
# unvalidated value reaches an arithmetic context, where a string is a syntax
# error, and under `set -e` an arithmetic syntax error ends the script: the
# guard against a skewed clock would have become a new way to keep the node
# down.
if [[ ! "${CLOCK_WAIT_SECONDS}" =~ ^[0-9]+$ ]]; then
  echo "protea-lab-worker: PROTEA_LAB_CLOCK_WAIT wants whole seconds, got '${CLOCK_WAIT_SECONDS}'; using 120" >&2
  CLOCK_WAIT_SECONDS=120
fi
# Forced to base ten and then capped, and both halves are load-bearing. Bash
# arithmetic reads a leading zero as octal, so `0120` is eighty and `09` is not a
# number at all; the syntax check above accepts all three. And the budget is the
# one number in this gate that can hold the node off its queue, so a value read
# from a hand-edited environment file must not be able to do that without a
# ceiling: 1200 was a plausible "give NTP plenty of time" and it buys twenty
# minutes of a unit sitting in `active (running)`, absent from --failed, silent
# in the log, consuming nothing. 600 is fifty times the measured need, so
# anything above it is a typo rather than an intent, and the cap degrades toward
# consuming rather than toward waiting.
CLOCK_WAIT_SECONDS=$(( 10#${CLOCK_WAIT_SECONDS} ))
if (( CLOCK_WAIT_SECONDS > 600 )); then
  echo "protea-lab-worker: PROTEA_LAB_CLOCK_WAIT=${CLOCK_WAIT_SECONDS} would hold this node off the queue for longer than any clock takes to settle; capping at 600" >&2
  CLOCK_WAIT_SECONDS=600
fi

# The skew is created exactly once per boot, when the kernel reads the RTC, so a
# worker that has already sat out the whole budget has nothing left to learn by
# sitting out another. This is not a micro-optimisation. The unit restarts every
# thirty seconds for as long as the server is unreachable, a state it is built to
# sit in for hours, and without this marker a node with permanently broken NTP
# would add two minutes to every one of those retries and take 150 seconds
# rather than 30 to notice the server come back. The marker can only ever cause
# LESS waiting, never more and never a refusal, so a stale one degrades in the
# safe direction. XDG_RUNTIME_DIR is tmpfs and is recreated at boot, which is
# where "once per boot" comes from with no expiry logic of its own, and the
# marker is removed the moment any start sees a synchronised clock.
#
# Scoped to the QUEUE, because this node runs several instances of the template
# at once: on 2026-08-29 systemd started @protea.evaluations and
# @protea.predictions.batch in the same millisecond. An unscoped marker lets the
# first instance to give up disarm the gate for every other instance on that
# boot, which is a gate that reads as a gate in this file and does not fire.
CLOCK_MARKER="${XDG_RUNTIME_DIR:-/tmp}/protea-lab-worker.${QUEUE}.clock-unsynced"
CLOCK_NOTE=""
if [[ -e "${CLOCK_MARKER}" ]]; then
  CLOCK_WAIT_SECONDS=0
  CLOCK_NOTE=" (this queue's worker already waited the full budget out on this boot)"
fi

clock_synchronised() {
  # Three ways this bites under `set -euo pipefail`, so, in order:
  #   - an assignment from a failing command substitution takes the whole script
  #     down, so the status is swallowed INSIDE the substitution and the answer
  #     judged as text instead;
  #   - timedatectl prints "yes", "no", or NOTHING AT ALL while exiting 0, which
  #     is what an unrecognised property looks like on another systemd, so only
  #     the literal "yes" may be read as synchronised;
  #   - a wedged system bus would otherwise block for sd-bus's own patience on
  #     every probe, which across a whole budget is the outage this gate exists
  #     to prevent, so each probe is bounded on its own.
  # Only ever call this as a condition, never bare: it returns 1 by design.
  local answer
  answer="$(timeout 5 timedatectl show -p NTPSynchronized --value 2>/dev/null || true)"
  [[ "${answer}" == "yes" ]]
}

# Three verdicts, not two. "unchecked" has to stay distinct from "unsynced" so
# that a node missing a tool says that once, rather than also claiming a clock is
# wrong when it has no way to know.
CLOCK_VERDICT=unchecked
CLOCK_HELD=no
CLOCK_WAITED=0
CLOCK_STEP=0
CLOCK_UP0=0
CLOCK_WALL0=0
if ! command -v timedatectl >/dev/null 2>&1; then
  echo "protea-lab-worker: WARNING no timedatectl, so the clock cannot be checked; starting anyway" >&2
elif ! command -v timeout >/dev/null 2>&1; then
  echo "protea-lab-worker: WARNING no timeout(1), so a probe could not be bounded; starting anyway rather than let a wedged system bus hold this node off the queue" >&2
elif ! read -r CLOCK_UP0 _clock_rest < /proc/uptime 2>/dev/null; then
  echo "protea-lab-worker: WARNING cannot read /proc/uptime, so a wait could not be bounded safely; starting anyway" >&2
else
  # Both baselines are sampled here, in the same breath and BEFORE the first
  # probe. The step is the difference between how far each of the two clocks
  # moved, so a pair taken at different instants manufactures a step that never
  # happened.
  CLOCK_UP0="${CLOCK_UP0%%.*}"
  CLOCK_WALL0="$(date +%s 2>/dev/null || true)"

  if clock_synchronised; then
    CLOCK_VERDICT=ok
  else
    CLOCK_VERDICT=unsynced
    if (( CLOCK_WAIT_SECONDS > 0 )); then
      CLOCK_HELD=yes
      echo "protea-lab-worker: clock NOT synchronised (up ${CLOCK_UP0}s, reads $(date -Is)); holding this worker off queue=${QUEUE} for up to ${CLOCK_WAIT_SECONDS}s rather than stamp events with a clock that is about to move" >&2
    fi

    # Elapsed time comes from /proc/uptime, which is CLOCK_BOOTTIME, and never
    # from the wall clock, because the wall clock is the thing under test. A
    # deadline computed as `date +%s` plus a budget would, at the instant chronyd
    # steps the clock back by 7,199 seconds, conclude it had two hours of budget
    # left, and this loop sits on the one path that must never hang. Bash's own
    # $SECONDS has the same defect for the same reason. `sleep` is safe here
    # because a relative sleep is resolved against the monotonic clock too.
    #
    # The poll count is a second and independent bound, and it is the loop
    # condition rather than the elapsed check, so the loop terminates even if the
    # arithmetic inside it is ever wrong. The cost of this loop not ending is the
    # node never consuming, which is the one outcome that is not allowed. A zero
    # budget, which is what the marker above sets, runs it zero times.
    clock_polls=0
    while (( clock_polls < CLOCK_WAIT_SECONDS )); do
      sleep 1
      # Never `(( clock_polls++ ))`: that arithmetic command returns 1 on the
      # pass where the value was still 0, and under `set -e` the first turn of
      # this loop would kill the script.
      clock_polls=$(( clock_polls + 1 ))
      if clock_synchronised; then
        CLOCK_VERDICT=ok
        break
      fi
      # Guarded, because an unguarded failing redirection would end the script
      # and a fallback value could hold the loop open. Neither is acceptable
      # here, so a read that fails ends the wait and starts the worker.
      if ! read -r clock_now _clock_rest < /proc/uptime 2>/dev/null; then
        echo "protea-lab-worker: WARNING /proc/uptime went unreadable mid-wait; ending the wait and starting anyway" >&2
        break
      fi
      if (( ${clock_now%%.*} - CLOCK_UP0 >= CLOCK_WAIT_SECONDS )); then
        break
      fi
    done
  fi

  # Measured once, on every path that got as far as a baseline, so the two
  # figures always share it. How far the wall clock moved BEYOND what the wait
  # itself accounts for is the size of chronyd's step, and it is measurable this
  # way and no other: hwclock is not installed on this machine, only its manual
  # page, a unit stub and a completion file survive.
  if read -r clock_now _clock_rest < /proc/uptime 2>/dev/null; then
    CLOCK_WAITED=$(( ${clock_now%%.*} - CLOCK_UP0 ))
  fi
  clock_wall1="$(date +%s 2>/dev/null || true)"
  if [[ "${CLOCK_WALL0}" =~ ^[0-9]+$ && "${clock_wall1}" =~ ^[0-9]+$ ]]; then
    CLOCK_STEP=$(( (clock_wall1 - CLOCK_WALL0) - CLOCK_WAITED ))
  fi
fi

if [[ "${CLOCK_VERDICT}" == "ok" ]]; then
  rm -f "${CLOCK_MARKER}" 2>/dev/null || true
  # Only when this start actually held the worker back. Without the flag a first
  # probe that happened to take over a second would announce a wait on a start
  # where nothing waited.
  if [[ "${CLOCK_HELD}" == "yes" ]]; then
    echo "protea-lab-worker: clock synchronised after ${CLOCK_WAITED}s of waiting" >&2
  fi
elif [[ "${CLOCK_VERDICT}" == "unsynced" ]]; then
  touch "${CLOCK_MARKER}" 2>/dev/null || true
  echo "protea-lab-worker: WARNING clock still unsynchronised after ${CLOCK_WAITED}s${CLOCK_NOTE}. Starting anyway, because a queue with no consumer costs this project more than a wrong timestamp does. Events from this process may carry whatever skew the hardware clock was holding; this machine dual-boots, so check 'timedatectl status' and chronyd." >&2
  # Only on the start that actually waited, not on every marker-suppressed
  # restart after it. The unit restarts every thirty seconds while the server is
  # unreachable, and a fourteen-line dump on each of those is about 1,800 lines
  # an hour into a file the README itself says does not rotate and the throughput
  # analysis parses. Failing to explain the problem must not become the problem,
  # which is also why the dump is bounded and wrapped in `|| true`.
  if [[ "${CLOCK_HELD}" == "yes" ]] && command -v chronyc >/dev/null 2>&1; then
    timeout 5 chronyc tracking 2>&1 | sed 's/^/protea-lab-worker:   /' >&2 || true
  fi
fi

# The line a reader needs a month later. The two episodes took most of a day to
# find, and what cracked them was noticing that timestamps ran backwards inside
# one log file. Nothing announced the skew while it was happening.
if (( CLOCK_STEP <= -2 || CLOCK_STEP >= 2 )); then
  echo "protea-lab-worker: the system clock STEPPED by ${CLOCK_STEP}s during this startup. Lines above this one carry the old clock, lines below the corrected one." >&2
  # Rounded to the NEAREST hour, not truncated. The real step is a whole number
  # of hours minus the genuine drift, so 7200 arrives as 7199, and division
  # toward zero would call that one hour with a 3599 second remainder and
  # suppress the hint on the exact case it exists for.
  clock_abs=${CLOCK_STEP#-}
  clock_hours=$(( (clock_abs + 1800) / 3600 ))
  clock_slop=$(( clock_abs - clock_hours * 3600 )); clock_slop=${clock_slop#-}
  if (( clock_hours >= 1 && clock_hours <= 14 && clock_slop <= 60 )); then
    echo "protea-lab-worker: a step of ${clock_hours}h is the dual boot: Windows leaves LOCAL time in the hardware clock and Linux reads it as UTC." >&2
  fi
fi

# The clock verdict rides on the line that already anchors every per-batch
# timing rather than on a line of its own: the timestamp here is the first one
# anybody trusts, so it should say how far to trust it. "ok" is a synchronised
# clock, "unsynced" means the wait ran out, "unchecked" means the check itself
# could not run. The token is appended, so anything already parsing this line
# keeps working, and `grep 'clock=unsynced'` over the logs is the investigation.
echo "protea-lab-worker: starting queue=${QUEUE} repo=${REPO} at $(date -Is) clock=${CLOCK_VERDICT}"
# JSON and not text. The platform's own default is json, and a text line is
# invisible to any log pipeline that filters on structure: a Loki rule written
# as `| json | level="error"` never matches one. The first version of this
# script passed --log-format text and would have made the compute node the one
# machine whose failures no dashboard could see.
exec "${POETRY}" run python scripts/worker.py --queue "${QUEUE}" --log-format json
