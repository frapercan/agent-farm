# THE SIGNAL REGISTRY (receipt-backed, 2026-07-27)

Companion to `E2E-CANONICAL-RUN.md`. Built from a seven-way parallel audit of the
code, the frozen receipts, the lab results, and the memory store. Every status
here is backed by a measurement someone can open. Where audits disagreed, the
disagreement is stated and reconciled explicitly.

Two categories, judged by different criteria:

- **CONSOLIDATED SIGNAL**: a source of evidence with its own mechanism, whose
  contribution is measurable per cell. Judged by measured delta.
- **INDISPENSABLE MECHANISM**: machinery without which the number does not
  stand, and which usually has NO delta of its own because it is not optional.
  Judged by whether the result survives its absence.

Confusing the two is what made the previous registry look complete when it was
not.

## THE LESSON THAT GOVERNS THE WHOLE TABLE: gain is not contribution

Proven three separate times in the receipts:

1. `go_term_frequency` carries **25.47%** of the sealed champion's aggregate
   split gain, the single largest feature of 64. Dropping its ENTIRE family
   (`go_context`) costs NK-BPO **+0.011** and LK-MFO **+0.00005**.
2. `lineage_is_ancestor_of_known` is **20.55%** of the PK booster's gain (#2 of
   64). Dropping the whole lineage family is NEGATIVE on PK-BPO (-0.00379).
3. The decisive one: in SSE Mode B, `sse_score` ranks **#1 of 71 by gain** in
   both the nk and lk boosters, and **every PK bootstrap CI crosses zero**.

Never rank signals by tree importance. Rank by LOFO delta with a CI. (Companion
rule already banked: never triage levers by AUC, which ordered arms OPPOSITE to
f_micro_w at least five times.)

---

## 1. INDISPENSABLE SIGNALS (the 7/9 does not stand without these)

| Signal | What it is | Measured contribution |
|---|---|---|
| **Production base `08234f06`** (Ankh-base, mean-pool, last layer) | The embedding everything else sits on | Same encoder recipe on the weak local L48 base reaches 0.1447 vs 0.22013 on the production base = **~+0.075 mean9**. The single biggest lever in the project |
| **Learned k-WTA encoder `d8979601`** | The retrieval representation (sparse codes over the mean-pooled base) | KNN-only mean9 **0.2150** vs dense L48 **0.1336** (+61%), vs best hand-crafted L10-kWTA128-std 0.1460. Wins all cells |
| **M2 anc2vec hybrid classifier** | Full-vocabulary classifier; NK/LK candidate generator AND the `classifier_score` feature | LOFO NK **+0.180 / +0.198 / +0.245**, LK **+0.134 / +0.104 / +0.158**, PK **exactly 0.000** |
| **Two-tower sparse classifier** | PK candidate generator (per-cut, 554K curated) | PK **+0.038 / +0.031 / +0.040** (mean +0.036). See reconciliation below |
| **Per-category LightGBM lambdarank reranker** | The fusion layer itself | vs raw-KNN champion on the same pool: per-cell mean **0.5006 vs 0.3653 = +0.1353** |
| **`association`** (cross-aspect GO co-occurrence) | Prior-knowledge channel | LOFO PK **+0.024 / +0.017 / +0.016** (#1 family in PK-MFO and PK-BPO); LK small; NK **exactly 0.000** (leakage-clean by construction) |
| **`anc2vec_query` + `lineage`** | The query's own known GO, related to the candidate | LOFO PK **+0.020 / +0.016 / +0.031**; `anc2vec_query_known_maxcos` = 2nd-highest gain overall (19.36%) and TOP feature in PK |
| **InterPro2GO BP noisy-OR graft** | Score-level graft, NOT a feature column | **+0.0179** mean9 (0.3884 -> 0.40629). ALL of it in BP. **This is the delta that buys the 7/9** |

### Reconciliations where the audits disagreed

- **Two-tower**: audits split INDISPENSABLE / CONDITIONAL / REFUTED. All three
  are right about different things. As a PK generator it is **+0.036 mean**; on
  NK/LK it is **WORSE on 6 of 6 (mean -0.115)**. It is indispensable ONLY
  through per-category routing. The routing is the mechanism; the tower alone is
  not a champion. `graft_9cell.json` reproduces PK-MFO 0.24163 and PK-CCO
  0.26554 exactly, so its provenance in the 7/9 is certain.
- **`go_term_frequency`**: INDISPENSABLE by gain, small by LOFO. Classed
  CONDITIONAL below per the governing lesson.
- **Prefilter `tau_pre`**: strongest evidence in the project (10 of 10 disjoint
  folds chose 0.4, +0.0092 sd 0.0034) BUT it shrinks **3.5x** under the true
  board frame, to +0.00415 PK-BP / +0.00722 LK-BP. Real, smaller than advertised.

## 2. CONDITIONAL (real, but only in a stratum or behind a routing)

- **`go_context` / `go_term_frequency`**: 25.47% of gain, small LOFO. Keep, do not headline.
- **`anc2vec_neighbor`**: NK **+0.030 / +0.009 / +0.008** (#2 family in NK-MFO/NK-CCO), PK ~0.
- **Prefilter `tau_pre = 0.4`**: see above.
- **`pminmax` on LK-BPO only**: LK-BPO 0.307 -> 0.370 (**+0.063**, +0.022 over board) with ZERO regression on the other 8 cells. Category-routed.
- **`self_prior`**: feature-level CONFIRMED (part of the 0.358 -> 0.381 step); score-level blend REFUTED (alpha 0.0-0.7 invisible, alpha 1.0 HURTS).
- **ProtST as a reranker feature**: mean9 **+0.0088 / +0.0118** across two seeds, all 3 BP cells positive. Small but real.
- **Classifier-alone as the PK scorer**: **+0.00839** sd 0.00578, 9/10 folds (corrected down from an inflated +0.02106 by the dict-join fix). Gate PASS but barely (1.45x).

## 3. OBSOLETE / BROKEN (archive, with the reason)

| Item | Verdict |
|---|---|
| **Entire KNN homology block** (`knn_distance`, `knn_vote`, `alignment_nw`, `alignment_sw`, `taxonomy_pair`, `taxonomy_voters`, `length`) | **Never in the top-2 of ANY of the nine cells.** Largest positive anywhere is knn_vote PK-CCO +0.00893. Deltas inside noise. An entire block of the thesis that does not pay |
| **`emb_pca_query_0..15`** | Gain **exactly 0.000** in all three boosters, LOFO **exactly 0.0** in all 9 cells. In the newer export they are **all NaN**. Dead |
| **`interpro_*` reranker feature family** (11 cols) | Gain exactly 0.000 everywhere. IMPORTANT NUANCE: this is a **CONFIG gap**, not a broken producer. InterPro works, but as a **score-level graft**, not as a feature |
| **`length_query`** | NaN 100%. Mechanical cause confirmed: the KNN producers never run over classifier candidates |
| **Self-prior as a score blend** | Invisible at alpha 0.0-0.7; HURTS at 1.0 |
| **`rankpct()` normalisation** | A BUG that cost **0.088** f_micro_w and MANUFACTURED the 0.1255 baseline. Fixed in PROTEA#737. It invalidated every technique lever measured against it |

## 4. REFUTED (measured, negative, closed. Do not revisit)

SSE (Mode A generator and Mode B feature, despite excellent intrinsics),
DeepGO-SE entailment, learned k-WTA GO encoder (intrinsically 4x better, does
not convert), multi-PLM candidate-pool union (in-window positive that FULLY
REVERSES under the temporal gate), TransFew frequency-partitioned IA
calibration, ProtEx exemplar verification, STRING PPI, phylogenetic profiling,
structural gate (AFDB/FoldSeek), annotation-space RAG, literature/abstract text
as a channel, cross-modality consensus, co-occurrence candidate expansion,
soft IA-weighted-F objective (-0.023), fuse_listwise (-0.0355 at equal input),
L10-std, learned multi-layer mixing, attention pooling, multivector/ColBERT,
naive SDR + Tanimoto, budgeted ontology profile, donor-recency weighting,
soft Pmin/Pmax DAG propagation, GO-text BioBERT label basis, M3 IEA pretraining,
SVD label embedding, GCN label encoder, per-cell reranker split, binary
objective, within-protein rank features, class weighting.

The pattern across ALL of them: **the mechanism is often REAL, the conversion is
not.** Cross-modality consensus compounds precision ~23x and still tops out at
2.5-3% precision. STRING was the strongest of five generation channels at 5.8%
IA-precision and still floods. This is not a series of failures, it is a
characterisation of the calibration wall, and it belongs in the thesis as such.

## 5. UNMEASURED (the real gaps, ranked by expected value)

1. **ProtST as the PRIMARY RETRIEVAL SPACE** (not as a feature). kNN mean9
   **0.2485 vs champion 0.2150 = +0.0335, WINNING ALL 9 CELLS** (BP nk +0.040 /
   lk +0.017 / pk +0.029). As a feature it is worth +0.0016 (noise). As a
   retrieval space it beats the champion outright. **This is the largest
   unexploited measured lever in the project.**
2. **Triple-combine at retrieval** `protst + protrek + d8979601` = **0.2650 vs
   champion 0.2213 = +0.044 pre-reranker**.
3. **8-PLM ensemble**: NONE-MEASURED. The METHOD_CARD carries no f_micro_w and
   no per-PLM vs ensemble comparison. The mean-combine rationale is argued, not
   measured.
4. **Categorical features never enrolled**: `annotation_meta` (qualifier,
   evidence_code, aspect), `plm_context` (plm_id), `k_neighborhood` (k_context).
   Absent from the sealed champion's 64 features and from the LOFO grid.
5. **`IA` itself**: computed by `apply_ia`, stamped on every prediction,
   persisted to a typed column, fed to boosters, and **present in NO branch of
   `feature_schema`**. A signal outside the fingerprint.
6. **Composition of the prefilter with the classifier swap in the TRUE frame**
   (measured only in the no-`-known` frame, where levers composed to +0.016).
7. Sparse-contrastive / JEPA in the load-bearing form (sparsify-per-chunk then
   union). The served champion is pool-then-kWTA, so it has never been built.
8. Per-aspect layer routing on the production base; cross-PLM levers; the
   8,195 discarded `regulates` DAG edges; the t0-non-experimental trivial
   baseline as a reported control.

## 6. INDISPENSABLE MECHANISMS (no delta of their own, everything depends on them)

| Mechanism | Why it is load-bearing |
|---|---|
| **`-known groundtruth_PK_known.tsv` on PK cells ONLY** | Omitting it moves PK-BP 0.20132 -> 0.11666 (**-0.0847**) and was the ENTIRE "we do not reproduce the board" gap. It SIGN-FLIPPED the headline lever (+0.02245 -> -0.01331) and shrank the prefilter 3.5x. **The single most consequential flag in the project** |
| **The temporal train/test gate** (fit <= v225, blind on v227->v230) | Caught FOUR in-window positives that fully reversed. The most load-bearing non-signal machinery there is |
| **Per-category routing** (NK/LK/PK boosters + per-category generator selection) | Per-CELL (per-aspect) splitting LOSES: 0.2017 vs pooled 0.2222. Routing turns a generator that regresses NK/LK by -0.115 into a net positive |
| **`prop=fill` ancestor inheritance** | The inheritance tax every fusion is judged against. Free inherited ancestors arrive at weighted precision 0.2967 vs the arm's own 0.1801. This is WHY every low-precision channel floods |
| **cafaeval single global tau sweep** | The calibration wall itself. The single mechanism that explains why ~15 real, separable channels all fail to convert |
| **Anchor reproduction as a hard precondition** | Its ABSENCE produced two of the four big invalidations |
| **Row-alignment ASSERT instead of a dict join** | The dict join silently rewrote 71,574 of 863,748 rows (8.3%); duplicate scores differ by a MEDIAN of 3.60 |
| **10-fold disjoint-protein cross-fit gate** | Produced every surviving positive with an honest error bar |
| **Shuffled-feature / fixed-score / random-order controls** | Demoted SSE's two apparent LK levers to noise; reversed a reported +0.0122 to -0.0004 |
| **Matched-volume + IA-precision (not counted precision)** | A precision precondition is only checkable at matched volume |
| **Seed-averaging by convergence** | Classifier 0.343 -> 0.369 (3 seeds), generalises. Anti-winner's-curse. **CURRENTLY DEAD IN DEPLOY, see below** |
| **Paired bootstrap CIs + declared noise floor (0.0034)** | What separates a result from a story |
| **Stratification by length x category x neighbour-identity** | Revealed the entire regime map |

## 7. THREE DEFECTS FOUND BY THE AUDIT (act before the format)

1. **The lab artifacts backing the headline are UNTRACKED.** `git status
   --porcelain results/` returns **30 untracked entries**, including all of
   `results/clean_227230/` (the three sealed boosters) and
   `s2e_serve_reranker/` (the blobs registered as RerankerModels 94f0030e /
   83d758fe / 66c5a25f). Only 9 files under `results/` are tracked. The lab
   README forbids committing model binaries, so this is by policy, which means
   **the policy has no preservation path**.

   A first archive pass on 2026-07-27 was declared MITIGATED and **that claim
   was WRONG**. Adversarial verification found the tar excluded `*.pt` and so
   contained **zero torch checkpoints**, while the seven LIVE two-tower heads
   (`storage/two_tower_sparse/heads/head_seed{0,7,23,31,53,91,137}.pt`, the ones
   `PROTEA_TWO_TOWER_SEED_DIR` actually points at) existed in no tar, no dump and
   no repo. Without them, two of the seven won cells fall below board (PK-MFO
   percut 0.2416 vs baseline 0.2038, board 0.235; PK-CCO 0.2655 vs 0.2252, board
   0.254). Five further preservation gaps were found by the same pass and all are
   now closed and md5-verified:
   - `storage/two_tower_sparse/` (3.0G: the 7 heads, `go_sparse_codes.npz`, `vocab_go.npy`, `per_cut/`)
   - `~/.secrets/protea.env` + 3 `.bak_*` + `publish-tokens.env`: the **operational definition of the deployed champion** (routing knob, embedding config, learned-encoder path, two-tower paths, JWT secret). In no tar, no dump, no repo
   - `storage/learned_encoders/` (21M) including `ankh_base_hardneg.pt`, the artifact `PROTEA_LEARNED_ENCODER_ARTIFACT` points at, and the receipt for a contribution section 9 calls MISSING from the thesis
   - the **`mlflow` database**: the nightly cron dumps `protea` ONLY. Every MLflow run behind the representation and pooling audit lived only inside the docker volume. Dumped (317K, 53 tables with data)
   - **MinIO**: a backup exists but is dated 2026-06-04 and predates every artifact of the current frame. `rerankers` (1.8G), `eval_groundtruth` (338M), `runs`, and the mlflow bucket are now preserved. `datasets` (19G) and `eval_artifacts` (25G) were deliberately NOT copied: they are derived results the clean run regenerates
   - the two documents driving this decision (`E2E-CANONICAL-RUN.md`, `SIGNAL-REGISTRY.md`) were themselves untracked and existed only on the disk to be formatted

   **The generalisation worth keeping: a claim of PRESERVATION is as dangerous as
   a claim of deletion.** "It is saved" licenses the author to destroy the
   original. Never report an artifact as backed up without reading it back OUT of
   the destination.

   Still open: `pg_restore --list` on the 40G `protea` dump exits 0, but a TOC
   listing does NOT verify the data blocks, and `pgdump.log` records prior
   failures of this exact job (disk-full, and a dropped connection mid-COPY of
   `sequence_embedding`). A full decompression check was launched and must be
   confirmed green BEFORE the format.
2. **The deployed system is not the champion.**
   `worktrees/protea-deploy/.env:15` sets
   `PROTEA_CLASSIFIER_SEED_DIR=storage/fullgo_models/seeds`, **a directory that
   does not exist** (deleted 2026-07-11 in a disk-pressure prune). The
   seed-averaging parity rule is silently dead for the M2 classifier in serve.
3. **The thesis has forked.** The working tree is on
   `thesis/validated-lafa-numbers-2026-07-02`; `origin/main` holds 7 commits the
   checkout lacks and the checkout holds 5 that main lacks. **The two lineages
   disagree on the headline.** The PDF served publicly is the branch state.

Good news that corrects the record: **the two-tower SVD reproducibility blocker
is NOT real for the deployed artifacts.** The frozen deterministic SVD basis and
saved components exist; the memory claim was true only for the SUPERSEDED
champion. Candidate generation IS re-derivable.

## 8. THE CLEAN TRAJECTORY (what the E2E run carries)

1. **Re-baseline the retrieval space FIRST.** ProtST alone beats the champion on
   all 9 cells and the triple-combine is +0.044 pre-reranker. Every downstream
   number depends on the retrieval substrate, so settling it first is the only
   ordering that does not force a re-run. This is also the honest form of the
   8-PLM grid: a matched-parameter comparison at retrieval level, gated on
   recall@30 and IA-coverage, not on the board.
2. **Keep exactly four signal groups** into the reranker: the learned sparse
   retrieval codes, the classifier (routed NK/LK) plus the two-tower (routed
   PK), the prior-knowledge trio (`association` + `anc2vec_query` + `lineage`),
   and `go_context`. Drop the entire homology block, emb_pca, and interpro-as-
   feature. That is roughly 64 features down to a defensible core.
3. **Keep InterPro as a BP score-level graft**, which is what actually earns the
   +0.0179, and say so plainly.
4. **Restore seed-averaging in serve** or drop the parity claim. It cannot stay
   asserted and dead.
5. **Enrol the never-measured categoricals** (aspect, evidence_code, qualifier,
   plm_id, k_context) once, so the schema stops carrying declared-but-unused
   families.
6. **Measure the score-to-tree transversal explicitly** per cell: the tuned
   hand-calibrated blend ceiling vs the tree crossing it. This is contribution
   #2 and it currently has no chapter.
7. **Report the refuted set as a characterisation of the calibration wall**, not
   as an appendix of failures.

## 9. THESIS RESTRUCTURE (the audit's chapter verdict)

- **Ch2 Biological Background**: KEEP nearly as is (one non-trivial number, no defects).
- **Ch1 Introduction, Ch3 Related Work**: rewrite the contribution list. It currently omits the temporal dataset, the sparse retrieval encoder, and the scale claim.
- **Ch4 System Design, Ch5 Implementation**: 52 pages, ~30% of the body, almost number-free. This is the **argument-to-page distortion**: the four contributions the campaign actually produced get less space than the plumbing.
- **Ch6 Evaluation**: REWRITE. ~70 quantitative claims, the placeholder multi-PLM grid, and the metric/frame/backbone chaos. The flagship result is reported in a metric the chapter treats as secondary.
- **Ch7 Conclusion**: REWRITE around the surviving claims.
- **Appendix D (Development Trace)**: 28 pages of Fmax on RETIRED frames. Cut or move to the archive.
- **`defensa.tex`**: five weeks stale, asserts a superseded headline. Regenerate from the final numbers.
- **MISSING ENTIRELY** (zero lines each, all with receipts on disk): the learned k-WTA sparse retrieval encoder, SSE plus the entailment characterisation of the BP frontier, the temporal-dataset contribution, the distributed/scale claim, and the 9-cell LOFO regime map.

Both hard constraints (no em-dashes in publishable prose, no AI attribution) are
currently SATISFIED in the manuscript.
