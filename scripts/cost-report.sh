#!/usr/bin/env bash
# cost-report.sh — aggregate results.metrics_json into a per-day/agent/model
# cost table.
#
# Usage:
#   bash cost-report.sh                # last 7 days, human table
#   bash cost-report.sh --days 1
#   bash cost-report.sh --agent executor
#   bash cost-report.sh --model claude-opus-4-7
#   bash cost-report.sh --json         # machine-readable JSON array
#
# Filters can be combined. Output is sorted by USD descending (human view)
# or by (date, agent, model) ascending (JSON view).
#
# Data source: results.metrics_json populated by FARM-2.2's finalize-subagent.sh
# + spawn.sh hooks. Tasks without metrics_json are skipped (historical tasks
# remain null; future runs accumulate).

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

DAYS=7
AGENT_FILTER=""
MODEL_FILTER=""
EMIT_JSON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --days)  DAYS="${2:?--days needs a value}"; shift 2 ;;
    --agent) AGENT_FILTER="${2:?--agent needs a value}"; shift 2 ;;
    --model) MODEL_FILTER="${2:?--model needs a value}"; shift 2 ;;
    --json)  EMIT_JSON=1; shift ;;
    -h|--help)
      sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown arg: $1 (try --help)" ;;
  esac
done

# Delegate the actual aggregation to a Python helper so the JSON parsing
# stays sane; bash + jq alone would be fragile against missing fields.
exec python3 "$ROOT/scripts/lib/cost_report.py" \
  --days "$DAYS" \
  ${AGENT_FILTER:+--agent "$AGENT_FILTER"} \
  ${MODEL_FILTER:+--model "$MODEL_FILTER"} \
  $([[ "$EMIT_JSON" -eq 1 ]] && echo "--json")
