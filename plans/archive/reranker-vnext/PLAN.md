# reranker-vNext + InterPro chain

The nonlinear lever after A-SCORE.2 closed (linear scorer exhausted: gamma dead,
evidence dead, richer features add no cells; composite near-optimal; only K per
cell + PK specialization). LightGBM reranker on KNN candidates with **InterPro as
a LEARNED feature** (NOT flat blend, which was rejected held-out). Design source of
truth: memory `project_interpro_reranker_integration_2026_06_12`.

## Current state (shepherd 2026-06-12)
- **protea-reranker-lab**: code INTACT (universal_runner + streaming LightGBM,
  staging/pooled_staging, IA-weighted LambdaMART, calibration, hierarchical
  correction, in-lab f_micro_w eval). "Empezamos de cero" = drop registered
  runs/champions, NOT the code. Reusable; needs union-candidate staging + flags.
- **InterProScan compute: DONE** on both query sets — `interproscan6/out_test7401/`
  (7401 LAFA) + `interproscan6/out_valid/` (VALID). Ran via InterProScan6 Nextflow.
  Pinned `latest`; design wants a fixed release (e.g. 107.0) for reproducibility
  (minor re-pin, deferrable).
- **InterPro->GO + eval**: `storage/interpro_run/parse_interpro_to_go.py` (interpro2go
  + true-path propagation, emits protein/GO/score) + `eval_lafa_frame.py`
  (parity-locked) both exist + validated.
- **protea-sources/interpro**: scaffold exists but emits DOMAIN hits, not
  `(protein,go_id,score)`. Needs interpro2go mapping + ORM + batch op.
- **export_research_dataset**: producer pattern via CanonicalFeatureRegistry +
  `protea/core/features/_bindings.py`; rows keyed (protein, go_id), aspect a column.
  T1.8 invariant crashes the dump if any ALL_FEATURES col lacks an unconditional producer.
- **protea-contracts**: no interpro features in ALL_FEATURES/FEATURE_FAMILIES yet.

## Slice DAG
```
S0  InterProScan-on-queries .......... DONE (optional re-pin to fixed release; defer)
S1  contracts: declare interpro_* family ──┐  (parallel, unblocked)
S2  sources: interpro->GO emission ────────┤  (parallel, unblocked)
                       ▼ (S1 + S2)
S3  PROTEA: InterPro export producer (join (protein,go_id) + union candidates + knn_present/interpro_present)
                       ▼
S4  export run: dispatch export_research_dataset w/ InterPro producer on VALID(+LAFA)   [requires_human: long]
                       ▼
S5  reranker-vNext train: union-candidate staging + missingness, LightGBM universal_runner
                       ▼
S6  held-out VALID validation: f_micro_w vs A-SCORE champion, beat-pooled-or-revert
```
Parallel: S1 ‖ S2. Linear tail: S3 -> S4 -> S5 -> S6.

| Slice | Loop | Repo | Base | requires_human |
|---|---|---|---|---|
| S1 contracts interpro family | executor | protea-contracts | main | no |
| S2 sources interpro->GO | executor | protea-sources | develop | no |
| S3 export producer | executor | PROTEA | develop | no |
| S4 export run | executor (dispatch) | PROTEA | — | yes |
| S5 reranker train | executor / bioinfo-quick | protea-reranker-lab | develop | no |
| S6 VALID validation | bioinfo-quick | protea-reranker-lab | develop | partial |

## Landmines
- **Contracts cascade (S1)**: keep `__all__` a strict superset (do NOT drop
  `axis_tuple`/`CANONICAL_AXIS_KEYS`); NO `file://` pin; minor bump only; verify
  protea-reranker-lab AND PROTEA pytest collection GREEN before merge (advisory
  auto-merge has masked breakage before).
- **T1.8 invariant (S3)**: every new `interpro_*` col needs an *unconditional*
  producer or the dump crashes at the parquet boundary after hours of compute.
- **Export OOM (S4)**: `PROTEA_EXPORT_MINIJOBS=0` for the unattended run.
- **No flat blend (S5/S6)**: InterPro enters as LEARNED features only; hold the
  beat-pooled-or-revert guard on VALID f_micro_w.
- **Release pinning (S0)**: re-pin InterProScan to a fixed release for repro (deferrable).

## First slices to execute
**S1 + S2 in parallel** (both unblocked, foundational).
- S1 gates S3->all; do the cascade landmine first and verify consumers green.
- S2 is independent: port `parse_interpro_to_go` interpro2go + propagation into the
  `protea_sources/interpro` plugin so it emits `(protein, go_id, interpro_score)`.
