---
name: frontend-designer
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/frontend-designer.yaml
  - prompts/frontend-designer.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/frontend-designer.yaml'))"
---

# frontend-designer

Subagent that implements UX recommendations on the PROTEA Next.js app and
opens a PR. Opus-class because component composition + Tailwind + i18n
together exceed sonnet's reliability bar.

## Source coordinates

- `agents/frontend-designer.yaml` (model: opus)
- `prompts/frontend-designer.md`

## State

working. Reuses the existing component set (StatusBadge, EventTimeline,
FloatingJobsWidget, SystemStatusPill, CommandPalette, cytoscape-dagre).

## Smoke test

```bash
python3 -c "import yaml; print(yaml.safe_load(open('agents/frontend-designer.yaml'))['model'])"
```

## Runbook

- Consumes `ux-reviewer` output as spec.
- PR base = origin/develop on PROTEA.

## Current owner

agent-farm conductor loop.
