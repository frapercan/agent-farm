# D34. DAG + resource-constrained scheduler for agent-farm

- Status: proposed
- Date: 2026-06-22
- Driver: dag-scheduler campaign (phase F-SCHED)
- Author: Francisco Miguel Pérez Canales

## Context

Agent-farm coordinates many concurrent fronts (PROTEA, the LAFA method,
the reranker lab, the thesis, infra). Work is described as a per-loop
catalog of slices in `plans/<loop>/PLAN.md`. The conductor is a Claude
REPL in tmux that reads `prompts/conductor.md` plus
`prompts/bootstrap-autowork.md` and picks what to run next.

Two structural facts drive this decision.

1. The plan store is already a latent DAG. Every slice carries
   `deps: list[str]` of slice ids, and `scripts/lib/plan_parser.py:find_next`
   already gates eligibility on `all(d in done_ids for d in s.deps)`. The
   edges and the "deps done means eligible" rule exist. What is missing is
   not the graph.

2. The parts that fail are not the dependency logic. They are
   concurrency and shared resources, and they live in prose, not code:
   - `find_next` returns one slice, not the ready frontier, so real
     parallelism is whatever the conductor prompt happens to spawn.
   - The "one executor, one doc-writer in flight" cap is English in
     `bootstrap-autowork.md`, enforced by prompt discipline alone.
   - There is exactly one shared-resource mutex, `scripts/lib/stack_owner.sh`,
     a bespoke flock over "the dev stack" with owners hard-coded to
     `deploy|export`. It is disconnected from the plan: a slice cannot
     declare which resources it needs, and `find_next` is resource-blind.
   - There is no GPU lease, no DB-write lease, no node concept, no cycle
     detection.

The cost of (2) is in the incident record: postgres OOM when a second
consumer was scaled up, repeated wipes of the live database when an agent
was pointed at it, CUDA-OOM loops when a model was double-loaded on the
single 12GB GPU. Each of these is a resource-contention failure that a
resource-aware scheduler would refuse to schedule.

The user also intends to add a second compute node (a laptop) alongside
the desktop in the future. So the resource model must be node-aware from
the start, even while only one node exists today.

## Decision

Move scheduling into deterministic code and make it DAG-aware and
resource-constrained, node-aware by construction. The conductor stops
choosing concurrency by prompt discipline and instead dispatches exactly
what the scheduler returns.

Five components, all building on the existing markdown plan store (no plan
rewrite, no external workflow engine).

### 1. DAG validation

At parse time (`discover_slices`), build the dependency graph, reject
cycles and dangling dep ids the same way duplicate ids are already
rejected (raise `SystemExit`). The plan store becomes a validated DAG, not
a list that happens to carry edges.

### 2. Resource model on slices

Each slice optionally declares the resources it needs. Two kinds:

- Exclusive (named mutex, capacity one, held to the exclusion of all
  others): `stack`, `db-write`.
- Quantitative (capacity, divisible, bin-packed): `ram_gb`, `cpu_cores`,
  `gpu` (count or VRAM), `pg_consumers`, `minio_io`.

```yaml
resources:
  exclusive: [db-write]
  ram_gb: 24
  gpu: 1
  pg_consumers: 1
```

Default is empty: a slice with no `resources` block schedules freely, so
every existing slice behaves exactly as today. `stack_owner.sh` is
absorbed: "the stack" becomes one exclusive resource, and its current
acquire/release callers keep working through a shim until migrated.

### 3. Node registry

A node advertises capacity. Today one node (desktop); tomorrow a laptop is
added as another row, no code change.

```yaml
id: desktop
capacity: { ram_gb: 64, cpu_cores: 16, gpu: 1, pg_consumers: 1, minio_io: 1 }
status: online
```

State lives in sqlite (`nodes`, `leases` tables) next to the existing
`tasks` and `heartbeats` tables.

### 4. Frontier scheduler

`find_next` (top-1) is kept for single-pick callers. A new `find_frontier`
returns all ready slices (pending, deps done, dependents-of-failed
excluded). The scheduler then, in priority order, tries to place each
frontier slice on a node whose free capacity fits its quantitative
requests and whose named mutexes are free, acquiring an atomic lease per
resource. A slice that fits is dispatched on that node and set
`in_progress`; a slice that does not fit waits. Leases are released on
task finalize, and a TTL reaper (reusing the existing heartbeat pattern)
releases stale leases from dead tasks.

This subsumes the OOM/wipe class structurally: `db-write` as an exclusive
mutex means at most one DB writer ever exists; `pg_consumers: 1` capacity
means a second consumer is never scheduled; `gpu: 1` means no double-load.

### 5. Status lifecycle and failure isolation

Extend the lifecycle from `pending|in_progress|blocked|done|deferred` with
`in_review`, `failed`, `quarantined`.

- `in_review`: agent finished, PR open, CI running (the delivery surface,
  distinct from `in_progress`).
- `failed`: the task errored.
- `quarantined`: failed and awaiting a human decision or retry.

Failure isolation rule: a slice whose dep is `failed` or `quarantined` is
withheld from the frontier (it shows as blocked-by-failure), but every
slice not transitively downstream of the failure keeps scheduling. One red
node stalls only its own subtree, never the whole frontier.

History stays sequential: shipped slices keep `status: done` for the audit
trail, and the live working set is the current frontier. This matches the
intent that history can be a linear changelog while the active plan is a
partial order.

## Consequences

- The conductor prompt shrinks: the per-loop cap and "pick the top slice"
  prose are replaced by "call the scheduler, dispatch what it returns."
  Concurrency discipline becomes code, not prompt hygiene.
- The whole incident class of resource-contention OOM/wipes becomes a
  scheduling refusal instead of a runtime crash.
- Multi-node is an extension (add a node row plus a remote dispatch path),
  not a rewrite.
- New code to own and test: cycle/dep validation, the lease registry, the
  node registry, the frontier scheduler. Backed by sqlite and the existing
  flock pattern, kept deliberately small.

## Alternatives considered

- Prose-only enrichment (add fields to YAML, document in prompts, no
  enforcement). Rejected: it repeats the exact pattern that produced the
  OOM and wipe incidents. Resource safety must fail closed in code.
- An external workflow engine (Nomad, Prefect, Temporal, Airflow).
  Rejected: heavy dependency and operational surface for a single-box (soon
  two-box) farm whose plan store plus sqlite already provide 90 percent of
  the model. The missing 10 percent is a frontier function and a lease
  table.

## Migration

1. Add `resources` to the `Slice` dataclass and parser, default empty:
   existing plans schedule unchanged.
2. Stand up the lease and node registries; route `stack_owner.sh` through
   the new lease registry behind its current interface.
3. Ship `find_frontier` and the scheduler alongside `find_next`.
4. Add the extended statuses and the failure-isolation gate.
5. Rewire the conductor to call the scheduler; retire the prose cap.
6. (Later, optional) Add the laptop as a second node and a remote dispatch
   path.

Insertion points: `scripts/lib/plan_parser.py` (Slice dataclass at line 66,
parse at line 141, `find_next` at line 220), a new `scripts/lib/scheduler.py`
and `scripts/lib/leases.py`, and `state/schema.sql` for the `leases` and
`nodes` tables. The campaign slices are in `plans/dag-scheduler/PLAN.md`.
