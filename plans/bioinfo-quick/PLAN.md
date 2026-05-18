# bioinfo-quick — Plan

Research / experimental slices for the LightGBM reranker lab + benchmark
campaigns. Lives in `protea-reranker-lab` repo (separate from PROTEA);
results land back in PROTEA via the artifact-store contract (Dataset
publish + RerankerModel import).

The lab is a filter for ideas: experiments here surface deltas that may
or may not be worth productionising in PROTEA. The bridge to executor
is via T-RES.* slices in executor/PLAN.md.

## Phase semantics

| Phase | Theme |
|---|---|
| LB | Benchmark hygiene (datasets, evaluators, ablations) |
| LR | Research initiatives (lineage, GeOKG, ensemble, DAG features) |
| LM | Method analysis (champion tracking, per-cell breakdowns) |
| LP | Plumbing (lab runtime, dataset pull, training infra) |

Hard constraints:
- Decoupled evaluators: lab Fmax (custom) is a filter; cafaeval (PROTEA)
  is the canonical metric. Disagreement is a feature, not a bug
- Reuse over recompute: never recompute KNN / features / deltas on the
  fly when an artefact already exists. Persist + reuse via Dataset rows
- `protea-method` is the inference layer; the lab does NOT re-implement
  KNN or feature compute. Pull via shim
- Run traceability: every training run writes `run.json` upfront (run_id,
  resolved hparams, git sha, artefact paths) — not at the end

## LB — Benchmark hygiene

### LB.1 — bench-v1-K5-v226-lineage dataset publish

```yaml
id: LB.1
phase: LB
loop: bioinfo-quick
status: done
deps: []
acceptance: |-
  PROTEA-side executor publishes Dataset bench-v1-K5-v226-lineage
  (13 train pairs incl v220-v226 + eval v226-v230)
  Lab pulls the Dataset and trains the v22 reranker
estimated_hours: 2
priority: P0
tags: [dataset, lineage, lafa]
note: "2026-05-18 agent reconcile: Dataset row id=3517bc8b-4562-49e0-8c67-99afc5fdc67f published to PROTEA on 2026-05-14 (13 train pairs v160-v226, eval v226-v230, 24.35M train rows, schema_sha 6d97a624b8a7). v22 booster (study_v23 lambdarank, lineage features) trained on the dataset and registered as nine v226full_lineage_<cell> RerankerModel rows via POST /v1/reranker-models/import-by-reference on 2026-05-14. LR.1 PR #18 merged 2026-05-18. Cafaeval Fmax NK+LK selective avg 0.6215 +/- 0.0014 (LB.2 multi-seed)."
```

Blockers F2C.5 (PR #402 merged) and T-RES.1 (done) resolved. v22 reranker
training completed and registered. See LR.1 PR #18 for full closure artefacts.

### LB.2 — anc2vec leakage retrofix on PROTEA-side cafaeval

```yaml
id: LB.2
phase: LB
loop: bioinfo-quick
status: done
deps: []
acceptance: |-
  Re-run cafaeval on PROTEA against the leakage-free baseline
  Numbers match the lab's avg cafaeval Fmax 0.4488
  Update project_anc2vec_count_leakage.md memory with PROTEA-side numbers
estimated_hours: 4
priority: P1
tags: [eval, anc2vec, leakage-fix]
note: "2026-05-17 janitor reconcile: multi-seed sweep (3 seeds × 6 cells) completed; selective avg cafaeval Fmax 0.6215 ± 0.0014 on v226 per memory project_lb2_leakage_fixed_champion"
```

Lab fixed the leakage 2026-05-05; PROTEA-side cafaeval reproduction was
pending and is the closing artefact.

### LB.3 — paired CI reporting per cell

```yaml
id: LB.3
phase: LB
loop: bioinfo-quick
status: done
deps: []
acceptance: |-
  Each cell × aspect reported as paired bootstrap CI vs baseline
  CSV + plot in lab outputs; consumed by thesis chapter 6
estimated_hours: 6
priority: P2
tags: [stats, ci, chapter-6]
note: "2026-05-18 agent reconcile: paired bootstrap CI (N=10000) completed; 6/6 NK+LK cells strictly positive at 95% CI on bench-v1-K5-v226-lineage. Artefact at experiments/lb3/per_cell_paired_ci.csv on lab/develop. Script: scripts/lb3_paired_ci.py. Shipped via lab PR #19 (feat/lb3-paired-ci). Memory: project_lb3_paired_ci_2026_05_18."
```

## LR — Research initiatives

### LR.1 — v22 lineage feature training

```yaml
id: LR.1
phase: LR
loop: bioinfo-quick
status: done
deps: [LB.1]
acceptance: |-
  v22 booster trained with lineage feature on bench-v1-K5-v226-lineage
  Lab Fmax delta vs baseline reported per cell × aspect
  Booster registered in PROTEA via /reranker-models/import-by-reference
estimated_hours: 8
priority: P0
tags: [research, lineage, training]
note: "2026-05-18 agent reconcile: study_v23 lambdarank booster (v6+lineage-leakfree bundle, 34 features, anc2vec/emb_pca dropped) trained on bench-v1-K5-v226-lineage. Nine v226full_lineage_<cell> RerankerModel rows registered in PROTEA (dataset_id 3517bc8b, external_source protea-reranker-lab@28d9ce0-study_v23). Per-cell lab_fmax delta CSV in experiments/lr1/lineage_delta.csv. LR.1 PR #18 merged 2026-05-18."
```

Active study completed. Reranker design: 13 train pairs (12 historical + v220-v226
new), eval window v226-v230. Nine per-cell boosters registered in PROTEA. Cafaeval
NK+LK selective avg 0.6215 +/- 0.0014 (LB.2 multi-seed sweep).

### LR.2 — GeOKG embeddings vs anc2vec

```yaml
id: LR.2
phase: LR
loop: bioinfo-quick
status: deferred
deps: [LR.1]
acceptance: |-
  GeOKG embeddings ingested as alternative GO embedding source
  Bench-v1-K5-v226-geokg Dataset trained reranker
  Per-cell delta vs anc2vec baseline reported
  Decision: GeOKG default or stay anc2vec (memo + ADR)
estimated_hours: 16
priority: P2
tags: [research, embeddings, geokg]
note: "2026-05-17 janitor reconcile: NO-GO decision per memory project_geokg_nogo_2026_05_17 (task mismatch, paywall, anc2vec load-bearing in LB.2 champion, coverage unknown); defer until preconditions met (Fmax gain >0.005 on CAFA + v226 coverage parity)"
```

Per `reference_geokg_paper.md`: hyperbolic + Euclidean GO embeddings.
Likely reduces anc2vec leakage exposure but doesn't fix dataset replication.

### LR.3 — ensemble multi-K reranker

```yaml
id: LR.3
phase: LR
loop: bioinfo-quick
status: deferred
deps: [LR.1]
acceptance: |-
  Reranker that ensembles K∈{3,5,10,20} prediction sets reports a delta
  Decision: ship in F-LAFA.3 or post-defensa
estimated_hours: 12
priority: P3
tags: [research, ensemble, post-defensa]
```

### LR.4 — k=10 v18-selective re-run with leakage-free dataset

```yaml
id: LR.4
phase: LR
loop: bioinfo-quick
status: done
deps: [LB.2]
acceptance: |-
  v18-selective reranker re-trained on the leakage-free baseline
  Per-cell delta vs leaky champion reported (likely large)
  Updated champion table in champions.md
estimated_hours: 4
priority: P2
tags: [research, v18, k10]
note: "2026-05-18: leakage-free recompute done; selective avg cafaeval Fmax 0.6215 ± 0.0014 on v226; delta vs leaky 0.4562 = +0.1653 (confounded by eval distribution shift); per-cell table in experiments/lr4/v18_selective_delta.csv; champions.md updated; PR #21 merged"
```

Memory: the v18 selective rerank champion was contaminated by anc2vec
leakage. Recompute completed 2026-05-18 on bench-v1-K5-v226-lineage
with the leakage-fixed bundle (anc2vec + emb_pca families dropped).
Selective avg cafaeval Fmax 0.6215 supersedes the legacy 0.4562 record.

## LM — Method analysis

### LM.1 — champion tracking system

```yaml
id: LM.1
phase: LM
loop: bioinfo-quick
status: done
deps: []
acceptance: |-
  champions.md per-cell × aspect; auto-updated by training scripts
  Source of truth for "what's our best per K and per aspect"
estimated_hours: 4
priority: P2
tags: [method, tracking]
note: "2026-05-18 agent reconcile: champions.md + scripts/update_champions.py + scripts/render_champions_bootstrap.py shipped via lab PR #23 (feat/lm1-champion-tracking, commit 3c735e3 on lab/develop). Auto-updater fires after each training batch in FARM-EXP.8 orchestrator."
```

### LM.2 — spec catalog + outcome registry

```yaml
id: LM.2
phase: LM
loop: bioinfo-quick
status: pending
deps: []
acceptance: |-
  spec_catalog.md lists every spec tested + outcome (ship / drop / iterate)
  New specs propose against the catalog
estimated_hours: 3
priority: P3
tags: [method, registry]
```

### LM.3 — per-aspect feature importance audit

```yaml
id: LM.3
phase: LM
loop: bioinfo-quick
status: done
deps: [LR.1]
acceptance: |-
  Per-aspect (P/F/C) feature importance table; identifies cross-aspect
  generalists vs specialists
estimated_hours: 4
priority: P3
tags: [method, interpretability]
note: "2026-05-18 agent reconcile: feature importance audit completed on v226 lineage champion; 9 aspect-stable generalist features dominate NK+LK; alignment+taxonomy families score 0 gain; PK cells lineage-dominated (motivates selective-deploy). Artefacts at experiments/lm3/feature_importance_per_aspect.csv and experiments/lm3/feature_importance_summary.md on lab/develop. Script: scripts/lm3_feature_importance.py. Shipped via lab PR #20 (feat/lm3-feature-importance, commit 766c1c2). Memory: project_lm3_feature_importance_2026_05_18."
```

## LP — Plumbing

### LP.1 — pull_dataset.py resilience

```yaml
id: LP.1
phase: LP
loop: bioinfo-quick
status: pending
deps: []
acceptance: |-
  pull_dataset retries transient MinIO/S3 errors with exponential backoff
  Resumes partial downloads
estimated_hours: 4
priority: P3
tags: [plumbing, dataset]
```

### LP.2 — training_dump_helpers shim refresh after T-CONTEXTS

```yaml
id: LP.2
phase: LP
loop: bioinfo-quick
status: done
deps: []
acceptance: |-
  Lab consumes the new KnnContext / FeatureBuildContext from protea-contracts v0.2.0
  No breakage on pull_dataset + train_reranker round trip
estimated_hours: 4
priority: P2
tags: [plumbing, contracts]
note: "shipped via lab PR #26 (2026-05-18)"
```
