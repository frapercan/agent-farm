# LAFA-IMPROVE — next-iteration plan to lift the canonical LAFA-frame score

Baseline (validated 2026-06-14, canonical 7401 frame, f_micro_w mean over 3 namespaces):

| | NK | LK | PK | MEAN |
|---|---|---|---|---|
| **OURS (composite KNN)** | 0.412 | 0.394 | 0.165 | **0.324** |
| GOA-nonexp | 0.426 | 0.390 | 0.158 | 0.325 |
| FunBind | 0.441 | 0.451 | 0.205 | 0.366 |
| TransFew | 0.428 | 0.485 | 0.230 | 0.381 |

We are #4 (tied #3 GOA-nonexp), beating the prior PROTEA-KNN-v1 (0.312).

## Diagnosis (where the gap is)

We win/tie on **no-knowledge** (NK 0.412 ~ best homology methods): KNN homology transfer is strong.
We lose on **prior-knowledge** (LK 0.394 vs 0.485; PK 0.165 vs 0.230). The bottleneck is **not** the
KNN transfer and **not** the reference labels (audit 2026-06-13: LAFA's experimental source is
`goa_uniprot_all` filtered to SwissProt-reviewed via `democafa.filter_gaf` — the SAME source we import,
not a richer curated one). The gap is a **method gap**: we do not exploit the protein's OWN existing
annotations, and we do not fuse signals the way TransFew/FunBind do.

## REFUTED — do not pursue

- **Phase-0 "enrich reference pool from SwissProt-curated GAF"**: REFUTED. `goa_uniprot_sprot.gaf` is
  `goa_uniprot_all` filtered to reviewed (a subset of what we already import), not a richer source.
- InterPro as a **flat source** (union recall 0.03%); only valid as a reranker feature.
- IA/gamma prior (dead 9/9 cells), evidence-code ablation (dead 9/9), linear-scorer tuning (saturated).
  The linear scorer is EXHAUSTED.

## Levers (sequenced by leverage x tractability)

### P1 — Prior-knowledge / self-prior stream (targets LK, the biggest gap +0.091)
The protein's own t0 annotations (experimental + IEA/non-exp), propagated, plus a **cross-aspect
association** model (GO term co-occurrence learned from the t0 reference pool: e.g. MFO "kinase
activity" -> BPO "phosphorylation"). GOA-non-exp alone already scores 0.325 on the LAFA frame and has
real within-cell complementarity with our KNN (audit max-union = 0.327). Leakage-clean via t0 cutoff.
Integrate as **learned reranker features**, NOT a flat blend (rejected held-out; max-union only +0.002).

### P2 — Generalizing reranker (fusion mechanism; targets LK + PK)
LightGBM over {KNN features, self-prior, InterPro, structure}, per-protein `rank_normalize`
calibration, focal/class-balanced loss for sparse PK-BPO (1.4% positives). The prior reranker did not
generalize to the sealed test (winner's curse) because the bridge models were UNDER-TRAINED, not
because the method is wrong. Proper training volume + held-out folds + beat-or-revert.

### P3 — Structure modality (targets the NK ceiling; orthogonal)
Second KNN index in structure space (Foldseek over AlphaFold DB, or ProstT5 structure tokens) -> remote
homologs sequence-KNN misses -> features into the reranker.

## Validation protocol (reuse the 2026-06-14 pipeline)

Every lever: SELECT 220->227 with held-out protein folds for selection/calibration -> seal ONCE on the
**exact 7401 LAFA frame** via the platform (`run_cafa_evaluation` + LAFA `IA.tsv`, eval set 34a634a8
reframed to official GT) -> compare to leaderboard with the EXACT published harness
(`-toi -known(exclude, propagated) -no_orphans`, Sep_2025 OBO; see `/tmp/eval_lafa_exact.py`).
Beat-or-revert. Watch winner's curse. NO flat blends.

Harness note: the platform gets `-known` right via the injected `pk_known` bucket; `eval_lafa_frame.py`
is BUGGED for PK (pre-filters known leaves -> inflates PK 0.236 vs correct 0.165). Use the platform or
`/tmp/eval_lafa_exact.py`.

## Realistic target

LK 0.394->~0.45, PK 0.165->~0.20, NK 0.412->~0.44 => mean ~0.35-0.36, contesting FunBind for #2-3.
TransFew (0.381) is a stretch; honest target = clear #2-3.

## Execution order

1. P1 self-prior on SELECT 220->227 + 7401 frames; learned KNN+self-prior blend, SELECT-validated,
   sealed on 7401. (Fastest proof; if a 2-feature learned blend beats max-union 0.327, P1+P2 thesis confirmed.)
2. P2 full reranker once P1 features land.
3. P3 structure last.
