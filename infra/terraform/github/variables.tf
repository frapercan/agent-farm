# ---------------------------------------------------------------------------
# variables.tf
# Declares the GitHub owner and the per-repo, per-branch protection matrix.
#
# This map is the codified mirror of the LIVE branch protection on each repo
# (captured via `gh api repos/frapercan/<r>/branches/<b>/protection`). The
# required-status-check contexts are the real CI job names, already aligned to
# the Python 3.12 matrix (the "test (3.10)" / "test (3.11)" legs were dropped
# out of band on the plugin repos). Keep this file equal to live so
# `terraform plan` stays a no-op and any future UI drift surfaces as a diff.
# ---------------------------------------------------------------------------

variable "github_owner" {
  description = "GitHub organisation or user that owns all managed repos."
  type        = string
  default     = "frapercan"
}

# ---------------------------------------------------------------------------
# Repo list with per-branch protection configuration
# ---------------------------------------------------------------------------

variable "repos" {
  description = <<-EOT
    Map of repo name to configuration block.

    Fields:
      default_branch - the repo's GitHub default branch (informational; drives
                       outputs only). Protection itself is declared per pattern
                       under `protections`.
      protections    - map of branch pattern (main, develop) to its live
                       protection settings. A repo with no develop branch simply
                       omits the develop key.

    Per-protection fields mirror the live GitHub state:
      contexts                   - exact required status-check job names (3.12)
      strict                     - require branch up to date before merge
      dismiss_stale_reviews      - dismiss approvals on new push
      require_code_owner_reviews - enforce CODEOWNERS gate
  EOT

  type = map(object({
    default_branch = string
    protections = map(object({
      contexts                   = list(string)
      strict                     = bool
      dismiss_stale_reviews      = bool
      require_code_owner_reviews = bool
    }))
  }))

  default = {
    "PROTEA" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts = [
            "lint (3.12, 2.1.0)",
            "test (3.12, 2.1.0)",
            "docs (3.12, 2.1.0)",
          ]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "lint (3.12, 2.1.0)",
            "test (3.12, 2.1.0)",
            "docs/openapi.json matches code (3.12, 2.1.0)",
            "integration (3.12, 2.1.0)",
            "deploy slice builds and smokes",
            "lint / scan",
            "scan",
            "audit",
            "critical user flows",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-contracts" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["coauthor-guard / scan"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "test (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "scan",
            "audit",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-method" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["ci", "security"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "test (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "scan",
            "audit",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-sources" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["coauthor-guard / scan"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "test (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "scan",
            "audit",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-runners" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["coauthor-guard / scan"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "test (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "scan",
            "audit",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-backends" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["coauthor-guard / scan"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "test (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "scan",
            "audit",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "protea-reranker-lab" = {
      default_branch = "develop"
      protections = {
        "main" = {
          contexts                   = ["coauthor-guard / scan"]
          strict                     = false
          dismiss_stale_reviews      = true
          require_code_owner_reviews = false
        }
        "develop" = {
          contexts = [
            "lint (3.12)",
            "smell-budget (3.12)",
            "pip-audit (3.12)",
            "bandit (3.12)",
            "lint / scan",
          ]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "cafaeval-protea" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["scan", "audit"]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }

    "agent-farm" = {
      default_branch = "main"
      protections = {
        "main" = {
          contexts                   = ["scan", "audit"]
          strict                     = false
          dismiss_stale_reviews      = false
          require_code_owner_reviews = true
        }
      }
    }
  }
}
