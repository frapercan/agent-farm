---
name: shepherd
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/shepherd.yaml
  - prompts/shepherd.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/shepherd.yaml'))"
---

# shepherd

Subagent that scans the live farm state (sqlite tasks, recent
heartbeats, plan progress) and recommends the next priorities for the
conductor. Read-only by contract.

## Source coordinates

- `agents/shepherd.yaml` (model: sonnet, kind: subagent)
- `prompts/shepherd.md`

## State

working. Used between conductor session boots when the operator wants a
sanity read on what to spawn next.

## Smoke test

```bash
python3 -c "import yaml; print(yaml.safe_load(open('agents/shepherd.yaml'))['kind'])"
bash scripts/plan-progress.sh --next
```

## Runbook

- Run via the conductor Agent tool: "shepherd, recommend the next slice".
- Output is advisory; the conductor still chooses.

## Current owner

agent-farm conductor loop.
