# lab-runner — Plan

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
loop: lab-runner
status: blocked
deps: []
acceptance: |-
  PROTEA-side executor publishes Dataset bench-v1-K5-v226-lineage
  (13 train pairs incl v220-v226 + eval v226-v230)
  Lab pulls the Dataset and trains the v22 reranker
estimated_hours: 2
priority: P0
tags: [dataset, lineage, lafa]
```

Blocked on executor F2C.5 / T-RES.1 prep work. v22 reranker training
cannot start without this Dataset.

### LB.2 — anc2vec leakage retrofix on PROTEA-side cafaeval

```yaml
id: LB.2
phase: LB
loop: lab-runner
status: pending
deps: []
acceptance: |-
  Re-run cafaeval on PROTEA against the leakage-free baseline
  Numbers match the lab's avg cafaeval Fmax 0.4488
  Update project_anc2vec_count_leakage.md memory with PROTEA-side numbers
estimated_hours: 4
priority: P1
tags: [eval, anc2vec, leakage-fix]
```

Lab fixed the leakage 2026-05-05; PROTEA-side cafaeval reproduction was
pending and is the closing artefact.

### LB.3 — paired CI reporting per cell

```yaml
id: LB.3
phase: LB
loop: lab-runner
status: pending
deps: []
acceptance: |-
  Each cell × aspect reported as paired bootstrap CI vs baseline
  CSV + plot in lab outputs; consumed by thesis chapter 6
estimated_hours: 6
priority: P2
tags: [stats, ci, chapter-6]
```

## LR — Research initiatives

### LR.1 — v22 lineage feature training

```yaml
id: LR.1
phase: LR
loop: lab-runner
status: blocked
deps: [LB.1]
acceptance: |-
  v22 booster trained with lineage feature on bench-v1-K5-v226-lineage
  Lab Fmax delta vs baseline reported per cell × aspect
  Booster registered in PROTEA via /reranker-models/import-by-reference
estimated_hours: 8
priority: P0
tags: [research, lineage, training]
```

Active study per memory; lab plan
`~/Thesis/loop/plans/lab-runner-20260508T203252.md` superseded by this
slice.

### LR.2 — GeOKG embeddings vs anc2vec

```yaml
id: LR.2
phase: LR
loop: lab-runner
status: pending
deps: [LR.1]
acceptance: |-
  GeOKG embeddings ingested as alternative GO embedding source
  Bench-v1-K5-v226-geokg Dataset trained reranker
  Per-cell delta vs anc2vec baseline reported
  Decision: GeOKG default or stay anc2vec (memo + ADR)
estimated_hours: 16
priority: P2
tags: [research, embeddings, geokg]
```

Per `reference_geokg_paper.md`: hyperbolic + Euclidean GO embeddings.
Likely reduces anc2vec leakage exposure but doesn't fix dataset replication.

### LR.3 — ensemble multi-K reranker

```yaml
id: LR.3
phase: LR
loop: lab-runner
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
loop: lab-runner
status: pending
deps: [LB.2]
acceptance: |-
  v18-selective reranker re-trained on the leakage-free baseline
  Per-cell delta vs leaky champion reported (likely large)
  Updated champion table in champions.md
estimated_hours: 4
priority: P2
tags: [research, v18, k10]
```

Memory: the v18 selective rerank champion was contaminated by anc2vec
leakage. Honest re-run pending.

## LM — Method analysis

### LM.1 — champion tracking system

```yaml
id: LM.1
phase: LM
loop: lab-runner
status: pending
deps: []
acceptance: |-
  champions.md per-cell × aspect; auto-updated by training scripts
  Source of truth for "what's our best per K and per aspect"
estimated_hours: 4
priority: P2
tags: [method, tracking]
```

### LM.2 — spec catalog + outcome registry

```yaml
id: LM.2
phase: LM
loop: lab-runner
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
loop: lab-runner
status: pending
deps: [LR.1]
acceptance: |-
  Per-aspect (P/F/C) feature importance table; identifies cross-aspect
  generalists vs specialists
estimated_hours: 4
priority: P3
tags: [method, interpretability]
```

## LP — Plumbing

### LP.1 — pull_dataset.py resilience

```yaml
id: LP.1
phase: LP
loop: lab-runner
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
loop: lab-runner
status: pending
deps: []
acceptance: |-
  Lab consumes the new KnnContext / FeatureBuildContext from protea-contracts v0.2.0
  No breakage on pull_dataset + train_reranker round trip
estimated_hours: 4
priority: P2
tags: [plumbing, contracts]
```
