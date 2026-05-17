#!/usr/bin/env bash
# plan-progress.sh — show plan progress, joining sqlite executor task
# history with the slices declared in the internal plan store under
# `plans/<loop>/PLAN.md`.
#
# Usage:
#   bash plan-progress.sh                    # full table, all loops
#   bash plan-progress.sh --phase F-FARM-1   # one phase only
#   bash plan-progress.sh --next             # just the next pickable slice
#   bash plan-progress.sh --json             # machine-readable for shepherd

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
PLANS_ROOT="${PROTEA_PLANS_ROOT:-$ROOT/plans}"
DB="$ROOT/state/tasks.sqlite"

[[ -d "$PLANS_ROOT" ]] || { echo "ERROR: plans root not found at $PLANS_ROOT" >&2; exit 2; }
[[ -f "$DB"         ]] || { echo "ERROR: sqlite not found at $DB. Run init.sh." >&2; exit 2; }

exec python3 "$ROOT/scripts/lib/plan_parser.py" --plans-root "$PLANS_ROOT" --db "$DB" "$@"
