# Branch-protection audit (FARM-1.2)

Generated: 2026-05-17T14:28:29Z
Operator: frapercan (gh CLI, admin on all listed repos)

| repo | branch | enforce_admins | dismiss_stale_reviews | required_review_count | allow_force_pushes | allow_deletions | required_contexts |
|------|--------|----------------|------------------------|------------------------|---------------------|------------------|--------------------|
| PROTEA | main | True | True | 0 | False | False | `lint (3.12, 2.1.0)`, `test (3.12, 2.1.0)`, `docs (3.12, 2.1.0)` |
| PROTEA | develop | True | True | 0 | False | False | `lint (3.12, 2.1.0)`, `test (3.12, 2.1.0)`, `docs/openapi.json matches code (3.12, 2.1.0)`, `integration (3.12, 2.1.0)`, `deploy slice builds and smokes` |
| protea-contracts | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| protea-contracts | develop | True | True | 0 | False | False | `test (3.10)`, `test (3.11)`, `test (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| protea-method | main | True | True | 0 | False | False | `ci`, `security` |
| protea-method | develop | True | True | 0 | False | False | `test (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| protea-sources | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| protea-sources | develop | True | True | 0 | False | False | `test (3.10)`, `test (3.11)`, `test (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| protea-runners | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| protea-runners | develop | True | True | 0 | False | False | `test (3.10)`, `test (3.11)`, `test (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| protea-backends | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| protea-backends | develop | True | True | 0 | False | False | `test (3.10)`, `test (3.11)`, `test (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| protea-reranker-lab | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| protea-reranker-lab | develop | True | True | 0 | False | False | `lint (3.12)`, `smell-budget (3.12)`, `pip-audit (3.12)`, `bandit (3.12)` |
| agent-farm | main | True | True | 0 | False | False | `coauthor-guard / scan` |
| thesis | main | True | True | 0 | False | False | `Build PDF` |

## Notes

- `cafaeval-protea` was deliberately skipped: it does not publish a `coauthor-guard` workflow, so requiring that check would soft-block every future PR. The plan brief calls for `try once, skip on failure`; workflow-incompatibility is the failure case.
- `agent-farm` has no `develop` branch and is intentionally not in the target list for that branch.
- `thesis` is single-trunk (`main` only).
- Existing required-check contexts were preserved per branch; the script only fills in a fallback when the branch had no contexts set (e.g. plugin-repo `main` branches, which previously had protection but zero required checks).
- `required_approving_review_count: 0` is by design (solo developer; PR + green checks are the gate).
- `required_conversation_resolution: false` (solo developer, no review conversations).
- `required_linear_history: false` (squash-merge is the convention; linear history is implicit).

Audit result: PASS (all branches: enforce_admins=true, dismiss_stale_reviews=true, allow_force_pushes=false, allow_deletions=false)
