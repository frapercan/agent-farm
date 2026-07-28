---
name: pinned-deps-guard
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/pinned-deps-guard.yml
smoke: yamllint .github/workflows/pinned-deps-guard.yml || python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pinned-deps-guard.yml'))"
---

# pinned-deps-guard

Reusable GitHub Actions workflow that fails any pull request declaring an
internal git dependency by branch instead of by commit. Callers invoke it via
`workflow_call` from their own pull-request workflow, the same shape as
[coauthor-guard](coauthor-guard.md).

## Why it exists

A branch name is not a version. While a consumer pins a branch, that branch is
the delivery channel, so urgent work lands on it directly to unblock the
consumer and bypasses the gates on the trunk. The divergence then grows by
construction rather than by neglect, which is why every repository in the stack
was diverged in both directions when this was written.

The failure is not only bookkeeping. A resolver refuses outright to satisfy one
dependency pinned to a commit and another pinned to a branch, so a
half-migrated stack does not build at all. That is what forces a migration to
proceed leaf-first: every consumed package pins its own dependencies before the
package that consumes it can pin anything.

A sweep of the stack found twelve internal edges pinned to a moving branch and
one pinned to a commit.

## What it flags

Two spellings reach the same place and both are checked:

- the table form, `pkg = { git = "...", branch = "main" }`, including `tag =`
- the URL form, `pkg @ git+https://host/org/repo.git@main`, where the ref after
  the `@` is not a full forty-character commit

A session-level `merge` on a SQLAlchemy session is not a dependency and is
skipped.

## Calibration

Run over all eight repositories before landing, per the rule that a check
firing on correct code is a check people learn to skip. It flagged exactly the
branch pins and left untouched the three repositories that had none.

## Source coordinates

- `.github/workflows/pinned-deps-guard.yml`

## State

working. Wired in the platform; the plugin repositories inherit the rule
through their own callers as they migrate.

## Smoke test

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pinned-deps-guard.yml'))"
```
