---
name: stash-audit
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/stash-audit.yml
runbook: scripts/lib/README-hooks.md
smoke: yamllint .github/workflows/stash-audit.yml || python3 -c "import yaml; yaml.safe_load(open('.github/workflows/stash-audit.yml'))"
---

# stash-audit

Server-side GitHub Actions workflow that fails any PR whose checkout
contains a non-empty `git stash list`. Backstop for the worktree-local
pre-commit / pre-push hooks, which an agent can bypass via `gh api`.
Shipped alongside the FARM-1.1a coauthor-guard after eight stash-bypass
incidents across three sessions (memory `feedback_git_stash_6x`).

## Source coordinates

- `.github/workflows/stash-audit.yml`

## State

Working. The workflow runs on every `pull_request` event and exits
non-zero when `git stash list` returns anything. Required check on the
default branch of every repo in the stack (PROTEA, the seven satellite
plugin repos, and agent-farm). Pairs with the inverse pattern in
[coauthor-guard](coauthor-guard.md): both gates are intentionally
narrow, single-purpose, and have no escape hatch.

## Behaviour matrix

| Scenario                                | Outcome              |
|-----------------------------------------|----------------------|
| `git stash list` is empty               | scan passes          |
| Stash entry present at checkout time    | scan fails, PR blocks |
| Workflow file invalid YAML              | scan errors, PR blocks |

## Migration notes

The reusable workflow lives in
`frapercan/agent-farm/.github/workflows/stash-audit.yml`; consumer repos
call it through a thin three-line caller workflow under their own
`.github/workflows/stash-audit.yml`. This mirrors the
[coauthor-guard](coauthor-guard.md) reusable-workflow pattern (restored
2026-05-24 after an inline reimplementation introduced a shell-injection
incident, memory `feedback_audit_janitor_shipped_shell_injection`).
