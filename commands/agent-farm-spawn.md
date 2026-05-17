---
description: Spawn an agent to run a task
---

Run `bash ~/Thesis2/agent-farm/scripts/spawn.sh $AGENT $SPEC` where $AGENT is the agent type (e.g., executor, janitor, deploy-keeper) and $SPEC is an optional JSON object with spawn arguments (e.g., `{"slice":"FARM-2.1","phase":"F-FEAT"}`). Report the task_id on success. For headless agents, the task runs in the background; for subagents, the task is dispatched via the Agent tool.
