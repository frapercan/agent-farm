# FARM-COORD: cross-machine coordination on a git ledger

Specification, written 2026-08-12. Designed as three competing proposals, one
inside the platform, one on the broker and one on git, scored by three judges on
survivability, fit with the standing rules, and cost. Git won all three.

`TOPOLOGY.md` says git is the only channel that crosses. That is true for
reviewable instructions and false for transport: probed today from the desktop,
declaring a durable queue on the laptop's broker returned 201 and deleting it 204,
the platform API answered 200, and MinIO answered 200. The transport existed. What
did not exist was any agent layer above it. Correct the sentence rather than
repeat it.

## A correction to the reasoning, made after the design ran

The synthesis was given, in its brief, the assumption that the laptop is closed
most of the day, and it used that as its decisive argument: a mechanism hosted on
a machine that is often down inverts the topology.

**The assumption was wrong.** The laptop holds the containers and does not shut
down. The desktop is the compute and experimentation node, and it is the machine
designed to fail without consequence.

The conclusion survives, on three grounds that do not depend on uptime:

- **The arbiter is neither machine.** A push to the ledger branch is the lock,
  because GitHub serialises ref updates and rejects a non-fast-forward, so the
  loser of a race always learns it lost. No design hosted on either machine has
  an impartial arbiter.
- **The record is permanent.** A research campaign whose whole claim is
  reproducibility should not coordinate over a channel that destroys its record
  on acknowledgement.
- **No coupling to the live database.** Coordination never touches the shared
  Postgres, which is the object five wipes have taught this project to keep away
  from anything that spawns agents.

One thing the correction does change: failure mode 1 below, that the arbiter is
a WAN hop away while the alternatives are on the LAN, is now a **stronger**
objection than it looked, because the LAN alternative is always up. It is
recorded as the one place the losing designs genuinely beat this one.

## Why the other two lost, in their own terms

**Inside the platform.** The strongest design on interface, and the only one that
inherits tested claim, lease and reaper machinery. It loses by a category: its
first version runs the agent-spawning process as a worker holding a live session
factory against the shared Postgres and forks the spawn script out of it, so the
agent inherits the live connection details in its environment. That is the
hardest rule in the project and the proposal reported it as compliance. Its
reclaim path also re-executes a non-idempotent agent up to three times, because
the requeue limit was written for compute rows and not for worktrees, branches,
pull requests and token bills.

**On the broker.** Dominated: best on no criterion. Its headline property,
redelivery of unacknowledged messages, is switched off by its own consumer-timeout
workaround for the whole duration of every task. What remains as the record of a
claim is a SQLite file placed on the machine defined as holding no state. It is
the only design that loses silently, because after the acknowledgement the
message is gone with no history and no replay, so the two machines end up holding
different views of what was coordinated.

**Keeping the broker as a low-latency accelerator was considered and rejected.**
Sub-second delivery is worth nothing when the unit of work is a fifteen-hour run
or a pull request, and it costs a second control plane and a credential on a
personal machine.

## Prerequisites

| prerequisite | state | action |
|---|---|---|
| unattended restart after reboot | **done 2026-08-12** | `Linger=yes` set, unit enabled and active. It was `no`, and the unit is a user unit, so before today a reboot left the card idle until somebody logged in. `CLAUDE.md` claimed the opposite and was wrong |
| `tmux` | **absent** | needs a package install with root |
| farm state initialised | `state/` holds no task database | run the farm's init |
| topology documents on the trunk | `docs/two-machine-topology` and `feat/lab-worker-service` exist only as remote branches | merge both, or this specification describes a topology the default checkout cannot see |

## The contract

A private repository, `farm-coord`, with no CI, no branch protection, and no
branch named `main` or `develop` so the direct-push habit stays unambiguous.
Default branch `ledger`.

```
inbox/<machine>/<utc-ts>-<ulid>-<kind>.json    messages addressed TO a machine
claims/<message-id>.json                       exclusive claims, the CAS target
ledger/<yyyy-mm-dd>/<ulid>-<machine>.json      append-only outcome record
ARCHIVE/<yyyy-mm>.jsonl                        monthly compaction by ordinary commit
SCHEMA.md                                      the contract, versioned with the data
```

Branch `pulse` carries `pulse/<machine>.json` and nothing else. It is disposable,
force-pushed on truncation, and read only for liveness.

**One writer per path, by construction.** `inbox/<machine>/` is created by the
sender and deleted by the recipient. `claims/<id>.json` is created by the
claimant and rewritten only by the claimant or by a superseding compare-and-swap.
`pulse/<machine>.json` is written only by that machine. Textual conflicts are
therefore impossible and semantic ones are settled by the swap.

A message:

```json
{
  "schema": "farm.coord/1",
  "id": "01K2Q7X4M8ZB3V0N7YQ2C6TD9E",
  "kind": "task",
  "created_at": "2026-08-12T14:03:21Z",
  "from": "laptop",
  "to": "any",
  "requires": ["gpu"],
  "priority": 50,
  "expires_at": "2026-08-13T14:03:21Z",
  "subject": "size the oracle calibration gap on the frozen BPO score TSV",
  "body": "CPU only. Numbers go in the referenced job's events, not in the reply.",
  "ref": {
    "loop": "rung2",
    "slice": "R2-S07",
    "repo": "agent-farm",
    "commit": "9c1f0ae4bd2f1c33a0e77b9d4c8e12ab5f6d0a91",
    "path": "plans/rung2/PLAN.md",
    "protea_job_id": null
  }
}
```

**Nothing sensitive fits in it.** There is no field for a connection string, a
credential or an absolute path, and the tick rejects a message matching a home
path, a database URL, a broker URL or a bare address before it is pushed.

## Lifecycle

**On boot.** The supervisor starts under systemd beside the lab worker. It
fetches, reads back its own claims, and reconciles them against local processes.
A claim with no live process is released explicitly, which turns a clean reboot
from a fifteen-minute lease stall into a sixty-second one. It publishes a pulse
and enters the loop.

**On noticing.** Poll is `git ls-remote`, one round trip with no object transfer,
measured on this desktop at 0.61 to 0.82 seconds. Fetch happens only on a change.
Interval is 15 seconds with capacity and 60 without, since a busy machine cannot
take work anyway. Worst-case delivery is 16 seconds, mean about 8.5.

**On claiming.** Filter the inbox by address, expiry, and whether the machine's
own published capabilities satisfy `requires`. Take the highest priority, write
the claim, commit, push. **Push accepted means the claim is exclusive.** Push
rejected means somebody moved the branch: fetch, reset, re-read the claim, and
branch three ways. Absent, retry with jitter. Mine, proceed. Not mine, yield and
take the next.

**On the first irreversible act.** The spawned agent re-reads the claim and
verifies the owner and the epoch before its first push, its first job dispatch
and any pull request. A mismatch means it was superseded and it stops. This
fences the process rather than the record, which no proposal did, and it costs
one `git show` per irreversible act.

**On finishing.** Write the ledger entry with durable references, set the claim
done or failed, delete the inbox file, push under the same retry. **Results are
not in the ledger.** They are in the platform, and the ledger names the job id.

**On dying.** Nothing pushed is lost, because the state is on a remote neither
machine hosts, and delivery is a log rather than a stream, so there is no
missed-while-offline class: the machine wakes, fetches once, and sees everything
since its last-seen sha. The dead machine stops pulsing, and after the grace
period any eligible machine supersedes its claims with a higher epoch. If the
original agent is somehow alive it fails its fence and stops.

## How duplicated work is prevented

Four layers, in firing order:

1. **Capability routing** narrows most messages to one eligible machine.
2. **Compare-and-swap on the remote ref** is the real lock.
3. **The pulse lease** reclaims after a crash, bounded and observable.
4. **The platform's own dedup key** already refuses duplicate compute with a 409.

The claim prevents duplicate **attention**, which is the expensive duplication:
two agents deciding the same thing costs two worktrees, two branches, two pull
requests and two token bills before either reaches a dispatch that would have
refused it.

## How the human injects a message

- **`coord-send.sh --to desktop --requires gpu --subject "..." --body-file note.md`**,
  from any checkout on either machine. It stages outside the coordination
  worktree and holds a lock, because a retry loop that resets a worktree shared
  with the sender would discard a committed but unpushed human message with no
  error, and this project has an incident of exactly that shape.
- **The GitHub web editor**, from a phone. Create a file under `inbox/<machine>/`
  on `ledger`. No tunnel, no VPN, no SSH hop.
- **The paste case.** Each tick renders the pending inbox as plain text and
  composes the prompt in the form the conductor already consumes, so there is
  always a prepared message to paste into the other machine's session.
- **`to: "any"` with `requires`** is the right form when the human knows the
  capability but not the machine.

## V0, and what it deliberately is not

About 400 lines of shell, one schema, no new tables, no migrations, no new
dependencies, and no credential on the desktop beyond the git token already
there.

1. Create the private repository with the layout and the schema.
2. `coord-send.sh`, about 80 lines.
3. `coord-tick.sh`, about 250 lines.
4. `coord-fence.sh`, about 20 lines.
5. `coord-keeper-supervisor.sh`, about 40 lines, structurally a copy of the
   deploy keeper.
6. **One systemd unit per machine.** Neither of the other proposals shipped one,
   and the existing keeper documents its own lifecycle as spawned in tmux and
   terminated by hand, which on this desktop means a supervisor that dies at
   reboot and stays dead in a tmux that is not installed.
7. One line in the conductor launcher so the bootstrap paste includes the inbox.

It deliberately does not:

- **Reach sub-second.** The floor is about 8.5 seconds mean. Coordination
  messages are complete instructions, not the opening of a conversation.
- **Dispatch compute.** That stays on the job registry; the message carries the
  job id.
- **Resurrect agents.** systemd does that, and as of today it can.
- **Spawn an agent automatically.** The tick prints the composed prompt and the
  conductor decides. V0 changes no existing behaviour and can be deleted without
  trace.
- **Scale past a handful of writers.** One lock word for the whole branch. At two
  machines the retry is invisible; at ten it degrades into a retry storm, and at
  that point the correct answer is a broker.
- **Synchronise assistant memory.** That stays per machine.

**V1**, in order: the expiry sweep, monthly compaction by ordinary commit and
never by rewrite, and a mirror operation in the platform that emits one event per
coordination message so the stream appears in the frontend beside the jobs. Git
is the transport, the platform is the display, and the mirror is allowed to fail
without coordination failing.

## Failure modes that remain

1. **The arbiter is a WAN hop away.** A router or provider outage kills
   coordination completely, while a broker or database on the laptop would keep
   working, and the laptop is always up. This is the one place the losing designs
   genuinely beat this one. Degradation is graceful: work in flight continues and
   the local plans are an offline cache of intent.
2. **Silence is indistinguishable from having nothing to say.** The pulse proves
   the supervisor is alive, not that the agent is doing anything useful. This is
   the recorded lesson that stale output is not a dead agent, and this design does
   not solve it.
3. **The fence has a window.** A machine can start spending tokens before it
   learns it lost the race. Claiming first bounds the exposure to one round trip.
4. **Semantic duplication survives a clean merge.** Two machines can start the
   same experiment under two message ids. The platform catches it at the compute
   boundary, after the tokens are spent.
5. **The branch grows**, and compaction must never rewrite `ledger` history,
   because a rewrite breaks the swap for any concurrent reader.
6. **Nothing enforces the content rules except the lint.** No secrets and no
   absolute paths are contract, not mechanism.
7. **The repository is private, not encrypted.** Anyone with read access reads
   every message, permanently. Smaller than the anonymous job stream the platform
   design would have used, and still a surface.
8. **`ledger` is force-pushable**, necessarily, because the mechanism is direct
   push. The mitigation is that the repository contains no code, so no agent has
   a reason to touch it outside the two scripts, and both push fast-forward only.
9. **V0 violates the letter of the platform-integration norm**, with a plan to
   close it in V1. Unbuilt second phases have a poor record in this project, and
   this should be labelled as a violation with a plan rather than argued around.
