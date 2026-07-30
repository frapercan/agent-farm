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

REPO="${PROTEA_REPO:-${HOME}/Thesis2/repositories/PROTEA}"
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
exec "${POETRY}" run python scripts/worker.py --queue "${QUEUE}" --log-format text
