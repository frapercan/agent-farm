# agent-farm

agent-farm is an autonomous multi-agent orchestration system for software
engineering work. A long-lived conductor session reads a plan store, selects
the next ready unit of work, dispatches it to a specialised agent running in
an isolated git worktree, and delivers the result as a pull request. State for
every task is recorded in a local sqlite database so a human operator has a
single place to see what is planned, what is running, and what is done.

It was built to drive a doctoral research project (PROTEA, a protein function
annotation pipeline) without paying for an always-on cron baseline: deterministic
work runs on a plain bash happy path and only escalates to an agent on failure,
while open-ended engineering and research work is handled by agents spawned on
demand. The orchestration layer itself is project-agnostic. Agents are declared
as data, so the same machinery can drive any codebase by pointing it at a
different set of repositories and prompts.

## How it works

The system is organised around three ideas: a plan store, on-demand agents, and
worktree-isolated delivery.

1. Work is described as **plan slices** in `plans/`. Each slice is a Markdown
   section with a small YAML frontmatter block (`id`, `phase`, `status`, `deps`,
   `priority`, `acceptance`, ...). Slices form a latent dependency graph through
   their `deps` field.
2. A **scheduler** (`scripts/lib/plan_parser.py`, surfaced by
   `scripts/plan-progress.sh`) walks every plan, joins it against the sqlite
   task history, and reports which slices are pickable, in flight, blocked, or
   done. `find_next` returns the highest-priority slice whose dependencies are
   all met.
3. The **conductor** picks up a slice and dispatches an agent. Implementation
   agents run inside an ephemeral git worktree created by the lifecycle hooks in
   `scripts/hooks/`, so concurrent agents never touch each other's working tree.
4. The agent completes the slice, runs local checks, and opens a **pull request**.
   The slice status moves to done once its acceptance criteria are met and the PR
   is merged.

A single unit of work therefore flows: plan slice, selected by the scheduler,
executed in a dedicated worktree, delivered as a PR.

## Layout

```
agent-farm/
├── README.md
├── agents/            # agent type registry (one YAML per agent type)
│   ├── _template.yaml
│   └── <name>.yaml
├── prompts/           # system prompt bodies (one Markdown file per agent)
│   ├── conductor.md
│   └── <name>.md
├── plans/             # canonical plan store (see plans/README.md for the schema)
│   ├── README.md      # slice schema specification
│   ├── render.py      # builds the aggregate PLAN.md index from per-loop plans
│   └── <loop>/PLAN.md # one plan file per loop (executor, doc-writer, ...)
├── scripts/
│   ├── init.sh             # initialise the sqlite state DB from schema
│   ├── spawn.sh            # spawn a headless agent
│   ├── spawn-subagent.sh   # spawn helper for conductor-driven agents
│   ├── status.sh           # tabular view of live tasks
│   ├── kill.sh             # cancel a task and clean up
│   ├── cleanup.sh          # garbage-collect stale tmux sessions and worktrees
│   ├── plan-progress.sh    # report plan status, next pickable slice
│   ├── launch-conductor.sh # boot the conductor in a tmux session
│   ├── lib/                # shared bash and python helpers (incl. plan_parser.py)
│   ├── hooks/              # git worktree lifecycle hooks
│   └── services/           # supervisor and tick loop for persistent agents
├── apps/
│   └── farm-api/      # FastAPI sidecar exposing read-only views over the state DB
├── commands/          # installable slash commands for the orchestration CLI
├── docs/              # design notes, runbooks, and a cost analysis
├── state/
│   ├── schema.sql
│   └── tasks.sqlite   # created by init.sh; gitignored
└── results/           # per-task artifacts; gitignored
```

`state/` and `results/` hold runtime data, not source, and are gitignored.

## Agents

An agent is a `prompts/<name>.md` system prompt paired with an
`agents/<name>.yaml` registration that declares its kind, model, and permission
scope. Permissions are scoped per agent, so no single agent has repo-wide blast
radius. To add a new type, copy `agents/_template.yaml` to `agents/<new>.yaml`
and write `prompts/<new>.md`.

Agents fall into three kinds:

- **Persistent services** run continuously and escalate to an agent only on
  failure (for example, keeping a development deployment healthy on its tunnel).
- **Headless one-shot jobs** dispatch and poll a long-running external batch and
  exit when it finishes.
- **Conductor-spawned agents** do open-ended cognitive work: implementing a plan
  slice and opening a PR, syncing documentation with code, reviewing UX, running
  the next research experiment in the lab, and similar tasks.

## Plan store

The plan store is the single source of truth for what the system is working on.
It lives at `plans/<loop>/PLAN.md`, one Markdown file per loop. Each `###`
section is a slice carrying a YAML frontmatter block; the full field reference
(required and optional fields, status semantics) is in `plans/README.md`.
`plans/render.py` aggregates every loop's plan into a generated `plans/PLAN.md`
index and can run as a CI gate (`render.py --check`) that fails if the index is
stale.

Every implementation spawn carries the `slice` and `phase` it is working on, so
`scripts/plan-progress.sh` can join the live sqlite task history back to the plan
and report progress without manual bookkeeping.

## Getting started

```bash
# 1. initialise the sqlite state database
bash scripts/init.sh

# 2. boot the conductor in a tmux session
bash scripts/launch-conductor.sh

# 3. attach to the session
tmux attach -t agent-farm
```

The conductor reads `prompts/conductor.md` to load its operating instructions
and runs a read-only boot diagnostic before doing anything. It does not spawn
any agent until the operator explicitly approves.

### Permission modes

The conductor's permission posture is set with `AGENT_FARM_AUTOYES` at launch:

| `AGENT_FARM_AUTOYES=` | Behaviour |
|---|---|
| `1` (default) | bypass all prompts (use only with a trusted plan store and scoped agents) |
| `accept` | auto-approve edits and safe shell commands, prompt on risky operations |
| `0` | prompt on every tool call |

Headless agents declare their own permission scope in their YAML and are
independent of this setting.

## Slash commands

The orchestration commands can be installed into a local command directory and
then invoked from any session:

```bash
bash commands/install.sh
```

| Command | Purpose |
|---|---|
| `/agent-farm-conductor` | load the conductor identity (run first) |
| `/agent-farm-agents` | list the registered agent types |
| `/agent-farm-spawn <agent> [spec]` | spawn an agent |
| `/agent-farm-status [task_id]` | show live tasks (or detail / recent history) |
| `/agent-farm-kill <task_id>` | cancel a task and clean up |
| `/agent-farm-cleanup` | garbage-collect stale tmux sessions and worktrees |
| `/agent-farm-plan [--next]` | report plan progress and the next pickable slice |

The same operations are available directly from the shell, for scripting:

```bash
bash scripts/spawn.sh <agent>
bash scripts/status.sh
bash scripts/kill.sh <task_id>
bash scripts/cleanup.sh --apply
```

## Status and scope

The plan store, scheduler, sqlite state model, worktree-isolated execution, and
PR-based delivery are in active use. A read-only FastAPI sidecar
(`apps/farm-api/`) exposes the state database for tooling. A fuller
dependency-graph scheduler (resource-aware and node-aware leasing) is designed
but not yet implemented; its rationale lives in `docs/decisions/` and its plan in
`plans/dag-scheduler/`.

## See also

- `plans/README.md`: the plan slice schema specification
- `prompts/conductor.md`: the conductor system prompt (read first if you operate
  the system manually)
- `agents/_template.yaml`: copy this to add a new agent type
- `docs/token-savings.md`: cost analysis and the levers that keep the system cheap
