#!/usr/bin/env bash
# coord-send.sh: compose one FARM-COORD message and push it to the ledger.
#
# The message is staged with a TEMPORARY INDEX against the coordination
# repository's object database, so the coordination worktree, its HEAD and its
# real index are never read, reset or written. That is deliberate: a retry loop
# that reset a worktree shared with the sender would discard a committed but
# unpushed human message with no error, and this project has an incident of
# exactly that shape.
#
# The push of <commit>:refs/heads/ledger IS the compare-and-swap. It is never
# forced, so a concurrent writer that moved the branch makes the push a
# non-fast-forward, the remote rejects it, and this script re-reads the tip and
# rebuilds on top of it. The arbiter is the remote, not either machine.
#
# Usage:
#   coord-send.sh --to <machine|any> --subject "..." [--body-file FILE]
#                 [--requires gpu,cpu] [--priority 50] [--expires-in 24h]
#                 [--kind task] [--ref-repo R] [--ref-commit SHA] [--ref-path P]
#
# Output (stdout, K=V, one per line): message_id, inbox_path, ledger_commit.
# Everything else goes to stderr.
#
# This is the SHARED checkout (~/Thesis2/farm-coord): the one a human sends
# from, the one a finishing agent writes its ledger entry in, and the one
# coord-fence.sh reads. The keeper polls a clone of its own and never touches
# this tree, which is why nothing here has to defend against its resets.
#
# Env knobs: FARM_COORD_ROOT (checkout of farm-coord), FARM_COORD_BRANCH,
# FARM_COORD_REMOTE, COORD_MACHINE (this machine's name), COORD_LOCK_WAIT_SEC.

set -euo pipefail

# Resolved from this script's own location rather than the caller's directory,
# so a send from anywhere finds the same state directory the keeper writes to.
FARM_ROOT="${AGENT_FARM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
COORD_ROOT="${FARM_COORD_ROOT:-$HOME/Thesis2/farm-coord}"
COORD_BRANCH="${FARM_COORD_BRANCH:-ledger}"
COORD_REMOTE="${FARM_COORD_REMOTE:-origin}"
LOCK_WAIT_SEC="${COORD_LOCK_WAIT_SEC:-30}"
MAX_ATTEMPTS="${COORD_PUSH_ATTEMPTS:-5}"

die() { printf 'coord-send: %s\n' "$*" >&2; exit 1; }
usage() { sed -n '2,25p' "$0" >&2; exit "${1:-2}"; }

TO="" SUBJECT="" BODY_FILE="" REQUIRES="" PRIORITY=50 EXPIRES_IN="24h" KIND="task"
REF_REPO="" REF_COMMIT="" REF_PATH=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --to)          TO="${2:?--to needs a value}"; shift 2 ;;
    --subject)     SUBJECT="${2:?--subject needs a value}"; shift 2 ;;
    --body-file)   BODY_FILE="${2:?--body-file needs a value}"; shift 2 ;;
    --requires)    REQUIRES="${2:?--requires needs a value}"; shift 2 ;;
    --priority)    PRIORITY="${2:?--priority needs a value}"; shift 2 ;;
    --expires-in)  EXPIRES_IN="${2:?--expires-in needs a value}"; shift 2 ;;
    --kind)        KIND="${2:?--kind needs a value}"; shift 2 ;;
    --ref-repo)    REF_REPO="${2:?--ref-repo needs a value}"; shift 2 ;;
    --ref-commit)  REF_COMMIT="${2:?--ref-commit needs a value}"; shift 2 ;;
    --ref-path)    REF_PATH="${2:?--ref-path needs a value}"; shift 2 ;;
    -h|--help)     usage 0 ;;
    *)             printf 'coord-send: unknown flag %s\n' "$1" >&2; usage 2 ;;
  esac
done

# This machine's coordination name routes every claim and is stamped into every
# message, so it is never guessed from the hostname: a wrong name addresses a
# machine that does not exist and nothing downstream reports it.
#
# The SAME file the tick reads. These two scripts run against different clones,
# the human's and the keeper's, so a name kept beside either clone is a name
# that can disagree with itself; the identity belongs to the machine, not to a
# checkout. Keeping it in the farm's state directory is what makes "one name per
# machine" true rather than merely intended.
MACHINE_FILE="${COORD_MACHINE_FILE:-$FARM_ROOT/state/coord-machine}"
FROM="${COORD_MACHINE:-}"
if [[ -z "$FROM" && -r "$MACHINE_FILE" ]]; then FROM=$(tr -d '[:space:]' < "$MACHINE_FILE"); fi
[[ -n "$FROM" ]] || die "this machine has no coordination name: write it to $MACHINE_FILE (one word, for example 'desktop' or 'laptop'), or export COORD_MACHINE"

[[ -n "$TO" ]]       || die "--to is required (a machine name, or 'any')"
[[ -n "$SUBJECT" ]]  || die "--subject is required"
[[ "$TO"    =~ ^[a-z][a-z0-9-]{0,31}$ ]] || die "--to '$TO' is not a plain machine name"
[[ "$KIND"  =~ ^[a-z][a-z0-9-]{0,31}$ ]] || die "--kind '$KIND' is not a plain kind name"
[[ "$FROM"  =~ ^[a-z][a-z0-9-]{0,31}$ ]] || die "coordination name '$FROM' is not plain (lowercase, digits, hyphen)"
[[ "$PRIORITY" =~ ^[0-9]{1,3}$ ]]        || die "--priority '$PRIORITY' is not an integer"
[[ -z "$BODY_FILE" || -r "$BODY_FILE" ]] || die "--body-file '$BODY_FILE' is not readable"
[[ -d "$COORD_ROOT/.git" ]] || die "no coordination checkout at $COORD_ROOT (set FARM_COORD_ROOT, or clone farm-coord there)"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/coord-send.XXXXXX") || die "cannot create a staging directory"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/message.json"

# Compose. python3 owns the ULID, the clocks and the JSON escaping, because
# hand-rolled JSON quoting in shell is how a body with a quote in it corrupts a
# branch that every other reader parses strictly.
read -r MSG_ID MSG_TS < <(python3 - "$OUT" "$KIND" "$FROM" "$TO" "$REQUIRES" "$PRIORITY" \
    "$EXPIRES_IN" "$SUBJECT" "$BODY_FILE" "$REF_REPO" "$REF_COMMIT" "$REF_PATH" <<'PY'
import json, os, re, sys, time, datetime
out, kind, frm, to, requires, priority, expires, subject, body_file, r_repo, r_commit, r_path = sys.argv[1:13]
A = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"          # Crockford base32
def b32(n, ln): return "".join(A[(n >> (5 * i)) & 31] for i in range(ln - 1, -1, -1))
now = time.time()
ulid = b32(int(now * 1000), 10) + b32(int.from_bytes(os.urandom(10), "big"), 16)
m = re.fullmatch(r"(\d+)([smhd])", expires.strip())   # the unit is required, never assumed
if not m: sys.exit(f"coord-send: --expires-in '{expires}' is not <n> followed by s, m, h or d")
ttl = int(m.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]
stamp = lambda t, f: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime(f)
utc = lambda t: stamp(t, "%Y-%m-%dT%H:%M:%SZ")
body = open(body_file, encoding="utf-8").read().rstrip("\n") if body_file else ""
msg = {
    "schema": "farm.coord/1", "id": ulid, "kind": kind,
    "created_at": utc(now), "from": frm, "to": to,
    "requires": [c for c in (x.strip() for x in requires.split(",")) if c],
    "priority": int(priority), "expires_at": utc(now + ttl),
    "subject": subject, "body": body,
    "ref": {"repo": r_repo or None, "commit": r_commit or None,
            "path": r_path or None, "protea_job_id": None},
}
with open(out, "w", encoding="utf-8") as f:
    json.dump(msg, f, indent=2, ensure_ascii=False, sort_keys=False)
    f.write("\n")
print(ulid, stamp(now, "%Y%m%dT%H%M%SZ"))
PY
) || die "composing the message failed (see the error above)"

# Content gate. Contract, enforced here because nothing downstream enforces it:
# no home path, no database or broker URL, no bare address may reach a branch
# that is permanent and readable by anyone with access to the repository.
BAD=()
scan() {
  local label="$1" re="$2" hit
  hit=$( { grep -oP "$re" "$OUT" || true; } | sort -u | head -3 | tr '\n' ' ') || true
  [[ -n "${hit// /}" ]] && BAD+=("$label -> ${hit% }")
  return 0
}
scan "absolute home path"   '(?:/home|/Users|/root)/[A-Za-z0-9._-]+'
scan "database URL"         '(?:postgres(?:ql)?|mysql|mongodb|sqlite)(?:\+[a-z0-9]+)?://[^"\s\\]*'
scan "broker URL"           '(?:amqps?|redis|kafka)://[^"\s\\]*'
scan "bare network address" '(?<![0-9A-Za-z.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9A-Za-z.])'
if [[ ${#BAD[@]} -gt 0 ]]; then
  printf 'coord-send: refusing to push, the message carries forbidden content:\n' >&2
  printf '  %s\n' "${BAD[@]}" >&2
  die "rewrite the subject or the body; the ledger is permanent and world-readable to anyone with repository access"
fi

REL="inbox/$TO/$MSG_TS-$MSG_ID-$KIND.json"
LOCK="$COORD_ROOT/.git/farm-coord.lock"   # inside .git, so it is never an untracked file
COMMIT_OUT="$TMP/commit"
RC=0
(
  # `flock -w` bounds the wait so a wedged tick cannot hang a human send.
  flock -w "$LOCK_WAIT_SEC" 9 || { printf 'coord-send: lock on %s still held after %ss (a tick is running?)\n' "$LOCK" "$LOCK_WAIT_SEC" >&2; exit 4; }
  blob=$(git -C "$COORD_ROOT" hash-object -w -- "$OUT") \
    || { printf 'coord-send: cannot write the message blob into %s\n' "$COORD_ROOT" >&2; exit 6; }
  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    git -C "$COORD_ROOT" fetch --quiet "$COORD_REMOTE" "$COORD_BRANCH" \
      || { printf 'coord-send: cannot fetch %s/%s (network or credentials)\n' "$COORD_REMOTE" "$COORD_BRANCH" >&2; exit 5; }
    base=$(git -C "$COORD_ROOT" rev-parse FETCH_HEAD)
    rm -f "$TMP/index"
    export GIT_INDEX_FILE="$TMP/index"      # staged OUTSIDE the worktree index
    git -C "$COORD_ROOT" read-tree "$base"
    git -C "$COORD_ROOT" update-index --add --cacheinfo "100644,$blob,$REL"
    tree=$(git -C "$COORD_ROOT" write-tree)
    unset GIT_INDEX_FILE
    commit=$(git -C "$COORD_ROOT" commit-tree "$tree" -p "$base" \
      -m "coord: $KIND $MSG_ID from $FROM to $TO") \
      || { printf 'coord-send: commit-tree failed (is user.name and user.email set?)\n' >&2; exit 6; }
    if git -C "$COORD_ROOT" push --quiet "$COORD_REMOTE" "$commit:refs/heads/$COORD_BRANCH"; then
      printf '%s' "$commit" > "$COMMIT_OUT"; exit 0
    fi
    printf 'coord-send: push rejected, %s moved under us; attempt %s/%s\n' "$COORD_BRANCH" "$attempt" "$MAX_ATTEMPTS" >&2
    sleep "$(( (RANDOM % 4) + 1 ))"
  done
  printf 'coord-send: lost the compare-and-swap %s times in a row; nothing was written\n' "$MAX_ATTEMPTS" >&2
  exit 7
) 9>"$LOCK" || RC=$?
[[ $RC -eq 0 ]] || exit "$RC"

printf 'message_id=%s\ninbox_path=%s\nledger_commit=%s\n' "$MSG_ID" "$REL" "$(cat "$COMMIT_OUT")"
