---
name: spawn-subagent
section: "3-spawning"
state: partial
owner: agent-farm conductor loop
source:
  - scripts/spawn-subagent.sh
runbook: docs/features/README.md
smoke: bash -n scripts/spawn-subagent.sh
---

# spawn-subagent

Helper called by the conductor (through the Agent tool) to prepare a
subagent: create the worktree, install hooks, register the task in
sqlite, hand the worktree path to the LLM via the composed prompt.

## Source coordinates

- `scripts/spawn-subagent.sh`
- `scripts/hooks/worktree-create.sh`
- `scripts/lib/install-hooks.sh`

## State

partial. Known issue (memory `feedback_spawn_subagent_wrong_repo`): the
script always builds the worktree off PROTEA even for lab / agent-farm /
thesis slices. Conductor injects a secondary-worktree instruction in the
prompt as a workaround. FARM-FEAT.2 / FARM-FEAT.7 schedule the
structural fix.

## Smoke test

```bash
bash -n scripts/spawn-subagent.sh
# Test the hook installer it depends on
bash tests/test_install_hooks.py 2>&1 | tail -5
```

## Runbook

- Called from the conductor: "spawn executor with slice X".
- For non-PROTEA slices, override repo in the conductor's prompt to the
  agent.

## Current owner

agent-farm conductor loop.
