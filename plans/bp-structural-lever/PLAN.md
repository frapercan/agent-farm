# BP structural lever: break the candidate-generation ceiling (loop `bp-structural-lever`)

DRAFT (uncommitted, pending user greenlight). The honest BP frontier: on the
LAFA 227->230 board PROTEA is #1 in 7/9 cells but loses LK-BP (0.440 vs TransFew
0.512 / FunBind 0.472) and PK-BP (0.218 vs 0.294 / 0.235). This loop closes that
gap at its root.

## The diagnosis it must fix (measured, not assumed)

The gap is **candidate GENERATION**, not ranking. Board-faithful recall ceiling
(predict the whole pool, IA-weighted + propagation, cafa_eval):

- **PK-BP recall ceiling = 0.319** -> even perfect ranking caps at 0.32 IA-recall;
  68% of informative BP mass is never generated. TransFew scores 0.294 -> it
  recovers BP terms outside our pool. HARD generation wall.
- **LK-BP recall ceiling = 0.739**, operating at recall 0.358 / precision 0.572.
  Mixed: ranking headroom plus some generation.
- **NK-BP we WIN** (0.337 vs 0.301/0.295): on novel proteins (no side-info) our
  learned k-WTA encoder + retrieval is SOTA. We lose only on LK/PK = proteins
  rich in side-modalities (prior GO, text, domains, structure) that TransFew/
  FunBind exploit and we underuse.

What TransFew/FunBind do that we do not: a learned GO-label encoder (text + DAG
graph) + a classifier/zero-shot head that scores the FULL label space (TransFew),
and multimodal contrastive fusion of sequence+structure+text+domains+GO (FunBind).
Both generate/score BP terms beyond a retrieval neighbourhood.

## Already built and validated (reuse ~80%)

- Two-tower sparse classifier `results/sparse_classifier/p2/two_tower.py`: protein
  d8979601 k-WTA codes x GO codes, ASL loss + soft DAG-consistency hinge,
  learned temperature, 7-seed.
- Functional GO codes (`go_sparse_codes.npz`, `go_text_emb.npz`): whitened BioBERT
  name/def k-WTA + t0 co-annotation PPMI/SVD k-WTA (glycolysis~gluconeogenesis
  25x over unrelated; beats anc2vec).
- DAG `go_parents.json`; per-cut codes `build_per_cut_codes.py` (anti-leakage);
  554K-curated training corpus.
- **Recall-ceiling proof `results/sparse_classifier/p4_recall_ceiling.json`**:
  KNN+CLF lifts the BP ceiling by +0.04..+0.07 (PK-bpo 0.470->0.537, LK-bpo
  0.767->0.823). The generator already raises the ceiling; the open question is
  whether that converts to f_micro_w.
- Meta-reranker ADR-D43 (per-category combiner) + the abandoned 0.391 design
  UNION(knn, clf, sp, assoc) pool.

## Architecture (3 components + 1 optional)

- (A) Two-tower classifier as a full-label-space CANDIDATE SOURCE: union its
  top-N into the KNN pool -> raises PK-BP ceiling 0.47->0.54 directly.
- (B) Learnable DAG label encoder: replace fixed GO codes with a GCN over
  `go_parents` (TransFew label-encoder / ProtBoost GCN-stacking mechanism) so
  rare/deep BP terms inherit neighbour signal; trained jointly (ASL + DAG-hinge
  already exist).
- (C) Fuse into the meta-reranker: clf as (i) candidate source (UNION) and (ii)
  EvidenceScorer (its score as a feature). Restores the 0.391 union pool.
- (D, optional) Structure modality: FoldSeek 3Di strings (the one FunBind
  modality we lack). After A-C convert.

## Data

Have: protein k-WTA codes (d8979601), GO codes (text + co-annotation), DAG, 554K
corpus, per-cut codes. New only for (D): FoldSeek 3Di from AFDB, fetched+cached
as a backend.

## Temporally-honest validation (the literature_infame lesson)

- Train ALWAYS in-frame on rolling-origin multi-snapshot history (v160..v225),
  never on the validation window (window-only training overfits: proven, the
  literature gate regressed LK 0.385 / PK 0.161 exactly this way).
- Per-cut codes so co-annotation never leaks future.
- Validate 225->227, test 227->230.
- Dual metric: recall ceiling (generation) AND board-faithful f_micro_w (the real
  gate). Stratify by length x category x neighbour-identity (standing norm).

## Phased plan with gates (cheap/decisive first)

- Phase 0 (cheap, decisive): union clf candidates into the pool, re-rank, score
  board-faithful. GATE: does the +0.068 PK-BP ceiling uplift convert to f_micro_w?
  If no (precision dilution) -> the neck is scoring, pivot straight to (B).
- Phase 1: learnable GCN label encoder. GATE: ceiling + Fmax up; close part of the
  TransFew gap.
- Phase 2: light cross-attention joint scoring over the unioned pool. GATE.
- Phase 3 (optional): FoldSeek structure modality. GATE.
- Phase 4: productionize - clf as candidate source + EvidenceScorer in PROTEA
  (dispatch POST /jobs, no migrations, features in the GOPrediction JSONB).

## Honest risk

A higher ceiling may not convert to Fmax if the reranker cannot separate the new
candidates (precision dilution). Phase 0 is exactly that gate: cheap, and either
confirms generation is the lever or tells us the neck is joint scoring (B/C). NK
we already win; this is for LK/PK.
