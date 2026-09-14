# dag-scheduler — Plan

New campaign: turn agent-farm's scheduling from prose-driven slice picking
into a deterministic, DAG-aware, resource-constrained, node-aware
scheduler. Design rationale in `docs/decisions/D34-dag-resource-scheduler.md`.

The plan store is already a latent DAG (every slice carries `deps`, and
`plan_parser.py:find_next` already gates on deps-done). This campaign adds
what is missing: a ready frontier instead of top-1, resource leases tied to
slice metadata, a node registry, an extended status lifecycle with failure
isolation, and cycle detection. The conductor stops choosing concurrency by
prompt discipline and dispatches exactly what the scheduler returns.

The slices below themselves form a small DAG (see each `deps`), which is a
deliberate dogfood of the model this campaign builds.

## Phase semantics

| Phase | Theme | Notes |
|---|---|---|
| F-SCHED | Scheduler core | Validation, resource model, node registry, frontier scheduler, status lifecycle, conductor rewire, multi-node. |

Hard constraints (inherited from `~/Thesis2/CLAUDE.md`):

- NEVER push to main/develop directly; PR + status checks.
- NEVER `--no-verify`, `--no-gpg-sign`, force-push, or skip pre-commit hooks.
- NEVER `git stash`. Use `git restore` + commit-on-WIP-branch.
- NEVER add "Co-Authored-By: Claude" or any AI mention to commits, PRs, or
  repo prose.
- NEVER add em-dashes to ADRs / READMEs / publishable prose.
- ALWAYS run local CI (ruff + mypy + pytest) BEFORE push.
- ALWAYS check `git status -sb` before any merge/edit.

## F-SCHED — Scheduler core

### F-SCHED.1 — DAG validation + resources schema on the Slice

```yaml
id: F-SCHED.1
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: []
acceptance: |-
  Slice dataclass (scripts/lib/plan_parser.py:66) gains a `resources` field parsed from YAML frontmatter; default {} so every existing slice is unchanged
  resources schema supports exclusive: list[str] (named mutexes) and quantitative keys (ram_gb, cpu_cores, gpu, pg_consumers, minio_io) as ints
  discover_slices builds the dep graph and raises SystemExit on a cycle (with the cycle path) and on a dangling dep id (referencing a non-existent slice), the same failure style as the existing duplicate-id check
  render.py stays in lockstep (no schema drift between parser and renderer)
  pytest covers: empty resources default, a valid resources block, a cycle, a dangling dep
estimated_hours: 5
priority: P0
tags: [scheduler, schema, validation, dag]
requires_human: false
```

**Goal**: make the plan store a validated DAG that can carry resource
requests, without changing how any current slice schedules. Default-empty
`resources` is the backward-compat hinge. Cycle and dangling-dep detection
turn silent latent edges into a fail-closed parse.

### F-SCHED.2 — Lease registry (generalize stack_owner.sh)

```yaml
id: F-SCHED.2
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: []
acceptance: |-
  A lease registry (scripts/lib/leases.py or .sh) backs resource acquisition: a lease is (resource, node, amount-or-exclusive, task_id, acquired_at, ttl) in a sqlite `leases` table (state/schema.sql)
  acquire is atomic (flock or sqlite transaction) and fails closed on contention; release refuses on holder mismatch; a TTL reaper releases leases from dead tasks (reuse the existing heartbeats pattern)
  exclusive resources (stack, db-write) are capacity-1; quantitative resources subtract from a node pool
  stack_owner.sh is routed through the new registry behind its current interface (the dispatch_with_lock.sh and deploy-keeper-tick.sh callers keep working unchanged); "the stack" is modelled as one exclusive resource
  pytest covers: acquire/release roundtrip, exclusive contention, quantitative fit/no-fit, TTL reaping, stack_owner shim parity
estimated_hours: 8
priority: P0
tags: [scheduler, leases, resources, stack-owner, sqlite]
requires_human: false
```

**Goal**: one general lease registry that subsumes the single bespoke
stack mutex. This is the component that turns the OOM/wipe incident class
into a scheduling refusal. Migrate stack_owner.sh callers behind the
existing interface so nothing breaks mid-flight.

### F-SCHED.3 — Node registry (node-aware, single node today)

```yaml
id: F-SCHED.3
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: []
acceptance: |-
  A `nodes` table (state/schema.sql) holds id, capacity JSON (ram_gb, cpu_cores, gpu, pg_consumers, minio_io), status (online|offline|drain)
  The desktop is seeded as the single node with its real capacity; adding a second node is a row insert, not a code change
  A helper reports per-node free capacity = capacity minus the sum of active quantitative leases on that node
  pytest covers: seed, free-capacity computation with active leases, a second node added with no code change
estimated_hours: 4
priority: P1
tags: [scheduler, nodes, capacity, multi-node-ready]
requires_human: false
```

**Goal**: make capacity node-scoped from day one so the future laptop is
an extension, not a rework. Single node now; the schema and the
free-capacity math are already multi-node.

### F-SCHED.4 — Frontier scheduler (assignment over nodes + leases)

```yaml
id: F-SCHED.4
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: [F-SCHED.1, F-SCHED.2, F-SCHED.3]
acceptance: |-
  find_frontier(slices) returns ALL ready slices (status pending, all deps done, not requires_human, not transitively downstream of a failed/quarantined dep), distinct from the existing top-1 find_next which is kept for single-pick callers
  The scheduler walks the frontier in priority order and, per slice, tries to place it on a node whose free quantitative capacity fits and whose named mutexes are free; on fit it acquires the lease bundle atomically and emits a dispatch assignment (slice, node); on no-fit it withholds the slice
  Output is a deterministic list of (slice, node) dispatch assignments plus the leases acquired, consumable by the conductor / spawn-subagent
  A concurrency cap per agent/loop is enforceable here in code (not prose)
  pytest covers: empty frontier, multiple independent ready slices placed concurrently, a slice withheld for capacity, a slice withheld for an exclusive mutex held elsewhere, priority ordering
estimated_hours: 10
priority: P0
tags: [scheduler, frontier, assignment, concurrency, bin-packing]
requires_human: false
```

**Goal**: the heart of the campaign. Top-1 picking becomes a
resource-constrained assignment of the whole ready frontier onto available
node capacity. This is where real, safe concurrency comes from, and where
the per-agent cap finally lives in code.

### F-SCHED.5 — Extended status lifecycle + failure isolation

```yaml
id: F-SCHED.5
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: [F-SCHED.1]
acceptance: |-
  Status enum extends to pending|in_progress|in_review|blocked|done|deferred|failed|quarantined across plan_parser.py, render.py, the glyph maps, and plans/README.md
  in_review means PR open / CI running; failed means the task errored; quarantined means failed and awaiting human decision or retry
  Failure isolation: a slice with a failed/quarantined dep is withheld from the frontier (shown as blocked-by-failure), while every slice not transitively downstream of the failure keeps scheduling
  finalize-subagent.sh maps a failed task to status failed (then quarantined after N retries or on human flag)
  pytest covers: failed dep withholds only its subtree, independent slices keep flowing, in_review does not count as schedulable
estimated_hours: 6
priority: P1
tags: [scheduler, status, failure-isolation, lifecycle]
requires_human: false
```

**Goal**: a red node stalls only its own subtree, never the whole
frontier. Distinguish "awaiting merge" (in_review) from "in flight"
(in_progress), and give failures an explicit quarantine state instead of
silently blocking the catalog.

### F-SCHED.6 — Conductor rewire (prose cap to scheduler call)

```yaml
id: F-SCHED.6
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: [F-SCHED.4, F-SCHED.5]
acceptance: |-
  prompts/conductor.md and prompts/bootstrap-autowork.md replace the prose "one executor / one doc-writer in flight, pick the top slice" logic with "call the scheduler, dispatch the returned (slice, node) assignments"
  spawn-subagent.sh accepts a node assignment and a lease handle, and finalize-subagent.sh releases the lease bundle
  plan-progress.sh / a new scheduler CLI exposes find_frontier and the dispatch plan as JSON for the conductor
  The prompt is demonstrably shorter (cap discipline moved to code) and a dry-run shows the scheduler dispatching a multi-slice frontier on the single node within capacity
estimated_hours: 6
priority: P0
tags: [conductor, prompts, dispatch, integration]
requires_human: false
```

**Goal**: close the loop. The conductor becomes a thin dispatcher over the
deterministic scheduler. Concurrency and resource safety are no longer the
conductor's prompt discipline to maintain.

### F-SCHED.8 — Autonomous dispatch: pre-loaded service ApiKey + pre-declared chain authorizations

```yaml
id: F-SCHED.8
phase: F-SCHED
loop: dag-scheduler
status: pending
deps: [F-SCHED.4]
acceptance: |-
  A persistent SERVICE api-key (role operator/admin, named `farm-conductor`) is provisioned once and stored where the conductor/scheduler reads it (e.g. ~/.secrets/protea.env as PROTEA_SERVICE_APIKEY), so dispatch POST /jobs never discovers auth hot; a runbook documents minting/rotating it (the api_key SQL-bootstrap recipe) and the POST /jobs queue_name requirement
  A CHAIN is a first-class plan object: an ordered sub-DAG of dispatch steps (operation + payload + queue + resources) carrying ONE pre-declared authorization scope; the human approves the chain ONCE (a chain_authorized marker or a single one-time gate) and the scheduler then runs every step end-to-end without per-step human OK
  The INT-8 chain (build_go_cooccurrence [db-write, minio_io] -> ANALYZE -> predict_go_terms [gpu] -> run_cafa_evaluation [pg_consumers]) is encoded as the reference chain, each step carrying its resource leases
  Failure isolation applies: a failed chain step quarantines the chain (it never silently stalls the frontier); the service key is TTL-safe and never blocks
  pytest covers: chain parse + dep order, the pre-declared-auth gate (an unauthorized chain is withheld), per-step lease acquisition, a failed step quarantines the chain
estimated_hours: 7
priority: P0
tags: [scheduler, autonomy, service-key, chain-authorization, dispatch]
requires_human: false
note: "2026-06-22. Directly motivated by the INT-8 run: the GPU run was nearly lost to an unsent human Enter, auth was discovered hot (env JWT secret mismatch with the live API, a prepared api-key stuck at viewer role, a /proc secret-forge attempt correctly blocked by the safety layer), and the chain needed step-by-step human OK. A pre-loaded service key + pre-declared chain authorization make such chains run end-to-end autonomously without weakening the per-action security boundaries. See memory project_dispatch_auth_apikey_bootstrap_2026_06_22."
```

**Goal**: chains like INT-8 run end-to-end autonomously. Auth is pre-loaded (a
service key), not discovered hot; authorization is pre-declared per chain (approved
once), not requested per step. This closes the two autonomy failures from the INT-8
run: the human gate lost to an unsent Enter, and the hot auth discovery.

### F-SCHED.7 — Multi-node extension (add the laptop)

```yaml
id: F-SCHED.7
phase: F-SCHED
loop: dag-scheduler
status: deferred
deps: [F-SCHED.6]
acceptance: |-
  The laptop is registered as a second node with its real capacity
  A remote dispatch path runs an agent task on the remote node (ssh or a small node agent) with heartbeats flowing into the shared sqlite state
  The scheduler places ready slices across both nodes by fit; a node going offline drains its leases via the TTL reaper
  Verified: two independent ready slices dispatched one per node concurrently
estimated_hours: 12
priority: P2
tags: [scheduler, multi-node, remote-dispatch, laptop]
requires_human: true
note: "2026-06-22. Future per the user: 'es posible que en el futuro pongamos también el portátil a funcionar'. Deferred until the single-node scheduler (F-SCHED.1..6) is proven. requires_human: network/ssh and node bring-up are person-in-the-loop. The node registry (F-SCHED.3) is built multi-node-ready precisely so this is an extension, not a rework."
```

**Goal**: realise the node-aware design with a real second node. Kept
deferred so the single-node scheduler is proven before adding the network
surface.
