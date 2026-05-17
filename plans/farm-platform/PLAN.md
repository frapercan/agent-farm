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
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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

### FARM-FEAT.4 — Wire deploy-keeper service.triggers

```yaml
id: FARM-FEAT.4
phase: F-FEAT
loop: farm-platform
status: pending
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
status: pending
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
status: pending
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
status: pending
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
status: pending
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

## F-EXP-RESET — Transversal benchmark

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

### FARM-EXP.9 — Re-run pre-leakage pre-computed cells on bench-v1-K5-filtered

```yaml
id: FARM-EXP.9
phase: F-EXP-RESET
loop: farm-platform
status: pending
deps: [FARM-EXP.2]
acceptance: |-
  Identify the ~80-100 pre-computed cells on bench-v1-K5 (pre-leakage) per axis-map §"Pre-computed cells in snapshot"
  Re-run each on bench-v1-K5-filtered so they count toward the re-benchmark
  Per-cell run.json + paired CI vs prior pre-leakage run logged with a note that the numbers are NOT comparable to the old bench-v1-K5 cells
  Champion table (FARM-EXP.4) updated where the leakage-free re-run changes the winner
estimated_hours: 12
priority: P1
tags: [benchmark, lineage]
requires_human: false
```

**Goal**: reuse the pre-computed coverage rather than starting from
scratch; ~80-100 cells already trained.

**Repos touched**: protea-reranker-lab.

**Out of scope**:
1. Re-running cells that never trained against ESMC-300M (those land
   in FARM-EXP.8).

**Notes**: Cites `context/experiment-axis-map.md §"Pre-computed cells
in snapshot"` + thesis Tab `tab:improvement` warning that
bench-v1-K5 and bench-v1-K5-filtered rows are not comparable.
Suggested agent: bioinfo-quick.

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
deps: [FARM-EXP.3, FARM-EXP.4, FARM-EXP.8, FARM-EXP.9]
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
