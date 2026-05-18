---
name: worktree-guard
section: "7-worktree"
state: working
owner: agent-farm conductor loop
source:
  - scripts/lib/worktree-guard.sh
runbook: scripts/lib/README-hooks.md
smoke: bash -n scripts/lib/worktree-guard.sh
---

# worktree-guard

Asserts that the current working directory is a fresh worktree (not the
developer's main checkout). Sourced at the top of every executor /
janitor / doc-writer script run so a misconfigured prompt cannot
accidentally edit `~/Thesis2/repositories/PROTEA/` directly.

## Source coordinates

- `scripts/lib/worktree-guard.sh`

## State

working. Tested via `tests/test_worktree_guard.py`.

## Smoke test

```bash
bash -n scripts/lib/worktree-guard.sh
python3 -m pytest tests/test_worktree_guard.py -q
```

## Runbook

- `bash scripts/lib/worktree-guard.sh assert "$PWD"` at agent start.
- Memory `feedback_janitor_must_use_worktree` is the motivation.

## Current owner

agent-farm conductor loop.
