---
description: Garbage-collect stale tmux sessions and worktrees
---

Run `bash ~/Thesis2/agent-farm/scripts/cleanup.sh` to scan for orphaned tmux windows and worktrees left behind by crashed or killed agents, and report what would be removed. To actually delete them, add `--apply`. Report the cleanup summary.
