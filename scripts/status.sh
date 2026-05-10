#!/usr/bin/env bash
# status.sh — show live tasks (tabular) or detail of one task.
#
# Usage:
#   bash status.sh                # tabla de live tasks
#   bash status.sh <task_id>      # detail + last 10 heartbeats
#   bash status.sh --all          # include completed/failed/killed (last 24h)

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

ARG="${1:-}"

if [[ -z "$ARG" ]]; then
  echo "Live tasks:"
  printf '%-30s %-20s %-10s %-10s %-12s %s\n' \
    "task_id" "agent" "kind" "status" "model" "started_at"
  echo "--------------------------------------------------------------------------------"
  db_query "SELECT id, agent_name, kind, status, COALESCE(model,''),
                   COALESCE(started_at, created_at)
            FROM tasks
            WHERE status IN ('pending','running')
            ORDER BY created_at DESC;" \
  | while IFS=$'\t' read -r id agent kind status model start; do
      printf '%-30s %-20s %-10s %-10s %-12s %s\n' \
        "$id" "$agent" "$kind" "$status" "$model" "$start"
    done
elif [[ "$ARG" == "--all" ]]; then
  echo "All tasks (last 24h):"
  printf '%-30s %-20s %-10s %-10s %-12s %s\n' \
    "task_id" "agent" "kind" "status" "model" "ended_at"
  echo "--------------------------------------------------------------------------------"
  db_query "SELECT id, agent_name, kind, status, COALESCE(model,''),
                   COALESCE(ended_at, started_at, created_at)
            FROM tasks
            WHERE created_at > datetime('now', '-1 day')
            ORDER BY created_at DESC;" \
  | while IFS=$'\t' read -r id agent kind status model ts; do
      printf '%-30s %-20s %-10s %-10s %-12s %s\n' \
        "$id" "$agent" "$kind" "$status" "$model" "$ts"
    done
else
  TASK_ID="$ARG"
  echo "=== Task $TASK_ID ==="
  db_query "SELECT 'agent     ', agent_name FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'kind      ', kind FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'persistent', CAST(persistent AS TEXT) FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'status    ', status FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'model     ', COALESCE(model,'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'worktree  ', COALESCE(worktree,'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'tmux      ', COALESCE(tmux_window,'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'pid       ', COALESCE(CAST(pid AS TEXT),'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'created   ', created_at FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'started   ', COALESCE(started_at,'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'ended     ', COALESCE(ended_at,'') FROM tasks WHERE id='$TASK_ID'
            UNION ALL SELECT 'exit_code ', COALESCE(CAST(exit_code AS TEXT),'') FROM tasks WHERE id='$TASK_ID';"
  echo
  echo "--- Last 10 heartbeats ---"
  db_query "SELECT ts, level, message FROM heartbeats
            WHERE task_id='$TASK_ID' ORDER BY ts DESC LIMIT 10;"
  echo
  echo "--- Result (if any) ---"
  db_query "SELECT 'summary', COALESCE(summary,'') FROM results WHERE task_id='$TASK_ID'
            UNION ALL SELECT 'sha_before', COALESCE(sha_before,'') FROM results WHERE task_id='$TASK_ID'
            UNION ALL SELECT 'sha_after',  COALESCE(sha_after,'')  FROM results WHERE task_id='$TASK_ID';"
fi
