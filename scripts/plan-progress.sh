#!/usr/bin/env bash
# plan-progress.sh — show §24 master plan progress, joining sqlite executor
# task history with the slice list parsed from
# ~/.claude/projects/-home-frapercan-Thesis/memory/project_protea_master_plan.md
#
# Usage:
#   bash plan-progress.sh                  # full table, all 8 phases
#   bash plan-progress.sh --phase 1        # one phase only
#   bash plan-progress.sh --next           # just the next unblocked slice
#   bash plan-progress.sh --json           # machine-readable for shepherd

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
PLAN="${PROTEA_MASTER_PLAN:-$HOME/.claude/projects/-home-frapercan-Thesis/memory/project_protea_master_plan.md}"
DB="$ROOT/state/tasks.sqlite"

[[ -f "$PLAN" ]] || { echo "ERROR: master plan not found at $PLAN" >&2; exit 2; }
[[ -f "$DB"   ]] || { echo "ERROR: sqlite not found at $DB. Run init.sh." >&2; exit 2; }

exec python3 "$ROOT/scripts/lib/plan_parser.py" --plan "$PLAN" --db "$DB" "$@"
