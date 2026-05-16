# D32. lab-runner plan loop vs bioinfo-quick agent

- Status: accepted
- Date: 2026-05-16
- Driver: FARM-FEAT.5 (Resolve dangling lab-runner plan loop)
- Author: executor agent on behalf of Francisco Miguel Pérez Canales

## Context

agent-farm had an orphan plan loop. `plans/lab-runner/PLAN.md` listed 12
research slices (LB / LR / LM / LP phases) whose YAML frontmatter declared
`loop: lab-runner`, yet no agent named `lab-runner` existed in `agents/` or
`prompts/`. The bioinfo-quick agent (sonnet, subagent, kind=subagent)
already covered the experiment-cycle workflow described in those slices.

The F-EXP-RESET phase of `plans/farm-platform/PLAN.md` (FARM-EXP.1 through
FARM-EXP.11) plans to land work onto this loop. Closing the orphan was a
prerequisite before that benchmark phase could start, otherwise the
spawn pipeline would have no agent to dispatch.

FARM-FEAT.5's acceptance criteria offered two paths:

- **A**: add `agents/lab-runner.yaml` + `prompts/lab-runner.md` with a
  broader scope than bioinfo-quick (lab benchmark + champion tracking +
  experiment scheduling), update the conductor menu.
- **B**: rename `plans/lab-runner/` to `plans/bioinfo-quick/` so render.py
  picks up the directory under bioinfo-quick's name, update the 12 slice
  `loop:` fields and the prose cross-references.

## Decision

Path **B** (rename).

## Rationale

1. **Lower maintenance**. Path A would have created a second lab-tier
   subagent whose worktree, model tier, timeout, permissions and tool
   allowlist would have duplicated `agents/bioinfo-quick.yaml` almost
   verbatim. Two near-identical agents diverge slowly and demand
   parallel updates each time the lab workflow shifts (poetry version,
   eval script path, MEMORY.md location, etc.).

2. **render.py is rename-aware by construction**. The script discovers
   loop directories by listing `plans/*/PLAN.md`. Once the directory
   is renamed and the slice `loop:` fields match the new directory
   name, the master `plans/PLAN.md` regenerates with no code change.
   Slice anchors and the slice count are preserved.

3. **Conductor menu already lists bioinfo-quick**. `prompts/conductor.md`
   line 108 and `README.md` line 52 already advertise bioinfo-quick as
   the lab-tier agent. Path A would have introduced a new agent name
   (lab-runner) that the conductor would have had to learn, plus a
   reasonable risk that the conductor would oscillate between the two
   when picking spawn targets.

4. **Scope mismatch is bounded and recoverable**. Some slices in the
   loop (LP.1 pull_dataset resilience, LM.1 champion tracking system,
   LB.3 paired CI per cell) are tooling work rather than the
   experiment-cycle pattern that bioinfo-quick's prompt focuses on. The
   conductor handles this by reading each slice body before spawn: when
   a slice is tooling-flavoured, an executor against the lab worktree
   is the right pick. The plan loop name is the *ownership label* for
   the slice family; it need not be 1:1 with the spawned agent type
   for every individual slice.

5. **F-EXP-RESET already documented this expectation**. FARM-EXP.2's
   suggested-agent note read `"lab-runner (or bioinfo-quick if
   FARM-FEAT.5 chose the rename path)"`. The conditional is closed by
   choosing B.

6. **Reversibility cost is low**. If the scope mismatch becomes
   blocking, a follow-up slice can widen `prompts/bioinfo-quick.md`
   (extra Option E/F/G entries plus a tooling-mode branch). That is a
   smaller change than splitting an established two-agent zoo back
   into one.

## Consequences

### Positive

- bioinfo-quick is the canonical owner of the 12 research slices.
  Slice spawn no longer fails with "agent not found".
- The agent zoo stays at its current cardinality (10 named agents in
  the README, conductor menu unchanged).
- Future slice additions to the lab loop write `loop: bioinfo-quick`,
  matching the directory and the spawn target.
- The F-EXP-RESET phase (FARM-EXP.2 through FARM-EXP.11) can now reach
  spawn without further plumbing.

### Negative / accepted trade-offs

- `prompts/bioinfo-quick.md` is narrower than the union of lab-loop
  slice scopes. Tooling-flavoured slices (LP.1, LM.1, LB.3) require
  the conductor to either widen the spawn prompt inline or dispatch
  an executor against the lab worktree. This is acceptable today and
  flagged for re-evaluation if the tooling slice traffic increases.
- The slice id `FARM-FEAT.5` and its anchor in the master plan retain
  the historical title `Resolve dangling lab-runner plan loop`. That
  is intentional historical record; future readers see the original
  problem statement plus this ADR.
- A path under `~/.claude/projects/.../memory/loops/lab-runner/MEMORY.md`
  referenced from `prompts/bioinfo-quick.md` line 10 is *not* renamed
  by this change. That memory store lives under the developer's
  Claude Code state, not under the agent-farm repo. Renaming it is a
  one-line manual `mv` outside of this slice's scope and the prompt
  reference can stay as-is until that memory file is itself moved.

## Implementation summary

- `git mv plans/lab-runner plans/bioinfo-quick`.
- Twelve `loop: lab-runner` lines under the renamed PLAN.md rewritten
  to `loop: bioinfo-quick`.
- Top-of-file heading renamed.
- Prose cross-references updated in:
  - `plans/README.md` (layout tree + schema spec).
  - `plans/thesis-writer/PLAN.md` (TC.6 acceptance prose).
  - `plans/executor/PLAN.md` (T-RES.2 acceptance + janitor note).
  - `plans/farm-platform/PLAN.md` (suggested-agent notes for FARM-EXP.2,
    .3, .4, .7, .8, .9, .10 plus the FARM-FEAT.5 resolution note).
- `python3 plans/render.py` re-ran; `plans/PLAN.md` regenerated with
  the same 159-slice / 169-table-row count as before.
- New `docs/decisions/` directory bootstrapped with this file.

## Notes on the ADR convention

The agent-farm repo had no `docs/decisions/` directory before this
slice. PROTEA's repo uses an `.rst` + Sphinx convention. agent-farm is
not Sphinx-built, so this ADR is plain markdown with a numbered prefix
(`D32-`) to match the broader Thesis2 decision-numbering line.
