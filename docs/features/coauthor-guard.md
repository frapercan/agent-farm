---
name: coauthor-guard
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/coauthor-guard.yml
runbook: scripts/lib/README-hooks.md
smoke: yamllint .github/workflows/coauthor-guard.yml || python3 -c "import yaml; yaml.safe_load(open('.github/workflows/coauthor-guard.yml'))"
---

# coauthor-guard

Server-side GitHub Actions workflow that fails any PR whose commit
messages contain `co-authored-by:.*claude|anthropic|noreply`. Backstop
for the worktree-local `commit-msg` hook, which an agent can bypass via
`gh api`. Shipped FARM-1.1a after the FARM-1.1 hook-bypass incident
(memory `feedback_farm_1_1_hook_bypass`).

## Source coordinates

- `.github/workflows/coauthor-guard.yml`

## State

working. Replicated in each of the 8 watched repos via FARM-1.1a.

## Smoke test

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/coauthor-guard.yml'))"
```

## Runbook

- Required check on every protected branch (main, develop).
- Failure recipe: amend the offending commit to drop the trailer; push.

## Current owner

agent-farm conductor loop.
