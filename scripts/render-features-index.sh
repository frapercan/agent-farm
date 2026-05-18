#!/usr/bin/env bash
# render-features-index.sh — regenerate docs/features/README.md from the
# per-feature markdown files.
#
# Output: a tabla grouped by `section:` (frontmatter), one row per feature,
# columns: name, state, source-coords, smoke, runbook, owner.
#
# Usage:
#   bash scripts/render-features-index.sh           # write README.md
#   bash scripts/render-features-index.sh --check   # exit 1 if README.md is stale
#
# Companion: scripts/check-features-coverage.sh detects missing feature pages.

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
FEATURES_DIR="$ROOT/docs/features"
INDEX_FILE="$FEATURES_DIR/README.md"

MODE="${1:-write}"
case "$MODE" in
  --check) MODE=check ;;
  ""|--write|write) MODE=write ;;
  *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac

if [[ ! -d "$FEATURES_DIR" ]]; then
  echo "render-features-index: $FEATURES_DIR not found" >&2
  exit 1
fi

# Render to a temp file, then diff or move.
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

python3 "$ROOT/scripts/lib/features/render_index.py" "$FEATURES_DIR" > "$TMP"

if [[ "$MODE" == check ]]; then
  if ! diff -q "$INDEX_FILE" "$TMP" >/dev/null 2>&1; then
    echo "render-features-index: $INDEX_FILE is stale; run 'bash scripts/render-features-index.sh'" >&2
    diff -u "$INDEX_FILE" "$TMP" || true
    exit 1
  fi
  echo "render-features-index: index in sync"
  exit 0
fi

mv "$TMP" "$INDEX_FILE"
trap - EXIT
echo "render-features-index: wrote $INDEX_FILE"
