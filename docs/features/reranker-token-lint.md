---
name: reranker-token-lint
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/reranker-token-lint.yml
  - scripts/lint-reranker-tokens.py
  - tests/test_lint_reranker_tokens.py
runbook: docs/features/README.md
smoke: python3 -m pytest tests/test_lint_reranker_tokens.py -q
---

# reranker-token-lint

Lints prose (READMEs, ADRs, thesis chapters, CHANGELOGs) for the
deprecated `vN` reranker shorthand: every reference to a reranker
version must use the axis-tuple form `(plm, k, reranker, features,
eval_set, propagation, ensemble)`. GOA snapshot tokens like `v220`,
`v226`, `v230` are exempt (legitimate dataset cutoffs).

## Source coordinates

- `.github/workflows/reranker-token-lint.yml`
- `scripts/lint-reranker-tokens.py`
- `tests/test_lint_reranker_tokens.py`

## State

working. CHANGELOG.md was excluded from defaults (memory
`project_farm_exp_6_changelog_exclude`); `bench-v1-K5-*` dataset names
are structurally allowlisted.

## Smoke test

```bash
python3 scripts/lint-reranker-tokens.py --help 2>&1 | head -5
python3 -m pytest tests/test_lint_reranker_tokens.py -q
```

## Runbook

- Live across PROTEA + lab + thesis (memory
  `project_farm_exp_6_pending_cleanups`).
- Don't extend GOA_ALLOWLIST to silence CHANGELOG offences; fix prose.

## Current owner

agent-farm conductor loop.
