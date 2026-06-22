# LAFA-LEVERS — native 0.315 -> 0.391 (and the road to thesis 10/10)

Status entry point: INT-1..INT-8 DONE. PROTEA computes the full LAFA f_micro_w
NATIVELY end-to-end in /benchmark. Native baseline (2026-06-17):

| | NK | LK | PK | MEAN |
|---|---|---|---|---|
| Native baseline | 0.414 | 0.369 | 0.163 | **0.3152** |
| Champion offline | 0.477 | 0.482 | 0.215 | 0.391 |
| KNN-v1 (#4) | 0.412 | 0.394 | 0.165 | 0.324 |

Diagnosis driving this plan: the native per-category boosters currently SUBTRACT
value (LK 0.369 < KNN 0.394), because they were trained binary, on 69 NUMERIC
features with the 4 categoricals dropped, no EMA/SWA, no late-fusion. The levers
below are not optional polish; they are what makes the reranking net-positive.

Cheap-iteration enabler: PR #640 (MERGED) content-addresses the stable-feature
table, so a classifier/booster A/B is classifier-compute-only, not an 8h
re-export. Everything here is measured on the native /benchmark on the official
7401 frame; booster/feature SELECTION happens on the held-out SELECT split
(select_cv discipline), the 7401 TEST frame is sealed once per decision.

Requirement IDs: REQUIREMENTS.md (FR-1 UI-actionable, FR-2 temporal windows,
FR-3 local LAFA-inference product, FR-4 confidence intervals, NFR-PERF/REPRO/
ARCH/UI/TEST/INFRA/DOCS/PROCESS).

---

## PHASE A — Diagnose before throwing levers (cheap, no re-export)

### A1. Feature/booster attribution ablation  [NFR-PERF]
Why is 0.315 < KNN 0.324? On the held-out SELECT split, score: (a) raw KNN
composite (no booster), (b) booster on KNN-only features, (c) +classifier,
(d) +self_prior, (e) +association, (f) +categoricals, per category. Reuse the
cached stable parquet (#640) + the existing boosters; no recompute.
Accept: a per-category attribution table showing which family/choice causes the
LK regression and whether classifier/self_prior/association are net-positive.

### A2. Objective + imbalance probe  [NFR-PERF]
On the same split, A/B binary vs lambdarank, and for PK (1.6% positives) probe
scale_pos_weight / is_unbalance. Cheap (boosters only).
Accept: ranked shortlist of the highest-leverage changes with expected deltas.

---

## PHASE B — The levers (each: train booster -> seal native, via #640 cache)

### B1. Recover the 4 categoricals  [NFR-PERF] (suspected LK culprit)
The per-category boosters take the generic apply_reranker path, which coerces
string categoricals to NaN (no categorical_codes passed). Fix one of: (i) route
per-category boosters through a categorical_codes-aware path (persist the
factorize vocabulary on the RerankerModel spec + pass at predict), or (ii) make
the export emit categoricals as stable int codes + a vocabulary the predict
reuses. Re-train, seal native.
Accept: categoricals net-positive; LK climbs above KNN 0.394. Depends: A1.

### B2. lambdarank objective  [NFR-PERF]
Re-train the 3 boosters with lambdarank + per-query groups ((protein, aspect)
candidate sets). Streaming group construction (no pandas full-load).
Accept: mean f_micro_w improves vs binary on SELECT, confirmed on TEST seal.

### B3. PK imbalance + booster hyperparameters  [NFR-PERF]
Tune PK specifically (scale_pos_weight/focal-style, min_data_in_leaf, leaves)
given 1.6% positives; sweep on SELECT.
Accept: PK climbs toward 0.215 without NK/LK regression.

### B4. EMA/SWA classifier  [NFR-PERF, NFR-REPRO]
Screen EMA/SWA vs the 7-seed Deep Ensemble at the classifier level
(screen_ensembling.py). If competitive, fold the single weight-averaged model
in via the #640 stable cache (classifier-compute-only).
Accept: equal-or-better mean with ONE model + ONE artifact (no K checkpoints) ->
serve simplification + reproducibility win; else documented as not-adopted.

### B5. Late-fusion per-PLM classifier  [NFR-PERF] (PK diversity)
Train one classifier head per PLM, average outputs (raises Krogh-Vedelsby
ambiguity vs the early-fusion concat). Screen, then fold via #640.
Accept: PK and/or mean improves; ablation shows lower inter-member correlation.

### B6. Seal converged native + FR-4 interval  [NFR-PERF, FR-4]
After B1..B5 settle, re-fit the chosen booster/classifier stack, seal the native
number once on 7401. Bound the seed-variance interval cheaply (classifier-level
variance + eval bootstrap; at most 1-2 disjoint-seed full draws).
Accept: a sealed native mean +/- interval; target >= 0.391; if short, an honest
"native #1-class" claim with the gap attributed.

---

## PHASE C — Reproducibility + architecture maturation

### C1. Commit the from-zero runbook to the lab  [NFR-REPRO]
Move storage/fullgo_models/{rebuild_seed_checkpoints,train_native_boosters,
screen_ensembling}.py into protea-reranker-lab as the canonical, documented,
parameterized reproduction pipeline (currently lives in gitignored storage/).
Accept: a third party reproduces the native number from the lab + docs alone.

### C2. Streaming refactor of lab training  [NFR-ARCH, NFR-REPRO]
Kill the to_pandas() full-load in the lab's prepare_dataset (the 56GB OOM root
cause); make booster training columnar/streaming (pyarrow batches -> LightGBM
Dataset). Keep apply_reranker (inference, small) as-is.
Accept: lab trains on 50M+ rows under RAM ceiling; no one-off scripts left.

### C3. End-to-end NFR-REPRO runbook  [NFR-REPRO]
One document: raw inputs -> embeddings -> KNN -> features -> classifier ->
boosters -> sealed score, deterministic, any-seeds-converge, full provenance.
Accept: reproducible by a third party; native==offline parity stated + checked.

### C4. Reaper lease fix  [NFR-INFRA] (the landmine)
The stale-job-reaper requeues multi-hour jobs (export/predict) as phantom
duplicates (lease starves on long GPU splits). Fix: raise/heartbeat the lease,
or exempt the long-job queues, or stamp leased_until from job events.
Accept: a multi-hour export survives with no manual lease-pinning.

---

## PHASE D — The broader thesis-10/10 fronts (from the audit)

### D1. FR-2 temporal windows  [FR-2]
Predict+eval the native stack on LAFA's rolling windows (Sep->Nov, ->Dec, ->Mar),
leakage-clean per window (boosters fit once on SELECT, sealed per window).
Accept: per-window native scores agree with LAFA, each with an interval.

### D2. Exp 9 grid + Exp 10  [FR-1, thesis]
Recover the 24-cell multi-PLM grid from minio-backup-2026-06-04 (the ONLY copy;
live MinIO has 2) -> re-register Datasets -> /benchmark -> fill thesis
06_evaluation.tex \gridna (Exp 9) and the Exp 10 \TODO (universal reranker).
Accept: no placeholders left in the evaluation chapter; numbers UI-verifiable.

### D3. FR-4 intervals to headline + UI  [FR-4, NFR-UI]
Bootstrap CIs on every reported cell, carried to /benchmark + the thesis
headline numbers + the native 0.3xx.
Accept: every reported score carries an interval, live in the UI.

### D4. NFR-UI: no dead-ends + native number surfaced  [NFR-UI]
Audit UI for dead-ends/a11y; surface the native LAFA number + provenance
(schema_sha, feature families, booster ids) + intervals; verify the prod build
(now fixed) stays green in CI.
Accept: every operation UI-actionable, no dead-ends, native number visible.

### D5. FR-3 local LAFA-inference product  [FR-3]
Single container/entrypoint: LAFA inputs -> reranked predictions with the native
#1 method (inference only, not the whole stack), runnable from docs alone.
Accept: a third party runs LAFA locally and reproduces the native scores.

### D6. v1.0 release + develop->main  [thesis, process]
Coordinated 1.0.0 of the 8 repos + reconcile PROTEA develop->main (feature-freeze
decision required). Accept: tagged v1.0, green docs, main == develop.

### D7. Zenodo + token rotation  [reference, security]
Deposit the data package (needs the 24-grid re-registered from the backup +
creds). Rotate the 3 pasted tokens (github/hf/zenodo) after publishing.
Accept: Zenodo DOI; tokens rotated.

### D8. NFR-DOCS cleanup tail  [NFR-DOCS]
Fix the flagged thesis "Hardware and Software" staleness (ESMC-300M + pgvector
mention contradicts the never-pgvector + Ankh-base/ProstT5/numpy reality);
finish the noise-free pass.
Accept: docs clean, no contradictions, secondary material marked appendix.

---

## Ordering / critical path
A1 -> A2 (diagnose) -> B1 (categoricals, the likely LK fix) -> B2/B3 (objective +
PK) -> measure; if >= KNN, proceed B4/B5 (EMA-SWA, late-fusion) -> B6 (seal +
interval). C1..C4 ride alongside B (repro + the reaper fix is urgent for any long
job). D1..D8 are the remaining 10/10 fronts, parallelizable once the native
number is competitive. NFR-PROCESS throughout: work on develop, deploy develop
via ngrok, every number UI-verifiable. NFR-PERF discipline: SELECT for selection,
seal once on TEST, converged seed-averaging (no winner's curse).
