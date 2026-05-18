---
name: cleanup-modes
section: "8-cleanup-modes"
state: working
owner: agent-farm conductor loop
source:
  - agents/_template.yaml
  - scripts/cleanup.sh
  - scripts/finalize-subagent.sh
  - docs/decisions/D31-per-action-worktree.md
runbook: docs/features/cleanup.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/_template.yaml'))"
---

# cleanup-modes

The `worktree.cleanup` axis in `agents/*.yaml` is binary: `ephemeral`
or `none`. `ephemeral` deletes the worktree at task end; `none` leaves
a stable path that `cleanup.sh` refuses to touch (the agent yaml must
declare `worktree.path` so the protection target is explicit). ADR
**D31** (`docs/decisions/D31-per-action-worktree.md`) records the
removal of a third `per_action` option that was documented in
`_template.yaml` but never adopted by any agent.

## Source coordinates

- `agents/_template.yaml` (documents the two modes)
- `scripts/cleanup.sh` (honours `cleanup: none` protected paths)
- `scripts/spawn.sh`, `scripts/spawn-subagent.sh` (skip worktree
  creation when `cleanup == "none"`)
- `scripts/finalize-subagent.sh` (skips teardown when
  `cleanup == "none"`)
- `docs/decisions/D31-per-action-worktree.md`

## State

working. Both values are used in production. `ephemeral` is the
default for executor / janitor / bioinfo-quick / shepherd / doc-writer
/ thesis-writer / ux-reviewer / frontend-designer / playwright-platform.
`none` is used by deploy-keeper (stable
`~/Thesis2/worktrees/protea-deploy`) and embeddings-runner (HTTP-only
against PROTEA's API, no worktree at all).

## Smoke test

```bash
python3 -c "
import yaml, glob
for f in glob.glob('agents/*.yaml'):
    d = yaml.safe_load(open(f))
    if d.get('worktree'):
        print(d['name'], d['worktree'].get('cleanup'))
"
```

Expected output: every agent prints either `ephemeral` or `none`. Any
other value is a yaml drift and should be reverted to one of the two
canonical values.

## Runbook

- Choose mode per agent in its yaml.
- `cleanup: none` requires a `worktree.path` so `cleanup.sh` can
  protect it.
- A future agent that needs a fresh worktree per action (not per task)
  is the trigger for revisiting D31; today there is no such caller.

## Current owner

agent-farm conductor loop.
