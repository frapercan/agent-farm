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

### GO-term tower (output head) — fuse 3 COMPLEMENTARY sources, then sparsify
The sources are complementary (different facets), not alternatives:
- **Text (a)**: BioBERT (`dmis-lab/biobert-base-cased-v1.1`, cached) over
  `name + ". " + def` from the OBO. 768-dim, mean-pooled, GPU, no network.
  100% term coverage (48,165 defs in go-basic). = functional MEANING.
- **Co-annotation (b)**: term-term PPMI from the t0 (v227) annotation corpus ->
  truncated SVD (k~256). = how terms are USED TOGETHER. Built from the
  cooccurrence CSR infra (PROTEA_ASSOCIATION_CSR path), t0-only (leakage-clean).
- **Structure (c0)**: anc2vec (DAG ancestors). Keep as ONE component (structure
  is useful, just not sufficient alone).
- **Fuse**: L2-normalize each block, concat -> optional learned projection.
- **Sparsify (c)**: k-WTA (top-k active dims) -> sparse functional GO codes.
  The thesis form (sparse.pdf). This is the novel contribution.

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

## Aspect/category consistency (folded in)
- Keep the per-CATEGORY reranker (NK/LK/PK); per-aspect models REGRESS (CCO data
  starvation, verified). Add aspect as a FEATURE + DAG-consistent post-processing
  (isotonic up the hierarchy) for precision + consistency, not aspect-split models.

## Artifacts (durable, survive reboot — NOT /tmp)
All under `~/Thesis2/repositories/protea-reranker-lab/results/sparse_classifier/`:
go_text_emb.npz, go_cooc_svd.npz, go_sparse_codes.npz, booster/encoder ckpts,
smoke logs, comparison_9cell.json, SUMMARY.md.

## Environment
- BioBERT cached: `dmis-lab/biobert-base-cased-v1.1`; transformers 4.48.1; GPU
  RTX 3060 11.5GB; OBO `protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo`; anc2vec
  `storage/fullgo_models/artifacts/anc2vec/anc2vec_2020-10.npz`; t0 annotation
  set v227 = c905dffa; lab venv for torch/transformers.
- NEVER live DB to subagents; conductor read-only OK. One heavy job at a time.
