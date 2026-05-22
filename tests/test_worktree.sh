#!/usr/bin/env bash
# tests/test_worktree.sh -- FARM-FEAT.7
#
# Unit tests for scripts/lib/worktree.sh: wt_create, wt_remove, wt_changed,
# wt_cleanup_orphans. Uses throwaway tmpdir git repos; never touches real
# worktrees or the live database.
#
# Run from anywhere:
#   bash tests/test_worktree.sh
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKTREE_SH="$REPO_ROOT/scripts/lib/worktree.sh"

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
    printf '  FAIL %s (expected rc=%s, got %s)\n' "$desc" "$expected" "$actual" >&2
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
    printf '  FAIL %s\n' "$desc" >&2
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: '$needle' not found in output")
    printf '  FAIL %s ("%s" missing)\n' "$desc" "$needle" >&2
  fi
}

# --- 0. preflight ---------------------------------------------------------
echo "## 0. preflight"
assert_true "worktree.sh present" "[[ -f '$WORKTREE_SH' ]]"
PARSE_RC=0
bash -n "$WORKTREE_SH" || PARSE_RC=$?
assert_rc "worktree.sh bash -n passes" 0 "$PARSE_RC"

# --- scaffold: build a throwaway git repo + remote ------------------------
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

REMOTE="$SANDBOX/remote.git"
REPO="$SANDBOX/repo"
WT_DIR="$SANDBOX/worktrees"

git init --bare --initial-branch=main --quiet "$REMOTE" 2>/dev/null || \
  git init --bare --quiet "$REMOTE"
SEED="$SANDBOX/seed"
git init --initial-branch=main --quiet "$SEED" 2>/dev/null || \
  git init --quiet "$SEED"
git -C "$SEED" -c user.email="test@t" -c user.name="t" \
  commit --allow-empty -m "seed" --quiet
git -C "$SEED" remote add origin "$REMOTE"
git -C "$SEED" push --quiet origin HEAD:main

git clone --quiet "$REMOTE" "$REPO"
git -C "$REPO" fetch --quiet origin main

# --- 1. wt_create ---------------------------------------------------------
echo "## 1. wt_create"

# Source worktree.sh with minimal required env
AGENT_FARM_WORKTREES="$WT_DIR"
AGENT_FARM_ROOT="$REPO_ROOT"
export AGENT_FARM_WORKTREES AGENT_FARM_ROOT
# shellcheck source=../scripts/lib/worktree.sh
source "$WORKTREE_SH"

mkdir -p "$WT_DIR"
TASK1="task-test-001"
WT1=$(wt_create "$TASK1" "$REPO" "origin/main" 2>/tmp/wt-test-err.log)
CREATE_RC=$?
assert_rc "wt_create exits 0" 0 "$CREATE_RC"
assert_true "wt_create echoes path = $WT_DIR/$TASK1" "[[ '$WT1' == '$WT_DIR/$TASK1' ]]"
assert_true "worktree directory exists" "[[ -d '$WT1' ]]"
assert_true "worktree has .git file" "[[ -f '$WT1/.git' ]]"

# Branch created with name task/<task_id>
BRANCH=$(git -C "$WT1" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
assert_true "worktree branch is task/$TASK1" "[[ '$BRANCH' == 'task/$TASK1' ]]"

# Idempotent: second wt_create with same task_id should fail (branch exists)
WT1_DUP=$(wt_create "$TASK1" "$REPO" "origin/main" 2>/dev/null) || true
assert_true "duplicate wt_create does not create second dir" "[[ ! -d '$WT_DIR/${TASK1}-dup' ]]"

# --- 2. wt_changed --------------------------------------------------------
echo "## 2. wt_changed"

# Fresh worktree: no uncommitted changes, no commits ahead -> not changed
wt_changed "$WT1"
CHANGED_RC=$?
assert_rc "fresh worktree not changed (rc=1)" 1 "$CHANGED_RC"

# Make the worktree dirty (untracked file)
touch "$WT1/untracked_file"
wt_changed "$WT1"
CHANGED_DIRTY_RC=$?
assert_rc "worktree with untracked file is changed (rc=0)" 0 "$CHANGED_DIRTY_RC"

# Clean the untracked file and add a real commit
rm "$WT1/untracked_file"
touch "$WT1/new_file.txt"
git -C "$WT1" add new_file.txt
git -C "$WT1" -c user.email="test@t" -c user.name="t" \
  commit -m "test commit" --quiet
wt_changed "$WT1"
CHANGED_COMMIT_RC=$?
assert_rc "worktree with commit ahead is changed (rc=0)" 0 "$CHANGED_COMMIT_RC"

# Missing directory: should return 1 (not changed)
wt_changed "/tmp/nonexistent-worktree-$$"
CHANGED_MISSING_RC=$?
assert_rc "missing worktree dir returns 1" 1 "$CHANGED_MISSING_RC"

# --- 3. wt_remove ---------------------------------------------------------
echo "## 3. wt_remove"

# Create a second throwaway worktree for remove testing
TASK2="task-test-002"
WT2=$(wt_create "$TASK2" "$REPO" "origin/main")
assert_true "second worktree exists before remove" "[[ -d '$WT2' ]]"

# Verify it appears in git worktree list
if git -C "$REPO" worktree list --porcelain 2>/dev/null | grep -q "^worktree $WT2$"; then
  WT2_LISTED=1
else
  WT2_LISTED=0
fi
assert_true "second worktree registered in repo" "[[ '$WT2_LISTED' -ge 1 ]]"

# Remove with explicit repo hint (O(1) path)
wt_remove "$WT2" "$REPO"
REMOVE_RC=$?
assert_rc "wt_remove exits 0" 0 "$REMOVE_RC"
assert_true "worktree dir gone after wt_remove" "[[ ! -d '$WT2' ]]"

# Verify removed from git registry
if git -C "$REPO" worktree list --porcelain 2>/dev/null | grep -q "^worktree $WT2$"; then
  WT2_STILL=1
else
  WT2_STILL=0
fi
assert_true "removed worktree deregistered from repo" "[[ '$WT2_STILL' -eq 0 ]]"

# Create another worktree and remove WITHOUT explicit repo hint (scan fallback)
TASK3="task-test-003"
WT3=$(wt_create "$TASK3" "$REPO" "origin/main")
assert_true "third worktree exists before remove" "[[ -d '$WT3' ]]"
wt_remove "$WT3"
assert_true "worktree dir gone after wt_remove (no hint)" "[[ ! -d '$WT3' ]]"

# Calling wt_remove on non-existent path is a noop (returns 0)
wt_remove "/tmp/gone-already-$$"
REMOVE_GONE_RC=$?
assert_rc "wt_remove on missing path returns 0" 0 "$REMOVE_GONE_RC"

# --- 4. wt_cleanup_orphans ------------------------------------------------
echo "## 4. wt_cleanup_orphans"

# Create two worktrees. We test the helper directly using a local stub for
# the active-tasks query (wt_cleanup_orphans calls python3 db.py query).
TASK4="task-test-004"
TASK5="task-test-005"
WT4=$(wt_create "$TASK4" "$REPO" "origin/main")
WT5=$(wt_create "$TASK5" "$REPO" "origin/main")
assert_true "orphan1 exists" "[[ -d '$WT4' ]]"
assert_true "orphan2 exists" "[[ -d '$WT5' ]]"

# Stub db.py: returns empty active set so every worktree looks orphaned.
STUB_DB="$SANDBOX/db_stub.py"
cat > "$STUB_DB" <<PYEOF
import sys
# Return empty result for the active-tasks query; all else noop.
sys.exit(0)
PYEOF

# Run wt_cleanup_orphans with stubbed db path. We override AGENT_FARM_ROOT to
# point at a fake root that has only the stub db.py so the real database is
# never touched.
FAKE_ROOT="$SANDBOX/fake-farm"
mkdir -p "$FAKE_ROOT/scripts/lib"
cp "$STUB_DB" "$FAKE_ROOT/scripts/lib/db.py"

CLEANUP_OUT=$(
  AGENT_FARM_WORKTREES="$WT_DIR" \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  bash -c "source '$WORKTREE_SH' ; wt_cleanup_orphans" 2>&1
)

assert_contains "cleanup reports orphan removal" "wt_cleanup: removing orphan" "$CLEANUP_OUT"
assert_true "orphan1 removed by cleanup" "[[ ! -d '$WT4' ]]"
assert_true "orphan2 removed by cleanup" "[[ ! -d '$WT5' ]]"

# Verify wt_cleanup_orphans with AGENT_FARM_WT_FORCE=0 skips dirty worktrees.
TASK6="task-test-006"
WT6=$(wt_create "$TASK6" "$REPO" "origin/main")
touch "$WT6/dirty_file"  # make it dirty (untracked)

SKIP_OUT=$(
  AGENT_FARM_WORKTREES="$WT_DIR" \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  AGENT_FARM_WT_FORCE=0 \
  bash -c "source '$WORKTREE_SH' ; wt_cleanup_orphans" 2>&1
)
assert_contains "dirty worktree skipped" "wt_cleanup: SKIP dirty" "$SKIP_OUT"
assert_true "dirty worktree not removed" "[[ -d '$WT6' ]]"

# Cleanup remaining worktrees (WT1 still has a commit ahead, WT6 is dirty)
wt_remove "$WT1" "$REPO"
wt_remove "$WT6" "$REPO"

# --- 5. smoke-test callers parse cleanly ----------------------------------
echo "## 5. bash -n on all four callers"
for script in \
  "$REPO_ROOT/scripts/spawn-subagent.sh" \
  "$REPO_ROOT/scripts/cleanup.sh" \
  "$REPO_ROOT/scripts/kill.sh" \
  "$REPO_ROOT/scripts/finalize-subagent.sh"; do
  PARSE_RC=0
  bash -n "$script" 2>/tmp/parse-err.log || PARSE_RC=$?
  assert_rc "bash -n $(basename "$script")" 0 "$PARSE_RC"
done

# --- summary --------------------------------------------------------------
echo
echo "================================================================"
printf 'test_worktree.sh: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0
