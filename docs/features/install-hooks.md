---
name: install-hooks
section: "7-worktree"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/install-hooks.sh
  - scripts/lib/README-hooks.md
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/lib/install-hooks.sh
---

# install-hooks

Installs the four git hooks (commit-msg, pre-commit, pre-push, +
optional prepare-commit-msg) into a worktree's `core.hooksPath`. Sets the
worktree-local `core.hooksPath` so the bundle survives `git worktree
remove + re-add`.

## Source coordinates

- `scripts/lib/install-hooks.sh`
- `scripts/lib/README-hooks.md` (authoritative docs for hooks)

## State

working. Shipped FARM-1.1 (PR #19). Known bypass: agents that commit via
`gh api` or `git commit-tree` skip these; the server-side fallback is
FARM-1.1a `coauthor-guard.yml`.

## Smoke test

```bash
bash -n scripts/lib/install-hooks.sh
python3 -m pytest tests/test_install_hooks.py -q
```

## Runbook

- `scripts/lib/README-hooks.md` describes each hook's rejection rules,
  the escape hatch, and how the hooks integrate with `spawn-subagent.sh`
  + `worktree-create.sh`.

## Current owner

agent-farm conductor loop.
