---
name: terraform-github-policy
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - infra/terraform/github/main.tf
  - infra/terraform/github/variables.tf
  - infra/terraform/github/repos.tf
  - infra/terraform/github/versions.tf
  - infra/terraform/github/outputs.tf
  - .github/workflows/terraform-validate.yml
  - tests/test_terraform_module_validates.py
runbook: infra/terraform/github/README.md
smoke: python3 -m pytest tests/test_terraform_module_validates.py -q
---

# terraform-github-policy

Terraform module (`infra/terraform/github/`) that encodes the canonical
GitHub repo policy for all 9 PROTEA-stack repositories as HCL. Any policy
drift (a protection rule toggled off in the UI, auto-delete disabled)
becomes a detectable diff rather than a silent incident.

## Source coordinates

- `infra/terraform/github/main.tf` (provider config)
- `infra/terraform/github/variables.tf` (repo list and required-check matrix)
- `infra/terraform/github/repos.tf` (per-repo resources via `for_each`)
- `infra/terraform/github/versions.tf` (Terraform + provider version constraints)
- `infra/terraform/github/outputs.tf` (applied rule summary)
- `.github/workflows/terraform-validate.yml` (CI: init + validate + plan on PRs)
- `tests/test_terraform_module_validates.py` (Python test wrapping terraform validate)

## Managed repos

PROTEA, protea-contracts, protea-method, protea-sources, protea-runners,
protea-backends, protea-reranker-lab, cafaeval-protea, agent-farm.

## Policy bundle

- Branch protection on each repo's default branch (develop or main).
- Required status checks (strict mode) per the per-repo CI workflow.
- PR required before merge (0 approvers for solo-dev workflow).
- Stale reviews dismissed on new push.
- CODEOWNERS enforcement on `.github/workflows/**` via
  `require_code_owner_reviews = true`.
- `enforce_admins = true`: no bypass even for the repo owner.
- Force-push and branch deletion blocked.
- `delete_branch_on_merge = true` on all repos (fixes the 416 zombie
  remote branches from `project_cruft_audit_2026_05_22`).

## Incidents closed

| Memory key | Description |
|---|---|
| `feedback_pr_base_develop` | develop had no enforced protection; executors created PRs against main |
| `project_plugin_push_direct_main_incident` | plugin repos had no branch protection on main |
| `feedback_janitor_direct_push_agentfarm` | agent-farm/main had zero branch protection |
| `project_cruft_audit_2026_05_22` | auto-delete-head-branches was off, accumulating 416 zombie remotes |

## State

working. Shipped by FARM-INFRA.1. CI gate (`terraform-validate.yml`) runs on
every PR touching `infra/terraform/**`. Apply is intentionally manual:
run `make terraform-plan` to review the diff, then `terraform apply`.

## Smoke test

```bash
python3 -m pytest tests/test_terraform_module_validates.py -q
```

(Skips automatically when `terraform` is not on PATH.)

## Runbook

See `infra/terraform/github/README.md` for the full apply walkthrough,
GITHUB_TOKEN scope requirements, and the import commands needed before
the first apply.

## Current owner

agent-farm conductor loop.
