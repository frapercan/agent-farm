# LAFA evaluation — canonical result (consolidated 2026-06-14)

## Headline

PROTEA (composite KNN, Ankh-base, K=30, t0 reference goa@227) on the **official LAFA
Sep_2025_Mar_2026 frame (7401 targets)**, f_micro_w (IA-weighted micro-F, mean over the three
namespaces):

| Method | NK | LK | PK | **Mean** |
|---|---|---|---|---|
| TransFew | 0.428 | 0.485 | 0.230 | 0.381 |
| FunBind | 0.441 | 0.451 | 0.205 | 0.366 |
| GOA-nonexp | 0.426 | 0.390 | 0.158 | 0.325 |
| **PROTEA (this work)** | **0.412** | **0.394** | **0.165** | **0.324** |
| PROTEA-KNN-v1 (prior submission) | 0.416 | 0.368 | 0.150 | 0.312 |
| DeepGOPlus | 0.384 | 0.392 | 0.157 | 0.311 |
| ProtT5 | 0.287 | 0.282 | 0.123 | 0.231 |
| BLAST | 0.264 | 0.274 | 0.102 | 0.213 |

**Position: #4 overall, effectively tied with GOA-nonexp for #3, and an improvement over the prior
PROTEA-KNN-v1 submission (0.312).** Per category, LK and PK both rank #3; NK is on par with the prior
KNN submission.

## Provenance (reproducible, UI-verifiable)

- Query set: `lafa-official-7401` (`acc27f47`), the exact 7401 official targets, all with Ankh-base embeddings.
- Prediction set: `12739db3` (composite, embedding `08234f06` Ankh-base, reference annotation set
  `c905dffa` = goa@227 t0-clean, snapshot `35c3ad67`, K=30), 7401/7401 covered.
- Evaluation set: `34a634a8`, groundtruth = LAFA official (NK 399 / LK 868 / PK 6340 + pk_known 307k),
  stats.frame = lafa_official.
- Scoring config: `bae5ece3` (composite linear). Result row marked frame=lafa, TEST_227_230, in /benchmark.
- Information accretion: LAFA official `IA.tsv` (Sep_2025).

## Harness (the only leaderboard-comparable invocation)

Per `CAFA_forever/modules/local/evaluation.nf`:
`cafaeval <Sep_2025 go-basic.obo> <preds> <gt> -ia IA.tsv -toi terms_of_interest -prop fill -norm cafa
-no_orphans` plus `-known groundtruth_PK_known.tsv` for PK (maps to `cafa_eval(exclude=...)`, which masks
known terms at the PROPAGATED level). Validated two ways (offline exact harness and the platform), both
mean 0.324.

Note: `storage/interpro_run/eval_lafa_frame.py` is unreliable for PK (it pre-filters only the exact known
leaf pairs, so propagated known ancestors leak back as predictions and inflate PK, 0.236 vs the correct
0.165). Use the platform or the exact offline harness.

## Methodology contributions

1. **Frame audit.** Our reconstructed 227->230 delta (7002 targets) diverged from LAFA's official 7401
   (miss 1322 PK, add 921). Root cause: LAFA's experimental source is `goa_uniprot_all` filtered to
   SwissProt-reviewed, and our import shows essentially no experimental growth over the window (only 3
   of 3631 LAFA novel-PK terms are experimental for us). The window itself is identical (GAF release 227
   = 2025-09-04 = t0, 230 = 2026-03-04 = t1, both clean by annotation date). Not a window bug.
2. **Frame alignment.** Predicted and scored on the exact official 7401 targets inside the platform, so
   the reported number is comparable and live in the UI.
3. **Winner's-curse discipline.** Levers are selected on SELECT 220->227 (held-out) and sealed once on
   the 7401 frame.

## Negative results (documented, do not repeat)

- IA/gamma prior: dead in all 9 (category x namespace) cells. Evidence-code ablation: dead in all 9.
  The linear scorer is exhausted; composite is near-optimal.
- InterPro as a flat candidate source: union recall 0.03%; refuted. Only viable as a learned feature.
- Self-prior (the protein's own t0 GOA-non-exp annotations) fused with KNN at the score level: refuted
  two ways on SELECT (maxblend never beats KNN-alone and hurts PK at high weight; agreement-boost is
  flat). The KNN neighbors already subsume the protein's own electronic annotations, and the composite
  score saturates so there is nothing to boost. The 7401 max-union (+0.002) did not replicate on SELECT.

## Decision (2026-06-14)

Consolidate 0.324 as the thesis result. The cheap levers are exhausted; closing the remaining gap to
FunBind/TransFew would require out-engineering dedicated learned multimodal models, which is high effort,
uncertain, and marginal for the thesis narrative. P2 (learned reranker with agreement + cross-aspect +
structure features) and P3 (structure for NK) are deferred, not abandoned.
