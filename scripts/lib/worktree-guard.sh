#!/usr/bin/env bash
# worktree-guard.sh — refuse to operate inside the developer's main checkout.
#
# Implements FARM-1.4. Janitor agents (and any other subagent that may be
# tempted to `gh pr checkout` a branch) must run inside an ephemeral
# worktree under `$HOME/Thesis2/worktrees/`. The dev workspace at
# `$HOME/Thesis2/repositories/<repo>/` is off-limits because:
#
#   1. It is the developer's primary checkout. Switching branches there
#      moves the dev's working tree (memory: feedback_janitor_must_use_worktree).
#   2. The main checkout has no FARM-1.1 enforcement hooks installed
#      (the install-hooks.sh installer only wires per-worktree hooks).
#
# Two callable entry points:
#
#   bash worktree-guard.sh assert [path]
#       Assert that <path> (default $PWD) is an ephemeral worktree.
#       Exit 0 if OK, exit 1 with a clear stderr message otherwise.
#
#   bash worktree-guard.sh checkout <pr-number> [-- extra gh args]
#       Safe wrapper around `gh pr checkout`. Calls `assert` first; only
#       then runs the checkout. Anything after `--` is forwarded to
#       `gh pr checkout` (e.g. -R owner/repo).
#
# Sourceable: callers may also `source` this file and call the function
# `assert_in_worktree [path]` directly.
#
# Bypass switch (test-suite + rollback only):
#   AGENT_FARM_SKIP_WORKTREE_GUARD=1  — assert exits 0 unconditionally.
#   This env var is intentionally NOT exposed to agent prompts.

set -euo pipefail

# Where the dev's main checkouts live. Configurable for test purposes.
AGENT_FARM_REPOS_ROOT="${AGENT_FARM_REPOS_ROOT:-$HOME/Thesis2/repositories}"
AGENT_FARM_WORKTREES_ROOT="${AGENT_FARM_WORKTREES_ROOT:-$HOME/Thesis2/worktrees}"

_wtg_info() {
  printf 'worktree-guard: %s\n' "$*" >&2
}

_wtg_die() {
  _wtg_info "$*"
  exit 1
}

# assert_in_worktree [path]
#   Returns 0 if the path is an ephemeral agent worktree.
#   Exits 1 (with a message) if it is the dev's main checkout or not a worktree.
assert_in_worktree() {
  if [[ "${AGENT_FARM_SKIP_WORKTREE_GUARD:-0}" == "1" ]]; then
    return 0
  fi

  local target="${1:-$PWD}"
  if [[ ! -d "$target" ]]; then
    _wtg_die "path does not exist: $target"
  fi

  # Resolve symlinks so the prefix checks are robust.
  local abs
  abs=$(cd "$target" 2>/dev/null && pwd -P) || _wtg_die "cannot enter $target"

  # 1. Must NOT be under the dev's repositories root.
  local repos_root_abs
  repos_root_abs=$(cd "$AGENT_FARM_REPOS_ROOT" 2>/dev/null && pwd -P) || true
  if [[ -n "$repos_root_abs" && "$abs" == "$repos_root_abs"/* ]]; then
    _wtg_info "refusing to operate inside the dev workspace: $abs"
    _wtg_info "(this would alter the developer's main checkout under $repos_root_abs)"
    _wtg_die "spawn yourself in a worktree under $AGENT_FARM_WORKTREES_ROOT/<task_id>/"
  fi

  # 2. Must be a git checkout.
  local git_dir common_dir
  git_dir=$(git -C "$abs" rev-parse --git-dir 2>/dev/null) || \
    _wtg_die "not a git working tree: $abs"
  common_dir=$(git -C "$abs" rev-parse --git-common-dir 2>/dev/null) || \
    _wtg_die "git rev-parse --git-common-dir failed for $abs"

  # Normalise both to absolute paths so equality works regardless of cwd.
  [[ "$git_dir" = /* ]]    || git_dir=$(cd "$abs" && cd "$git_dir" && pwd -P)
  [[ "$common_dir" = /* ]] || common_dir=$(cd "$abs" && cd "$common_dir" && pwd -P)

  # 3. Must be a worktree (git-dir != git-common-dir). Main checkouts have
  #    git_dir == common_dir; linked worktrees have git_dir = .git/worktrees/<name>.
  if [[ "$git_dir" == "$common_dir" ]]; then
    _wtg_info "refusing to operate in the main checkout (not a linked worktree): $abs"
    _wtg_info "git-dir and git-common-dir are identical ($git_dir)"
    _wtg_die "use 'git worktree add' to make an ephemeral worktree first"
  fi

  return 0
}

# safe_pr_checkout <pr-number> [extra gh args...]
#   Asserts the current dir is a worktree, then runs `gh pr checkout`.
safe_pr_checkout() {
  local pr="${1:-}"
  [[ -n "$pr" ]] || _wtg_die "safe_pr_checkout: missing <pr-number>"
  shift
  assert_in_worktree "$PWD"
  exec gh pr checkout "$pr" "$@"
}

# CLI dispatch (only when invoked as a script, not when sourced).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cmd="${1:-}"
  shift || true
  case "$cmd" in
    assert)
      assert_in_worktree "${1:-$PWD}"
      ;;
    checkout)
      safe_pr_checkout "$@"
      ;;
    ""|-h|--help)
      cat <<'USAGE'
worktree-guard.sh — refuse to mutate the dev workspace

  worktree-guard.sh assert [path]            -> exit 0 if path is an agent worktree
  worktree-guard.sh checkout <pr> [-- gh args]  -> assert + gh pr checkout
USAGE
      ;;
    *)
      echo "worktree-guard.sh: unknown command '$cmd'" >&2
      exit 2
      ;;
  esac
fi
