# ---------------------------------------------------------------------------
# repos.tf
# Codifies the canonical GitHub policy bundle across the PROTEA-stack repos.
#
# The branch-protection resources mirror the LIVE GitHub state exactly (one
# resource per protected pattern, with the real per-branch required checks and
# review settings). This makes `terraform plan` a drift detector: a non-empty
# diff means a protection rule was changed in the UI without updating this
# module.
#
# Root-causes addressed:
#   - feedback_pr_base_develop        : develop protection enforced where present
#   - project_plugin_push_direct_main : plugin repos have main protection
#   - feedback_janitor_direct_push_agentfarm : agent-farm/main protected
#   - project_cruft_audit_2026_05_22 : delete_branch_on_merge turned on
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Flatten the per-repo, per-branch protection map into a single keyed map so
# each protected pattern becomes one github_branch_protection instance.
# ---------------------------------------------------------------------------

locals {
  branch_protections = merge([
    for repo, cfg in var.repos : {
      for branch, p in cfg.protections :
      "${repo}:${branch}" => {
        repository                 = repo
        pattern                    = branch
        contexts                   = p.contexts
        strict                     = p.strict
        dismiss_stale_reviews      = p.dismiss_stale_reviews
        require_code_owner_reviews = p.require_code_owner_reviews
      }
    }
  ]...)
}

# ---------------------------------------------------------------------------
# Repository-level settings (delete head branch on merge)
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
    # (description, visibility, topics, merge buttons, etc.) so this module is
    # additive only and does not fight the repo's own settings.
    ignore_changes = [
      description,
      homepage_url,
      visibility,
      has_issues,
      has_projects,
      has_wiki,
      has_downloads,
      auto_init,
      gitignore_template,
      license_template,
      archived,
      archive_on_destroy,
      pages,
      template,
      vulnerability_alerts,
      security_and_analysis,
      allow_merge_commit,
      allow_squash_merge,
      allow_rebase_merge,
      allow_auto_merge,
      allow_update_branch,
      merge_commit_title,
      merge_commit_message,
      squash_merge_commit_title,
      squash_merge_commit_message,
      web_commit_signoff_required,
      topics,
    ]
  }
}

# ---------------------------------------------------------------------------
# Branch protection: one instance per protected (repo, pattern), mirroring the
# live per-branch required checks and review settings.
# ---------------------------------------------------------------------------

resource "github_branch_protection" "this" {
  for_each = local.branch_protections

  # Reference the repository's node_id (not its name): the GitHub provider
  # normalises repository_id to the node_id, so passing the bare name would
  # force perpetual replacement of every protection rule.
  repository_id = github_repository.repos[each.value.repository].node_id
  pattern       = each.value.pattern

  required_pull_request_reviews {
    dismiss_stale_reviews           = each.value.dismiss_stale_reviews
    require_code_owner_reviews      = each.value.require_code_owner_reviews
    required_approving_review_count = 0
  }

  required_status_checks {
    strict   = each.value.strict
    contexts = each.value.contexts
  }

  # Enforce protection even for administrators; block force-push and deletion.
  enforce_admins      = true
  allows_force_pushes = false
  allows_deletions    = false

  depends_on = [github_repository.repos]
}
