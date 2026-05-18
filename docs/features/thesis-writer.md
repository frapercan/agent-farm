---
name: thesis-writer
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/thesis-writer.yaml
  - prompts/thesis-writer.md
runbook: docs/runbook-thesis-pdf-publish.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/thesis-writer.yaml'))"
---

# thesis-writer

Subagent that syncs the LaTeX manuscript at `~/Thesis2/thesis/` with
code, experiments, and ADRs. Writes chapters/, figures/, glosario/.
Always works in English (thesis is monolingual EN).

## Source coordinates

- `agents/thesis-writer.yaml` (worktree base: origin/main, repo: thesis)
- `prompts/thesis-writer.md`

## State

working. Known operational landmine: `thesis.pdf` is git-tracked and
parallel PRs cascade dirty on binary conflict (memory
`feedback_thesis_pdf_untrack`); see runbook for the untrack one-shot.

## Smoke test

```bash
python3 -c "import yaml; d = yaml.safe_load(open('agents/thesis-writer.yaml')); assert d['worktree']['repo'].endswith('thesis')"
```

## Runbook

- `docs/runbook-thesis-pdf-publish.md` for build + publish.
- Author name (Francisco Miguel Perez Canales) and co-supervisor framing
  (David Orellana-Martin + Ana M. Rojas) are non-negotiable per CLAUDE.md.

## Current owner

agent-farm conductor loop.
