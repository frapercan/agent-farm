# ---------------------------------------------------------------------------
# main.tf
# Provider configuration for the GitHub Terraform module.
# Auth: set GITHUB_TOKEN in the environment before running plan/apply.
# ---------------------------------------------------------------------------

provider "github" {
  owner = var.github_owner
  # token is read from the GITHUB_TOKEN environment variable automatically.
}
