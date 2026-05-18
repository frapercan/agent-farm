---
name: commands-install
section: "5-slash-commands"
state: working
owner: agent-farm conductor loop
source:
  - commands/install.sh
runbook: docs/features/README.md
smoke: bash -n commands/install.sh
---

# commands-install

One-shot installer that copies the 7 `/agent-farm-*` slash command
markdown files to `~/.claude/commands/`. Idempotent.

## Source coordinates

- `commands/install.sh`

## State

working.

## Smoke test

```bash
bash -n commands/install.sh
```

## Runbook

- `bash commands/install.sh` once per workstation.
- Re-run after pulling new commands.

## Current owner

agent-farm conductor loop.
