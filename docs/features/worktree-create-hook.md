---
name: worktree-create-hook
section: "7-worktree"
state: working
owner: agent-farm conductor loop
source:
  - scripts/hooks/worktree-create.sh
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/hooks/worktree-create.sh
---

# worktree-create hook

Runs after `git worktree add` from `spawn-subagent.sh` and the manual
`hooks/worktree-create.sh` path. Installs git hooks (commit-msg +
pre-commit + pre-push) into the new worktree via
`scripts/lib/install-hooks.sh`.

## Source coordinates

- `scripts/hooks/worktree-create.sh`
- `scripts/lib/install-hooks.sh`

## State

working. Companion server-side guard is `coauthor-guard` workflow
(FARM-1.1a).

## Smoke test

```bash
bash -n scripts/hooks/worktree-create.sh
python3 -m pytest tests/test_install_hooks.py -q
```

## Runbook

- `scripts/lib/README-hooks.md` documents the 4 hooks, escape hatch,
  and integration points (FARM-1.1).

## Current owner

agent-farm conductor loop.
