# Bootstrap autowork — what the conductor does on session entry

This is the canonical session opener. The launch-conductor.sh tmux flow
pastes a single line that points the conductor at this file. The
conductor reads it, runs the boot sequence in order, and reports back.

## Read first

- `~/Thesis2/agent-farm/prompts/conductor.md` (operating manual)
- `~/Thesis2/CLAUDE.md` (hard constraints)

## The 4 parallel threads (steady state)

Once boot is green and the user has explicitly OK'd spawning, the farm
runs four threads concurrently:

1. **Plan execution** (executor, opus) — one slice at a time from
   `plans/executor/PLAN.md`. Picks the highest-priority unblocked slice
   per shepherd's recommendation.
2. **Operational reactive** (deploy-keeper persistent + janitor on
   demand). deploy-keeper holds `develop` deployed at protea.ngrok.app;
   janitor only fires when shepherd flags a red CI PR or a 1-line
   landmine.
3. **Documentation** (doc-writer, sonnet) — one slice at a time from
   `plans/doc-writer/PLAN.md` when there is one pending.
4. **Thesis** (thesis-writer, sonnet) — one slice at a time from
   `plans/thesis-writer/PLAN.md` when there is one pending. Worktree is
   in `~/Thesis2/thesis`, NOT PROTEA — they don't collide with executor.

All four threads run as background `Agent(run_in_background=true)` calls
so the user can chat with you while they run.

## Boot sequence (do this when the user says "go" or pastes the prompt)

The boot is **diagnose-first**. You do not auto-revive the API stack,
auto-pull agent-farm, auto-relaunch deploy-keeper, purge the DLQ, or
reset ghost jobs. You diagnose, report, and wait for the user before
spawning any agents. The script handles two cero-risk auto-fixes for
you (`_siblings/*` prune, dev-hooks install). See memory
`feedback_boot_diagnostic_first` for the rationale.

### Step 0 — run the diagnostic

```bash
bash ~/Thesis2/agent-farm/scripts/boot.sh
```

This runs the 14-invariant audit + the 2 auto-fixes. Read the exit code:

| Exit | Meaning | What you do |
|------|---------|-------------|
| 0    | green/amber — only WARN/OK lines, or all FAILs were resolved | report and wait for user OK |
| 1    | at least one `[FAIL]` — user action required before spawning | report and STOP. Surface each FAIL with its suggested command. Do NOT auto-run those commands. |
| 2    | SALVAGE CANDIDATES — worktrees with dirty/unpushed/unmerged work | report and STOP. Ask the user how to resolve each candidate. Never `git worktree remove` a salvage candidate. |

### Step 1 — advisory checks (still part of the report)

These run regardless of boot.sh exit code; they are advisory only.

```bash
# memory-to-prompt drift linter (FARM-2.6)
python3 ~/Thesis2/agent-farm/scripts/memory-prompt-drift.py \
  --memory-dir ~/.claude/projects/-home-frapercan-Thesis2/memory/ \
  --prompts-dir ~/Thesis2/agent-farm/prompts/ \
  --quiet
# read stale_count from the JSON output

# cost-budget rollup (FARM-FEAT.8)
python3 ~/Thesis2/agent-farm/scripts/lib/budget_check.py overages --only-alerts
# each line = an agent in the NEAR (>=80%) or OVER (>100%) band
```

Include in the boot report as:

```
Drift linter: N stale entries.
Cost budget: K agent(s) near/over cap.
```

If N > 0, list them as bullets. If any OVER lines appear, list them.
Neither blocks anything.

### Step 2 — STOP and report

Output to the user, in this order:

1. The `boot.sh` classified output (FAIL → SALV → WARN → OK lines).
2. The advisory linter + cost-budget summary.
3. One sentence: "Awaiting your OK before spawning agents."

**Do NOT spawn ANY agent yet.** Not shepherd, not deploy-keeper, not
executor. The user explicitly asked to see the plan first.

### Step 3 — wait for the user

The user will respond with either:

- "OK, spawn" / "adelante" / "go ahead" → proceed to Step 4.
- Specific corrections ("first restart the stack", "ignore the
  protea-deploy stale warning, that's expected today") → adjust and ask
  again.
- "no deploy hoy" / "polish only" → flag for Step 4 (skip
  deploy-keeper).

### Step 4 — once the user OKs, spawn

Spawn the 4 threads, respecting these gates:

- **deploy-keeper**: spawn only if BOTH conditions hold:
  - `protea.training` RMQ queue is empty (`docker exec
    protea-rabbitmq-1 rabbitmqctl list_queues -q name messages | awk
    '$1=="protea.training"{print $2}'` returns 0), AND
  - no `job` rows are `RUNNING` for operation `export_research_dataset`
    or any other long-running export (psql lookup).

  Otherwise deploy-keeper would restart the stack mid-export and kill
  the worker (memories `feedback_deploykeeper_vs_export_stack_conflict`
  and `project_deploy_keeper_paused_2026_05_23`).

  Also skip if the user said "no deploy hoy".

  Spawn command: `bash ~/Thesis2/agent-farm/scripts/spawn.sh deploy-keeper`.

- **shepherd**: spawn as subagent (sonnet, background) for top-3
  recommendations.

- **executor**: spawn on the top P0/P1 slice from
  `plans/executor/PLAN.md`, unless it is `requires_human` or has unmet
  deps.

- **doc-writer / thesis-writer**: spawn each if its PLAN has a pending
  slice.

- **janitor**: only if shepherd recommends it (red CI / landmine).

Report to the user: ≤8 lines, what got spawned with which slice + any
threads you skipped and why.

## Steady-state rules

- When an Agent returns, **always** call `finalize-subagent.sh` to close
  out the task and clean its worktree. Never skip.
- Right after finalize, if the slice ID has a successor in the same
  loop and capacity allows, spawn the next slice (same agent type,
  background).
- Keep no more than 1 executor, 1 thesis-writer, 1 doc-writer in flight
  at a time — they compete for the user's attention if they all finish
  at once. Multiple janitors are fine; they are short.
- Heartbeat to the user every ~30 min by reading `status.sh` and
  reporting changes since last heartbeat. One line per change.

## When the user says "stop" or "stop autowork"

- Do NOT kill subagents in flight; they finish what they started.
- Stop accepting new spawn cycles.
- Run the audit-only diagnostic so the user sees what state the farm
  is in on exit:

  ```bash
  bash ~/Thesis2/agent-farm/scripts/boot.sh --audit-only
  ```

  Surface any `[SALV]` lines so the user can decide whether to commit,
  push, or finalize them before walking away. Never `git worktree
  remove` a dirty/unmerged worktree.
- Final report: what was completed this session, what PRs are open,
  what's left for next session, and any worktrees the user must resolve
  manually.

## Manual deploy of develop (when the user asks)

Canonical command (the `manage.sh` script lives under `scripts/`, not
at the repo root; `.env` does NOT auto-source):

```bash
cd ~/Thesis2/worktrees/protea-deploy \
  && git fetch origin && git reset --hard origin/develop \
  && poetry install --sync \
  && set -a && source .env && set +a \
  && bash scripts/manage.sh restart
```

Then expose via ngrok in its own terminal:

```bash
bash scripts/expose.sh   # foreground; serves https://protea.ngrok.app
```

## Hard rules (carried over from CLAUDE.md)

- No `--no-verify`, no force-push, no stash, no Claude/AI mentions in
  commits or PRs.
- Never touch `~/Thesis2/repositories/PROTEA` directly — always via
  ephemeral worktree.
- Convert relative dates to absolute when saving anything.
- 4-thread parallelism is the default; never serialize for "safety"
  unless deps in the plan force it.
