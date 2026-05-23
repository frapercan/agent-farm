#!/usr/bin/env bash
# stack_owner.sh -- advisory cooperative lock for the PROTEA dev stack.
#
# FARM-FEAT.12. The dev workspace stack (postgres + rabbit + uvicorn +
# workers + Next.js + ngrok) is a single shared resource between two
# independent agents:
#
#   1. deploy-keeper-supervisor.sh, which rebuilds + restarts the stack
#      whenever origin/develop moves (and on a 5min poll).
#   2. The conductor (or a human), which keeps the stack running by hand
#      while a long export pipeline (e.g. FARM-EXP.13 24-cell research-dataset
#      sweep) is in flight. Those exports take days and depend on env vars
#      that protea-deploy does NOT carry (anc2vec path, pair-feature pool
#      size, align-cache dir, ...). A blind restart by deploy-keeper kills
#      the in-flight export and silently corrupts the run.
#
# The 2026-05-20 incident (memory: feedback_deploykeeper_vs_export_stack_conflict)
# burned exactly this hole. This lock is the structural fix the user
# requested in project_deploy_keeper_coordination_directive.
#
# Shape: a single JSON file at agent-farm/state/stack-owner.json with
# four keys:
#   { "owner": "export"|"deploy"|"free",
#     "task_id": "<spawn task id or human label>",
#     "acquired_at": "<ISO8601 timestamp>",
#     "reason": "<short free-form reason>" }
#
# Concurrency: file-locked via flock(1) on a sibling .lock file. The
# lock is advisory (any agent can ignore it; the deploy-keeper supervisor
# tick CHOOSES to honor it). flock acquisitions are bounded by
# STACK_OWNER_FLOCK_TIMEOUT_SEC (default 5s) so a stuck holder can never
# wedge the helper indefinitely.
#
# Verbs:
#   acquire <owner> <task_id> <reason>
#     Atomically write {owner, task_id, acquired_at, reason} when the
#     current owner is "free" (or matches the requested task_id, which
#     makes acquire idempotent under reentry). Refuses with exit 2 when
#     a different owner already holds.
#   release <task_id>
#     Atomically clear the owner back to "free" iff the current task_id
#     matches the caller's. A mismatched release returns exit 3 (the
#     caller does not own the lock; this is intentional so a stale
#     supervisor cannot trample a live export's hold).
#   current
#     Print the current owner string ("export" / "deploy" / "free") on
#     stdout. Exit 0. Missing file = "free". This is the load-bearing
#     query the deploy-keeper tick consults before redeploying.
#   status
#     Print the full JSON record on stdout (pretty-printed). Exit 0.
#     Missing file synthesises the canonical "free" record.
#
# All verbs accept STACK_OWNER_FILE in env to point at an alternate path
# (used by tests). The default is $AGENT_FARM_ROOT/state/stack-owner.json.
#
# Usage from another shell script:
#   source "$ROOT/scripts/lib/stack_owner.sh"
#   stack_owner_current        # echoes free | deploy | export
#   stack_owner_acquire export "$TASK_ID" "FARM-EXP.13 24-cell sweep"
#   stack_owner_release "$TASK_ID"
#
# Usage from the CLI (deploy-keeper-trigger style):
#   bash scripts/lib/stack_owner.sh acquire export farm-exp-13 "long sweep"
#   bash scripts/lib/stack_owner.sh current
#   bash scripts/lib/stack_owner.sh release farm-exp-13

set -uo pipefail

STACK_OWNER_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
STACK_OWNER_FILE="${STACK_OWNER_FILE:-$STACK_OWNER_ROOT/state/stack-owner.json}"
STACK_OWNER_LOCK="${STACK_OWNER_FILE}.lock"
STACK_OWNER_FLOCK_TIMEOUT_SEC="${STACK_OWNER_FLOCK_TIMEOUT_SEC:-5}"

# Allowed owners. "free" means nobody holds the lock; any other value
# means an agent has explicitly claimed it. We keep the set small so a
# typo at the conductor surface fails loudly.
_stack_owner_valid_owner() {
  case "$1" in
    free|deploy|export) return 0 ;;
    *) return 1 ;;
  esac
}

# _stack_owner_with_lock <cmd> [args...]
# Run <cmd> inside an flock-guarded subshell. Bounded by
# STACK_OWNER_FLOCK_TIMEOUT_SEC; a contended call exits non-zero rather
# than hanging the caller.
_stack_owner_with_lock() {
  mkdir -p "$(dirname "$STACK_OWNER_LOCK")" 2>/dev/null || true
  # `flock -w N` waits up to N seconds; exit code 1 means timeout.
  (
    flock -w "$STACK_OWNER_FLOCK_TIMEOUT_SEC" 9 || {
      printf 'stack_owner: flock contention (>%ss); aborting\n' \
        "$STACK_OWNER_FLOCK_TIMEOUT_SEC" >&2
      exit 4
    }
    "$@"
  ) 9>"$STACK_OWNER_LOCK"
}

# _stack_owner_read_field <field>
# Print the value of <field> from the JSON record. Missing file means
# the canonical "free" record (owner=free, task_id=, acquired_at=, reason=).
# Uses python3 so we never grow a jq dep just for this.
_stack_owner_read_field() {
  local field="$1"
  if [[ ! -f "$STACK_OWNER_FILE" ]]; then
    case "$field" in
      owner) printf 'free' ;;
      *) printf '' ;;
    esac
    return 0
  fi
  python3 - "$STACK_OWNER_FILE" "$field" <<'PY'
import json, sys
path, field = sys.argv[1], sys.argv[2]
try:
    with open(path) as f:
        d = json.load(f)
except Exception:
    d = {"owner": "free"}
val = d.get(field, "")
if val is None:
    val = ""
sys.stdout.write(str(val))
PY
}

# _stack_owner_write <owner> <task_id> <reason>
# Atomic-ish write: tmpfile in the same dir + rename. Caller MUST already
# hold the flock.
_stack_owner_write() {
  local owner="$1" task_id="$2" reason="$3"
  local dir tmp
  dir="$(dirname "$STACK_OWNER_FILE")"
  mkdir -p "$dir"
  tmp=$(mktemp "${STACK_OWNER_FILE}.XXXXXX")
  python3 - "$tmp" "$owner" "$task_id" "$reason" <<'PY'
import json, sys, datetime
tmp, owner, task_id, reason = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
record = {
    "owner": owner,
    "task_id": task_id,
    "acquired_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "reason": reason,
}
with open(tmp, "w") as f:
    json.dump(record, f, indent=2, sort_keys=True)
    f.write("\n")
PY
  mv -f "$tmp" "$STACK_OWNER_FILE"
}

# stack_owner_current: print the current owner (one of free|deploy|export).
# Exit 0. Safe to call without a lock; the read is one stat + one json.load.
stack_owner_current() {
  _stack_owner_read_field owner
  printf '\n'
}

# stack_owner_status: print the full JSON record. Missing file synthesises
# the canonical "free" record so downstream readers always see a complete
# shape.
stack_owner_status() {
  if [[ -f "$STACK_OWNER_FILE" ]]; then
    cat "$STACK_OWNER_FILE"
    return 0
  fi
  cat <<'EOF'
{
  "acquired_at": "",
  "owner": "free",
  "reason": "",
  "task_id": ""
}
EOF
}

# stack_owner_acquire <owner> <task_id> <reason>
# Atomically claim the lock for <owner>=<task_id>. Idempotent under
# reentry by the same task_id. Refuses when a different owner holds.
# Exits:
#   0 on success (lock now held by caller)
#   1 on bad args
#   2 on contention (a different owner holds)
#   4 on flock timeout
stack_owner_acquire() {
  local owner="${1:-}" task_id="${2:-}" reason="${3:-}"
  if [[ -z "$owner" || -z "$task_id" ]]; then
    printf 'stack_owner_acquire: usage: acquire <owner> <task_id> <reason>\n' >&2
    return 1
  fi
  if ! _stack_owner_valid_owner "$owner" || [[ "$owner" == "free" ]]; then
    printf 'stack_owner_acquire: invalid owner %q (expected deploy|export)\n' "$owner" >&2
    return 1
  fi
  _stack_owner_with_lock _stack_owner_acquire_inner "$owner" "$task_id" "$reason"
}

_stack_owner_acquire_inner() {
  local owner="$1" task_id="$2" reason="$3"
  local cur_owner cur_task
  cur_owner=$(_stack_owner_read_field owner)
  cur_task=$(_stack_owner_read_field task_id)
  if [[ "$cur_owner" == "free" || ( "$cur_owner" == "$owner" && "$cur_task" == "$task_id" ) ]]; then
    _stack_owner_write "$owner" "$task_id" "$reason"
    printf 'stack_owner: acquired owner=%s task_id=%s\n' "$owner" "$task_id"
    return 0
  fi
  printf 'stack_owner: contention: owner=%s task_id=%s already holds (requested owner=%s task_id=%s)\n' \
    "$cur_owner" "$cur_task" "$owner" "$task_id" >&2
  return 2
}

# stack_owner_release <task_id>
# Clear the lock iff the current holder matches <task_id>. Exits:
#   0 on success (lock is now free, or was already free)
#   1 on bad args
#   3 on mismatched holder
#   4 on flock timeout
stack_owner_release() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    printf 'stack_owner_release: usage: release <task_id>\n' >&2
    return 1
  fi
  _stack_owner_with_lock _stack_owner_release_inner "$task_id"
}

_stack_owner_release_inner() {
  local task_id="$1"
  local cur_owner cur_task
  cur_owner=$(_stack_owner_read_field owner)
  cur_task=$(_stack_owner_read_field task_id)
  if [[ "$cur_owner" == "free" ]]; then
    printf 'stack_owner: release noop (already free)\n'
    return 0
  fi
  if [[ "$cur_task" != "$task_id" ]]; then
    printf 'stack_owner: release refused: owner=%s task_id=%s does not match caller %s\n' \
      "$cur_owner" "$cur_task" "$task_id" >&2
    return 3
  fi
  _stack_owner_write "free" "" "released by $task_id"
  printf 'stack_owner: released (was owner=%s task_id=%s)\n' "$cur_owner" "$cur_task"
  return 0
}

# CLI dispatcher. When sourced (BASH_SOURCE[0] != $0) this block is a
# no-op; the caller uses the stack_owner_* functions directly.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  verb="${1:-}"
  shift || true
  case "$verb" in
    acquire) stack_owner_acquire "$@"; exit $? ;;
    release) stack_owner_release "$@"; exit $? ;;
    current) stack_owner_current; exit 0 ;;
    status)  stack_owner_status; exit 0 ;;
    ""|-h|--help)
      cat <<EOF
stack_owner.sh -- advisory PROTEA-stack ownership lock (FARM-FEAT.12)

Usage:
  stack_owner.sh acquire <owner> <task_id> <reason>
  stack_owner.sh release <task_id>
  stack_owner.sh current
  stack_owner.sh status

Owners: deploy | export

Storage: \$STACK_OWNER_FILE (default \$AGENT_FARM_ROOT/state/stack-owner.json)
EOF
      exit 0
      ;;
    *)
      printf 'stack_owner.sh: unknown verb %q (try --help)\n' "$verb" >&2
      exit 1
      ;;
  esac
fi
