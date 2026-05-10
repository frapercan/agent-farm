# agent-farm

Manual-orchestration agent farm. A conductor session spawns specialised Claude
Code agents (subagents, headless one-shots, headless persistents) on demand,
records their state in sqlite, and gives the human a single tabla-de-mando
to drive long-running engineering work without paying for a wall-to-wall
cron baseline.

The agent zoo is project-agnostic by construction: agents are defined as a
`prompts/<name>.md` + `agents/<name>.yaml` pair, registered via the registry
helpers in `scripts/lib/`, and dispatched by the conductor or by slash
commands. Wire any project in by writing its prompts and pointing the
agents at its repos.

## Why this exists

Always-on agentic loops (cron + Claude every 5-30 min) burn token budget
even on quiet days. Long-running deploys leave a Claude session blocked
just to babysit a healthy process. Per-project orchestrators leak credentials
between unrelated repos. agent-farm separates the three concerns:

- **bash happy-path** for any deterministic work (deploys, embeddings dispatch),
  invoking Claude only on failure
- **subagents on demand** for cognitive work (executor, doc-writer, shepherd)
  spawned by a conductor in natural language
- **per-agent permission scope** baked into each agent yaml, no global
  blast-radius

Token efficiency analysis with concrete numbers: see `docs/token-savings.md`.

## Agent zoo (current)

### Persistent services
| Agent | Kind | Model | Purpose |
|---|---|---|---|
| `deploy-keeper` | headless persistent | haiku | keep `develop` deployed on the configured tunnel; escalate to Claude only on failure |

### One-shot batch jobs (headless)
| Agent | Kind | Model | Purpose |
|---|---|---|---|
| `embeddings-runner` | headless | haiku | dispatch + poll PROTEA `/jobs` for massive embedding batches |

### Subagents (spawned by conductor via Agent tool)
| Agent | Kind | Model | Purpose |
|---|---|---|---|
| `executor` | subagent | opus | implement one master plan slice, open PR |
| `janitor` | subagent | haiku | trivial CI/PR cleanup across the repo stack |
| `shepherd` | subagent | sonnet | scan state + recommend next priorities |
| `doc-writer` | subagent | sonnet | sync docs ↔ código, write ADRs |
| `thesis-writer` | subagent | sonnet | sync LaTeX manuscript with código + experiments |
| `playwright-platform` | subagent | haiku | e2e test the platform UI live |
| `bioinfo-quick` | subagent | sonnet | choose + run next experiment in the lab repo |
| `ux-reviewer` | subagent | sonnet | audit UX of platform, prioritized findings |
| `frontend-designer` | subagent | opus | implement UX recommendations on the web app, open PR |

Add a new one: `cp agents/_template.yaml agents/<new>.yaml` + write
`prompts/<new>.md`.

## Layout

```
agent-farm/
├── README.md
├── agents/                      # type registry (one yaml per agent type)
│   ├── _template.yaml
│   └── <name>.yaml
├── prompts/                     # system prompt bodies (one per agent)
│   ├── conductor.md
│   └── <name>.md
├── scripts/
│   ├── init.sh                  # init sqlite from schema
│   ├── spawn.sh                 # spawn an agent (headless kinds)
│   ├── spawn-subagent.sh        # spawn helper for the Agent tool
│   ├── status.sh                # tabla live tasks
│   ├── kill.sh                  # cancel + cleanup
│   ├── cleanup.sh               # GC stale tmux/worktrees
│   ├── plan-progress.sh         # parse master plan + join sqlite
│   ├── launch-conductor.sh      # boot the conductor in tmux
│   ├── lib/                     # shared bash + python helpers
│   ├── hooks/                   # worktree lifecycle hooks
│   └── services/                # per-persistent-agent supervisor + tick
├── docs/
│   └── token-savings.md         # cost analysis + 5 levers
├── state/
│   ├── schema.sql
│   └── tasks.sqlite             # created by init.sh; gitignored
└── results/                     # per-task artifacts; gitignored
```

`state/` and `results/` are runtime data, not source — they are gitignored.

## Bootstrap

```bash
# 1. create sqlite
bash ~/Thesis2/agent-farm/scripts/init.sh

# 2. boot conductor — autoyes ON by default
bash ~/Thesis2/agent-farm/scripts/launch-conductor.sh

# 3. attach
tmux attach -t agent-farm
```

Inside the conductor session, paste:
```
Lee ~/Thesis2/agent-farm/prompts/conductor.md y operá como conductor.
```

### Autoyes modes (set via env var at launch)

| `AGENT_FARM_AUTOYES=` | Behavior |
|---|---|
| `1` (default) | `--dangerously-skip-permissions` — zero prompts anywhere |
| `accept` | `--permission-mode acceptEdits` — auto on edits + safe bash; prompts on `rm`, `push`, etc |
| `0` | no flag — every tool prompt asked |

To change after launch:
`tmux kill-window -t agent-farm:conductor && AGENT_FARM_AUTOYES=accept bash launch-conductor.sh`.

Headless agents (`deploy-keeper`, `embeddings-runner`) are independent of this
— they always launch with `--dangerously-skip-permissions` per their yaml
`permissions: bypassPermissions`. Only the conductor's mode (which subagents
inherit) is configurable here.

## Daily use

### From the conductor session (natural language)

Inside the conductor tmux window, just talk:

- *"spawn deploy-keeper"* → conductor calls `spawn.sh deploy-keeper`
- *"smoke test the docs"* → conductor uses the `Agent` tool with the docs prompt
- *"what's running?"* → conductor runs `status.sh`
- *"kill the bioinfo task"* → conductor finds task_id and runs `kill.sh`

### Slash commands (also work from any session)

```
/agent-farm-conductor                # load conductor identity (run first)
/agent-farm-agents                   # list agent types
/agent-farm-spawn <agent> [spec]     # spawn (headless via shell, subagent via Agent tool)
/agent-farm-status [task_id|--all]   # tabla of live (or detail / 24h history)
/agent-farm-kill <task_id>           # cancel + cleanup
/agent-farm-cleanup                  # GC stale tmux/worktrees
/agent-farm-plan [--phase N|--next]  # master plan progress + next untouched slice
```

### Plan tracking

The agent-farm is plan-aware. Point `scripts/plan-progress.sh` at your
project's canonical plan file (Markdown with `## §<N>` slice sections,
each slice having an `id` field). The script joins it with the sqlite
executor task history (via the `spawn_args.slice` convention) to show
which slices are touched, in flight, or untouched.

Convention: every `executor` spawn MUST include `slice` and `phase` in
spawn_args (the executor prompt enforces this). Example:

```bash
/agent-farm-spawn executor '{"slice":"T2B.5-per-split-loop","phase":1,"notes":"continue partials, leave test-split block for next slice"}'
```

### Direct shell (when scripting / automation)

```bash
bash ~/Thesis2/agent-farm/scripts/spawn.sh deploy-keeper
bash ~/Thesis2/agent-farm/scripts/status.sh
bash ~/Thesis2/agent-farm/scripts/kill.sh <task_id>
bash ~/Thesis2/agent-farm/scripts/cleanup.sh --apply
```

## See also

- `docs/token-savings.md` — concrete cost analysis, daily budget table,
  the 5 levers that keep this cheap
- `prompts/conductor.md` — conductor system prompt (read first if you're
  orchestrating manually)
- `agents/_template.yaml` — copy this to add a new agent type

## Quick reference card

```
SPAWN:     /agent-farm-spawn <agent> [spec]   OR    bash scripts/spawn.sh <agent>
STATUS:    /agent-farm-status                  OR    bash scripts/status.sh
KILL:      /agent-farm-kill <task_id>          OR    bash scripts/kill.sh <id>
CLEANUP:   /agent-farm-cleanup                 OR    bash scripts/cleanup.sh --apply
AGENTS:    /agent-farm-agents                  OR    ls agents/*.yaml
ATTACH:    tmux attach -t agent-farm
SUPERVISOR LOG: tmux attach -t agent-farm → Ctrl-b w → pick supervisor window
```
