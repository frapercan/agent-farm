# deploy-keeper (placeholder, never invoked as an LLM)

deploy-keeper is a persistent headless service. Its supervisor runs
`scripts/services/deploy-keeper-tick.sh` every `poll_interval` and
records heartbeats to `state/tasks.sqlite`.

On non-prereq tick failure the supervisor escalates to a janitor
subagent via `scripts/spawn-subagent.sh janitor`. The janitor (not this
agent) reads the recent heartbeats and applies recovery.

This file exists only because `agents/deploy-keeper.yaml` historically
referenced a `system_prompt_file`. No Claude run ever loads it. Do not
delete unless `system_prompt_file:` is also removed from the agent
yaml.
