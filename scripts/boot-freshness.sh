#!/usr/bin/env bash
# boot-freshness.sh — DEPRECATED. Forwards to boot.sh.
#
# Kept for backward-compat with existing callers (bootstrap-autowork.md,
# cron, documentation). All real work has moved to scripts/boot.sh which
# is the unified 14-invariant diagnostic.
#
# Arg translation:
#   --no-pull → --audit-only  (boot.sh never auto-pulls anything anyway,
#                              but audit-only also disables the two safe
#                              auto-fixes for parity with the old "audit"
#                              semantics)
#   --json    → ignored (boot.sh emits plain text only; pipe to a parser
#                        if you need structured output)
#
# Exit codes follow boot.sh's contract:
#   0 = green/amber
#   1 = at least one FAIL
#   2 = SALVAGE CANDIDATES

set -uo pipefail
ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

NEW_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --no-pull) NEW_ARGS+=("--audit-only") ;;
    --json)    : ;;   # silently drop
    *)         NEW_ARGS+=("$arg") ;;
  esac
done

exec bash "$ROOT/scripts/boot.sh" "${NEW_ARGS[@]:-}"
