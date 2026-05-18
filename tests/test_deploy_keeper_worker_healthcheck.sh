#!/usr/bin/env bash
# tests/test_deploy_keeper_worker_healthcheck.sh
# Slice: FARM-DK-WORKER-HEALTHCHECK
#
# Verifies the verify_workers_alive() function added to
# scripts/services/lib/protea_redeploy.sh:
#
#   1. Returns 0 when no pid dir exists (fresh bootstrap case).
#   2. Returns 0 when every worker-*.pid points at a live pid.
#   3. Returns 1 ONLY after a dead worker has been missed for
#      $WORKER_MISS_THRESHOLD consecutive ticks (debouncer).
#   4. Populates WORKERS_MISSING_NAMES with the queue label for the
#      breached worker (e.g. protea.evaluations for worker-evaluations).
#   5. Resets a worker's miss-count to zero once it comes back alive.
#   6. Ignores api.pid / frontend.pid (only worker-*.pid is scanned).
#
# Strategy: source the redeploy script with $PROTEA_REDEPLOY_SELF_HEAL_TEST=1
# so the heavy deploy pipeline is short-circuited and we can run
# verify_workers_alive() in isolation against a synthetic pids dir
# populated with controlled pids.
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)
#
# A pytest shim (test_deploy_keeper_worker_healthcheck_pyshim.py) wraps
# this so the pytest sweep picks it up too.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REDEPLOY="$REPO_ROOT/scripts/services/lib/protea_redeploy.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() {
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("$1")
  printf '  FAIL %s\n' "$1"
}

assert_rc() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    note_pass "$desc"
  else
    note_fail "$desc (expected rc=$expected, got rc=$actual)"
  fi
}

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    note_pass "$desc"
  else
    note_fail "$desc (expected '$expected', got '$actual')"
  fi
}

# --- 0. preflight ------------------------------------------------------
echo "## 0. preflight"
if [[ -f "$REDEPLOY" ]]; then
  note_pass "redeploy script present at $REDEPLOY"
else
  note_fail "redeploy script missing: $REDEPLOY"
  exit 1
fi

# --- 1. synthetic deploy worktree shell --------------------------------
echo "## 1. synthetic deploy worktree + state dir"
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

DEPLOY_PATH_T="$SANDBOX/worktrees/protea-deploy"
PIDS_DIR="$DEPLOY_PATH_T/logs/pids"
STATE_FILE="$SANDBOX/state/deploy_keeper_worker_miss_count"
LOG_FILE_T="$SANDBOX/state/logs/protea_redeploy.log"
mkdir -p "$(dirname "$STATE_FILE")" "$(dirname "$LOG_FILE_T")"

# Helper: write a pid file pointing at a long-lived sleep process, so
# `kill -0 $pid` reliably succeeds. Track the pid in $LIVE_PIDS so we
# can clean them up at the end.
LIVE_PIDS=()
spawn_live_worker() {
  local name="$1"
  mkdir -p "$PIDS_DIR"
  sleep 600 &
  local pid=$!
  LIVE_PIDS+=("$pid")
  printf '%s\n' "$pid" > "$PIDS_DIR/${name}.pid"
}

# Helper: write a pid file pointing at a dead pid (start + kill a
# short-lived process; reuse its pid string. Risk of pid reuse is
# negligible inside the test runtime).
write_dead_pid() {
  local name="$1"
  mkdir -p "$PIDS_DIR"
  (true) &
  local pid=$!
  wait "$pid" 2>/dev/null || true
  # Confirm the pid is no longer running before writing it.
  if kill -0 "$pid" 2>/dev/null; then
    note_fail "pid $pid still running after wait (test setup error)"
    return 1
  fi
  printf '%s\n' "$pid" > "$PIDS_DIR/${name}.pid"
}

cleanup_live_pids() {
  local p
  for p in "${LIVE_PIDS[@]}"; do
    kill -9 "$p" 2>/dev/null || true
    # Reap so the shell does not print a "Terminated" notification line.
    wait "$p" 2>/dev/null || true
  done
  LIVE_PIDS=()
}

# Source the redeploy script with the self-heal test short-circuit AND
# AGENT_FARM_ROOT pointing at a writeable sandbox dir, so it does not
# touch the real $HOME state. We must point PROTEA_DEPLOY_PATH at a
# real-enough dir (just needs to exist; verify_workers_alive only reads
# logs/pids inside it). PROTEA_REPOS_DIR is set but no clone is needed
# because we exit before fetch.
#
# We do NOT actually want the script to run its main flow; we only need
# the function definitions. Trick: $PROTEA_REDEPLOY_SELF_HEAL_TEST=1
# exits 0 at the preflight stage. So we cannot source it directly to
# get the function defs (sourcing would also exit our own shell on the
# `exit 0`). Instead, we run the function in a fresh subshell that
# sources the script with `return` short-circuit via a sentinel.
#
# Simpler approach: dynamically build a tiny harness script that
# inlines the function-definition block from the redeploy script by
# sourcing it inside a subshell where `exit` is replaced. We use bash's
# extdebug "DEBUG trap + exit trap" for that. Cleanest method: copy the
# redeploy script up to (but not including) its top-level code into a
# tmpfile and source that instead.
#
# We use a robust approach: copy the part of the file BEFORE the
# `# 0) Self-heal the deploy worktree if it has been removed.` comment
# into a tmpfile (function defs + globals only), source it, then exec
# the test.

LIB_ONLY="$SANDBOX/redeploy_lib_only.sh"
awk 'BEGIN{p=1} /^# 0\) Self-heal the deploy worktree if it has been removed\./{p=0} p' \
  "$REDEPLOY" > "$LIB_ONLY"
if ! grep -q 'verify_workers_alive()' "$LIB_ONLY"; then
  note_fail "lib-only extract did not capture verify_workers_alive()"
  exit 1
fi
note_pass "lib-only extract captures verify_workers_alive()"

# Make $DEPLOY_PATH exist; verify_workers_alive only reads
# $DEPLOY_PATH/logs/pids and writes its state file at $WORKER_MISS_STATE.
mkdir -p "$DEPLOY_PATH_T"

# Source the lib-only script with all overrides in place.
# shellcheck disable=SC1090
PROTEA_DEPLOY_PATH="$DEPLOY_PATH_T" \
PROTEA_REDEPLOY_LOG="$LOG_FILE_T" \
PROTEA_WORKER_MISS_STATE="$STATE_FILE" \
PROTEA_WORKER_MISS_THRESHOLD=2 \
TASK_ID="" \
  source "$LIB_ONLY"

# Re-set after source (the source resets globals from defaults).
# These are consumed by verify_workers_alive() from the sourced lib.
# shellcheck disable=SC2034
DEPLOY_PATH="$DEPLOY_PATH_T"
# shellcheck disable=SC2034
WORKER_MISS_STATE="$STATE_FILE"
# shellcheck disable=SC2034
WORKER_MISS_THRESHOLD=2

# --- 2. no pid dir -> 0 ------------------------------------------------
echo "## 2. no pid dir -> verify_workers_alive returns 0"
verify_workers_alive
assert_rc "no pid dir -> rc 0" 0 "$?"
assert_eq "no pid dir -> WORKERS_MISSING_NAMES empty" "" "$WORKERS_MISSING_NAMES"

# --- 3. all workers alive --------------------------------------------
echo "## 3. all workers alive -> rc 0"
mkdir -p "$PIDS_DIR"
spawn_live_worker worker-ping
spawn_live_worker worker-jobs
spawn_live_worker worker-evaluations
# Also drop an api.pid pointing at a DEAD pid; the function must
# ignore it (api healthcheck handles that path upstream).
write_dead_pid api
write_dead_pid frontend

verify_workers_alive
assert_rc "all workers alive -> rc 0" 0 "$?"
assert_eq "all workers alive -> WORKERS_MISSING_NAMES empty" "" "$WORKERS_MISSING_NAMES"

# --- 4. one worker dies; tick 1 must NOT trip (debouncer) -------------
echo "## 4. one worker dies; first miss tick does NOT trip"
# Kill the worker-evaluations pid.
EVAL_PID=$(cat "$PIDS_DIR/worker-evaluations.pid")
kill -9 "$EVAL_PID" 2>/dev/null || true
wait "$EVAL_PID" 2>/dev/null || true
# Drop it from LIVE_PIDS bookkeeping.
NEW_LIVE=()
for p in "${LIVE_PIDS[@]}"; do
  [[ "$p" != "$EVAL_PID" ]] && NEW_LIVE+=("$p")
done
LIVE_PIDS=("${NEW_LIVE[@]}")

verify_workers_alive
rc1=$?
assert_rc "first miss tick -> rc 0 (debouncer)" 0 "$rc1"
# State file should show worker-evaluations count = 1.
if grep -q $'^worker-evaluations\t1$' "$STATE_FILE"; then
  note_pass "state file records worker-evaluations miss_count=1"
else
  note_fail "state file does not record worker-evaluations miss_count=1; contents=$(cat "$STATE_FILE")"
fi

# --- 5. second consecutive miss -> trip + correct queue label ---------
echo "## 5. second consecutive miss -> rc 1 + protea.evaluations label"
verify_workers_alive
rc2=$?
assert_rc "second miss tick -> rc 1 (threshold breached)" 1 "$rc2"
assert_eq "WORKERS_MISSING_NAMES == protea.evaluations" "protea.evaluations" "$WORKERS_MISSING_NAMES"

# --- 6. recover: re-spawn the worker; count resets to 0 ---------------
echo "## 6. worker recovers -> miss_count resets to 0"
spawn_live_worker worker-evaluations
verify_workers_alive
rc3=$?
assert_rc "recovered worker -> rc 0" 0 "$rc3"
if grep -q $'^worker-evaluations\t0$' "$STATE_FILE"; then
  note_pass "state file resets worker-evaluations miss_count to 0"
else
  note_fail "state file did not reset worker-evaluations to 0; contents=$(cat "$STATE_FILE")"
fi

# --- 7. queue-label mapping for batch + coord/write --------------------
echo "## 7. queue-label mapping for batch / coord / write / reaper"
# Kill ALL the alive workers + add a few more with the names we want to
# probe. Then trip the debouncer for each and assert label.
cleanup_live_pids
rm -rf "$PIDS_DIR"
mkdir -p "$PIDS_DIR"
rm -f "$STATE_FILE"
# speed up: trip after first miss for this case (consumed by sourced lib)
# shellcheck disable=SC2034
WORKER_MISS_THRESHOLD=1
# shellcheck disable=SC2034
PROTEA_WORKER_MISS_THRESHOLD=1

write_dead_pid worker-predictions-batch-1
write_dead_pid worker-embeddings-coord
write_dead_pid worker-reaper

verify_workers_alive
rc7=$?
assert_rc "all three breached at threshold=1 -> rc 1" 1 "$rc7"
# Expect comma-separated label set; order is dict-traversal so check
# membership for robustness.
case ",$WORKERS_MISSING_NAMES," in
  *",protea.predictions.batch,"*) note_pass "label includes protea.predictions.batch" ;;
  *) note_fail "label missing protea.predictions.batch (got: $WORKERS_MISSING_NAMES)" ;;
esac
case ",$WORKERS_MISSING_NAMES," in
  *",protea.embeddings,"*) note_pass "label includes protea.embeddings (coord)" ;;
  *) note_fail "label missing protea.embeddings (got: $WORKERS_MISSING_NAMES)" ;;
esac
case ",$WORKERS_MISSING_NAMES," in
  *",reaper,"*) note_pass "label includes reaper" ;;
  *) note_fail "label missing reaper (got: $WORKERS_MISSING_NAMES)" ;;
esac

# --- 8. cleanup --------------------------------------------------------
cleanup_live_pids

# --- summary -----------------------------------------------------------
echo
echo "================================================================"
printf 'verify_workers_alive tests: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0
