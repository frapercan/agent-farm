# Runbook: GitHub branch protection (FARM-1.2)

Server-side enforcement of the "no direct push to `main` / `develop`" rule
across the 8 Thesis2 repos. Branch protection is the authoritative gate;
the FARM-1.1 client-side hooks are the first line of defence but can be
bypassed by editing local `.git/hooks` or by an agent with a stale
checkout.

## Why protection exists

Two real incidents motivate the rule set:

- `feedback_janitor_direct_push_agentfarm.md` (2026-05-16). A janitor agent
  pushed commit `565b5af` straight to `agent-farm/main` because the repo
  had zero branch protection. The push bypassed PR review, status checks,
  and the co-author guard.
- `project_plugin_push_direct_main_incident.md` (2026-05-13). Chore
  commits were pushed directly to `protea-sources`, `protea-runners`,
  and `protea-backends` on `main` over a single afternoon. Once landed
  the commits could not be reverted because force-push was already
  banned by convention but not by the server.
- `feedback_farm_1_1_hook_bypass.md` (2026-05-16). Two `Co-Authored-By:
  Claude` commits slipped through despite the new pre-commit hook. Root
  cause was a missing hook installation in the main checkout. Branch
  protection plus the `coauthor-guard` workflow now make the bypass
  irrelevant: a Claude trailer fails the check, the check is required,
  the merge is blocked.

## Rule set (YAML form)

The script `scripts/apply-branch-protection.sh` writes the following body
to `PUT /repos/<owner>/<repo>/branches/<branch>/protection` for every
(repo, branch) target:

```yaml
required_status_checks:
  strict: false                       # squash-merge tolerates lagging branches
  contexts:                           # filled per repo from existing checks
    - "<context-1>"
    - "<context-2>"
enforce_admins: true                  # admins (including the operator) bound by the rule
required_pull_request_reviews:
  dismiss_stale_reviews: true         # new push to PR drops prior approvals
  require_code_owner_reviews: false
  required_approving_review_count: 0  # solo developer; checks are the gate, not human review
restrictions: null                    # no team-push allowlist
allow_force_pushes: false
allow_deletions: false
required_conversation_resolution: false   # solo dev, no review conversations
required_linear_history: false            # squash-merge is the convention
```

### 0 required reviews + 1 required check

The author works solo on this thesis. The protection model is therefore:

- PRs are mandatory (no direct push).
- Required status checks gate merge. Each branch carries at least one
  required check; existing per-repo CI contexts are preserved.
- `enforce_admins: true` means the operator must follow the same path.
- Human review is not required because there are no other humans.

If a second maintainer joins, flip `required_approving_review_count` to
`1` in `scripts/apply-branch-protection.sh` and re-run with `--apply`.

## Protected branches (current state)

Re-generated automatically by the apply script. Latest audit:
`state/logs/branch-protection-audit-2026-05-17.md`.

| repo | branches protected | trunk |
|------|---------------------|-------|
| PROTEA | main, develop | develop |
| protea-contracts | main, develop | develop |
| protea-method | main, develop | develop |
| protea-sources | main, develop | develop |
| protea-runners | main, develop | develop |
| protea-backends | main, develop | develop |
| protea-reranker-lab | main, develop | develop |
| agent-farm | main | main |
| thesis | main | main |

`cafaeval-protea` is intentionally excluded (see "Out of scope" below).

## Inspect protection

```bash
gh api /repos/<owner>/<repo>/branches/<branch>/protection | jq
```

Shortcut for a quick "are admins bound?" check:

```bash
gh api /repos/frapercan/PROTEA/branches/develop/protection \
  | jq '.enforce_admins.enabled'
```

## Add a new required check

1. Push the new workflow to the repo and let it run on at least one PR
   so GitHub registers the check context (the API rejects unknown
   contexts on first apply with a confusing 422).
2. Edit `scripts/apply-branch-protection.sh` and, if the new check
   should apply to ALL protected branches, extend the fallback. If it
   applies to one specific (repo, branch), no script edit is needed:
   the script preserves existing contexts, so all you need is:

   ```bash
   gh api -X PATCH \
     /repos/<owner>/<repo>/branches/<branch>/protection/required_status_checks \
     -f 'contexts[]=existing-1' \
     -f 'contexts[]=existing-2' \
     -f 'contexts[]=new-check'
   ```

   The next `--apply` run will read the new context back, preserve it,
   and re-assert the rest of the policy.
3. Re-run `bash scripts/apply-branch-protection.sh --apply` to refresh
   the audit log.

## Remove a required check (escape hatch)

Permanent removal: edit the workflow, then drop the context from
`scripts/apply-branch-protection.sh` fallback, then re-apply.

Temporary remove (genuine emergency, e.g. CI provider outage):

```bash
gh api -X DELETE /repos/frapercan/<repo>/branches/<branch>/protection
# do the emergency thing
bash scripts/apply-branch-protection.sh --apply
```

The `DELETE` is recorded in the GitHub audit log under the operator's
identity. The follow-up apply is the only legitimate close for the
escape hatch.

## Day-to-day commands

```bash
# Dry-run (default): print the planned API calls without sending them.
bash scripts/apply-branch-protection.sh --dry-run

# Apply for real.
bash scripts/apply-branch-protection.sh --apply

# Confirm enforce_admins on every branch (post-apply spot check).
for repo in PROTEA protea-contracts protea-method protea-sources \
            protea-runners protea-backends protea-reranker-lab \
            agent-farm thesis; do
  for branch in main develop; do
    out=$(gh api "/repos/frapercan/$repo/branches/$branch/protection" 2>/dev/null) || continue
    echo "$repo/$branch: enforce_admins=$(echo "$out" | jq -r '.enforce_admins.enabled')"
  done
done
```

The script appends one TSV line per (repo, branch) to
`state/logs/branch-protection-<date>.log`. Keep the log alongside the
audit markdown for post-incident review.

## Out of scope

- `cafaeval-protea` is skipped: it has no `coauthor-guard` workflow, so
  setting that as a required check would block every future PR. The
  cafaeval fork is small, low-traffic, and treated as upstream-tracking;
  apply protection manually if the situation changes.
- CODEOWNERS rollout (single maintainer; no team to assign).
- Cross-repo policy automation via GitHub rulesets (deferred until the
  rule set stops changing per repo).

## Related slices

- FARM-1.1 (client-side hooks). Belt-and-braces with this slice.
- FARM-1.1a (server-side co-author CI). The `coauthor-guard / scan` check
  is the canonical required context on every meta-repo `main`.
- FARM-1.3 (PR base enforcement). Complementary: ensures `gh pr create`
  targets the right base; this slice ensures the base cannot be bypassed.
