---
name: ci
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/ci.yml
runbook: tests/test_db.py
smoke: python3 -m pytest tests/test_db.py tests/test_render.py tests/test_plan_parser.py -q
---

# ci

Pull-request gate that runs the agent-farm pytest suite plus a scoped
ruff check on every PR and on every push to `main`. Replaces the
ad-hoc "run pytest locally before push" rule with a server-side
backstop: a regression in `scripts/lib/db.py`, `plans/render.py`, or
`scripts/lib/plan_parser.py` now fails the PR before merge.

Shipped FARM-FEAT.9 to bootstrap `tests/` as a first-class artefact.

## Source coordinates

- `.github/workflows/ci.yml`

## State

working. Two jobs:

- `pytest`: installs `pyyaml`, `pytest`, `pytest-cov` and runs the full
  suite (`python -m pytest -q`).
- `ruff`: lints the three files this slice introduced/owns
  (`tests/test_db.py`, `tests/test_render.py`,
  `tests/test_plan_parser.py`). Pre-existing offences elsewhere are
  out of scope; a separate slice can flip the gate to repo-wide once
  the backlog is paid down.

mypy is not wired in CI because it is not installed in the developer's
local environment (FARM-FEAT.2 finding). A future slice can turn it on
once mypy lands on PATH.

## Smoke test

```bash
python3 -m pytest tests/test_db.py tests/test_render.py tests/test_plan_parser.py -q
```

## Runbook

- Adjust scope: edit `ruff check` paths in `.github/workflows/ci.yml`.
- Add deps: extend the `pip install` line in the `pytest` job.
- The workflow is a candidate for a required status check on `main`
  once it has settled.

## Current owner

agent-farm conductor loop.
