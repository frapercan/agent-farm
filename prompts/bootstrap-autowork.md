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

1. `bash ~/Thesis2/agent-farm/scripts/status.sh` — sanity check.
2. If deploy-keeper is NOT running, spawn it now (headless):
   `bash ~/Thesis2/agent-farm/scripts/spawn.sh deploy-keeper`.
   If the user explicitly said "no deploy hoy", skip this.
3. Spawn shepherd as a subagent (sonnet, background). When it returns
   its coord.md, read the top 3 recommendations.
4. Based on shepherd:
   - Spawn **executor** in background on the top P0/P1 slice from
     `plans/executor/PLAN.md` (unless requires_human or deps unmet).
   - Spawn **thesis-writer** in background on the top slice from
     `plans/thesis-writer/PLAN.md` if there is one pending.
   - Spawn **doc-writer** in background on the top slice from
     `plans/doc-writer/PLAN.md` if there is one pending.
   - Spawn **janitor** only if shepherd recommends it (red CI or
     landmine), background.
5. Report to the user in ≤8 lines: what got spawned with which slice,
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
- Final report: what was completed this session, what PRs are open,
  what's left for next session.

## Hard rules (carried over from CLAUDE.md)

- No `--no-verify`, no force-push, no stash, no Claude/AI mentions in
  commits or PRs.
- Never touch `~/Thesis2/repositories/PROTEA` directly — always via
  ephemeral worktree.
- Convert relative dates to absolute when saving anything.
- 4-thread parallelism is the default; never serialize for "safety"
  unless deps in the plan force it.
