---
name: cleanup
section: "4-lifecycle"
state: working
owner: agent-farm conductor loop
source:
  - scripts/cleanup.sh
runbook: docs/features/README.md
smoke: bash scripts/cleanup.sh
---

# cleanup

GC: detects crashed tasks (sqlite says running, tmux + pid both gone),
removes orphaned tmux windows, removes orphaned worktrees across every
repo under `~/Thesis2/repositories/` plus `~/Thesis2/thesis`. Default is
report-only; `--apply` actually removes.

## Source coordinates

- `scripts/cleanup.sh`
- `scripts/lib/zombie_reconcile.py`

## State

working. Companion test: `tests/test_zombie_reconcile.py`.

## Smoke test

```bash
bash -n scripts/cleanup.sh
bash scripts/cleanup.sh 2>&1 | head -20
python3 -m pytest tests/test_zombie_reconcile.py -q
```

## Runbook

- `bash scripts/cleanup.sh` → dry-run report.
- `bash scripts/cleanup.sh --apply` → actually clean.
- Protected paths (worktree.path in agent yaml with cleanup: none) are
  skipped even with `--apply`.

## Current owner

agent-farm conductor loop.
