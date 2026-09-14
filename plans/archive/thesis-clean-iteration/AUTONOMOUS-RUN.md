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
7. **Never narrate a verification you do not gate on.** A destructive step is
   `if check; then act; else report and stop; fi`. A printed check that decides nothing
   is theatre, and it makes a false rationale look verified. Before deleting anything
   not created by this run, enumerate every git repo in the tree (including `thesis/`),
   salvage uncommitted work to `storage/worktree_salvage/`, and let the check decide.
   MinIO objects are removed through the S3 API, never the filesystem.

## The three tracks

They are sequenced by dependency, not by importance, and two of them run in
parallel because one is DB/CPU bound and the other is GPU bound.

### Track B (priority): the signal-store foundation

Per `SIGNAL-STORE.md`, one PR per step, each independently revertible. Step 0 was
rewritten on 2026-07-10 once the seam was traced to code and data: **D45 is a producer
seam, not a storage seam.** The fingerprint pins family names, and the export path fills
three declared families with a well-defined `0.0` because their producers were never
wired into it. Closing it means no silent default, a degeneracy check at export, and
provenance per family. The six additive columns remain worth doing, because they let the
redundant blob go and **return ~75 GB**, but they are a separate, storage-motivated step.

0. **Close D45 (the producer seam), and separately get paid for the blob.** Six scalars
   live only in the jsonb: `classifier_score`, `self_prior_score`, `association_cross`,
   `association_total`, `classifier_present`, `association_present`. They are already
   declared in `feature_schema.py`, so the fingerprint already covers their names, yet
   `_leaf_record_builder._lafa_default_fields()` exports the classifier and
   association families as a constant `0.0` because their producers were never wired
   into the export path, and the sealed run's `comparison.json` records the consequence
   verbatim: `zero-filled in export`. The fix is a **failing** export (no silent default,
   a degeneracy check, provenance per family), not a column type. Independently:
   `go_prediction` is 101 GB over 52.2M rows whose `features` jsonb (~75 GB) has 60 keys,
   of which 54 merely duplicate typed columns on the same row, so promoting the six
   (~2.5 GB) lets the blob be dropped as a separate reviewed step, verified against the
   sealed numbers first. **Representations are not features:** dense vectors and learned codes are
   embeddings and belong in `SequenceEmbedding` keyed by `embedding_config`; ProtST and
   ProTrek therefore need no new table, they are two more embedding configs.
1. Pre-flight: fresh `pg_dump` plus restore verification. **Done 2026-07-10.**
2. Schema plus additive Alembic migration for what step 0 does not cover:
   `SignalConfig`, `SignalValue` (per-protein dense, halfvec), `SignalGlobalArtifact`
   (association matrix, IA, term bases). ADR entry.
3. Producers become `compute-or-load`; the on-the-fly path becomes a cache-miss filler.
4. Backfill the 227 and 230 snapshots.
5. Dataset assembly reads from the store; one `feature_schema_sha` covers every signal.
6. **Regenerate** the 9-cell headline and the LOFO and compare against the sealed
   0.4063. Divergence is not a failure, it is the drift made visible: quantify it.
7. Register `protst_text` and `protrek_text` as embedding configs and measure the text
   lift on the regenerated frame. This is where the BP-wall question gets its
   board-faithful answer.

### Track A (parallel, GPU): the 8-PLM grid

**A previous attempt exists and cannot be reused as a result.**
`protea-reranker-lab/farm_exp_14_grid_sweep.py` is precisely this grid (9 cells x 8 PLMs
x 3 K x 2 objectives = 432 runs) and `runs/transversal` holds 349 completed runs. It
does not populate Exp 9, for four independent reasons: it records `f`, `s` and
`f_micro` but **never `f_micro_w`**, the IA-weighted governing metric (zero files
contain it); it ran on the **v226** frame, not the canonical v227->v230; it is a
**full-pipeline reranker** grid, which confounds representation with fusion; and it is
single-seed, while the design calls for paired Wilcoxon with Holm correction. It also
never finished (`status=todo` on the prot_t5 rows of
`plans/farm-platform/artefacts/farm_exp_14_grid_log.csv`). So the empty Exp 9 table is
not an oversight: the grid was started and never scored on the right metric or frame.
**Reuse the harness (sweep driver, spec format, CSV logging) and the materialized
reference embeddings; do not reuse the numbers.**

The grid exists to disentangle model *family* from *parameter count*. Running it
through the full reranker would confound representation with fusion, and would
inherit the D45 seam that Track B is closing. So it runs at the **retrieval level**
(kNN GO transfer over the cached, provenance-versioned embeddings), which is clean by
construction and is the sharper measurement of the thing the grid is actually about.
The eight PLMs' reference embeddings are already materialized as `.npy` in
`worktrees/protea-deploy/data/ref_cache`, keyed `<embedding_config>__<annotation_set>`,
so no embedding compute is needed and postgres does not have to be read for them:

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

- **Pillar 4: done** (merged). The frontier stays evidence-bound and the thesis now
  names the first crack, function-description-aligned representation.
- **Pillar 1 needs a nuance, not a retraction.** InterPro enters the system by two
  different doors and only one of them works, which an earlier reading of this document
  got wrong. As **reranker features** it is absent: `interpro_go_mapping` and
  `interpro_annotation` both hold zero rows, so the nine `interpro_*` columns score
  0.00% gain in the sealed boosters *because they are empty*. As a **post-hoc
  InterPro2GO noisy-OR graft** it is real, validated and decisive: built from
  `interpro2go.txt` plus a small `protein2ipr.json` (7,326 of 7,401 queries carry an
  IPR, 6,121 map to GO, 8.24 BP terms per protein), with the blend weight tuned per
  (category, aspect) on the v225-v227 validation and applied to test. It contributes
  **+0.0179** and is what secures seven of nine cells (`0.3884` without it). Class E is
  therefore supported, but the thesis must say *how* it enters: as a graft, not as
  features, and it is **not yet wired to serve**. Two honest jobs follow: feed InterPro
  to the reranker as features and measure it, and close the serve gap. Note the 50 GB
  InterProScan install is unrelated to the graft, which reads two small files.
- Write the three missing sections: the learned k-WTA retrieval encoder, the
  representation-science ablation (its writeup does not exist either, see below), the
  structural GATE.
- **New, and the reader's on-ramp: "How a score is made".** A short early section that
  walks one protein and one GO term end to end, from retrieval to calibrated
  probability, and shows which evidence moved the number. The material is already
  measured: in the sealed boosters **16 of 64 features carry 95% of the gain**, led by
  `go_term_frequency` (33.45%), `anc2vec_neighbour_cos` (15.03%), `k_position` (13.58%),
  `anc2vec_query_known_maxcos` (11.19%) and `lineage_is_ancestor_of_known` (6.85%);
  alignment, the most expensive family to compute, contributes 4.28%. The per-category
  split *is* Pillar 3 seen from inside the model: PK leads with the protein's own prior
  annotations, NK and LK with term frequency and neighbour semantic coherence. Write the
  honest wrinkle too: the single largest driver is a **base-rate prior**, which is worth
  a paragraph on calibration rather than a silence.
- Mechanical deposit blockers: em-dash sweep, the dangling `\cref`, reconcile each
  inconsistent value to one canonical figure, add the ADR for D40.

### Track D (new, GPU, cheap): the crowning experiment and the missing writeup

The representation ablation swept 6 layers x {dense, k-WTA 64/128/256} x {raw, std} =
48 cells and board-confirmed six of them. The learned k-WTA head beats the best fixed
configuration by 47% and the naive last-layer-dense baseline by 61%. **But the head and
its base (`08234f06`) both sit on the LAST layer, which the ablation itself flags as the
worst base**, and a learned head was never trained anywhere else. Naive `concat(L10,L48)`
is worse than L10 alone, so multi-layer only helps if the combination is *learned*.

Arms, same recipe, same output dim, same k, at least three seeds with confidence
intervals and paired Wilcoxon plus Holm across arms: (i) L48 control, reproducing
`d8979601` to bound training noise; (ii) L10; (iii) L10 standardized; (iv) learned
scalar mix over all layers, ELMo-style; (v) learned attention pooling over tokens and
layers. The interpretability question is as valuable as the score: **does the learned
mix rediscover L10?** Extract layers in float32, never float16 (layer 38 reaches
|440,611|, which overflows and silently corrupts to Inf).

Also: `storage/layer_ablation/WRITEUP.md` is cited by `PLAN.md` as the source of a
thesis section and **does not exist**. Only the raw result JSONs do. Write it, and state
plainly that six of the 48 cells were board-confirmed, so "beats any fixed
representation" holds for the confirmed and proxy-selected configurations, not for all 48.

### Track E (after Track B step 6): the feature-necessity audit

Dense vectors and learned codes are **representations** (embeddings, keyed by
`embedding_config`, recomputed per model). The per-`(query, candidate GO)` scalars the
reranker consumes are **features**. The two were conflated, and it shows in the data:
`emb_pca_query_0..15` is a representation smuggled into the feature table, replicated
across every candidate row of a query, costing 6.2 GB where 75 MB would do, and it is
fully populated (118,609 distinct values, no zeros, no nulls) while contributing
**0.00% gain**. It is genuinely obsolete; the learned retrieval code now does its job.

Gain is a heuristic and correlated features share it, so the causal test is family-level
leave-one-out with retraining, run on the **regenerated** frame where `classifier_*` and
`association_*` are actually populated (they were zero-filled in the sealed export and
excluded from that booster; they live in a separate `clfassoc` arm). Then drop what does
not earn its place, and say in the thesis which evidence was necessary and which was
decoration.

## How the conductor works

The tracks are parallel because their bottlenecks differ: B is DB and CPU bound, A and D
are GPU bound, C and E are writing and analysis. The GPU is single, so GPU work is
serialized between A and D; everything else overlaps.

- **One subagent per unit of work, on opus, each in its own ephemeral worktree.** No
  agent is ever pointed at the live database, and no agent touches
  `repositories/PROTEA/`, which is the developer's workspace.
- **Every change lands as a PR**, squash-merged when CI is green. PROTEA-stack PRs base
  `develop`; `agent-farm` and `thesis` PRs base `main`. Never a direct push.
- **The conductor keeps the product alive.** A watchdog runs `cold-boot.sh --quiet`
  every five minutes; the fast path is a 2 second no-op when containers, API, frontend
  and ngrok are all up. Infra state and every outage land in
  `storage/infra_state/{state.json,events.log}`, which is the first thing to read after
  any context summary, before re-diagnosing anything.
- **Results are candidates, not conclusions.** Each lands with a receipt (`*_result.json`
  plus the script that made it) and is reported, never promoted.
- **Cadence.** The conductor loops: check health, advance the tracks, record, decide.
  It stops for the author only on the escalation conditions below.

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
