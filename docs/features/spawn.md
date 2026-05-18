---
name: spawn
section: "3-spawning"
state: working
owner: agent-farm conductor loop
source:
  - scripts/spawn.sh
runbook: docs/features/README.md
smoke: bash -n scripts/spawn.sh
---

# spawn

Spawns a headless agent in the farm tmux session. Reads
`agents/<name>.yaml`; for `kind=headless persistent=true` it delegates to
`scripts/services/<name>-supervisor.sh`. Prints the task_id on stdout.

## Source coordinates

- `scripts/spawn.sh`
- `scripts/lib/common.sh`
- `scripts/lib/yaml_parse.sh`

## State

working. The declarative-worktree-from-yaml path for headless one-shots
is FARM-FEAT.2 (pending).

## Smoke test

```bash
bash -n scripts/spawn.sh
# Argument validation
bash scripts/spawn.sh 2>&1 | grep -q usage && echo OK
```

## Runbook

- `bash scripts/spawn.sh deploy-keeper` (persistent).
- `bash scripts/spawn.sh embeddings-runner '{"operation":"embed_batch"}'` (one-shot).

## Current owner

agent-farm conductor loop.
