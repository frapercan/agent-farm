---
name: conductor
section: "2-conductor"
state: working
owner: agent-farm conductor loop
source:
  - prompts/conductor.md
  - prompts/bootstrap-autowork.md
  - scripts/launch-conductor.sh
runbook: docs/features/README.md
smoke: bash -n scripts/launch-conductor.sh
---

# conductor

Operator-facing meta-agent that drives the farm in natural language.
Reads `prompts/conductor.md` + `prompts/bootstrap-autowork.md` at boot,
then spawns subagents (executor, janitor, shepherd, etc.) and headless
agents (deploy-keeper, embeddings-runner) on demand.

## Source coordinates

- `prompts/conductor.md` (~600-line operator prompt)
- `prompts/bootstrap-autowork.md` (bootstrap loop: read state, pick next)
- `scripts/launch-conductor.sh` (tmux boot)

## State

working. Memory `feedback_autonomous_no_stop` is the conductor's hard
policy: never idle the pipeline; on every Agent completion immediately
spawn the next slice without asking.

## Smoke test

```bash
bash -n scripts/launch-conductor.sh
python3 -c "import os; assert os.path.getsize('prompts/conductor.md') > 1000"
```

## Runbook

- Launch: `cd ~/Thesis2 && bash agent-farm/scripts/launch-conductor.sh`.
- Attach: `tmux attach -t agent-farm`.
- Autoyes: `AGENT_FARM_AUTOYES=accept` to prompt on rm/push/etc.

## Current owner

agent-farm conductor loop.
