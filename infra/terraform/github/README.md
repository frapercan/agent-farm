# infra/terraform/github

Terraform module that enforces the canonical GitHub repo policy across
all 9 PROTEA-stack repositories. Any policy drift (a protection rule
toggled off in the UI, auto-delete disabled) becomes a detectable diff
rather than a silent incident.

## Managed repos

The module is a codified mirror of the LIVE branch protection on each repo.
Required status-check contexts are the real CI job names, aligned to the
Python 3.12 matrix (the `test (3.10)` / `test (3.11)` legs were dropped).
Each repo declares protection per branch pattern under `protections`; a repo
with no develop branch simply omits the develop key.

| Repo | Default branch | Protected branches |
|---|---|---|
| PROTEA | main | main, develop |
| protea-contracts | main | main, develop |
| protea-method | main | main, develop |
| protea-sources | main | main, develop |
| protea-runners | main | main, develop |
| protea-backends | main | main, develop |
| protea-reranker-lab | develop | main, develop |
| cafaeval-protea | main | main |
| agent-farm | main | main |

The exact required-check contexts per (repo, branch) live in `variables.tf`.

## Policy bundle

For every protected branch:

- Require a pull request before merging (0 required approvers, matching
  the solo-dev workflow; the rule still blocks direct push for everyone
  including admins).
- Required status checks must pass. Contexts are declared per branch to
  match the real CI jobs; `strict` is false (live state does not require the
  branch to be up to date before merge).
- On `main` patterns, stale reviews are dismissed on a new push. On
  `develop` patterns (and on the main of repos that have no develop), the
  CODEOWNERS gate is enforced via `require_code_owner_reviews = true`.
- `enforce_admins = true`: no bypass even for the repo owner.
- Force-push and branch deletion blocked.
- `delete_branch_on_merge = true`: head branches are deleted automatically
  after merge (fixes the 416 zombie remote branches from
  `project_cruft_audit_2026_05_22`).

## Incidents this module closes

| Memory key | Incident |
|---|---|
| `feedback_pr_base_develop` | Executors created PRs against main instead of develop because develop had no enforced protection |
| `project_plugin_push_direct_main_incident` | Plugin repos (sources, runners, backends) had no branch protection on main; janitors pushed directly |
| `feedback_janitor_direct_push_agentfarm` | agent-farm/main had zero branch protection |
| `project_cruft_audit_2026_05_22` | auto-delete-head-branches was off across all repos |

## Prerequisites

1. A GitHub Personal Access Token (classic) with the following scopes:
   - `repo` (full control of private repositories)
   - `admin:org` (read:org is sufficient for public repos in a personal account)

2. Export the token before running any Terraform command:

   ```bash
   export GITHUB_TOKEN="ghp_..."
   ```

3. Import the existing repos before the first apply (Terraform does not
   create repos from scratch; it manages existing ones):

   ```bash
   cd infra/terraform/github
   terraform init
   terraform import 'github_repository.repos["PROTEA"]' PROTEA
   terraform import 'github_repository.repos["agent-farm"]' agent-farm
   # ... repeat for each repo in variables.tf
   ```

## Usage

```bash
export GITHUB_TOKEN="ghp_..."
cd infra/terraform/github

terraform init
terraform validate
terraform plan          # review the diff
terraform apply         # confirm interactively
```

The canonical make target wraps the plan step:

```bash
make terraform-plan
```

## Drift detection

Run `terraform plan` against the live state at any time. A non-empty diff
means someone changed a protection rule in the GitHub UI without updating
this module. The CI workflow (`terraform-validate.yml`) runs init, validate,
and plan on every PR that touches `infra/terraform/**`, catching syntax
errors and provider schema mismatches early. The plan step in CI uses a
dummy token so it validates configuration structure only (it will not apply
or authenticate against GitHub).

## State

Terraform state is stored locally (`terraform.tfstate` in this directory)
by default. Do not commit `terraform.tfstate` or `terraform.tfstate.backup`
to git (both are in `.gitignore`). For a shared setup, configure a remote
backend (S3, Terraform Cloud, etc.) before the first `terraform init`.
