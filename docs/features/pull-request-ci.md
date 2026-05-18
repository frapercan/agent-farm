---
name: pull-request-ci
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/pull_request.yml
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pull_request.yml'))"
---

# pull-request-ci

Main CI workflow for the agent-farm repo: ruff + mypy + pytest on every
PR to `main`. Required check on `main` per branch protection.

## Source coordinates

- `.github/workflows/pull_request.yml`

## State

working.

## Smoke test

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pull_request.yml'))"
# Local equivalent
poetry run ruff check . && poetry run mypy . && poetry run pytest -q
```

## Runbook

- Local CI MUST pass before push (memory: 5+ check failures from missed
  poetry-lock regen).

## Current owner

agent-farm conductor loop.
