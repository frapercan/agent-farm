#!/usr/bin/env bash
# check-features-coverage.sh — drift gate for the per-feature docs surface.
#
# Fails when:
#   - A new agent yaml under agents/*.yaml has no matching docs/features/<name>.md
#     (excluding _template.yaml).
#   - A new top-level script under scripts/*.sh or scripts/*.py has no
#     docs/features/<name>.md referencing it in `source:`.
#   - A new persistent service under scripts/services/*.sh likewise.
#   - The rendered docs/features/README.md is stale.
#
# Reverse direction (feature page references a path that no longer exists)
# is reported as a warning, not a failure, because some pages legitimately
# describe out-of-tree artefacts (e.g. systemd unit files installed by a
# script).
#
# Usage:
#   bash scripts/check-features-coverage.sh           # report + exit code
#   bash scripts/check-features-coverage.sh --strict  # turn warnings into failures

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
FEATURES_DIR="$ROOT/docs/features"

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

python3 "$ROOT/scripts/lib/features/coverage.py" --root "$ROOT" $([[ $STRICT == 1 ]] && echo --strict)
coverage_rc=$?

if (( coverage_rc != 0 )); then
  exit "$coverage_rc"
fi

# Index freshness: re-render and diff.
bash "$ROOT/scripts/render-features-index.sh" --check
