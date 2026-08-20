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

echo "protea-lab-worker: starting queue=${QUEUE} repo=${REPO} at $(date -Is)"
# JSON and not text. The platform's own default is json, and a text line is
# invisible to any log pipeline that filters on structure: a Loki rule written
# as `| json | level="error"` never matches one. The first version of this
# script passed --log-format text and would have made the compute node the one
# machine whose failures no dashboard could see.
exec "${POETRY}" run python scripts/worker.py --queue "${QUEUE}" --log-format json
