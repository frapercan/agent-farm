# Bootstrap autowork — what the conductor does when the user says "go"

This is the canonical session opener for the conductor. Paste-able as a
single message. When the user wants to start a fresh day of parallel work,
the conductor reads this, executes the steps in order, and reports back.

## Read first

- `~/Thesis2/agent-farm/prompts/conductor.md` (your operating manual)
- `~/Thesis2/CLAUDE.md` (hard constraints)

## The 4 parallel threads

This farm runs four threads concurrently. Your job is to keep them flowing
without blocking the user:

1. **Plan execution** (executor, opus) — one slice at a time from
   `plans/executor/PLAN.md`. Picks the highest-priority unblocked slice
   per shepherd's recommendation.
2. **Operational reactive** (deploy-keeper persistent + janitor on demand).
   deploy-keeper holds `develop` deployed at protea.ngrok.app. janitor
   only fires when shepherd flags a red CI PR or a 1-line landmine.
3. **Documentation** (doc-writer, sonnet) — one slice at a time from
   `plans/doc-writer/PLAN.md` when there is one pending.
4. **Thesis** (thesis-writer, sonnet) — one slice at a time from
   `plans/thesis-writer/PLAN.md` when there is one pending. Worktree is
   in `~/Thesis2/thesis`, NOT PROTEA — they don't collide with executor.

All four threads run as background `Agent(run_in_background=true)` calls,
so the user can chat with you while they run.

## Boot sequence (do this when the user says "go" or pastes this prompt)

0. **Freshness probe** (mandatory, idempotent).
   `bash ~/Thesis2/agent-farm/scripts/boot-freshness.sh` — pulls
   `agent-farm` up to `origin/main` (ff-only) and audits every worktree
   under `~/Thesis2/worktrees/*` for dirty trees, unpushed commits, or
   branches not yet merged into the owning repo's trunk. Exit code 2
   means there are SALVAGE CANDIDATES; surface them to the user and
   resolve (commit+push, finalize, or human salvage) BEFORE spawning
   any new agents that might recreate the same problem. Never auto-prune.
   On session exit ("stop"), rerun with `--no-pull` and report.
1. `bash ~/Thesis2/agent-farm/scripts/status.sh` — sanity check.
2. Install dev-clone guards into the developer's workspace (FARM-1.4):
   `bash ~/Thesis2/agent-farm/scripts/install-dev-hooks.sh --all`.
   Idempotent; no-op if already installed.
3. Run the memory-to-prompt drift linter (FARM-2.6, advisory, non-blocking):
   ```bash
   python3 ~/Thesis2/agent-farm/scripts/memory-prompt-drift.py \
     --memory-dir ~/.claude/projects/-home-frapercan-Thesis2/memory/ \
     --prompts-dir ~/Thesis2/agent-farm/prompts/ \
     --quiet
   ```
   Read `stale_count` from the JSON output. Include it in the boot
   summary as: "Drift linter: N stale entries." If N > 0, list them
   as bullets. Do NOT block the boot sequence regardless of the count.
3b. Cost-budget rollup (FARM-FEAT.8, advisory, non-blocking). Run
   `python3 ~/Thesis2/agent-farm/scripts/lib/budget_check.py overages --only-alerts`.
   Each line names an agent currently in the `NEAR` (>= 80% of cap) or
   `OVER` (> 100% of cap) band against its `cost_budget.max_usd_per_day`
   advisory cap over the last 24h. Empty output prints
   `(no cost_budget alerts)`. Include the count in the boot summary as:
   "Cost budget: K agent(s) near/over cap." If any OVER lines appear,
   list them as bullets. Do NOT block the boot sequence regardless of K.
4. If deploy-keeper is NOT running, spawn it now (headless):
   `bash ~/Thesis2/agent-farm/scripts/spawn.sh deploy-keeper`.
   If the user explicitly said "no deploy hoy", skip this.
5. Spawn shepherd as a subagent (sonnet, background). When it returns
   its coord.md, read the top 3 recommendations.
6. Based on shepherd:
   - Spawn **executor** in background on the top P0/P1 slice from
     `plans/executor/PLAN.md` (unless requires_human or deps unmet).
   - Spawn **thesis-writer** in background on the top slice from
     `plans/thesis-writer/PLAN.md` if there is one pending.
   - Spawn **doc-writer** in background on the top slice from
     `plans/doc-writer/PLAN.md` if there is one pending.
   - Spawn **janitor** only if shepherd recommends it (red CI or
     landmine), background.
7. Report to the user in ≤8 lines: what got spawned with which slice,
   any threads you skipped and why. Do not block on user reply unless
   shepherd flagged a `requires_human` slice.

## Steady-state rules

- When an Agent returns, **always** call `finalize-subagent.sh` to close
  out the task and clean its worktree. Never skip.
- Right after finalize, if the slice ID has a successor in the same loop
  and capacity allows, spawn the next slice (same agent type, background).
- Keep no more than 1 executor, 1 thesis-writer, 1 doc-writer in flight
  at a time — they compete for the user's attention if they all finish
  at once. (Multiple janitors are fine; they are short.)
- Heartbeat to the user every ~30 min by reading status.sh and reporting
  changes since last heartbeat. One line per change.

## When the user says "stop" or "stop autowork"

- Do NOT kill subagents in flight; they finish what they started.
- Stop accepting new spawn cycles.
- Rerun the freshness probe in exit mode:
  `bash ~/Thesis2/agent-farm/scripts/boot-freshness.sh --no-pull`.
  Surface any SALVAGE CANDIDATES so the user can decide whether to commit,
  push, or finalize them before walking away. Never `git worktree remove`
  a dirty/unmerged worktree.
- Final report: what was completed this session, what PRs are open,
  what's left for next session, and any worktrees the user must
  resolve manually.

## Manual deploy of develop (when the user asks)

Canonical command (the `manage.sh` script lives under `scripts/`, not at
the repo root; `.env` does NOT auto-source):

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
