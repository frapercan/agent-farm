# Agent-Farm Hook Bundle (FARM-1.1)

Per-worktree git hooks enforcing agent-farm policies: no AI authorship,
no em-dashes in publishable prose, no `git stash`, no direct push to
trunks, and Poetry lockfile consistency.

## Hook Enforcement Scope

Each worktree installs a bundle of four hooks via `scripts/lib/install-hooks.sh`:

1. **commit-msg** — blocks Claude/Anthropic co-author trailers and prose mentions
2. **pre-commit** — blocks stash artifacts, em-dashes in publishable prose, poetry-lock drift
3. **pre-push** — blocks direct push to `refs/heads/{main,master,develop}`
4. **_lib.sh** — shared helpers sourced by all hooks

Hooks are installed per-worktree to `<git-common-dir>/worktrees/<name>/farm-hooks/`
and addressed via `core.hooksPath` (worktree-scoped config).

## Em-Dash Carve-Out

The pre-commit em-dash check applies to **publishable prose** only:
- Thesis chapters (`thesis/*`)
- Documentation (`docs/*`, `*.md`, `README*`)
- NOT: internal plan catalogs (`plans/*.md`)

### Why Plans Are Excluded

Internal plan catalog files (`plans/<loop>/PLAN.md` and `plans/PLAN.md`)
use em-dashes in slice titles by convention (e.g.,
`### FARM-1.8 — Untrack thesis.pdf and serve via deploy-keeper`).
These are not publishable prose; they are machine-readable catalogs
consumed by render.py and the orchestration layer. Per CLAUDE.md, the
em-dash rule applies only to prose destined for publication (papers,
thesis chapters, ADRs, READMEs).

### Pathspec Exclusion

The pre-commit hook filters out `plans/` from the prose path list:

```bash
prose_paths=$(git diff --cached --name-only --diff-filter=AM -- \
  'thesis/*' 'docs/*' '*.md' 'README*' 2>/dev/null || true)
```

Note: `plans/*.md` is deliberately absent from the pathspec.

## Markdown Documentation Carve-Out

The pre-commit hook rejects new `git stash` invocations added to
executable scripts (`scripts/*`, `agents/*`, `*.sh`, `*.py`), but
does not police markdown or docs. This allows documenting the
no-stash policy in prose without blocking the commit.

## Bypass (Testing and Rollback)

Set `AGENT_FARM_SKIP_HOOKS=1` to disable all hooks:

```bash
AGENT_FARM_SKIP_HOOKS=1 git commit -m "msg"
```

This env var is intentionally NOT exposed to agent prompts and must
not be used by agents in production. It is for developer rollback and
test-suite use only.

## Installation

Hooks are installed lazily on first use:

```bash
bash scripts/lib/install-hooks.sh <worktree_path>
```

Re-running is idempotent and updates the hook templates. Uninstall:

```bash
bash scripts/lib/install-hooks.sh --uninstall <worktree_path>
```

## Related

- `CLAUDE.md` — root project constraints (em-dash rule, no-stash policy, no AI authorship)
- FARM-1.1 — hook bundle delivery
- FARM-2.7 — plans/ carve-out follow-up (unblocks regeneration of plans/PLAN.md)
