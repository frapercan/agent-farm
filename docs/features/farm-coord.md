---
name: farm-coord
section: "6-services"
state: partial
owner: agent-farm conductor loop
source:
  - scripts/coord/coord-send.sh
  - scripts/coord/coord-tick.sh
  - scripts/coord/coord-fence.sh
  - scripts/services/coord-keeper-supervisor.sh
  - scripts/services/coord-keeper.service
runbook: docs/features/farm-coord.md
smoke: bash -n scripts/coord/coord-tick.sh
---

# farm-coord

Coordination between the two machines of the farm, carried on a git
repository (`farm-coord`) rather than on a queue. One machine writes a
message, the other claims it, and the claim is exclusive because the push
that records it is a compare-and-swap that the remote arbitrates. Neither
machine is the arbiter, so neither has to be reachable by the other, and
the whole thing survives a laptop that is closed and a desktop that
reboots without warning.

Five pieces, three of which a human touches:

| Piece | Runs | Does |
|---|---|---|
| `scripts/coord/coord-send.sh` | by hand | composes one message and pushes it to the ledger branch |
| `scripts/services/coord-keeper-supervisor.sh` | systemd, or `spawn.sh` | the persistent loop: probe, tick, back off, escalate |
| `scripts/coord/coord-tick.sh` | one pass per poll | reads the inbox, claims one message, prints a handoff block |
| `scripts/coord/coord-fence.sh` | by the spawned agent | re-reads the claim from the remote before an irreversible act |
| `scripts/services/coord-keeper.service` | systemd user unit | brings the supervisor back after a reboot |

## Source coordinates

- `scripts/coord/coord-send.sh`
- `scripts/coord/coord-tick.sh`
- `scripts/coord/coord-fence.sh`
- `scripts/services/coord-keeper-supervisor.sh`
- `scripts/services/coord-keeper.service`
- `state/coord-machine` (this machine's coordination name, one line)
- `state/coord-capabilities` (one capability per line)
- `state/coord-keeper/` (markers, pulse throttle, last fail kind)

## Branches on the coordination repository

| Branch | Written by | Holds |
|---|---|---|
| `ledger` | everybody, one path each | `inbox/<machine>/`, `claims/`, `ledger/<date>/` |
| `pulse` | each keeper, its own file | `pulse/<machine>.json`, liveness only |

The ledger merges cleanly because every writer owns a distinct path. That
property is about merging, and it is worth being explicit that it says
nothing about resets: `git reset` and `git clean` are branch scoped and
tree scoped, never path scoped.

## Two clones, and why

There are two checkouts of the coordination repository on a machine that
runs the keeper, and swapping them is the single easiest way to lose work.

- `~/Thesis2/farm-coord` is the SHARED one. A human sends from it, a
  finishing agent writes its outcome entry in it, and the fence reads
  through it. Nothing ever resets it.
- `~/Thesis2/farm-coord-keeper` is the KEEPER's own. Only the tick opens
  it. The tick follows the remote tip by resetting and cleaning, which is
  safe precisely because nothing else writes there.

Create the second one before enabling the unit, or the supervisor exits
78 and says so:

```bash
git clone <farm-coord remote> ~/Thesis2/farm-coord-keeper
```

The tick refuses to discard anything it cannot prove it wrote (an
uncommitted edit under `ledger/` or `inbox/`, or a local commit touching
anything outside `claims/`), so pointing `COORD_REPO` at the shared clone
degrades into skipped ticks with a warning heartbeat rather than into a
deleted outcome entry. That guard is a seatbelt, not a licence: use two
clones.

## The claim is a one-way door in V0

`coord-tick.sh` writes `claims/<id>.json` with state `claimed`, and
nothing in this version ever writes any other value. There is no lease,
no expiry sweep and no supersede by epoch. The consequences, so that
nobody has to rediscover them from behaviour:

1. Once a message is claimed, the other machine yields to it for as long
   as the message sits inside its `expires_at`.
2. This machine hands the message off again after a reboot. The marker
   that says "already handed off" is scoped to the boot id, so a reboot
   makes it vanish, the claim on the remote is unchanged, and the fence
   passes for the replacement agent at the same epoch. This is the
   failure this desktop is documented to hit, and it costs nothing.
3. An agent that dies WITHOUT a reboot is not recovered. The claim stays
   open and the task row stays where the agent left it. The keeper raises
   one error heartbeat per message once the claim is older than
   `COORD_STALE_CLAIM_SEC` (six hours by default), and a human resolves
   it. Nothing else will.

Closing case 3 needs a lease: a writer for the `released` state, a grace
period, and a boot reconciliation in the supervisor. Both readers of that
value are already written against it, so the lease item adds a writer and
does not re-open the branches.

## Ordering, expiry and capability

A message carries `to` (a machine name or `any`), `requires` (capability
names the taking machine must have), `priority` and `expires_at`. The
tick takes the highest priority eligible message and the oldest within a
priority. A message whose `expires_at` has passed is dropped by both
machines with no ledger entry, which is the one silent outcome in the
design: set the window with the work in mind.

## The content contract

The ledger is permanent and readable by anyone with access to the
repository, so a message may not carry an absolute home path, a database
or broker URL, a bare network address, a credential, a token or a private
key. It is enforced twice, on the send side and again on the receive
side, because the receive side is what protects a machine from a message
composed anywhere else. A refusal quarantines the message, names the
RULES that matched and never the text that matched them, and exits
`contract_fail`.

## State

partial. Working and exercised on a throwaway fixture: the claim path,
the compare-and-swap under contention, the yield, the handoff block, the
pulse, the reboot re-handoff, the content contract, the resync guard and
the supervisor's systemd path. Not yet exercised against the real remote
repository, which does not exist yet.

Deliberately absent in V0: the tick does not spawn the agent (the
conductor consumes the block), does not write the ledger outcome entry
(the finishing agent does), and does not release a claim.

## Smoke test

```bash
bash -n scripts/coord/coord-send.sh
bash -n scripts/coord/coord-tick.sh
bash -n scripts/coord/coord-fence.sh
bash -n scripts/services/coord-keeper-supervisor.sh

# One pass by hand, against the keeper's clone. Prints a K=V block only
# when it took a message; silence means there was nothing eligible.
TASK_ID=<a task row> bash scripts/coord/coord-tick.sh
```

## Runbook

Send a message:

```bash
bash scripts/coord/coord-send.sh --to any --requires gpu \
  --subject "embed the new shard" --body-file /path/to/body.md \
  --priority 60 --expires-in 12h
```

Enable the keeper (a user unit; lingering must be on or it stops at
logout):

```bash
cp scripts/services/coord-keeper.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now coord-keeper
```

Read what it is doing. The durable record is the heartbeats table and the
ledger itself, not the journal:

```bash
python3 scripts/lib/db.py query \
  "SELECT ts, level, message FROM heartbeats
    WHERE task_id LIKE 'coord-keeper%' ORDER BY rowid DESC LIMIT 20"
```

Fail kinds and what they mean:

| Kind | Meaning | Escalates a janitor |
|---|---|---|
| `config_fail` | the branch resolves to a trunk, the clone is inside a code checkout, or the machine name is not plain | the unit stops (78) |
| `prereq_fail` | the remote cannot be reached, the lock is held, or the resync was refused | no, by design: a WAN outage is not something a janitor can fix |
| `contract_fail` | a message carries forbidden content; it was refused and nothing about it was pushed | yes |

A spawned agent must fence before its first push, its first job dispatch
and any pull request:

```bash
bash scripts/coord/coord-fence.sh <message-id> <expected-epoch>
```

Exit 0 proceeds. Exit 1 means the claim was superseded and the work must
stop. Exit 3 means ownership could not be verified (no clone, no `jq`, no
remote), which also stops: ownership that cannot be read is not
ownership.

## Current owner

agent-farm conductor loop, on the compute node. The laptop runs the same
keeper against the same remote with its own machine name and its own
capability file.
