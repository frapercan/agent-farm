# Autonomous run charter

Operating contract for a multi-day unattended run of the clean thesis iteration
(the author is away). Authorized 2026-07-09. Companion to `PLAN.md`,
`SIGNAL-STORE.md` and `../thesis-pillars/PILLARS.md`.

## Why this document exists

An unattended run needs its decisions made in advance, its blast radius bounded,
and its escalation rules written down. Everything below was decided with the
author before departure; the run does not reopen these questions.

## Preconditions (met before the run starts)

The box reboots or suspends several times a day, and until now every event killed
the stack. That is fixed first, otherwise unattended compute silently stalls:

- infra containers carry `restart=unless-stopped` (self-heal across machine events);
- `cold-boot.sh` is fast and idempotent (`boot != deploy`, ~2s no-op when healthy,
  reuses the venv, never re-downloads CUDA torch, starts ngrok);
- a cron watchdog runs `cold-boot.sh --quiet` every 5 minutes under `flock`;
- infra state is recorded to `storage/infra_state/{state.json,events.log}` so a
  fresh session reads what happened instead of re-diagnosing.

## Standing decisions

| Question | Decision |
|---|---|
| 8-PLM grid (Exp 9), the deposit blocker | **Populate.** All eight canonical PLMs already have ~527k cached embeddings, so no embedding compute is needed. |
| Signal-store vs writing the thesis | **Store first.** Numbers are regenerated from the store before the manuscript is rewritten. The 0.3462 incident proved the JSONB blob drifts; a number that cannot be regenerated carries an asterisk. |
| Autonomy | Open PRs and squash-merge them when CI is green; train offline in the reranker lab; dispatch on-platform jobs via `POST /jobs`; redeploy or restart the stack. |
| Conflict or blocker | Investigate with evidence, decide, document the reasoning. Notify only when still blocked after investigation. |

## Invariants (the run may not violate these)

1. **The sealed 0.4063 (#1 in 7 of 9 cells) is immutable.** Any regenerated or new
   number is a *candidate* reported for review. Nothing auto-promotes into the thesis.
2. **Migrations are additive only.** New tables, no drops, no destructive backfills.
   The on-the-fly path stays as the cache-miss filler, so the live pipeline keeps working.
3. **A verified backup precedes any migration** (fresh `pg_dump` plus a restore check;
   `pg_restore` needs `--jobs 1`).
4. Never push to `main`/`develop` directly; never `--no-verify`; never `git stash`;
   never `poetry install --sync`; never `pkill ngrok`; never pgvector for KNN.
5. No orphan worktrees. Local CI (ruff, mypy, pytest, smell-check) green before push.
6. Every result lands with a reproducible receipt (`*_result.json` plus the script).

## The three tracks

They are sequenced by dependency, not by importance, and two of them run in
parallel because one is DB/CPU bound and the other is GPU bound.

### Track B (priority): the signal-store foundation

Per `SIGNAL-STORE.md`, one PR per step, each independently revertible:

1. Pre-flight: fresh `pg_dump` plus restore verification.
2. Schema plus additive Alembic migration: `SignalConfig`, `SignalValue`,
   `SignalGlobalArtifact` (halfvec for dense). ADR entry.
3. Producers become `compute-or-load` against the store, starting with the signals
   that actually drift (the D45 blob: `classifier_score`, `self_prior`,
   `association_*`, `IA`).
4. Backfill the 227 and 230 snapshots.
5. Dataset assembly reads from the store; one `feature_schema_sha` covers every
   signal, which closes D45.
6. **Regenerate** the 9-cell headline and the LOFO from the assembled matrix and
   compare against the sealed 0.4063. Divergence is not a failure, it is the drift
   made visible: investigate, quantify, document.
7. Register `protst_text` and `protrek_text` (section 2.1 of `SIGNAL-STORE.md`) and
   measure the text lift on the regenerated frame. This is where the BP-wall question
   gets its board-faithful answer.

### Track A (parallel, GPU): the 8-PLM grid

The grid exists to disentangle model *family* from *parameter count*. Running it
through the full reranker would confound representation with fusion, and would
inherit the D45 seam that Track B is closing. So it runs at the **retrieval level**
(kNN GO transfer over the cached, provenance-versioned embeddings), which is clean by
construction and is the sharper measurement of the thing the grid is actually about:

- matched-parameter matrix over the canonical eight (ESMC-300M/600M, ESM2-650M/3B,
  Ankh-base/large, ProtT5-XL, ProstT5-XL), pairs chosen so family and scale read
  orthogonally;
- board-faithful `f_micro_w`, 9 cells, stratified by length, category and
  neighbour identity;
- per-protein paired deltas, **Wilcoxon signed-rank** with **Holm-Bonferroni**
  correction across matrix cells;
- authored fresh against the current frame, not resurrected from the stale design doc.

A full-pipeline confirmation of the winner runs after Track B step 6.

### Track C (fills the gaps): the manuscript

- Rewrite **Pillar 4**. Its current wording ("every orthogonal lever is RED, so the
  wall is evidence-bound") is now false: ProtST dents it. The frontier claim becomes
  "evidence-bound, and here is the first crack: function-description-aligned
  representation". The sealed `#1-in-7/9` does not change, because the text signal is
  not yet in the pipeline.
- Write the three missing sections: the learned k-WTA retrieval encoder, the
  representation-science ablation, the structural GATE.
- Mechanical deposit blockers: em-dash sweep, the dangling `\cref`, reconcile each
  inconsistent value to one canonical figure, add the ADR for D40.

## Escalation

Investigate first, then decide, then document. Notify (one notification per state,
not per event) when:

- a blocker survives investigation;
- a regenerated number contradicts a sealed one and the cause is not established;
- infra is down in a way the watchdog cannot fix;
- a decision would violate an invariant above.

## What comes back

A written report per track with receipts, the candidate numbers (never promoted),
the open questions, and an honest account of what was not finished.
