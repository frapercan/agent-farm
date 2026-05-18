---
name: memory-prompt-drift
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - scripts/memory-prompt-drift.py
  - tests/test_memory_prompt_drift.py
runbook: docs/features/README.md
smoke: python3 -m pytest tests/test_memory_prompt_drift.py -q
---

# memory-prompt-drift

Drift linter: every `memory:` reference in `prompts/*.md` must point to
a real memory file under `~/.claude/projects/-home-frapercan-Thesis2/memory/`.
Catches the case where a prompt cites a memory that has since been
renamed or deleted.

## Source coordinates

- `scripts/memory-prompt-drift.py`
- `tests/test_memory_prompt_drift.py`

## State

working.

## Smoke test

```bash
python3 scripts/memory-prompt-drift.py --help 2>&1 | head -5
python3 -m pytest tests/test_memory_prompt_drift.py -q
```

## Runbook

- Run before committing prompt edits.
- Failure recipe: rename the citation OR re-create the missing memory file.

## Current owner

agent-farm conductor loop.
