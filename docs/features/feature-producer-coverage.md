---
name: feature-producer-coverage
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/feature-producer-coverage.yml
  - scripts/lib/feature_producer_coverage.py
  - tests/test_feature_producer_coverage.py
runbook: docs/features/README.md
smoke: python3 -m pytest tests/test_feature_producer_coverage.py -q
---

# feature-producer-coverage

CI gate that asserts every column added to PROTEA's
`ALL_FEATURES` has an unconditional producer wired into the dump
pipeline. Motivated by memory `project_canonical_feature_producer_consumer`:
without the gate, the dump pipeline crashes at T1.8 invariant.

## Source coordinates

- `.github/workflows/feature-producer-coverage.yml`
- `scripts/lib/feature_producer_coverage.py`
- `tests/test_feature_producer_coverage.py`

## State

working. Shipped FARM-1.10.

## Smoke test

```bash
python3 -m pytest tests/test_feature_producer_coverage.py -q
```

## Runbook

- The script mocks every payload flag combination and asserts every
  feature column gets populated.
- On failure: add the producer or guard the column with a feature flag.

## Current owner

agent-farm conductor loop.
