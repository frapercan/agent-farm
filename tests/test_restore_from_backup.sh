#!/usr/bin/env bash
# tests/test_restore_from_backup.sh -- FARM-INFRA.3
#
# Lightweight test harness for scripts/restore-from-backup.sh.
# Verifies the CLI surface and the --dry-run code path WITHOUT touching
# a real postgres container or running pg_restore (which takes 30-90 min).
#
# Run from anywhere:
#   bash tests/test_restore_from_backup.sh
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)
#
# Also discovered by pytest via the pyshim at
# tests/test_restore_from_backup_pyshim.py.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/restore-from-backup.sh"

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
    FAIL_MSGS+=("FAIL $desc: expected rc=$expected, got rc=$actual")
    printf '  FAIL %s (expected rc=%s, got rc=%s)\n' "$desc" "$expected" "$actual"
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("FAIL $desc: '$needle' not found in output")
    printf '  FAIL %s ("%s" missing)\n' "$desc" "$needle"
  fi
}

assert_not_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("FAIL $desc: '$needle' was unexpectedly found in output")
    printf '  FAIL %s ("%s" unexpectedly found)\n' "$desc" "$needle"
  fi
}

# --- 1. script exists + bash -n clean --------------------------------------
echo "## 1. script exists and bash -n passes"
if [[ -f "$SCRIPT" ]]; then
  PASS=$((PASS + 1))
  echo "  ok  script present at $SCRIPT"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("missing script: $SCRIPT")
  echo "  FAIL script missing"
fi

BASH_N_OUT=$(bash -n "$SCRIPT" 2>&1)
BASH_N_RC=$?
assert_rc "bash -n exits 0" 0 "$BASH_N_RC"
if (( BASH_N_RC == 0 )); then
  assert_not_contains "bash -n produces no output" "error" "$BASH_N_OUT"
fi

# --- 2. shellcheck (advisory; skip if not installed) -----------------------
echo "## 2. shellcheck"
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$SCRIPT" >/dev/null 2>&1
  SC_RC=$?
  assert_rc "shellcheck exits 0" 0 "$SC_RC"
else
  echo "  skip  shellcheck not installed"
fi

# --- 3. --help exits 0 and documents key flags ----------------------------
echo "## 3. --help"
HELP_OUT=$(bash "$SCRIPT" --help 2>&1)
HELP_RC=$?
assert_rc "--help exits 0" 0 "$HELP_RC"
assert_contains "--help mentions --dry-run"  "--dry-run"  "$HELP_OUT"
assert_contains "--help mentions --apply"    "--apply"    "$HELP_OUT"
assert_contains "--help mentions --yes"      "--yes"      "$HELP_OUT"
assert_contains "--help mentions --dump"     "--dump"     "$HELP_OUT"
assert_contains "--help mentions --jobs"     "--jobs"     "$HELP_OUT"

# --- 4. unknown flag rejected ---------------------------------------------
echo "## 4. unknown flag rejected"
UNK_OUT=$(bash "$SCRIPT" --totally-unknown 2>&1)
UNK_RC=$?
assert_rc "unknown flag exits 1" 1 "$UNK_RC"
assert_contains "error mentions 'unknown argument'" "unknown argument" "$UNK_OUT"

# --- 5. --dump with missing PATH argument ---------------------------------
echo "## 5. --dump without value rejected"
bash "$SCRIPT" --dump >/dev/null 2>&1
ND_RC=$?
assert_rc "--dump with no value exits 1" 1 "$ND_RC"

# --- 6. --dump with non-existent file exits 1 ----------------------------
echo "## 6. --dump pointing at missing file exits 1"
MF_OUT=$(bash "$SCRIPT" --dump /nonexistent/protea-fake.dump 2>&1)
MF_RC=$?
assert_rc "missing --dump file exits 1" 1 "$MF_RC"
assert_contains "error mentions 'missing'" "missing" "$MF_OUT"

# --- 7. dry-run with empty backup dir exits 2 ----------------------------
echo "## 7. --dry-run with empty BACKUP_DIR exits 2"
EMPTY_DIR=$(mktemp -d)
trap 'rm -rf "$EMPTY_DIR"' EXIT
BACKUP_DIR="$EMPTY_DIR" bash "$SCRIPT" --dry-run >/dev/null 2>&1
EMPTY_RC=$?
assert_rc "--dry-run empty dir exits 2" 2 "$EMPTY_RC"

# --- 8. dry-run with a real (fake) dump prints plan -----------------------
echo "## 8. --dry-run with --dump prints plan and exits 0"
FAKE_DUMP="$EMPTY_DIR/protea-2026-05-11.dump"
printf 'fake-dump-content' > "$FAKE_DUMP"
PLAN_OUT=$(bash "$SCRIPT" --dry-run --dump "$FAKE_DUMP" 2>&1)
PLAN_RC=$?
assert_rc "--dry-run --dump exits 0" 0 "$PLAN_RC"
assert_contains "plan shows dump file"        "protea-2026-05-11.dump"  "$PLAN_OUT"
assert_contains "plan shows container"        "protea-postgres-1"       "$PLAN_OUT"
assert_contains "plan shows alembic step"     "alembic"                 "$PLAN_OUT"
assert_contains "plan shows restore step"     "pg_restore"              "$PLAN_OUT"
assert_contains "plan shows smoke step"       "smoke"                   "$PLAN_OUT"
assert_contains "plan shows how to execute"   "--apply"                 "$PLAN_OUT"

# --- 9. default (no flags) is dry-run: never prompts for input -----------
echo "## 9. no flags -> dry-run (never blocks on interactive prompt)"
# Use the fake dump dir: the script must produce a plan or 'no dump' exit,
# but must NOT prompt "Type YES to confirm".
DEFAULT_OUT=$(BACKUP_DIR="$EMPTY_DIR" bash "$SCRIPT" --dry-run --dump "$FAKE_DUMP" 2>&1)
DEFAULT_RC=$?
assert_rc "no-flag + --dump exits 0" 0 "$DEFAULT_RC"
assert_not_contains "no prompt without --apply" "Type YES" "$DEFAULT_OUT"

# --- 10. --jobs flag accepted by dry-run ---------------------------------
echo "## 10. --jobs N shows in dry-run plan"
JOBS_OUT=$(bash "$SCRIPT" --dry-run --dump "$FAKE_DUMP" --jobs 8 2>&1)
JOBS_RC=$?
assert_rc "--jobs 8 dry-run exits 0" 0 "$JOBS_RC"
assert_contains "plan shows --jobs=8" "8" "$JOBS_OUT"

# --- summary ---------------------------------------------------------------
echo ""
echo "================================================================"
printf 'restore-from-backup.sh tests: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0
