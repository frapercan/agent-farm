# ---------------------------------------------------------------------------
# outputs.tf
# Emits a summary of the applied policy so `terraform output` gives a quick
# audit snapshot without needing to open the GitHub UI.
# ---------------------------------------------------------------------------

output "protected_repos" {
  description = "Map of repo name to the branch that is protected."
  value = {
    for k, v in var.repos : k => {
      protected_branch       = v.default_branch
      has_develop            = v.has_develop
      required_status_checks = v.required_status_checks
    }
  }
}

output "auto_delete_head_branches_enabled" {
  description = "Repos where delete_branch_on_merge is managed by this module."
  value       = keys(var.repos)
}
