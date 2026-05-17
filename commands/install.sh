#!/bin/bash
# Install agent-farm slash commands to ~/.claude/commands/

set -euo pipefail

COMMANDS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_COMMANDS="${HOME}/.claude/commands"

# Ensure target directory exists
mkdir -p "$CLAUDE_COMMANDS"

# Count before
before=$(ls -1 "$CLAUDE_COMMANDS"/agent-farm-* 2>/dev/null | wc -l)

# Install (copy) each command file
for cmd in agent-farm-{conductor,agents,spawn,status,kill,cleanup,plan}.md; do
  src="$COMMANDS_DIR/$cmd"
  dst="$CLAUDE_COMMANDS/$cmd"

  if [ ! -f "$src" ]; then
    echo "ERROR: source not found: $src" >&2
    exit 1
  fi

  cp "$src" "$dst"
done

# Count after
after=$(ls -1 "$CLAUDE_COMMANDS"/agent-farm-* 2>/dev/null | wc -l)

echo "Installed ${after} agent-farm slash commands to $CLAUDE_COMMANDS"
echo "Before: $before, After: $after"
echo ""
echo "Available commands:"
ls -1 "$CLAUDE_COMMANDS"/agent-farm-*.md | xargs -I {} basename {}
