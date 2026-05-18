---
name: features-surface
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - docs/features/
  - scripts/render-features-index.sh
  - scripts/check-features-coverage.sh
  - scripts/lib/features/render_index.py
  - scripts/lib/features/coverage.py
  - .github/workflows/features-coverage.yml
runbook: docs/features/README.md
smoke: bash scripts/check-features-coverage.sh
---

# features-surface

The `docs/features/` documentation surface itself: one markdown file per
first-class capability, an auto-generated index, and a CI gate that
fails any PR that adds a new agent / script / workflow / slash command
without a corresponding feature page. Shipped FARM-FEAT.11.

## Source coordinates

- `docs/features/*.md` (one page per capability)
- `docs/features/README.md` (rendered index, do not edit by hand)
- `scripts/render-features-index.sh` (renderer wrapper)
- `scripts/check-features-coverage.sh` (CI gate wrapper)
- `scripts/lib/features/render_index.py` (renderer implementation)
- `scripts/lib/features/coverage.py` (coverage gate implementation)

## State

working.

## Smoke test

```bash
bash scripts/render-features-index.sh --check
bash scripts/check-features-coverage.sh
```

## Runbook

- Add a feature: write `docs/features/<name>.md` with the standard
  frontmatter (name, section, state, owner, source[], runbook, smoke),
  then re-run `bash scripts/render-features-index.sh`.
- The coverage gate (`check-features-coverage.sh`) enumerates expected
  capabilities from `agents/`, `scripts/services/`, `commands/`,
  `.github/workflows/`, and a curated list of top-level scripts. Adding
  a new top-level script means also editing
  `EXPECTED_TOP_LEVEL_SCRIPTS` in `coverage.py`.
- The gate is wired into `.github/workflows/features-coverage.yml`.

## Current owner

agent-farm conductor loop.
