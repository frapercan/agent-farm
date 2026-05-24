# ---------------------------------------------------------------------------
# variables.tf
# Declares the GitHub owner, the list of managed repos, and the per-repo
# required-status-check matrix.
# ---------------------------------------------------------------------------

variable "github_owner" {
  description = "GitHub organisation or user that owns all managed repos."
  type        = string
  default     = "frapercan"
}

# ---------------------------------------------------------------------------
# Repo list with per-repo configuration
# ---------------------------------------------------------------------------

variable "repos" {
  description = <<-EOT
    Map of repo name to configuration block.

    Fields:
      default_branch          - the branch that Terraform protects (develop or main)
      required_status_checks  - list of CI job names that must pass before merge
      has_develop             - true when the repo uses a separate develop branch
  EOT

  type = map(object({
    default_branch         = string
    has_develop            = bool
    required_status_checks = list(string)
  }))

  default = {
    "PROTEA" = {
      default_branch = "develop"
      has_develop    = true
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-contracts" = {
      default_branch = "develop"
      has_develop    = true
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-method" = {
      default_branch = "develop"
      has_develop    = true
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-sources" = {
      default_branch = "main"
      has_develop    = false
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-runners" = {
      default_branch = "main"
      has_develop    = false
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-backends" = {
      default_branch = "main"
      has_develop    = false
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
      ]
    }

    "protea-reranker-lab" = {
      default_branch = "develop"
      has_develop    = true
      required_status_checks = [
        "pytest",
        "ruff",
        "coauthor-guard",
        "reranker-token-lint",
      ]
    }

    "cafaeval-protea" = {
      default_branch = "main"
      has_develop    = false
      required_status_checks = [
        "pytest",
        "coauthor-guard",
      ]
    }

    "agent-farm" = {
      default_branch = "main"
      has_develop    = false
      required_status_checks = [
        "pytest",
        "coauthor-guard",
        "features-coverage",
        "plans-render-check",
      ]
    }
  }
}
