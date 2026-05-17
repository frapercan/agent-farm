# D33. cafaeval-protea janitor scope decision

- Status: accepted
- Date: 2026-05-17
- Driver: FARM-FEAT.10 (cafaeval-protea coverage decision)
- Author: executor agent on behalf of Francisco Miguel Pérez Canales

## Context

`cafaeval-protea` is a speedup fork of the upstream CAFA evaluator
(cafaeval / CAFA-evaluator-PK). It lives at
`~/Thesis2/repositories/cafaeval-protea/` and is published as
`frapercan/cafaeval-protea` on GitHub. The fork adds sparse-kernel
and vectorised-parser speedups developed during CAFA 5/6 cycles; it
is GPLv3-licensed and is the evaluation harness that PROTEA's lab
pipeline calls when computing Fmax / S-min scores.

The janitor agent sweeps 7 repositories (PROTEA + 6 plugin repos)
for stale PRs and CI failures. `cafaeval-protea` was never added to
that list, creating a visibility gap: PRs opened on the fork go
untriaged unless the author reviews them manually.

This gap surfaced during FARM-1.2 (branch-protection rollout,
2026-05-17), where `cafaeval-protea` was deliberately excluded
because it lacked the `coauthor-guard` GitHub Actions workflow
required by FARM-1.1. Adding it to the janitor scope without that
workflow would let co-authored commits land on `cafaeval-protea/main`
undetected, violating the co-author-guard policy.

The FARM-FEAT.10 slice asks for a concrete decision with an ADR.

## Decision

Exclude `cafaeval-protea` from the janitor sweep scope.

## Rationale

1. **Activity below threshold**. The rubric in the FARM-FEAT.10 slice
   specifies: fewer than 2 open PRs and fewer than 2 commits in the
   last 30 days signals a low-touch fork. Observation on 2026-05-17:
   0 open PRs and 5 commits in 30 days (all docs or minor fixes, no
   feature work). This is the low-touch pattern.

2. **No coauthor-guard workflow**. The fork has no
   `.github/workflows/coauthor-guard.yml`. Adding `cafaeval-protea`
   to the janitor sweep before shipping that workflow would create a
   gap in the co-author-check coverage that FARM-1.1 and FARM-1.2
   were designed to close. The FARM-1.2 executor explicitly flagged
   this: cafaeval-protea was skipped in branch-protection because
   requiring a check that does not exist would soft-block every PR.

3. **No branch protection**. `cafaeval-protea/main` has no branch
   protection rules as of 2026-05-17. A janitor merging PRs on an
   unprotected branch provides no safety guarantee.

4. **Distinct release lifecycle**. The fork targets PyPI and
   ReadTheDocs publication and is consumed by PROTEA as a versioned
   dependency, not as a co-developed plugin. Its release cadence is
   decoupled from the PROTEA stack's develop-trunk cycle. Including
   it in the janitor's scope would conflate two distinct maintenance
   models.

5. **pr_base.py already lists it**. The canonical PR-base table
   (`scripts/lib/pr_base.py`) already carries `cafaeval-protea:
   develop`. That entry is retained for the finalize script's PR-URL
   scanner (so the base is correct if an agent ever opens a PR there
   manually) but does not imply janitor sweep coverage.

## Consequences

### Positive

- The janitor scope stays at 7 repos. No new coauthor-guard or
  branch-protection work is required as a precondition.
- `cafaeval-protea` PRs are not silently merged without branch
  protection or CI checks in place.
- The decision is documented and revisitable; see the Follow-up
  section below.

### Negative / accepted trade-offs

- PRs on `cafaeval-protea` remain manually reviewed by the author.
  At current activity levels (0 open PRs as of 2026-05-17) this is
  not a burden.
- If fork activity grows the gap will be noticed only when the author
  observes stale PRs manually, not via the farm.

## Implementation

This ADR is the only file changed by FARM-FEAT.10. No changes to
`prompts/janitor.md`, `scripts/lib/redcheck-systemic.py`, or any
agent configuration are made.

The `scripts/lib/pr_base.py` entry for `cafaeval-protea` is retained
as-is (it serves the PR-URL finalize scanner regardless of janitor
scope).

## Follow-up (recommended, out of scope for this slice)

The decision is revisitable. If any of the following conditions are
met, file a new slice (FARM-FEAT.10a) to add `cafaeval-protea`:

1. A `coauthor-guard` workflow is shipped on `cafaeval-protea`
   (prerequisite for branch protection + janitor merge safety).
2. Branch protection is enabled on `cafaeval-protea/main`.
3. Open PR count or commit frequency exceeds the activity threshold
   (more than 5 PRs or commits in any 30-day window).

Until those conditions are satisfied the exclusion stands.
