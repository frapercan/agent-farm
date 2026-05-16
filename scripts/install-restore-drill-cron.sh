#!/usr/bin/env bash
# install-restore-drill-cron.sh -- FARM-1.7
#
# Install (or re-install) the weekly cron entry that runs
# scripts/restore-drill.sh against the latest postgres dump.
#
# Idempotent: any prior entry tagged `# FARM-1.7-restore-drill` is
# removed before the new one is appended.
#
# Usage:
#   bash scripts/install-restore-drill-cron.sh           # install/refresh
#   bash scripts/install-restore-drill-cron.sh --remove  # uninstall
#   bash scripts/install-restore-drill-cron.sh --dry-run # print, do not modify

set -euo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TAG="# FARM-1.7-restore-drill"
SCHEDULE="${RESTORE_DRILL_SCHEDULE:-30 4 * * 0}"   # Sun 04:30 by default
LOG_FILE="${RESTORE_DRILL_LOG:-$ROOT/state/logs/restore_drill.log}"
LINE="$SCHEDULE cd $ROOT && bash scripts/restore-drill.sh >> $LOG_FILE 2>&1 $TAG"

MODE="install"
for arg in "$@"; do
  case "$arg" in
    --remove)  MODE="remove";;
    --dry-run) MODE="dryrun";;
    --help|-h)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "unknown arg: $arg" >&2; exit 2;;
  esac
done

CURRENT=$(crontab -l 2>/dev/null || true)
# Strip any prior FARM-1.7-restore-drill entry.
FILTERED=$(printf '%s\n' "$CURRENT" | grep -vF "$TAG" || true)

case "$MODE" in
  install)
    NEW=$(printf '%s\n%s\n' "$FILTERED" "$LINE" | sed '/^$/N;/^\n$/D')
    printf '%s\n' "$NEW" | crontab -
    echo "[install-restore-drill-cron] installed:"
    echo "  $LINE"
    ;;
  remove)
    printf '%s\n' "$FILTERED" | crontab -
    echo "[install-restore-drill-cron] removed $TAG entries"
    ;;
  dryrun)
    echo "[install-restore-drill-cron] DRY-RUN; would install:"
    echo "  $LINE"
    echo "[install-restore-drill-cron] crontab AFTER would be:"
    printf '%s\n%s\n' "$FILTERED" "$LINE" | sed '/^$/N;/^\n$/D'
    ;;
esac
