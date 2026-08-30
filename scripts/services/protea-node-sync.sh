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
STATE="${HOME}/Thesis2/storage/logs/node-sync.state"
PY="${VENV}/bin/python"

# A batch that has been running for less than this is worth waiting a tick for
# rather than interrupting. Longer than this and it is not progress, it is a
# stall, and the sync goes ahead.
INFLIGHT_GRACE=1500

say() { echo "$(date -Is) node-sync: $*"; }
refuse() { say "REFUSED, $*"; exit 0; }

# --- read the declaration, without touching any working tree ----------------
# `git show origin/main:<path>` reads the committed file directly. A checkout
# or a pull here would move a tree somebody else may be using.
git -C "${FARM}" fetch --quiet origin || refuse "cannot reach agent-farm origin; leaving the node as it is"

DECL=""
if ! DECL="$(git -C "${FARM}" show "origin/main:${DECL_PATH}" 2>/dev/null)"; then
  say "no ${DECL_PATH} on agent-farm origin/main yet; nothing declared, nothing to follow"
  # State is written on every path, including this one. A state file left over
  # from an earlier run reads as a current verdict, which is the same defect as
  # a status that means "was true once".
  echo "undeclared $(git -C "${SLOT}" rev-parse HEAD)" > "${STATE}"
  exit 0
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

# --- what is actually installed ---------------------------------------------
installed_sha() {
  "${PY}" - "$1" <<'PYEOF'
import json, sys, pathlib, importlib.metadata as md
try:
    d = md.distribution(sys.argv[1])
    j = json.loads((pathlib.Path(str(d._path)) / "direct_url.json").read_text())
    print(j["vcs_info"]["commit_id"])
except Exception:
    print("")
PYEOF
}

DRIFT=()
[[ "${HAVE_COORD}" == "${WANT_COORD}" ]] || DRIFT+=("coordinator ${HAVE_COORD:0:12}->${WANT_COORD:0:12}")
while read -r name want url; do
  [[ -n "${name}" ]] || continue
  got="$(installed_sha "${name}")"
  [[ "${got}" == "${want}" ]] || DRIFT+=("${name} ${got:0:12}->${want:0:12}")
done <<< "${LOCKED}"

if (( ${#DRIFT[@]} == 0 )); then
  echo "in-sync ${WANT_COORD}" > "${STATE}"
  exit 0
fi

say "drift: ${DRIFT[*]}"

# A dry run says what it would do and touches nothing. It exists so the acting
# path can be exercised on a live node without acting on it.
if [[ "${PROTEA_SYNC_DRYRUN:-0}" == "1" ]]; then
  say "DRY RUN, would stop ${UNIT}, check out ${WANT_COORD:0:12} and install the siblings above"
  exit 0
fi

# --- refuse rather than guess ------------------------------------------------
if [[ -n "$(git -C "${SLOT}" status --porcelain)" ]]; then
  echo "blocked dirty-slot ${WANT_COORD}" > "${STATE}"
  refuse "the deploy slot has uncommitted changes; a sync would destroy them"
fi

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
    echo "blocked unmigrated ${WANT_COORD}" > "${STATE}"
    say "the declared revision changes migrations: $(printf '%s' "${MIG}" | tr '\n' ' ')"
    refuse "no 'schema-applied ${WANT_COORD:0:12}' line in the declaration; the server must apply the migration and say so before this node follows"
  fi
  say "migrations change and the declaration says the schema is applied; proceeding"
fi

# An unacknowledged batch is redelivered by the broker, so stopping mid-batch
# costs duplicated compute rather than work. It is still worth one tick to
# avoid, but not worth blocking on forever: past the grace it is a stall.
LOG="${HOME}/Thesis2/storage/logs/protea-lab-worker-${QUEUE}.log"
if [[ -r "${LOG}" ]]; then
  last_disp="$(grep -a 'Dispatching operation' "${LOG}" | tail -1 || true)"
  last_ack="$(grep -a 'Operation acked' "${LOG}" | tail -1 || true)"
  if [[ -n "${last_disp}" && -z "${last_ack}" ]] || \
     [[ -n "${last_disp}" && "$(grep -an 'Dispatching operation' "${LOG}" | tail -1 | cut -d: -f1)" -gt "$(grep -an 'Operation acked' "${LOG}" | tail -1 | cut -d: -f1 || echo 0)" ]]; then
    age=$(( $(date +%s) - $(stat -c %Y "${LOG}") ))
    if (( age < INFLIGHT_GRACE )); then
      echo "deferred in-flight ${WANT_COORD}" > "${STATE}"
      say "a batch is in flight and the log moved ${age}s ago; deferring to the next tick"
      exit 0
    fi
    say "a batch has been in flight with a log silent for ${age}s; that is a stall, syncing anyway"
  fi
fi

# --- act ---------------------------------------------------------------------
say "stopping ${UNIT}"
systemctl --user stop "${UNIT}" || refuse "could not stop the worker; not touching the tree under a running process"

git -C "${SLOT}" checkout --quiet --detach "${WANT_COORD}" \
  || { echo "failed checkout ${WANT_COORD}" > "${STATE}"; systemctl --user start "${UNIT}" || true; refuse "checkout failed; worker restarted on the old revision"; }
say "slot now at $(git -C "${SLOT}" rev-parse --short HEAD)"

while read -r name want url; do
  [[ -n "${name}" ]] || continue
  got="$(installed_sha "${name}")"
  [[ "${got}" == "${want}" ]] && continue
  say "installing ${name}@${want:0:12}"
  # --no-deps is the whole point: it installs this package and re-resolves
  # nothing, so it cannot swap the CUDA build of torch for a CPU one, which a
  # plain install here has done before.
  "${VENV}/bin/pip" install --quiet --no-deps --force-reinstall "${name} @ git+${url}@${want}" \
    || { echo "failed pip ${name} ${want}" > "${STATE}"; refuse "installing ${name} failed; worker left DOWN rather than running a half synced node"; }
done <<< "${LOCKED}"

# --- prove it before letting the worker consume ------------------------------
BAD=0
while read -r name want url; do
  [[ -n "${name}" ]] || continue
  got="$(installed_sha "${name}")"
  [[ "${got}" == "${want}" ]] || { say "STILL WRONG after install: ${name} ${got:0:12} != ${want:0:12}"; BAD=1; }
done <<< "${LOCKED}"
"${PY}" -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" \
  || { say "torch lost CUDA in this sync"; BAD=1; }
( cd "${SLOT}" && PYTHONPATH=. "${PY}" -c "import protea.core.operations.predict_go_terms" ) \
  || { say "the operation does not import at this revision"; BAD=1; }

if (( BAD )); then
  echo "failed verification ${WANT_COORD}" > "${STATE}"
  refuse "verification failed after sync; worker stays DOWN, a silent wrong consumer is worse than no consumer"
fi

systemctl --user start "${UNIT}" || { echo "failed start ${WANT_COORD}" > "${STATE}"; refuse "worker would not start"; }
echo "synced ${WANT_COORD}" > "${STATE}"
say "synced to ${WANT_COORD:0:12} and the worker is back on ${QUEUE}"
