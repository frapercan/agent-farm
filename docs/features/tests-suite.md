---
name: tests-suite
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - tests/
  - pyproject.toml
runbook: docs/features/README.md
smoke: python3 -m pytest tests -q
---

# tests-suite

The `tests/` directory in agent-farm root: ~30 test files covering the
plan parser, db layer, install-hooks, finalize, deploy-keeper, volume
watcher, restore drill, render check, etc. Wired into the
`pull_request.yml` workflow as a required check.

## Source coordinates

- `tests/`
- `pyproject.toml` (pytest config)

## State

working. Coverage of the three load-bearing parsers (plan_parser, db,
render) shipped via FARM-FEAT.9 + earlier slices; broader coverage is
incremental.

## Smoke test

```bash
python3 -m pytest tests -q
```

## Runbook

- Add a test next to every new script in `scripts/` or `scripts/lib/`.
- Bash tests are bash scripts ending in `.sh`; pytest tests end in `.py`.

## Current owner

agent-farm conductor loop.
