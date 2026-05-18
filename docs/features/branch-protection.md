---
name: branch-protection
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - scripts/apply-branch-protection.sh
  - tests/test_apply_branch_protection.py
runbook: docs/runbook-branch-protection.md
smoke: python3 -m pytest tests/test_apply_branch_protection.py -q
---

# branch-protection

Idempotent script that applies the canonical branch protection rule set
to every watched repo (8 PROTEA-family repos + agent-farm + thesis). The
canonical rule set: require PR + status checks + linear history,
disallow force-push, disallow deletions, require the coauthor-guard
check.

## Source coordinates

- `scripts/apply-branch-protection.sh`
- `tests/test_apply_branch_protection.py`
- `docs/runbook-branch-protection.md`

## State

working. Motivated by memory
`project_plugin_push_direct_main_incident` (plugin repos had no
protection) and `feedback_janitor_direct_push_agentfarm` (agent-farm/main
had no protection).

## Smoke test

```bash
bash -n scripts/apply-branch-protection.sh
python3 -m pytest tests/test_apply_branch_protection.py -q
```

## Runbook

- `docs/runbook-branch-protection.md` for the policy + apply walkthrough.

## Current owner

agent-farm conductor loop.
