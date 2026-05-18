---
name: embeddings-runner
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/embeddings-runner.yaml
  - prompts/embeddings-runner.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/embeddings-runner.yaml'))"
---

# embeddings-runner

One-shot headless agent that dispatches and polls PROTEA `/jobs` for
massive embedding batches. Haiku-class because the work is dispatch +
poll + summarise.

## Source coordinates

- `agents/embeddings-runner.yaml` (kind: headless, persistent: false)
- `prompts/embeddings-runner.md`

## State

working. Worktree creation is currently deferred to the agent itself; the
declarative path is FARM-FEAT.2 (pending).

## Smoke test

```bash
python3 -c "import yaml; d = yaml.safe_load(open('agents/embeddings-runner.yaml')); print(d['kind'], d['persistent'])"
```

## Runbook

- Spec carries the batch spec (`operation`, `payload`).
- Dispatches via `POST /jobs` on the PROTEA API; never ad-hoc curl.

## Current owner

agent-farm conductor loop.
