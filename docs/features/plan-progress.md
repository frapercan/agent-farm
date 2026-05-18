---
name: plan-progress
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/plan-progress.sh
  - scripts/lib/plan_parser.py
runbook: docs/features/plan-system.md
smoke: bash scripts/plan-progress.sh --next
---

# plan-progress

CLI that walks every `plans/<loop>/PLAN.md`, parses the yaml frontmatter
of each slice, joins with sqlite `spawn_args.slice` history, and reports
which slices are pickable / in flight / blocked / done. `--next` picks
the highest-priority pickable slice across all loops.

## Source coordinates

- `scripts/plan-progress.sh`
- `scripts/lib/plan_parser.py`

## State

working.

## Smoke test

```bash
bash scripts/plan-progress.sh --help 2>&1 | head -5
bash scripts/plan-progress.sh --next
python3 -m pytest tests/test_plan_parser.py -q
```

## Runbook

- `bash scripts/plan-progress.sh` → all loops, all slices.
- `bash scripts/plan-progress.sh --phase F-FEAT` → one phase.
- `bash scripts/plan-progress.sh --next` → next pickable slice.

## Current owner

agent-farm conductor loop.
