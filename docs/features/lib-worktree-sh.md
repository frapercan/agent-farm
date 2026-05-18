---
name: lib-worktree.sh
section: "7-worktree"
state: partial
owner: agent-farm conductor loop
source:
  - scripts/lib/worktree.sh
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/lib/worktree.sh
---

# lib/worktree.sh

Shared bash helpers for worktree lifecycle: `wt_create`, `wt_remove`,
`wt_changed`, `wt_cleanup_orphans`. Designed to replace the duplicated
worktree-add and worktree-remove logic scattered across `spawn-subagent.sh`,
`cleanup.sh`, `kill.sh`, `finalize-subagent.sh`.

## Source coordinates

- `scripts/lib/worktree.sh`

## State

partial: defined but not yet adopted by the callers. FARM-FEAT.7 is the
adoption slice.

## Smoke test

```bash
bash -n scripts/lib/worktree.sh
# Source-and-list functions
( source scripts/lib/worktree.sh && declare -F | grep wt_ )
```

## Runbook

- Once FARM-FEAT.7 ships, callers `source` this and use the helpers.
- Tests live under `tests/test_worktree.sh` (placeholder until FARM-FEAT.7).

## Current owner

agent-farm conductor loop.
