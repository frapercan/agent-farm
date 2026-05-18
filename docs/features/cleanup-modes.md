---
name: cleanup-modes
section: "8-cleanup-modes"
state: partial
owner: agent-farm conductor loop
source:
  - agents/_template.yaml
  - scripts/cleanup.sh
runbook: docs/features/cleanup.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/_template.yaml'))"
---

# cleanup-modes

The `worktree.cleanup` axis in `agents/*.yaml`: `ephemeral`,
`per_action`, `none`. Decides whether the worktree is deleted on task
end (ephemeral), recreated per action (per_action), or kept stable
(none, with `worktree.path` declaring the protected path).

## Source coordinates

- `agents/_template.yaml` (documents the three modes)
- `scripts/cleanup.sh` (honours `cleanup: none` protected paths)
- `scripts/finalize-subagent.sh` (handles ephemeral teardown)

## State

partial. `ephemeral` and `none` are both used in production. `per_action`
is documented in the template but no agent currently uses it. FARM-FEAT.3
schedules the decision (adopt for deploy-keeper or delete from template).

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

## Runbook

- Choose mode per agent in its yaml.
- `cleanup: none` requires a `worktree.path` so `cleanup.sh` can protect
  it.

## Current owner

agent-farm conductor loop.
