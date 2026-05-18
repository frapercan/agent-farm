---
name: /agent-farm-conductor
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/agent-farm-conductor.md
  - commands/install.sh
runbook: docs/features/README.md
smoke: test -s commands/agent-farm-conductor.md
---

# /agent-farm-conductor

Slash command that loads the conductor identity (system prompt +
bootstrap-autowork loop) inside any Claude Code session. Materialised by
FARM-FEAT.1.

## Source coordinates

- `commands/agent-farm-conductor.md`
- `commands/install.sh` (copy to `~/.claude/commands/`)

## State

working. All 7 slash commands shipped via FARM-FEAT.1.

## Smoke test

```bash
test -s commands/agent-farm-conductor.md && echo OK
grep -q prompts/conductor.md commands/agent-farm-conductor.md && echo binds-conductor
```

## Runbook

- Install once: `bash commands/install.sh`.
- Use anywhere: type `/agent-farm-conductor`.

## Current owner

agent-farm conductor loop.
