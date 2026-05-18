---
name: finalize-subagent
section: "3-spawning"
state: working
owner: agent-farm conductor loop
source:
  - scripts/finalize-subagent.sh
runbook: docs/features/README.md
smoke: bash -n scripts/finalize-subagent.sh
---

# finalize-subagent

Runs at the end of a subagent task: parses Claude cost metrics, records
them in `tasks.metrics_json`, removes the ephemeral worktree (unless
`cleanup: none`), updates task status. Closes the lifecycle.

## Source coordinates

- `scripts/finalize-subagent.sh`
- `scripts/lib/parse_claude_cost.py`

## State

working. Test coverage in `tests/test_finalize_metrics.py`,
`tests/test_finalize_lookup_perf.py`, `tests/test_finalize_uses_column.py`.

## Smoke test

```bash
bash -n scripts/finalize-subagent.sh
python3 -m pytest tests/test_finalize_metrics.py -q
```

## Runbook

- Called by `spawn-subagent.sh` on Agent tool completion.
- The `worktree_owner_repo` column shortcut (FARM-2.3) avoids the
  O(repos * worktrees) scan on teardown.

## Current owner

agent-farm conductor loop.
