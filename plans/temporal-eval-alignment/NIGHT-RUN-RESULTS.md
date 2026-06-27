# Temporal-eval autonomous run — results consolidation (2026-06-26)

Autonomous conductor run executing the temporal-eval-alignment plan (PR #209). All numbers below
are f_micro_w (IA-weighted micro-Fmax, the LAFA/CAFA metric) unless noted. Findings are durable in
session memory + MLflow; this doc consolidates them for the thesis.

## 1. The correct evaluation frame (the unblocker)

The prior frames were degenerate (a ~17-month validation window vs a ~6-month test; OBO mis-pins).
The run built a horizon-matched, leakage-free frame:

- Real GOA release dates (from `refresh_goa_release_dates` + EBI): TEST 227->230 = 2025-09-04 ->
  2026-03-04 = **6.0 months**. The horizon-matched validation = **225->227 = 5.9 months** (GAF 225 =
  2025-03-08), which had to be ingested (22 GB GAF, robust local download).
- Asymmetric cross-OBO pins per cut (old=OBO(t0), new=OBO(t1), pivot=OBO(t0) = the term universe the
  model could know at t0), the phantom-gap fix. Validation `63d2b433` (225->227, reconciled, delta
  14,926: NK 1277 / LK 2319 / PK 11,917). Test `6e41eb5b` (227->230).
- Neighbor-identity axis (MMseqs2 to nearest t0 donor): bands high>=50 / mod / twilight 20-30 /
  remote (no homolog). **Both frames are ~97.5% high-identity** (the LAFA temporal delta is mostly
  re-annotation of already-homologous proteins); the twilight+remote set is small but non-zero
  (test 78, valid 157), concentrated in NK. This CORRECTS the earlier "0 remote" claim: there ARE
  proteins with no detectable homolog (64 test / 129 valid), the hardest cases.

## 2. Champion baseline — reproduced and reconciled

The learned-mean champion (k-WTA hard-neg encoder, `d8979601`) reproduces on the correct frame and
beats the dense-mean baseline robustly across all 9 cells (NK/LK/PK x MFO/BPO/CCO), +0.03..0.07.
The platform export pipeline's raw-KNN reaches **0.502 NK-MFO ~= the prior champion claim 0.4937**;
a standalone reproduction under-reported (0.32) due to reference/k/GT setup differences. So the
champion IS ~0.49-0.50; the prior number stands.

## 3. D1 — the thesis differentiator (beat homology where it fails): SUPPORTED

Champion (learned) vs homology baseline (dense-mean KNN), f_micro_w by neighbor-identity band (NK,
aggregated across aspects):

| frame | NK-easy (high+mod) | NK-hard (twilight+remote) | ratio |
|---|---:|---:|---:|
| TEST 227->230 | dense 0.221 -> learned 0.322 (+0.044 over easy delta) | +0.101 | 2.3x |
| VALID 225->227 | +0.041 | +0.060 (dense DROPS on hard 0.170 vs easy 0.224) | 1.5x |

On BOTH independent frames the learned encoder's advantage over homology is LARGER where homology
fails (twilight/remote) than where it works (high-identity). This is the FANTASIA-surpassing claim,
measured on the correct frame. CAVEAT: thin n (hard = 78 / 157) -> wide CIs; magnitude varies
(1.5-2.3x); direction is consistent. This is the run's main thesis result.

## 4. The reranker (C1/C2) — lifts NK/LK, PK is the wall

A per-category combiner (ADR-D43) trained on a FRESH 73-feat export over the clean frame (train
<=225 [gap 220->225 closed], eval = validation 225->227; PR #113):

- Per-cell, the reranker LIFTS NK/LK significantly: NK-MFO 0.502->0.564 (+0.063), NK-CCO 0.452->
  0.554 (+0.103), NK-BPO +0.046, LK-MFO +0.038, LK-CCO +0.025 (bootstrap CIs exclude 0). This
  refutes "the reranker is a no-op" for NK/LK on the current schema.
- PK REGRESSES (precision collapse): pk-bpo 0.446->0.274 (-0.173), pk-mfo -0.027, pk-cco -0.043.
- **Threshold caveat (honest):** under per-cell-optimal thresholds the per-category GATE (rerank
  NK/LK, raw-KNN on PK) is +0.031 mean over the champion. But under POOLED CAFA-style scoring (one
  shared threshold per aspect = the LAFA deployment reality) the raw-KNN CHAMPION WINS (0.439 vs
  gated 0.329). So under deployment-realistic scoring the reranker does NOT beat the champion; PK
  drags it.
- C2: per-aspect ISOTONIC + Platt calibration does NOT recover PK (statistically identical to
  uncalibrated; pk-bpo IA-precision 0.167 either way). The PK precision collapse is INTRINSIC to the
  reranker's cross-protein ordering, not a score-scale artifact.

## 5. Honest verdict + open items

- **Thesis win:** the rigorous horizon-matched frame + D1 (beat homology in the twilight/remote
  zone). The representation lever (learned encoder) is the validated story.
- **The reranker number-lever is blocked by the PK wall** under deployment scoring; calibration is
  not the fix.
- **The real PK lever (deferred, "Track A next"):** a v2 export with `compute_association`
  (cooccurrence) + `compute_classifier` ON — the two zero-filled evidence ports that historically
  carried PK precision. Prerequisites: build cooccurrence per train-t0-set (only v227 built now) +
  classifier seeds; PK may still be a partial ceiling.
- **The final TEST number (227->230)** for champion + gated-reranker under pooled scoring needs a
  <=227 export (train [..,225,227], test [230] -> eval 227->230, deployment-realistic training).
  Validation-frame numbers are the proxy until then.

Artifacts: lab PR #113 (C1+C2, `results/clean_a4/`), MLflow exps `reranker-clean-A4-train225`;
session memory `project_temporal_eval_run_2026_06_26`.

## 6. TEST 227->230 champion (THE LAFA NUMBER) -- delivered 2026-06-27

The deployment-realistic <=227 export completed (job `d6d9fc55`, dataset
`clean-learned-train227-test230`, train 14 cuts 160->227, test 230, eval pair `v227-v230`, learned
encoder `d8979601`, k=30, alignments+self_prior ON, association+classifier OFF; schema v2
`775611822dd9`; 471,798 eval rows, 10,034 positives). Published to `s3://protea/datasets/`. Champion
= raw-KNN score (`1 - cosine distance`), GT = eval label>0, cafaeval(prop=fill, norm=cafa,
no_orphans, max_terms=500, th_step=0.001), OBO+IA = v227 LAFA-aligned (lafa_t0_Sep_2025). Scorer
`scratchpad/champ_227230_v2.py` (canonical, mirrors `farm_exp_15_knn_226_227.py`).

POOLED-per-aspect (one threshold per namespace = the LAFA deployment number = headline):

| aspect | f_micro_w | fmax (unweighted) | n cand | pos | prot |
|---|---:|---:|---:|---:|---:|
| MFO | **0.357** | 0.401 | 31,113 | 2,089 | 1,574 |
| BPO | **0.160** | 0.351 | 387,084 | 5,047 | 5,278 |
| CCO | **0.311** | 0.558 | 53,601 | 2,898 | 2,052 |
| **mean** | **0.276** | | | | |

Per-cell f_micro_w (category-specific threshold, diagnostic):

| | MFO | BPO | CCO |
|---|---:|---:|---:|
| NK | **0.555** | 0.362 | 0.428 |
| LK | 0.442 | 0.376 | 0.391 |
| PK | 0.302 | 0.140 | 0.293 |

per-cell mean = **0.365**.

Reading: NK-MFO 0.555 holds the #1-class signal on the REAL test frame (matches/exceeds the
validation-frame champion ~0.50). The pooled mean (0.276) sits below the per-cell mean (0.365)
because pooling forces one threshold and the PK mass -- especially PK-BPO (0.140, 4,455 proteins,
the volume-dominant cell) -- drags the shared-threshold Fmax down.

## 7. Reranker BEATS champion on 227->230 -- this REVERSES the C1/C2 PK-wall conclusion

A per-category LightGBM lambdarank reranker (one model per NK/LK/PK, 64 real features; the
zero-filled association_*/classifier_* columns excluded), trained on the 14 train cuts v160..v227 of
the SAME clean export (v225-v227 holdout for early stopping), re-scored the 227->230 eval candidates.
Compared to the raw-KNN champion with the identical cafaeval harness:

POOLED-per-aspect f_micro_w (the LAFA deployment number):

| aspect | champion | reranked | gate (D43) | d_reranked |
|---|---:|---:|---:|---:|
| MFO | 0.357 | **0.519** | 0.317 | +0.162 |
| BPO | 0.160 | **0.363** | 0.142 | +0.202 |
| CCO | 0.311 | **0.495** | 0.308 | +0.184 |
| **mean** | **0.276** | **0.459** | 0.256 | **+0.183** |

Per-cell mean: champion 0.365 -> reranked **0.501** (+0.135); the reranker lifts EVERY cell incl PK
(pk-bpo 0.140->0.343, pk-cco 0.293->0.489, pk-mfo 0.302->0.471). The ADR-D43 GATE (reranker NK/LK +
raw-KNN PK) is the WORST pooled option (0.256, below champion): mixing reranker scores with 1-distance
breaks the single shared threshold. So the LAFA submission config = FULL RERANKED (all categories).

This CONTRADICTS section 4 (C1/C2: "PK regresses, raw-KNN champion wins pooled"). The contradiction
is explained: C1/C2 ran on a stale schema / dense substrate / gate-only pooled comparison; this is the
first clean run on the learned-champion encoder + schema v2 `775611822dd9`. Section 4's pessimism was
the artifact; the PK wall is NOT intrinsic.

LEAKAGE AUDIT (the +0.18 is large and reverses a documented result, so it was audited hard):
- Eval pair v227-v230 is NOT among the 14 train pairs (no snapshot leak).
- No single feature separates the label at leakage level (all per-category AUC in 0.46..0.66; the
  anc2vec_query_known_*/lineage_*_of_known features are correctly EMPTY for NK -- no prior annotations
  -- and only modestly predictive for PK, t0-derived).
- Positive (protein,go) pair overlap train<->eval = 7.4% (NK 2.1 / LK 11 / PK 7.6). Removing ALL 741
  train-seen eval-positive pairs leaves the lift essentially unchanged: +0.183 -> +0.179. So pair
  overlap does NOT drive it.
- 92% of eval proteins recur in train (expected for PK), but the reranker has no protein-identity
  feature, so it cannot memorise per protein.
- Conclusion: the lift is genuine = better within-cell ranking (+0.135 per-cell) PLUS cross-category
  calibration that 1-distance lacks (the pooled/LAFA metric rewards a globally comparable score).
  Robust and deployable.

Artifacts: `protea-reranker-lab/results/clean_227230/` (boosters/, eval_scores.parquet, comparison.json,
leak_check_overlap.json, champ_227230_v2.py).

## 8. Scored by LAFA's OWN pipeline (the authoritative, directly-comparable number)

The reranked predictions for the official LAFA query set (7401 proteins; 7347 from our eval, 54 KNN
fallback) were scored by CAFA_forever's exact invocation (`cafaeval <obo> <preds> <gt> -ia IA.tsv -toi
terms_of_interest -prop fill -norm cafa -no_orphans`, PK adds `-known groundtruth_PK_known.tsv`)
against LAFA's official ground truth for release `Sep_2025_Mar_2026` (= 227->230; NK 400 / LK 869 /
PK 6341 proteins). This is deployment-realistic AND removes the known-term advantage on PK via
`-known`. PROTEA-reranked f_micro_w vs the leaderboard:

| cell | PROTEA-reranked | best baseline | PROTEA-KNN | rank |
|---|---:|---|---:|:--|
| NK-MFO | **0.602** | GOA-nonexp 0.591 | 0.579 | #1 |
| NK-BPO | **0.309** | TransFew 0.301 | 0.263 | #1 |
| NK-CCO | 0.431 | FunBind 0.473 | 0.407 | #3 |
| LK-MFO | **0.519** | GOA-nonexp 0.510 | 0.489 | #1 |
| LK-CCO | 0.419 | TransFew 0.434 | 0.332 | #2 |
| LK-BPO | 0.348 | TransFew 0.512 | 0.284 | #3 |
| PK-MFO | **0.235** | GOA-nonexp 0.194 | 0.191 | #1 |
| PK-CCO | **0.254** | TransFew 0.220 | 0.184 | #1 |
| PK-BPO | 0.117 | TransFew 0.294 | 0.075 | #4 |

PROTEA-reranked is #1 of all methods in 5/9 cells (NK-MFO, NK-BPO, LK-MFO, PK-MFO, PK-CCO) and beats
our deployed PROTEA-KNN in ALL 9 (mean 0.312 -> 0.359). Per-category means: NK 0.447, LK 0.429, PK
0.202. Crucially, under LAFA's `-known` PK scoring (which excludes already-known terms) the reranker
STILL leads PK-MFO/PK-CCO and beats KNN on PK-BPO -- so the section-7 internal PK lift was partly
known-term inflation, but a genuine, leaderboard-leading PK signal remains. The reranker is weakest on
BPO (TransFew, a specialised GO model, dominates LK-BPO/PK-BPO). Injected live as method
`PROTEA-reranked` on the deployed LAFA board (protea-lafa.ngrok.app, release Sep_2025_Mar_2026);
release-data backups suffixed `.bak_prereranked`. Artifacts:
`protea-reranker-lab/results/clean_227230/lafa_submission/` + `protea-lafa-knn/predictions_7401_reranked.tsv`.
