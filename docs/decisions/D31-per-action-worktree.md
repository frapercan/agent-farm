# D31. Per-action cleanup mode: delete the unused option

- Status: accepted
- Date: 2026-05-18
- Driver: FARM-FEAT.3 (Decide on per_action cleanup mode)
- Author: executor agent on behalf of Francisco Miguel Pérez Canales

## Context

`agents/_template.yaml` documents three values for the `worktree.cleanup`
axis: `ephemeral`, `per_action`, `none`. The first two delete the
worktree once the agent finishes; the third keeps a stable path that
`scripts/cleanup.sh` refuses to touch (`worktree.path` declares the
protected location).

Audit of `agents/*.yaml` (2026-05-18, this slice):

- `bioinfo-quick`: ephemeral.
- `deploy-keeper`: none, with stable `worktree.path` of
  `~/Thesis2/worktrees/protea-deploy`.
- `doc-writer`: ephemeral.
- `embeddings-runner`: none. HTTP-only against PROTEA's API, so no
  worktree at all.
- `executor`: ephemeral.
- `frontend-designer`: ephemeral.
- `janitor`: ephemeral.
- `playwright-platform`: ephemeral.
- `shepherd`: ephemeral.
- `thesis-writer`: ephemeral.
- `ux-reviewer`: ephemeral.

No agent declares `cleanup: per_action`. The spawn machinery does not
branch on the value either: `scripts/spawn.sh`, `scripts/spawn-subagent.sh`
and `scripts/finalize-subagent.sh` all treat `worktree.cleanup != "none"`
as a single ephemeral path (create on spawn, remove on finalize).
`scripts/cleanup.sh` only reads the value to discover protected paths
(those with `cleanup: none` plus a declared `worktree.path`). There is
no per-action code path to remove.

The slice acceptance frames the choice as a binary:

1. **Adopt** per_action for deploy-keeper: re-architect
   `deploy-keeper-supervisor.sh` to create a fresh worktree per tick and
   tear it down post-tick.
2. **Delete** the mode from `_template.yaml`; the unused option stops
   lingering as undocumented aspiration.

Cited memory pointer: `context/feature-inventory.md` section 8.2 plus
section 12.5 (`per_action` documented but no agent uses it).

## Decision

Path **2** (delete).

The canonical `worktree.cleanup` axis is now binary: `ephemeral` or
`none`. `_template.yaml` documents both with their use cases; no third
mode is offered.

## Rationale

1. **Deploy-keeper does not want a fresh worktree per tick.** Its
   `agents/deploy-keeper.yaml` comments explicitly state the existing
   `worktree.path: ~/Thesis2/worktrees/protea-deploy` is reused across
   ticks "for Docker/npm cache reuse. DO NOT ephemeralize." A per-tick
   wipe would invalidate the npm install cache, the Next.js `.next`
   cache, the Docker layer cache pulled by `docker compose`, and the
   PROTEA Poetry virtualenv. Tick latency would balloon from seconds
   to minutes, the exact opposite of what the supervisor needs to
   respond to `new_commit_on:origin/develop` quickly.

2. **No other agent has asked for the mode either.** The eleven
   non-deploy agents are content with one of the two existing values.
   The slice's own "Out of scope" rules out building a per_action
   option for non-deploy agents (`FARM-FEAT.3`, line "Building a
   per_action option for non-deploy agents"). With deploy-keeper out
   plus non-deploy agents out, no caller remains.

3. **Two modes are easier to reason about than three.** Documentation
   today says one mode is "live, partial, never used". A reader has to
   resolve that ambiguity by reading the spawn scripts. Removing the
   option collapses the axis to "deleted on exit" vs "stable, protected"
   and matches the two code paths that actually exist in `spawn.sh` and
   `finalize-subagent.sh`.

4. **Reversibility is cheap.** If a future agent does need
   per-action behaviour (e.g. a sandboxed runner that wants a clean
   filesystem between actions), it can be reintroduced as a new ADR
   plus the matching code path. Deleting now does not lock the door;
   it just stops paying maintenance interest on a feature with no
   tenant.

5. **Symmetric with the deploy-keeper service.triggers resolution.**
   `FARM-FEAT.4` made the `service.triggers` field load-bearing rather
   than human-readable. Here the symmetric move closes the other side
   of the same observation: an axis present in the template but never
   exercised is documentation debt. Either implement it or strike it.

## Consequences

### Positive

- `agents/_template.yaml` now describes the axis honestly: two values,
  both with at least one production tenant.
- `docs/features/cleanup-modes.md` flips from `state: partial` to
  `state: working`. The features-coverage gate stops carrying a
  permanent "partial" flag on this capability.
- New agents added to `agents/*.yaml` cannot accidentally declare a
  silently-unsupported `per_action` and discover the gap at runtime;
  the option is no longer offered.
- `cleanup.sh` and `finalize-subagent.sh` keep their existing single
  branch on `cleanup != "none"`; no script touched.

### Negative / accepted trade-offs

- A future agent that wants per-action behaviour will need a fresh
  ADR plus implementation work. That cost is appropriate: the
  reintroduction should be motivated by an actual caller, not by a
  template entry.
- The slice acceptance also mentioned `cleanup.sh special-case
  removed`. There is no such special-case to remove; `cleanup.sh`
  only reads `cleanup` to populate the protected-paths set
  (`cleanup == "none"` + `worktree.path`). This ADR is the contract
  that no special-case exists or should be added.

## Implementation summary

- `agents/_template.yaml`: the `cleanup:` comment block now lists
  two values (`ephemeral`, `none`). The deleted line is the
  `per_action` description.
- `docs/features/cleanup-modes.md`: prose rewritten to two-mode form,
  state flipped to `working`, smoke test unchanged.
- `docs/features/decisions-adr.md`: source list extended with this
  ADR path.
- `plans/farm-platform/PLAN.md` (FARM-FEAT.3 block): status set to
  `done`, resolution prose appended.
- `plans/PLAN.md`: regenerated via `python3 plans/render.py` in the
  same commit so the master index reflects the new slice state.
- No agent yamls touched. None of the eleven non-template yamls
  declared `per_action`, so no migration is required.
- No script touched. `scripts/spawn.sh`, `scripts/spawn-subagent.sh`,
  `scripts/finalize-subagent.sh` and `scripts/cleanup.sh` already
  treat `cleanup != "none"` as the single ephemeral path; the unused
  third branch never existed in code.

## Notes on the ADR convention

The slice acceptance pinned the ADR number to `D31`. The previously
written ADRs are `D32` (lab-runner vs bioinfo-quick, 2026-05-16) and
`D33` (cafaeval-protea scope, 2026-05-17). `D31` was reserved for this
slice ahead of time; this file fills that reservation.
