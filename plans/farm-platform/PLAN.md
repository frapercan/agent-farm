# farm-platform — Plan

Master slice catalog for the agent-farm FREEZE pass + transversal
benchmark. Lives in `agent-farm/plans/farm-platform/` once dropped into
the agent-farm repo; auto-discovered by `plans/render.py` (which walks
any sibling subdir containing a `PLAN.md`, per `render.py:25-28`).

This loop is the union of the four §2 goals from
`context/PLANNING_BRIEF.md`: stabilise development, strengthen UI/UX,
formalise features, transversal benchmark by axis. Every slice cites
concrete evidence (a memory file, a pain-point row, a feature-inventory
entry, an axis-map wiring item) and proposes a STRUCTURAL fix at the
hook / schema / CI-gate / UI layer, not just a prompt sentence.

## Phase semantics

| Phase | Theme | Notes |
|---|---|---|
| F-FARM-1 | Structural stability fixes | One slice per P0/P1 pain-point from `context/stability-pain-points.md`; the common fix family is "git hooks at worktree-create time". |
| F-FARM-2 | Schema + tracking | sqlite extensions (events table, metrics writer, owner-repo column), drift linter, plan-system unification. |
| F-UI | Web dashboard (Option B) | `/en/farm/` routes inside the existing PROTEA Next.js app. Reuses StatusBadge, EventTimeline, FloatingJobsWidget, SystemStatusPill, CommandPalette, cytoscape-dagre. Mobile + tablet via existing playwright config. |
| F-FEAT | Feature consolidation | One slice per `partial` / `aspirational` / orphan feature in `context/feature-inventory.md §12`. |
| F-EXP-RESET | Transversal benchmark | Replace the prior `vN` reranker shorthand with the seven-axis tuple from `context/experiment-axis-map.md`. Re-run grid with paired CIs and a single results table per aspect. |
| F-DATA-PACK | Dataset deliverable | FAIR packaging, provenance docs, manifest schema validation, README+dataset-card per PLM, Zenodo/HF upload for bench-v1-K{3,5,10}-v226-lineage-{plm} family. Pivot deliverable per [[dl-postponed-2026-05-25]]. |

Hard constraints (apply to every slice, inherited from
`~/Thesis2/CLAUDE.md` §4 in the brief):

- NEVER use pgvector for KNN (>500k vectors). Use numpy or FAISS.
- NEVER push to main/develop directly; PR + status checks.
- NEVER `--no-verify`, `--no-gpg-sign`, force-push to main/master, or
  skip pre-commit hooks.
- NEVER `git stash`. Use `git restore` + commit-on-WIP-branch.
- NEVER add "Co-Authored-By: Claude" or any AI mention to commits,
  PRs, or repo prose.
- NEVER add em-dashes to publishable prose (thesis chapters, READMEs,
  papers, ADRs).
- NEVER restart the dev stack without explicit user permission.
- NEVER touch `~/Thesis2/repositories/PROTEA/` from a worktree-running
  agent.
- NEVER use ad-hoc curl/wget to PROTEA endpoints; dispatch via
  `POST /jobs`.
- ALWAYS run local CI (ruff + mypy + pytest + smell-check) BEFORE push.
- ALWAYS check `git status -sb` before any merge/edit/build/restart.

Conductor agent-routing convention: the schema has no `agent:` field,
so each slice's Notes ends with a `Suggested agent:` line; the
conductor picks at spawn time based on `loop` + `tags` + this hint
(per brief §6).

## F-FARM-1 — Structural stability fixes

### FARM-1.1 — Worktree git-hooks bundle (commit-msg + pre-push + pre-commit)

```yaml
id: FARM-1.1
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  scripts/lib/install-hooks.sh installs four hooks into every freshly created worktree
  commit-msg rejects messages matching /co-authored-by:.*claude|anthropic|noreply/i
  pre-push rejects pushes whose ref is refs/heads/main or refs/heads/develop
  pre-push rejects when git stash list is non-empty
  pre-commit runs poetry lock --check when pyproject.toml is staged
  spawn-subagent.sh calls the installer right after git worktree add (today line 82)
  hooks/worktree-create.sh calls the installer right after git worktree add (today line 39)
  unit tests in agent-farm/tests/test_install_hooks.py cover each rejection path
  scripts/lib/README-hooks.md documents the four hooks, escape hatch, and integration points
  prompts/executor.md and prompts/janitor.md point at README-hooks.md as authoritative
estimated_hours: 6
priority: P0
tags: [stability, hook, ci-gate, security]
requires_human: false
```

Shipped 2026-05-16 (PR #19) and re-anchored 2026-05-17 with the
README-hooks.md documentation and prompt pointers. The follow-up
server-side guard is FARM-1.1a (shipped same day in PR #23).
Lessons captured in `feedback_farm_1_1_hook_bypass`: the bundle is
necessary but not sufficient; server-side CI is the real backstop
when an agent commits via `gh api`, `git commit-tree`, or with
hooks uninstalled.

**Goal**: install enforcement at the only layer agents cannot bypass
(the git client they use to push) so the recurring "prompt rule
without enforcement" pattern is killed for five of nine P0-P1 issues
at once.

**Repos touched**: agent-farm.

**Out of scope**:
1. Hook coverage for the developer's main PROTEA clone (covered by
   FARM-1.4).
2. Server-side branch protection (covered by FARM-1.2).
3. GPG-signing enforcement (orthogonal; see observation 2 in
   `context/stability-pain-points.md`).

**Notes**: Cites
`context/stability-pain-points.md` P0-1 (direct push to protected
trunks), P1-1 (`git stash` x5 in one session), P1-2 (Co-Authored-By
slipthrough), P1-5 (poetry.lock regenerate). Common-root-cause
analysis in §"Cross-cutting observations" → "Recurring root causes"
explicitly names this insertion point. Memory:
`feedback_executor_git_stash_pattern.md`, `feedback_git_stash_5x.md`,
`feedback_claude_coauthor_slipthrough.md`,
`feedback_poetry_lock_regenerate.md`,
`project_plugin_push_direct_main_incident.md`. Suggested agent:
executor.

### FARM-1.1a — Server-side coauthor/AI-attribution CI guard

```yaml
id: FARM-1.1a
phase: F-FARM-1
loop: farm-platform
status: done
deps: [FARM-1.1]
acceptance: |-
  A GitHub Actions workflow lives in each of the 8 watched repos (PROTEA,
  protea-contracts, protea-method, protea-sources, protea-runners,
  protea-backends, protea-reranker-lab, agent-farm).
  The workflow runs on every pull_request event, walks every commit
  introduced by the PR, and fails the check if any commit message contains
  (case-insensitive):
    - Co-Authored-By: trailers naming Claude / Anthropic / noreply emails
    - "Generated with Claude" or "by Anthropic" prose attribution
    - bare leading "Claude (Code|Opus|Sonnet|Haiku)" attribution lines
  The workflow is a required check on the default branch protection so a
  red result blocks merge. Memory reference: feedback_farm_1_1_hook_bypass.
estimated_hours: 3
priority: P0
tags: [farm, ci, governance]
requires_human: false
```

Shipped across 8 repos (2026-05-16):
- PROTEA PR #390 (coauthor guard caller)
- protea-contracts PR #13 (guard caller)
- protea-reranker-lab PR #10 (guard caller)
- agent-farm PR #23 (server-side coauthor + AI-attribution PR guard)

Goal: server-side defense against Claude/AI co-author trailer slipthrough that bypassed FARM-1.1's client-side hooks on 2026-05-16 (agent-farm PR #20, PROTEA PR #387). Workflow is reusable across all 8 repos.

### FARM-1.2 — GitHub branch protection on main + develop (8 repos)

```yaml
id: FARM-1.2
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  Branch protection enabled on main and develop for all 8 frapercan/ repos
  Require a pull request before merging, with at least one required status check
  Force-pushes disabled, deletions disabled
  Audit log entry confirms the rule applies to administrators too
  Settings documented in docs/runbook-branch-protection.md
estimated_hours: 2
priority: P0
tags: [stability, security, branch-protection, gh-policy]
requires_human: true
```

Shipped 2026-05-17 via `scripts/apply-branch-protection.sh --apply`:
- 16 (repo, branch) targets protected with `enforce_admins=true`,
  `dismiss_stale_reviews=true`, `allow_force_pushes=false`,
  `allow_deletions=false`, `required_approving_review_count=0`,
  and at least one required status check each.
- Audit: `state/logs/branch-protection-audit-2026-05-17.md`.
- Run log: `state/logs/branch-protection-2026-05-17.log`.
- Runbook: `docs/runbook-branch-protection.md`.
- `cafaeval-protea` deliberately skipped (no `coauthor-guard`
  workflow; requiring it would soft-block every PR; documented in
  the runbook out-of-scope section).
- `agent-farm/develop` and `thesis/develop` absent on GitHub; the
  script skips missing branches gracefully.

**Goal**: server-side enforcement of the PR-only rule. Until this
lands, the worktree pre-push hook (FARM-1.1) is the only barrier and
can be bypassed by editing local hooks. Branch protection is
authoritative.

**Repos touched**: GitHub repo settings for PROTEA, protea-method,
protea-contracts, protea-backends, protea-sources, protea-runners,
protea-reranker-lab, cafaeval-protea.

**Out of scope**:
1. Per-PR review requirement (1 reviewer is enough; the user is sole
   maintainer).
2. CODEOWNERS rollout.

**Notes**: Cites `context/stability-pain-points.md` P0-1 +
`context/memory/project_plugin_push_direct_main_incident.md`
(2026-05-13, plugin repos received chore commits straight on main).
`requires_human: true` because GitHub branch-protection toggles cannot
be reached from a worktree-running agent and the brief mandates no
managed/automated cloud changes. Suggested agent: human (the operator
applies via GitHub UI). Documented in a doc-writer follow-on slice
inside this same loop.

### FARM-1.3 — gh pr create base-branch enforcement

```yaml
id: FARM-1.3
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  prompts/executor.md and prompts/doc-writer.md and prompts/thesis-writer.md show literal "gh pr create --base develop"
  finalize-subagent.sh scans agent heartbeats for PR URLs and runs gh pr view <n> --json baseRefName
  if baseRefName != develop (or main for thesis), finalize emits an error heartbeat and re-bases via gh api PATCH
  test_finalize.py covers the rebase path
estimated_hours: 4
priority: P1
tags: [stability, prompt, gh-policy, ci-gate]
requires_human: false
note: "2026-05-17 janitor audit: all bullets verified in shipped code (finalize-subagent.sh:51-89 + scripts/lib/pr_base.{py,sh} + tests/test_pr_base.py 35 tests)"
```

**Goal**: kill the "gh pr create defaulted to main" class of incident
by combining a literal flag in every prompt example with a finalize
auto-correct that catches the rare slip.

**Repos touched**: agent-farm.

**Out of scope**:
1. Changing the GitHub default branch from main to develop on PROTEA
   (deferred; would ripple across the docs portal links and PR
   templates).

**Notes**: Cites `context/stability-pain-points.md` P1-3 +
`context/memory/feedback_pr_base_develop.md` (3 PRs in one day:
2026-05-13 #352, #356, #357). Suggested agent: executor (script + test
work) plus a doc-writer follow-on for the prompt edits.

### FARM-1.4 — Janitor worktree-only hardening

```yaml
id: FARM-1.4
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  prompts/janitor.md gains an explicit "operate inside $WORKTREE only" section that references the injected variable from spawn-subagent.sh
  ~/Thesis2/repositories/PROTEA/.git/hooks/pre-commit rejects commits whose branch matches ^(task/|feat/T|hookwt/)
  An install-dev-hooks.sh script is shipped under agent-farm/scripts/ and idempotently writes the dev-clone hook
  Conductor bootstrap runs install-dev-hooks.sh once on session start
estimated_hours: 4
priority: P1
tags: [stability, prompt, hook, agent]
requires_human: false
```

**Goal**: stop janitors from accidentally checking out PR branches
inside the developer's main PROTEA clone and leaving the workspace on
the wrong branch.

**Repos touched**: agent-farm. The dev-clone hook lives in
`~/Thesis2/repositories/PROTEA/.git/hooks/` which is gitignored by
design; the installer ships in agent-farm.

**Out of scope**:
1. Catching the inverse case (executor accidentally writing to the
   dev clone) since the executor uses ephemeral worktrees by yaml.

**Notes**: Cites `context/stability-pain-points.md` P1-4 +
`context/memory/feedback_janitor_must_use_worktree.md`
(janitor-1778594859-3177 on PR #330, 2026-05-12). Cross-cutting
observation 5 in stability brief flags that
`~/Thesis2/repositories/PROTEA/` is currently sitting on a misrouted
branch state. Suggested agent: executor.

### FARM-1.5 — Janitor systemic red-check carve-out

```yaml
id: FARM-1.5
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  scripts/janitor-systemic-check.sh pulls gh pr list --state open --json statusCheckRollup, counts identical failures across PRs
  Threshold: 3 or more unrelated PRs failing the same required check classifies the failure as systemic
  Output format: machine-readable JSON plus a one-line human summary for the janitor prompt
  prompts/janitor.md step 1 calls the script and branches: systemic -> escalate to conductor, not systemic -> proceed
  Unit test seeds three fixture PRs with matching failures and asserts systemic=true
estimated_hours: 4
priority: P1
tags: [stability, prompt, ci-gate, agent]
requires_human: false
```

**Goal**: stop the strict-merge deadlock where the janitor queues
every PR (including the fix PR) when a required check is red on
unrelated PRs due to systemic infra issues.

**Repos touched**: agent-farm.

**Out of scope**:
1. Auto-escalation channel beyond a conductor heartbeat (Slack/email
   alerts come later in FARM-UI.7).

**Notes**: Cites `context/stability-pain-points.md` P2-4 +
`context/memory/feedback_janitor_systemic_redcheck_carveout.md`
(2026-05-13 PR #364, 11/12 green but Deploy E2E red on every PR due to
master/main mismatch). Suggested agent: executor.

### FARM-1.6 — Deploy-keeper worktree self-heal

```yaml
id: FARM-1.6
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  protea_redeploy.sh checks [[ ! -d "$DEPLOY_PATH" ]] before the cd at today's line 42
  If missing, runs git -C $REPOS_DIR/PROTEA worktree add "$DEPLOY_PATH" origin/develop and emits an info heartbeat
  Tick proceeds normally after self-heal
  Bash test under tests/test_redeploy_self_heal.sh deletes the worktree and asserts the next tick rebuilds it
estimated_hours: 3
priority: P1
tags: [stability, hook, observability]
requires_human: false
```

**Goal**: make the deploy-keeper tick self-healing so an accidental
worktree removal does not chain into a 30-min supervisor pause.

**Repos touched**: agent-farm.

**Out of scope**:
1. Rewriting the rest of the redeploy logic.

**Notes**: Cites `context/stability-pain-points.md` P2-3 +
`context/memory/feedback_deploy_worktree_bootstrap.md` (2026-05-11
cleanup incident). Suggested agent: executor.

### FARM-1.7 — Postgres data volume audit + restore-test cron

```yaml
id: FARM-1.7
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  inotify or auditd watch on /var/lib/docker/volumes/postgres_data/ logs every container recreate or volume-removal event with invoking PID + cwd to agent-farm/state/logs/volume_audit.log
  deploy-keeper-tick.sh adds a preflight that runs SELECT count(*) FROM pg_tables WHERE schemaname='public' and emits a P0 heartbeat if the count drops to 1 (alembic_version only)
  scripts/restore-drill.sh restores the latest ~/Thesis2/backups/protea-*.dump to a throwaway port (15433), runs a smoke query, and tears down
  cron entry runs the drill weekly and writes the result to state/logs/restore_drill.log
  Runbook docs/runbook-pg-volume-recovery.md links the audit log and the restore drill
estimated_hours: 8
priority: P0
tags: [stability, backup, observability, security]
requires_human: false
```

**Goal**: ensure any future postgres-volume wipe has an attribution
trail and the backups are known-good (not just known-recent).

**Repos touched**: agent-farm. Cron entry installed on the user
workstation (documented in the runbook; not auto-installed since cron
mutations need user permission).

**Out of scope**:
1. Migrating the volume out of Docker (recommended in the
   stability brief as fix b, but high-blast-radius; left to a future
   ADR).
2. Off-host backup replication.

**Notes**: Cites `context/stability-pain-points.md` P0-2 +
`context/memory/project_db_volume_landmine.md` (2026-05-11 01:19 CEST
wipe, root cause unattributed, recovery ~28min then, estimated 60-90
min now). Observation 5 of stability brief flags that
deploy-keeper-supervisor.sh recovery escalation today uses
`--dangerously-skip-permissions` and could in principle re-trigger the
wipe scenario; the audit log makes that detectable. Suggested agent:
executor.

### FARM-1.8 — Untrack thesis.pdf and serve via deploy-keeper

```yaml
id: FARM-1.8
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  One-shot janitor commit on thesis repo: git rm --cached thesis.pdf + add to .gitignore
  Deploy-keeper publishes the rendered PDF on every tick to ~/Thesis2/worktrees/protea-deploy/apps/web/public/thesis.pdf
  protea.ngrok.app/thesis.pdf returns the latest build
  Parallel thesis-writer PRs no longer cascade DIRTY on merge (verified by spawning 3 thesis-writers in parallel against a smoke chapter)
  prompts/thesis-writer.md updated to remove the "commit the PDF" instruction
estimated_hours: 5
priority: P1
tags: [stability, thesis, observability]
requires_human: false
```

**Goal**: unblock the 4-thread parallelism that the
bootstrap-autowork.md framework promises; today every parallel thesis
PR collides on the binary `thesis.pdf` and the user serialises by
hand.

**Repos touched**: thesis (initial untrack), agent-farm (deploy-keeper
publish wiring, prompt edit).

**Out of scope**:
1. Rendering the PDF inside CI instead of at deploy-time.

**Notes**: Cites `context/stability-pain-points.md` P2-1 +
`context/memory/feedback_thesis_pdf_untrack.md` (2026-05-12 cascade
event: after #23 merged, #24-29 went DIRTY simultaneously). Suggested
agent: janitor for the initial untrack, executor for the deploy-keeper
publish wiring, doc-writer for the prompt edit.

### FARM-1.9 — agent-farm .gitignore hygiene

```yaml
id: FARM-1.9
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  agent-farm/.gitignore covers: *.db, state/*.bak-*, state/*.sqlite*, state/logs/, results/*/
  agent-farm/plans/PLAN.md is gitignored (render.py output) OR render.py grows a --check CI gate that fails when the file is dirty
  Live `git status -sb` in agent-farm shows zero spurious untracked files after a fresh clone + init
  CI in agent-farm runs python plans/render.py --check on every PR
estimated_hours: 2
priority: P2
tags: [stability, ci-gate, cleanup]
requires_human: false
```

**Goal**: stop the runtime state polluting the agent-farm git
workspace so the conductor cannot accidentally stage a live sqlite or
the bak snapshot.

**Repos touched**: agent-farm.

**Out of scope**:
1. Migrating runtime state out of the repo entirely.

**Notes**: Cites `context/stability-pain-points.md` P3-3 +
`context/repo-status-snapshot.md` lines 72-76 (live `M plans/PLAN.md`,
`?? agent_farm.db`, `?? state/tasks.sqlite.bak-20260512-094535`).
Suggested agent: executor.

### FARM-1.10 — protea-contracts ALL_FEATURES producer-coverage CI

```yaml
id: FARM-1.10
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  tests/test_feature_producer_coverage.py mocks a minimal dump for every payload-flag combination from FEATURE_FAMILIES
  Asserts produced_columns is a superset of ALL_FEATURES for every combination
  CI workflow in protea-contracts runs the test on every PR that touches ALL_FEATURES or feature_schema.py
  Failure mode: 1-second CI red on the contracts PR, not a 5-hour KNN compute waste downstream
estimated_hours: 6
priority: P1
tags: [stability, schema, ci-gate, lineage]
requires_human: false
note: "2026-05-17 shipped via protea-contracts PR #14 (merged 16:27Z); 128 flag combinations, producer-coverage workflow live"
```

**Goal**: catch canonical-feature drift at PR time on
protea-contracts, not after hours of KNN compute on PROTEA.

**Repos touched**: protea-contracts.

**Out of scope**:
1. Auto-suggesting the producer wiring on the PROTEA side (still a
   manual cross-repo step).

**Notes**: Cites `context/stability-pain-points.md` P2-2 +
`context/memory/project_canonical_feature_producer_consumer.md`
(T-RES.1b added 4 lineage_* columns 2026-05-13; LB.1 v226 failed
after ~5h with `missing=['lineage_is_ancestor_of_known', ...]`).
Suggested agent: executor.

### FARM-1.11 — Deploy-keeper supervisor exponential backoff

```yaml
id: FARM-1.11
phase: F-FARM-1
loop: farm-platform
status: done
deps: []
acceptance: |-
  deploy-keeper-supervisor.sh runs a quick-retry ladder before the existing 30-min PAUSE_AFTER_PAUSE_SEC pause: 30s, 2min, 5min
  Quick retries call only the bash tick (no claude -p escalation) so token cost stays near zero
  Only after 3 consecutive quick-retry failures does the supervisor escalate to claude -p and the 30-min pause
  Test harness: simulated docker-down for 90 seconds; the supervisor recovers on the second quick retry without invoking claude -p
estimated_hours: 4
priority: P2
tags: [stability, observability]
requires_human: false
```

**Goal**: make transient docker/postgres/rabbit hiccups self-recover
in 30 seconds instead of locking the deploy pipeline for 30 minutes.

**Repos touched**: agent-farm.

**Out of scope**:
1. Auto-restarting docker (banned by `prompts/deploy-keeper.md:21`
   and `~/Thesis2/CLAUDE.md`).

**Notes**: Cites `context/stability-pain-points.md` P3-5. Suggested
agent: executor.

## F-FARM-2 — Schema + tracking

### FARM-2.1 — events table for lifecycle audit

```yaml
id: FARM-2.1
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  state/schema.sql gains an events table: id (AI PK), task_id (FK cascade), ts, kind (CHECK in 'spawn','start','end','kill','heartbeat','cleanup'), level, message, payload_json
  Index events(task_id, ts DESC) and events(kind, ts DESC)
  lib/db.py emits an event row from each of: task_insert, task_set_started, task_set_ended, heartbeat, kill, cleanup-mark-crashed
  Migration script state/migrations/001_events.sql applies cleanly to the live tasks.sqlite (which is WAL-mode)
  status.sh --events flag prints the last 50 events across the farm, optionally filtered by --kind / --since
estimated_hours: 6
priority: P1
tags: [schema, observability, dashboard]
requires_human: false
```

**Goal**: append-only audit trail so the operator can answer "what
happened in the last hour across the farm?" without stitching tasks +
heartbeats by `created_at`. Powers the dashboard timeline (FARM-UI.2)
and the alerting webhook (FARM-UI.7).

**Repos touched**: agent-farm.

**Out of scope**:
1. Rewriting heartbeats into events (they coexist; heartbeats remain
   per-task narrative, events are farm-wide lifecycle).

**Notes**: Cites `context/ui-ux-current-state.md` G13 (no lifecycle
event audit trail today). Suggested agent: executor.

### FARM-2.2 — metrics_json writer (tokens, duration, model)

```yaml
id: FARM-2.2
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  finalize-subagent.sh parses the Claude CLI last-turn cost line and writes results.metrics_json with input_tokens, output_tokens, cache_tokens, usd_estimate, duration_seconds, model
  spawn.sh (headless one-shots) similarly captures end-of-run metrics via the claude -p stderr summary
  lib/db.py grows a set-metrics command
  scripts/cost-report.sh aggregates by agent / model / day and prints a table
  Cost shown in status.sh detail view (today shows only summary + sha_before/after)
estimated_hours: 6
priority: P1
tags: [schema, observability, dashboard]
requires_human: false
```

**Goal**: actually populate the `results.metrics_json` column that
schema.sql declared but no writer ever filled. Unlocks the
cost-rollup dashboard panel (FARM-UI.5) and cost_budget enforcement
(FARM-FEAT.8).

**Repos touched**: agent-farm.

**Out of scope**:
1. Pre-spawn budget enforcement (covered by FARM-FEAT.8).
2. Anthropic-console parity (different namespace; we record what the
   CLI surfaces).

**Notes**: Cites `context/ui-ux-current-state.md` G2 + G5 +
`context/feature-inventory.md §12.13` (cost_budget advisory only).
Suggested agent: executor.

### FARM-2.3 — tasks.worktree_owner_repo column

```yaml
id: FARM-2.3
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  state/migrations/002_owner_repo.sql adds tasks.worktree_owner_repo TEXT
  spawn-subagent.sh writes the resolved REPO into the column right after worktree creation (today line 82)
  finalize-subagent.sh consults the column instead of scanning repositories/*/.git + thesis/.git
  Worktree-removal path in cleanup.sh and kill.sh uses the column when present, falls back to scan when null
  Benchmark: finalize teardown drops from O(repos x worktrees) to O(1) per task
estimated_hours: 4
priority: P2
tags: [schema, cleanup]
requires_human: false
```

Shipped 2026-05-17 (combined with FARM-2.4 because they share the
spawn/finalize integration surface).
- Migration `state/migrations/002_task_metadata.sql` adds the column;
  idempotent via the new `scripts/lib/apply_migrations.py` helper, which
  guards each statement with a `PRAGMA table_info()` precondition.
- `state/schema.sql` carries the column inline for fresh inits.
- `db.py set-worktree-owner-repo` writes the column without emitting
  an event row (plumbing, not lifecycle).
- `spawn-subagent.sh` records the owner immediately after
  `git worktree add`.
- `finalize-subagent.sh`, `cleanup.sh`, and `kill.sh` consult the
  column for O(1) teardown and fall back to the legacy scan when the
  column is null or stale.
- Benchmark `tests/test_finalize_lookup_perf.py` showed about 10x
  speedup on a 3-repo / 15-worktree fixture (scan ~23ms vs column
  ~2.5ms).

**Goal**: replace the every-teardown owner-repo scan with a recorded
column populated at create time.

**Repos touched**: agent-farm.

**Out of scope**:
1. Back-filling the column for historical tasks (left null; the scan
   fallback handles them).

**Notes**: Cites `context/stability-pain-points.md` cross-cutting
observation 4 + `context/feature-inventory.md §8.4`
(owning-repo discovery scans every repo). Suggested agent: executor.

### FARM-2.4 — populate results.sha_before / sha_after

```yaml
id: FARM-2.4
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  spawn-subagent.sh writes results.sha_before = git -C $WORKTREE rev-parse HEAD right after worktree creation
  finalize-subagent.sh writes results.sha_after = git -C $WORKTREE rev-parse HEAD right before teardown
  status.sh detail view shows both fields when populated
  Backward-compatible: null fields still render gracefully
estimated_hours: 3
priority: P2
tags: [schema, observability]
requires_human: false
```

Shipped 2026-05-17 (combined PR with FARM-2.3).
- `db.py set-sha <task> before|after <sha>` upserts the results row
  preserving sibling columns (summary, metrics_json).
- `spawn-subagent.sh` captures `git rev-parse HEAD` straight after
  `git worktree add` so sha_before is non-null for every fresh task.
- `finalize-subagent.sh` captures HEAD just before the teardown block;
  if the worktree directory is already gone, sha_after stays null and
  status.sh renders `(unset)`.
- The pre-existing `INSERT OR REPLACE INTO results(...summary...)` in
  finalize was changed to a proper UPSERT so it no longer blanks
  sha_before / metrics_json on its way through.
- `status.sh <task>` adds an `owner_repo` row and a combined
  `SHA: <before> -> <after>` line; null columns render gracefully.

**Goal**: make the executor-trail introspectable. Schema declares
both columns but no writer fills them today.

**Repos touched**: agent-farm.

**Out of scope**:
1. Linking sha_after to a PR URL (separate slice could derive via
   gh api; not in this freeze).

**Notes**: Cites `context/feature-inventory.md §3.4` + §12.12
(sha_before/sha_after schema-defined, never written). Suggested
agent: executor.

### FARM-2.5 — Read deploy-keeper poll_interval from yaml

```yaml
id: FARM-2.5
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  deploy-keeper-supervisor.sh parses service.poll_interval from agents/deploy-keeper.yaml (5m -> 300, 30s -> 30)
  Hardcoded POLL_INTERVAL_SEC=300 removed
  Test: change yaml to 60s, restart supervisor, assert next tick fires within 65s
  _template.yaml documentation updated to reflect that the field is now load-bearing
estimated_hours: 2
priority: P3
tags: [schema, observability]
requires_human: false
```

**Goal**: make declarative yaml fields actually drive behaviour
instead of being decorative.

**Repos touched**: agent-farm.

**Out of scope**:
1. Reading other yaml `service.*` fields (covered by FARM-FEAT.4 for
   triggers).

**Notes**: Cites `context/feature-inventory.md §6.1` + §12.7
(supervisor hardcodes 300 ignoring yaml). Suggested agent: executor.

### FARM-2.6 — Memory-to-prompt drift linter

```yaml
id: FARM-2.6
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  scripts/memory-prompt-drift.py scans context/memory/feedback_*.md + project_*.md for "How to apply" blocks
  Regex-detects the verbs: "the prompt must", "update prompts/", "fold into prompts/"
  For each match, greps the named prompt file and reports stale entries (memory says X, prompt does not contain X)
  Output: machine-readable JSON + a one-line human summary
  Conductor bootstrap (bootstrap-autowork.md) calls it on session start and surfaces the count
  Test fixture: a memory file says "the prompt must include FOO"; the linter reports 1 stale entry when prompts/janitor.md lacks FOO
estimated_hours: 6
priority: P2
tags: [schema, lint, prompt, observability]
requires_human: false
```

Shipped 2026-05-17 (PR). `scripts/memory-prompt-drift.py` (~175 LOC)
scans the real memory dir against `prompts/`. Smoke run on
2026-05-17: 0 stale entries across 28 memory files. Boot sequence
step added to `prompts/bootstrap-autowork.md`. 17 unit tests covering
all heading styles, file-reference pairing, all-prompts fallback, JSON
mode, and robustness.

**Goal**: convert the latent "rule lives only in memory" class
(P1-4, P2-4, P3-2 today) into a mechanical check the conductor runs
once per session.

**Repos touched**: agent-farm.

**Out of scope**:
1. Auto-folding memory entries into prompts (that is what the
   doc-writer agent does, manually, after the linter flags drift).

**Notes**: Cites `context/stability-pain-points.md` top-5 fix #5
(memory-to-prompt drift linter) + cross-cutting observation 6.
Suggested agent: executor.

### FARM-2.7 — Bridge the two plan systems

```yaml
id: FARM-2.7
phase: F-FARM-2
loop: farm-platform
status: done
deps: []
acceptance: |-
  scripts/lib/plan_parser.py reads plans/<loop>/PLAN.md as the canonical source (today walks the external §24 memory file)
  --json output keys remain stable so existing dashboards do not break
  plan-progress.sh --next picks across all loops, including farm-platform
  prompts/executor.md updated: "slice + phase spawn_args reference the internal store under plans/<loop>/PLAN.md"
  prompts/shepherd.md similarly updated
  External §24 memory file no longer linked from any prompt or script
estimated_hours: 6
priority: P1
tags: [schema, prompt, docs]
requires_human: false
```

**Goal**: collapse two parallel plan systems (internal `plans/` store
versus external §24 master plan) into a single canonical store. Today
executor reads the external memory file; render.py + plan-progress.sh
diverge.

**Repos touched**: agent-farm.

**Out of scope**:
1. Migrating historical content from the §24 memory file (it is
   superseded; the internal store already has 106 slices across 4
   loops plus this one).

**Notes**: Cites `context/feature-inventory.md §4.1` + §12.8 (two
plan systems unbridged) + `context/ui-ux-current-state.md` G15 (plan
editing surface). Suggested agent: executor for the parser changes,
doc-writer for the prompt edits.

## F-UI — Web dashboard (Option B)

Decision: **Option B** from `context/ui-ux-current-state.md` "web
dashboard inside the existing PROTEA Next.js app". Rationale: only
option whose row in the gap-comparison table is ✅ for G7 (phone
access) and G8 (mobile-friendly), both explicit §3 requirements
(operator opens the dashboard from a phone). Reuses 17 existing
PROTEA components and the playwright mobile/tablet config. Read +
write but write-affordances gated by existing AuthChip middleware.

### FARM-UI.1 — farm-api FastAPI sidecar

```yaml
id: FARM-UI.1
phase: F-UI
loop: farm-platform
status: done
deps: [FARM-2.1, FARM-2.2]
acceptance: |-
  apps/farm-api/ FastAPI service exposes: GET /tasks (list with filters by status/agent/since), GET /tasks/{id}, GET /tasks/{id}/heartbeats, GET /tasks/{id}/results, GET /events (since, kind), GET /plan (per loop), GET /cost (rollup by agent/day/model), GET /worktrees (du-aware)
  All endpoints are read-only by default; write endpoints (spawn, kill, cleanup) gated by an explicit FARM_API_WRITE=1 env flag plus auth header
  Reads agent-farm/state/tasks.sqlite directly (WAL-safe; read-only connection)
  OpenAPI spec auto-generated at /openapi.json; runbook docs/runbook-farm-api.md documents the auth model
  Pytest suite covers each endpoint with a fixture sqlite
estimated_hours: 10
priority: P1
tags: [ui, api, dashboard]
requires_human: false
```

**Goal**: provide the backend the Next.js farm pages call. Sidecar
runs alongside the PROTEA app on the same docker-compose so ngrok
already covers it.

**Repos touched**: agent-farm (new `apps/farm-api/` package),
PROTEA (docker-compose entry).

**Out of scope**:
1. Write endpoints (covered by FARM-UI.6).
2. WebSocket / SSE log streaming (the `/events` polling endpoint is
   the v1 surface; SSE is a follow-on).

**Notes**: Cites `context/ui-ux-current-state.md` Option B "Server-
side: a thin FastAPI endpoint exposing listTasks / getTask /
getHeartbeats / getResults / getPlan". Depends on FARM-2.1 (events
table) + FARM-2.2 (metrics writer) for the `/events` and `/cost`
endpoints. Suggested agent: executor.

```
ASCII surface sketch:
  GET /tasks?status=running&since=24h
  -> [ {id, agent_name, kind, status, model, started_at,
        worktree, tmux_window, sha_before, sha_after,
        cost_usd, duration_s} ... ]
  GET /events?kind=heartbeat&level=error&since=1h
  -> [ {ts, task_id, kind, level, message, payload} ... ]
```

### FARM-UI.2 — /en/farm/ routes (list + detail)

```yaml
id: FARM-UI.2
phase: F-UI
loop: farm-platform
status: done
deps: [FARM-UI.1]
acceptance: |-
  apps/web/app/[locale]/farm/page.tsx renders the task list with status filter (useUrlParam) + agent filter + 24h/7d windows
  apps/web/app/[locale]/farm/[task_id]/page.tsx renders the detail view: status badge, sha_before/after, worktree path, last 50 heartbeats via EventTimeline, results.summary
  Strings backed by messages/{en,es,de,pt,zh}.json for the 5 locales
  Reuses StatusBadge.tsx (add 'killed' and 'crashed' to its vocabulary), EventTimeline.tsx, Skeleton.tsx, Toast.tsx
  Existing locale middleware gates the route, AuthChip surfaces user identity
  Playwright e2e at viewport 375x667 + 1280x800 in apps/web/e2e/farm-list.spec.ts
estimated_hours: 8
priority: P1
tags: [ui, frontend, dashboard, mobile]
requires_human: false
```

**Goal**: read-only farm dashboard reachable from a phone via the
existing ngrok tunnel.

**Repos touched**: PROTEA (apps/web).

**Out of scope**:
1. Write affordances (covered by FARM-UI.6).
2. Slice DAG visualisation (FARM-UI.4).

**Notes**: Cites `context/ui-ux-current-state.md` "Existing reusable
UI infrastructure" + G7 (remote/browser access) + G8 (mobile-friendly
read-only status). StatusBadge.tsx already covers queued / running /
succeeded / failed / cancelled; we add `killed` and `crashed` from
the farm vocabulary. Suggested agent: frontend-designer.

```
ASCII sketch of /en/farm/ list (mobile):
  [PROTEA logo] [AuthChip]
  ----------- farm tasks -----------
  filter: [status v]  [agent v]  [24h v]
  [Floating jobs pill: 3 running]
  ----------------------------------
   exec-1715... ✅ executor opus  2026-05-16 12:03  4m02s  $0.12
   janitor-... ⏳ janitor haiku   2026-05-16 11:57  --     --
   bioinfo-... ❌ bioinfo sonnet  2026-05-16 09:12  18m    $0.91
```

### FARM-UI.3 — FloatingJobsWidget + SystemStatusPill for farm

```yaml
id: FARM-UI.3
phase: F-UI
loop: farm-platform
status: done
note: "shipped via PROTEA PR #409 (2026-05-18)"
deps: [FARM-UI.1, FARM-UI.2]
acceptance: |-
  apps/web/components/FarmJobsWidget.tsx (cloned from FloatingJobsWidget.tsx) polls /api/farm/tasks?status=running every 10s, visibility-aware
  apps/web/components/FarmStatusPill.tsx (cloned from SystemStatusPill.tsx) shows health dot (green/amber/red) + running count + recent error count
  Both mounted in the global layout (visible on every page once the user is in the /farm/ section)
  Mobile-tested at 390x844 (existing playwright profile)
estimated_hours: 5
priority: P2
tags: [ui, frontend, dashboard, observability]
requires_human: false
```

**Goal**: at-a-glance farm health from any page in the app.

**Repos touched**: PROTEA (apps/web).

**Out of scope**:
1. Desktop notifications (separate browser API; not in scope).

**Notes**: Cites `context/ui-ux-current-state.md` "Existing reusable
UI infrastructure" (FloatingJobsWidget 119 LOC, SystemStatusPill 130
LOC) + G12 (real-time heartbeat dashboard). Suggested agent:
frontend-designer.

### FARM-UI.4 — /en/farm/plan/ slice-DAG view

```yaml
id: FARM-UI.4
phase: F-UI
loop: farm-platform
status: done
note: "shipped via PROTEA PR #410 (2026-05-18)"
deps: [FARM-UI.1, FARM-UI.2]
acceptance: |-
  apps/web/app/[locale]/farm/plan/page.tsx renders a cytoscape-dagre DAG of all slices from /api/farm/plan
  Node colour encodes status (uses STATUS_GLYPH mapping from render.py); edges encode deps
  Hover shows id + priority + estimated_hours + acceptance summary
  Filter chips: by loop, by phase, by priority, by status
  Critical-path highlight: longest dep-chain from a pending root to a pending leaf
  Reuses GoGraph.tsx layout patterns (cytoscape 3.33 + cytoscape-dagre 2.5 already in package.json)
estimated_hours: 8
priority: P2
tags: [ui, frontend, dashboard, lint]
requires_human: false
```

**Goal**: visualise dependencies instead of reading flat YAML.

**Repos touched**: PROTEA (apps/web).

**Out of scope**:
1. Plan editing UI (covered by FARM-FEAT.11 docs surface; full edit
   stays in the per-loop PLAN.md files).

**Notes**: Cites `context/ui-ux-current-state.md` G3 (plan-progress
visualization) + GoGraph.tsx as the existing cytoscape-dagre anchor
(333 LOC). Suggested agent: frontend-designer.

### FARM-UI.5 — Cost-per-day rollup panel

```yaml
id: FARM-UI.5
phase: F-UI
loop: farm-platform
status: done
note: "shipped via PROTEA PR #412 (2026-05-18) + agent-farm PR #77 (2026-05-18)"
deps: [FARM-UI.1, FARM-2.2]
acceptance: |-
  apps/web/app/[locale]/farm/cost/page.tsx shows cost rollup
  Three views: by agent (bar), by model (stacked area, last 30d), by day (line, last 60d)
  Numbers consume /api/farm/cost grouped by the chosen axis
  Compare-to-budget overlay (the cost_budget.max_usd_per_day from each agent yaml)
  Mobile-tested at 390x844
estimated_hours: 6
priority: P2
tags: [ui, frontend, dashboard, observability]
requires_human: false
```

**Goal**: turn the hypothetical docs/token-savings.md numbers into a
verifiable live panel.

**Repos touched**: PROTEA (apps/web).

**Out of scope**:
1. Pre-spawn cost prediction (advisory; not a hard gate).

**Notes**: Cites `context/ui-ux-current-state.md` G2 + G5 +
`context/feature-inventory.md §9.6` (daily budget table). Depends on
FARM-2.2 metrics writer to have populated metrics_json for at least a
week of historical tasks before the panel reads non-empty. Suggested
agent: frontend-designer.

### FARM-UI.6 — CommandPalette farm verbs (auth-gated)

```yaml
id: FARM-UI.6
phase: F-UI
loop: farm-platform
status: done
note: "shipped via agent-farm PR #71 (2026-05-18) + PROTEA PR #411 (2026-05-18)"
deps: [FARM-UI.1, FARM-UI.2]
acceptance: |-
  apps/web/components/CommandPalette.tsx gains a "farm:" namespace with verbs: spawn next pickable, kill <task>, cleanup --apply, view task <id>
  Each verb produces a fetch to /api/farm/<endpoint>; write verbs require an authenticated session via existing AuthChip middleware
  Unauthenticated users see the verbs as disabled with an "auth required" tooltip
  Spawn-next-pickable invokes the equivalent of plan-progress.sh --next plus the spawn command directly via /api/farm/spawn
  e2e test at apps/web/e2e/farm-palette.spec.ts: simulate authed user, run "farm: spawn next pickable", assert a new task row appears
estimated_hours: 8
priority: P2
tags: [ui, frontend, dashboard, security]
requires_human: false
```

**Goal**: take the operator out of the "manually paste JSON spec"
loop for routine spawns.

**Repos touched**: PROTEA (apps/web), agent-farm (write endpoints in
the FastAPI sidecar).

**Out of scope**:
1. Editing slice YAML from the UI (deferred).

**Notes**: Cites `context/ui-ux-current-state.md` G11 (plan-aware
spawn helper) + CommandPalette.tsx (313 LOC, extensible). Suggested
agent: frontend-designer (UI) + executor (write endpoints).

### FARM-UI.7 — Heartbeat error alerting via Grafana / Slack

```yaml
id: FARM-UI.7
phase: F-UI
loop: farm-platform
status: done
note: "shipped via PROTEA PR #413 + agent-farm PR #80 (2026-05-18)"
deps: [FARM-2.1]
acceptance: |-
  Loki-docker-driver added to the agent-farm tmux session (or a sidecar that tails state/tasks.sqlite events)
  Grafana 11.3 dashboard agent-farm-heartbeats.json provisioned under deploy/grafana/dashboards/
  Alert rule: 3 or more error-level events in 5 minutes -> Slack webhook (existing T5.3 stack already has webhook plumbing)
  Webhook payload includes task_id, agent_name, message, link to /en/farm/<task_id> in the dashboard
  Test: spawn a synthetic task that emits 5 error heartbeats; assert Slack receives 1 alert (rate-limited by Grafana)
estimated_hours: 5
priority: P2
tags: [ui, observability, alerting]
requires_human: false
```

**Goal**: surface heartbeat errors outside the tmux session so the
operator notices without opening status.sh.

**Repos touched**: PROTEA (deploy/grafana), agent-farm (event tail
wiring).

**Out of scope**:
1. Email alerting (Slack is the user's primary channel).

**Notes**: Cites `context/ui-ux-current-state.md` G6 (alerting hooks)
+ "Grafana / Loki monitoring sidecar (T5.3, already shipped)".
Suggested agent: executor.

### FARM-UI.8 — Mobile + tablet playwright suite for /en/farm/

```yaml
id: FARM-UI.8
phase: F-UI
loop: farm-platform
status: done
note: "shipped via PROTEA PR #414 + agent-farm PR #81 (2026-05-18)"
deps: [FARM-UI.2, FARM-UI.3, FARM-UI.4, FARM-UI.5]
acceptance: |-
  apps/web/e2e/farm-mobile.spec.ts covers /en/farm/, /en/farm/<id>/, /en/farm/plan/, /en/farm/cost/ at viewport 390x844 (existing mobile profile)
  apps/web/e2e/farm-tablet.spec.ts mirrors the same at 768x1024 (existing tablet profile)
  Screenshots land under apps/web/e2e/screenshots/farm-{mobile,tablet}-*.png
  The existing playwright-platform agent runs both specs against https://protea.ngrok.app/ on schedule
  Failures emit a heartbeat (level=warn) into the new events table
estimated_hours: 4
priority: P2
tags: [ui, e2e, mobile, frontend]
requires_human: false
```

**Goal**: keep the farm dashboard mobile-stable; the PROTEA app
already has 10 mobile screenshots covering jobs / proteins /
annotations.

**Repos touched**: PROTEA (apps/web/e2e).

**Out of scope**:
1. Chromium-other-browser coverage (existing playwright config is
   chromium-only by choice).

**Notes**: Cites `context/ui-ux-current-state.md` "Playwright
scaffolding" + G8. Suggested agent: frontend-designer (write specs),
playwright-platform (run).

### FARM-UI.9 — ux-reviewer audit of farm dashboard

```yaml
id: FARM-UI.9
phase: F-UI
loop: farm-platform
status: pending
deps: [FARM-UI.2, FARM-UI.3, FARM-UI.4, FARM-UI.5, FARM-UI.6]
acceptance: |-
  ux-reviewer agent runs against /en/farm/ surfaces with scope "P0+P1" audit dimensions: hierarchy, scanability, navigation, cognitive load, mobile, performance, accessibility
  Output written to results/<task_id>/audit.md as the standard ux-reviewer findings list
  Findings categorised P0/P1/P2; frontend-designer follow-on slice picks the P0/P1 set for fix-up
  Lighthouse + Playwright accessibility checker results captured
estimated_hours: 3
priority: P3
tags: [ui, ux-audit, frontend]
requires_human: false
```

**Goal**: validate the farm dashboard against the same 7-dimension
review the PROTEA platform passes.

**Repos touched**: agent-farm (results dir).

**Out of scope**:
1. Implementing the findings (a follow-on frontend-designer slice
   after this audit lands; not pre-declared here since the findings
   list does not exist yet).

**Notes**: Cites `context/feature-inventory.md §1.8` (ux-reviewer
audit dimensions). Suggested agent: ux-reviewer.

## F-FEAT — Feature consolidation

### FARM-FEAT.1 — Materialise /agent-farm-* slash commands

```yaml
id: FARM-FEAT.1
phase: F-FEAT
loop: farm-platform
status: done
deps: []
acceptance: |-
  ~/.claude/commands/agent-farm-conductor.md, -agents.md, -spawn.md, -status.md, -kill.md, -cleanup.md, -plan.md ship as small markdown files matching the project's slash-command template
  Each command runs the underlying scripts/*.sh from the agent-farm root
  /agent-farm-conductor loads prompts/conductor.md plus prompts/bootstrap-autowork.md
  /agent-farm-plan delegates to plan-progress.sh
  README.md updated to remove the "aspirational" caveat on the slash-command table
estimated_hours: 3
priority: P2
tags: [docs, agent, prompt]
requires_human: false
```

**Goal**: convert the documented-but-aspirational slash commands into
real registered commands.

**Repos touched**: agent-farm (templates land here; the user's
`~/.claude/commands/` is filled by a one-shot copy step documented in
the README).

**Out of scope**:
1. Plugin packaging (the user is the sole consumer; no plugin needed).

**Notes**: Cites `context/feature-inventory.md §5` (all 7 slash
commands aspirational). Suggested agent: doc-writer.

### FARM-FEAT.2 — Declarative ephemeral worktree for headless one-shots

```yaml
id: FARM-FEAT.2
phase: F-FEAT
loop: farm-platform
status: done
deps: []
acceptance: |-
  spawn.sh resolves worktree.repo / worktree.base_branch / worktree.cleanup from the agent yaml for kind=headless persistent=false
  Creates ~/Thesis2/worktrees/<task_id>/ if cleanup != none, mirroring spawn-subagent.sh:73-87
  embeddings-runner consumes the created worktree path via the existing composed_prompt mechanism
  TODO comment at spawn.sh:66-69 ("Future: make worktree creation declarative via spec.repo") removed
  Test: spawn embeddings-runner with cleanup=ephemeral, assert worktree exists during run and is removed by finalize
estimated_hours: 4
priority: P2
tags: [agent, schema, cleanup]
requires_human: false
```

**Goal**: remove the last "deferred to the agent" worktree TODO.

**Repos touched**: agent-farm.

**Out of scope**:
1. Per-action worktree mode for headless agents (covered by
   FARM-FEAT.3).

**Notes**: Cites `context/feature-inventory.md §12.4` + §7.1
(embeddings-runner worktree creation deferred). Suggested agent:
executor.

### FARM-FEAT.3 — Decide on per_action cleanup mode

```yaml
id: FARM-FEAT.3
phase: F-FEAT
loop: farm-platform
status: done
deps: []
acceptance: |-
  ADR docs/decisions/D31-per-action-worktree.md decides: adopt for deploy-keeper OR delete the mode from _template.yaml
  If adopt: deploy-keeper-supervisor.sh creates a fresh worktree per tick and removes it post-tick
  If delete: _template.yaml stops listing per_action; cleanup.sh special-case removed
  Either way, no aspirational mode lingers undocumented
estimated_hours: 3
priority: P3
tags: [agent, docs, cleanup]
requires_human: false
```

**Goal**: stop documenting a feature no agent uses.

**Repos touched**: agent-farm.

**Out of scope**:
1. Building a per_action option for non-deploy agents.

**Notes**: Cites `context/feature-inventory.md §8.2` + §12.5
(per_action documented but no agent uses it). Suggested agent:
executor (decision + edit) plus doc-writer for the ADR.

Resolution (2026-05-18): ADR
`docs/decisions/D31-per-action-worktree.md` chose the delete path.
`agents/_template.yaml` now documents two canonical modes
(`ephemeral`, `none`); the `per_action` line is removed and a back
reference to D31 sits in its place. `docs/features/cleanup-modes.md`
flipped from `state: partial` to `state: working` and lists both
production-tenant modes plus the agents that use each. No script
required editing: `scripts/spawn.sh`, `scripts/spawn-subagent.sh` and
`scripts/finalize-subagent.sh` already treated `cleanup != "none"` as
the single ephemeral path, and `scripts/cleanup.sh` only reads the
value to populate the protected-paths set, so the acceptance line
about `cleanup.sh special-case removed` was vacuous (the special-case
never existed in code). Eleven non-template agent yamls audited; all
declare either `ephemeral` or `none`, so no agent migration was
needed.

### FARM-FEAT.4 — Wire deploy-keeper service.triggers

```yaml
id: FARM-FEAT.4
phase: F-FEAT
loop: farm-platform
status: done
deps: [FARM-2.5]
acceptance: |-
  deploy-keeper-supervisor.sh implements new_commit_on:origin/develop via a lightweight git fetch + rev-parse loop (no polling, runs every 60s in addition to the yaml poll_interval)
  Implements ngrok_tunnel_down via curl -sfI https://protea.ngrok.app/ with backoff
  manual trigger surfaces as a tmux send-keys hook the conductor can fire from the dashboard CommandPalette
  yaml triggers field becomes load-bearing rather than human-readable
  Bash test simulates a new commit and asserts the tick fires within 90s independent of the poll_interval
estimated_hours: 6
priority: P2
tags: [agent, observability, schema]
requires_human: false
```

**Goal**: deliver on the yaml contract; today the field is
documentation only.

**Repos touched**: agent-farm.

**Out of scope**:
1. Watching the GitHub events API directly (the local-fetch pattern
   is enough and keeps the supervisor offline-tolerant).

**Notes**: Cites `context/feature-inventory.md §6.1` + §12.6
(supervisor only implements time-based polling). Suggested agent:
executor.

Resolution (2026-05-18): supervisor reads `service.triggers` via
`yaml_get`, dispatches `new_commit_on:<ref>` (lightweight git fetch +
rev-parse, armed on first sighting), `ngrok_tunnel_down` (curl -sfI
with `NGROK_BACKOFF_SEC` floor), and `manual` (marker file consumed
between ticks). New script `scripts/services/deploy-keeper-trigger.sh`
writes the marker file and, when reachable, nudges the deploy-keeper
tmux window via `send-keys` so an attached operator sees the fire.
Trigger evaluation runs on a `TRIGGER_CHECK_INTERVAL_SEC` cadence
(default 60s) inside `nap_with_triggers`, independent of the yaml
`poll_interval`. Bash test `tests/test_deploy_keeper_triggers.sh`
covers all three trigger kinds plus the trigger-script smoke; the
new-commit and ngrok cases assert the early tick fires at virtual
t<=90s with a 3600s poll_interval. CommandPalette wire-up (the
`farm: deploy-keeper trigger` verb) is deferred to FARM-UI.6, which
will shell out to `deploy-keeper-trigger.sh` via the existing
`/spawn` / writes router pattern.

### FARM-FEAT.5 — Resolve dangling lab-runner plan loop

```yaml
id: FARM-FEAT.5
phase: F-FEAT
loop: farm-platform
status: done
deps: []
acceptance: |-
  EITHER: agents/lab-runner.yaml + prompts/lab-runner.md added (copy-base from agents/bioinfo-quick.yaml, broader scope: lab benchmark + champion tracking + experiment scheduling), conductor menu updated
  OR: plans/lab-runner/ dir renamed to plans/bioinfo-quick/, render.py picks it up (no code change), all slice loop: fields updated
  Decision documented in docs/decisions/D32-lab-runner-vs-bioinfo-quick.md
  Either path closes the dangling-plan-loop gap
estimated_hours: 4
priority: P1
tags: [agent, docs]
requires_human: false
```

**Goal**: stop the orphan: a plan loop exists but no agent does. The
F-EXP-RESET slices land work on this loop, so the resolution must
happen before the benchmark phase starts.

**Repos touched**: agent-farm.

**Out of scope**:
1. Retraining the conductor on the new agent name (covered by the
   menu update in the same slice).

**Notes**: Cites `context/stability-pain-points.md` observation 7
(`plans/lab-runner/` exists, no agent) + `context/feature-inventory.md
§1.7` (bioinfo-quick is the closest match). Suggested agent: executor.

Resolution (2026-05-16): chose path B per ADR D32. `plans/lab-runner/`
renamed to `plans/bioinfo-quick/`; all 12 slice `loop:` fields updated;
no new agent created.

### FARM-FEAT.6 — Generic persistent-service factory

```yaml
id: FARM-FEAT.6
phase: F-FEAT
loop: farm-platform
status: pending
deps: []
acceptance: |-
  scripts/services/_supervisor-template.sh extracted from deploy-keeper-supervisor.sh: takes TICK_SCRIPT, POLL_INTERVAL, MAX_CONSECUTIVE_FAILURES, PAUSE_AFTER_PAUSE_SEC, FAIL_KIND_ENV_FILE
  deploy-keeper-supervisor.sh becomes a thin sourcing wrapper of the template
  docs/runbook-persistent-service.md walks through "how to add a new persistent service"
  A second persistent service (a placeholder name "queue-watcher") demonstrates the reuse in an example yaml + tick under examples/
estimated_hours: 6
priority: P3
tags: [agent, docs, observability]
requires_human: false
```

**Goal**: the docs already say "the pattern is
deploy-keeper-supervisor.sh, copy it"; convert that to a real factory.

**Repos touched**: agent-farm.

**Out of scope**:
1. Productionising the example queue-watcher.

**Notes**: Cites `context/feature-inventory.md §6.6` + §12.9
(persistent-service skeleton aspirational). Suggested agent:
executor + doc-writer.

### FARM-FEAT.7 — Adopt lib/worktree.sh helpers

```yaml
id: FARM-FEAT.7
phase: F-FEAT
loop: farm-platform
status: pending
deps: []
acceptance: |-
  spawn-subagent.sh, cleanup.sh, kill.sh, finalize-subagent.sh source lib/worktree.sh and call wt_create / wt_remove / wt_changed / wt_cleanup_orphans
  Duplicated worktree-add and worktree-remove logic removed from each caller
  worktree.sh tests under tests/test_worktree.sh cover the four functions
estimated_hours: 5
priority: P3
tags: [cleanup, schema]
requires_human: false
```

**Goal**: kill the parallel implementation. Today lib/worktree.sh is
defined but unused.

**Repos touched**: agent-farm.

**Out of scope**:
1. Rewriting the hook scripts (covered separately if needed).

**Notes**: Cites `context/feature-inventory.md §8.5` + §12.11
(lib/worktree.sh defined but unused). Suggested agent: executor.

### FARM-FEAT.8 — cost_budget enforcement (advisory -> warn-on-overage)

```yaml
id: FARM-FEAT.8
phase: F-FEAT
loop: farm-platform
status: done
note: "shipped via agent-farm PR (FARM-FEAT.8) on 2026-05-18"
deps: [FARM-2.2]
acceptance: |-
  finalize-subagent.sh sums per-agent metrics_json over the rolling 24h window
  If sum exceeds the agent's cost_budget.max_usd_per_day, emit an error-level event and a warn heartbeat on the next spawn
  Conductor bootstrap surfaces overage in the 8-line report
  No hard gate: spawns still succeed; the operator decides
estimated_hours: 4
priority: P3
tags: [observability, schema, agent]
requires_human: false
```

**Goal**: make advisory caps actually advisory (visible) rather than
documentation-only.

**Repos touched**: agent-farm.

**Out of scope**:
1. Hard-gating spawns on budget (rejected; the user prefers warn-only
   per current cost_budget framing).

**Notes**: Cites `context/feature-inventory.md §9.9` + §12.13
(cost_budget advisory only). Depends on FARM-2.2 (metrics writer).
Suggested agent: executor.

### FARM-FEAT.9 — Populate agent-farm/tests/

```yaml
id: FARM-FEAT.9
phase: F-FEAT
loop: farm-platform
status: done
note: "shipped via agent-farm PR #75 (2026-05-18)"
deps: []
acceptance: |-
  tests/test_plan_parser.py covers: phase-header detection, slice-id extraction, json_extract joining, --next fallback
  tests/test_db.py covers: schema init, task lifecycle (insert -> set-started -> set-ended), heartbeat insert
  tests/test_render.py covers: SECTION_RX matching, duplicate-id failure, loop mismatch failure, --check stale detection
  pytest runs cleanly via uv or poetry in CI; ruff + mypy clean
  GitHub Actions workflow .github/workflows/ci.yml runs the test suite on every PR
estimated_hours: 8
priority: P2
tags: [tests, ci-gate]
requires_human: false
```

**Goal**: tests/ exists with only a __pycache__; populate it with real
coverage of the three load-bearing parsers.

**Repos touched**: agent-farm.

**Out of scope**:
1. Coverage targets (no hard threshold; this is the bootstrap).

**Notes**: Cites `context/feature-inventory.md §12.15` (tests dir
empty). Suggested agent: executor.

### FARM-FEAT.10 — cafaeval-protea coverage decision

```yaml
id: FARM-FEAT.10
phase: F-FEAT
loop: farm-platform
status: done
deps: []
acceptance: |-
  ADR docs/decisions/D33-cafaeval-protea-scope.md decides: add cafaeval to janitor scope OR document why excluded
  If add: prompts/janitor.md scope list grows from 7 to 8 repos; CI sweep includes cafaeval-protea
  If exclude: ADR cites the reason (e.g., upstream fork, not actively maintained as PROTEA module)
estimated_hours: 2
priority: P3
tags: [docs, agent]
requires_human: false
```

**Goal**: cafaeval-protea is in `~/Thesis2/repositories/` but never
referenced by any agent; resolve the gap one way or another.

**Repos touched**: agent-farm (prompts), PROTEA (docs/decisions).

**Out of scope**:
1. Migrating cafaeval-protea upstream changes.

**Notes**: Cites `context/feature-inventory.md §10.1` + §12.16
(cafaeval-protea never referenced by any agent). Suggested agent:
doc-writer.

### FARM-FEAT.11 — One-file-per-feature surface under docs/features/

```yaml
id: FARM-FEAT.11
phase: F-FEAT
loop: farm-platform
status: done
note: "shipped via agent-farm PR #73 (2026-05-18)"
deps: []
acceptance: |-
  agent-farm/docs/features/ holds one markdown file per first-class capability listed in context/feature-inventory.md (sections 1-13)
  Each file has: name, source coordinates, state (working/partial/aspirational/undocumented), smoke test (bash one-liner or pytest invocation), runbook link, current owner
  Index docs/features/README.md auto-generated by scripts/render-features-index.sh
  Drift CI gate: scripts/check-features-coverage.sh fails if a new agent / script lands without a corresponding feature page
estimated_hours: 10
priority: P1
tags: [docs, ci-gate]
requires_human: false
```

**Goal**: satisfies §3 "every feature has README + runbook + smoke
test" (a 10/10 documentation requirement). Today the inventory is
read-only audit; this slice converts it into living docs.

**Repos touched**: agent-farm.

**Out of scope**:
1. Pre-existing PROTEA Sphinx docs (separate loop).

**Notes**: Cites `context/PLANNING_BRIEF.md` §3 (documentation 10/10)
+ `context/feature-inventory.md` (140 features inventoried).
Suggested agent: doc-writer.

### FARM-FEAT.12 — Stack-ownership lock for deploy-keeper vs export

```yaml
id: FARM-FEAT.12
phase: F-FEAT
loop: farm-platform
status: done
note: "shipped via agent-farm PR (FARM-FEAT.12) on 2026-05-23"
deps: []
acceptance: |-
  agent-farm/state/stack-owner.json is the single source of truth for who holds the PROTEA dev stack; record shape {owner, task_id, acquired_at, reason} with owner in {free, deploy, export}
  scripts/lib/stack_owner.sh exposes acquire / release / current / status verbs as both a sourceable library and a standalone CLI, file-locked via flock with a bounded timeout (default 5s)
  scripts/services/deploy-keeper-tick.sh checks stack_owner_current at the top of every tick; when owner=export the tick emits a deferred-stack-owned-by-task heartbeat and exits 0 (intentional noop) so the supervisor sleeps the full poll_interval; owner in {free, deploy} proceeds
  docs/runbook-stack-owner-lock.md walks through acquire / release / deploy-keeper integration / operator checks / hard-reset recovery
  tests/test_stack_owner_lock.sh covers two scenarios: (a) acquire export -> tick noops + deferred heartbeat, (b) release export -> tick proceeds; plus bad-input guardrails (reject owner=free, empty task_id, mismatched release exits 3)
estimated_hours: 4
priority: P1
tags: [services, deploy-keeper, lock, coordination]
requires_human: false
```

**Goal**: structural fix for the 2026-05-20 incident where an
auto-spawned deploy-keeper killed an in-flight FARM-EXP.13 export by
silently restarting the stack out from under it (memory:
`feedback_deploykeeper_vs_export_stack_conflict`). The lock is advisory:
the deploy-keeper supervisor CHOOSES to honor it because the two
failure modes are asymmetric (a no-op tick costs nothing, a blind
restart costs hours-to-days of GPU export progress). Per
`project_deploy_keeper_coordination_directive` user mandate.

**Repos touched**: agent-farm.

**Out of scope**:
1. Conductor-side acquire/release wrapper around long-export dispatch
   (separate FARM follow-up, will reuse the same helper).
2. Liveness probe in deploy-keeper (separate from the lock; the lock
   handles "should I tick" while the probe handles "did my last tick
   land").
3. Per-process supervision (no daemon registry; the lock is one JSON
   file + flock).

**Notes**: Cites memory
`project_deploy_keeper_coordination_directive` (user directive
2026-05-22) + `feedback_deploykeeper_vs_export_stack_conflict`
(landmine 2026-05-20) +
`project_deploy_keeper_paused_2026_05_23` (today's incident that
forced the slice). Suggested agent: executor (bash + tests scope).

### FARM-FEAT.13 -- Conductor-side stack_owner_acquire wrapper

```yaml
id: FARM-FEAT.13
phase: F-FEAT
loop: farm-platform
status: done
note: "shipped via agent-farm PR (FARM-FEAT.13) on 2026-05-24"
deps: [FARM-FEAT.12]
acceptance: |-
  scripts/services/lib/dispatch_with_lock.sh wraps any POST /v1/datasets dispatch:
    signature dispatch_with_lock <task_id> <reason> -- <command...>
    acquires stack-owner lock as owner=export under task_id before running command
    releases lock in a trap-EXIT block so lock is always freed even on SIGTERM or command failure
    exits 2 with diagnostic message (current holder task_id + acquired_at) when lock is contended; command is NOT run
  prompts/bioinfo-quick.md has a hard rule: NEVER POST /v1/datasets without dispatch_with_lock
  prompts/conductor.md documents dispatch_with_lock under "Subagent spawn recipe" for ad-hoc export tasks
  tests/test_dispatch_with_lock.sh covers: happy path, failure path (lock released), contended path (exit 2 no-run), missing separator
estimated_hours: 2
priority: P0
tags: [services, deploy-keeper, lock, coordination, conductor]
requires_human: false
```

FARM-FEAT.12 shipped the server-side gate (deploy-keeper tick checks the lock
before redeploying). FARM-FEAT.13 ships the client-side gate: the conductor and
bioinfo-quick now acquire the lock BEFORE dispatching exports, so deploy-keeper
always sees owner=export and defers. The 2026-05-23 17:12 incident happened
because bioinfo-quick posted directly to /v1/datasets without holding the lock;
deploy-keeper saw owner=free and redeployed mid-export, killing the in-flight
EXP.13 training worker (memory: `project_deploy_keeper_paused_2026_05_23`).

The wrapper is a single-file shell library at
`scripts/services/lib/dispatch_with_lock.sh`. It sources
`scripts/lib/stack_owner.sh` (FARM-FEAT.12) and is both sourceable (function
`dispatch_with_lock`) and directly executable as a CLI.

**Repos touched**: agent-farm.

**Out of scope**:
1. Per-cell lock granularity (the current design holds one lock for the full
   export campaign; per-cell would need a queue mechanism).
2. Auto-retry on contention (callers must decide whether to wait or stop; the
   lock gives them the information to make that call).

**Notes**: Cites memory `project_deploy_keeper_paused_2026_05_23`
(2026-05-23 incident) + `feedback_spawn_subagent_wrong_repo` (context on
why conductor-side fixes must be explicit in prompts).
Suggested agent: executor (bash + shell tests scope).

## F-EXP-RESET -- Transversal benchmark

All slices use the axis-tuple form `(plm, k, reranker, features,
eval_set, propagation, ensemble)` from
`context/experiment-axis-map.md §"Proposed orthogonal axes"`. No
slice text uses the prior `vN` reranker shorthand for reranker
versions; GOA snapshot tokens like `v220` / `v226` / `v230` are
legitimate references to external dataset cutoffs and remain.

### FARM-EXP.1 — ExperimentRun axis columns + UNIQUE shortid

```yaml
id: FARM-EXP.1
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: []
acceptance: |-
  PROTEA alembic migration adds columns to ExperimentRun: plm, k, reranker_spec_id, feature_schema_sha, eval_set_name, eval_set_manifest_sha, propagation, ensemble_spec, axis_tuple_shortid
  UNIQUE constraint on axis_tuple_shortid
  shortid = sha256(canonical_json(axis_tuple))[:12] mirroring ExperimentSpec.hash() at protea-reranker-lab/src/protea_reranker_lab/experiment.py:108
  Backfill script populates the new columns from the existing provenance JSONB where derivable
  Lab and PROTEA both consult the same columns when reporting cell membership
estimated_hours: 8
priority: P0
tags: [schema, benchmark, lineage]
requires_human: false
```

Shipped via PROTEA PR #388 (2026-05-16) + protea-contracts PR #12 (canonical
shortid helper). All acceptance criteria met: ExperimentRun has typed axis
columns, UNIQUE constraint on shortid, backfill script populates from provenance
JSONB, both Lab and PROTEA consult the same columns. Out of scope: UI for
browsing by axis (deferred post-FREEZE).

### FARM-EXP.2 — Transversal cell catalog

```yaml
id: FARM-EXP.2
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.1, FARM-FEAT.5]
acceptance: |-
  protea-reranker-lab/experiments/_catalog/transversal.yaml lists every materialised cell as one YAML stanza per cell
  Each stanza carries (plm, k, reranker, features, eval_set, propagation, ensemble) + shortid + status (planned/running/done/superseded)
  scripts/build_study_specs.py extended to emit the catalog from a constrained Cartesian product (axis defaults + one principled sweep per axis)
  Pruning rules applied: drop heuristic alignment_weighted where dominated by lgbm.*, skip feat=knn-only x reranker=lgbm.* (degenerate), skip eval=bench-v1-K5-v226-lineage x feat without lineage (axis-map §"What the transversal re-benchmark would cover")
  Result: ~120 constrained cells written
estimated_hours: 10
priority: P0
tags: [benchmark, schema]
requires_human: false
```

Shipped via protea-reranker-lab PR #11 (2026-05-16). Transversal catalog
generated with 49-cell constrained Cartesian product (down from 512 unconstrained).
Catalog includes axis-tuple shortids, status tracking (planned/running/done/superseded).
Out of scope: running the cells (covered by FARM-EXP.8).

### FARM-EXP.3 — bootstrap_cis.py grouping by axis

```yaml
id: FARM-EXP.3
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.2]
acceptance: |-
  scripts/bootstrap_cis.py grows --group-by plm,k,reranker,features (comma-separated subset)
  Emits per-grouping CSV under outputs/bootstrap_cis/<group_signature>.csv
  Plots: matplotlib violin or paired-CI plot per grouping under outputs/bootstrap_cis/<group_signature>.png
  Test fixture: 6 fake runs across 2 PLMs x 3 K values; assert correct grouping and CI math
estimated_hours: 6
priority: P1
tags: [benchmark, observability]
requires_human: false
```

Shipped via protea-reranker-lab PR #12 (2026-05-16). bootstrap_cis.py
extended with --group-by axis flag, emits per-grouping CSVs and matplotlib
plots. Test fixture validates correct grouping and CI math across 2 PLMs x 3
K values. Out of scope: LaTeX integration (FARM-EXP.11).

### FARM-EXP.4 — Champion tracking auto-updater

```yaml
id: FARM-EXP.4
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.2, FARM-EXP.3]
acceptance: |-
  protea-reranker-lab/champions.md auto-regenerated by scripts/update_champions.py keyed by (eval_set, tier, aspect)
  Each entry carries axis tuple + shortid + CI vs the eval-set baseline + run_id
  Auto-update fires on every run.json that improves an existing champion (CI lower-bound exceeds prior champion's mean)
  Frozen path: champions.md is committed; runs/champion/<eval_set>/<tier>/<aspect>/ symlinks the winning run artefact
estimated_hours: 6
priority: P1
tags: [benchmark, observability]
requires_human: false
```

Shipped via protea-reranker-lab PR #13 (2026-05-16). champions.md now
auto-generated and kept canonical via update_champions.py. Auto-update fires
on every run.json that improves existing champion. Keyed by (eval_set, tier,
aspect) with axis tuple + shortid + CI + run_id. Out of scope: UI surface.

### FARM-EXP.5 — feature_schema_sha guard on PROTEA scoring router

```yaml
id: FARM-EXP.5
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.1]
acceptance: |-
  PROTEA scoring router refuses to load a booster whose recorded feature_schema_sha does not match the current compute_feature_schema_sha()
  Refusal returns a structured error (job status=failed, reason=schema_sha_mismatch) instead of silently producing predictions on the wrong layout
  Unit test seeds a booster with a stale sha and asserts the router rejects it
  Logged into the canonical events table (FARM-2.1) at error level so the dashboard surfaces the rejection
estimated_hours: 6
priority: P1
tags: [schema, benchmark, ci-gate]
requires_human: false
```

Shipped via PROTEA PR #391 (2026-05-16). Scoring router now hard-fails on
feature_schema_sha mismatch with structured error (job status=failed,
reason=schema_sha_mismatch). Unit test validates rejection of stale booster.
Eliminates silent failure mode where booster trained on older FEATURE_FAMILIES
scores against current features. Out of scope: automatic re-training.

### FARM-EXP.6 — Reject vN reranker tokens in publishable prose

```yaml
id: FARM-EXP.6
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: []
acceptance: |-
  scripts/lint-reranker-tokens.py greps publishable surfaces (PROTEA/docs/, thesis/chapters/, READMEs, ADRs) for /\bv\d+\b/ that is NOT a GOA snapshot reference (allowlist: v160, v200, v210, v215, v220, v226, v227, v229, v230)
  Any reranker shorthand of the prior `vN` family (single-digit or low-double-digit tokens outside the GOA allowlist) -> linter emits an error pointing at the file+line and suggests the axis-tuple form
  doc-writer prompt fold: every doc-writer slice runs the linter before pushing
  CI gate in PROTEA + protea-reranker-lab + thesis runs the linter on every PR
estimated_hours: 4
priority: P2
tags: [lint, benchmark, docs, ci-gate, prompt]
requires_human: false
```

Shipped via PROTEA PR #392, protea-reranker-lab PR #14, agent-farm PR #28
(2026-05-16). Reranker-token linter deployed to all 3 repos with CI gate.
lints publishable surfaces for literal vN tokens (outside GOA allowlist),
suggests axis-tuple form. Mechanical enforcement of no-shorthand convention.
Out of scope: auto-rewriting (manual prose sweep).

### FARM-EXP.7 — In-tree eval cell for 8-PLM ensemble

```yaml
id: FARM-EXP.7
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.2]
acceptance: |-
  Catalog adds an axis-tuple stanza: plm=ensemble:8plm-canonical, k=5, rr=none, feat=knn, eval=bench-v1-K5-filtered, prop=tpr_pred, ens=score_mean
  Run produced and stored under runs/transversal/<shortid>/
  Paired CI vs the single-PLM (ESMC-300M) baseline reported per aspect
  Lab Fmax + cafaeval Fmax both captured (decoupled evaluators per lab CLAUDE.md)
estimated_hours: 6
priority: P2
tags: [benchmark, lafa, lineage]
requires_human: false
```

**Goal**: today the 8-PLM ensemble has only LAFA-blind evaluation;
add an in-tree cell on the leakage-free baseline so the ensemble gain
is measurable.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. Score_max ablation (a separate catalog stanza if the user wants
   it).

**Notes**: Cites `context/experiment-axis-map.md §"Wiring needs"` #8
(8-PLM ensemble re-benchmarking blind spot). Suggested agent:
bioinfo-quick.

### FARM-EXP.8 — Constrained 120-cell grid execution

```yaml
id: FARM-EXP.8
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.2, FARM-EXP.3]
acceptance: |-
  scripts/run_transversal_grid.py reads experiments/_catalog/transversal.yaml and schedules cells in batches of 10
  Each batch: PLM embeddings (reused across cells), KNN retrieval, reranker training, cafaeval
  Per-cell run.json written upfront (run_id, resolved hparams, axis tuple, shortid, git sha, artefact paths)
  Champion auto-updater (FARM-EXP.4) runs after every batch
  Estimated wall-clock 5-7 days serial / ~2 days with overlapping GPU+CPU workers per axis-map §"What the transversal re-benchmark would cover"
  Per-cell artefact: booster + predictions parquet + run.json under runs/transversal/<shortid>/
estimated_hours: 16
priority: P1
tags: [benchmark, lineage, observability]
requires_human: false
annotation: "Partial: 9-cell esmc_300m × K=5 grid done; full 120-cell grid requires PLM embedding caches not locally available."
```

**Goal**: execute the constrained grid. This is the largest single
slice in the plan; the batching + run-json-upfront pattern keeps
incremental progress visible.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. The full unconstrained 512-cell Cartesian (pruning rules apply per
   axis-map; the user keeps the ~120 constrained set).
2. Leakage-free re-run of the selective-rerank-at-K-10 cell (covered by FARM-EXP.10).

**Notes**: Cites `context/experiment-axis-map.md §"What the
transversal re-benchmark would cover"` (cell count + compute estimate
+ storage estimate 12-60 GB). Suggested agent: bioinfo-quick.

### FARM-EXP.9a — Orchestration + partial pass on bench-v1-K5-filtered

```yaml
id: FARM-EXP.9a
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.2]
acceptance: |-
  Identify the ~80-100 pre-computed cells on bench-v1-K5 (pre-leakage) per axis-map §"Pre-computed cells in snapshot"
  Ship the partial pass orchestrator (cells_to_rerun.csv, partial_ci.csv, summary.json) so cells trained on the filtered dataset can be aggregated incrementally
  Per-cell run.json + paired CI for the cells that DID complete this pass
estimated_hours: 4
priority: P1
tags: [benchmark, lineage, orchestration]
requires_human: false
note: "Shipped via lab PR #24 (2026-05-18). 25 / 94 cells completed in this pass (all 18 NK+LK replication seeds + 3 pk-bpo seeds + 2 pk-mfo seeds + 2 nk-bpo alignment ablations). Remaining 69 cells live in FARM-EXP.9b."
```

**Goal**: split FARM-EXP.9's code task from the compute task. The
orchestration + summary scripts are shippable now; the bulk compute
moves to FARM-EXP.9b.

**Repos touched**: protea-reranker-lab.

**Notes**: Split decision 2026-05-18 — `[[farm-exp-9-split-needed]]`
memory documents why the original 12 h estimate collapsed under a 4 h
executor budget. Cites `context/experiment-axis-map.md §"Pre-computed
cells in snapshot"` + thesis Tab `tab:improvement` warning that
bench-v1-K5 and bench-v1-K5-filtered rows are not comparable.
Suggested agent: bioinfo-quick.

### FARM-EXP.9b — 69 remaining cells compute pass

```yaml
id: FARM-EXP.9b
phase: F-EXP-RESET
loop: farm-platform
status: done
deps: [FARM-EXP.9a]
acceptance: |-
  Run the remaining 69 cells from FARM-EXP.9a's cells_to_rerun.csv against bench-v1-K5-filtered
  Per-cell run.json with paired CI vs prior pre-leakage run; note that the numbers are NOT comparable to the old bench-v1-K5 cells
  Champion table (FARM-EXP.4) updated where the leakage-free re-run changes the winner
  Pass-2 infrastructure from the developer's local `6342d70` commit (27 hparam specs + standalone runner + summary script) consolidated into a fresh PR off origin/develop
estimated_hours: 90
priority: P1
tags: [benchmark, lineage, compute-long]
requires_human: false
note: "Shipped via lab PR #32 (2026-05-18); harvest summary at experiments/farm_exp_9b/summary.md. Runner completed 94/94 cells (27 rep x 3 seeds + 39 ablations + 27 hparam + 1 standalone). Champion table unchanged (FARM-EXP.5 writer slice required for auto-promoter). Key results on bench-v1-K5-filtered (NOT comparable to v226): NK avg 0.6654, LK avg 0.6590, PK avg 0.2320."
```

**Goal**: actually run the bulk compute that FARM-EXP.9 originally
bundled. Decouples shippable orchestration code (9a) from a 70-100 h
compute job (9b) that cannot fit a normal 4 h executor budget.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. Re-running cells that never trained against ESMC-300M (those land
   in FARM-EXP.8).
2. Champion auto-promotion to `champions.md` — covered by FARM-EXP.4
   acceptance bullet 4 once 9b finishes.

**Notes**: After 9b completes, the chapter-6 results refresh
(FARM-EXP.11) can unblock. Suggested agent: bioinfo-quick with
extended budget, OR a headless one-shot runner spawned via the
new declarative `worktree.repo` mechanism from FARM-FEAT.2.

### FARM-EXP.10 — Selective rerank resurrection: recompute, not archaeology

```yaml
id: FARM-EXP.10
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.2]
acceptance: |-
  Re-train the selective-rerank-at-K=10 cell on bench-v1-K5-v226-lineage (and optionally v230) using the current selective rerank policy
  Store under runs/transversal/<shortid>/ with run.json per F-EXP-RESET layout; pin eval_set_name explicitly
  ADR D34-selective-rerank-resurrection.rst documents why the legacy v18 0.4562 is superseded (range-unknown, leakage-suspected) and what the recomputed champion replaces it
  The legacy memory-only [[project_v18_selective_rerank]] record stays as historical context; the recomputed run becomes the live champion
estimated_hours: 8
priority: P2
tags: [benchmark, lineage, recompute]
requires_human: false
```

**Goal**: replace the memory-only legacy champion (0.4562 avg cafaeval,
leakage-contaminated, range-unknown) with a recomputed record on the
current validation band (bench-v1-K5-v226-lineage).

**Repos touched**: protea-reranker-lab, PROTEA (current selective rerank
policy via live codebase).

**Out of scope**:
1. Resurrecting v4 / v5 / v6 / v7 / v8 rerankers (needs-archaeology
   marks them as does-not-exist unless evidence surfaces; defer).

**Notes**: Decision per ADR D34: when historical records conflict with
current data, recompute on the current bench rather than reverse-engineer
old config. Suggested agent: bioinfo-quick.

### FARM-EXP.11 — Per-aspect results table for thesis chapter 6

```yaml
id: FARM-EXP.11
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.3, FARM-EXP.4, FARM-EXP.8, FARM-EXP.9b]
acceptance: |-
  thesis/chapters/06_evaluation.tex regenerated to use the axis-tuple form throughout (zero vN reranker shorthand)
  Three results tables (one per aspect BPO/MFO/CCO) replace the prior consolidated table
  Each row carries the axis tuple shortid and the paired CI vs the eval-set baseline
  Plots regenerated from outputs/bootstrap_cis/ (FARM-EXP.3)
  Cross-checked against champions.md (FARM-EXP.4) so the in-text champion claims match the table
estimated_hours: 10
priority: P1
tags: [benchmark, thesis, docs]
requires_human: false
```

**Goal**: deliver the chapter 6 refresh that the whole re-benchmark
exists to enable.

**Repos touched**: thesis.

**Out of scope**:
1. Chapter 7 / 8 refresh (separate slices on the thesis-writer loop
   if needed).

**Notes**: Cites `context/PLANNING_BRIEF.md` §3 reproducibility +
`context/experiment-axis-map.md` migration map (worst trap: two
distinct artefacts that shared the same `vN` shorthand label in the
prior thesis text, now disambiguated by axis tuple).
Suggested agent: thesis-writer.

### FARM-EXP.12 — PLM axis explicit in dataset naming

```yaml
id: FARM-EXP.12
phase: F-EXP-RESET
loop: farm-platform
status: done
note: Reconciled to done; work shipped via PROTEA PR #420 + lab PRs #33/#34 (all merged).
deps: [FARM-EXP.2]
acceptance: |-
  ADR D36 (PROTEA) documents the per-PLM dataset naming convention `bench-v1-K{k}-v{val_band}-lineage-{plm_short}` with explicit canonical short keys (esm2_150m, esm2_650m, esm2_3b, prot_t5, prostt5, ankh_base, ankh_large, esmc_600m, esmc_300m)
  Lab repo: rename current `datasets/bench-v1-K5-v226-lineage/` to `datasets/bench-v1-K5-v226-lineage-prostt5/` and update every yaml reference (experiments/_generated/**, experiments/leakage_fix/**, experiments/_catalog/transversal.yaml, scripts/* references) plus all `tags:` lists that mention the old name
  Backward-compat symlink at the old path pointing to `-prostt5` for 1 release cycle, then removed in a follow-up slice
  Existing `Dataset` row in PROTEA renamed via Alembic data-only migration (UNIQUE name constraint forces a single atomic UPDATE); a `Dataset.alias_names` JSONB column added or the old name kept in `Dataset.description` for traceability
  champions.md updated so any axis tuple that referenced the old name now reads the `-prostt5` form
  Pre-commit linter rejects new committed files that contain `bench-v1-K5-v226-lineage` without a `-{plm}` suffix
estimated_hours: 5
priority: P0
tags: [naming, axis, schema, lineage]
requires_human: false
```

**Goal**: the current dataset implicitly encodes ProstT5 as the PLM
but does not name it, which makes the PLM axis invisible and blocks
multi-PLM sweeps. Make the axis explicit at directory + manifest +
Dataset-row level before generating per-PLM siblings.

**Repos touched**: protea-reranker-lab, PROTEA (Alembic +
artifact-store rekeying), thesis (only if it references the old name
inline; FARM-EXP.11 handles the chapter-6 rewrite).

**Out of scope**:
1. Actually building the 7 sibling datasets for the other PLMs
   (covered by FARM-EXP.13).
2. PLM short-name harmonisation in `apps/lafa_knn_8plm/plm_encoders.py`
   (already canonical per `[[project_canonical_8plm_embedding_configs]]`).

**Notes**: Cites memory `[[project_canonical_8plm_embedding_configs]]`
for the PLM short-name list. ADR D36 should reference D35 (the
canonical embedding_config_id audit) and the `c0ae5b69` ProstT5 row.
Suggested agent: executor (PROTEA + lab cross-repo).

### FARM-EXP.13 — Per-PLM dataset family build (8 PLMs × K∈{3,5,10})

```yaml
id: FARM-EXP.13
phase: F-EXP-RESET
loop: farm-platform
status: done
completed: 2026-05-28T12:34:00Z via executor-1779665491-0153
deps: [FARM-EXP.12]
acceptance: |-
  24 datasets emitted via `POST /jobs` operation `export_research_dataset`: one per (plm × K) combination where plm ∈ {esm2_150m, esm2_650m, esm2_3b, prot_t5, prostt5, ankh_base, ankh_large, esmc_600m} and K ∈ {3, 5, 10}
  Each job uses `embedding_config_id` from `[[project_canonical_8plm_embedding_configs]]`, `k` from the K axis, identical `train_versions` / `test_versions` to the current ProstT5 dataset, `output_name` = `bench-v1-K{k}-v226-lineage-{plm}`
  `compute_alignments=true`, `compute_taxonomy=true`, `expand_votes_to_ancestors=true`, `use_embedding_pca=true` for parity with the current `c0ae5b69` build
  All 24 `Dataset` rows present in PROTEA registry with consistent `schema_sha` (PLM-independent feature schema, only `anc2vec_*` + `emb_pca_*` values differ); a per-PLM `parent_schema_sha` is acceptable if the PCA cache forces a re-fingerprint
  Each dataset registers an EvaluationSet pin via `eval_set_name = bench-v1-K{k}-v226-lineage-{plm}`
  Build manifest CSV at `agent-farm/plans/farm-platform/artefacts/farm_exp_13_build_log.csv` with: plm, k, dataset_id, n_train_rows, n_eval_rows, total_seconds, status
  Dispatch waits on `prot_t5` hydration job completion (job_id `b76ad98c-6834-4311-83b6-43dd0721957b` or successor) before scheduling its prot_t5 variants
estimated_hours: 16
priority: P0
tags: [benchmark, lineage, dataset, compute-long]
requires_human: false
```

**Goal**: materialise the per-PLM dataset family that the multi-PLM
sweep consumes. PROTEA's `export_research_dataset` operation already
accepts `embedding_config_id` + `k` + `output_name` as parameters; no
code change required, only orchestration.

**Repos touched**: PROTEA (job dispatch, artifact store, registry),
protea-reranker-lab (consumer parquet pulls in subsequent slices).

**Out of scope**:
1. The `allplm` derived view (FARM-EXP.16 handles multi-manifest at
   training time; no physical concat dataset is produced).
2. Training rerankers on these datasets (FARM-EXP.14).
3. `esmc_300m` baseline dataset (separate optional slice if the user
   wants the legacy single-PLM reference column in the thesis
   chapter-6 table).

**Notes**: Per the dataset-builder audit (2026-05-19, see Explore
report summary in conductor session): `anc2vec_neighbor/query` (6
features) and `emb_pca` (16 features) are the only PLM-specific
families; the other 46 features are PLM-invariant. PCA cache lives
at `protea/artifacts/pca/{embedding_config_id}.npz`, refit per PLM
on first build. Suggested agent: executor (PROTEA dispatch +
artifact-store monitoring); long-running compute pass requires
budget extension or split into batches of 6-8 cells per executor run.

### FARM-EXP.14 — Per-PLM reranker sweep (full binary × lambdarank grid)

```yaml
id: FARM-EXP.14
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.13]
acceptance: |-
  Full single-seed grid: 9 cells × 8 PLMs × 3 K × 2 objectives = 432 reranker runs, where:
    - binary arm = v27-binary recipe (objective=binary, neg_pos_ratio=10, num_boost_round=10000, early_stopping_rounds=100, learning_rate=0.05, num_leaves=63, min_data_in_leaf=100, val_strategy=protein_group, val_fraction=0.2)
    - lambdarank arm = v22-lambdarank recipe (objective=lambdarank, drop_features = anc2vec_* + emb_pca_*, otherwise same hparams as study_v22 baseline)
  Both arms produce runs/transversal/<shortid>/ artefacts with run.json + model.txt + predictions.parquet
  Post-hoc per-cell selection: for each (PLM, K, cell) tuple, the winner among {binary, lambdarank, KNN-only baseline from FARM-EXP.15} is determined by cafaeval Fmax with paired 95% CI vs KNN-only; the loser arms are retained for the full chapter-6 appendix table but excluded from the headline "champion" column
  Multi-seed pass (seeds 42/43/44) ships ONLY on winning cells: a cell qualifies only if its post-hoc reranker champion (binary or lambdarank, regardless of PLM) beats the FARM-EXP.15 KNN-only baseline at 95% paired CI; cells whose winner is the KNN-only baseline (likely the 3 PK cells under current features) get no multi-seed pass since there is no booster to retrain. Upper bound: 3 K × 9 cells = 27 (K, cell) tuples × 2 extra seeds = 54 runs; realistic estimate after PK exclusion: 3 K × 6 cells = 18 tuples × 2 extra seeds = 36 runs
  Champion table (FARM-EXP.4) auto-updates per axis tuple; champions.md lists winners per (eval, aspect, K) split with the objective family explicitly tagged (rr=reranker:v27-binary or rr=reranker:v22-lambdarank or rr=knn-baseline)
  Per-cell paired CI vs FARM-EXP.15 KNN-only baseline at 95% via FARM-EXP.3 bootstrap_cis; an additional paired CI binary-vs-lambdarank reported per cell for the appendix
  Wall-clock estimate logged in run.json: ~10-15 min per binary single-seed run, ~25-30 min per lambdarank single-seed run (lambdarank converges slower at full 13.6M train rows); ~144 h serial total for the full grid; champion multi-seed adds ~12-18 h
  Build manifest CSV at agent-farm/plans/farm-platform/artefacts/farm_exp_14_grid_log.csv with: plm, k, cell, objective, seed, fmax, auprc, smin, wall_seconds, status
estimated_hours: 48
priority: P0
tags: [benchmark, reranker, lineage, compute-long]
requires_human: false
```

**Goal**: compute the full per-(PLM, K, cell, objective) grid so the
post-hoc winner per cell is supported by data on every PLM rather
than extrapolated from the single-PLM ProstT5 verdict in
`runs/SUMMARY_v23-v26.md`. Honest scientific reporting requires both
arms on every cell; the post-hoc selection then justifies the
production deployment policy.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. All-PLM multi-manifest trainer (FARM-EXP.16).
2. Ensemble of per-PLM rerankers (FARM-EXP.17).
3. Per-PLM hyperparameter retuning (assumes the v27-binary and
   v22-lambdarank hparams generalise across PLMs; if a PLM yields
   degraded Fmax under both arms the user can spawn a per-PLM
   tuning follow-up).

**Notes**: Compute budget driver: ~144 h serial single-seed + ~12-18 h
multi-seed champion. Splits cleanly across multiple executor passes
by (PLM, K) batch (24 batches × ~6 h each). Anchored by
`runs/SUMMARY_v23-v26.md` (per-cell ProstT5 verdict; v26-binary wins
5/6 NK+LK, v22-lambdarank wins lk-mfo, PK unreachable by reranking
under either objective on ProstT5) and `[[v27-binary-multiseed-2026-05-18]]`
(0.7291 ± 0.0028 NK+LK multi-seed on ProstT5). FARM-EXP.14 verifies
whether that per-cell verdict holds on the other 7 PLMs. Suggested
agent: bioinfo-quick with extended budget; consider splitting per-PLM
batches across 4-8 executor passes.

### FARM-EXP.15 — KNN-only baseline scores per (PLM, K, cell)

```yaml
id: FARM-EXP.15
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.13]
acceptance: |-
  For each (PLM, K, cell) in the 24-dataset family: compute the KNN-only "scores" baseline (no reranker) and persist Fmax + AuPRC + coverage under runs/transversal/<shortid>/ with reranker=knn-baseline in the axis tuple
  Lab CLI `scripts/run_knn_baseline.py` or equivalent path that reads the dataset's eval.parquet, applies the GO-transfer rule, and emits the same run.json schema as reranker runs (so FARM-EXP.4 champion table and FARM-EXP.3 paired-CI machinery treat both uniformly)
  216 baseline cells logged in `agent-farm/plans/farm-platform/artefacts/farm_exp_15_baseline_log.csv` with: plm, k, cell, fmax, auprc, coverage
  Paired bootstrap (10000 resamples) per (PLM, K) family confirms the reranker uplift sign vs baseline at 95% per FARM-EXP.3 grouping
estimated_hours: 6
priority: P1
tags: [benchmark, baseline, lineage]
requires_human: false
```

**Goal**: provide the "scores" column the user asked for explicitly.
KNN-only is the cheapest single-PLM baseline and the reference against
which every per-PLM reranker uplift is measured for paired CIs.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. The legacy `bench-v1-K5-filtered` pre-leakage rows (not comparable
   per memory `[[no-archaeology-recompute]]`).

**Notes**: Cheap pass: KNN scoring is already produced by the dataset
build (it's the input to feature generation); this slice just
formalises the read path and the per-cell metric write-out so the
"scores" column exists in the chapter-6 table. Suggested agent:
bioinfo-quick.

### FARM-EXP.16 — All-PLM derived reranker (multi-manifest trainer)

```yaml
id: FARM-EXP.16
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.14]
acceptance: |-
  Lab trainer (`src/protea_reranker_lab/reranker.py` or sibling) accepts a list of dataset manifests instead of a single one, joins on (query_id, candidate_id, k_position), and concatenates the PLM-specific feature families (`anc2vec_*`, `emb_pca_*`) under per-PLM column prefixes (e.g. `anc2vec_query_known_cos__esmc_600m`)
  No physical `allplm` dataset is written; the merge is a runtime view that the trainer composes from the per-PLM parquets
  New study spec `study_v28_allplm_multimanifest` produces 3 K × 9 cells = 27 runs reading from the 8 PLM manifests at K∈{3,5,10}
  Schema_sha encodes the multi-manifest fingerprint (sha256 of sorted manifest URIs + per-PLM column prefix list)
  Paired CI vs the best single-PLM champion per (K, cell) confirmed at 95% (positive uplift expected, negative is a publishable finding too)
estimated_hours: 14
priority: P1
tags: [benchmark, multi-plm, lineage, trainer]
requires_human: false
```

**Goal**: deliver the user-asked "dataset con todos los PLM, para
aplicarlo sobre todos los PLM" via runtime feature concatenation
rather than a physical concat dataset. Keeps the per-PLM artefacts
canonical and avoids a 10x disk footprint.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. PCA refit across the joined column space (each PLM's PCA stays
   per-PLM; the trainer just concatenates the projected coordinates).
2. Score-level ensemble (FARM-EXP.17).

**Notes**: Trainer change is additive: existing single-manifest entry
point stays intact; new entry point accepts `list[manifest_uri]`.
Suggested agent: executor (codepath change in lab + 27 training runs
under bioinfo-quick budget).

### FARM-EXP.17 — PLM ensemble of single-PLM rerankers (supersedes FARM-EXP.7 scope)

```yaml
id: FARM-EXP.17
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.14]
acceptance: |-
  Score-level ensemble of the per-PLM rerankers from FARM-EXP.14: for each (K, cell), aggregate the 8 PLM-specific predicted scores via score_mean and score_max (two ensemble flavours)
  Axis-tuple stanza in `experiments/_catalog/transversal.yaml`: plm=ensemble:8plm-canonical, k∈{3,5,10}, rr=reranker:v27-binary, feat=8plm-axis, eval=bench-v1-K{k}-v226-lineage-{plm}-family, prop=tpr_pred, ens∈{score_mean, score_max}
  6 ensemble runs (3 K × 2 strategies) stored under runs/transversal/<shortid>/ with run.json that lists the contributing booster URIs
  Paired CI per (K, cell) vs (a) best single-PLM reranker, (b) all-PLM multi-manifest reranker (FARM-EXP.16); table shows which strategy wins each cell
  Lab Fmax + cafaeval Fmax both captured (decoupled evaluators per lab CLAUDE.md)
estimated_hours: 8
priority: P1
tags: [benchmark, ensemble, lineage]
requires_human: false
```

**Goal**: deliver the ensemble step the user marked as "PLM ensemble"
on the roadmap. Subsumes FARM-EXP.7's narrower 1-K-only scope —
FARM-EXP.7 stays formally pending only until this lands; when FARM-EXP.17
ships, FARM-EXP.7 is marked superseded.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. Learned ensemble (a meta-reranker that learns weights over the 8
   PLM scores). If FARM-EXP.16 already beats score_mean/score_max
   that's evidence the learned approach is redundant; defer.

**Notes**: Cites `[[v27-binary-multiseed-2026-05-18]]` for the single-PLM
champion baseline. Suggested agent: bioinfo-quick.

### FARM-EXP.18 — InterProScan feature family integration (deferred)

```yaml
id: FARM-EXP.18
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.17]
acceptance: |-
  PROTEA feature pipeline grows an `interproscan` family: protein-level domain/family signatures (Pfam, SUPERFAMILY, CDD, PANTHER subset) mapped to GO terms via the InterPro2GO crosswalk
  `export_research_dataset` payload exposes `compute_interproscan: bool = false`; when true, the dump includes 6-12 new feature columns prefixed `ips_*` (e.g. ips_pfam_match_score, ips_panther_subfamily_match, ips_ipr2go_voter_count, ips_ipr2go_max_score)
  3 K × 1 PLM (best single-PLM champion from FARM-EXP.14) × {ips_off, ips_on} = 6 reranker runs ship as an ablation showing the InterProScan uplift on the leakage-free v226 band
  ADR D37 records the InterPro release pinned, the IPR2GO mapping snapshot SHA, and the data-licensing note (EBI redistributes InterProScan under an academic-use clause)
  Champion table updated if ips_on beats ips_off at 95% paired CI on ≥2 of the 3 K values
estimated_hours: 20
priority: P2
tags: [benchmark, interproscan, lineage, feature-family]
requires_human: false
```

**Goal**: add the third roadmap dimension the user named explicitly
("luego trabajaremos PLM ensemble, y interproscan"). Placed last
because it widens the feature pipeline upstream of the lab and
requires a new external dependency (InterProScan binary or the EBI
REST API).

**Repos touched**: PROTEA (feature pipeline + new operation),
protea-reranker-lab (trainer reads new columns; no schema break
because `ips_*` lives under its own feature family).

**Out of scope**:
1. Running InterProScan on the full UniProt training corpus —
   start with the eval set + the K-NN reference set only and
   evaluate the ROI before scaling.
2. Per-PLM × InterProScan grid (deferred unless the 1-PLM ablation
   shows uplift).

**Notes**: InterProScan is CPU-bound (~30 s/protein) and the EBI REST
quota is 25 req/min; budget the dump accordingly or pin a local
InterProScan container. Suggested agent: executor (PROTEA feature
pipeline change) followed by bioinfo-quick for the ablation runs.

## F-AUTH — Single auth system, manual approvals, multi-instance

Design rationale captured in ADR D37
(`docs/source/adr/D37-feat-auth-v2-users-roles-multi-instance.rst` in PROTEA).
This phase supersedes the partial FEAT-AUTH (PR #456) and the prior
ADR D6 Authentik-OIDC decision.

Four roles form a strict linear order: guest < researcher < operator < admin.
A single `require_role(min_role)` FastAPI dependency replaces the legacy
`_require_admin_token` throughout. Each PROTEA deployment is sovereign with
its own User table; no cross-instance identity plane.

Waves:
- Wave 3 (slices 1-5): foundation, migrations, bootstrap, login/signup, legacy token drop, endpoint gating.
- Wave 4 (slices 6-9): anonymous quota, per-user rate limits, session revocation, audit log.
- Wave 5 (slices 10-11): frontend pages and optional SMTP.

Hard constraints inherited from CLAUDE.md apply to every slice. Additionally:
- NEVER introduce a new `_require_admin_token` call; all such calls are removed in FARM-AUTH.4.
- NEVER store the raw API key secret after initial creation; only the sha256 hash is persisted.
- NEVER skip Alembic migration for schema changes; each new table ships its own `alembic revision`.

### FARM-AUTH.1 — User table + password helpers (Wave 3)

```yaml
id: FARM-AUTH.1
phase: F-AUTH
loop: farm-platform
status: done
deps: []
acceptance: |-
  Alembic migration creates `user` table: id (UUID PK), email (unique not null), username (unique not null), display_name, password_hash (argon2id text), role (enum: guest/researcher/operator/admin), status (enum: pending/active/deactivated), intended_use (text), created_at, last_login_at, deactivated_at
  protea/api/auth/passwords.py exports hash_password(plaintext)->str and verify_password(plaintext, stored_hash)->bool using argon2-cffi; no bcrypt fallback
  Unit tests tests/test_auth_passwords.py: hash is not plaintext, verify returns True on match and False on mismatch, two calls produce different hashes (random salt)
  alembic upgrade head runs without error on a clean DB
  ORM model protea/infrastructure/orm/models/user.py imported in models/__init__.py
estimated_hours: 6
priority: P0
tags: [auth, schema, migration, security]
requires_human: false
```

**Goal**: establish the identity foundation that every subsequent F-AUTH slice depends on.

**Touches**: `alembic/versions/<hash>_auth_user_table.py`, `protea/infrastructure/orm/models/user.py`, `protea/api/auth/passwords.py`, `tests/test_auth_passwords.py`, `protea/infrastructure/orm/models/__init__.py`.

**Depends on**: none.

**Acceptance**: `pytest tests/test_auth_passwords.py` passes; `alembic upgrade head` completes on a fresh schema.

**Notes**: argon2-cffi must be added explicitly to pyproject.toml if not already a direct dep. Suggested agent: executor.

### FARM-AUTH.2 — Bootstrap admin: env var + CLI subcommand (Wave 3)

```yaml
id: FARM-AUTH.2
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.1]
acceptance: |-
  On startup, if PROTEA_BOOTSTRAP_ADMIN_EMAIL is set and no User row with role=admin exists, PROTEA creates the admin; password read from PROTEA_BOOTSTRAP_ADMIN_PASSWORD if set, otherwise generated and printed to stderr once
  Bootstrap is idempotent: second startup with same env var does nothing
  `protea-cli admin add-user` Click subcommand accepts email, role (default researcher), and password-prompt flag; exits 0 on success, 1 if email already exists
  Unit test mocks the session and asserts admin row created on first call, skipped on second
estimated_hours: 5
priority: P0
tags: [auth, bootstrap, cli]
requires_human: false
```

**Goal**: ensure every PROTEA deployment can reach /admin from day one without manual DB surgery.

**Touches**: `protea/api/startup.py` (or lifespan hook), `protea/cli/admin.py`, `tests/test_auth_bootstrap.py`.

**Depends on**: FARM-AUTH.1.

**Acceptance**: `PROTEA_BOOTSTRAP_ADMIN_EMAIL=x@y.test pytest tests/test_auth_bootstrap.py` passes; second invocation is a no-op.

**Notes**: Bootstrap runs inside the FastAPI lifespan event before first request. The CLI subcommand is a separate entry point for break-glass use without starting the full API. Suggested agent: executor.

### FARM-AUTH.3 — Login + signup endpoints (Wave 3)

```yaml
id: FARM-AUTH.3
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.1]
acceptance: |-
  POST /auth/signup accepts {email, display_name, intended_use}; creates User row with status=pending, role=researcher; returns 201 with {id, email, status}; rejects duplicate email with 409
  POST /auth/login accepts {email, password}; on success returns 200 and sets HttpOnly+Secure+SameSite=Strict JWT cookie; on failure returns 401; records last_login_at on success; rejects pending-status users with 403
  JWT payload includes sub (user_id), role, jti (UUID), exp signed with PROTEA_JWT_SECRET
  GET /auth/me returns {id, email, role, status} for authenticated user, 401 if no valid cookie
  POST /auth/logout clears session cookie; returns 204
  pytest tests/test_auth_endpoints.py covers all five scenarios above
estimated_hours: 8
priority: P0
tags: [auth, api, jwt]
requires_human: false
```

**Goal**: wire the identity flow end-to-end so subsequent slices can depend on a real authenticated session.

**Touches**: `protea/api/routers/auth.py`, `protea/api/auth/jwt.py` (extend existing), `tests/test_auth_endpoints.py`.

**Depends on**: FARM-AUTH.1.

**Acceptance**: `pytest tests/test_auth_endpoints.py -v` passes; login response carries Set-Cookie with correct attributes.

**Notes**: Reconcile with any session JWT already introduced in PR #456; schema must match ADR D37. Suggested agent: executor.

### FARM-AUTH.4 — Drop legacy _require_admin_token (Wave 3)

```yaml
id: FARM-AUTH.4
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.3]
acceptance: |-
  _require_admin_token function deleted from codebase; PROTEA_ADMIN_TOKEN env var removed from settings.py and system.yaml template
  All /admin/* and /maintenance/* routes formerly calling _require_admin_token now call require_role("admin") or require_role("operator") per ADR D37 endpoint map
  `grep -r '_require_admin_token' protea/` returns empty
  `grep -r 'PROTEA_ADMIN_TOKEN' protea/ docs/` returns empty (legacy docs updated)
  pytest covers: GET /admin/audit returns 403 for a researcher session and 200 for an admin session
estimated_hours: 5
priority: P0
tags: [auth, cleanup, breaking-change]
requires_human: false
```

**Goal**: eliminate the dual auth surface so there is exactly one guard on every protected endpoint.

**Touches**: `protea/api/routers/admin.py`, `protea/api/routers/maintenance.py`, `protea/api/auth/dependencies.py` (new `require_role`), `protea/config/settings.py`, `tests/test_auth_roles.py`.

**Depends on**: FARM-AUTH.3.

**Acceptance**: `grep -r '_require_admin_token' protea/` returns empty; `pytest tests/test_auth_roles.py` passes.

**Notes**: Document the migration path in the PR description: callers that used PROTEA_ADMIN_TOKEN bearer must switch to an operator/admin API key. Suggested agent: executor.

### FARM-AUTH.5 — Endpoint gating sweep (Wave 3)

```yaml
id: FARM-AUTH.5
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.4]
acceptance: |-
  Every POST, PATCH, and DELETE endpoint in the PROTEA FastAPI surface has an explicit require_role dependency; default minimum is researcher
  Endpoints requiring operator or admin have explicit downgrade annotation matching ADR D37 endpoint map
  Parametrised pytest tests/test_auth_gating.py walks every registered route via app.routes and asserts unauthenticated POST/PATCH/DELETE returns 401 (not 200/403)
  GET endpoints listed as guest-accessible in ADR D37 return 200 without a session cookie
estimated_hours: 6
priority: P1
tags: [auth, api, security]
requires_human: false
```

**Goal**: guarantee no POST/PATCH/DELETE accidentally accepts unauthenticated requests after the legacy token is dropped.

**Touches**: all router files under `protea/api/routers/`, `tests/test_auth_gating.py`.

**Depends on**: FARM-AUTH.4.

**Acceptance**: `pytest tests/test_auth_gating.py` passes; parametrised test covers every route registered in the app.

**Notes**: Use FastAPI `app.routes` to enumerate routes in the test. Endpoints not explicitly annotated default to `require_role("researcher")` via a router-level dependency. Suggested agent: executor.

### FARM-AUTH.6 — Anonymous quick-annotate with IP-hash quota (Wave 4)

```yaml
id: FARM-AUTH.6
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.5]
acceptance: |-
  POST /annotate?save_history=false accepts unauthenticated requests up to 10 sequences per day per daily-rotated-salt IP hash
  Quota exhaustion returns 429 with Retry-After header set to seconds until midnight UTC
  IP hash uses same daily-salt rotation as VisitorCounter; plaintext IP is never stored
  pytest tests/test_auth_anonymous_annotate.py: 10 requests succeed, 11th returns 429; mocked new day resets counter
estimated_hours: 5
priority: P1
tags: [auth, quota, anonymous, annotate]
requires_human: false
```

**Goal**: let unauthenticated visitors try PROTEA without creating an account, bounded by a per-IP daily limit.

**Touches**: `protea/api/routers/annotate.py`, `protea/api/auth/quota.py` (new, shared with FARM-AUTH.7), `tests/test_auth_anonymous_annotate.py`.

**Depends on**: FARM-AUTH.5.

**Acceptance**: `pytest tests/test_auth_anonymous_annotate.py` passes; 429 body includes `retry_after_seconds`.

**Notes**: Fail-open on DB error: if the quota row cannot be read or written, allow the request. Suggested agent: executor.

### FARM-AUTH.7 — Per-user quota table + rate-limit middleware (Wave 4)

```yaml
id: FARM-AUTH.7
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.6]
acceptance: |-
  Alembic migration creates `quota` table: key (composite text of user_id+resource+period_start), resource (enum: annotate/job), period_start (date), count (integer), limit (integer)
  Researcher defaults: 1000 annotate sequences/day, 100 job dispatches/day; configurable under quota.limits in system.yaml
  Middleware increments quota.count on every authenticated POST /annotate and POST /jobs; returns 429 with Retry-After on limit breach
  pytest tests/test_auth_quota.py: researcher hits annotate limit and gets 429; admin is not rate-limited (no quota row for admin)
estimated_hours: 6
priority: P1
tags: [auth, quota, middleware]
requires_human: false
```

**Goal**: provide per-user anti-abuse protection with configurable limits per role.

**Touches**: `alembic/versions/<hash>_auth_quota_table.py`, `protea/api/auth/quota.py`, `protea/config/system.yaml` (quota.limits block), `tests/test_auth_quota.py`.

**Depends on**: FARM-AUTH.6 (reuses quota.py module started there).

**Acceptance**: `pytest tests/test_auth_quota.py` passes; `alembic upgrade head` completes; admin role has no quota limit.

**Notes**: Admin and operator roles are exempt by default; the YAML config may override. Suggested agent: executor.

### FARM-AUTH.8 — Session revocation table + middleware (Wave 4)

```yaml
id: FARM-AUTH.8
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.3]
acceptance: |-
  Alembic migration creates `session_revocation` table: jti (text PK), user_id (FK User), revoked_at (timestamp), reason (text)
  JWT middleware checks jti against session_revocation on every authenticated request; revoked jti returns 401
  POST /auth/logout inserts current jti into session_revocation and clears the cookie
  POST /auth/logout-all (researcher+) revokes all active sessions for the user via a revoke_before timestamp on the User row
  DELETE /admin/sessions/{user_id} (admin only) force-revokes all sessions for the target user
  pytest tests/test_auth_revocation.py: logout then cookie reuse returns 401; logout-all invalidates all sessions; admin force-logout works
estimated_hours: 7
priority: P1
tags: [auth, session, revocation, security]
requires_human: false
```

**Goal**: enable per-session and account-wide revocation to support forced logout after role changes or compromise.

**Touches**: `alembic/versions/<hash>_auth_session_revocation.py`, `protea/api/auth/jwt.py` (middleware extension), `protea/api/routers/auth.py` (new endpoints), `tests/test_auth_revocation.py`.

**Depends on**: FARM-AUTH.3.

**Acceptance**: `pytest tests/test_auth_revocation.py` passes; revoked jti returns 401 on next use.

**Notes**: logout-all is implemented via a `revoke_before` timestamp on the User row to avoid scanning unbounded rows. Suggested agent: executor.

### FARM-AUTH.9 — Audit log table + insert helpers (Wave 4)

```yaml
id: FARM-AUTH.9
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.4, FARM-AUTH.8]
acceptance: |-
  Alembic migration creates `audit_log` table: id (UUID PK), actor_user_id (FK User nullable), action (text not null), target (text), payload (JSONB), occurred_at (timestamp default utcnow); append-only (no UPDATE/DELETE)
  protea/api/auth/audit.py exports log_action(session, actor_id, action, target, payload); call is fire-and-forget (errors logged, never raised)
  Wrapped actions: login-ok, login-fail, role-change, api-key-mint, api-key-revoke, user-deactivate, db-reset, signup-approve
  GET /admin/audit (admin only) returns paginated JSON list of rows, filterable by actor_user_id and action
  pytest tests/test_auth_audit.py: login-ok inserts a row; login-fail inserts a row with actor_user_id=None; GET /admin/audit returns 200 for admin and 403 for researcher
estimated_hours: 6
priority: P1
tags: [auth, audit, observability]
requires_human: false
```

**Goal**: provide an append-only audit trail for all security-relevant actions, required for any multi-user deployment.

**Touches**: `alembic/versions/<hash>_auth_audit_log.py`, `protea/api/auth/audit.py`, `protea/api/routers/admin.py` (new GET /admin/audit endpoint), `tests/test_auth_audit.py`.

**Depends on**: FARM-AUTH.4 (admin router finalised), FARM-AUTH.8 (session middleware complete).

**Acceptance**: `pytest tests/test_auth_audit.py` passes; GET /admin/audit returns 403 for non-admin sessions.

**Notes**: Index on `occurred_at` for the paginated viewer. No UPDATE or DELETE on this table, by convention enforced in audit.py. Suggested agent: executor.

### FARM-AUTH.10 — Frontend: signup, login, profile, admin/users pages (Wave 5)

```yaml
id: FARM-AUTH.10
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.5, FARM-AUTH.9]
acceptance: |-
  /signup: email + display_name + intended_use form; POST /auth/signup; shows confirmation on 201; shows conflict error on 409
  /login: email + password; POST /auth/login; redirects to / on success; magic-link button hidden when GET /auth/smtp-enabled returns false
  /profile (researcher+): change-password form, own API key list with create/revoke, quota usage bar, job history table
  /admin/users (admin): three tabs Pending/Active/Deactivated; per-row: approve+role-pick, deactivate, reset-password, mint-key-on-behalf
  AuthChip in layout header: avatar initials + username + role badge when authenticated; Sign in link when guest; dropdown: Profile, Admin console (admin only), Operator console (operator only), Sign out
  Playwright smoke test: signup form submits and shows confirmation; login form redirects on success
estimated_hours: 12
priority: P1
tags: [auth, frontend, ui]
requires_human: false
```

**Goal**: deliver the complete auth user experience before F-AUTH is considered production-ready.

**Touches**: `apps/web/app/signup/page.tsx`, `apps/web/app/login/page.tsx`, `apps/web/app/profile/page.tsx`, `apps/web/app/admin/users/page.tsx`, `apps/web/components/AuthChip.tsx`, `apps/web/lib/api.ts` (new auth endpoints).

**Depends on**: FARM-AUTH.5 (all API endpoints gated), FARM-AUTH.9 (audit log populated on approve action).

**Acceptance**: `npm run build` in `apps/web/` exits 0; Playwright signup and login smoke tests pass.

**Notes**: SameSite=Strict cookie policy is the primary CSRF protection for same-origin deployments. Suggested agent: executor.

### FARM-AUTH.11 — Optional SMTP: magic-link login + email password reset (Wave 5)

```yaml
id: FARM-AUTH.11
phase: F-AUTH
loop: farm-platform
status: done
deps: [FARM-AUTH.10]
acceptance: |-
  PROTEA_SMTP_HOST, PROTEA_SMTP_PORT, PROTEA_SMTP_USER, PROTEA_SMTP_PASSWORD, PROTEA_SMTP_FROM env vars; all optional; SMTP features disabled if PROTEA_SMTP_HOST is unset
  GET /auth/smtp-enabled returns {enabled: bool}; frontend uses this to show/hide magic-link button
  POST /auth/magic-link accepts {email}; if SMTP enabled generates signed one-time token (30-min TTL), sends link, returns 202; if SMTP disabled returns 503 with {detail: "SMTP not configured"}
  GET /auth/magic-link?token=<t> validates token, creates session cookie, redirects to /profile; returns 400 on invalid or expired token
  POST /auth/password-reset-request and POST /auth/password-reset follow same SMTP-gated pattern
  pytest tests/test_auth_smtp.py mocks SMTP: magic-link token is single-use, expired token returns 400, reset updates password hash
estimated_hours: 8
priority: P2
tags: [auth, smtp, email, optional]
requires_human: false
```

**Goal**: add email-driven convenience flows for deployments that have SMTP configured, without breaking those that do not.

**Touches**: `protea/api/auth/smtp.py` (new), `protea/api/routers/auth.py` (new endpoints), `protea/config/settings.py` (SMTP env vars), `tests/test_auth_smtp.py`.

**Depends on**: FARM-AUTH.10 (frontend shows/hides magic-link button).

**Acceptance**: `pytest tests/test_auth_smtp.py` passes with SMTP mocked; deploying without SMTP env vars leaves all existing functionality intact.

**Notes**: Magic-link token stored in a dedicated one-time-token table (not session_revocation), deleted on use or expiry. Suggested agent: executor.

## F-INFRA — Infrastructure-as-code on the gaps that compound

Three concrete gaps in the current single-machine setup map directly to
memory-tracked incidents that recur and compound: GitHub repo policy
lives in the UI and drifts (two direct-to-main push incidents, 416 zombie
branches), fresh-machine bootstrap is prose-only (not executable), and
the postgres recovery procedure survived as a runbook note rather than a
runnable script. The five slices below address those gaps plus two
adjacent artefacts (a full-stack compose file and a thesis-grade
reproducibility ceremony) that share the same fix surface.

Rejected alternatives (documented here so future agents do not re-open
them): Ansible for single-machine ops is overkill; bash scripts are
simpler and carry no inventory/role/handler tax. Terraform for runtime
infra (postgres/rabbit/minio) is premature; everything is local
containers and no cloud resource is in scope. Ansible becomes worth
revisiting only when there is more than one host or recurring GPU box
provisioning. FARM-INFRA.5 is explicitly deferred until the user
greenlights cloud spend before the thesis defence.

### FARM-INFRA.1 — Terraform module for GitHub repo policy (9 repos)

```yaml
id: FARM-INFRA.1
phase: F-INFRA
loop: farm-platform
status: done
deps: []
acceptance: |-
  infra/terraform/github/main.tf encodes branch protection + required checks + auto-delete-head-branches + signed-commit requirement for all 9 repos (PROTEA, protea-contracts, protea-method, protea-sources, protea-runners, protea-backends, protea-reranker-lab, cafaeval-protea, agent-farm)
  infra/terraform/github/variables.tf declares repo list and PAT scope; infra/terraform/github/outputs.tf emits the applied rule summary
  infra/terraform/github/README.md documents apply instructions, state location, and required GH PAT scope
  terraform plan is a no-op against the current production state (IaC matches hand-maintained reality)
  terraform apply would re-apply if anyone drifted the UI settings
  make terraform-plan wrapper added to agent-farm Makefile
estimated_hours: 6
priority: P1
tags: [infra, terraform, gh-policy, stability]
requires_human: false
```

**Goal**: encode the GitHub repo policy that currently lives in the UI
as HCL in a new `infra/terraform/github/` directory. Any policy drift
(a protection rule toggled off, auto-delete disabled) becomes a
detectable diff rather than a silent incident.

**Touches**: `infra/terraform/github/main.tf` (new),
`infra/terraform/github/variables.tf` (new),
`infra/terraform/github/outputs.tf` (new),
`infra/terraform/github/README.md` (new),
`Makefile` (`terraform-plan` target).

**Depends on**: none.

**Acceptance**: `terraform plan` shows no changes against production;
`make terraform-plan` is the canonical invocation.

**Notes**: Root-causes the three policy-drift incidents:
`project_plugin_push_direct_main_incident` (2026-05-13, sources/runners/backends),
`feedback_janitor_direct_push_agentfarm` (agent-farm/main unprotected),
`project_cruft_audit_2026_05_22` (auto-delete-head-branches OFF, 416 zombie
remote branches). Highest ROI single change in the analysis. Suggested
agent: executor.

### FARM-INFRA.2 — `scripts/bootstrap-fresh-machine.sh`

```yaml
id: FARM-INFRA.2
phase: F-INFRA
loop: farm-platform
status: done
deps: []
acceptance: |-
  agent-farm/scripts/bootstrap-fresh-machine.sh is idempotent: running it twice on an already-bootstrapped box is a no-op
  Script covers docker install, poetry install, python 3.12 install, 8 repo clones under ~/Thesis2/repositories/, ~/.secrets/protea.env template creation, pg_restore from ~/Thesis2/backups/protea-*.dump (picking the newest dump), alembic upgrade head, manage.sh start
  agent-farm/docs/runbooks/bootstrap.md documents the curl-pipe-bash invocation and any pre-conditions
  End-to-end check: curl localhost:8000/jobs returns HTTP 200 after the script completes
  Second invocation (idempotency): no repo re-cloned, no volume wiped, no alembic migration re-run, exit 0
estimated_hours: 8
priority: P1
tags: [infra, bootstrap, bash, runbook]
requires_human: false
```

**Goal**: collapse the multi-step manual setup documented in prose
memories (`project_stack_env_not_sourced_outage`,
`project_db_volume_landmine`) into a single idempotent command. Any
new collaborator or fresh VM can reach a working PROTEA dev env with one
script invocation.

**Touches**: `agent-farm/scripts/bootstrap-fresh-machine.sh` (new),
`agent-farm/docs/runbooks/bootstrap.md` (new), reference pointer added
to `PROTEA/docs/source/runbooks/deployment-process-stack.rst`.

**Depends on**: none (but the restore step cleanly delegates to
FARM-INFRA.3 when that slice is done).

**Acceptance**: on a fresh Ubuntu 24.04 VM, `bash bootstrap-fresh-machine.sh`
brings the stack up; second invocation is a no-op; final health-check
passes.

**Notes**: Cites memory `project_stack_env_not_sourced_outage`
(AUTHN_REQUIRED=true aborts without JWT_SECRET; the script sources
.env before manage.sh start) and `project_db_volume_landmine`
(2026-05-11 wipe; the restore step is the canonical recovery path).
Suggested agent: executor.

### FARM-INFRA.3 — `scripts/restore-from-backup.sh`

```yaml
id: FARM-INFRA.3
phase: F-INFRA
loop: farm-platform
status: done
deps: []
acceptance: |-
  agent-farm/scripts/restore-from-backup.sh --dry-run lists the dump it would pick and the alembic head SHA, then exits 0 without touching the database
  agent-farm/scripts/restore-from-backup.sh --apply (with a confirmation prompt) or --apply --yes (non-interactive) runs pg_restore, alembic upgrade head, and a smoke query (SELECT count(*) FROM proteins)
  Newest dump under ~/Thesis2/backups/protea-*.dump is selected automatically; --dump <path> overrides
  Runbook agent-farm/docs/runbooks/restore.md documents the dry-run and apply paths
  Makefile target restore-latest delegates to the script with --apply
estimated_hours: 4
priority: P1
tags: [infra, backup, bash, runbook]
requires_human: false
```

**Goal**: convert the postgres-recovery prose from memory
`project_db_volume_landmine` into a single executable. The 2026-05-11
wipe took ~28 min to recover manually; a scripted path with --dry-run
and --yes flags reduces that to under 5 min and eliminates
copy-paste error.

**Touches**: `agent-farm/scripts/restore-from-backup.sh` (new),
`agent-farm/docs/runbooks/restore.md` (new),
`agent-farm/Makefile` (`restore-latest` target).

**Depends on**: none.

**Acceptance**: `--dry-run` is always safe; `--apply --yes` is the
non-interactive recovery path used in automation.

**Notes**: Cites memory `project_db_volume_landmine`
(2026-05-11 01:19 wipe, root cause unattributed, recovery ~28 min)
and `FARM-1.7` restore-drill acceptance (the weekly drill already calls
`scripts/restore-drill.sh`; this slice makes the production recovery
path the same script with `--apply`). Suggested agent: executor.

### FARM-INFRA.4 — `docker-compose.full-stack.yml`

```yaml
id: FARM-INFRA.4
phase: F-INFRA
loop: farm-platform
status: done
deps: []
acceptance: |-
  PROTEA/docker-compose.full-stack.yml brings up infra (postgres, rabbit, minio, grafana, loki, prometheus, promtail) and the PROTEA app surface (api, workers, frontend, ngrok) on a single shared network in one docker compose up -d command
  All containers reach healthy state within 90 s on a machine that already has the images pulled
  docker compose -f docker-compose.full-stack.yml down -v cleans without orphan containers
  PROTEA/scripts/manage.sh gains a compose subcommand that delegates to docker compose -f docker-compose.full-stack.yml up -d
  A short section in docs/source/runbooks/deployment-process-stack.rst documents the compose path alongside the existing manage.sh start path
estimated_hours: 6
priority: P2
tags: [infra, docker, compose, deployment]
requires_human: false
```

**Goal**: replace the five separate compose files that exist today
(docker-compose.infra.yml for postgres/rabbit/minio, separate monitoring
stack, etc.) with a single umbrella file so a fresh deployment ceremony
is one `up -d` command. Directly supports the FARM-INFRA.5
reproducibility ceremony.

**Touches**: `PROTEA/docker-compose.full-stack.yml` (new),
`PROTEA/scripts/manage.sh` (`compose` subcommand),
`PROTEA/docs/source/runbooks/deployment-process-stack.rst` (new section).

**Depends on**: none.

**Acceptance**: on a fresh box after FARM-INFRA.2 ran to install docker,
`docker compose -f docker-compose.full-stack.yml up -d` ends with all
containers healthy; `down -v` leaves no orphans.

**Notes**: Today there are 5 compose files but no umbrella one; every
deployment ceremony requires knowing which files to pass in which order.
Eliminates a recurring source of "stack not fully up" operator error.
Suggested agent: executor.

### FARM-INFRA.5 — Thesis-grade reproducibility ceremony (deferred)

```yaml
id: FARM-INFRA.5
phase: F-INFRA
loop: farm-platform
status: deferred
priority: low
deps: [FARM-INFRA.1, FARM-INFRA.2, FARM-INFRA.3, FARM-INFRA.4]
acceptance: |-
  agent-farm/infra/terraform/gpu-box/ provisions a GPU instance on a chosen provider (Lambda Labs, RunPod, or vast.ai) via the provider's Terraform plugin
  agent-farm/infra/ansible/protea-reproduce.yml drives FARM-INFRA.2 bootstrap + FARM-INFRA.3 restore + dispatches a known canonical export job + diff-asserts the produced parquet against a fixture sha (schema_sha + manifest_sha match)
  PROTEA/docs/source/chapters/06-evaluation/reproducibility.rst cites both the Terraform module and the Ansible playbook as the citable reproducibility artefact
  Ceremony documented step-by-step; tested on at least one cloud provider; checksum match on the produced parquet
estimated_hours: 20
priority: low
tags: [infra, terraform, ansible, reproducibility, thesis, deferred]
requires_human: true
```

**Goal**: produce a tribunal-grade citable artefact that converts
"reproducible if you ask me" to "reproducible if you run these two
commands". A Terraform module + Ansible playbook pair that provisions
a GPU box, installs PROTEA, restores a demo backup, dispatches a
canonical export job, and verifies the parquet checksum is citable
from Chapter 6 at the thesis defence.

**Touches**: `agent-farm/infra/terraform/gpu-box/` (new),
`agent-farm/infra/ansible/protea-reproduce.yml` (new),
`PROTEA/docs/source/chapters/06-evaluation/reproducibility.rst` (new,
citation point in Ch6).

**Depends on**: FARM-INFRA.1, FARM-INFRA.2, FARM-INFRA.3, FARM-INFRA.4
all done.

**Acceptance**: ceremony documented step-by-step; tested on at least
one cloud provider; checksum match on the produced parquet confirms
`schema_sha + manifest_sha` parity.

**Notes**: Marked `status: deferred` and `requires_human: true` until
the user explicitly greenlights cloud spend before the tribunal date.
Ansible is justified here (not in FARM-INFRA.2) because this slice
drives a remote host over SSH, which is the canonical Ansible use case.
Suggested agent: executor (IaC authoring) with human approval gate
before `terraform apply` or `ansible-playbook` touches live cloud
resources.

## F-DATA-PACK — Dataset deliverable (FAIR packaging)

Pivot deliverable per [[dl-postponed-2026-05-25]]: the thesis research
contribution is the curated, exploitable multi-PLM x K dataset family
produced by PROTEA, not a DL champion model. This phase ships the datasets
so they are citable, reproducible, and reusable by the community.

Depends on FARM-EXP.13 reaching SUCCEEDED for all 24 (PLM x K) cells.

### F-DATA-PACK.1 — Manifest schema validator

```yaml
id: F-DATA-PACK.1
phase: F-DATA-PACK
loop: farm-platform
status: done
deps: [FARM-EXP.13]
acceptance: |-
  protea-reranker-lab/scripts/validate_manifest.py --manifest <path> passes
  on every existing bench-v1-K{3,5,10}-v226-lineage-{plm} Dataset manifest
  Schema version pinned in manifest header; validator rejects unknown keys
  CI job in protea-reranker-lab runs validate_manifest.py on every PR that
  touches a manifest JSON
  schema_sha + manifest_sha fields non-placeholder on all 24 cells
estimated_hours: 4
priority: P0
tags: [dataset, manifest, validator, ci]
requires_human: false
```

**Goal**: ensure every manifest produced by FARM-EXP.13 has correct,
non-placeholder schema_sha + manifest_sha before any public release.
Closes the gap noted in memory `[[farm-exp-2-placeholder-digests]]`.

**Touches**: `protea-reranker-lab/scripts/validate_manifest.py` (new),
`.github/workflows/validate-manifests.yml` in protea-reranker-lab.

**Suggested agent**: executor.

### F-DATA-PACK.2 — README per dataset (24 cells)

```yaml
id: F-DATA-PACK.2
phase: F-DATA-PACK
loop: farm-platform
status: done
deps: [F-DATA-PACK.1]
acceptance: |-
  Each of the 24 bench-v1-K{k}-v226-lineage-{plm} datasets has a README.md
  committed alongside its manifest: provenance (PROTEA version, export job id,
  export date), column schema (feature families, dtypes), train/eval split
  description, known caveats (PCA transductive fit, anc2vec artefact)
  README generated from a template by a script (not hand-written per cell)
  Template cites [[dl-postponed-2026-05-25]] as context for why the
  dataset deliverable is the primary contribution
estimated_hours: 6
priority: P1
tags: [dataset, readme, documentation, provenance]
requires_human: false
```

**Goal**: make each dataset self-describing so a reader downloading a
parquet can understand its provenance without querying PROTEA's DB.

**Touches**: `protea-reranker-lab/scripts/generate_dataset_readme.py` (new),
`protea-reranker-lab/datasets/bench-v1-*/README.md` (generated).

**Suggested agent**: doc-writer.

### F-DATA-PACK.5 — Zenodo / Hugging Face upload

```yaml
id: F-DATA-PACK.5
phase: F-DATA-PACK
loop: farm-platform
status: pending
deps: [F-DATA-PACK.4, FARM-EXP.14]
acceptance: |-
  All 24 bench-v1-K{3,5,10}-v226-lineage-{plm} parquet files + manifests +
  per-cell READMEs uploaded to Zenodo (preferred) or HF datasets repo
  under CC-BY-4.0 license with Francisco Miguel Perez Canales as creator
  Zenodo DOI obtained and recorded in agent-farm memory
  protea-reranker-lab/scripts/upload_to_zenodo.py (or HF equivalent)
  is idempotent: re-running does not create duplicate depositions
  F-DATA-PACK.3 dataset cards backfilled with real DOI (replacing TBD)
  Thesis chapter 6 / chapter 7 cites the DOI
estimated_hours: 8
priority: P1
tags: [dataset, zenodo, huggingface, publish, open-data]
requires_human: true
```

**Goal**: make the dataset family publicly citable and discoverable.
`requires_human: true` because Zenodo upload needs user's account token
(kept in `~/.secrets/`).

**Touches**: `protea-reranker-lab/scripts/upload_to_zenodo.py` (new),
memory update with DOI, thesis citation backfill.

**Suggested agent**: executor (script authoring) + human (account token
and final upload confirmation).


### UX-ADMIN-AUDIT — Audit admin + auth surface (anonymous audit only covered public)

```yaml
id: UX-ADMIN-AUDIT
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: []
acceptance: |-
  ux-reviewer scope: /es/admin/* + /es/login + /es/signup + /es/profile +
  /es/auth/pending-approval + /es/farm.
  Earlier audit (2026-05-25 evening, ux-reviewer-1779719334-3a3e) was
  scope anonymous-user-flow only and explicitly excluded admin surface
  per user mandate.
  User complaint 2026-05-25 22:48: "/es/admin/experiment-runs es bastante
  inutil" — admin UI is bare-bones, not polished like public pages.
  Deliverable: explore.md-style report with P0/P1/P2 findings per admin
  page covering: information hierarchy, scanability, navigation,
  cognitive load, mobile, performance, a11y. Special focus on:
  experiment-runs CRUD UX, api-keys management, profile page (post
  FD-6 i18n), pending-approval flow, farm dashboard. Output goes
  to RESULTS_DIR/explore-admin.md. Frontend-designer wave 2 will
  pick up the prioritized list.
estimated_hours: 4
priority: P1
tags: [ux, admin, audit]
```


### FIX-METRIC-IA — IA-weighted f_micro_w comparable to CAFA/LAFA (end-to-end)

```yaml
id: FIX-METRIC-IA
phase: F-METRIC
loop: farm-platform
status: pending
deps: []
acceptance: |-
  IA-gen util computes information accretion from OntologySnapshot + t0 annotation corpus; reproduces lafa_t0_Sep_2025/IA.tsv on overlapping terms (max abs diff < 1e-3) -- own IA that MUST match LAFA
  run_cafa_evaluation resolves a REAL ia file (snapshot.ia_url or payload.ia_file), never the IC=1 fallback, for benchmark eval-sets
  EvaluationResult.results stores f_micro_w + weighted precision/recall per aspect (today only fmax); migration of the JSONB blob shape
  FARM-EXP.13 grid re-evaluated with IA -> real f_micro_w persisted
  /v1/benchmark/matrix primary metric = f_micro_w (not unweighted fmax); web home + benchmark + scoring pages show f_micro_w aggregate + per-task CI, best-cell only labelled as such (no winner's-curse headline)
  FINAL GATE: re-evaluating the existing protea-knn-v1 predictions with the re-wired PROTEA eval + own IA on a t0=Sep_2025 eval-set reproduces the LAFA numbers already on record (NK BP 0.263 / CC 0.407 / MF 0.579, etc.) within tolerance
  docs/ADR + thesis ch6 report the IA-weighted aggregate
estimated_hours: 16
priority: P0
tags: [metrics, evaluation, ia, cafaeval, comparability, web, thesis]
requires_human: false
note: "2026-06-04 session finding: run_cafa_evaluation falls back to uniform IC=1 (generate_evaluation_set never produces IA; snapshot.ia_url unset), so the internal 'f_micro_w' is NOT real IA-weighting and is incomparable to LAFA. The dashboard also headlines best-per-cell (winner's-curse, measured ~+0.02-0.03 within-task, dwarfed by aspect-difficulty spread). LAFA-vs-bench reconciliation: MFO matches/exceeds (method transfers), CC/BP/PK drop is the IA-weighting penalty on generic terms. Validated against /v1/benchmark/matrix (2223 cells) + LAFA score injection this session."
```

**Goal**: make every PROTEA-reported quality number IA-weighted `f_micro_w`
under the exact CAFA protocol (`-ia <real> -prop fill -norm cafa -no_orphans
-toi`), so internal benchmark numbers are directly comparable to CAFA/LAFA,
and stop the dashboard from headlining cherry-picked best-cell maxima.

**Repos touched**: PROTEA (core eval pipeline + IA-gen + ORM/migration + API
benchmark router + apps/web), thesis (ch6 numbers), agent-farm (this slice).

**Out of scope**:
1. Re-running the full multi-PLM grid is gated on FARM-EXP.13 completion; this
   slice ships the pipeline + re-evals what exists, and backfills the rest as
   EXP.13 cells land.
2. Changing the scoring recipes themselves (composite/reranker only add
   ~+0.01-0.015 over embedding-only; not this slice's concern).

**Notes**: IA source decision (user, 2026-06-04) = compute our OWN IA in-pipeline
but it MUST reproduce LAFA's IA on the shared Sep_2025 t0 (validation gate). The
final acceptance gate reuses the protea-knn-v1 predictions already scored on the
locally-deployed LAFA (protea-lafa.ngrok.app) as ground truth for comparability.
Suggested agents: executor (IA-gen + pipeline wiring + migration + API), then a
web follow-on (dashboard metric + de-bias), then doc/thesis.

**Status update (2026-06-06):** the PROTEA core + algorithm-level correctness
gate shipped as FIX-METRIC-IA.a (PR #599): own IA reproduces LAFA `calc_ia`
within 1e-3, `f_micro_w` + weighted P/R persisted, `/v1/benchmark/matrix` ranks
by `f_micro_w` (with `primary_metric` flag + `per_task` mean/CI). The remainder
is tracked as FIX-METRIC-IA.b below.

### FIX-METRIC-IA.b — IA-weighted metric: web de-bias + DB grid re-eval + thesis

```yaml
id: FIX-METRIC-IA.b
phase: F-METRIC
loop: farm-platform
status: pending
deps: [FIX-METRIC-IA]
acceptance: |-
  apps/web de-bias: home + benchmark + scoring pages headline the f_micro_w aggregate + per-task 95% CI (consuming the router's primary_metric + per_task), and label any best-cell ONLY as such (no winner's-curse maximum as headline)
  DB-level IA reproduction: the in-pipeline IA, run over the deployed Sep_2025 snapshot, reproduces lafa_t0_Sep_2025/IA.tsv on overlapping terms within max abs diff < 1e-3 (the .a gate was algorithm-level on synthetic DAGs; this is the real-corpus gate)
  FARM-EXP.13 grid re-evaluated with real IA -> real f_micro_w persisted for every existing prediction_set (backfill as v227 cells land; do NOT re-run grid compute)
  docs/ADR updated; thesis ch6 reports the IA-weighted aggregate as the headline number
estimated_hours: 10
priority: P1
tags: [metrics, web, thesis, ia, evaluation]
requires_human: false
note: "Part 1 (web de-bias) is unblocked NOW (router already exposes primary_metric + per_task). Parts 2-3 (real-corpus IA reproduction + grid re-eval) are GATED on the Sep_2025 OBO + SwissProt-exp corpus being ingested, which is the intentionally-paused v227 work (phase2-lafa-v227 chain). Thesis ch6 lives in the thesis repo (base main)."
```

**Goal**: finish the user-facing and on-record half of the IA-weighted metric
so the deployed app and the thesis report the honest, LAFA-comparable
`f_micro_w`, not the legacy unweighted Fmax.

**Out of scope**: re-running grid compute (only re-score existing predictions);
changing scoring recipes.

**Suggested split**: a web executor for Part 1 (ship now), then a PROTEA
executor for Part 2 once the v227 corpus lands, then doc/thesis for Part 3.

### F-EVAL-PROTOCOL — leakage-free temporal split (CAFA-ready train/valid/test)

```yaml
id: F-EVAL-PROTOCOL
phase: F-EVAL
loop: farm-platform
status: pending
deps: []
acceptance: |-
  Three temporal (rolling-origin) windows formalized and documented: TRAIN (<= t-1, builds KNN corpus + reranker labels + IA), VALID (t-1 -> t0, selection + tuning + threshold), TEST (t0 -> t1, touched once, the reported LAFA number); random/shuffled CV explicitly forbidden in an ADR
  An explicit VALID window concept exists in dataset/eval metadata (alongside train_versions/test_versions), so a cell can be scored on VALID without touching TEST
  Selection protocol implemented: PLM/K/recipe + LightGBM hyperparams + selective-deploy decision (NK+LK reranker vs PK KNN, per category/aspect) are chosen on VALID and frozen before TEST; the reported number is either the VALID-selected model on TEST or the full grid (no in-TEST selection)
  Operating threshold tau is fixed on VALID and reported alongside the Fmax-over-tau benchmark number
  Cutoff CI guard: a check fails if any produced artifact (corpus, features, labels, IA) references a release > the declared cutoff (structural no-future-data enforcement, mirroring the ALL_FEATURES producer-consumer guard)
  Feature leakage audit: every feature family (not just anc2vec) passes the golden rule -- computable identically for a never-seen protein with zero known labels; offenders documented + fixed or dropped
  A documented "fresh t0" inference path: the whole pipeline runs from a single cutoff knob, producing a CAFA submission with no data > t0
estimated_hours: 20
priority: P1
tags: [evaluation, methodology, leakage, cafa, reranker, reproducibility]
requires_human: false
note: "2026-06-06 design session. Closes the METHODOLOGY half of CAFA-readiness; FIX-METRIC-IA closes the metric half and the v227 rebuild closes the band half. Current lab gap: phase3a_*_sweep.py selects champions on the SAME v226->v230 window used for reporting (winner's-curse) and there is no distinct VALID window. The anc2vec replication artifact (project_anc2vec_leakage_mechanism) is the template for the feature audit. Likely splits into F-EVAL-PROTOCOL.a (VALID window + selection protocol + threshold) + .b (cutoff CI guard + feature audit) + .c (fresh-t0 submission path)."
```

**Goal**: make the whole reranker + model-selection + inference + validation
flow reusable for a NEW CAFA with no temporal leakage of any kind, via an
explicit rolling-origin TRAIN/VALID/TEST protocol bound per pipeline stage (not
a row-split).

**Repos touched**: protea-reranker-lab (selection + VALID window + sweeps),
PROTEA (cutoff knob + eval metadata + CI guard + feature audit), agent-farm
(this slice), thesis (ch6 protocol section), docs/ADR.

**Out of scope**: the metric itself (FIX-METRIC-IA) and the v227 band rebuild
(phase2-lafa-v227); this slice is orthogonal and composes with both.

### F-EVAL-PROTOCOL.b — cutoff CI guard + feature leakage audit + select-on-VALID

```yaml
id: F-EVAL-PROTOCOL.b
phase: F-EVAL
loop: farm-platform
status: pending
deps: [F-EVAL-PROTOCOL]
acceptance: |-
  Cutoff CI guard: a check fails if any produced artifact (corpus, candidate set, features, labels, IA) references a release > the declared training cutoff; mirrors the ALL_FEATURES producer-consumer guard; runs in PROTEA CI and the reranker-lab CI
  Feature leakage audit: every feature family (alignment, taxonomy, vote/consensus, embedding, anc2vec, etc.) is checked against the golden rule (computable identically for a never-seen protein with zero known labels); offenders documented + fixed or dropped; anc2vec replication fix is the template
  protea-reranker-lab phase3a_*_sweep.py refactored to SELECT champion (PLM/K/recipe/hyperparams) + selective-deploy decision (NK+LK reranker vs PK KNN, per category/aspect) + operating-threshold tau on the VALID window, then evaluate the frozen choice ONCE on TEST; no in-TEST selection
estimated_hours: 16
priority: P1
tags: [evaluation, leakage, ci, reranker, methodology]
requires_human: false
note: "2026-06-06. Closes the enforcement half of F-EVAL-PROTOCOL (the .a slice shipped the ADR + VALID-window metadata in PROTEA #600). The current lab winner-curse (select + report on the same v226->v230 window) is fixed here by selecting on VALID. Uses the VALID window_role marker from .a."
```

**Goal**: make the leakage-free protocol ENFORCED (not just documented), and remove the winner's-curse from champion selection by selecting on VALID and reporting on TEST.

### F-EVAL-PROTOCOL.c — fresh-cutoff single-knob inference path (LAFA submission generator)

```yaml
id: F-EVAL-PROTOCOL.c
phase: F-EVAL
loop: farm-platform
status: pending
deps: [F-EVAL-PROTOCOL, F-EVAL-PROTOCOL.b]
acceptance: |-
  A single `cutoff` knob threads the whole pipeline (corpus, embeddings, candidate KNN, features, IA) so the entire method runs reading ONLY data <= cutoff, producing predictions for a target set with no future-data leakage
  Running with cutoff = a LAFA timepoint (e.g. Jun_2026) reproduces a submission-shaped prediction file with the same format the LAFA container guide requires (offline, fixed input/output)
  A retrain with a later cutoff (e.g. Aug_2026) produces a second, comparable submission with only the cutoff changed (the training-data-recency comparison An Phan described)
  The cutoff CI guard from .b passes on every artifact this path produces
estimated_hours: 14
priority: P0
tags: [evaluation, inference, lafa, cafa, submission, leakage]
requires_human: false
note: "2026-06-06. This IS the LAFA submission generator: An Phan (LAFA host) freezes a container at a timepoint and evaluates its predictions over multiple future windows, and welcomes a retrained version to measure data-recency effect. A single-cutoff path makes both the frozen Jun_2026 entry and a later retrained entry fall out cleanly. Feeds F-LAFA-SUBMIT.*."
```

**Goal**: produce a LAFA-submittable prediction set from a single training-cutoff parameter, with structural no-future-data enforcement, for both the frozen entry and recency-controlled resubmissions.

### F-LAFA-SUBMIT.knn — package + submit PROTEA-KNN to the LAFA server

```yaml
id: F-LAFA-SUBMIT.knn
phase: F-LAFA-SUBMIT
loop: farm-platform
status: pending
deps: [F-EVAL-PROTOCOL.c, FIX-METRIC-IA]
acceptance: |-
  PROTEA-KNN container (ghcr.io/frapercan/protea/knn-v1) conforms to the LAFA container guide: runs OFFLINE, fixed input/output format, deterministic; the ProtT5/Swiss-Prot reference embeddings live in a persistent data volume per LAFA's hosting requirement
  A dry-run on a LAFA-shaped timepoint input produces a valid prediction file that scores under cafaeval with the IA-weighted f_micro_w matching our internal numbers
  Submission completed via the LAFA intake form + host coordination; entry name + dataset (XaxiPiruli/protea-lafa-knn-v227) recorded
estimated_hours: 10
priority: P0
tags: [lafa, submission, container, knn, packaging]
requires_human: true
note: "2026-06-06. The KNN container + dataset already exist (per the LAFA thread). This slice aligns packaging to the guide, validates the offline run against the IA-weighted protocol, and submits. requires_human: the intake form + host back-and-forth is a person-in-the-loop step. The KNN is the transparent baseline entry; the richer reranker is F-LAFA-SUBMIT.reranker."
```

**Goal**: get the clean PROTEA-KNN baseline live on the LAFA server as a reproducible, offline, leakage-free containerized method.

### F-LAFA-SUBMIT.reranker — package + submit the reranker as a second LAFA entry

```yaml
id: F-LAFA-SUBMIT.reranker
phase: F-LAFA-SUBMIT
loop: farm-platform
status: pending
deps: [F-LAFA-SUBMIT.knn, FIX-METRIC-IA.b]
acceptance: |-
  The learned re-ranker (gradient-boosted over KNN candidates; alignment + taxonomy + IA-aware features; per-aspect selection; selective-deploy NK+LK reranker / PK KNN) packaged as a separate offline LAFA container, reference + booster artifacts in a persistent volume
  Validated to beat the KNN baseline on IA-weighted f_micro_w (NK + LK) under the LAFA protocol on the v227 band, with PK held at the KNN baseline (honest selective deploy)
  Submitted as a distinct LAFA entry once the v227 grid + reranker are stabilized
estimated_hours: 12
priority: P1
tags: [lafa, submission, reranker, ensemble, container]
requires_human: true
note: "2026-06-06. The richer method An Phan welcomed. Gated on the v227 grid (phase2-lafa-v227 rebuild) + FIX-METRIC-IA.b Part 2 so the reported lift is real IA-weighted. Optional further variants (baseline concatenation, InterProScan features, adaptive K) are follow-on entries, not this slice."
```

**Goal**: submit the competitive, IA-weighted-validated reranker as PROTEA's richer LAFA entry alongside the KNN baseline.

### F-BAND-REGISTRY — canonical (ontology snapshot, IA) per band, derived + guarded

```yaml
id: F-BAND-REGISTRY
phase: F-EVAL
loop: farm-platform
status: pending
deps: [FIX-METRIC-IA]
acceptance: |-
  One registry maps each band/cutoff to its canonical OntologySnapshot + IA artifact as DERIVED (not free) values; the ontology snapshot governs propagation (true-path), term universe, orphans, and TOI, and the IA is computed from that snapshot + the t0 corpus
  Resolution is deterministic (snapshot ia_url or explicit payload ia_file) and NEVER falls back to uniform IC=1 (extends the #599 resolver to also bind propagation/TOI/term-universe to the band ontology, not just the IA)
  A cell is rejected at runtime AND in CI if its IA / ontology snapshot come from a band other than its declared cutoff (phantom-gap guard)
  Documented: which (snapshot, IA) is authoritative per band (v226, v227), and why a snapshot mismatch between train and eval inflates a fake PROTEA-vs-LAFA gap
estimated_hours: 10
priority: P0
tags: [evaluation, ia, ontology, leakage, comparability]
requires_human: false
note: "2026-06-06. Answers the user's 'manage IA and ontology correctly' requirement structurally: snapshot + IA are derived from (band, cutoff), pinned in one registry, never free-floated. Foundational to both FARM-EXP.GRID-v226 and F-RERANK-UNIVERSAL. Builds on #599 (ia_file/ia_url resolver + IC=1 hard-fail) and #602 (IA provenance doc)."
```

**Goal**: make the per-band ontology snapshot and IA a single, derived, deterministically-resolved, CI-guarded pair, so no cell ever mixes bands and no phantom gap appears from snapshot drift.

### FARM-EXP.GRID-v226 — complete v226 benchmark as a declared closed set + coverage query

```yaml
id: FARM-EXP.GRID-v226
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [F-BAND-REGISTRY]
acceptance: |-
  The full v226 benchmark space is declared as DATA (8 PLM x K{3,5,10} x the NK/LK/PK x MFO/BPO/CCO cells x 7 scoring_configs x {KNN baseline, champion reranker}), bound to the v226-canonical snapshot + IA from F-BAND-REGISTRY
  Completeness is a set-difference QUERY ("these M cells are missing"), surfaced on /v1/benchmark/matrix; no manual checklist
  Idempotent gap-fill reuses the FARM-EXP.13 artifacts (MinIO) + the align-cache (K10 superset K5 superset K3); every evaluation_result carries its full axis tuple + content hash
  "Complete v226 benchmark" is reportable as 100% coverage with IA-weighted f_micro_w on every cell
estimated_hours: 12
priority: P1
tags: [benchmark, grid, coverage, v226, evaluation]
requires_human: false
note: "2026-06-06. The user's long-term 'tener todo calculado sobre 226, benchmark completo' deliverable. Treats the grid as EVALUATION coverage (a closed declared set + a coverage query), NOT as a reason to train one model per cell (see F-RERANK-UNIVERSAL)."
```

**Goal**: have the entire v226 benchmark computed and reportable as a single declared, hash-addressed, query-checkable closed set.

### F-RERANK-UNIVERSAL — one pooled, aspect-conditioned reranker (supersedes per-cell phase3a)

```yaml
id: F-RERANK-UNIVERSAL
phase: F-RERANK
loop: farm-platform
status: pending
deps: [F-EVAL-PROTOCOL.b, F-BAND-REGISTRY]
acceptance: |-
  ONE universal reranker trained on the POOLED candidate pairs across PLM and K, with (PLM-id, K-context, neighborhood stats: rank/distance/local-density/vote-count) as FEATURES, aspect-conditioned (aspect feature or per-aspect head); replaces the up-to-216 per-cell phase3a models with a single artifact (decouples evaluation-grid coverage from model granularity)
  K-augmentation: training candidates drawn from a SEEDED, bounded K distribution (retrieve-wide + rerank), so the model is K-agnostic; inference uses a deterministic K policy (fixed or adaptive), never an unseeded random stream (cell must stay hashable/reproducible per F-EVAL-PROTOCOL)
  Balanced positive:negative sampling (1:1 or tuned) for reranker training; the negative-construction MUST pass the F-EVAL-PROTOCOL.b feature-leakage audit (anc2vec replication is the cautionary template, since that leak came from how negatives were replicated)
  Selective-deploy (NK+LK reranker / PK KNN) chosen per (category, aspect) on the VALID window, frozen, then evaluated ONCE on TEST on IA-weighted f_micro_w
  Matches or beats the per-cell phase3a champion on wFmax (NK + LK) with far fewer models, on the v226 (and v227) band; one container ships to LAFA
estimated_hours: 24
priority: P0
tags: [reranker, universal, pooling, sampling, lafa, performance]
requires_human: false
note: "2026-06-06 design with user. The biggest performance lever for LAFA #1: a single pooled, aspect-conditioned reranker with PLM/K as features and K-randomization as augmentation, instead of 216 per-cell models. The 'infinite random K stream' idea is adopted as a SEEDED bounded training distribution (retrieve-wide + neighborhood-context features), not as the inference policy. Supersedes the earlier per-cell phase3a sweep approach."
```

**Goal**: replace the per-cell reranker grid with a single universal, aspect-conditioned, pooled reranker (PLM/K as features, K-augmented, balanced-sampled, leakage-audited) that is both simpler to ship and stronger, as the main lever toward LAFA #1.
