# Plan: surpass #1 on LAFA (f_micro_w), honest + product-integrated

## 1. Honest situation (2026-06-21)

- Native productized number: **0.3745** (NK 0.4645 / LK 0.4526 / PK 0.2065), UI-verifiable
  on /benchmark, frame=lafa, official harness (TOI + PK-known exclusion). #1-class on NK.
- We have NOT surpassed #1: TransFew ~0.381, our sealed offline champion 0.391 (the champion
  is #1 on this frame but carries frame optimism + its source files are deleted).
- Easy levers are exhausted: self_prior (+0.0063), IA (+0.0033), scale_pos_weight calibration
  (+0.0023) all banked; the curated-feature representation was refuted (clean-15 0.3660 < 0.3722);
  the first new-signal scorer (descendant-of-known DAG prior) was refuted on validation (-0.0072).
- **The bottleneck is PK precision, and it is the field's open problem.** At PK's Fmax operating
  point: recall ~0.25, precision ~0.15, coverage 1.0. NOT a candidate-pool/recall ceiling -> the
  pool has plenty of candidates; PK ranks too many plausible-but-FALSE terms high. The CAFA5
  assessment paper names previously-known / partial-knowledge as the hardest, least-optimized,
  open-innovation category. So PK is where the leaderboard is won, and it needs a DISCRIMINATIVE
  signal (separate true from plausible-false), not another plausibility prior.

## 2. Bibliography (grounding)

- **ProtBoost** (CAFA5 #2, arXiv:2412.04529): Py-Boost + CondProbMod + GCN-stacking. Ablation
  (their CAFA-Fmax frame, directional only): Ridge/ProtT5 0.47 -> +Py-Boost+CondProbMod 0.51 ->
  +taxon 0.53 -> +CondProbMod-blend 0.55 -> +GOA-electronic 0.57 -> +NN-ensemble 0.59 ->
  +GCN-stack-all 0.62. Biggest single levers: **CondProbMod (+0.04)**, **GCN stacking (+0.03)**.
- **GOCurator** (CAFA5 #1, Fudan): diverse ensemble (text mining + PLM + structure + GORetriever
  GO<->protein matcher), many models combined. Diversity is the lever.
- **GORetriever / ProtNote**: GO-definition-text cross-encoder rerank. Gains concentrated on
  low-homology proteins; depends on protein literature/name text (leaky/dead on novel proteins;
  legitimate only on PK where literature exists).
- **TransFew** (the LAFA #1 we chase): ESM2 + BioBert GO-text + GCN GO-graph autoencoder via
  cross-attention; its edge is RARE GO terms via label representations + frequency-group experts.
- **DeepGO-SE**: axiom-constrained "possible-world" ensemble; cross-model agreement = consistency
  filter. **GOBoost**: head/tail (frequent/rare) term split ensemble. **Obozinski 2008 (guardrail):
  naive Max/And/Or consistency enforcement LOWERS precision; use isotonic / KL-projection if ever
  enforcing hard consistency.**

Caveat on every number above: reported on different frames/metrics (CAFA organism-weighted Fmax,
not our LAFA f_micro_w). Treat as DIRECTION, not transferable deltas.

## 3. Product integration — the meta-reranker (ADR-D43)

Each lever plugs into the stacked meta-reranker as ONE EvidenceScorer (a port) or a
post-processing step over the score frame, no refactor of candidate retrieval or other scorers
(MR invariant #1). The per-category LightGBM booster is the Combiner. Calibration is first-class.
Everything keyed on go_id STRING, leakage-audited against t0. Surfaced in the UI per-component
(FR-1). This keeps the project expandable: a new lever = one scorer + one combiner column.

## 4. Prioritized levers (by EV for the PK-precision bottleneck)

### TIER 1 — highest mechanism-match, leakage-clean, reuse existing data

- **L6 Retrieved hard-negatives** (NEW, highest EV). For each candidate term t, derive features
  from the KNN neighbors that ARE annotated in t's aspect but DO NOT carry t: fraction of top-k
  same-aspect-annotated neighbors lacking t; sim-margin between supporting vs non-supporting
  neighbors. A candidate "plausible by association" whose well-annotated similar proteins
  systematically lack it is exactly a false positive to down-rank. Sources: ProtEx, GOBeacon
  (InfoNCE). Integration: new GBM features from the EXISTING KNN neighbor set (no new model/data).
  PK EV HIGH (direct answer to our diagnosis). Leakage-clean (t0 neighbors). NOT our association
  (that is pure plausibility; this is the negative evidence it structurally cannot see).

- **L1 CondProbMod** (lever F in our backlog; HIGH EV). EXACT mechanism from ProtBoost 4.3 (3 parts):
  (1) TRAINING change: exclude (protein, term) pairs where ALL GO-parents are zero from the loss
  (NA them) -> the model learns P(term | parents non-zero), conditional not marginal. (2) POST-PROC
  recompute, recursive from root: `P_mod(N) = P_model(N) * (1 - prod_{P in parents}(1 - P_mod(P)))`
  (a 2nd less-used variant: `P_mod(N) = P_model(N) * prod_parents(P_mod(P))`). (3) THE GAIN IS THE
  ENSEMBLE of the modified model with the original (ProtBoost: "main use is to ensemble"). So L1 is
  a training-variant + post-proc + ensemble, NOT just a post-proc -> bigger build than first scoped.
  ProtBoost ablation 0.47->0.51. Integration: a CondProbMod-trained booster + its post-proc score,
  fed alongside the marginal booster as decorrelated combiner inputs. PK EV HIGH (discriminative
  anti-plausible-false; targets precision). Distinct from refuted descendant-prior (suppression op,
  not a plausibility prior). IMPL NOTE: the post-proc interacts with cafaeval prop=fill (fill re-max-
  propagates ancestors); de-risk must control prop order + sanity-check baseline reproduces 0.3720.

### TIER 2 — cheap post-proc / feature trio (bank in one loop)

- **L3 Per-category low-prob clipping**: zero predictions below a per-aspect threshold before the
  Fmax sweep; PK threshold higher. Prunes the false-positive tail killing PK precision. Trivial A/B.
- **L2 Averaged soft Pmin/Pmax propagation** (EXACT from ProtBoost 4.5/Fig.4): `Pmin(N) =
  min(Pmin(k): k in Parents(N))*0.7 + P(N)*0.3` (recursive root->leaf); `Pmax(N) = max(Pmax(m):
  m in Children(N))*0.7 + P(N)*0.3` (recursive leaf->root); `P_post(N) = (Pmin(N)+Pmax(N))/2`.
  Soft parent>=child without hard collapse. NOTE: this REPLACES CAFA fill-propagation -> de-risk
  must score the soft-propagated frame with prop=no (not prop=fill), compared to the prop=fill
  baseline; sanity-check the baseline reproduces 0.3720 first. Cleanest exact-formula post-proc to
  pilot the post-processing + DAG pipeline. MED EV (insurance) but lowest-risk first execution.
- **L4 Candidate annotation-frequency bucket as a GBM feature**: log-annotation-count / freq-group
  id per candidate term, so the booster can apply a rare-term-specific precision regime (TransFew
  freq-group experts; GOBoost head/tail). Correlated with our IA but not identical (IA=depth-info,
  this=raw count); add and let LightGBM decide. MED-HIGH for PK (novel PK terms are rare/deep).

### TIER 3 — bigger build / caveated

- **L5 GCN stacker over the score vector with GO-DAG message passing** (the MR endgame). Node =
  {our base scores + small <=8-dim GO embedding}; shallow GCN passes messages over the DAG so a
  term's score sees neighbor consistency. ProtBoost's biggest jump (0.59->0.62). MED-HIGH EV
  (neighbor-consistency = precision), but highest effort + the v6 overfit trap -> tiny embedding,
  regularize hard. This is GCN as a STACKER over scores (different object than our refuted GCN
  label-embedding).
- **L7 GO-definition text cross-encoder, PK-ONLY**: PubMedBERT/E5 score (GO def text) vs (protein
  literature/name). LOW-MED EV, heavy text dependency + leakage-audit burden; legitimate only on
  PK (literature exists for known proteins), NK-unsafe. Prototype small on the PK split only.

### DO-NOT (refuted/redundant; explicit)

multi-PLM concat (have it); SVD/GCN/BioBERT LABEL-embeddings (refuted); IEA as features
(prototyped -> negligible; at most a single re-test as a raw per-pair feature, not a project);
literature TF-IDF (NK-unsafe); hard Max/And/Or reconciliation (Obozinski: lowers precision);
structural/BLAST/Foldseek (user-vetoed); descendant-of-known DAG prior (refuted -0.0072).

## 5. Sequencing (each de-risked on VALIDATION 220->227 before the TEST cycle)

1. **L6 hard-negatives + L1 CondProbMod** — the two highest mechanism-match PK-precision levers,
   both leakage-clean and reuse existing data. Build each as an overlay/post-proc, de-risk on
   validation PK vs both=0.3720, only TEST-cycle the ones that clear it.
2. **L3 + L2 + L4** — cheap post-proc/feature trio, banked in one validation loop; tune per-category.
3. **L5 GCN stacker** — the meta-reranker endgame; only after T1 lands, tiny GO embedding.
4. **L7 PK-only text** — prototype on the PK split with a strict t0 leakage audit before committing.

## 6. Honest expectations

- No single lever is promised to surpass #1; the bibliography says it takes a STACK (ProtBoost
  climbed 0.47->0.62 across 7 components). Realistic path to >0.381/0.391 = 2-3 of L6/L1/L4/L5
  stacking, with PK precision as the target.
- Every external gain is frame-relative; our only truth is the on-platform validation->TEST cycle.
- The methodology is proven for FEATURE levers: de-risk on validation first (it caught the
  descendant prior at -0.0072). BUT CRITICAL LESSON (2026-06-21, L2): for POST-PROCESSING levers
  that interact with the eval recipe's propagation + PK-known exclusion, the optimistic validation
  recipe (no-TOI, no-PK-exclude) MISLEADS. L2 soft-prop showed PK +0.0141 on the optimistic
  validation recipe but PK -0.0126 on the official TEST recipe (TOI + PK-exclude) -- a full
  reversal. Feature levers (self_prior/IA/S2) transfer because their VALUE does not interact with
  the recipe; post-proc levers DO. => de-risk every post-proc lever (L1 CondProbMod, L3 clipping,
  L2) on the OFFICIAL recipe (TOI + PK-exclude), not the optimistic one. L2 is net -0.0026 on
  official TEST (helps NK/LK +0.0012/+0.0034, hurts PK -0.0126); kept in-platform as opt-in
  (useful NK/LK-only ~0.3761 projected). 0.3745 remains the best confirmed TEST.
- Each shipped lever is productized (a scorer port, UI-surfaced, reproducible), so the thesis
  narrative stays "honest, on-platform, expandable" even for levers that don't pan out.

## Provenance
Bibliography: ProtBoost arXiv:2412.04529; GORetriever PMC11520413; TransFew PMC11374024;
DeepGO-SE Nature MI s42256-024-00795-w; ProtNote PMC12054973; Obozinski Genome Biol 2008
PMC2447540; GOBoost btaf267; CAFA5 advances biorxiv 2026.04.27.716980; CAFA5 Kaggle writeups
(GOCurator #1, ProtBoost #2). Cross-referenced against PROTEA's refuted-levers memory.
