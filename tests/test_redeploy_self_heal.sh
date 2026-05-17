#!/usr/bin/env bash
# tests/test_redeploy_self_heal.sh -- FARM-1.6
#
# Verifies that scripts/services/lib/protea_redeploy.sh self-heals when
# the deploy worktree at $DEPLOY_PATH has been removed (memory
# feedback_deploy_worktree_bootstrap). The test uses a synthetic
# PROTEA-shaped git clone in a tmpdir so no real network / docker /
# develop branch is touched, and short-circuits before the heavy deploy
# pipeline via PROTEA_REDEPLOY_SELF_HEAL_TEST=1.
#
# Run from anywhere:
#   bash tests/test_redeploy_self_heal.sh
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)
#
# Also discovered by the pytest sweep via the worktree's test_*.py shim
# convention; if no shim is shipped we are still safe because the
# bash test is fully self-contained.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REDEPLOY="$REPO_ROOT/scripts/services/lib/protea_redeploy.sh"

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

assert_true() {
  local desc="$1" cond="$2"
  if eval "$cond"; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: condition failed: $cond")
    printf '  FAIL %s\n' "$desc"
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

# --- 0. preflight ------------------------------------------------------
echo "## 0. preflight"
if [[ -f "$REDEPLOY" ]]; then
  PASS=$((PASS + 1))
  echo "  ok  redeploy script present at $REDEPLOY"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("missing script: $REDEPLOY")
  echo "  FAIL redeploy script missing"
fi
if bash -n "$REDEPLOY"; then
  PASS=$((PASS + 1))
  echo "  ok  bash -n passes"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("bash -n failed on $REDEPLOY")
fi

# --- 1. set up synthetic PROTEA clone ----------------------------------
# We need a git repo that looks like PROTEA from the redeploy script's
# point of view: it must have a working `origin/develop` ref that a
# `git worktree add` can resolve. We achieve this by creating a "remote"
# bare repo with a develop branch and cloning it.
echo "## 1. synthetic PROTEA clone + remote"
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

REPOS_DIR_T="$SANDBOX/repositories"
REMOTE_DIR="$SANDBOX/remote"
DEPLOY_PARENT="$SANDBOX/worktrees"
DEPLOY_PATH_T="$DEPLOY_PARENT/protea-deploy"
LOG_DIR="$SANDBOX/state/logs"
LOG_FILE_T="$LOG_DIR/protea_redeploy.log"

mkdir -p "$REPOS_DIR_T" "$REMOTE_DIR" "$DEPLOY_PARENT" "$LOG_DIR"

# 1a. Build the "remote" repo with a develop branch (bare so we can push to it).
git -C "$REMOTE_DIR" init --bare --initial-branch=develop --quiet
SEED_DIR="$SANDBOX/seed"
git init --initial-branch=develop --quiet "$SEED_DIR"
git -C "$SEED_DIR" -c user.email="test@example.com" -c user.name="test" \
  commit --allow-empty -m "seed commit" --quiet
git -C "$SEED_DIR" remote add origin "$REMOTE_DIR"
git -C "$SEED_DIR" push --quiet origin develop

# 1b. Clone "PROTEA" from the remote.
PROTEA_T="$REPOS_DIR_T/PROTEA"
git clone --quiet "$REMOTE_DIR" "$PROTEA_T"
# Ensure origin/develop ref is resolvable.
git -C "$PROTEA_T" fetch --quiet origin develop

# 1c. Pre-create the deploy worktree (mirrors normal steady state).
git -C "$PROTEA_T" worktree add "$DEPLOY_PATH_T" origin/develop --quiet
assert_true "deploy worktree exists initially" "[[ -d '$DEPLOY_PATH_T/.git' || -f '$DEPLOY_PATH_T/.git' ]]"

# --- 2. self-heal preflight: noop when worktree present ---------------
echo "## 2. self-heal noop when worktree present"
NOOP_OUT=$(
  PROTEA_DEPLOY_PATH="$DEPLOY_PATH_T" \
  PROTEA_REPOS_DIR="$REPOS_DIR_T" \
  PROTEA_REDEPLOY_LOG="$LOG_FILE_T" \
  PROTEA_REDEPLOY_SELF_HEAL_TEST=1 \
  TASK_ID="" \
  bash "$REDEPLOY" 2>&1
)
NOOP_RC=$?
assert_rc "redeploy with present worktree exits 0" 0 "$NOOP_RC"
if [[ "$NOOP_OUT" == *"[self-heal] deploy worktree missing"* ]]; then
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("self-heal triggered when worktree present")
  printf '  FAIL self-heal should not trigger when worktree present\n'
else
  PASS=$((PASS + 1))
  printf '  ok  self-heal did not trigger (worktree present)\n'
fi

# --- 3. delete worktree and re-run: assert rebuild --------------------
echo "## 3. delete deploy worktree; next tick self-heals it"
git -C "$PROTEA_T" worktree remove --force "$DEPLOY_PATH_T"
assert_true "deploy worktree removed" "[[ ! -d '$DEPLOY_PATH_T' ]]"

HEAL_OUT=$(
  PROTEA_DEPLOY_PATH="$DEPLOY_PATH_T" \
  PROTEA_REPOS_DIR="$REPOS_DIR_T" \
  PROTEA_REDEPLOY_LOG="$LOG_FILE_T" \
  PROTEA_REDEPLOY_SELF_HEAL_TEST=1 \
  TASK_ID="" \
  bash "$REDEPLOY" 2>&1
)
HEAL_RC=$?
assert_rc "redeploy after worktree removal exits 0" 0 "$HEAL_RC"
assert_contains "log mentions self-heal" "[self-heal]" "$HEAL_OUT"
assert_contains "log mentions recreated deploy worktree" "recreated deploy worktree" "$HEAL_OUT"
assert_true "deploy worktree exists again" "[[ -d '$DEPLOY_PATH_T/.git' || -f '$DEPLOY_PATH_T/.git' ]]"

# Sanity: the recreated worktree should be on the same commit as origin/develop.
EXPECTED_SHA=$(git -C "$PROTEA_T" rev-parse origin/develop)
ACTUAL_SHA=$(git -C "$DEPLOY_PATH_T" rev-parse HEAD 2>/dev/null || echo MISSING)
if [[ "$EXPECTED_SHA" == "$ACTUAL_SHA" ]]; then
  PASS=$((PASS + 1))
  printf '  ok  recreated worktree HEAD matches origin/develop (%s)\n' "${EXPECTED_SHA:0:8}"
else
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("recreated worktree HEAD mismatch: expected $EXPECTED_SHA, got $ACTUAL_SHA")
  printf '  FAIL recreated worktree HEAD mismatch\n'
fi

# --- 4. PROTEA clone missing: hard fail w/ exit 30 --------------------
echo "## 4. PROTEA clone missing -> exit 30 (cannot self-heal)"
SANDBOX2=$(mktemp -d)
EMPTY_REPOS="$SANDBOX2/empty-repos"
EMPTY_DEPLOY="$SANDBOX2/worktrees/protea-deploy"
mkdir -p "$EMPTY_REPOS"
ERR_OUT=$(
  PROTEA_DEPLOY_PATH="$EMPTY_DEPLOY" \
  PROTEA_REPOS_DIR="$EMPTY_REPOS" \
  PROTEA_REDEPLOY_LOG="$SANDBOX2/redeploy.log" \
  PROTEA_REDEPLOY_SELF_HEAL_TEST=1 \
  TASK_ID="" \
  bash "$REDEPLOY" 2>&1
)
ERR_RC=$?
assert_rc "missing PROTEA clone exits 30" 30 "$ERR_RC"
assert_contains "error mentions PROTEA clone not found" "PROTEA clone not found" "$ERR_OUT"
rm -rf "$SANDBOX2"

# --- summary -----------------------------------------------------------
echo
echo "================================================================"
printf 'protea_redeploy self-heal tests: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0
