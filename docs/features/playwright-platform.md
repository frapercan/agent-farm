---
name: playwright-platform
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/playwright-platform.yaml
  - prompts/playwright-platform.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/playwright-platform.yaml'))"
---

# playwright-platform

Subagent that exercises the live platform UI via Playwright (PROTEA Next.js
app at :3000 or the configured tunnel). Haiku-class because the work is
mostly mechanical: drive a script, record results, summarise failures.

## Source coordinates

- `agents/playwright-platform.yaml` (model: haiku)
- `prompts/playwright-platform.md`

## State

working. Depends on deploy-keeper having the dev stack live; if the
tunnel is down, the agent escalates rather than retrying blindly.

## Smoke test

```bash
python3 -c "import yaml; print(yaml.safe_load(open('agents/playwright-platform.yaml'))['model'])"
```

## Runbook

- Spawn with `spawn_args.url` to target a specific page.
- Mobile + tablet via the existing PROTEA playwright config.

## Current owner

agent-farm conductor loop.
