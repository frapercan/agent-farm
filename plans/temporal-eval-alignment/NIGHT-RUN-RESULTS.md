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
