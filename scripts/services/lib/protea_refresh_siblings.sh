#!/usr/bin/env bash
# Keep a frozen copy of every sibling stack repo on origin/develop, so
# the docs portal builds from the upstream tip regardless of whatever
# feature branch is checked out in the regular Thesis2/repositories/<slug>
# clones (where other agents may be doing live work).
#
# Per sibling: ensures the worktree path exists as a detached git worktree
# of the main clone, fetches origin, and hard-resets HEAD to origin/develop.
# Detached so it never collides with any branch the main clone has out.
#
# Exit codes:
#   0  no sibling advanced (all already on origin/develop tip)
#   10 at least one sibling advanced; deploy worktree should rebuild
#   20 a sibling failed to refresh (printed to stderr, others still tried)

set -uo pipefail

AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
REPOS_DIR="${PROTEA_REPOS_DIR:-$HOME/Thesis2/repositories}"
WORKTREES_DIR="${PROTEA_SIBLINGS_DIR:-$HOME/Thesis2/worktrees/_siblings}"
LOG_FILE="${PROTEA_SIBLINGS_LOG:-$AGENT_FARM_ROOT/state/logs/protea_siblings.log}"

mkdir -p "$(dirname "$LOG_FILE")"

# Slugs that have Sphinx docs in this stack. Kept in sync with the
# _DOC_SLUGS tuple in scripts/build_docs.py (minus protea-core, which
# is built from the deploy worktree itself).
SLUGS=(protea-contracts protea-sources protea-runners protea-backends)

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG_FILE"; }

mkdir -p "$WORKTREES_DIR"

advanced=0
failed=0

for slug in "${SLUGS[@]}"; do
  src="$REPOS_DIR/$slug"
  wt="$WORKTREES_DIR/$slug"

  if [[ ! -d "$src/.git" ]]; then
    log "skip $slug: $src not a clone"
    continue
  fi

  if [[ ! -d "$wt" ]]; then
    if ! git -C "$src" worktree add --detach "$wt" origin/develop >>"$LOG_FILE" 2>&1; then
      log "ERR $slug: worktree add failed"
      failed=1
      continue
    fi
    log "$slug: created worktree at $wt"
  fi

  if ! git -C "$src" fetch --quiet origin develop 2>>"$LOG_FILE"; then
    log "ERR $slug: fetch failed"
    failed=1
    continue
  fi

  before=$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")
  target=$(git -C "$src" rev-parse origin/develop 2>/dev/null || echo "")

  if [[ "$before" == "$target" ]]; then
    continue
  fi

  if ! git -C "$wt" reset --hard "$target" >>"$LOG_FILE" 2>&1; then
    log "ERR $slug: reset --hard failed"
    failed=1
    continue
  fi

  log "$slug: ${before:0:7} to ${target:0:7}"
  advanced=1
done

if [[ "$failed" -eq 1 ]]; then
  exit 20
fi
if [[ "$advanced" -eq 1 ]]; then
  exit 10
fi
exit 0
