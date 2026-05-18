---
name: cost-report
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/cost-report.sh
  - scripts/lib/cost_report.py
  - scripts/lib/parse_claude_cost.py
  - scripts/lib/budget_check.py
runbook: docs/token-savings.md
smoke: bash -n scripts/cost-report.sh
---

# cost-report

Aggregates per-task Claude metrics (input tokens, output tokens, USD)
into a daily and per-agent rollup. Backed by
`tasks.metrics_json`, populated by `finalize-subagent.sh` via
`parse_claude_cost.py`.

## Source coordinates

- `scripts/cost-report.sh` (CLI wrapper)
- `scripts/lib/cost_report.py` (aggregation)
- `scripts/lib/parse_claude_cost.py` (parse `claude -p` stderr)
- `scripts/lib/budget_check.py` (FARM-FEAT.8 advisory enforcement)

## State

working. Tested via `tests/test_cost_report.py`,
`tests/test_parse_claude_cost.py`, `tests/test_budget_check.py`.
FARM-FEAT.8 wires the per-agent advisory cap (`cost_budget.max_usd_per_day`)
into finalize, spawn, and the conductor boot-report as a warn-level
signal; the caps remain advisory (no hard gate).

## Smoke test

```bash
bash -n scripts/cost-report.sh
python3 -m pytest tests/test_cost_report.py tests/test_parse_claude_cost.py tests/test_budget_check.py -q
```

## Runbook

- `bash scripts/cost-report.sh` → daily summary.
- `bash scripts/cost-report.sh --agent executor` → per-agent rollup.
- `python3 scripts/lib/budget_check.py overages --only-alerts` →
  per-agent advisory cap state; lines like `OVER  executor  $13.50 /
  $12.00  (3 task(s) in last 24h)` for actionable rows.
- `docs/token-savings.md` describes the 5 cost levers.

## Current owner

agent-farm conductor loop.
