#!/usr/bin/env bash
# Idempotent installer for the nightly PROTEA pg_dump cron.
# Usage: bash scripts/install-nightly-pgdump-cron.sh [--apply]
# Without --apply: prints the proposed crontab entries and exits.
# With --apply: edits the user's crontab to include the entries if missing.
set -euo pipefail

BACKUPS_DIR="${BACKUPS_DIR:-$HOME/Thesis2/backups}"
PROTEA_PG_URL="${PROTEA_PG_URL:-postgresql://protea:protea@localhost:5432/protea}"

# Cron lines for nightly dump and retention
CRON_DUMP="0 3 * * * pg_dump --format=custom --no-owner --file=${BACKUPS_DIR}/protea-\$(date +\\%Y-\\%m-\\%d).dump ${PROTEA_PG_URL} 2>>${BACKUPS_DIR}/pgdump.log"
CRON_RETENTION="15 3 * * * find ${BACKUPS_DIR} -name 'protea-*.dump' -mtime +30 -delete"

# Check if running with --apply
APPLY=false
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=true
fi

# Function to check if a cron line exists
cron_line_exists() {
  local line="$1"
  crontab -l 2>/dev/null | grep -F "$line" >/dev/null 2>&1 || return 1
}

# Print what we would do
echo "Proposed nightly pg_dump cron entries:"
echo ""
echo "1. Daily dump at 03:00 (UTC):"
echo "   $CRON_DUMP"
echo ""
echo "2. Retention sweep at 03:15 (remove dumps >30 days old):"
echo "   $CRON_RETENTION"
echo ""

if [[ "$APPLY" == false ]]; then
  echo "To install these entries, run:"
  echo "  bash scripts/install-nightly-pgdump-cron.sh --apply"
  exit 0
fi

# Apply mode: merge into user's crontab
echo "Installing to crontab..."

# Create a temporary file with existing crontab + new entries
{
  crontab -l 2>/dev/null || true

  if ! cron_line_exists "$CRON_DUMP"; then
    echo "$CRON_DUMP"
  else
    echo "# (pg_dump entry already present)" >&2
  fi

  if ! cron_line_exists "$CRON_RETENTION"; then
    echo "$CRON_RETENTION"
  else
    echo "# (retention entry already present)" >&2
  fi
} | crontab -

echo "Crontab updated successfully."
echo ""
echo "Verify with: crontab -l | grep protea"
