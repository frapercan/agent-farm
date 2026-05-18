---
name: cost-report
section: "9-schema-state"
state: working
owner: agent-farm conductor loop
source:
  - scripts/cost-report.sh
  - scripts/lib/cost_report.py
  - scripts/lib/parse_claude_cost.py
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

## State

working. Tested via `tests/test_cost_report.py`,
`tests/test_parse_claude_cost.py`. The advisory cost_budget enforcement
slice is FARM-FEAT.8.

## Smoke test

```bash
bash -n scripts/cost-report.sh
python3 -m pytest tests/test_cost_report.py tests/test_parse_claude_cost.py -q
```

## Runbook

- `bash scripts/cost-report.sh` → daily summary.
- `bash scripts/cost-report.sh --agent executor` → per-agent rollup.
- `docs/token-savings.md` describes the 5 cost levers.

## Current owner

agent-farm conductor loop.
