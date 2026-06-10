# ---------------------------------------------------------------------------
# outputs.tf
# Emits a summary of the declared policy so `terraform output` gives a quick
# audit snapshot without needing to open the GitHub UI.
# ---------------------------------------------------------------------------

output "protected_branches" {
  description = "Map of repo name to its protected branches and required checks."
  value = {
    for repo, cfg in var.repos : repo => {
      default_branch = cfg.default_branch
      protections = {
        for branch, p in cfg.protections : branch => p.contexts
      }
    }
  }
}

output "delete_branch_on_merge_enabled" {
  description = "Repos where delete_branch_on_merge is managed by this module."
  value       = keys(var.repos)
}
