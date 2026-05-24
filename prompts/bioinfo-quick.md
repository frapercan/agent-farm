# bioinfo-quick

You design + run ONE experiment in `~/Thesis2/repositories/protea-reranker-lab`
(working in your ephemeral worktree, NOT touching the original). Sonnet-tier
judgment: pick the most informative next experiment given current state.

## Read first (in this order)

1. `EXPERIMENTS.md` in the lab repo (champion log + history)
2. `~/.claude/projects/-home-frapercan-Thesis/memory/loops/lab-runner/MEMORY.md`
4. `~/.claude/projects/-home-frapercan-Thesis/memory/project_v18_selective_rerank.md`
   (current champion: v18 selective, avg cafaeval 0.4562)
5. `~/.claude/projects/-home-frapercan-Thesis/memory/project_anc2vec_count_leakage.md`
   (CRITICAL leakage finding from 2026-05-05)

## Decision: what to run

You have one experiment slot. Pick exactly ONE of:

| Option | When | Cost |
|---|---|---|
| **A. Re-run champion baseline** | Before any new feature, to confirm reproducibility | 1 LightGBM run, ~15 min |
| **B. Add a new feature** | If a clear hypothesis is on the queue | 1 train + 1 eval, ~30 min |
| **C. Sweep a hyperparam** | If a current param is suspected suboptimal | 5-9 LightGBM runs, ~2h |
| **D. Lineage feature investigation** | Pending from 2026-05-04 sessions | 1 train + 1 eval, ~45 min |

Justify your choice in the summary you return. Bias toward small,
reversible experiments that close a specific question.

## Run protocol

1. Activate the lab venv: `cd <worktree> && poetry install` then `poetry shell`
2. Edit `configs/active.yaml` (NOT `default.yaml`) with the experiment's params
3. Run: `poetry run python -m lab.train --config configs/active.yaml --out runs/<exp-tag>`
4. Eval: `poetry run python -m lab.eval --run runs/<exp-tag>`
5. Compare to champion: `poetry run python -m lab.compare runs/<exp-tag> runs/champion`
6. Summary: paste Fmax delta + 1-paragraph interpretation

## Stack-ownership lock (FARM-FEAT.13)

NEVER POST /v1/datasets without going through `dispatch_with_lock` -- it is
what prevents the deploy-keeper-kills-export incident (2026-05-23 17:12, memory:
`project_deploy_keeper_paused_2026_05_23`).

Wrap every `/v1/datasets` dispatch loop:

```bash
source "$AGENT_FARM_ROOT/scripts/services/lib/dispatch_with_lock.sh"

dispatch_with_lock "$TASK_ID" "FARM-EXP.<N> <cell-label>" -- \
  bash -c 'curl -s -X POST "$PROTEA_BASE_URL/v1/datasets" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD"'
```

If `dispatch_with_lock` exits 2, a different task already owns the stack.
Stop and report to the conductor -- do NOT bypass the lock.

## Hard constraints

- NEVER run on the original `~/Thesis2/repositories/protea-reranker-lab/` —
  always use your ephemeral worktree.
- NEVER overwrite `runs/champion/` — it's frozen.
- NEVER modify `configs/default.yaml` — use `configs/active.yaml`.
- NEVER `git stash` (memory: feedback_git_stash_6x.md). To run an A/B
  on a current-branch tweak against develop without stashing, spin up
  a throwaway worktree:

  ```bash
  git -C "$REPO" worktree add /tmp/baseline-$$ origin/develop
  # Run the eval (replace EVAL_CMD with your lab invocation):
  EVAL_CMD="poetry run python -m lab.eval"
  diff <(cd "$WORKTREE" && $EVAL_CMD 2>&1) \
       <(cd /tmp/baseline-$$ && $EVAL_CMD 2>&1)
  git -C "$REPO" worktree remove -f /tmp/baseline-$$
  ```

  Hooks reject pending stashes at commit and push time.
- NEVER skip cafaeval — Fmax in lab can be misleading per the leakage
  memory; cafaeval is the contract.
- If the run takes >2h, halt and report — that means hyperparams are off
  or the dataset bloated. Don't burn compute.

## Output

Return a summary to the conductor:

```
bioinfo-quick @ <ts>
Choice: <A|B|C|D> — <one-line justification>
Run tag: <exp-tag>
Champion baseline avg Fmax: 0.4562
This run avg Fmax: 0.4XYZ
Delta: <+/-0.0XYZ>
Interpretation: <1-2 sentences>
Recommendation for next slot: <what to try next OR "stop, champion stands">
```
