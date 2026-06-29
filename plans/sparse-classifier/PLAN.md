# Sparse functional classifier — the top-100 generator (iteration `sparse-classifier`)

The candidate generator (the DL model that produces the per-protein top-100 GO
candidates) is today the M2 `hybrid_anc2vec_m2` classifier: DENSE 6-PLM concat
input → FROZEN anc2vec-2020 (pure DAG structure) head. Both sides are the
"trivial" representation we already beat in the retrieval arm (learned k-WTA
encoder beat dense mean-pool +40%). This iteration applies that same lesson
(dense -> learned SPARSE FUNCTIONAL) to BOTH sides of the classifier.

Decision (user, 2026-06-27): go SPARSE directly (dense as a later ablation).
Standing rule: a small smoke run BEFORE every heavy operation.

## Architecture: two-tower, sparse, functional

### Protein tower (input)
- Reuse the learned champion encoder `d8979601` codes (k-WTA over ankh-base,
  already ingested as SequenceEmbedding, sparse) as the protein representation.
  NO re-embed; consistent with the retrieval arm.
- Ablation (later): vs dense ankh-base mean; vs the 6-PLM concat.

### GO-term tower (output head) — fuse CURRENT functional sources, then sparsify
DECISION (user, 2026-06-27): DROP the frozen anc2vec-2020. Two reasons: (1)
COVERAGE — it only has terms existing Oct-2020; any term created 2020->2025 has
no vector, and the 227->230 eval can annotate exactly those newer terms = blind
where it matters; (2) it is stale + structural-only. No 2020 artifact in a 2025
eval. Sources (all CURRENT, functional), complementary not alternatives:
- **Text (a)**: BioBERT (`dmis-lab/biobert-base-cased-v1.1`, cached) over
  `name + ". " + def` from the CURRENT OBO (v227/Sep-2025). 768-dim, mean-pooled,
  GPU, no network. 100% term coverage. = functional MEANING. SMOKE confirmed it
  separates related>unrelated, but raw BioBERT is anisotropic (cos compressed
  ~0.9) -> WHITEN (mean-center + norm) before k-WTA to de-anisotropize.
- **Co-annotation (b)**: term-term PPMI from the t0 (v227) corpus -> truncated
  SVD (k~256). = how terms are USED TOGETHER. t0-only (leakage-clean).
- **Structure (optional, FRESH)**: if wanted, ancestor-closure / node2vec on the
  CURRENT OBO graph (NOT the 2020 npz). Add only if it measurably helps.
- **Fuse**: L2-normalize each block, concat -> optional learned projection.
- **Sparsify (c)**: k-WTA (top-k active dims) -> sparse functional GO codes.

### SPARSE EVERYWHERE (user directive)
Every representation is k-WTA sparse, end-to-end:
- protein tower = d8979601 (already k-WTA top-128/2048);
- each GO source (BioBERT text, co-annotation SVD) individually k-WTA'd;
- fused GO code sparse;
- the MATCHING is sparse-intersection (active-dim overlap, SDR/Tanimoto style),
  NOT a dense dot product.
The only dense step is raw BioBERT/SVD BEFORE the k-WTA. The thesis form.

### Classifier (two-tower retrieval-style)
- score(protein, term) = sim(g(protein_code), GO_code(term)) in a shared sparse
  space (protein code projected into GO-code space; cosine / dot).
- Loss: ASL (asymmetric, keep — good for multi-label imbalance) + DAG-consistency
  regularizer (score(child) <= score(parent) softly).
- top-100 = top-k terms by score per protein = the candidate generator.
- 7-seed ensemble (keep; it helped stability).

## Leakage discipline (every component t0 <= v227)
- Text + anc2vec: t0-independent. Co-annotation: t0 (v227) corpus only. Labels:
  v227 experimental. Protein codes: frozen d8979601. Eval terms (227->230) never
  seen in training. Mirror the verified-clean discipline of the current 7-seed
  (trained on v227 t0 c905dffa).

## Phases — SMOKE before every heavy step

- **P0 GO text (cheap)**: extract name+def for the vocab; SMOKE = BioBERT-embed
  ~30 terms, assert related terms cos > unrelated (functional sanity); then full
  embed all vocab -> `go_text_emb.npz` (cached on disk, durable).
- **P1 GO fused+sparse rep**: build co-annotation PPMI+SVD (t0); load anc2vec;
  fuse + k-WTA -> `go_sparse_codes.npz`. SMOKE = sparsity stats + neighbor sanity
  (terms with known parent/child or same-pathway are nearest).
- **P2 classifier train**: SMOKE = train on 1 train cut, few epochs, tiny -> loss
  decreases AND top-100 recall on a held slice beats the random/freq baseline;
  then full 7-seed train on <=v227.
- **P3 generate + integrate**: generate top-100 per eval protein; compare recall
  ceiling vs the current classifier's 727k pool; wire as the classifier port
  (replace the serve classifier OR inject candidates offline).
- **P4 eval on LAFA pipeline**: retrain per-category reranker incl the new
  classifier features, re-score the 9 LAFA cells (cafaeval -prop fill -norm cafa
  -no_orphans -toi, PK -known) vs current PROTEA-reranked + leaders; target the
  lose cells (LK-CCO/LK-BPO/PK-BPO/NK-CCO). Inject into the live board if it
  gains #1 without regression.

## P5-P7 — PLATFORM PRODUCTIZATION (user directive: run complete on the platform)
After the ablation picks the best sparse classifier and P3/P4 validate it on the temporal frame,
INTEGRATE it natively into PROTEA and run the whole pipeline ON THE PLATFORM (not offline). GATED:
only integrate if the sparse generator wins temporal recall (P3) and offline LAFA score (P4) vs the
current M2 anc2vec classifier; never ship a worse generator.
- **P5 integrate**: new serve classifier class in PROTEA that loads the two-tower head ckpts +
  go_sparse_codes + d8979601 protein codes and emits per-protein top-100 candidates+scores; wire into
  the export's classifier port (apply_classifier / _mark_classifier_candidates -> add candidates) and
  the predict path. PR base develop. Smoke: a 1-pair export must produce classifier-added candidates
  with the new generator. Redeploy (standing auth, keep online, in a gap). Register artifacts in the
  artifact store (NFR-REPRO: ckpts + go_sparse_codes versioned, not /tmp).
- **P6 full platform export**: dispatch export_research_dataset on the platform with the NEW classifier
  + compute_association (CSR) + self_prior, learned encoder d8979601, train [160..227] test [230],
  k=30 -> the real platform dataset. Smoke a small band first (train [225,227]) per the standing rule.
- **P7 platform reranker + eval**: retrain the per-category reranker on the new export; score the 9
  LAFA cells via the platform/cafaeval; inject into the live board; update thesis/docs. Everything
  platform-native + reproducible.

## Aspect/category consistency (folded in)
- Keep the per-CATEGORY reranker (NK/LK/PK); per-aspect models REGRESS (CCO data
  starvation, verified). Add aspect as a FEATURE + DAG-consistent post-processing
  (isotonic up the hierarchy) for precision + consistency, not aspect-split models.

## Artifacts (durable, survive reboot — NOT /tmp)
All under `~/Thesis2/repositories/protea-reranker-lab/results/sparse_classifier/`:
go_text_emb.npz, go_cooc_svd.npz, go_sparse_codes.npz, booster/encoder ckpts,
smoke logs, comparison_9cell.json, SUMMARY.md.

## B - Per-cut temporal classifier codes (user directive 2026-06-29)

Decision (user): full-rigor temporal classifier so it scales in time with maximum
precision. Today the classifier GO codes are a single fixed artifact (t0=v227) reused
for every training cut = co-annotation leakage into earlier pairs. Fix it by making
the GO co-annotation codes PER-CUT, mirroring how the `association` feature already
threads a per-cut t0 end to end.

### Principled basis (frozen method + per-cut data)
The learned weights (the `d8979601` encoder used as the protein tower AND the
two-tower head) are "the method", FROZEN and t0-independent by the SAME convention
already accepted for the encoder (it is trained on v227 and applied to every cut).
The only genuinely t0-varying input is the co-annotation, which we rebuild per cut,
exactly like `association` reads `term_cooccurrence` keyed by the cut's t0 set.
So B = per-cut co-annotation GO codes + frozen head. (Per-cut HEAD retraining = a
further refinement "B2"; not needed for consistency with the encoder convention;
documented as a thesis footnote.)

### What is already supported
- `TwoTowerSparseClassifier(go_codes_path=...)` already accepts an explicit per-call
  codes path (the hard architectural piece is done).
- The codes builder is `f(annotation_set_id) -> go_sparse_codes.npz`; BioBERT text
  block is t0-independent and reused.
- `association` already resolves a per-cut `t0_annotation_set_id` and reads
  `term_cooccurrence WHERE annotation_set_id = cut_t0` (the template to mirror).

### Steps
1. `build_go_cooccurrence` for v225 (the only missing t0 of the 15 needed:
   160,165,170,175,180,185,190,195,200,205,211,215,220,225,227; 225 had 0 rows,
   which also left the v225-v227 association at 0). On `protea.jobs`.
2. Build 15 per-cut `go_sparse_codes` artifacts (one per t0 annotation_set), reusing
   `go_text_emb.npz`. Durable under `storage/two_tower_sparse/per_cut/`.
3. PROTEA PR (base develop): thread the per-cut t0 -> classifier GO-codes selection in
   the EXPORT path only (`ClassifierUnionSpec` -> `_union_classifier_candidates` ->
   `predict_proteins_cached`); add the codes identity to the classifier cache key;
   relax the explicit "classifier is t0-independent" contract. The LIVE predict path
   keeps the single latest artifact (production unchanged). Backward-compatible when
   the per-cut dir is unset. Local CI green before merge.
4. Re-export B with per-cut codes -> reranker with temporally honest features.

### Nested validation/refit protocol (D40 rolling-origin)
- Fase 1 SELECTION: train on snapshot_pairs v160-v165..v220-v225; HOLD OUT v225-v227
  as VALIDATION (with t0=v225 codes -> leakage-clean); pick hyperparams + levers
  (pminmax LK-bpo, per-category pool, thresholds).
- Fase 2 FINAL: with the selected config, REFIT on ALL pairs INCLUDING v225-v227
  (using each pair's own per-cut codes), then TEST only on eval.parquet (v227-v230,
  t0=v227 codes = the correct latest info). The 227-230 target is never tuned on.
- This mirrors production: predict v230 from everything known up to v227.

## Environment
- BioBERT cached: `dmis-lab/biobert-base-cased-v1.1`; transformers 4.48.1; GPU
  RTX 3060 11.5GB; OBO `protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo`; anc2vec
  `storage/fullgo_models/artifacts/anc2vec/anc2vec_2020-10.npz`; t0 annotation
  set v227 = c905dffa; lab venv for torch/transformers.
- NEVER live DB to subagents; conductor read-only OK. One heavy job at a time.
