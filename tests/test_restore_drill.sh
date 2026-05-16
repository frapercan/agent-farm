#!/usr/bin/env bash
# tests/test_restore_drill.sh -- FARM-1.7
#
# Lightweight test harness for scripts/restore-drill.sh. Verifies the
# flag surface and the --dry-run code path WITHOUT actually launching
# docker or restoring the multi-GB dump (which takes 60-90 min and
# needs a working Docker daemon).
#
# Run from anywhere:
#   bash tests/test_restore_drill.sh
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)
#
# This test is also discovered by the pytest sweep via
# tests/test_restore_drill_pyshim.py (which just shells out to this
# script). Keeping the assertions in bash avoids re-implementing flag
# parsing in two languages.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DRILL="$REPO_ROOT/scripts/restore-drill.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

assert_rc() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: expected rc=$expected, got rc=$actual")
    printf '  FAIL %s (expected rc=%s, got %s)\n' "$desc" "$expected" "$actual"
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: '$needle' not found")
    printf '  FAIL %s ("%s" missing)\n' "$desc" "$needle"
  fi
}

# --- 1. script exists + bash -n clean ----------------------------------
echo "## 1. script exists and is shellcheck-syntax clean"
if [[ -f "$DRILL" ]]; then
  PASS=$((PASS + 1))
  echo "  ok  script present at $DRILL"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("missing script: $DRILL")
  echo "  FAIL script missing"
fi
if bash -n "$DRILL"; then
  PASS=$((PASS + 1))
  echo "  ok  bash -n passes"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("bash -n failed")
fi

# --- 2. --help exits 0 and prints usage --------------------------------
echo "## 2. --help"
HELP_OUT=$(bash "$DRILL" --help 2>&1)
HELP_RC=$?
assert_rc "--help exits 0" 0 "$HELP_RC"
assert_contains "--help mentions --dry-run" "--dry-run" "$HELP_OUT"
assert_contains "--help mentions --backup" "--backup" "$HELP_OUT"

# --- 3. unknown flag rejected ------------------------------------------
echo "## 3. unknown flag is rejected"
UNK_OUT=$(bash "$DRILL" --nope 2>&1)
UNK_RC=$?
assert_rc "--nope exits non-zero" 1 "$UNK_RC"
assert_contains "unknown-flag error mentions arg" "unknown arg" "$UNK_OUT"

# --- 4. --backup missing PATH rejected ---------------------------------
echo "## 4. --backup with no value rejected"
NB_OUT=$(bash "$DRILL" --backup 2>&1)
NB_RC=$?
assert_rc "--backup w/o value exits non-zero" 1 "$NB_RC"
assert_contains "error mentions PATH" "PATH" "$NB_OUT"

# --- 5. --backup PATH for missing file -> die --------------------------
echo "## 5. --backup with missing file -> die"
MF_OUT=$(bash "$DRILL" --backup /nonexistent/protea-fake.dump 2>&1)
MF_RC=$?
assert_rc "missing --backup file exits 1" 1 "$MF_RC"
assert_contains "die mentions missing file" "missing" "$MF_OUT"

# --- 6. --dry-run when no dump exists yields rc=2 ----------------------
echo "## 6. --dry-run with empty BACKUP_DIR -> rc=2 (no docker needed)"
EMPTY_DIR=$(mktemp -d)
trap 'rm -rf "$EMPTY_DIR"' EXIT
EMPTY_OUT=$(BACKUP_DIR="$EMPTY_DIR" bash "$DRILL" --dry-run 2>&1)
EMPTY_RC=$?
assert_rc "--dry-run empty dir exits 2" 2 "$EMPTY_RC"
assert_contains "--dry-run empty mentions DRY-RUN" "DRY-RUN" "$EMPTY_OUT"

# --- 7. --dry-run with --backup PATH skips docker ----------------------
echo "## 7. --dry-run with explicit --backup prints plan, exits 0"
FAKE_DUMP="$EMPTY_DIR/protea-fake.dump"
printf 'fake-dump-content' > "$FAKE_DUMP"
PLAN_OUT=$(BACKUP_DIR="$EMPTY_DIR" bash "$DRILL" --dry-run --backup "$FAKE_DUMP" 2>&1)
PLAN_RC=$?
assert_rc "--dry-run --backup exits 0" 0 "$PLAN_RC"
assert_contains "plan includes container name" "protea-pg-drill" "$PLAN_OUT"
assert_contains "plan includes drill port" "15433" "$PLAN_OUT"
assert_contains "plan includes the supplied backup path" "protea-fake.dump" "$PLAN_OUT"

# --- summary -----------------------------------------------------------
echo
echo "================================================================"
printf 'restore-drill.sh tests: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0
