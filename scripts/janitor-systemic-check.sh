#!/usr/bin/env bash
# janitor-systemic-check.sh — thin wrapper around redcheck-systemic.py (FARM-1.5).
#
# Usage:
#   bash scripts/janitor-systemic-check.sh [--pretty]
#
# The wrapper delegates to the canonical Python tool with preset options
# for the janitor workflow (canonical stack, threshold=3, pretty output).

set -eu

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PYTHON_TOOL="$SCRIPT_DIR/lib/redcheck-systemic.py"

if [[ ! -f "$PYTHON_TOOL" ]]; then
  echo "janitor-systemic-check: $PYTHON_TOOL not found" >&2
  exit 2
fi

python3 "$PYTHON_TOOL" --threshold 3 "$@"
