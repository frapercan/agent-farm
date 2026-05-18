---
name: plans-render-check
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/plans-render-check.yml
  - plans/render.py
runbook: docs/features/plan-system.md
smoke: python3 plans/render.py --check
---

# plans-render-check

CI gate that fails any PR which edits `plans/<loop>/PLAN.md` without
re-running `python3 plans/render.py`. Keeps the rendered plan index in
sync with the source markdown.

## Source coordinates

- `.github/workflows/plans-render-check.yml`
- `plans/render.py`
- `tests/test_render_check.py`

## State

working.

## Smoke test

```bash
python3 plans/render.py --check
python3 -m pytest tests/test_render_check.py -q
```

## Runbook

- After editing any PLAN.md: `python3 plans/render.py` then commit the
  rendered diff.

## Current owner

agent-farm conductor loop.
