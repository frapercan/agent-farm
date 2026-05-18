---
name: repo-scope
section: "10-repos-scope"
state: working
owner: agent-farm conductor loop
source:
  - prompts/janitor.md
  - scripts/cleanup.sh
runbook: docs/features/README.md
smoke: test -d ~/Thesis2/repositories
---

# repo-scope

The 8 GitHub repos the farm operates on, plus the thesis tree:

- PROTEA (develop trunk)
- protea-method (LAFA inference layer)
- protea-backends (PLM embedding backends)
- protea-reranker-lab (offline LightGBM lab)
- protea-runners (experiment runner plugins)
- protea-sources (annotation source plugins)
- protea-contracts (ABCs / payloads / schema)
- cafaeval-protea (cafaeval fork; scope decided in ADR D33)
- thesis (LaTeX manuscript)

`cleanup.sh` iterates this set when GC-ing orphan worktrees; `janitor.md`
lists the same set as the default sweep scope; `apply-branch-protection.sh`
applies the same set's branch protection rules.

## Source coordinates

- `prompts/janitor.md` (authoritative scope list for sweeps)
- `scripts/cleanup.sh` (worktree scan)
- `scripts/apply-branch-protection.sh` (branch protection)
- `docs/decisions/D33-cafaeval-protea-scope.md` (cafaeval inclusion
  decision)

## State

working.

## Smoke test

```bash
test -d ~/Thesis2/repositories && ls ~/Thesis2/repositories | wc -l
```

## Runbook

- Add a repo: clone into `~/Thesis2/repositories/`, edit `janitor.md`
  scope list, run `apply-branch-protection.sh`, add to `cleanup.sh` repo
  list.

## Current owner

agent-farm conductor loop.
