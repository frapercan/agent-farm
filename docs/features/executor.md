---
name: executor
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/executor.yaml
  - prompts/executor.md
runbook: docs/features/README.md
smoke: bash scripts/spawn-subagent.sh executor '{"slice":"FARM-X","phase":"F-X","notes":"smoke"}' --dry-run
---

# executor

Subagent that implements one master-plan slice end to end: branches off the
correct base, edits code, runs local CI, opens a PR. Spawned by the
conductor via the Agent tool, never as a headless process.

## Source coordinates

- `agents/executor.yaml` (model: opus, permissions: acceptEdits)
- `prompts/executor.md` (system prompt, ~400 lines)
- `scripts/spawn-subagent.sh` (worktree + sqlite registration)

## State

working. Daily driver across the F-FARM and F-FEAT phases. The slice
contract (must include `slice`, `phase` in spawn_args) is enforced by
`scripts/plan-progress.sh`.

## Smoke test

```bash
# 1. Spawn template check (does not call the LLM)
bash ~/Thesis2/agent-farm/scripts/spawn-subagent.sh executor \
  '{"slice":"SMOKE","phase":"SMOKE","notes":"dry run"}' --dry-run

# 2. Verify yaml parse
python3 -c "import yaml; print(yaml.safe_load(open('agents/executor.yaml'))['name'])"
```

## Runbook

- One-PR-per-slice convention. See `prompts/executor.md` for the contract.
- Reads `~/Thesis2/CLAUDE.md` hard constraints on every spawn.
- Failures escalate to `janitor` (cleanup) or back to the conductor.

## Current owner

agent-farm conductor loop (Francisco). No co-owner: this is the load-bearing
implementation agent for the FREEZE pass.
