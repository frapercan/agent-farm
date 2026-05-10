# plans/

Canonical plan store for agent-farm. The conductor and executor agents
read these files to decide the next slice; humans read them to know what
the system is working on. Every plan is human-readable Markdown with
machine-parseable YAML frontmatter on each slice.

## Layout

```
plans/
├── README.md             # this file (the schema spec)
├── PLAN.md               # AUTO-GENERATED master index — do not edit by hand
├── render.py             # build PLAN.md from per-loop plans
├── executor/PLAN.md      # technical implementation slices (PROTEA + LAFA)
├── lab-runner/PLAN.md    # research / experiment slices
├── doc-writer/PLAN.md    # docs initiatives (Sphinx, ADRs, runbooks)
└── thesis-writer/PLAN.md # LaTeX manuscript chapter slices
```

Slices are owned by exactly one loop (the `loop` field in the frontmatter
must match the directory name). Cross-loop dependencies are expressed via
the `deps` field referencing slice ids.

## Slice schema

Each slice is a `###` Markdown subsection inside its loop's `PLAN.md`,
preceded by a YAML frontmatter block:

````markdown
### T2D.3 — services LOC cleanup

```yaml
id: T2D.3
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  scoring_service.py <500 LOC
  embeddings_service.py <500 LOC
  router tests green without changes
estimated_hours: 6
priority: P1
tags: [refactor, smell-budget]
```

Free-form Markdown body. Explain the why, hints, references to files,
links to ADRs, anything an agent or human needs to do the slice well.
````

### Required fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | unique across the whole plan store; convention `<area>.<n>` (e.g. `T2D.3`, `F-LAFA.7`) |
| `phase` | string | grouping bucket; per-loop convention (e.g. executor uses `F1`-`F8`) |
| `loop` | string | must match directory name (`executor`, `lab-runner`, `doc-writer`, `thesis-writer`) |
| `status` | enum | `pending` / `in_progress` / `blocked` / `done` / `deferred` |
| `acceptance` | string (multiline) | binary criteria; reviewer flips to `done` when met |

### Optional fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `deps` | list[string] | `[]` | other slice ids that must reach `done` before this one starts |
| `estimated_hours` | int | omit | rough sizing for capacity planning |
| `priority` | enum | `P2` | `P0` (blocker) / `P1` (high) / `P2` (normal) / `P3` (when free) |
| `tags` | list[string] | `[]` | free-form labels (`refactor`, `experiment`, `chapter-6`, `requires-human`) |
| `requires_human` | bool | `false` | true if cannot be done autonomously (DB migrations, security, decisions) |
| `superseded_by` | string | omit | id of the slice that replaces this one (still keep status here for history) |

## Status semantics

- **pending**: not started; eligible for an agent to pick (subject to `deps`)
- **in_progress**: an agent task is in flight; check sqlite for `task_id`
- **blocked**: started but stuck on external input (review, deploy window, decision)
- **done**: acceptance criteria met; PR merged or artefact delivered
- **deferred**: scope-out for the current planning horizon (e.g. post-defensa)

## Conventions

- **One slice per `###` heading** with a unique `id` in its frontmatter
- **Phase buckets** are loop-specific and serve as ordering scaffolding;
  see each loop's PLAN.md preamble for that loop's phase semantics
- **Don't edit `PLAN.md`** at the root — it's regenerated from the per-loop plans by `render.py`
- **History stays**: when a slice ships, set `status: done` and leave the body
  in place; the master index hides done slices but the audit trail survives
- **Renames**: if a slice is renamed (e.g. shapeshift), keep the old id with
  `superseded_by: <new-id>`. Don't rewrite history

## Picking the next slice (executor convention)

The executor's spawn arg `slice` MUST match an `id` from
`plans/executor/PLAN.md` whose `status` is `pending` and whose `deps` are
all `done`. The conductor consults `scripts/plan-progress.sh` (or
`render.py --next` once implemented) to decide.

If no such slice exists, the conductor should escalate to the user with
a recommendation (block on a `requires_human`, deferred backlog, or
new-slice-needed).
