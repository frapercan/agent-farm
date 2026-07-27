#!/usr/bin/env bash
# Idempotent installer for the PROTEA cold-boot watchdog cron.
# Usage: bash scripts/install-watchdog-cron.sh [--apply]
# Without --apply: prints the proposed crontab entry and exits.
# With --apply: edits the user's crontab to include it, and repairs the entry in
# place if it is present but missing the `-o` flag.
#
# WHY THIS FILE EXISTS
# The watchdog line was hand-installed and lived only in the live crontab, so the
# one flag that makes it work at all was untracked. This records it.
#
# THE `-o` FLAG IS LOAD-BEARING. Do not drop it.
# `flock` holds the lock on an OPEN FILE DESCRIPTION, and cold-boot.sh starts the
# long-lived uvicorn + worker daemons, which INHERIT that descriptor. The lock is
# released only when every holder closes it, so without `-o` the watchdog cannot
# acquire the lock while the stack is up: it can only ever fire when the API and
# all workers are already dead, i.e. only for a total outage, which is the one
# case a reboot already fixes. Partial outages, which is what actually happens,
# are exactly what it can never see. Measured 2026-07-17: the frontend was down
# for hours behind a green API and the watchdog no-opped every 5 minutes.
# `flock -o` closes the descriptor before exec'ing the command, so the daemons do
# not inherit it while the flock parent still holds the lock for the duration of
# the run. Both properties were verified in a sandbox before this landed:
# the lock frees once cold-boot exits, and a concurrent run is still blocked.
set -euo pipefail

ROOT="${THESIS_ROOT:-$HOME/Thesis2}"
LOCK="/tmp/protea-coldboot.lock"
CRON_PATH="PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
TAG="# protea-watchdog"
CRON_LINE="*/5 * * * * ${CRON_PATH} /usr/bin/flock -n -o ${LOCK} bash ${ROOT}/agent-farm/scripts/cold-boot.sh --quiet >> ${ROOT}/storage/infra_state/watchdog.log 2>&1 ${TAG}"

APPLY=false
[[ "${1:-}" == "--apply" ]] && APPLY=true

echo "Proposed watchdog cron entry (every 5 minutes, silent when healthy):"
echo "  $CRON_LINE"
echo ""

current="$(crontab -l 2>/dev/null || true)"
existing="$(printf '%s\n' "$current" | grep -F "$TAG" || true)"

if [[ -n "$existing" ]]; then
  if printf '%s\n' "$existing" | grep -qE '/usr/bin/flock -n -o '; then
    echo "Already installed and carries -o. Nothing to do."
    exit 0
  fi
  echo "FOUND an existing watchdog line WITHOUT -o. It cannot fire while the stack"
  echo "is up (the daemons inherit the lock fd). Current:"
  echo "  $existing"
  echo ""
fi

if [[ "$APPLY" == false ]]; then
  echo "To install or repair, run:"
  echo "  bash scripts/install-watchdog-cron.sh --apply"
  exit 0
fi

backup="${ROOT}/storage/infra_state/crontab.backup.$(date +%Y%m%d-%H%M%S)"
mkdir -p "$(dirname "$backup")"
printf '%s\n' "$current" > "$backup"
echo "Backed up crontab to $backup"

# Drop any prior watchdog line, then append the correct one. Every other entry,
# including the operator-authorised conductor-monitor, is preserved verbatim.
printf '%s\n' "$current" | grep -vF "$TAG" | { cat; printf '%s\n' "$CRON_LINE"; } | crontab -

echo "Installed."
crontab -l | grep -F "$TAG"
echo ""
echo "NOTE: daemons started by a PREVIOUS, un-fixed watchdog still hold the old"
echo "descriptor. The fix takes effect for ticks after the next stack restart."
