#!/usr/bin/env bash
# common.sh — shared helpers for agent-farm scripts. Source from each script.
# DO NOT execute directly.

# Set strict mode in callers, not here (so we don't break interactive sourcing).

AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# AGENT_FARM_DB defaults to the canonical location but tests / fixture runs
# can override it (set AGENT_FARM_DB before sourcing this file).
AGENT_FARM_DB="${AGENT_FARM_DB:-$AGENT_FARM_ROOT/state/tasks.sqlite}"
AGENT_FARM_TMUX_SESSION="${AGENT_FARM_TMUX_SESSION:-agent-farm}"
AGENT_FARM_WORKTREES="${AGENT_FARM_WORKTREES:-$HOME/Thesis2/worktrees}"

# Logging
ts() { date -Iseconds; }
log() { printf '[%s] %s\n' "$(ts)" "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# YAML reader: minimal, requires python3 + pyyaml.
# Usage: yaml_get <file> <dotted.path>
yaml_get() {
  local file="$1" path="$2"
  python3 -c "
import sys, yaml
with open('$file') as f:
    d = yaml.safe_load(f) or {}
for p in '$path'.split('.'):
    if isinstance(d, dict):
        d = d.get(p)
    elif isinstance(d, list) and p.isdigit():
        d = d[int(p)] if int(p) < len(d) else None
    else:
        d = None
    if d is None:
        sys.exit(0)
if isinstance(d, (dict, list)):
    import json; print(json.dumps(d))
else:
    print(d)
"
}

# task_id format: <agent>-<unix>-<rand4>
make_task_id() {
  local agent="$1"
  local rand
  rand=$(printf '%04x' $((RANDOM % 65536)))
  printf '%s-%d-%s' "$agent" "$(date +%s)" "$rand"
}

# DB helpers — delegate to lib/db.py for proper escaping.
DB_PY="$AGENT_FARM_ROOT/scripts/lib/db.py"
db_query() { python3 "$DB_PY" query "$1"; }
db_exec()  { python3 "$DB_PY" exec  "$1"; }

task_insert() {
  local id="$1" agent="$2" kind="$3" persistent="$4" model="${5:-}" args="${6:-{}}"
  python3 "$DB_PY" insert-task "$id" "$agent" "$kind" "$persistent" "$model" "$args"
}

task_set_status() {
  python3 "$DB_PY" set-status "$1" "$2"
}

task_set_started() {
  python3 "$DB_PY" set-started "$1" "${2:-}" "${3:-}" "${4:-}"
}

task_set_ended() {
  # task_set_ended <id> <status> [exit_code] [summary]
  # The optional summary argument (FARM-2.1) is forwarded to db.py so the
  # corresponding events row carries the first 200 chars in payload_json.
  python3 "$DB_PY" set-ended "$1" "$2" "${3:-0}" "${4:-}"
}

task_mark_killed() {
  # task_mark_killed <id> [reason] — emits a kind=kill events row.
  python3 "$DB_PY" mark-killed "$1" "${2:-}"
}

task_mark_crashed() {
  # task_mark_crashed <id> [reason] — emits a kind=cleanup events row.
  python3 "$DB_PY" mark-crashed "$1" "${2:-}"
}

heartbeat() {
  python3 "$DB_PY" heartbeat "$1" "${2:-info}" "${3:-}"
}

# Find agent yaml or die.
agent_file() {
  local name="$1"
  local f="$AGENT_FARM_ROOT/agents/${name}.yaml"
  [[ -f "$f" ]] || die "agent definition not found: $f"
  printf '%s' "$f"
}
