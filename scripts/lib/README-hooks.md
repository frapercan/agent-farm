# Worktree git-hooks bundle (FARM-1.1)

This bundle installs four enforcement hooks into every ephemeral
agent worktree the farm creates. The goal is to convert recurring
"prompt rule without enforcement" failures into hard stops at the
git client layer, the only layer an agent cannot bypass without an
explicit env-var override.

## Hooks

The installer is `scripts/lib/install-hooks.sh`. It drops four files
into a per-worktree directory (`<git-common-dir>/farm-hooks/`) and
points the worktree's `core.hooksPath` at it via worktree-scoped
git config. The shared `.git/hooks` directory is NOT touched, so the
developer's main checkout stays clean.

### `commit-msg`

Rejects commit messages that credit Claude / Anthropic / AI authorship:

1. Co-Authored-By trailers matching `co-authored-by:.*(claude|anthropic|noreply)` (case-insensitive).
2. Prose lines matching `generated with claude`, `by anthropic`, or bare leading `Claude (Code|Opus|Sonnet|Haiku)` attribution.

Memory pointer: `feedback_claude_coauthor_slipthrough`,
`feedback_farm_1_1_hook_bypass`.

### `pre-commit`

Three independent checks; any failure rejects the commit:

1. **Pending stash artefacts**. Refuses to commit while `git stash list`
   is non-empty (the canonical "executor stashed work and lost it" trap).
2. **New `git stash` invocations** added to staged executable files
   under `scripts/`, `agents/`, `*.sh`, `*.py`. Documentation mentions
   in markdown are still allowed so the no-stash policy can be written
   down.
3. **Em-dash in publishable prose**. Catches `--` and U+2014 in staged
   diffs under `thesis/`, `docs/`, `plans/*.md`, `README*`, `*.md`.
   Source code is exempt (argparse `--flag` etc).
4. **Poetry lock drift**. When `pyproject.toml` is staged the hook runs
   `poetry check --lock` (or the older `poetry lock --check`) and
   refuses if the lockfile is out of sync.

Memory pointers: `feedback_git_stash_6x`,
`feedback_executor_git_stash_pattern`, `feedback_poetry_lock_regenerate`.

### `pre-push`

Two reject paths:

1. **Direct push to protected trunks**. Refuses pushes whose remote ref
   matches `refs/heads/(main|master|develop)`, on any remote. Open a PR
   instead.
2. **Stash non-empty at push time**. Same rationale as the pre-commit
   stash check, second line of defence if the commit slipped through.

Memory pointers: `feedback_janitor_direct_push_agentfarm`,
`project_plugin_push_direct_main_incident`.

### `_lib.sh`

Sourced by every hook. Provides `farm_die`, `farm_info`, and
`farm_should_skip`. Not directly executable.

## Escape hatch

`AGENT_FARM_SKIP_HOOKS=1` makes every hook exit 0 immediately. This
exists for rollback drills and the test suite. It is intentionally
NOT mentioned in any spawn prompt and is stripped from the agent
environment. If you find yourself reaching for it as an agent, stop
and fix the underlying issue instead.

## Where hooks fire

Two integration points install the bundle automatically:

1. `scripts/spawn-subagent.sh` (around line 89) calls the installer
   right after `git worktree add` for kind=subagent runs.
2. `scripts/hooks/worktree-create.sh` (around line 44) does the same
   for Claude Code's WorktreeCreate hook (the conductor path).

Both call `bash scripts/lib/install-hooks.sh <worktree_path>`. Install
failures are logged to `/tmp/install-hooks.log` and emitted as a
heartbeat or stderr warning, never as a fatal error. The hooks are a
backstop, not a hard gate on worktree creation.

## Not enforced here

These belong to other slices:

- Server-side coauthor check (FARM-1.1a, shipped). GitHub Actions on
  every PR. Backstop for the case where a hook is uninstalled or the
  commit comes via `gh api` / `git commit-tree`.
- Branch protection on main/develop (FARM-1.2, requires_human). The
  authoritative server-side enforcement.
- Hook coverage for the developer's main PROTEA clone (FARM-1.4).
  This bundle is worktree-only by design.
- Force-push and `--no-verify` blocks. Force-push is server-side
  branch protection. `--no-verify` bypasses every client hook by
  design, so server-side CI is the answer.

## Tests

`tests/test_install_hooks.py`. 27 cases covering each rejection path,
both rejection and accept paths for commit-msg / pre-commit / pre-push,
idempotency, uninstall, and the `AGENT_FARM_SKIP_HOOKS=1` escape hatch.
Run with:

```
python3 -m pytest tests/test_install_hooks.py -xvs
```

## For agent prompts

Executors and janitors do not need to read or call the installer.
The hooks fire automatically. If a hook rejects a commit or push,
the stderr message names the policy and points at the relevant
memory file. The fix is always to amend the commit message, drop
the stash, or open a PR instead of pushing to a trunk. Never reach
for `AGENT_FARM_SKIP_HOOKS=1` from inside an agent loop.
