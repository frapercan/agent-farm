---
description: Display status of running and recent tasks
---

Run `bash ~/Thesis2/agent-farm/scripts/status.sh $ARGS` where $ARGS is optional (e.g., a specific task_id or `--all` for full history). Default shows live tasks only. Report the tabla (table) of tasks with their status, start time, and result. Caveat: supervisor/heartbeat logs are in `tmux attach -t agent-farm`.
