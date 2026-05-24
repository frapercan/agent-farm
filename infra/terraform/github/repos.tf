# ---------------------------------------------------------------------------
# repos.tf
# Enforces the canonical policy bundle across all 9 PROTEA-stack repos.
#
# Policy bundle (per FARM-INFRA.1 spec):
#   - auto_delete_head_branches = true   (fixes cruft_audit_2026_05_22: 416 zombie remotes)
#   - Branch protection on default_branch:
#       require_pull_request_reviews (dismiss_stale_reviews, enforce_admins)
#       required_status_checks (strict + per-repo check list)
#       restrictions (null = any collaborator can push after checks pass)
#   - CODEOWNERS enforcement on .github/workflows/** and .github/actions/**
#     is handled via the CODEOWNERS file already present in each repo;
#     Terraform sets enforce_admins so even admins cannot bypass the gate.
#
# Root-causes addressed:
#   - feedback_pr_base_develop        : develop protection now enforced uniformly
#   - project_plugin_push_direct_main : plugin repos now have branch protection on main
#   - feedback_janitor_direct_push_agentfarm : agent-farm/main now protected
#   - project_cruft_audit_2026_05_22 : auto_delete_head_branches turned on
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Repository-level settings (auto-delete head branches)
# ---------------------------------------------------------------------------

resource "github_repository" "repos" {
  for_each = var.repos

  name = each.key

  # Do not create or delete repos; only manage the lifecycle settings.
  # (import existing repos before applying)
  auto_init = false

  # Root-cause fix: project_cruft_audit_2026_05_22 (416 zombie remote branches)
  delete_branch_on_merge = true

  lifecycle {
    # Prevent Terraform from accidentally deleting a repo that already exists.
    prevent_destroy = true
    # We only manage the fields declared above; ignore everything else
    # (description, visibility, topics, etc.) so this module is additive only.
    ignore_changes = [
      description,
      homepage_url,
      visibility,
      has_issues,
      has_projects,
      has_wiki,
      has_downloads,
      topics,
      auto_init,
      gitignore_template,
      license_template,
      archived,
      archive_on_destroy,
      pages,
      template,
      vulnerability_alerts,
      security_and_analysis,
    ]
  }
}

# ---------------------------------------------------------------------------
# Branch protection on the default branch of each repo
# ---------------------------------------------------------------------------

resource "github_branch_protection" "default" {
  for_each = var.repos

  repository_id = each.key
  pattern       = each.value.default_branch

  # Require a PR before merging (0 approvers matches solo-dev workflow).
  require_conversation_resolution = true

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = true
    required_approving_review_count = 0
  }

  required_status_checks {
    # strict = true means the branch must be up to date with the base before merge.
    strict   = true
    contexts = each.value.required_status_checks
  }

  # Enforce the protection rules even for administrators.
  enforce_admins = true

  # Nobody may force-push or delete the protected branch.
  allows_force_pushes = false
  allows_deletions    = false

  depends_on = [github_repository.repos]
}

# ---------------------------------------------------------------------------
# Branch protection on main for repos that ALSO have a develop branch
# (so main cannot be pushed to directly either).
# ---------------------------------------------------------------------------

resource "github_branch_protection" "main_for_develop_repos" {
  for_each = { for k, v in var.repos : k => v if v.has_develop }

  repository_id = each.key
  pattern       = "main"

  require_conversation_resolution = true

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = false
    required_approving_review_count = 0
  }

  required_status_checks {
    strict   = true
    contexts = each.value.required_status_checks
  }

  enforce_admins      = true
  allows_force_pushes = false
  allows_deletions    = false

  depends_on = [github_repository.repos]
}
