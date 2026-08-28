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
#   PROTEA_LAB_ENV   path to the node's environment file
#   PROTEA_REPO      path to the PROTEA checkout
#   POETRY_BIN       path to the poetry executable
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

# Prefer the deploy slot, and say so loudly when there is none.
#
# The default used to be the developer's checkout, which meant the workers ran
# whatever happened to be checked out there: their version was decided by someone
# editing rather than by a deploy, silently, and a worker could be twenty commits
# behind the branch that had just been merged. Nothing said so, because from the
# outside a worker serving old code and a worker serving new code look identical.
#
# The slot has to be created by hand and nothing creates it, so the fallback stays,
# but it now announces which of the two is in use.
REPO="${PROTEA_REPO:-}"
if [[ -z "${REPO}" ]]; then
  DEPLOY_SLOT="${HOME}/Thesis2/worktrees/protea-deploy"
  if [[ -d "${DEPLOY_SLOT}" ]]; then
    REPO="${DEPLOY_SLOT}"
  else
    REPO="${HOME}/Thesis2/repositories/PROTEA"
    echo "protea-lab-worker: no deploy slot at ${DEPLOY_SLOT}, serving from the" \
         "developer checkout at ${REPO}. Its version is whatever is checked out" \
         "there, which is decided by editing rather than by deploying." >&2
  fi
fi
if [[ ! -d "${REPO}" ]]; then
  echo "protea-lab-worker: no PROTEA checkout at ${REPO}" >&2
  exit 78
fi
cd "${REPO}"

POETRY="${POETRY_BIN:-${HOME}/.local/bin/poetry}"
if [[ ! -x "${POETRY}" ]]; then
  echo "protea-lab-worker: poetry not executable at ${POETRY}" >&2
  exit 78
fi

# A slot is a location, not a guarantee, and this script stopped at the location.
# On 2026-08-27 a slot sat thirty-two commits and six days behind its branch while
# serving evaluations. It did not have the depth filter, so it accepted jobs that
# declared one, dropped the field without a word, scored the unrestricted frame
# and returned success. Sixteen of fifty-two cells came back carrying another
# arm's measurement under this arm's label, and nothing anywhere failed.
#
# So the slot has to be able to refuse. Behind its own tracking branch is a
# refusal by default, exit 78 like every other precondition here, because a
# worker that will silently produce mislabelled results is worse than one that
# will not start. PROTEA_ALLOW_STALE_SLOT=1 overrides it for the case where the
# node is deliberately pinned, and says so in the log rather than being quiet.
#
# Fetch is --dry-run: this script must not move the slot it is checking. Moving
# it would make the check pass by changing the thing under test, and a node that
# updates itself on start is a node whose version nobody chose.
if git -C "${REPO}" rev-parse --git-dir >/dev/null 2>&1; then
  UPSTREAM="$(git -C "${REPO}" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
  if [[ -n "${UPSTREAM}" ]]; then
    git -C "${REPO}" fetch --quiet --dry-run 2>/dev/null || true
    git -C "${REPO}" fetch --quiet origin 2>/dev/null || true
    BEHIND="$(git -C "${REPO}" rev-list --count "HEAD..${UPSTREAM}" 2>/dev/null || echo 0)"
    if [[ "${BEHIND}" -gt 0 ]]; then
      if [[ "${PROTEA_ALLOW_STALE_SLOT:-0}" == "1" ]]; then
        echo "protea-lab-worker: slot is ${BEHIND} commits behind ${UPSTREAM} and" \
             "PROTEA_ALLOW_STALE_SLOT=1, starting anyway. Results from this worker" \
             "carry the code at $(git -C "${REPO}" rev-parse --short HEAD), not the" \
             "branch tip." >&2
      else
        echo "protea-lab-worker: refusing to start. The slot at ${REPO} is" \
             "${BEHIND} commits behind ${UPSTREAM}. A worker behind its branch" \
             "accepts payload fields its code does not know and drops them without" \
             "failing, which is how sixteen results were mislabelled on" \
             "2026-08-27. Update the slot, or set PROTEA_ALLOW_STALE_SLOT=1 to" \
             "pin this node on purpose." >&2
        exit 78
      fi
    fi
  else
    echo "protea-lab-worker: ${REPO} tracks no upstream, so its freshness cannot" \
         "be checked. Serving it anyway; its version is whatever is checked out." >&2
  fi
fi

echo "protea-lab-worker: starting queue=${QUEUE} repo=${REPO} rev=$(git -C "${REPO}" rev-parse --short HEAD 2>/dev/null || echo unknown) at $(date -Is)"
# JSON and not text. The platform's own default is json, and a text line is
# invisible to any log pipeline that filters on structure: a Loki rule written
# as `| json | level="error"` never matches one. The first version of this
# script passed --log-format text and would have made the compute node the one
# machine whose failures no dashboard could see.
exec "${POETRY}" run python scripts/worker.py --queue "${QUEUE}" --log-format json
