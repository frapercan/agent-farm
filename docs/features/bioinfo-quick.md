---
name: bioinfo-quick
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/bioinfo-quick.yaml
  - prompts/bioinfo-quick.md
runbook: docs/decisions/D32-lab-runner-vs-bioinfo-quick.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/bioinfo-quick.yaml'))"
---

# bioinfo-quick

Subagent that picks and runs the next experiment in the reranker lab
(`protea-reranker-lab`). Single agent for the lab loop; chosen over a
separate `lab-runner` per ADR D32 (memory
`feedback_bioinfo_quick_wrong_base`).

## Source coordinates

- `agents/bioinfo-quick.yaml` (worktree base: origin/develop on lab repo)
- `prompts/bioinfo-quick.md`
- `docs/decisions/D32-lab-runner-vs-bioinfo-quick.md`

## State

working. Operational caveat: `spawn-subagent.sh` defaults to PROTEA; the
conductor must override `worktree.repo` and reset to origin/develop on the
lab repo before sending the prompt.

## Smoke test

```bash
python3 -c "import yaml; d = yaml.safe_load(open('agents/bioinfo-quick.yaml')); print(d['worktree']['repo'])"
```

## Runbook

- Lab plan loop = `plans/bioinfo-quick/PLAN.md`.
- Champion bookkeeping: see lab repo `experiments/_catalog/transversal.yaml`.

## Current owner

agent-farm conductor loop.
