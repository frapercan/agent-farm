# Serve-offline reconciliation: deliver the validated pipeline to the live product

The board #1-in-7/9 is the OFFLINE pipeline (d8979601 k-WTA retrieval + the validated
reranker). The LIVE product serves something else. Close the gap. See memory
project_serve_offline_drift_2026_06_30.

## Verified drift (backup protea-2026-06-30.dump, read-only)
- RETRIEVAL: `d8979601` is family `learned-code`, param_count NULL -> `/annotate`
  (`ORDER BY param_count ASC NULLS LAST`, EXISTS on sequence_embedding) never picks it ->
  serves a DENSE PLM. Generic predict_go_terms is payload-driven. Offline board uses d8979601.
- RERANKER: 70 reranker_model rows, ALL feature_schema_sha `7fcecf26`, embedding_config_id NULL.
  Latest-by-created_at (what /annotate serves) = 2026-06-22 trio 20c90bf6/15bd5cfd/78fb3f92.
  Parity S2 trio 198baf99/68f3232c/f0669e41 = 2026-06-21, also 7fcecf26. There is NO is_active flag.
- SCHEMA: offline champion (clean_227230) = `775611822dd9`, NOT registered (no DB model has it).
  3-way mismatch (registered 7fcecf26 / offline 775611822dd9 / live-computed ~73-feat) -> serve-time
  schema guard likely FAILS the booster -> KNN-only served. Reranker is a de-facto serve no-op.
- D45 (ADR, Open): JSONB blob families (classifier/self_prior/association/IA) outside feature_schema_sha
  -> value skew passes the guard silently (the 0.3462 incident).

## Stages (gated, product stays online)
- S0 VERIFY (done): the drift above, from the backup.
- S1 SCHEMA ALIGN: compute the current live feature_schema_sha (from protea-contracts + the live
  feature producers); decide the canonical schema; reconcile vs offline 775611822dd9 and registered
  7fcecf26. Output: the exact schema the serving booster must carry.
- S2 RETRAIN + REGISTER the validated reranker ON the canonical live schema, over d8979601 candidates
  (the offline champion recipe), and register as RerankerModel(s) with the correct sha. Add an
  `is_active` (or explicit pin) selector. Board-faithful 9-cell must match the offline champion.
- S3 PIN SERVING: make /annotate (and the deployed parity payload) use d8979601 retrieval + the active
  reranker, not the param_count auto-select / latest-by-created_at. PR base develop; local CI green.
- S4 D45 GUARD: implement the blob-feature provenance/value check so train/serve value skew fails loudly.
- S5 REDEPLOY (standing auth, keep online) + verify the LIVE path serves d8979601 + the validated
  reranker, board-faithful, reaching the offline parity (~0.39 sealed target; PK the bottleneck).

## Gates
Nothing is served as "the method" until the LIVE board-faithful 9-cell matches the offline champion.
Each stage board-faithful; no silent regressions. The product stays online throughout.
