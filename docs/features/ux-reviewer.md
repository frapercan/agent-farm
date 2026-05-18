---
name: ux-reviewer
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/ux-reviewer.yaml
  - prompts/ux-reviewer.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/ux-reviewer.yaml'))"
---

# ux-reviewer

Subagent that audits the platform UX and produces a prioritised findings
list. Read-only; pairs with `frontend-designer` which implements the
recommendations.

## Source coordinates

- `agents/ux-reviewer.yaml`
- `prompts/ux-reviewer.md`

## State

working.

## Smoke test

```bash
python3 -c "import yaml; print(yaml.safe_load(open('agents/ux-reviewer.yaml'))['name'])"
```

## Runbook

- Spawn with `spawn_args.scope` (page, flow, or whole app).
- Output feeds directly into a `frontend-designer` slice spec.

## Current owner

agent-farm conductor loop.
