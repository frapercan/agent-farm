#!/usr/bin/env bash
# apply-branch-protection.sh -- FARM-1.2
#
# Server-side branch protection for the 8 watched Thesis2 repos. Applies
# the same rule shape across (repo, branch) pairs via the GitHub API,
# preserving the existing required-status-check contexts when the branch
# is already protected. Idempotent.
#
# The protection rule (per FARM-1.2 acceptance):
#   - required_status_checks: at least one context required; existing
#     contexts preserved when already set, else REPO_DEFAULT_CHECK applies
#     (PROTEA = "integration (3.12, 2.1.0)", others = "coauthor-guard / scan",
#     thesis = "Build PDF")
#   - enforce_admins: true              (rule applies to admins too)
#   - required_pull_request_reviews:
#       dismiss_stale_reviews: true
#       required_approving_review_count: 0   (solo dev; PR + checks is the gate)
#   - restrictions: null                (no team-push restrictions)
#   - allow_force_pushes: false
#   - allow_deletions: false
#   - required_conversation_resolution: false (solo dev, no convos)
#   - required_linear_history: false    (squash-merge is convention)
#
# Memory references for "why":
#   - feedback_janitor_direct_push_agentfarm.md   (agent-farm/main direct push, 2026-05-16)
#   - project_plugin_push_direct_main_incident.md (sources/runners/backends, 2026-05-13)
#   - feedback_farm_1_1_hook_bypass.md            (client-side hook bypass, 2026-05-16)
#
# Usage:
#   bash apply-branch-protection.sh                 # dry-run (default)
#   bash apply-branch-protection.sh --dry-run
#   bash apply-branch-protection.sh --apply
#
# Output: one line per (repo, branch):
#   ok          protection applied (or already-equivalent, idempotent)
#   skip(branch-missing)   branch does not exist on the repo
#   skip(no-admin)         403 from GitHub: caller is not admin
#   error(<reason>)        anything else; logged and we continue
#
# Exit codes:
#   0  every (repo, branch) ended in ok or a non-error skip
#   2  at least one (repo, branch) errored; check the log
#   1  precondition failure (no gh CLI, no auth)

set -euo pipefail

MODE="dry-run"
case "${1:-}" in
  --apply)   MODE="apply" ;;
  --dry-run) MODE="dry-run" ;;
  "")        MODE="dry-run" ;;
  *) echo "usage: $0 [--dry-run|--apply]" >&2; exit 1 ;;
esac

# Preconditions.
if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not on PATH" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh CLI not authenticated; run 'gh auth login'" >&2
  exit 1
fi

OWNER="frapercan"

# (repo, branch, fallback_check) tuples. Branches listed twice (main +
# develop) for the PROTEA stack repos that have both. PROTEA itself has
# both. agent-farm and cafaeval-protea have only main. thesis has main.
#
# Fallback check is used only when the branch has no protection yet OR
# has protection without any required contexts; otherwise the existing
# contexts are preserved verbatim (drift-free).
TARGETS=(
  "PROTEA              main      integration (3.12, 2.1.0)"
  "PROTEA              develop   integration (3.12, 2.1.0)"
  "protea-contracts    main      coauthor-guard / scan"
  "protea-contracts    develop   coauthor-guard / scan"
  "protea-method       main      coauthor-guard / scan"
  "protea-method       develop   coauthor-guard / scan"
  "protea-sources      main      coauthor-guard / scan"
  "protea-sources      develop   coauthor-guard / scan"
  "protea-runners      main      coauthor-guard / scan"
  "protea-runners      develop   coauthor-guard / scan"
  "protea-backends     main      coauthor-guard / scan"
  "protea-backends     develop   coauthor-guard / scan"
  "protea-reranker-lab main      coauthor-guard / scan"
  "protea-reranker-lab develop   coauthor-guard / scan"
  "agent-farm          main      coauthor-guard / scan"
  "thesis              main      Build PDF"
  # cafaeval-protea is intentionally skipped: it does not publish a
  # coauthor-guard workflow, so requiring that check would soft-block
  # every future PR. Per FARM-1.2 brief: "try once, skip on failure";
  # we treat workflow-incompatibility as the failure case and log it.
)

# Build the protection body. $1 = newline-separated contexts (may be empty
# string for none); produces JSON on stdout.
build_body() {
  local contexts="$1"
  python3 - "$contexts" <<'PY'
import json
import sys

raw = sys.argv[1]
contexts = [line for line in raw.splitlines() if line.strip()]
body = {
    "required_status_checks": {
        "strict": False,
        "contexts": contexts,
    },
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "required_approving_review_count": 0,
    },
    "restrictions": None,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_conversation_resolution": False,
    "required_linear_history": False,
}
print(json.dumps(body))
PY
}

# Decide the contexts to use for a given (repo, branch, fallback).
# Echoes the contexts newline-separated (empty if none decided).
decide_contexts() {
  local repo="$1" branch="$2" fallback="$3"
  local existing
  existing=$(gh api "/repos/$OWNER/$repo/branches/$branch/protection" 2>/dev/null \
    | jq -r 'try .required_status_checks.contexts[]' 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    printf '%s\n' "$existing"
  else
    printf '%s\n' "$fallback"
  fi
}

# Returns 0 if the branch exists on the repo, 1 if not.
branch_exists() {
  local repo="$1" branch="$2"
  gh api "/repos/$OWNER/$repo/branches/$branch" >/dev/null 2>&1
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/state/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/branch-protection-$(date -u +%Y-%m-%d).log"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

errors=0
ok_count=0
expected=0
{
  echo "# apply-branch-protection.sh run @ $(ts)  mode=$MODE"
} >> "$LOG_FILE"

for row in "${TARGETS[@]}"; do
  # Split the row by collapsing whitespace; the fallback check name is the
  # rest of the line after the second whitespace-separated token.
  read -r repo branch rest <<<"$row"
  fallback="$rest"
  expected=$((expected + 1))

  if ! branch_exists "$repo" "$branch"; then
    line="$repo/$branch: skip(branch-missing)"
    echo "$line"
    echo "$(ts) $line" >> "$LOG_FILE"
    continue
  fi

  contexts=$(decide_contexts "$repo" "$branch" "$fallback")
  body=$(build_body "$contexts")

  if [[ "$MODE" == "dry-run" ]]; then
    ctx_summary=$(printf '%s' "$contexts" | tr '\n' '|' | sed 's/|$//')
    line="$repo/$branch: dry-run (contexts=$ctx_summary)"
    echo "$line"
    echo "$(ts) $line" >> "$LOG_FILE"
    ok_count=$((ok_count + 1))
    continue
  fi

  # Apply mode. Capture HTTP body and status separately.
  tmp_body=$(mktemp)
  http_code=$(printf '%s' "$body" \
    | gh api -X PUT "/repos/$OWNER/$repo/branches/$branch/protection" \
        --input - \
        -H "Accept: application/vnd.github+json" \
        > "$tmp_body" 2>&1 && echo 200 || echo "$?")
  resp=$(cat "$tmp_body")
  rm -f "$tmp_body"

  if [[ "$http_code" == "200" ]]; then
    line="$repo/$branch: ok"
    ok_count=$((ok_count + 1))
  else
    if echo "$resp" | grep -qi "HTTP 403\|Must have admin"; then
      line="$repo/$branch: skip(no-admin)"
    else
      reason=$(echo "$resp" | tr '\n' ' ' | cut -c1-200)
      line="$repo/$branch: error($reason)"
      errors=$((errors + 1))
    fi
  fi
  echo "$line"
  echo "$(ts) $line" >> "$LOG_FILE"
done

{
  echo "# summary: ok=$ok_count expected=$expected errors=$errors mode=$MODE"
  echo
} >> "$LOG_FILE"

echo
echo "summary: ok=$ok_count/$expected errors=$errors  log=$LOG_FILE"

if [[ "$errors" -gt 0 ]]; then
  exit 2
fi
exit 0
