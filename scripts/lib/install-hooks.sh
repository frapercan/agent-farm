#!/usr/bin/env bash
# install-hooks.sh — install agent-farm enforcement hooks into a worktree.
#
# Implements FARM-1.1. Drops four files (commit-msg, pre-commit, pre-push,
# _lib.sh) into a per-worktree hooks directory and points the worktree's
# core.hooksPath at it via worktree-scoped git config.
#
# Why per-worktree, not the shared .git/hooks dir? Because the agent-farm
# repository shares one `.git/hooks` across the main checkout and every
# worktree. Installing into the shared dir would silently leak the hook
# bundle into the developer's main checkout (forbidden by Thesis2 hard
# constraints). Per-worktree hooks live under
# `<git-common-dir>/worktrees/<name>/farm-hooks/` and are addressed via
# `core.hooksPath` set with `git config --worktree`, which requires the
# `extensions.worktreeConfig=true` repo extension (enabled lazily here).
#
# Usage:
#   bash install-hooks.sh <worktree_path>
#   bash install-hooks.sh --uninstall <worktree_path>
#
# Idempotent: re-running overwrites the hooks with the current template
# bodies. Safe to call after every `git worktree add`.
#
# Bypass switch (rollback / test-suite use only):
#   AGENT_FARM_SKIP_HOOKS=1  — hooks no-op (still installed but exit 0).
#   This env var is intentionally NOT exposed to agent prompts.

set -euo pipefail

UNINSTALL=0
if [[ "${1:-}" == "--uninstall" ]]; then
  UNINSTALL=1
  shift
fi

WT="${1:-}"
if [[ -z "$WT" ]]; then
  echo "install-hooks: missing worktree path argument" >&2
  echo "usage: install-hooks.sh [--uninstall] <worktree_path>" >&2
  exit 2
fi
if [[ ! -d "$WT" ]]; then
  echo "install-hooks: worktree path does not exist: $WT" >&2
  exit 2
fi
if ! git -C "$WT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "install-hooks: not a git worktree: $WT" >&2
  exit 2
fi

GITDIR=$(git -C "$WT" rev-parse --absolute-git-dir)
HOOKDIR="$GITDIR/farm-hooks"

if [[ "$UNINSTALL" -eq 1 ]]; then
  if [[ -d "$HOOKDIR" ]]; then
    rm -rf "$HOOKDIR"
    echo "install-hooks: removed $HOOKDIR" >&2
  fi
  # Best effort: unset the per-worktree hooksPath. Ignore failure (e.g.,
  # worktreeConfig extension not enabled means there is nothing to unset).
  git -C "$WT" config --worktree --unset core.hooksPath 2>/dev/null || true
  exit 0
fi

# Enable per-worktree config extension lazily. Idempotent: setting the
# same value twice is a no-op for git. Affects only the agent-farm repo.
git -C "$WT" config extensions.worktreeConfig true

mkdir -p "$HOOKDIR"

# ---------------------------------------------------------------------------
# _lib.sh — shared helpers, sourced by every hook.
# ---------------------------------------------------------------------------
cat > "$HOOKDIR/_lib.sh" <<'LIB_EOF'
#!/usr/bin/env bash
# _lib.sh — shared helpers for agent-farm worktree hooks.
# Do not invoke directly; sourced by commit-msg / pre-commit / pre-push.

farm_die() {
  printf 'agent-farm hook (%s): %s\n' "${HOOK_NAME:-?}" "$*" >&2
  exit 1
}

farm_info() {
  printf 'agent-farm hook (%s): %s\n' "${HOOK_NAME:-?}" "$*" >&2
}

farm_should_skip() {
  # Rollback / test-suite bypass. NOT a backdoor for agents: not mentioned
  # in any spawn prompt and stripped from agent env.
  [[ "${AGENT_FARM_SKIP_HOOKS:-0}" == "1" ]]
}
LIB_EOF

# ---------------------------------------------------------------------------
# commit-msg — reject AI authorship trailers.
# ---------------------------------------------------------------------------
cat > "$HOOKDIR/commit-msg" <<'CM_EOF'
#!/usr/bin/env bash
# commit-msg — block Claude/Anthropic co-author trailers (FARM-1.1).
set -euo pipefail
HOOK_NAME="commit-msg"
HOOK_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
source "$HOOK_DIR/_lib.sh"

farm_should_skip && exit 0

MSG_FILE="$1"
[[ -f "$MSG_FILE" ]] || farm_die "commit-msg file missing: $MSG_FILE"

# Strip git comment lines (#) for matching, but keep originals for echoing.
content=$(grep -vE '^[[:space:]]*#' "$MSG_FILE" || true)

# Forbidden patterns (case-insensitive):
#   - Co-Authored-By trailers crediting Claude / Anthropic / noreply addresses
#   - "Generated with Claude" / "by Anthropic" prose mentions
if printf '%s' "$content" | grep -iEq 'co-authored-by:.*(claude|anthropic|noreply)'; then
  bad=$(printf '%s' "$content" | grep -iE 'co-authored-by:.*(claude|anthropic|noreply)' | head -3)
  farm_info "found forbidden Co-Authored-By line:"
  printf '  %s\n' "$bad" >&2
  farm_die "amend the commit message; do not credit Claude/Anthropic/AI authorship"
fi

if printf '%s' "$content" | grep -iEq '(generated with claude|by anthropic|^[[:space:]]*claude[[:space:]]+(code|opus|sonnet|haiku))'; then
  bad=$(printf '%s' "$content" | grep -iE '(generated with claude|by anthropic|^[[:space:]]*claude[[:space:]]+(code|opus|sonnet|haiku))' | head -3)
  farm_info "found forbidden AI-attribution line:"
  printf '  %s\n' "$bad" >&2
  farm_die "remove the Claude/Anthropic credit; agents must not self-attribute"
fi

exit 0
CM_EOF

# ---------------------------------------------------------------------------
# pre-commit — block git stash artifacts, em-dashes in prose, poetry-lock drift.
# ---------------------------------------------------------------------------
cat > "$HOOKDIR/pre-commit" <<'PC_EOF'
#!/usr/bin/env bash
# pre-commit — block stash artefacts, em-dashes, poetry-lock drift (FARM-1.1).
set -euo pipefail
HOOK_NAME="pre-commit"
HOOK_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
source "$HOOK_DIR/_lib.sh"

farm_should_skip && exit 0

REPO_TOPLEVEL=$(git rev-parse --show-toplevel)
cd "$REPO_TOPLEVEL"

# --- 1. Stash artefacts -----------------------------------------------------
# Reject if a previous stash is still pending; common failure mode is
# "executor stashed, lost track, commit lands without rebased work".
if git stash list 2>/dev/null | grep -q .; then
  farm_info "git stash list is non-empty:"
  git stash list >&2
  farm_die "drop or pop stashes before committing (no-stash policy: use commit-on-WIP branch instead)"
fi

# Reject newly added `git stash` calls in executable scripts/agents (we do
# not police docs/markdown so it remains possible to document the ban).
# Carve-out: `tests/` (the no-stash hook itself is exercised from there,
# FARM-1.1 + FARM-1.11) and test fixtures must contain literal stash
# strings as inputs. The pre-push hook still rejects a pending stash at
# push time, so a test that actually leaves a stash behind cannot ship.
staged_scripts=$(git diff --cached --name-only --diff-filter=AM \
  -- 'scripts/*' 'agents/*' '*.sh' '*.py' \
     ':(exclude)tests/*' ':(exclude)*/tests/*' 2>/dev/null || true)
if [[ -n "$staged_scripts" ]]; then
  # shellcheck disable=SC2086
  if git diff --cached -U0 -- $staged_scripts 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | grep -qE '(^|[^[:alnum:]_-])git[[:space:]]+stash([[:space:]]|$)'; then
    farm_info "staged hunk introduces a 'git stash' invocation in an executable file"
    git diff --cached -U0 -- $staged_scripts | grep -E '^\+' | grep -vE '^\+\+\+' | grep -E '(^|[^[:alnum:]_-])git[[:space:]]+stash([[:space:]]|$)' | head -5 >&2
    farm_die "use 'git restore' + commit-on-WIP branch instead of 'git stash' (no-stash policy)"
  fi
fi

# --- 2. Em-dashes in publishable prose --------------------------------------
prose_paths=$(git diff --cached --name-only --diff-filter=AM -- 'thesis/*' 'docs/*' '*.md' 'README*' 'plans/*.md' 2>/dev/null || true)
if [[ -n "$prose_paths" ]]; then
  # shellcheck disable=SC2086
  added=$(git diff --cached -U0 -- $prose_paths 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' || true)
  if printf '%s' "$added" | grep -E '(--|—)' | grep -vE '^\+\+\+|^\+[[:space:]]*<!--' >/dev/null; then
    farm_info "em-dash (-- or U+2014) detected in staged prose:"
    printf '%s' "$added" | grep -nE '(--|—)' | grep -vE '<!--' | head -5 >&2
    farm_die "no em-dashes in publishable prose; use point/comma/parens"
  fi
fi

# --- 3. Poetry lock drift ---------------------------------------------------
if git diff --cached --name-only --diff-filter=AM | grep -qx 'pyproject.toml'; then
  if command -v poetry >/dev/null 2>&1; then
    # Newer poetry: `poetry check --lock`. Older: `poetry lock --check`.
    if poetry check --lock >/dev/null 2>&1; then
      :
    elif poetry lock --check >/dev/null 2>&1; then
      :
    else
      farm_info "pyproject.toml changed but poetry.lock is out of sync"
      poetry check --lock 2>&1 | head -5 >&2 || poetry lock --check 2>&1 | head -5 >&2 || true
      farm_die "run 'poetry lock' and stage poetry.lock before committing"
    fi
  else
    farm_info "poetry not on PATH; skipping lock-drift check (install poetry or stage poetry.lock manually)"
  fi
fi

exit 0
PC_EOF

# ---------------------------------------------------------------------------
# pre-push — block direct push to trunks + stash-nonempty push.
# ---------------------------------------------------------------------------
cat > "$HOOKDIR/pre-push" <<'PP_EOF'
#!/usr/bin/env bash
# pre-push — block direct push to protected trunks; block push with stashes (FARM-1.1).
set -euo pipefail
HOOK_NAME="pre-push"
HOOK_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
source "$HOOK_DIR/_lib.sh"

farm_should_skip && exit 0

# Reject if any pending stash exists at push time.
if git stash list 2>/dev/null | grep -q .; then
  farm_info "git stash list is non-empty at push time:"
  git stash list >&2
  farm_die "drop or pop stashes before pushing (no-stash policy)"
fi

# stdin: "<local_ref> <local_sha> <remote_ref> <remote_sha>" per ref.
# Reject if remote_ref targets a protected trunk.
PROTECTED='^refs/heads/(main|master|develop)$'
violations=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [[ -z "${remote_ref:-}" ]] && continue
  # Skip deletes (local_sha = zeros).
  if [[ "$remote_ref" =~ $PROTECTED ]]; then
    farm_info "direct push blocked: $remote_ref (open a PR instead)"
    violations=$((violations + 1))
  fi
done

if [[ "$violations" -gt 0 ]]; then
  farm_die "$violations protected-trunk push(es) rejected; use 'gh pr create' against the trunk"
fi

exit 0
PP_EOF

chmod +x "$HOOKDIR/commit-msg" "$HOOKDIR/pre-commit" "$HOOKDIR/pre-push"
# _lib.sh is sourced, not executed; chmod for hygiene only.
chmod +x "$HOOKDIR/_lib.sh"

# Point this worktree's hooksPath at the per-worktree dir.
git -C "$WT" config --worktree core.hooksPath "$HOOKDIR"

echo "install-hooks: installed commit-msg, pre-commit, pre-push into $HOOKDIR" >&2
echo "install-hooks: worktree core.hooksPath -> $HOOKDIR" >&2
