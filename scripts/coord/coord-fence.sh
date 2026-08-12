#!/usr/bin/env bash
# coord-fence.sh -- the fence a spawned agent crosses before an irreversible act.
#
# FARM-COORD V0, item 4. Run this immediately before the first push, the first
# POST /jobs and any pull request. It re-reads claims/<message-id>.json from the
# REMOTE (not from any working tree) and proceeds only if the claim is still
# held by this machine at the epoch the agent was handed. A mismatch means the
# claim was superseded, the agent lost the race, and it must stop.
#
# Usage:
#   coord-fence.sh <message-id> <expected-epoch>
#
# Exit codes (0 proceeds, everything else stops):
#   0  claim is ours at the expected epoch
#   1  superseded: absent, owned by another machine, or a different epoch
#   2  usage error
#   3  the remote could not be read, so ownership is unknown
#
# It fails CLOSED on purpose. Ownership that cannot be verified is not
# ownership, and this runs in front of acts that cannot be undone.
#
# Overridable for testing:
#   COORD_REPO      path to the farm-coord clone
#   COORD_BRANCH    ledger branch name
#   COORD_REMOTE    remote name, default 'origin'
#   COORD_MACHINE   this machine's coordination name
#
# COORD_REPO here is the SHARED clone (~/Thesis2/farm-coord), the one the agent
# works in, and not the keeper's private clone. That is safe in the direction
# that matters: this script only fetches into a per-process ref and reads an
# object out of it, so it never writes the worktree, the index or HEAD.
set -uo pipefail

MSG_ID="${1:-}"
EXPECT_EPOCH="${2:-}"
if [[ -z "$MSG_ID" || -z "$EXPECT_EPOCH" ]]; then
  echo "usage: coord-fence.sh <message-id> <expected-epoch>" >&2
  exit 2
fi

COORD_REPO="${COORD_REPO:-${FARM_COORD_ROOT:-$HOME/Thesis2/farm-coord}}"
COORD_BRANCH="${COORD_BRANCH:-ledger}"
COORD_REMOTE="${COORD_REMOTE:-origin}"
# One name for this machine, from the same file the tick and the sender read.
# No hostname fallback, and here the reason is sharper than elsewhere: this
# script compares the name against the claim's owner, so a fallback that
# resolved to the hostname would answer 'held by somebody else' for a claim this
# machine holds perfectly well, and stop every agent while the ledger was
# healthy. A name it cannot establish is reported as unknown, below.
COORD_MACHINE_FILE="${COORD_MACHINE_FILE:-${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}/state/coord-machine}"
COORD_MACHINE="${COORD_MACHINE:-$(cat "$COORD_MACHINE_FILE" 2>/dev/null || true)}"
COORD_MACHINE="${COORD_MACHINE//[[:space:]]/}"

# Two prerequisites, each reported as 'ownership unknown' (3) and never as
# 'superseded' (1). Both stop the agent, but only one of them is a statement
# about the claim, and a missing tool that reported the claim gone would send
# every agent home while the ledger was perfectly healthy.
if [[ ! -d "$COORD_REPO/.git" ]]; then
  echo "coord-fence: no coordination clone at $COORD_REPO; ownership unknown, stopping" >&2
  exit 3
fi
if [[ -z "$COORD_MACHINE" ]]; then
  echo "coord-fence: this machine has no coordination name in $COORD_MACHINE_FILE; ownership unknown, stopping" >&2
  exit 3
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "coord-fence: jq is not installed, so the claim cannot be read; ownership unknown, stopping" >&2
  exit 3
fi

# Fetch into a private per-process ref rather than relying on FETCH_HEAD: two
# agents fencing at the same instant share one FETCH_HEAD file in one clone,
# and a half-written sha there would be read as a fence result.
FENCE_REF="refs/coord/fence-$$"
trap 'git -C "$COORD_REPO" update-ref -d "$FENCE_REF" 2>/dev/null || true' EXIT

if ! GIT_TERMINAL_PROMPT=0 timeout 30 git -C "$COORD_REPO" fetch --quiet --force \
     "$COORD_REMOTE" "refs/heads/$COORD_BRANCH:$FENCE_REF" 2>/dev/null; then
  echo "coord-fence: cannot read $COORD_BRANCH from the remote; ownership unknown, stopping" >&2
  exit 3
fi

CLAIM=$(git -C "$COORD_REPO" show "$FENCE_REF:claims/$MSG_ID.json" 2>/dev/null)
if [[ -z "$CLAIM" ]]; then
  echo "coord-fence: no claim for $MSG_ID on $COORD_BRANCH; superseded or released, stopping" >&2
  exit 1
fi

# jq absent or the json malformed leaves both empty, which fails the two
# comparisons below and stops. That is the direction we want to fail in.
OWNER=$(printf '%s' "$CLAIM" | jq -r '.claimed_by // ""' 2>/dev/null)
EPOCH=$(printf '%s' "$CLAIM" | jq -r '.epoch // ""' 2>/dev/null)

if [[ "$OWNER" != "$COORD_MACHINE" ]]; then
  echo "coord-fence: $MSG_ID is held by '${OWNER:-<unreadable>}', not '$COORD_MACHINE'; stopping" >&2
  exit 1
fi
if [[ "$EPOCH" != "$EXPECT_EPOCH" ]]; then
  echo "coord-fence: $MSG_ID epoch is '${EPOCH:-<unreadable>}', expected '$EXPECT_EPOCH'; superseded, stopping" >&2
  exit 1
fi

echo "coord-fence: $MSG_ID still ours (machine=$COORD_MACHINE epoch=$EPOCH); proceeding"
exit 0
