#!/usr/bin/env bash
# coord-tick.sh -- one pass of the FARM-COORD coordination loop.
#
# FARM-COORD V0, item 3. The supervisor (scripts/services/coord-keeper-supervisor.sh)
# owns the loop; this script owns exactly one pass and then exits.
#
# One pass:
#   1. probe the ledger tip with `git ls-remote`, and fetch only on a sha delta
#      (the delta gates the fetch, never the read: see the note on the scan)
#   2. read the inbox for messages addressed to this machine or to 'any', not
#      expired, not claimed, and whose `requires` this machine's capabilities
#      satisfy
#   3. take the highest priority one, write claims/<id>.json, commit, push
#   4. the push IS the compare-and-swap. Accepted means the claim is exclusive,
#      because GitHub serialises ref updates and rejects a non-fast-forward, so
#      the arbiter is neither machine. Rejected means somebody moved the branch:
#      fetch, reset, re-read the claim and branch three ways
#   5. only once the claim is on the remote, print the K=V block the conductor
#      consumes, and publish the pulse
#
# The fail contract (docs/runbook-persistent-service.md): exit 0 on success,
# and before any non-zero exit write FAIL_KIND and FAIL_EXIT to the file the
# supervisor reads. A remote that cannot be reached is FAIL_KIND=prereq_fail so
# that being offline never escalates: a WAN outage is failure mode 1 of the
# design, not something a janitor can fix. A message that carries a home path,
# a database or broker URL, an address or a credential is FAIL_KIND=contract_fail,
# and it is refused before anything about it is pushed.
#
# Output (stdout, only after a claim is exclusive; everything else is a
# heartbeat or stderr):
#   task_id=<id>
#   worktree=            (empty: this tick creates none, the agent does)
#   composed_prompt=<abs path to .md>
#   model=<opus>
#   message_id=<ULID>
#   claim_epoch=<n>
#
# What V0 deliberately leaves to a later item: it does not spawn the agent (the
# conductor decides), does not write the ledger outcome entry (the finishing
# agent does), and does not release an orphaned claim (it reports one).
#
# A CLAIM IS A ONE-WAY DOOR IN V0. write_claim is the only writer of
# claims/<id>.json in this repository and it only ever writes state "claimed".
# Nothing here, in coord-fence.sh or in coord-send.sh writes "released", and
# there is no lease, no expiry sweep and no supersede-by-epoch, so both readers
# of that value (the yield at the bottom of the scan, and the lost-race branch
# of claim_message) can only ever yield. Consequences, stated so nobody has to
# rediscover them:
#   - once a message is claimed, the OTHER machine will never take it, for as
#     long as the message sits inside its expires_at;
#   - this machine re-hands it off after a reboot (see the boot-scoped emitted
#     marker below), because a reboot is the failure this desktop is documented
#     to hit and losing the work to it is not acceptable;
#   - an agent that dies WITHOUT a reboot is not recovered by V0. The claim
#     stays open, the task row stays whatever the agent left it, and the pulse
#     reports it. The stale-claim warning below is the only alarm.
# The lease that closes the remaining two cases is a later item, and it needs a
# writer for "released" plus a boot reconciliation in the supervisor.
#
# THE KEEPER OWNS ITS OWN CLONE. COORD_REPO defaults to a clone that only this
# tick opens (~/Thesis2/farm-coord-keeper), NOT the shared ~/Thesis2/farm-coord
# that a human's coord-send.sh and a finishing agent write. sync_hard resets and
# cleans, and reset and clean are branch and tree scoped, not path scoped, so
# the "one writer per path" property that makes the ledger merge cleanly does
# not make a reset safe. Two clones cost one extra `git clone`; sharing one
# costs a silently discarded outcome entry the first time a tick and a finishing
# agent overlap. sync_hard additionally refuses to discard anything it cannot
# prove it wrote, so pointing COORD_REPO at a shared clone degrades into skipped
# ticks rather than into deletion.
#
# Env knobs, all shared with coord-send.sh, coord-fence.sh and the supervisor:
#   TASK_ID                     the supervisor's task row; required
#   AGENT_FARM_ROOT             default ~/Thesis2/agent-farm
#   COORD_REPO                  the KEEPER's clone, default
#                               ~/Thesis2/farm-coord-keeper (never the shared one)
#   COORD_BRANCH                ledger branch name, default 'ledger'
#   COORD_PULSE_BRANCH          pulse branch name, default 'pulse'
#   COORD_MACHINE               this machine's coordination name
#   COORD_CAPABILITIES_FILE     one capability per line, default state/coord-capabilities
#   COORD_PUSH_ATTEMPTS         bounded compare-and-swap retries, default 5
#   COORD_KEEPER_FAIL_ENV       the fail-contract K=V file
# Test seams: COORD_GIT_CMD, COORD_SLEEP_CMD, COORD_STATE_DIR, COORD_REMOTE,
# COORD_BOOT_ID (a test simulates a reboot by changing it).

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"
TASK_ID="${TASK_ID:?TASK_ID env required}"

# The keeper's own clone. FARM_COORD_ROOT is deliberately NOT consulted: that
# variable names the clone a human sends from, and inheriting it would put the
# reset path back inside a worktree this tick does not own.
COORD_REPO="${COORD_REPO:-$HOME/Thesis2/farm-coord-keeper}"
COORD_BRANCH="${COORD_BRANCH:-ledger}"
COORD_PULSE_BRANCH="${COORD_PULSE_BRANCH:-pulse}"
COORD_REMOTE="${COORD_REMOTE:-origin}"
# One name for this machine, shared with the fence and the supervisor. The
# state file wins so a rename is one edit; the hostname is only the fallback.
COORD_MACHINE="${COORD_MACHINE:-$(cat "$ROOT/state/coord-machine" 2>/dev/null || hostname -s)}"
COORD_CAPABILITIES_FILE="${COORD_CAPABILITIES_FILE:-$ROOT/state/coord-capabilities}"
COORD_STATE_DIR="${COORD_STATE_DIR:-$ROOT/state/coord-keeper}"
COORD_NET_TIMEOUT_SEC="${COORD_LSREMOTE_TIMEOUT_SEC:-30}"
COORD_LOCK_WAIT_SEC="${COORD_LOCK_WAIT_SEC:-30}"
COORD_PUSH_ATTEMPTS="${COORD_PUSH_ATTEMPTS:-5}"
COORD_PULSE_INTERVAL_SEC="${COORD_PULSE_INTERVAL_SEC:-300}"
COORD_MODEL="${COORD_MODEL:-opus}"
COORD_AGENT="${COORD_AGENT:-coord-keeper}"
COORD_STALE_CLAIM_SEC="${COORD_STALE_CLAIM_SEC:-21600}"

# The emitted marker says "this machine has already handed this message off, do
# not hand it off again". It is scoped to the BOOT, not to the disk, because
# that is exactly the span over which the statement is true: the agent it names
# is a process, and this desktop is documented to reboot without warning. A
# marker that outlived the boot turned a reboot into permanent loss, since the
# other machine yields to the claim forever and this one skips on the marker.
COORD_BOOT_ID="${COORD_BOOT_ID:-$(tr -cd 'a-f0-9' < /proc/sys/kernel/random/boot_id 2>/dev/null || true)}"
[[ -n "$COORD_BOOT_ID" ]] || COORD_BOOT_ID="noboot"
COORD_EMITTED_DIR="$COORD_STATE_DIR/emitted/$COORD_BOOT_ID"
mkdir -p "$COORD_EMITTED_DIR" "$COORD_STATE_DIR/quarantine" "$COORD_STATE_DIR/stale" 2>/dev/null || true
# Bounded: one directory per boot, each a few bytes per message. Swept only
# when a whole boot's markers are a month old, and NEVER the current boot's:
# a machine up for longer than the window would otherwise have its own live
# markers deleted under it and hand every open claim off a second time.
find "$COORD_STATE_DIR/emitted" -mindepth 1 -maxdepth 1 -type d -mtime +30 \
  ! -name "$COORD_BOOT_ID" -exec rm -rf {} + 2>/dev/null || true

# Under the state directory rather than /tmp: the supervisor SOURCES this file,
# and a world-writable path that another local user can write is a shell
# injection into a service. Truncated at the top of every pass so that a tick
# which dies without reaching fail() reports 'unknown' (which escalates) rather
# than inheriting some earlier pass's prereq_fail (which never does).
FAIL_ENV="${COORD_KEEPER_FAIL_ENV:-$COORD_STATE_DIR/last-fail.env}"
: > "$FAIL_ENV" 2>/dev/null || true

# fail <kind> <exit> <message>: honour the fail contract, then stop. Every
# non-zero exit in this file goes through here, so FAIL_KIND is never stale.
fail() {
  heartbeat "$TASK_ID" error "$3"
  { printf 'FAIL_KIND=%s\n' "$1"; printf 'FAIL_EXIT=%s\n' "$2"; } > "$FAIL_ENV"
  exit 1
}

# Configuration gates, checked before a single byte is written and each one
# gated on rather than narrated. The branch guard is the hard rule about
# trunks: this script pushes HEAD to refs/heads/$COORD_BRANCH, so the branch
# name is the only thing standing between it and a direct push to a trunk.
case "$COORD_BRANCH/$COORD_PULSE_BRANCH" in
  main/*|master/*|develop/*|*/main|*/master|*/develop)
    fail config_fail 78 "refusing to run: coordination branch resolves to a trunk ($COORD_BRANCH, $COORD_PULSE_BRANCH)" ;;
esac
# The coordination clone is never a code repository. This keeps the reset path
# below away from the developer workspace, which no agent may touch.
case "$COORD_REPO" in
  */repositories/*|*/agent-farm|*/agent-farm/*|*/worktrees/*)
    fail config_fail 78 "refusing to run: COORD_REPO=$COORD_REPO is inside a code checkout" ;;
esac
[[ -d "$COORD_REPO/.git" ]] || fail config_fail 78 "no farm-coord clone at $COORD_REPO"
[[ "$COORD_MACHINE" =~ ^[a-z][a-z0-9-]{0,31}$ ]] || fail config_fail 78 "machine name '$COORD_MACHINE' is not plain; set COORD_MACHINE"

# Capabilities. A file so the answer is the same for the tick and for a human
# reading it; 'gpu' on the desktop is only the fallback when the file is absent.
if [[ -z "${COORD_CAPABILITIES:-}" ]]; then
  if [[ -r "$COORD_CAPABILITIES_FILE" ]]; then
    COORD_CAPABILITIES=$(grep -vE '^[[:space:]]*(#|$)' "$COORD_CAPABILITIES_FILE" | tr ',\n' '  ' | tr -s ' ')
  elif [[ "$COORD_MACHINE" == "desktop" ]]; then
    COORD_CAPABILITIES="gpu"
  else
    COORD_CAPABILITIES=""
  fi
fi
COORD_CAPABILITIES="${COORD_CAPABILITIES#"${COORD_CAPABILITIES%%[![:space:]]*}"}"
COORD_CAPABILITIES="${COORD_CAPABILITIES%"${COORD_CAPABILITIES##*[![:space:]]}"}"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/coord-tick.XXXXXX") || fail prereq_fail 1 "cannot create a temporary directory"
trap 'rm -rf "$TMP"' EXIT

# Two git wrappers, because `timeout` runs a command and cannot run a shell
# function: every call that crosses the network goes through coord_git_net and
# is bounded, every local one through coord_git and is not. The unquoted
# expansion is deliberate, so COORD_GIT_CMD may be multi-token in a test.
# shellcheck disable=SC2086
coord_git() { GIT_TERMINAL_PROMPT=0 ${COORD_GIT_CMD:-git} -C "$COORD_REPO" "$@"; }
# shellcheck disable=SC2086
coord_git_net() {
  GIT_TERMINAL_PROMPT=0 timeout "$COORD_NET_TIMEOUT_SEC" \
    ${COORD_GIT_CMD:-git} -C "$COORD_REPO" "$@"
}
# shellcheck disable=SC2086
coord_sleep() { ${COORD_SLEEP_CMD:-sleep} "$1"; }

# json_get <file> <key>: one scalar, empty when absent or unparseable. Empty is
# the safe answer everywhere it is used: every comparison against it fails.
json_get() {
  python3 - "$1" "$2" <<'PY' 2>/dev/null
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        doc = json.load(fh)
except Exception:
    sys.exit(0)
val = doc.get(sys.argv[2]) if isinstance(doc, dict) else None
if val is not None and not isinstance(val, (dict, list)):
    print(val)
PY
}

# claim_is_stale <claim-file>: true when claimed_at is further in the past than
# COORD_STALE_CLAIM_SEC. An unreadable or absent stamp is NOT stale: this drives
# an alarm, and an alarm that fires on a parse failure is an alarm nobody reads.
claim_is_stale() {
  python3 - "$1" "$COORD_STALE_CLAIM_SEC" <<'PY'
import datetime, json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        stamp = json.load(fh)["claimed_at"]
    when = datetime.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
except Exception:
    sys.exit(1)
age = (datetime.datetime.now(datetime.timezone.utc) - when).total_seconds()
sys.exit(0 if age > float(sys.argv[2]) else 1)
PY
}

# remote_tip: the ledger sha at the remote, one round trip and no object
# transfer (measured on this desktop at 0.61 to 0.82 seconds). Empty means the
# remote could not be read, which is the network signal everywhere below.
remote_tip() {
  coord_git_net ls-remote "$COORD_REMOTE" "refs/heads/$COORD_BRANCH" 2>/dev/null \
    | awk 'NR==1{print $1}'
}

# reconcile_claims: put claims/ back exactly as HEAD has it. PATH SCOPED, so it
# cannot touch ledger/ or inbox/, and unconditional, because the state it
# repairs is reachable without the ledger ever moving.
#
# write_claim puts claims/<id>.json on disk while HEAD is still the remote tip;
# HEAD only diverges at the commit three statements later. A machine killed in
# that window, or a `commit` refused (no user.email, a signing prompt under
# systemd) which returns without undoing the write, leaves a claim file that the
# remote does not contain. Every later read below would take that orphan for a
# claim: the scan would skip the compare-and-swap entirely and hand off a
# message this machine does not hold (the fence then stops the agent after the
# tokens are spent), or two machines would both hand off the same message.
# So: never trust a file in this worktree that HEAD does not vouch for.
reconcile_claims() {
  coord_git reset --quiet -- claims >/dev/null 2>&1 || true
  coord_git checkout --quiet --force -- claims >/dev/null 2>&1 || true
  coord_git clean -qfd -- claims >/dev/null 2>&1 || true
}

# sync_hard: bring the worktree onto the remote tip WITHOUT discarding anything
# this tick cannot prove it wrote. NEVER `git stash` (prior incident).
#
# `reset --hard` and `clean` are branch and tree scoped, not path scoped, so the
# "one writer per path" property of the ledger does not make them safe: it makes
# them LOOK safe. The writers that share the ledger with this tick are a human
# running coord-send.sh (which stages through a temporary index and is therefore
# already safe) and the finishing agent, which writes ledger/<date>/<id>.json
# and removes the inbox file in a checkout of its own. If COORD_REPO ever points
# at a clone that agent uses, a reset here deletes a committed and unpushed
# outcome entry with no error, and clean deletes an uncommitted one.
#
# The two structural guards, neither of which needs any state to survive a pass:
#   - an uncommitted edit under ledger/ or inbox/ is somebody else composing;
#   - a local commit the remote does not have is safe to drop only if it touches
#     nothing outside claims/. That is exactly the shape of this tick's own
#     rejected or unpushed claim commit, and it is not the shape of an outcome.
# Refusing returns 1, which the two callers already route to a skipped tick.
sync_hard() {
  local target stray dirty
  coord_git_net fetch --quiet "$COORD_REMOTE" "$COORD_BRANCH" || return 1
  target=$(coord_git rev-parse FETCH_HEAD 2>/dev/null)
  [[ -n "$target" ]] || return 1

  dirty=$(coord_git status --porcelain -- ledger inbox 2>/dev/null | head -3)
  if [[ -n "$dirty" ]]; then
    heartbeat "$TASK_ID" warn "refusing to resync $COORD_REPO: uncommitted work under ledger/ or inbox/ (another writer holds this clone)"
    return 1
  fi
  stray=$(coord_git log --format= --name-only "$target..HEAD" 2>/dev/null \
          | grep -vE '^(claims/|$)' | head -3)
  if [[ -n "$stray" ]]; then
    heartbeat "$TASK_ID" warn "refusing to resync $COORD_REPO: a local commit touches $(printf '%s' "$stray" | tr '\n' ' ') and is not on the remote"
    return 1
  fi

  # The clean comes BEFORE the checkout: an untracked claims/<id>.json left by a
  # kill between write_claim and commit makes `checkout -B` abort on a file it
  # would overwrite, and an aborted checkout here made every later pass fail.
  reconcile_claims
  coord_git checkout --quiet -B "$COORD_BRANCH" "$target" || return 1
  coord_git reset --quiet --hard "$target" || return 1
  return 0
}

PUSH_CLASS=""
PUSH_MSG=""
# push_ledger <base-sha>: the compare-and-swap. Never forced, never to a trunk.
#
# The failure is classified structurally and NOT by reading git's wording. The
# wording differs by transport (a local path says "incorrect old value
# provided" exactly where GitHub says "fetch first"), and an unrecognised
# rejection would make the tick give up instead of re-applying, which is the
# whole mechanism. So, on a failed push: the remote cannot be read means the
# network, the remote has moved off the base we built on means we lost the
# race, and the remote still sitting on our base means the push itself failed
# and an identical retry would fail identically.
push_ledger() {
  local base="$1" out rc tip
  out=$(coord_git_net push --quiet "$COORD_REMOTE" "HEAD:refs/heads/$COORD_BRANCH" 2>&1)
  rc=$?
  PUSH_MSG=$(printf '%s' "$out" | tr '\n' ' ' | cut -c1-200)
  if (( rc == 0 )); then PUSH_CLASS=ok; return 0; fi
  tip=$(remote_tip)
  if [[ -z "$tip" ]]; then
    PUSH_CLASS=network
  elif [[ "$tip" != "$base" ]]; then
    PUSH_CLASS=rejected
  else
    PUSH_CLASS=error
  fi
  return 1
}

# jitter_seconds <attempt>: bounded, growing, randomised. Two machines is a
# retry that is invisible; the bound is what keeps ten from being a storm.
jitter_seconds() {
  local ms=$(( 250 * $1 + RANDOM % 750 ))
  (( ms > 4000 )) && ms=4000
  printf '%d.%03d' $((ms / 1000)) $((ms % 1000))
}

# lint_message <file>: the content contract, enforced on the receive side as
# well as the send side, because nothing else enforces it and the ledger is
# permanent. Prints the names of the rules that matched, never the match
# itself: a heartbeat that quotes the secret it found has published it again.
lint_message() {
  local f="$1" rule bad=""
  local rules=(
    'absolute home path|(/home|/Users|/root)/[A-Za-z0-9._-]+'
    'database URL|(postgres(ql)?|mysql|mongodb|sqlite)(\+[a-z0-9]+)?://'
    'broker URL|(amqps?|redis|kafka|mqtt)://'
    'bare network address|(^|[^0-9A-Za-z.])[0-9]{1,3}(\.[0-9]{1,3}){3}([^0-9A-Za-z.]|$)'
    'credential inside a URL|://[^"[:space:]/@]+:[^"[:space:]/@]+@'
    'access token|(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abprs]-[A-Za-z0-9-]{10,})'
    'private key|BEGIN [A-Z ]*PRIVATE KEY'
    'secret assignment|(password|api[_-]?key|secret[_-]?key|token)["'"'"']*[:=]'
    'platform environment|PROTEA_(DB|AMQP|S3|MINIO)_[A-Z_]*URL|POSTGRES_PASSWORD'
  )
  for rule in "${rules[@]}"; do
    if grep -qaEi -- "${rule#*|}" "$f" 2>/dev/null; then bad+="${bad:+, }${rule%%|*}"; fi
  done
  printf '%s' "$bad"
}

# next_epoch <id>: one past whatever the remote currently records, so a
# superseding claim always sorts after the one it replaces and coord-fence.sh
# can stop an agent whose epoch is stale.
next_epoch() {
  local prev
  prev=$(json_get "$COORD_REPO/claims/$1.json" epoch)
  [[ "$prev" =~ ^[0-9]+$ ]] || { printf '1'; return 0; }
  printf '%d' $((prev + 1))
}

write_claim() {
  python3 - "$COORD_REPO/claims/$1.json" "$1" "$COORD_MACHINE" "$2" "$3" "$TASK_ID" <<'PY'
import datetime, json, os, sys
path, mid, machine, epoch, rel, tick = sys.argv[1:7]
os.makedirs(os.path.dirname(path), exist_ok=True)
doc = {
    "schema": "farm.coord/1",
    "message_id": mid,
    "claimed_by": machine,
    "epoch": int(epoch),
    "state": "claimed",
    "claimed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "inbox_path": rel,
    "tick_task_id": tick,
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, ensure_ascii=False, sort_keys=False)
    fh.write("\n")
PY
}

CLAIM_EPOCH=""
CLAIM_NOTE=""
# claim_message <id> <inbox-rel-path>
#   0 the claim is ours on the remote      2 the remote is unreachable
#   1 yield, it is somebody else's         3 contention or a local git fault
claim_message() {
  local mid="$1" rel="$2" attempt=0 epoch owner state base
  while (( attempt < COORD_PUSH_ATTEMPTS )); do
    attempt=$((attempt + 1))
    # The tip we are about to build on. push_ledger compares the remote against
    # it to tell a lost race from a broken push.
    base=$(coord_git rev-parse HEAD 2>/dev/null)
    epoch=$(next_epoch "$mid")
    write_claim "$mid" "$epoch" "$rel" || { CLAIM_NOTE="could not write the claim"; return 3; }
    coord_git add -- "claims/$mid.json" || { CLAIM_NOTE="git add refused"; return 3; }
    coord_git commit --quiet -m "coord: claim $mid by $COORD_MACHINE epoch $epoch" \
      || { CLAIM_NOTE="commit refused (is user.name, user.email or signing configured?)"; return 3; }

    if push_ledger "$base"; then CLAIM_EPOCH="$epoch"; return 0; fi
    case "$PUSH_CLASS" in
      network) CLAIM_NOTE="remote unreachable during push"; return 2 ;;
      rejected) : ;;
      *) CLAIM_NOTE="push failed: $PUSH_MSG"; return 3 ;;
    esac

    # Rejected: somebody moved the branch. Reset onto the new tip, which
    # discards our commit, then read what the remote now says about this id.
    sync_hard || { CLAIM_NOTE="could not resync (remote unreachable, or another writer holds $COORD_REPO)"; return 2; }
    if [[ -f "$COORD_REPO/claims/$mid.json" ]]; then
      owner=$(json_get "$COORD_REPO/claims/$mid.json" claimed_by)
      state=$(json_get "$COORD_REPO/claims/$mid.json" state)
      if [[ "$owner" == "$COORD_MACHINE" && "$state" == "claimed" ]]; then
        CLAIM_EPOCH=$(json_get "$COORD_REPO/claims/$mid.json" epoch)
        CLAIM_NOTE="already ours at the tip"
        return 0
      fi
      # "released" has no writer in V0 (see the header), so in practice this
      # yields for every claim somebody else holds, permanently. It is written
      # against the value rather than against "a claim file exists" so that the
      # lease item only has to add the writer, not re-open this branch.
      if [[ "$state" != "released" ]]; then
        CLAIM_NOTE="held by ${owner:-another machine}"
        return 1
      fi
    fi
    # Absent, or released: re-apply on the new tip after bounded jitter.
    coord_sleep "$(jitter_seconds "$attempt")"
  done
  CLAIM_NOTE="lost the compare-and-swap $COORD_PUSH_ATTEMPTS times"
  return 3
}

# list_candidates: address, expiry and capability filtering live in python
# because it already has the message parsed; the claim check and the content
# lint stay in shell. Prints priority, created_at, id, path, tab separated,
# highest priority first and oldest first within a priority.
list_candidates() {
  python3 - "$COORD_REPO" "$COORD_MACHINE" "$COORD_CAPABILITIES" <<'PY'
import datetime, json, os, re, sys
repo, machine, caps_raw = sys.argv[1:4]
caps = {c for c in caps_raw.replace(",", " ").split() if c}
now = datetime.datetime.now(datetime.timezone.utc)
# A message id becomes a path (claims/<id>.json), so it may not contain a
# separator, and it may not start with a dot.
ID_RX = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{3,63}\Z")

def parsed(value):
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

rows = []
for box in dict.fromkeys((machine, "any")):
    folder = os.path.join(repo, "inbox", box)
    if not os.path.isdir(folder):
        continue
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(folder, name)
        try:
            with open(path, encoding="utf-8") as fh:
                msg = json.load(fh)
            assert isinstance(msg, dict)
        except Exception as exc:
            print(f"unreadable inbox/{box}/{name}: {exc}", file=sys.stderr)
            continue
        mid = str(msg.get("id") or "")
        if not ID_RX.match(mid):
            print(f"unusable message id in inbox/{box}/{name}", file=sys.stderr)
            continue
        if not str(msg.get("schema") or "").startswith("farm.coord/"):
            print(f"unknown schema in {mid}", file=sys.stderr)
            continue
        if str(msg.get("to") or "") not in (machine, "any"):
            continue
        expires = parsed(msg.get("expires_at"))
        if expires is not None and expires <= now:
            print(f"expired {mid}", file=sys.stderr)
            continue
        requires = msg.get("requires") or []
        requires = {str(r) for r in (requires if isinstance(requires, list) else [requires])}
        if not requires <= caps:
            print(f"not for us {mid}: requires {sorted(requires - caps)}", file=sys.stderr)
            continue
        try:
            priority = int(msg.get("priority", 0))
        except (TypeError, ValueError):
            priority = 0
        rows.append((-priority, str(msg.get("created_at") or ""), mid,
                     os.path.relpath(path, repo)))
rows.sort()
for priority, created, mid, rel in rows:
    print("\t".join((str(-priority), created, mid, rel)))
PY
}

# emit_handoff <id> <epoch> <rel>: mint the task row, compose the prompt, and
# print the K=V block. Called only once the claim is exclusive on the remote.
# The emitted marker is written BEFORE the block, so a crash here loses a
# handoff rather than duplicating one (nobody can undo a duplicate). What makes
# "a human can re-run" true rather than a hope: the same block is written to
# results/<task>/handoff.env, which survives the tick, the supervisor and the
# journal's retention, and the marker is scoped to this boot so a reboot hands
# the message off again by itself.
emit_handoff() {
  local mid="$1" epoch="$2" rel="$3" new_task results composed args
  new_task=$(make_task_id coord)
  results="$ROOT/results/$new_task"
  composed="$results/composed_prompt.md"
  mkdir -p "$results"
  args=$(python3 - "$mid" "$epoch" "$rel" "$COORD_MACHINE" <<'PY'
import json, sys
print(json.dumps({"source": "farm-coord", "message_id": sys.argv[1],
                  "claim_epoch": int(sys.argv[2]), "inbox_path": sys.argv[3],
                  "machine": sys.argv[4]}))
PY
)
  python3 - "$COORD_REPO/$rel" "$composed" "$mid" "$epoch" "$new_task" "$ROOT" "$COORD_MACHINE" <<'PY'
import json, sys
src, out, mid, epoch, task, root, machine = sys.argv[1:8]
with open(src, encoding="utf-8") as fh:
    msg = json.load(fh)
ref = msg.get("ref") or {}
lines = [
    f"# {msg.get('subject') or 'coordination message'}",
    "",
    f"A coordination message arrived from `{msg.get('from', 'unknown')}` and this",
    f"machine (`{machine}`) holds the exclusive claim on it at epoch {epoch}.",
    "",
    "## The message",
    "",
    f"- id: `{mid}`",
    f"- kind: `{msg.get('kind', 'task')}`",
    f"- created: `{msg.get('created_at', '')}`  expires: `{msg.get('expires_at', '')}`",
    f"- priority: `{msg.get('priority', 0)}`  requires: `{', '.join(msg.get('requires') or []) or 'nothing'}`",
    "",
    (msg.get("body") or "(no body)").rstrip(),
    "",
    "## Reference",
    "",
]
lines += [f"- {k}: `{v}`" for k, v in ref.items() if v] or ["- none given"]
lines += [
    "",
    "## The fence",
    "",
    "Before the first push, the first job dispatch and any pull request, run:",
    "",
    "```bash",
    f"bash {root}/scripts/coord/coord-fence.sh {mid} {epoch}",
    "```",
    "",
    "A non-zero exit means the claim was superseded and this work must stop.",
    "Results belong in the platform; the ledger entry names the job id, it does",
    "not carry the numbers.",
    "",
    "## Bookkeeping",
    "",
    f"- TASK_ID: `{task}`",
    f"- AGENT_FARM_ROOT: `{root}`",
    f"- heartbeats: `python3 $AGENT_FARM_ROOT/scripts/lib/db.py heartbeat \"{task}\" info \"...\"`",
    "",
]
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
PY
  # db.py directly, not the task_insert wrapper in lib/common.sh: that wrapper
  # writes its default as "${6:-{}}", which bash expands to the caller's value
  # followed by a literal closing brace, so every spawn_args JSON it stores is
  # malformed. Verified by probe on 2026-08-12; spawn-subagent.sh has the same
  # corruption in its rows and the wrapper is the thing that needs the fix.
  python3 "$DB_PY" insert-task "$new_task" "$COORD_AGENT" subagent 0 "$COORD_MODEL" "$args" \
    || heartbeat "$TASK_ID" warn "task row insert failed for $new_task; handing off anyway"
  # The pid column stays empty on purpose: the process this row will describe
  # is the agent the conductor has not spawned yet, and stamping this tick's own
  # pid there would make a liveness check answer about the wrong process.
  task_set_started "$new_task" "" "" "" || true
  printf '%s' "$new_task" > "$COORD_EMITTED_DIR/$mid"
  heartbeat "$TASK_ID" info "claimed $mid at epoch $epoch, handed off as $new_task"

  EMIT_BLOCK=$(printf 'task_id=%s\nworktree=\ncomposed_prompt=%s\nmodel=%s\nmessage_id=%s\nclaim_epoch=%s\n' \
    "$new_task" "$composed" "$COORD_MODEL" "$mid" "$epoch")
  printf '%s\n' "$EMIT_BLOCK" > "$results/handoff.env"
}

# publish_pulse: pulse/<machine>.json on the pulse branch, written through a
# temporary index so the ledger worktree is never checked out onto another
# branch mid-tick. The active list is the claims this machine holds whose task
# row is still open, so it is a measurement and not an aspiration.
publish_pulse() {
  local ledger_sha="$1" claim owner state mid tid status digest prev_digest="" stamp=0 now
  : > "$TMP/active.tsv"
  shopt -s nullglob
  for claim in "$COORD_REPO"/claims/*.json; do
    owner=$(json_get "$claim" claimed_by)
    [[ "$owner" == "$COORD_MACHINE" ]] || continue
    state=$(json_get "$claim" state)
    [[ "$state" == "claimed" ]] || continue
    mid=$(basename "$claim" .json)
    tid=""
    [[ -f "$COORD_EMITTED_DIR/$mid" ]] && tid=$(<"$COORD_EMITTED_DIR/$mid")
    status="claimed"
    if [[ "$tid" =~ ^[A-Za-z0-9_.-]+$ ]]; then
      status=$(db_query "SELECT status FROM tasks WHERE id='$tid'" 2>/dev/null | head -1 | tr -d '[:space:]')
      [[ -n "$status" ]] || status="unknown"
    fi
    case "$status" in
      claimed|pending|running) printf '%s\t%s\t%s\n' "$mid" "$tid" "$status" >> "$TMP/active.tsv" ;;
      *) heartbeat "$TASK_ID" warn "claim $mid is open but task ${tid:-none} is $status; not pulsed as active (V0 does not release)" ;;
    esac
    # The dangerous asymmetry, alarmed. A closed row under an open claim (above)
    # is harmless and was already warned about; a row that stays 'running' under
    # an open claim is the shape of an agent that died, and V0 cannot release
    # the claim, so the pulse would keep asserting this machine is working on it
    # for as long as the message lives. Once per message, because the condition
    # persists and a warning every fifteen seconds is not an alarm.
    # Marker first, so the interpreter only starts for a claim not yet warned.
    if [[ ! -f "$COORD_STATE_DIR/stale/$mid" ]] && claim_is_stale "$claim"; then
      : > "$COORD_STATE_DIR/stale/$mid" 2>/dev/null || true
      heartbeat "$TASK_ID" error "claim $mid has been held by this machine for over $((COORD_STALE_CLAIM_SEC / 3600))h with task ${tid:-none} at '$status'; V0 has no release path, so it must be resolved by hand"
    fi
  done
  shopt -u nullglob

  # Throttle. At a fifteen second poll an unconditional pulse would be a few
  # thousand commits a day on a branch whose only reader wants liveness.
  digest=$( { printf '%s\n' "$COORD_CAPABILITIES"; cat "$TMP/active.tsv"; } | sha1sum | awk '{print $1}')
  [[ -f "$COORD_STATE_DIR/pulse.digest" ]] && prev_digest=$(<"$COORD_STATE_DIR/pulse.digest")
  [[ -f "$COORD_STATE_DIR/pulse.stamp" ]] && stamp=$(<"$COORD_STATE_DIR/pulse.stamp")
  now=$(date +%s)
  [[ "$stamp" =~ ^[0-9]+$ ]] || stamp=0
  if [[ "$digest" == "$prev_digest" ]] && (( now - stamp < COORD_PULSE_INTERVAL_SEC )); then
    return 0
  fi

  python3 - "$TMP/pulse.json" "$COORD_MACHINE" "$COORD_CAPABILITIES" "$ledger_sha" "$TASK_ID" "$TMP/active.tsv" <<'PY'
import datetime, json, sys
out, machine, caps, sha, task, active_file = sys.argv[1:7]
active = []
with open(active_file, encoding="utf-8") as fh:
    for line in fh:
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 3:
            active.append({"message_id": parts[0], "task_id": parts[1] or None,
                           "status": parts[2]})
doc = {
    "schema": "farm.coord/1",
    "machine": machine,
    "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "capabilities": caps.split(),
    "ledger_sha": sha,
    "keeper_task_id": task,
    "active": active,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, ensure_ascii=False, sort_keys=False)
    fh.write("\n")
PY

  local rel="pulse/$COORD_MACHINE.json" attempt base blob tree commit
  local -a parent
  for attempt in 1 2 3; do
    base=""
    if coord_git_net fetch --quiet "$COORD_REMOTE" "$COORD_PULSE_BRANCH" 2>/dev/null; then
      base=$(coord_git rev-parse FETCH_HEAD 2>/dev/null)
    fi
    # The index is exported rather than prefixed onto the call, because a
    # variable assignment in front of a shell function is not reliably scoped
    # to it. It is unset again before the tick touches the real worktree.
    rm -f "$TMP/index"
    export GIT_INDEX_FILE="$TMP/index"
    parent=()
    if [[ -n "$base" ]]; then
      coord_git read-tree "$base" || { unset GIT_INDEX_FILE; return 1; }
      parent=(-p "$base")
    fi
    blob=$(coord_git hash-object -w -- "$TMP/pulse.json") || { unset GIT_INDEX_FILE; return 1; }
    coord_git update-index --add --cacheinfo "100644,$blob,$rel" || { unset GIT_INDEX_FILE; return 1; }
    tree=$(coord_git write-tree) || { unset GIT_INDEX_FILE; return 1; }
    unset GIT_INDEX_FILE
    commit=$(coord_git commit-tree "$tree" ${parent[@]+"${parent[@]}"} -m "pulse: $COORD_MACHINE") || return 1
    if coord_git_net push --quiet "$COORD_REMOTE" \
         "$commit:refs/heads/$COORD_PULSE_BRANCH" 2>/dev/null; then
      printf '%s' "$digest" > "$COORD_STATE_DIR/pulse.digest"
      printf '%s' "$now" > "$COORD_STATE_DIR/pulse.stamp"
      return 0
    fi
    coord_sleep "$(jitter_seconds "$attempt")"
  done
  return 1
}

# ---------------------------------------------------------------- the tick --
# One lock for the whole pass, taken on the keeper's own clone. It serialises
# two ticks (a slow pass and the next one the supervisor starts), which is the
# only overlap that can now happen: coord-send.sh locks the file of the clone a
# human sends from, and with the keeper on a clone of its own those are two
# different files. Nothing is lost by that, because the arbiter between the two
# clones was never this lock, it is the remote refusing a non-fast-forward.
# `-w` bounds the wait: a wedged tick must not wedge the next one.
exec 9>"$COORD_REPO/.git/farm-coord.lock"
flock -w "$COORD_LOCK_WAIT_SEC" 9 || fail prereq_fail 2 "another coord process still holds the lock after ${COORD_LOCK_WAIT_SEC}s"

# Before ANY read of a claim file, and whether or not the ledger moved. The
# state this repairs (a claim on disk that the remote does not have) is reached
# without the ledger moving at all, so gating it on the delta would leave the
# tick reading its own unpushed guess as if it were the remote's answer.
reconcile_claims

REMOTE_SHA=$(remote_tip)
[[ -n "$REMOTE_SHA" ]] || fail prereq_fail 10 "cannot reach $COORD_REMOTE/$COORD_BRANCH; coordination is offline this tick"
LOCAL_SHA=$(coord_git rev-parse HEAD 2>/dev/null)

# The delta gates the FETCH and nothing else. It must not gate the scan: at
# boot, and after any tick that pushed, the local tip already equals the remote
# one, so a scan conditional on the delta would never read a message that
# arrived while this machine was down. Reading the inbox is local work.
LEDGER_MOVED=0
if [[ "$REMOTE_SHA" != "$LOCAL_SHA" ]]; then
  sync_hard || fail prereq_fail 11 "ledger moved to ${REMOTE_SHA:0:7} but the resync did not happen (the fetch failed, or another writer holds $COORD_REPO)"
  heartbeat "$TASK_ID" info "ledger ${LOCAL_SHA:0:7} -> ${REMOTE_SHA:0:7}"
  LEDGER_MOVED=1
fi

EMIT_BLOCK=""
VIOLATION=""
# Written to a file rather than read straight into mapfile, so a scan that
# fails is reported instead of looking exactly like an empty inbox.
if ! list_candidates >"$TMP/candidates" 2>"$TMP/skipped"; then
  heartbeat "$TASK_ID" warn "the inbox scan failed; treating this tick as having nothing to take"
fi
mapfile -t CANDIDATES < "$TMP/candidates"
# Only on a tick where something actually changed. At a fifteen second poll an
# unconditional summary is a few thousand heartbeat rows a day that say nothing.
if (( LEDGER_MOVED == 1 )); then
  heartbeat "$TASK_ID" info \
    "inbox: ${#CANDIDATES[@]} eligible, $(wc -l < "$TMP/skipped" | tr -d '[:space:]') skipped"
fi

# PRI and CREATED are read only to consume the sorted columns.
# shellcheck disable=SC2034
while IFS=$'\t' read -r PRI CREATED MID REL; do
  [[ -n "${MID:-}" ]] || continue
  # A resync inside an earlier iteration can have deleted the file under us
  # (the other machine finished and removed its inbox entry).
  [[ -f "$COORD_REPO/$REL" ]] || continue

  BAD=$(lint_message "$COORD_REPO/$REL")
  if [[ -n "$BAD" ]]; then
    heartbeat "$TASK_ID" error "message $MID refused, it carries: $BAD"
    if [[ ! -f "$COORD_STATE_DIR/quarantine/$MID" ]]; then
      printf '%s\n' "$BAD" > "$COORD_STATE_DIR/quarantine/$MID"
      VIOLATION="$MID"
    fi
    continue
  fi

  # Already ours from an earlier tick: hand off again only if the earlier tick
  # died before printing the block, or this machine has rebooted since (the
  # marker is boot scoped, so the agent that marker named is provably gone).
  # reconcile_claims above is what makes this file trustworthy: it is now
  # exactly what HEAD says, and HEAD is what the remote accepted.
  if [[ -f "$COORD_REPO/claims/$MID.json" ]]; then
    OWNER=$(json_get "$COORD_REPO/claims/$MID.json" claimed_by)
    STATE=$(json_get "$COORD_REPO/claims/$MID.json" state)
    if [[ "$OWNER" == "$COORD_MACHINE" && "$STATE" == "claimed" ]]; then
      [[ -f "$COORD_EMITTED_DIR/$MID" ]] && continue
      emit_handoff "$MID" "$(json_get "$COORD_REPO/claims/$MID.json" epoch)" "$REL"
      break
    fi
    # Somebody else's claim. Nothing writes "released" in V0, so this yields for
    # the life of the message; that is the one-way door the header describes.
    [[ "$STATE" != "released" ]] && continue
  fi

  claim_message "$MID" "$REL"
  case "$?" in
    0) emit_handoff "$MID" "$CLAIM_EPOCH" "$REL"; break ;;
    1) heartbeat "$TASK_ID" info "yielded $MID: $CLAIM_NOTE"; continue ;;
    2) fail prereq_fail 12 "claiming $MID: $CLAIM_NOTE" ;;
    *) heartbeat "$TASK_ID" warn "could not claim $MID: $CLAIM_NOTE"; continue ;;
  esac
done < <(printf '%s\n' "${CANDIDATES[@]+"${CANDIDATES[@]}"}")

# The sha reported in the pulse is the local tip, not the one probed at the top
# of the tick: after a claim of our own the probed value is already stale, and a
# pulse that misreports where this machine stands is worse than no pulse.
publish_pulse "$(coord_git rev-parse HEAD 2>/dev/null || printf '%s' "$REMOTE_SHA")" \
  || heartbeat "$TASK_ID" warn "pulse not published this tick (the ledger side succeeded)"

# The lock is released before the handoff is printed, so that nothing the
# conductor starts from this block can inherit the descriptor and hold it.
exec 9>&-

# A handoff that happened is reported even when some OTHER message in the same
# inbox was refused, because the emitted marker means this tick will never
# offer it again: swallowing the block here would lose the work silently. The
# refusal is heartbeated at error level on every tick that sees it; the
# quarantine marker only stops it from escalating a janitor every fifteen
# seconds for as long as the offending file sits in the inbox.
if [[ -n "$EMIT_BLOCK" ]]; then
  printf '%s\n' "$EMIT_BLOCK"
  exit 0
fi
if [[ -n "$VIOLATION" ]]; then
  fail contract_fail 20 "inbox message $VIOLATION violates the content contract; it was refused and quarantined, nothing about it was pushed"
fi
exit 0
