---
name: doc-writer
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/doc-writer.yaml
  - prompts/doc-writer.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/doc-writer.yaml'))"
---

# doc-writer

Subagent that syncs prose docs with source code: READMEs, ADRs, runbooks,
slash-command text. Sonnet-class so it can read context broadly without
the opus cost.

## Source coordinates

- `agents/doc-writer.yaml`
- `prompts/doc-writer.md`

## State

working. Used for ADRs (`docs/decisions/D3X-*.md`), runbooks
(`docs/runbook-*.md`), and the slash-command markdown set.

## Smoke test

```bash
python3 -c "import yaml; print(yaml.safe_load(open('agents/doc-writer.yaml'))['name'])"
```

## Runbook

- Spawn via Agent tool; spec usually carries `target` (file or dir to write).
- Hard rule: no em-dashes in publishable prose (CLAUDE.md).

## Current owner

agent-farm conductor loop.
