#!/usr/bin/env bash
# Keep this compute node on the revision the server's workers are running.
#
# The two machines share exactly one repository, agent-farm, so that is where
# the declaration lives. Assistant memory does not cross machines and nothing
# here pulls on its own, which is why this runs on a timer instead of being
# remembered.
#
# The declaration names ONE thing, the coordinator commit the server's workers
# are running. Every internal dependency follows from that commit's own
# poetry.lock, because the lockfile is already the authority and a second list
# is a second thing to disagree with. A dependency line in the file overrides
# the lockfile for that package, for the case where the server is knowingly
# ahead of its own lock.
#
# EVERY WORKER THAT RUNS FROM THE SLOT MOVES WITH IT. Until 2026-11-04 this
# script stopped and restarted one unit, the queue it was configured for, while
# every worker on the node runs out of the same deploy slot. The others kept the
# modules they had already imported and would read any later import from the new
# tree, which is a revision nobody declared. That day a deploy left the methods
# worker on 6f7e1856 under a tree at 96354170, and the predictions, evaluations
# and training workers were restarted by hand after both deploys. So the units
# are derived, not listed: every protea-lab-worker@ instance whose working
# directory is the slot. Those that were running are stopped together and
# started together; those that were stopped on purpose stay stopped.
#
# AND EVERY ENVIRONMENT THOSE WORKERS RUN IN. A unit names its interpreter with
# VIRTUAL_ENV in its own environment, or runs in PROTEA_VENV. On the compute node
# the predictions, evaluations and training workers run a Python 3.12
# environment beside the 3.14 one, and only the 3.14 one followed the lockfile;
# the other was brought up to date by hand after a deploy, or not at all.
#
# Nothing here is best effort. Every step that changes the node is gated on the
# exit status of the check in front of it, and a check that cannot run is a
# refusal, never an assumption.

set -euo pipefail

FARM="${PROTEA_FARM:-${HOME}/Thesis2/agent-farm}"
SLOT="${PROTEA_REPO:-${HOME}/Thesis2/worktrees/protea-deploy}"
VENV="${PROTEA_VENV:-${HOME}/.cache/pypoetry/virtualenvs/protea-M-JALCmz-py3.12}"
QUEUE="${PROTEA_QUEUE:-protea.predictions.batch}"
UNIT="protea-lab-worker@${QUEUE}.service"
DECL_PATH="${PROTEA_DECL_PATH:-plans/DECLARED-REVISION.txt}"
LOGDIR="${PROTEA_LOGDIR:-${HOME}/Thesis2/storage/logs}"
STATE="${LOGDIR}/node-sync.state"
PY="${VENV}/bin/python"
UV="${PROTEA_UV:-${HOME}/.local/bin/uv}"
DRYRUN="${PROTEA_SYNC_DRYRUN:-0}"
# A local declaration, for rehearsing a move without committing one. It can
# only drive a dry run: a declaration nobody committed is not a declaration.
DECL_FILE="${PROTEA_DECL_FILE:-}"
[[ -z "${DECL_FILE}" ]] || DRYRUN=1

# A batch whose log moved less than this long ago is worth waiting a tick for
# rather than interrupting. A batch consumer writes a line per batch, so a log
# silent for longer than this is not progress, it is a stall, and the sync goes
# ahead.
INFLIGHT_GRACE=1500
# A job consumer writes nothing between "Dispatching job" and the end of the job,
# by design: a GOA release load ran 105 to 109 minutes silent on this node on
# 2026-10-08. So for a job the measure is the age of the job, not the silence of
# the log, and the bound is three times the longest job measured here.
INFLIGHT_JOB_STALL=21600
# How long a started worker has to write its own "Worker started" line.
# MEASURED on the compute node, 2026-11-04, from the wrapper's "starting" line
# to the worker's start line: at most 4.9 s over 52 starts of the card's worker,
# 2.9 s over 9 of predictions.batch, 2.4 s over 3 of training. The taxonomy
# warm-up that precedes the line on predictions.batch, jobs and training took
# under a millisecond, because the server's taxa dump is already local. The
# bound covers what the measurement did not see: the wrapper's clock gate, up to
# 120 s at boot, and a node without the dump, where the warm-up downloads about
# 100 MB before the line is written.
START_LINE_WAIT=240

say() { echo "$(date -Is) node-sync: $*"; }
refuse() { say "REFUSED, $*"; exit 0; }
# Past the drift check a dry run reports and touches nothing, the state file
# included: the state is this node's verdict, and a rehearsal is not one.
put_state() { [[ "${DRYRUN}" == "1" ]] || echo "$*" > "${STATE}"; }

queue_of() { local q="${1#protea-lab-worker@}"; echo "${q%.service}"; }

# --- which workers run from the slot, and in which environments --------------
# Two sources of instance names, because either alone misses workers.
# `list-units --all` names every instance the user manager has loaded, running
# or not, but after a reboot with the workers disabled it names none of them,
# and the environment of a worker that is started by hand an hour later would
# then never have been followed. The drop-in directories name every instance
# this node has configured, loaded or not; `systemctl show` loads a unit on
# demand to answer. The working directory is compared after resolving both
# sides, so a trailing slash or a symlink cannot hide a worker.
SLOT_REAL="$(realpath -m "${SLOT}")"
UNIT_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
SLOT_UNITS=()
while read -r u; do
  [[ "${u}" == protea-lab-worker@?*.service ]] || continue
  wd="$(systemctl --user show -p WorkingDirectory --value "${u}" 2>/dev/null || true)"
  [[ -n "${wd}" && "$(realpath -m "${wd}")" == "${SLOT_REAL}" ]] && SLOT_UNITS+=("${u}")
done < <(
  {
    systemctl --user list-units --all --plain --no-legend 'protea-lab-worker@*.service' 2>/dev/null \
      | awk '{print $1}' || true
    for d in "${UNIT_DIR}"/protea-lab-worker@?*.service.d; do
      [[ -d "${d}" ]] && basename "${d}" .d
    done
  } | sort -u
)
# The configured unit is always one of them, loaded or not, so a node whose
# only worker is stopped still has its environment followed.
[[ " ${SLOT_UNITS[*]} " == *" ${UNIT} "* ]] || SLOT_UNITS+=("${UNIT}")

# "activating" is a unit inside its RestartSec, which would start on its own
# in the middle of a sync if it were not stopped with the others.
ACTIVE_UNITS=()
for u in "${SLOT_UNITS[@]}"; do
  case "$(systemctl --user is-active "${u}" 2>/dev/null || true)" in
    active|activating|reloading) ACTIVE_UNITS+=("${u}") ;;
  esac
done

# One VIRTUAL_ENV per unit, read from the unit's own environment, which is what
# the wrapper hands poetry. A path with a space in it would be split here; none
# of this node's environments has one.
unit_venv() {
  local v
  v="$(systemctl --user show -p Environment --value "$1" 2>/dev/null \
        | tr ' ' '\n' | sed -n 's/^VIRTUAL_ENV=//p' | tail -1)"
  echo "${v:-${VENV}}"
}
declare -A VENV_USERS=()
for u in "${SLOT_UNITS[@]}"; do
  v="$(unit_venv "${u}")"
  VENV_USERS["${v}"]+="$(queue_of "${u}") "
done
VENVS=("${!VENV_USERS[@]}")

# --- read the declaration, without touching any working tree ----------------
# `git show origin/main:<path>` reads the committed file directly. A checkout
# or a pull here would move a tree somebody else may be using.
DECL=""
if [[ -n "${DECL_FILE}" ]]; then
  DECL="$(cat "${DECL_FILE}")" || refuse "cannot read the rehearsal declaration ${DECL_FILE}"
  say "REHEARSAL: reading ${DECL_FILE} instead of origin/main, so nothing will be changed"
else
  git -C "${FARM}" fetch --quiet origin || refuse "cannot reach agent-farm origin; leaving the node as it is"
  if ! DECL="$(git -C "${FARM}" show "origin/main:${DECL_PATH}" 2>/dev/null)"; then
    say "no ${DECL_PATH} on agent-farm origin/main yet; nothing declared, nothing to follow"
    # State is written on every path, including this one. A state file left over
    # from an earlier run reads as a current verdict, which is the same defect as
    # a status that means "was true once".
    echo "undeclared $(git -C "${SLOT}" rev-parse HEAD)" > "${STATE}"
    exit 0
  fi
fi

WANT_COORD="$(printf '%s\n' "${DECL}" | awk '$1=="coordinator"{print $2; exit}')"
if [[ ! "${WANT_COORD}" =~ ^[0-9a-f]{40}$ ]]; then
  refuse "the declaration does not carry a 40 character coordinator sha"
fi

# --- is the declared commit real, and is it on the trunk? -------------------
# A sha that is not an ancestor of develop is either a typo or a branch nobody
# promoted, and following one is how a node ends up running code that no
# review saw.
git -C "${SLOT}" fetch --quiet origin || refuse "cannot reach PROTEA origin"
git -C "${SLOT}" cat-file -e "${WANT_COORD}^{commit}" 2>/dev/null \
  || refuse "declared coordinator ${WANT_COORD:0:12} does not exist in this clone"
git -C "${SLOT}" merge-base --is-ancestor "${WANT_COORD}" origin/develop \
  || refuse "declared coordinator ${WANT_COORD:0:12} is not an ancestor of origin/develop"

HAVE_COORD="$(git -C "${SLOT}" rev-parse HEAD)"

# --- what that commit's lockfile says every sibling must be -----------------
LOCKED="$("${PY}" - "${SLOT}" "${WANT_COORD}" <<'PYEOF'
import subprocess, sys, tomllib
slot, sha = sys.argv[1], sys.argv[2]
raw = subprocess.run(["git","-C",slot,"show",f"{sha}:poetry.lock"],
                     capture_output=True, check=True).stdout
for pkg in tomllib.loads(raw.decode())["package"]:
    src = pkg.get("source") or {}
    if src.get("type") == "git":
        print(pkg["name"], src.get("resolved_reference") or src.get("reference"), src["url"])
PYEOF
)" || refuse "cannot read the lockfile at ${WANT_COORD:0:12}"

# A dependency line in the declaration overrides the lockfile for that package.
LOCKED="$(printf '%s\n' "${LOCKED}" | while read -r name sha url; do
  ov="$(printf '%s\n' "${DECL}" | awk -v n="${name}" '$1==n{print $2; exit}')"
  if [[ "${ov}" =~ ^[0-9a-f]{40}$ ]]; then echo "${name} ${ov} ${url}"; else echo "${name} ${sha} ${url}"; fi
done)"

# --- what is actually installed, in each environment -------------------------
installed_sha() {
  "$1/bin/python" - "$2" <<'PYEOF'
import json, sys, pathlib, importlib.metadata as md
try:
    d = md.distribution(sys.argv[1])
    j = json.loads((pathlib.Path(str(d._path)) / "direct_url.json").read_text())
    print(j["vcs_info"]["commit_id"])
except Exception:
    print("")
PYEOF
}

for v in "${VENVS[@]}"; do
  [[ -x "${v}/bin/python" ]] || refuse "the environment ${v} of ${VENV_USERS[${v}]}has no interpreter"
done

DRIFT=()
[[ "${HAVE_COORD}" == "${WANT_COORD}" ]] || DRIFT+=("coordinator ${HAVE_COORD:0:12}->${WANT_COORD:0:12}")
for v in "${VENVS[@]}"; do
  while read -r name want url; do
    [[ -n "${name}" ]] || continue
    got="$(installed_sha "${v}" "${name}")"
    [[ "${got}" == "${want}" ]] || DRIFT+=("$(basename "${v}"):${name} ${got:0:12}->${want:0:12}")
  done <<< "${LOCKED}"
done

if (( ${#DRIFT[@]} == 0 )); then
  [[ -n "${DECL_FILE}" ]] || echo "in-sync ${WANT_COORD}" > "${STATE}"
  [[ -z "${DECL_FILE}" ]] || say "REHEARSAL: the node already matches ${WANT_COORD:0:12}"
  exit 0
fi

say "drift: ${DRIFT[*]}"

# --- refuse rather than guess ------------------------------------------------
if [[ -n "$(git -C "${SLOT}" status --porcelain)" ]]; then
  put_state "blocked dirty-slot ${WANT_COORD}"
  refuse "the deploy slot has uncommitted changes; a sync would destroy them"
fi

# Every environment needs a way to install before anything is stopped. The 3.12
# environment was made with uv and has no pip of its own.
installer_of() {
  if [[ -x "$1/bin/pip" ]]; then echo pip
  elif [[ -x "${UV}" ]]; then echo uv
  else echo none
  fi
}
for v in "${VENVS[@]}"; do
  [[ "$(installer_of "${v}")" != none ]] \
    || refuse "the environment ${v} has no pip and there is no uv at ${UV}; it could not be synced"
done

# A revision can be correct code against a database that has not been migrated
# to it. The code sets the new columns on the ORM object and every insert fails,
# which is not a crash loop the node can diagnose and not something the sibling
# check can see: the schema lives on the other machine. So when the target adds
# or changes a migration, following it is a decision somebody has to make out
# loud, not a consequence of a poll.
#
# The check is entirely local, a diff of the migration directory between what we
# run and what is declared. It never opens the database, because reading the
# applied revision from the live server is exactly the access this node is not
# supposed to take.
MIG="$(git -C "${SLOT}" diff --name-only "${HAVE_COORD}" "${WANT_COORD}" -- 'alembic/versions/*' || true)"
if [[ -n "${MIG}" ]]; then
  ACK="$(printf '%s\n' "${DECL}" | awk '$1=="schema-applied"{print $2; exit}')"
  if [[ "${ACK}" != "${WANT_COORD}" ]]; then
    put_state "blocked unmigrated ${WANT_COORD}"
    say "the declared revision changes migrations: $(printf '%s' "${MIG}" | tr '\n' ' ')"
    refuse "no 'schema-applied ${WANT_COORD:0:12}' line in the declaration; the server must apply the migration and say so before this node follows"
  fi
  say "migrations change and the declaration says the schema is applied; proceeding"
fi

# --- is any worker running from the slot in the middle of something? ---------
# An unacknowledged batch is redelivered by the broker, so stopping mid-batch
# costs duplicated compute rather than work. A job costs more: a GOA release
# load runs for close to two hours, and until PROTEA#997 a job consumer acked
# its message on START, so a job stopped mid-run was not redelivered at all but
# left RUNNING for the reaper to find.
#
# The tree is shared, so a job in flight on ANY worker of the slot holds the
# whole sync: moving the tree under it is the defect this script exists for.
#
# Every worker of a queue appends to its own log. The unit named after the
# queue writes protea-lab-worker-<queue>.log, and each extra worker tied to it
# (protea-lab-worker-extra@.service, PartOf= that unit, so the stop below reaches
# it too) writes protea-lab-worker-<queue>@<n>.log. '@' cannot occur in a queue
# name, so the glob cannot pick up another queue's log, which a '.' suffix would:
# protea.embeddings.* matches protea.embeddings.batch.
#
# A log is in flight when its last dispatch line comes after its last end line.
# "Job acked." is in neither list, on purpose: before PROTEA#997 a job consumer
# acked on START and after it at the END, and a marker that changes side
# between two revisions of one consumer reads wrong under one of them. A worker
# restart ends whatever was running, so it counts as an end, and so does the
# operation watchdog's exit (PROTEA#1107), which ends the process.
#
# Until 2026-10-08 this check looked for "Dispatching operation" alone, which a
# job consumer never writes. Every job was invisible to it, and a declaration
# move would have stopped a release load wherever it happened to be.
DISPATCH_RE='Dispatching (operation|job)\.'
END_RE='(Operation acked\.|Operation failed\.|Operation requested retry|Job finished\.|Job failed\.|Job will retry|Job re-published\.|Worker started\.|Worker stopped\.|outlived the broker heartbeat window)'
now="$(date +%s)"
blocking=0
for u in "${ACTIVE_UNITS[@]}"; do
  q="$(queue_of "${u}")"
  for log in "${LOGDIR}/protea-lab-worker-${q}.log" "${LOGDIR}/protea-lab-worker-${q}@"*.log; do
    [[ -r "${log}" ]] || continue
    d="$(grep -anE "${DISPATCH_RE}" "${log}" | tail -1 | cut -d: -f1 || true)"
    [[ -n "${d}" ]] || continue
    e="$(grep -anE "${END_RE}" "${log}" | tail -1 | cut -d: -f1 || true)"
    (( d > ${e:-0} )) || continue
    line="$(sed -n "${d}p" "${log}")"
    name="$(basename "${log}")"
    if [[ "${line}" == *"Dispatching job."* ]]; then
      # The job's age is read off its own dispatch line, not off the log's mtime:
      # any line written mid-job would move the mtime and make an old job look
      # young, and since PROTEA#997 the I/O thread keeps running during a job.
      ts="$(printf '%s\n' "${line}" | sed -n 's/.*"timestamp": *"\([^"]*\)".*/\1/p')"
      since="$(date -d "${ts}" +%s 2>/dev/null || stat -c %Y "${log}")"
      job="$(printf '%s\n' "${line}" | sed -n 's/.*job_id=\([0-9a-f-]*\).*/\1/p')"
      age=$(( now - since ))
      if (( age < INFLIGHT_JOB_STALL )); then
        say "job ${job:-?} has been in flight on ${name} for ${age}s; deferring to the next tick"
        blocking=$(( blocking + 1 ))
      else
        say "job ${job:-?} has been in flight on ${name} for ${age}s, past ${INFLIGHT_JOB_STALL}s; that is a stall, not counting it"
      fi
    else
      age=$(( now - $(stat -c %Y "${log}") ))
      if (( age < INFLIGHT_GRACE )); then
        say "a batch is in flight on ${name} and the log moved ${age}s ago; deferring to the next tick"
        blocking=$(( blocking + 1 ))
      else
        say "a batch has been in flight on ${name} with the log silent for ${age}s; that is a stall, not counting it"
      fi
    fi
  done
done
if (( blocking > 0 )); then
  put_state "deferred in-flight ${WANT_COORD}"
  exit 0
fi

# A dry run stops here, after every check, so that what it reports is what a
# real tick would do: refuse, defer, or act. It exists so the acting path can
# be rehearsed on a live node without acting on it.
if [[ "${DRYRUN}" == "1" ]]; then
  say "DRY RUN, would stop ${ACTIVE_UNITS[*]:-no running worker}, check out ${WANT_COORD:0:12}, sync $(for v in "${VENVS[@]}"; do printf '%s (%s, for %s) ' "${v}" "$(installer_of "${v}")" "${VENV_USERS[${v}]% }"; done)and start the same units again"
  stopped="$(printf '%s\n' "${SLOT_UNITS[@]}" | grep -vxF -f <(printf '%s\n' "${ACTIVE_UNITS[@]}") || true)"
  [[ -z "${stopped}" ]] || say "DRY RUN, would leave stopped: $(echo ${stopped})"
  exit 0
fi

# What each environment's torch is before anything moves. --no-deps should leave
# it alone; the check after the installs proves it did.
torch_identity() {
  "$1/bin/python" -c 'import torch; print(torch.__version__, torch.version.cuda)' 2>/dev/null || echo "no torch"
}
declare -A TORCH_BEFORE=()
for v in "${VENVS[@]}"; do TORCH_BEFORE["${v}"]="$(torch_identity "${v}")"; done

# --- act ---------------------------------------------------------------------
# Stopping a unit also stops every unit that is PartOf it, and starting it
# brings back every unit whose [Install] says WantedBy= it, so extra workers of
# a queue move with it and none is left on the old revision.
restart_old() { (( ${#ACTIVE_UNITS[@]} == 0 )) || systemctl --user start "${ACTIVE_UNITS[@]}" || true; }
if (( ${#ACTIVE_UNITS[@]} > 0 )); then
  say "stopping ${ACTIVE_UNITS[*]}"
  systemctl --user stop "${ACTIVE_UNITS[@]}" \
    || { restart_old; refuse "could not stop every worker of the slot; not touching the tree under a running process"; }
fi

git -C "${SLOT}" checkout --quiet --detach "${WANT_COORD}" \
  || { echo "failed checkout ${WANT_COORD}" > "${STATE}"; restart_old; refuse "checkout failed; workers restarted on the old revision"; }
say "slot now at $(git -C "${SLOT}" rev-parse --short HEAD)"

for v in "${VENVS[@]}"; do
  how="$(installer_of "${v}")"
  while read -r name want url; do
    [[ -n "${name}" ]] || continue
    got="$(installed_sha "${v}" "${name}")"
    [[ "${got}" == "${want}" ]] && continue
    say "installing ${name}@${want:0:12} into ${v} with ${how}"
    # --no-deps is the whole point: it installs this package and re-resolves
    # nothing, so it cannot swap the CUDA build of torch for a CPU one, which a
    # plain install here has done before. And it reinstalls by force, because a
    # git ref at the same version string is otherwise skipped in silence.
    if [[ "${how}" == pip ]]; then
      "${v}/bin/pip" install --quiet --no-deps --force-reinstall "${name} @ git+${url}@${want}"
    else
      "${UV}" pip install --quiet --python "${v}/bin/python" --no-deps \
        --reinstall-package "${name}" "${name} @ git+${url}@${want}"
    fi || { echo "failed install ${name} ${want}" > "${STATE}"; refuse "installing ${name} into ${v} failed; workers left DOWN rather than running a half synced node"; }
  done <<< "${LOCKED}"
done

# --- prove it before letting the workers consume ------------------------------
BAD=0
for v in "${VENVS[@]}"; do
  while read -r name want url; do
    [[ -n "${name}" ]] || continue
    got="$(installed_sha "${v}" "${name}")"
    [[ "${got}" == "${want}" ]] || { say "STILL WRONG after install in ${v}: ${name} ${got:0:12} != ${want:0:12}"; BAD=1; }
  done <<< "${LOCKED}"
  after="$(torch_identity "${v}")"
  [[ "${after}" == "${TORCH_BEFORE[${v}]}" ]] \
    || { say "torch changed in ${v}: ${TORCH_BEFORE[${v}]} became ${after}"; BAD=1; }
  ( cd "${SLOT}" && PYTHONPATH=. "${v}/bin/python" -c "import protea.core.operations.predict_go_terms" ) \
    || { say "the operation does not import at this revision in ${v}"; BAD=1; }
done
# The environment of the configured queue is the card's, and it must keep it.
"${PY}" -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" \
  || { say "torch lost CUDA in ${VENV}"; BAD=1; }

if (( BAD )); then
  echo "failed verification ${WANT_COORD}" > "${STATE}"
  refuse "verification failed after sync; workers stay DOWN, a silent wrong consumer is worse than no consumer"
fi

if (( ${#ACTIVE_UNITS[@]} == 0 )); then
  echo "synced ${WANT_COORD} no-running-workers" > "${STATE}"
  say "synced to ${WANT_COORD:0:12}; no worker of the slot was running, so none was started"
  exit 0
fi

# --- and prove each worker came back on it -------------------------------------
# A unit that starts is not a worker on the new revision. Each one stamps the
# revision it imported on its own "Worker started" line, and that line is the
# only witness that this process holds this code: the journal says the unit
# started, not what it loaded. Read past where each log ended before the start.
declare -A LOG_AT=()
for u in "${ACTIVE_UNITS[@]}"; do
  f="${LOGDIR}/protea-lab-worker-$(queue_of "${u}").log"
  LOG_AT["${u}"]="$(stat -c %s "${f}" 2>/dev/null || echo 0)"
done
systemctl --user start "${ACTIVE_UNITS[@]}" \
  || { echo "failed start ${WANT_COORD}" > "${STATE}"; refuse "the workers would not start"; }

WRONG=()
pending=("${ACTIVE_UNITS[@]}")
deadline=$(( $(date +%s) + START_LINE_WAIT ))
while (( ${#pending[@]} > 0 )) && (( $(date +%s) < deadline )); do
  sleep 5
  still=()
  for u in "${pending[@]}"; do
    f="${LOGDIR}/protea-lab-worker-$(queue_of "${u}").log"
    # Read into a plain variable first: a unit name used as a key inside $(( ))
    # would be read as arithmetic. A log that is now SHORTER than it was before
    # the start was rotated in between, and its new start line is somewhere in
    # the new file, so it is read from the beginning instead of from past its end.
    from="${LOG_AT[${u}]}"
    (( $(stat -c %s "${f}" 2>/dev/null || echo 0) >= from )) || from=0
    line="$(tail -c +"$(( from + 1 ))" "${f}" 2>/dev/null \
            | grep -ao 'Worker started\. queue=[^ "]* revision=[^"]*' | tail -1 || true)"
    if [[ -z "${line}" ]]; then still+=("${u}"); continue; fi
    rev="${line##* revision=}"
    if [[ "${rev}" == "${WANT_COORD}" ]]; then
      say "$(queue_of "${u}") is back on ${WANT_COORD:0:12}"
    else
      say "$(queue_of "${u}") came back on ${rev}, not ${WANT_COORD:0:12}; stopping it"
      systemctl --user stop "${u}" || true
      WRONG+=("$(queue_of "${u}")")
    fi
  done
  pending=("${still[@]}")
done
for u in "${pending[@]}"; do WRONG+=("$(queue_of "${u}"):no-start-line"); done

if (( ${#WRONG[@]} > 0 )); then
  echo "failed start-revision ${WANT_COORD} ${WRONG[*]}" > "${STATE}"
  say "synced the slot to ${WANT_COORD:0:12}, but not every worker proved it: ${WRONG[*]}"
  exit 0
fi
echo "synced ${WANT_COORD}" > "${STATE}"
say "synced to ${WANT_COORD:0:12}; every worker of the slot is back on it: $(for u in "${ACTIVE_UNITS[@]}"; do printf '%s ' "$(queue_of "${u}")"; done)"
