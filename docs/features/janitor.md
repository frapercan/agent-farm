---
name: janitor
section: "1-agents"
state: working
owner: agent-farm conductor loop
source:
  - agents/janitor.yaml
  - prompts/janitor.md
runbook: docs/features/README.md
smoke: python3 -c "import yaml; yaml.safe_load(open('agents/janitor.yaml'))"
---

# janitor

Subagent that performs trivial PR + CI cleanup across the watched repo
stack (PROTEA, protea-method, protea-backends, protea-reranker-lab,
protea-runners, protea-sources, protea-contracts, plus agent-farm + thesis
when scoped). Delegated authority to merge green PRs (squash) and resolve
trivial conflicts per memory `feedback_janitor_automerge_policy`.

## Source coordinates

- `agents/janitor.yaml` (model: haiku, kind: subagent)
- `prompts/janitor.md` (scope list + auto-merge rules)

## State

working. Known issues tracked in memory: co-author slipthrough
(`feedback_claude_coauthor_slipthrough`), direct push to agent-farm/main
(`feedback_janitor_direct_push_agentfarm`), and rebase-time `git stash`
near-misses (`feedback_git_stash_6x`).

## Smoke test

```bash
python3 -c "import yaml; d = yaml.safe_load(open('agents/janitor.yaml')); print(d['name'], d['model'])"
bash scripts/spawn-subagent.sh janitor '{"task":"sweep","scope":"agent-farm"}' --dry-run
```

## Runbook

- Default scope = the 8 watched repos; `spawn_args.scope` narrows it.
- Systemic red-check carve-out: when >=3 PRs share a red check, janitor
  escalates instead of admin-overriding (memory
  `feedback_janitor_systemic_redcheck_carveout`).

## Current owner

agent-farm conductor loop. Companion server-side guard: FARM-1.1a
coauthor-guard workflow (see `coauthor-guard` feature).
