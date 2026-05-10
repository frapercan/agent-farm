# Token savings — how agent-farm controls cost

5 levers, in order of impact for our workloads.

## 1. Model routing per agent (15× ceiling)

Anthropic input pricing (per Mtok):

| Model | Input $ | Output $ | Use for |
|---|---|---|---|
| Haiku 4.5 | 1 | 5 | mechanical: deploy-keeper failure recovery, embeddings dispatch + polling, playwright smoke |
| Sonnet 4.6 | 3 | 15 | judgment: bioinfo experiment selection, ux-reviewer findings |
| Opus 4.7 | 15 | 75 | creative + correctness: frontend-designer implementing UX |

Each `agents/*.yaml` declares its tier. Default to Haiku; promote only when
the agent type genuinely needs judgment. Conductor itself is Opus (it makes
the orchestration decisions) but spawns mostly Haiku/Sonnet workers.

Concrete: a single Opus turn costs roughly 15× the same turn on Haiku. A
deploy-keeper that ticks every 5 min for a day = 288 ticks. If each tick
were 5k tokens on Opus = $0.36/day. Same on Haiku via failure escalation
ONLY (≈3 escalations/day at 5k each) = $0.015/day. **24× saving** from
moving the happy path off the LLM AND down-tiering escalation.

## 2. Bash happy path + LLM only on failure (∞× on the noop case)

context on every cron tick because a Claude session ran the whole loop. v2
runs `deploy-keeper-tick.sh` (pure bash) and only invokes `claude -p` when
a tick exits non-zero.

Per-day cost on a healthy day: **$0**. On a day with 3 transient failures:
≈$0.015. A naive always-on Claude loop ticking every 5-30 min would burn
~10-30k input tokens per tick on Opus (~$0.15-0.45) × 12 ticks/day =
**$1.80-5.40/day** baseline regardless of whether anything broke.

## 3. Subagent isolation (Agent tool returns summary, not transcript)

For `kind: subagent` agents (playwright-docs, ux-reviewer, etc.) the
conductor uses the `Agent` tool with `isolation: "worktree"`. The subagent
runs in its own context window, does its work, returns a summary (≈200-2k
tokens). The conductor only ingests the summary, NOT the subagent's full
exploration.

Concrete: a `ux-reviewer` audit might consume 30k tokens internally
(screenshots, Lighthouse JSON, page reads). The conductor sees only the
≈800-token findings list. **~37× savings** on parent context.

## 4. Headless `claude -p` for long batch jobs (zero parent context burn)

For `embeddings-runner` (6h+), spawn.sh forks `claude -p` in a tmux window.
The conductor doesn't sit on the conversation while it runs — it only polls
sqlite for heartbeats. The headless instance has its own context, dies on
completion, and the conductor reads the final results row.

Concrete: 6h embedding job, ~50 LLM turns for dispatch + polling. On Haiku
≈$0.20 total. The conductor's context burn during those 6h: **0 tokens**.

## 5. Prompt caching (5-min TTL hit = 10% of input price)

Claude API caches identical prompt prefixes for 5 minutes. Each agent-farm
process has its own cache. The persistent `deploy-keeper` supervisor's
escalation prompt + system prompt is cached after the first tick, so
subsequent failure escalations within 5 min cost ~10% on the cached prefix.

This matters most for `deploy-keeper` cluster failures and for
`embeddings-runner` polling cycles (every 60s, well within TTL).

## Daily budget sanity check

Conservative estimate of full v2 running 24/7 with the full 11-agent zoo
active:

| Agent | Invocations/day | Tokens each | Tier | $/day |
|---|---|---|---|---|
| deploy-keeper (escalations only) | 3 | 5k in / 1k out | haiku | 0.02 |
| embeddings-runner | 1 (6h job) | 250k in / 50k out | haiku | 0.50 |
| playwright-platform | 5 | 12k in / 3k out | haiku | 0.08 |
| janitor | 4 | 30k in / 5k out | haiku | 0.22 |
| shepherd | 2 | 20k in / 4k out | sonnet | 0.16 |
| bioinfo-quick | 2 | 25k in / 8k out | sonnet | 0.39 |
| doc-writer | 1 | 50k in / 8k out | sonnet | 0.27 |
| thesis-writer | 1 | 60k in / 10k out | sonnet | 0.33 |
| ux-reviewer | 1 | 30k in / 5k out | sonnet | 0.17 |
| executor | 2 | 120k in / 25k out | opus | 7.35 |
| frontend-designer | 1 | 80k in / 20k out | opus | 2.70 |
| **conductor** (you) | n/a | varies | opus | 0.50-2.00 |
| **Total (active week, all agents firing)** | | | | **≈$12-15/day** |
| **Total (typical day, 3-4 agents)** | | | | **≈$3-6/day** |

≈$15-30/day with much less throughput (cron tick != real work, lots of
no-op turns). v2 same throughput at **2-3× cheaper** AND zero spend on

## Anti-patterns to avoid

- **Spawning Opus for mechanical work**. Default to Haiku in `_template.yaml`.
- **Persistent claude session for a polling loop**. Use bash supervisor +
  escalation. The pattern is `deploy-keeper-supervisor.sh` — copy it.
- **Re-reading the same files in a tight loop without caching**. Heartbeat
  to sqlite (free) instead of asking the LLM to remember.
- **Subagent that returns full exploration to parent**. Tell the subagent
  to summarize aggressively in its system prompt.
