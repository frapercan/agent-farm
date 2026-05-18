---
name: plan-system
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - plans/render.py
  - plans/README.md
  - scripts/lib/plan_parser.py
  - scripts/plan-progress.sh
runbook: docs/features/README.md
smoke: python3 plans/render.py --check
---

# plan-system

Plan store + parser + progress reporter. Source of truth lives in
`plans/<loop>/PLAN.md` (one Markdown file per loop, each `### <title>`
slice carrying a yaml frontmatter block with id/phase/loop/status/deps).
`plans/render.py` validates + renders the index; `plan-progress.sh`
joins it with the sqlite task history.

## Source coordinates

- `plans/render.py`
- `plans/README.md`
- `scripts/lib/plan_parser.py`
- `scripts/plan-progress.sh`
- `tests/test_plan_parser.py`
- `tests/test_render_check.py`

## State

working.

## Smoke test

```bash
python3 plans/render.py --check
python3 -m pytest tests/test_plan_parser.py tests/test_render_check.py -q
bash scripts/plan-progress.sh --next
```

## Runbook

- Edit a slice: bump `status:` in the yaml block, then
  `python3 plans/render.py`.
- Add a new loop: `mkdir plans/<loop>/`, write `PLAN.md`, render picks it
  up automatically (per `render.py:25-28`).

## Current owner

agent-farm conductor loop.
