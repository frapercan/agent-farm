---
name: worktree-remove-hook
section: "7-worktree"
state: working
owner: agent-farm conductor loop
source:
  - scripts/hooks/worktree-remove.sh
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/hooks/worktree-remove.sh
---

# worktree-remove hook

Runs before / around `git worktree remove`. Guards protected paths
(declared via `worktree.path` in agent yaml with `cleanup: none`) so
they are never removed by accident.

## Source coordinates

- `scripts/hooks/worktree-remove.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/hooks/worktree-remove.sh
```

## Runbook

- Called by `cleanup.sh`, `kill.sh`, `finalize-subagent.sh`.
- Protected paths are listed by iterating `agents/*.yaml` for
  `worktree.path` entries.

## Current owner

agent-farm conductor loop.
