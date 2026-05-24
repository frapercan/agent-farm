#!/usr/bin/env bash
# test_bootstrap_fresh_machine.sh — shellcheck + syntax + container probe for
# scripts/bootstrap-fresh-machine.sh
#
# Usage:
#   bash tests/test_bootstrap_fresh_machine.sh
#
# Exit 0 if all checks pass, 1 otherwise.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/scripts/bootstrap-fresh-machine.sh"

PASS=0
FAIL=0

ok()   { echo "[PASS] $*"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }

# ---------------------------------------------------------------------------
# 1. File exists + is executable
# ---------------------------------------------------------------------------

if [[ -f "$SCRIPT" ]]; then
  ok "script file exists"
else
  fail "script not found at $SCRIPT"
fi

if [[ -x "$SCRIPT" ]]; then
  ok "script is executable"
else
  fail "script is not executable"
fi

# ---------------------------------------------------------------------------
# 2. Bash -n syntax check
# ---------------------------------------------------------------------------

if bash -n "$SCRIPT" 2>/dev/null; then
  ok "bash -n syntax check"
else
  bash -n "$SCRIPT" 2>&1 || true
  fail "bash -n syntax check"
fi

# ---------------------------------------------------------------------------
# 3. shellcheck
# ---------------------------------------------------------------------------

if command -v shellcheck &>/dev/null; then
  if shellcheck "$SCRIPT" 2>/dev/null; then
    ok "shellcheck"
  else
    shellcheck "$SCRIPT" 2>&1 || true
    fail "shellcheck"
  fi
else
  echo "[SKIP] shellcheck not installed"
fi

# ---------------------------------------------------------------------------
# 4. --dry-run prints plan and exits 0
# ---------------------------------------------------------------------------

DRY_OUT="$(bash "$SCRIPT" --dry-run 2>&1)" && DRY_EXIT=0 || DRY_EXIT=$?

if [[ $DRY_EXIT -eq 0 ]]; then
  ok "--dry-run exits 0"
else
  fail "--dry-run exited with $DRY_EXIT"
fi

if echo "$DRY_OUT" | grep -q "dry-run"; then
  ok "--dry-run output contains 'dry-run' marker"
else
  fail "--dry-run output missing 'dry-run' marker"
fi

if echo "$DRY_OUT" | grep -q "bootstrap done"; then
  ok "--dry-run output contains 'bootstrap done' summary"
else
  fail "--dry-run output missing 'bootstrap done' summary"
fi

# ---------------------------------------------------------------------------
# 5. Docker container probe: script does not crash on minimal ubuntu:22.04
#    (runs --dry-run inside the container so no network calls needed)
# ---------------------------------------------------------------------------

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  # Pass script via base64 to avoid heredoc quoting issues and Docker
  # file-sharing path restrictions on /tmp.
  SCRIPT_B64="$(base64 < "$SCRIPT")"
  CONTAINER_OUT="$(
    docker run --rm \
      -e "SCRIPT_B64=${SCRIPT_B64}" \
      ubuntu:22.04 bash -c '
        apt-get update -qq 2>/dev/null
        apt-get install -y -qq lsb-release 2>/dev/null
        echo "$SCRIPT_B64" | base64 -d > /bootstrap.sh
        bash /bootstrap.sh --dry-run
      ' 2>&1
  )" && CONTAINER_EXIT=0 || CONTAINER_EXIT=$?

  if [[ $CONTAINER_EXIT -eq 0 ]]; then
    ok "docker container probe (ubuntu:22.04 --dry-run) exits 0"
  else
    echo "$CONTAINER_OUT"
    fail "docker container probe exited with $CONTAINER_EXIT"
  fi

  if echo "$CONTAINER_OUT" | grep -q "bootstrap done"; then
    ok "docker container probe output contains 'bootstrap done'"
  else
    fail "docker container probe output missing 'bootstrap done'"
  fi
else
  echo "[SKIP] docker not available or daemon not running; skipping container probe"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
echo "Results: $PASS passed, $FAIL failed"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
