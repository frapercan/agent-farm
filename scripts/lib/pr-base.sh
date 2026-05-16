#!/usr/bin/env bash
# pr-base.sh — canonical PR base lookup + gh pr create wrapper (FARM-1.3).
#
# Two callable entry points:
#
#   bash pr-base.sh lookup <repo>
#       Print the canonical base branch (develop / main). Exit 0 on hit,
#       2 if the repo is unknown.
#
#   bash pr-base.sh create <repo> [-- extra gh args]
#       Wrapper around `gh pr create` that forces --base to the canonical
#       value for <repo>. Anything after `--` is forwarded verbatim to
#       `gh pr create`, so callers can still pass --title / --body / --draft.
#
#   bash pr-base.sh check <owner> <repo> <number>
#       Verify the PR's current baseRefName matches the canonical base.
#       Exit 0 if OK, 1 if mismatch (prints the mismatch line to stderr).
#
#   bash pr-base.sh fix <owner> <repo> <number>
#       Rebase the PR to the canonical base via `gh pr edit --base`.
#       Idempotent (no-op when already correct). Exit 0 on success.
#
# This script never falls back to a default base. If the repo is not in
# the canonical table, every entry point errors out — silent fallback is
# the bug this slice fixes (see context/memory/feedback_pr_base_develop).

set -euo pipefail

THIS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PR_BASE_PY="$THIS_DIR/pr_base.py"

[[ -f "$PR_BASE_PY" ]] || {
  echo "pr-base.sh: missing $PR_BASE_PY" >&2
  exit 2
}

pr_base_lookup() {
  local repo="${1:-}"
  [[ -n "$repo" ]] || { echo "pr-base.sh lookup: missing <repo>" >&2; exit 2; }
  python3 "$PR_BASE_PY" lookup "$repo"
}

pr_base_create() {
  local repo="${1:-}"
  [[ -n "$repo" ]] || { echo "pr-base.sh create: missing <repo>" >&2; exit 2; }
  shift
  local base
  base=$(pr_base_lookup "$repo")
  # If a --base was already passed in the extra args, honour it but warn.
  for arg in "$@"; do
    if [[ "$arg" == "--base" || "$arg" == "-B" ]]; then
      echo "pr-base.sh create: caller already passed --base; not overriding (use 'lookup' alone if you want to consult the table)." >&2
      exec gh pr create "$@"
    fi
  done
  exec gh pr create --base "$base" "$@"
}

pr_base_check() {
  local owner="${1:-}" repo="${2:-}" number="${3:-}"
  [[ -n "$owner" && -n "$repo" && -n "$number" ]] || {
    echo "pr-base.sh check: usage: check <owner> <repo> <number>" >&2
    exit 2
  }
  local expected actual
  expected=$(pr_base_lookup "$repo")
  actual=$(gh pr view "$number" -R "$owner/$repo" --json baseRefName -q .baseRefName 2>/dev/null) || {
    echo "pr-base.sh check: gh pr view failed for $owner/$repo#$number" >&2
    exit 1
  }
  if [[ "$actual" == "$expected" ]]; then
    return 0
  fi
  echo "pr-base.sh check: $owner/$repo#$number base=$actual expected=$expected" >&2
  return 1
}

pr_base_fix() {
  local owner="${1:-}" repo="${2:-}" number="${3:-}"
  [[ -n "$owner" && -n "$repo" && -n "$number" ]] || {
    echo "pr-base.sh fix: usage: fix <owner> <repo> <number>" >&2
    exit 2
  }
  local expected actual
  expected=$(pr_base_lookup "$repo")
  actual=$(gh pr view "$number" -R "$owner/$repo" --json baseRefName -q .baseRefName 2>/dev/null) || {
    echo "pr-base.sh fix: gh pr view failed for $owner/$repo#$number" >&2
    exit 1
  }
  if [[ "$actual" == "$expected" ]]; then
    echo "pr-base.sh fix: $owner/$repo#$number already on $expected (no-op)" >&2
    return 0
  fi
  echo "pr-base.sh fix: rebasing $owner/$repo#$number $actual -> $expected" >&2
  gh pr edit "$number" -R "$owner/$repo" --base "$expected"
}

cmd="${1:-}"
shift || true
case "$cmd" in
  lookup)  pr_base_lookup "$@" ;;
  create)  pr_base_create "$@" ;;
  check)   pr_base_check  "$@" ;;
  fix)     pr_base_fix    "$@" ;;
  list)    python3 "$PR_BASE_PY" list ;;
  ""|-h|--help)
    cat <<'USAGE'
pr-base.sh — canonical PR base helper

  pr-base.sh lookup <repo>                    -> prints develop|main
  pr-base.sh create <repo> [-- gh pr create args]
  pr-base.sh check  <owner> <repo> <number>   -> exit 0/1
  pr-base.sh fix    <owner> <repo> <number>   -> gh pr edit --base
  pr-base.sh list                              -> dump canonical table
USAGE
    ;;
  *)
    echo "pr-base.sh: unknown command '$cmd'" >&2
    exit 2
    ;;
esac
