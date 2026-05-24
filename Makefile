# Makefile for agent-farm
# Canonical make targets used by the conductor and CI.

.PHONY: terraform-plan terraform-validate

TF_DIR := infra/terraform/github

# terraform-plan: review the drift between HCL and live GitHub state.
# Requires GITHUB_TOKEN to be set in the environment.
terraform-plan:
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "ERROR: GITHUB_TOKEN is not set. Export a PAT with repo+admin:org scopes." >&2; \
		exit 1; \
	fi
	cd $(TF_DIR) && terraform init -backend=false -input=false
	cd $(TF_DIR) && terraform plan -input=false

# terraform-validate: syntax and structure check only (no auth required).
terraform-validate:
	cd $(TF_DIR) && terraform init -backend=false -input=false
	cd $(TF_DIR) && terraform validate
