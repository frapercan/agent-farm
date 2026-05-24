#!/usr/bin/env bash
# tests/test_dispatch_with_lock.sh -- FARM-FEAT.13
#
# Four scenarios:
#   (1) Happy path: dispatch_with_lock acquires, runs the command, releases.
#   (2) Failure path: command exits non-zero -> lock STILL released.
#   (3) Contended path: acquire fails when lock already held by a different
#       task -> exit 2, command NOT run.
#   (4) Missing separator: exit 1, command NOT run.
#
# Exit 0 iff every assertion passes.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACK_OWNER_LIB="$REPO_ROOT/scripts/lib/stack_owner.sh"
DWL="$REPO_ROOT/scripts/services/lib/dispatch_with_lock.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() {
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("$1")
  printf '  FAIL %s\n' "$1" >&2
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STATE_FILE="$TMP/stack-owner.json"

run_dwl() {
  # Run dispatch_with_lock with the test state file in a subshell so
  # the trap-EXIT in the library does not affect the test runner itself.
  AGENT_FARM_ROOT="$REPO_ROOT" \
  STACK_OWNER_FILE="$STATE_FILE" \
    bash "$DWL" "$@"
}

owner_current() {
  STACK_OWNER_FILE="$STATE_FILE" \
    bash "$STACK_OWNER_LIB" current | tr -d '[:space:]'
}

# ---------- Scenario 1: happy path ----------
echo "== scenario 1: happy path (acquire -> run -> release) =="
rm -f "$STATE_FILE" "${STATE_FILE}.lock"

CMD_RAN="$TMP/cmd_ran.1"
run_dwl "task-happy" "EXP.14 sweep" -- bash -c "touch $CMD_RAN; exit 0"
RC1=$?

if [[ "$RC1" == "0" ]]; then
  note_pass "dispatch_with_lock exits 0 on command success"
else
  note_fail "expected exit 0, got $RC1"
fi

if [[ -f "$CMD_RAN" ]]; then
  note_pass "command was executed"
else
  note_fail "command was NOT executed (sentinel file missing)"
fi

CUR=$(owner_current)
if [[ "$CUR" == "free" ]]; then
  note_pass "lock released after successful command"
else
  note_fail "expected free after success, got '$CUR'"
fi

# ---------- Scenario 2: command fails -> lock still released ----------
echo
echo "== scenario 2: command fails -> lock released anyway =="
rm -f "$STATE_FILE" "${STATE_FILE}.lock"

CMD_RAN2="$TMP/cmd_ran.2"
run_dwl "task-fail" "EXP.14 sweep" -- bash -c "touch $CMD_RAN2; exit 42" || RC2=$?
RC2=${RC2:-0}

if [[ "$RC2" == "42" ]]; then
  note_pass "dispatch_with_lock propagates command exit code 42"
else
  note_fail "expected exit 42, got $RC2"
fi

if [[ -f "$CMD_RAN2" ]]; then
  note_pass "command ran before failure"
else
  note_fail "command did not run in failure scenario"
fi

CUR2=$(owner_current)
if [[ "$CUR2" == "free" ]]; then
  note_pass "lock released despite command failure"
else
  note_fail "expected free after command failure, got '$CUR2'"
fi

# ---------- Scenario 3: contended path -> exit 2, command NOT run ----------
echo
echo "== scenario 3: contended path -> exit 2, command NOT run =="
rm -f "$STATE_FILE" "${STATE_FILE}.lock"

# Simulate another task holding the lock.
STACK_OWNER_FILE="$STATE_FILE" \
  bash "$STACK_OWNER_LIB" acquire export "other-task-99" "pre-existing export" \
  >/dev/null 2>&1

CMD_RAN3="$TMP/cmd_ran.3"
run_dwl "task-new" "EXP.15 sweep" -- bash -c "touch $CMD_RAN3; exit 0" || RC3=$?
RC3=${RC3:-0}

if [[ "$RC3" == "2" ]]; then
  note_pass "dispatch_with_lock exits 2 when lock is contended"
else
  note_fail "expected exit 2 (contended), got $RC3"
fi

if [[ ! -f "$CMD_RAN3" ]]; then
  note_pass "command was NOT executed when lock contended"
else
  note_fail "command ran despite lock contention (sentinel file exists)"
fi

# The original holder must still own the lock.
CUR3=$(owner_current)
if [[ "$CUR3" == "export" ]]; then
  note_pass "lock still held by original owner after contention rejection"
else
  note_fail "expected export owner after rejection, got '$CUR3'"
fi

HOLDER=$(STACK_OWNER_FILE="$STATE_FILE" \
           bash "$STACK_OWNER_LIB" status | python3 -c "import json,sys; print(json.load(sys.stdin)['task_id'])")
if [[ "$HOLDER" == "other-task-99" ]]; then
  note_pass "task_id still 'other-task-99' after failed contender attempt"
else
  note_fail "expected task_id=other-task-99, got '$HOLDER'"
fi

# ---------- Scenario 4: missing -- separator ----------
echo
echo "== scenario 4: missing separator -> exit 1 =="
rm -f "$STATE_FILE" "${STATE_FILE}.lock"

CMD_RAN4="$TMP/cmd_ran.4"
run_dwl "task-bad" "bad call" bash -c "touch $CMD_RAN4" || RC4=$?
RC4=${RC4:-0}

if [[ "$RC4" == "1" ]]; then
  note_pass "missing separator causes exit 1"
else
  note_fail "expected exit 1 for missing separator, got $RC4"
fi

if [[ ! -f "$CMD_RAN4" ]]; then
  note_pass "command NOT run when separator missing"
else
  note_fail "command ran despite missing separator"
fi

# Lock must still be free (no acquire attempted when args bad).
CUR4=$(owner_current)
if [[ "$CUR4" == "free" ]]; then
  note_pass "lock remains free when args are bad"
else
  note_fail "expected free after bad-args, got '$CUR4'"
fi

# ---------- Summary ----------
echo
echo "PASS=$PASS FAIL=$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  printf 'failures:\n' >&2
  for m in "${FAIL_MSGS[@]}"; do printf '  - %s\n' "$m" >&2; done
  exit 1
fi
exit 0
