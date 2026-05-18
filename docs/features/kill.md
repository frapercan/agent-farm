---
name: kill
section: "4-lifecycle"
state: working
owner: agent-farm conductor loop
source:
  - scripts/kill.sh
runbook: docs/features/README.md
smoke: bash -n scripts/kill.sh
---

# kill

Cancels a task: kills the tmux window or supervisor pid, removes the
worktree (if ephemeral), updates the task status to `killed` in sqlite.

## Source coordinates

- `scripts/kill.sh`

## State

working.

## Smoke test

```bash
bash -n scripts/kill.sh
bash scripts/kill.sh 2>&1 | grep -qi usage && echo OK
```

## Runbook

- `bash scripts/kill.sh <task_id>`.
- Protected paths (worktree.cleanup: none with explicit path) are never
  removed.

## Current owner

agent-farm conductor loop.
