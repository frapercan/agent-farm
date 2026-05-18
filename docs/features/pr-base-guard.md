---
name: pr-base-guard
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/pr_base.py
  - scripts/lib/pr-base.sh
  - tests/test_pr_base.py
runbook: docs/features/README.md
smoke: python3 -m pytest tests/test_pr_base.py -q
---

# pr-base-guard

Helper that resolves the correct PR base branch per repo (PROTEA +
plugins = `develop`, lab + thesis + agent-farm = `main`) and patches PRs
that were accidentally opened against the wrong base. Memory
`feedback_pr_base_develop`: executors default `gh pr create` to main and
must be re-patched.

## Source coordinates

- `scripts/lib/pr_base.py`
- `scripts/lib/pr-base.sh`
- `tests/test_pr_base.py`

## State

working.

## Smoke test

```bash
python3 -m pytest tests/test_pr_base.py -q
bash -n scripts/lib/pr-base.sh
```

## Runbook

- Called from `prompts/executor.md` boilerplate and the janitor sweep.
- Patch wrong base: `gh api PATCH /repos/<owner>/<repo>/pulls/<n> -f base=develop`.

## Current owner

agent-farm conductor loop.
