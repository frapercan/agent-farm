---
name: decisions-adr
section: "10-repos-scope"
state: working
owner: agent-farm conductor loop
source:
  - docs/decisions/
runbook: docs/features/README.md
smoke: ls docs/decisions/
---

# decisions-adr

Architecture Decision Records (ADRs) for choices that span multiple
slices. Each ADR is a markdown file in `docs/decisions/D<NN>-*.md` with
a status block (proposed / accepted / superseded) and a rationale that
cites the relevant memories and slices.

## Source coordinates

- `docs/decisions/D31-per-action-worktree.md`
- `docs/decisions/D32-lab-runner-vs-bioinfo-quick.md`
- `docs/decisions/D33-cafaeval-protea-scope.md`

## State

working. ADR template is the existing pair; new ADRs follow the same shape.

## Smoke test

```bash
ls docs/decisions/
```

## Runbook

- New ADR: `cp docs/decisions/D32-*.md docs/decisions/D34-<topic>.md`
  and edit.
- ADRs are immutable once accepted; supersede with a new ADR.

## Current owner

agent-farm conductor loop.
