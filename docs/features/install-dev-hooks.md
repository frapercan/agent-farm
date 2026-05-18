---
name: install-dev-hooks
section: "7-worktree"
state: working
owner: agent-farm conductor loop
source:
  - scripts/install-dev-hooks.sh
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/install-dev-hooks.sh
---

# install-dev-hooks

Installs the worktree-hook bundle into the developer's main checkout
(`~/Thesis2/repositories/PROTEA/`) so that direct commits from the
developer's IDE also get the coauthor + stash + branch protection guards.
Companion to `install-hooks.sh` (worktree-scoped). Slice FARM-1.4.

## Source coordinates

- `scripts/install-dev-hooks.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/install-dev-hooks.sh
```

## Runbook

- One-shot per workstation.
- Re-run on each clone of a new repo into `~/Thesis2/repositories/`.

## Current owner

agent-farm conductor loop.
