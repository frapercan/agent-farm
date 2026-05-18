---
name: redcheck-systemic
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/redcheck-systemic.py
  - scripts/janitor-systemic-check.sh
  - tests/test_redcheck_systemic.py
runbook: docs/features/janitor.md
smoke: python3 -m pytest tests/test_redcheck_systemic.py -q
---

# redcheck-systemic

Janitor helper that detects when the SAME required check is red on >=3
unrelated PRs. Memory `feedback_janitor_systemic_redcheck_carveout`
makes this the official escalation trigger: the janitor reports back
instead of admin-overriding.

## Source coordinates

- `scripts/lib/redcheck-systemic.py`
- `scripts/janitor-systemic-check.sh`
- `tests/test_redcheck_systemic.py`

## State

working.

## Smoke test

```bash
python3 -m pytest tests/test_redcheck_systemic.py -q
bash -n scripts/janitor-systemic-check.sh
```

## Runbook

- Run from the janitor prompt at sweep start.
- On systemic red → open the fix PR; the systemic red itself stays red
  until the fix lands.

## Current owner

agent-farm conductor loop.
