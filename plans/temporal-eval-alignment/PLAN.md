# Temporal evaluation alignment (horizon-matched, leakage-free) on the platform

## Goal
Make the champion (and every future lever) measured on a frame that (a) mirrors the
227 to 230 LAFA deployment target, (b) gives an UNBIASED, low-variance validation
signal for model/threshold selection, and (c) can be stratified across the four axes
(aspect x category x length x neighbor-identity) with CIs. All via platform operations
(`generate_evaluation_set`, `load_ontology_snapshot`, `export_research_dataset`,
`run_cafa_evaluation`), never ad-hoc scripts.

## Verified mechanism (read from the code, not memory)
- `domain/category.py`: NK/LK/PK is per `(protein, candidate aspect)` from the protein's
  EXPERIMENTAL annotations in the OLD (t0) set. PK dominates at recent t0 by nature.
- `generate_evaluation_set`: eval set = delta(old t0 -> new t1). Asymmetric cross-OBO is
  ALREADY supported via `old_native_snapshot_id` / `new_native_snapshot_id` /
  `pivot_ontology_snapshot_id` (the phantom-gap fix is in the payload). `window_role` in
  {valid, test, null} (ADR D40, rolling-origin, leakage-free).
- `band_registry.py`: each band pins its t0-congruent OBO + IA. v226 -> OBO
  releases/2025-03-16 + IA IA_cafa6.tsv (t0 2025-05-03). v227 -> OBO releases/2025-07-22 +
  IA lafa IA.tsv (t0 2025-09-04). `assert_band_consistency` forces the pivot OBO + IA into
  the declared band. The infra is correct-capable; this plan is about USING it right.

## Real DB inventory (resolved 2026-06-26)
GOA annotation sets (version -> id):
- 220 `1559d9f7-195d-4892-af16-8b58f7fc9942` (stored OBO 2024-03-28)
- 226 `5e1a7285-bb85-4816-88ab-2a32f7e96dd5` (stored OBO 2026-01-23 = WRONG/too-new)
- 227 `c905dffa-a5ce-430b-b17b-503e88666adb` (stored OBO 2026-01-23 = WRONG, must be 2025-07-22)
- 230 `2394b9a1-21df-4c2b-89af-3da084318fab` (stored OBO 2026-01-23)
- transversal train set ids 160..220 all present (5-spaced).

OBO snapshots (obo_version -> id):
- 2024-03-28 `0c543b89-...`  ·  2025-07-22 `aeb07c36-17db-4b0b-a560-a68376998476`  ·
  2026-01-23 `35c3ad67-3002-47db-8f71-eeed69d22ad6`
- releases/2025-03-16 (v226 congruent) = NOT INGESTED -> GAP.

Eval sets that already exist:
- 215->220 `d5c72079-...` (window_role null, a train delta)
- 220->227 `a3be0a6d-...` (window_role=VALID) <- the biased ~15-month frame, to demote
- 227->230 `6e41eb5b-df02-4400-95c5-9cef6c9029ed` (window_role=TEST, pivot 2025-07-22 = correct)

## Phase-0 findings (measured 2026-06-26, from annotation_date + evidence breakdown)
- TEST IS SOUND. Set 230 covers 552,967 proteins (~227's 556,447; -0.6% normal UniProt
  churn). The total-count drop (4.77M vs 227's 5.88M) is IEA (electronic) churn, irrelevant
  to CAFA. EXPERIMENTAL annotations are complete and GROWING (227: 88,212 exp proteins ->
  230: 88,250). The champion frame 227->230 is valid.
- Real dates (max annotation_date): 220 ~2024-04, 226 ~2025-05, 227 ~2025-09, 230 ~2026-03.
- GAF releases are sequential (220,221,...,230); PROTEA ingested only 220/226/227/230 in this
  range. 221-225 and 228-229 exist on EBI but are NOT ingested.

## The defect to fix (horizons measured)
- TEST 227->230 = ~6 months. VALID 220->227 = ~17 months (~3x too wide). 226->227 = ~4 months
  (close but short; only 215 new proteins vs the test's 325).
- Horizon-matched validation = ~6 months ending at 227 -> t0 ~2025-03 -> GAF 225 ->
  225->227 ~6 months ~ the test horizon AND more mass. GAF 225 must be ingested (gap).
- The bias is in MODEL SELECTION (thresholds/hyperparameters tuned on a wrong-horizon task),
  not leakage.

## Plan (phases; each step is a platform job)

### Phase 0 - dates + gaps  (verification DONE, ingestion PENDING stack)
- DONE: test verified sound; real horizons measured (test ~6 months; see findings above).
1. `POST /jobs {operation: refresh_goa_release_dates}` -> populate `source_published_at`
   and confirm GAF 225's exact date (~2025-03) before ingesting.
2. `POST /jobs {operation: load_goa_annotations, payload:{gaf release 225}}` -> ingest the
   ~2025-03 GOA set (the horizon-matched validation t0). Record its set id as `SET_225`.
3. `POST /jobs {operation: load_ontology_snapshot, payload:{obo_version:"releases/2025-03-16"}}`
   -> ingest the 225/226-congruent OBO (the gap). Record snapshot id as `OBO_225`.
   (releases/2025-03-16 is on/before GAF 225's ~2025-03 date -> congruent.)
4. Optional: ingest a second ~6-month sibling cut (e.g. GAF 222 -> a 222->224-style cut) for
   AVERAGING + variance reduction. Minimum viable = 225->227 alone.

### Phase 1 - register validation band (the one code change)
- v226 is ALREADY in `band_registry.BANDS` (OBO 2025-03-16, IA IA_cafa6). No new band needed
  for the 226->227 validation cut. If intermediate GOA releases are ingested, add their
  bands here (one row each, t0-congruent OBO + IA). PR base develop.

### Phase 2 - generate the horizon-matched validation eval set (225->227, ~6 months)
`POST /jobs {operation: generate_evaluation_set, payload:{`
  `old_annotation_set_id: SET_225,            # GOA 225 (~2025-03, ingested in Phase 0)`
  `new_annotation_set_id: "c905dffa-...",     # GOA 227`
  `old_native_snapshot_id: OBO_225,            # releases/2025-03-16 (t0-congruent)`
  `new_native_snapshot_id: "aeb07c36-...",     # releases/2025-07-22 (t1-congruent)`
  `pivot_ontology_snapshot_id: OBO_225,         # scoring universe = t0 (band guard)`
  `window_role: "valid"}}`
- Register a band for v225 in `band_registry` (t0 ~2025-03, OBO releases/2025-03-16, IA the
  congruent table) so `assert_band_consistency` passes for the validation cut.
- Demote the biased frame: re-bind `a3be0a6d` (220->227) window_role -> null (keep as a
  wide-horizon diagnostic only, NEVER the selection signal).

### Phase 3 - KNN reference + predictions per cut (frozen, no leakage)
- For each cut, the donor reference = the t0 annotation set, frozen, propagated under
  OBO(t0). Generate predictions (neighborhoods) for the delta query proteins:
  - VALID 226->227: donor = GOA 226 under OBO 2025-03-16.
  - TEST 227->230: donor = GOA 227 under OBO 2025-07-22 (the existing clean frame).
- Compute MMseqs2 neighbor sequence identity for each query to its nearest t0 donor ->
  the identity axis (high>=50 / mod / twilight 20-30 / remote<20).

### Phase 4 - training data realignment
- Train data = the transversal deltas 160..220 (already exist). Two corrections:
  (a) re-label / train HORIZON-AGNOSTIC (predict the full annotation, not a fixed-width
      delta) OR re-export at the ~4-month horizon, so the reranker is not calibrated to a
      foreign horizon; (b) BALANCE PK down in training (use the quasi-infinite samples) so
      NK/LK are not starved. Each cut frozen at its t0 + OBO(t0).
- Re-export via `export_research_dataset` on the CURRENT 73-feat schema (this also unblocks
  the reranker retrain, which was blocked on the stale bench-v1-K5 export).

### Phase 5 - evaluation + selection
- `run_cafa_evaluation` per cut, band-congruent OBO/IA (the guard enforces). cafaeval is
  fixed + fast (sparse default, correctness fix).
- SELECT models/thresholds ONLY on the validation cut(s) (226->227, averaged with any
  ingested siblings; bootstrap CIs). TEST (227->230) touched once at the end.
- Stratify EVERY report by aspect x category x length x identity, CIs on deltas, PK split
  into precision vs recall.

### Phase 6 - report (the champion)
- The reported number = TEST 227->230, v227 band (OBO 2025-07-22, lafa IA), stratified,
  directly comparable to LAFA and to the 0.3745 champion. MLflow-tracked + UI-verifiable.

## Leakage + provenance discipline (transversal, every cut ta->tb)
reference/donor frozen at ta + OBO(ta); truth = delta to tb (asymmetric reconcile via
pivot=OBO(ta)); category by ta state; IA from ta's band. Each eval set records its OBO
triple + window_role + band. No future annotations in any donor pool.

## Open decisions (need the user)
1. IA discontinuity: the 226 validation band uses IA_cafa6, the 227 test band uses lafa IA.
   Absolute f_micro_w differs across bands; RELATIVE model selection still holds. Accept, or
   also score validation under the 2025-07-22 universe (breaks strict t0-congruence by ~4
   months, minor)? Recommend: accept band-native IA, select on relative deltas.
2. How many intermediate GOA releases to ingest for validation averaging (0 = 226->227 only,
   higher variance; 1-2 = low-variance averaged estimate). Recommend: ingest 1 (~2025-01)
   for a 2-cut average.
