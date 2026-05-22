#!/usr/bin/env bash
# queue-watcher-supervisor.sh (EXAMPLE, not productionised) -- shows the
# minimal wrapper needed to stand up a new persistent service on top of
# scripts/services/_supervisor-template.sh.
#
# Compare with scripts/services/deploy-keeper-supervisor.sh: deploy-keeper
# adds a whole trigger subsystem (service_nap_between_ticks override) and
# a custom janitor escalation. This example uses the template defaults
# for both, so the wrapper is just: read poll_interval, set the five
# template parameters, source the template.
#
# Reads:
#   TASK_ID            task UUID (set by spawn.sh)
#   AGENT_FARM_ROOT    default ~/Thesis2/agent-farm

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
# shellcheck source=../../scripts/lib/common.sh
source "$ROOT/scripts/lib/common.sh"
# shellcheck source=../../scripts/lib/yaml_parse.sh
source "$ROOT/scripts/lib/yaml_parse.sh"

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YAML="${QUEUE_WATCHER_YAML:-$SELF_DIR/queue-watcher.yaml}"

# Read poll_interval (default 120s) and the ladder length (default 3)
# from the example yaml. parse_yaml_duration accepts 30s / 2m / 1h.
POLL_INTERVAL_SEC=$(parse_yaml_duration "$YAML" service.poll_interval 120)
MAX_FAILS=$(parse_yaml_duration "$YAML" service.max_consecutive_failures 3)

# Template parameters (see scripts/services/_supervisor-template.sh).
# shellcheck disable=SC2034
{
TICK_SCRIPT="$SELF_DIR/queue-watcher-tick.sh"
TICK_CMD_OVERRIDE="${QUEUE_WATCHER_TICK_CMD:-}"
POLL_INTERVAL="$POLL_INTERVAL_SEC"
MAX_CONSECUTIVE_FAILURES="$MAX_FAILS"
PAUSE_AFTER_PAUSE_SEC="${QUEUE_WATCHER_PAUSE_SEC:-900}"  # 15 min cool-off
FAIL_KIND_ENV_FILE="${QUEUE_WATCHER_FAIL_ENV:-/tmp/queue-watcher-last-fail.env}"
}

# No service_escalate / service_nap_between_ticks overrides: the example
# uses the template defaults (generic janitor spawn + plain nap).

# shellcheck source=../../scripts/services/_supervisor-template.sh
source "$ROOT/scripts/services/_supervisor-template.sh"
