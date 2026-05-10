#!/usr/bin/env bash
# init.sh — initialize agent-farm state from schema.sql. Idempotent.
#
# Usage:
#   bash ~/Thesis2/agent-farm/scripts/init.sh

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
python3 "$ROOT/scripts/lib/db.py" init
