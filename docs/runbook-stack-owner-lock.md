# Runbook: PROTEA-stack ownership lock

The dev workspace PROTEA stack (postgres + rabbit + uvicorn + workers +
Next.js + ngrok) is a single shared resource between two independent
agents:

1. `deploy-keeper-supervisor.sh`, which rebuilds + restarts the stack
   whenever `origin/develop` moves and on every poll cycle.
2. The conductor (or a human running a long export pipeline by hand)
   keeps the stack running with extra env vars set (anc2vec path,
   pair-feature pool size, align-cache dir, ...) that the deploy-keeper
   stack does NOT carry.

The 2026-05-20 incident burned exactly this hole: an auto-spawned
deploy-keeper killed an in-flight FARM-EXP.13 export by silently
restarting the stack out from under it. The advisory lock added in
FARM-FEAT.12 lets each side cooperate without a heavyweight scheduler.

## Shape

A single JSON file at `agent-farm/state/stack-owner.json`:

```json
{
  "owner": "export",
  "task_id": "farm-exp-13",
  "acquired_at": "2026-05-23T18:32:11+00:00",
  "reason": "FARM-EXP.13 24-cell sweep"
}
```

Three owners are recognised:

- `free` (default; file may be absent)
- `deploy` (deploy-keeper itself holds the stack for a deploy cycle)
- `export` (an export pipeline holds the stack and forbids restarts)

## Helper CLI

`scripts/lib/stack_owner.sh` is both a sourceable library and a
standalone CLI:

**`acquire <owner> <task_id> <reason>`**. Atomically claim the lock.
Idempotent under reentry by the same `task_id`. Exits: 0 on success,
1 on bad args, 2 on contention (a different owner holds), 4 on flock
timeout.

**`release <task_id>`**. Clear the owner back to `free` iff the current
holder matches. Exits: 0 on success (or already free), 1 on bad args,
3 on mismatched holder, 4 on flock timeout.

**`current`**. Print the current owner (`free`, `deploy`, `export`)
on stdout. Exit 0.

**`status`**. Print the full JSON record (synthesises a `free` record
if the file is missing). Exit 0.

Concurrency: each verb runs inside an `flock(1)`-guarded subshell on a
sibling `.lock` file. Bounded by `STACK_OWNER_FLOCK_TIMEOUT_SEC`
(default 5s) so a stuck holder can never wedge the helper indefinitely.

## Acquiring before a long export

The conductor (or a human) runs this before dispatching a long
export-batch job:

```bash
bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh \
  acquire export farm-exp-13 "24-cell research-dataset sweep"
```

The shell exits non-zero (code 2) if some other agent already holds the
lock; the conductor should treat that as a wait-and-retry condition,
NOT escalate.

## Releasing after the export completes

```bash
bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh release farm-exp-13
```

Mismatched releases exit non-zero (code 3) on purpose: a stale
supervisor cannot trample a live export's hold by accident.

## deploy-keeper integration

`scripts/services/deploy-keeper-tick.sh` consults the lock at the very
top of every tick (before the docker / port-listener probes):

- `owner == free` or `owner == deploy`: the tick proceeds normally.
- `owner == export`: the tick logs a
  `deferred-stack-owned-by-task task_id=<holder>` heartbeat and exits 0
  (intentional noop). The supervisor sleeps the full `poll_interval`
  (default 5min) and tries again next cycle.
- any unknown value: treated as `free` with a `warn` heartbeat so a typo
  in the file does not silently disable the keeper.

The lock is advisory. The supervisor CHOOSES to honor it because the
two failure modes are asymmetric: a no-op deploy-keeper tick costs
nothing, a blind restart costs hours-to-days of GPU export progress.

## Operator checks

- `bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh current` to see who
  holds the lock right now.
- `bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh status` for the
  full record (acquired-at + reason).
- Grep heartbeats for `deferred-stack-owned-by-task` to see when
  deploy-keeper last skipped a tick due to the lock.

## Recovery if the lock is stuck

If a process crashed mid-export without releasing the lock, force a
release via the standalone CLI (no flock contention because the holder
is gone):

```bash
bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh release <task_id>
```

`<task_id>` MUST match the value recorded in `stack-owner.json`. Reach
for `bash $AGENT_FARM_ROOT/scripts/lib/stack_owner.sh status` if you
need to look it up.

For a hard reset (e.g. a corrupted JSON record) just delete the file:

```bash
rm -f $AGENT_FARM_ROOT/state/stack-owner.json
```

The next `acquire` will start from a clean slate.

## Tests

`tests/test_stack_owner_lock.sh` exercises three scenarios end-to-end:

- Acquire `export`, run a tick, assert exit 0 + deferred heartbeat +
  redeploy stub NOT invoked.
- Release `export`, run a tick, assert exit 0 + redeploy stub invoked +
  no deferred heartbeat.
- Bad-input guardrails: reject `owner=free`, reject empty task_id,
  exit 3 on mismatched release.

Run via `bash tests/test_stack_owner_lock.sh`. The test never touches
the live PROTEA stack: docker + ss are stubbed via PATH, and the three
deploy `lib/*.sh` scripts are replaced with marker-printing stubs.

## References

- Memory `project_deploy_keeper_coordination_directive` (user-stated
  requirement on 2026-05-22).
- Memory `feedback_deploykeeper_vs_export_stack_conflict` (the
  2026-05-20 landmine that motivated the lock).
- Plan slice `FARM-FEAT.12` in
  `agent-farm/plans/farm-platform/PLAN.md`.
