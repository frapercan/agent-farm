# THE SIGNAL REGISTRY (receipt-backed, adversarially verified, 2026-07-27)

Companion to `E2E-CANONICAL-RUN.md`. Built from a seven-way parallel audit of the
code, the frozen receipts, the lab results and the memory store, then subjected
to a four-way adversarial verification whose job was to REFUTE each status call.
Forty-eight findings survived that verification and are folded in below.

The verification's own summary is worth stating up front, because it shapes how
to read this document: **the arithmetic was sound and the classification was
not.** Roughly twenty numbers were reopened from their receipts and reproduced,
including the LOFO grid to five decimals, the two-tower +0.036 / -0.115, the
InterPro +0.01789, the prefilter 10-of-10 with sd 0.0034, the `-known` -0.0847
and the k-WTA 0.2150 / 0.13356. Exactly one number was simply wrong. The damage
was in what the numbers were taken to MEAN.

Two categories, judged by different criteria:

- **CONSOLIDATED SIGNAL**: a source of evidence with its own mechanism, whose
  contribution is measurable per cell. Judged by measured delta with a CI.
- **INDISPENSABLE MECHANISM**: machinery without which the number does not
  stand, and which usually has NO delta of its own because it is not optional.
  Judged by whether the result survives its absence.

## THE FRAME PROBLEM (read before any number below)

Sections 1, 2 and 6 mix at least four incommensurable evaluation frames. The
same reranker reads PK-BPO **0.3433** in one row and **0.117** in another, and
both are correct in their own frame. A number here is meaningless without its
frame, which is: obo/IA version, `prop`, `norm`, `max_terms`, `th_step`, and
above all **whether `-known` was applied to PK**. Where a row's frame is known to
differ from the board's, it is flagged inline. Attaching a full frame column to
every row is outstanding work, listed in section 10.

## THE GOVERNING LESSON: gain is not contribution

Proven three times:

1. `go_term_frequency` carries **25.47%** of the sealed champion's aggregate
   split gain, the single largest feature of 64. Dropping its ENTIRE family
   (`go_context`) costs NK-BPO **+0.011** and LK-MFO **+0.00005**.
2. `lineage_is_ancestor_of_known` is **20.55%** of the PK booster's gain (#2 of
   64). Dropping the whole lineage family is NEGATIVE on PK-BPO (-0.00379).
3. In SSE Mode B, `sse_score` ranks **#1 of 71 by gain** in both the nk and lk
   boosters, and **every PK bootstrap CI crosses zero**.

**CAVEAT THE VERIFICATION ADDED, and it is serious:** the gain shares above are
computed on a **64-feature booster whose own SUMMARY.md records that
`classifier_*` and `association_*` were EXCLUDED** - the two families section 1
declares indispensable on LOFO evidence. **Gain and LOFO are measured on
different models.** Until the gain table is recomputed on the same booster the
LOFO used, gain rankings and LOFO deltas may not be compared row to row. Pin
"the sealed champion" to one artifact path plus `schema_sha` before quoting
either again.

Companion rule already banked: never triage levers by AUC, which ordered arms
OPPOSITE to f_micro_w at least five times.

---

## 1. INDISPENSABLE SIGNALS

Ordering convention throughout: **mfo / bpo / cco** (this differs from the order
used in some receipts, which is why it is stated).

| Signal | What it is | Measured contribution and its frame |
|---|---|---|
| **Production base `08234f06`** (Ankh-base, mean-pool, last layer) | The embedding everything sits on | Same encoder recipe on the weak local L48 base reaches 0.1447 vs 0.22013 on the production base = **~+0.075 mean9**. FRAME: KNN-only retrieval mean9, never re-measured through the reranker or the 9 board cells |
| **Learned k-WTA encoder `d8979601`** | The retrieval representation | **CORRECTED**: the isolated learned-head delta on a MATCHED base is 0.14467 vs 0.13356 = **+0.0111 (~+8%)**. The previously stated "+61%" double-counted the +0.075 already credited to the base in the row above. Same KNN-only frame caveat |
| **M2 anc2vec hybrid classifier** | NK/LK candidate generator AND the `classifier_score` feature | LOFO NK **+0.180 / +0.198 / +0.245**, LK **+0.134 / +0.104 / +0.158**, PK **exactly 0.000**. One of only two rows here with a genuine counterfactual |
| **Two-tower sparse classifier** | PK candidate generator (per-cut, 554K curated) | PK **+0.038 / +0.031 / +0.040** (mean +0.036); NK/LK **WORSE on 6 of 6** (mean -0.115). **The strongest indispensability case in this section**: without it PK-MFO falls to 0.2038 (below board 0.235) and PK-CCO to 0.2252 (below board 0.254), so **two of the seven won cells flip** |
| **Per-category LightGBM lambdarank reranker** | The fusion layer | vs raw-KNN champion, per-cell mean 0.5006 vs 0.3653 = **+0.1353**. **FRAME WARNING**: this is a no-`-known`, `max_terms=500` frame in which the three PK cells carry the largest deltas, i.e. exactly the cells declared overstated without `-known`. The **NK/LK-only delta from the same table is +0.108 and IS frame-safe**. Do not present 0.5006 alongside 0.3884 / 0.40629 as commensurable |
| **`association`** (cross-aspect GO co-occurrence) | Prior-knowledge channel | LOFO PK **+0.024 / +0.017 / +0.016** (#1 family in PK-MFO and PK-BPO); LK small; NK **exactly 0.000** (leakage-clean by construction). Gain half of this row is void per the 64-feature caveat |
| **`anc2vec_query`** | The query's own known GO vs the candidate | LOFO PK **+0.020 / +0.016 / +0.031**; `anc2vec_query_known_maxcos` = 2nd-highest gain overall (19.36%) and TOP feature in PK |
| **InterPro2GO BP graft** | Score-level graft, NOT a feature column | **+0.0179** mean9 (0.3884 -> 0.40629). See the two corrections immediately below |

### Corrections the verification forced in this section

- **`lineage` is SPLIT OUT of the indispensable row and demoted to CONDITIONAL.**
  By the registry's own LOFO-with-CI rule it helps on PK-MFO and PK-CCO only, is
  **negative on PK-BPO**, zero on all three NK cells and negative on 2 of 3 LK
  cells. Keeping it here contradicted the governing lesson.
- **"InterPro is the delta that buys the 7/9" is DELETED as false.** Its own
  receipt puts **96% of the +0.0179 into LK-BPO and PK-BPO, the two cells the
  project LOSES**. Only 4.0% (+0.00637, NK-BPO) lands in a won cell, and no
  receipt shows NK-BPO would flip without it. The true and still publishable
  claim: **InterPro is a real BP lever on the two cells we do not win.** The same
  false sentence appears in `storage/feature_necessity/WRITEUP.md` and must be
  struck there too.
- **InterPro mechanism and number do not match.** As written the row paired a
  tuned mechanism name ("noisy-OR") with an UNTUNED arm's number, and the higher
  of the two arms was **selected on test**. Choose one: either "noisy-OR" with
  the validation-selected **+0.0148 (0.3884 -> 0.40323)**, or 0.40629 relabelled
  **"naive max-blend, untuned"**.

## 2. CONDITIONAL

- **`lineage`** (moved here): PK-MFO / PK-CCO only, negative PK-BPO, zero NK.
- **`go_context` / `go_term_frequency`**: 25.47% of gain, small LOFO. Keep, never headline.
- **`anc2vec_neighbor`**: NK **+0.030 / +0.009 / +0.008**, PK ~0.
- **Prefilter `tau_pre = 0.4`**: 10 of 10 disjoint folds chose 0.4, **+0.0092 sd 0.0034**. **Two separate results, previously chained as one**: the 3.5x shrink is from the WITHHOLD arm, and the **+0.00415 PK-BP / +0.00722 LK-BP come from withholding 90%, not from `tau_pre=0.4`**.
- **`pminmax` on LK-BPO only**: 0.307 -> 0.370 (+0.063, +0.022 over board), zero regression elsewhere. Added clause: **the 0.307 baseline is a regression the clf+assoc arm itself introduced**, so +0.063 is recovery and **+0.022 is the net movement**.
- **KNN homology block** (moved UP from OBSOLETE, see section 3): **CONDITIONAL-UNTESTED**.
- **ProtST as a reranker feature**: mean9 +0.0088 / +0.0118 across two seeds.
- **Classifier-alone as the PK scorer**: +0.00839 sd 0.00578, 9/10 folds. **FRAME WARNING: measured WITHOUT `-known`**, in the frame the project itself declared invalid. At the documented shrink factor it would fall **below the 0.0034 noise floor**. Do not cite as a passing gate until re-measured.
- **`self_prior`**: **DOWNGRADED to UNMEASURED-IN-FRAME.** The only support is a confounded row in a retired frame; the current-frame LOFO puts it at or below noise and negative in most cells. Section 6 credits the SAME confounded row to seed-averaging, so one step was being spent twice.

## 3. BROKEN / RETRACTED (genuinely archived)

| Item | Verdict |
|---|---|
| **`rankpct()` normalisation** | A BUG that cost **0.088** f_micro_w and MANUFACTURED the 0.1255 baseline. Fixed in PROTEA#737. Invalidated every technique lever measured against it |
| **Self-prior as a SCORE BLEND** | Invisible at alpha 0.0-0.7; HURTS at 1.0. (The feature-level form is a separate question, now UNMEASURED-IN-FRAME) |

**This section used to contain four more entries. All four were WRONGLY
ARCHIVED and have been moved to section 5, because the measurement behind their
archival does not exist.** This was the single most dangerous class of error in
the draft: the author was about to format the machine and archive them.

## 4. REFUTED (measured, negative, closed)

SSE (Mode A generator and Mode B feature, despite excellent intrinsics),
DeepGO-SE entailment, **multi-PLM POOL-AUGMENTATION union** (renamed so it is not
read as closing the retrieval-level combination in section 5), TransFew
frequency-partitioned IA calibration, ProtEx exemplar verification,
phylogenetic profiling, structural gate (AFDB/FoldSeek), annotation-space RAG,
literature/abstract text as a channel, cross-modality consensus, soft
IA-weighted-F objective (-0.023), fuse_listwise (-0.0355 at equal input),
L10-std, attention pooling, multivector/ColBERT, naive SDR + Tanimoto, budgeted
ontology profile, donor-recency weighting, soft Pmin/Pmax DAG propagation,
GO-text BioBERT label basis, M3 IEA pretraining, SVD label embedding, GCN label
encoder, binary objective, within-protein rank features, class weighting.

**NEW ENTRY the draft was missing, and it is load-bearing:** a **learned k-WTA
head on ProtST LOSES to raw ProtST** (-0.0043 at d4096, -0.0074 at d2048,
negative on 8 of 9 cells). **The sparse head that helps raw Ankh does NOT
transfer.** This argues against section 8 item 1 and against the
sparse-contrastive direction generally, and it was invisible in the draft.

**Two entries RECLASSIFIED because they were refuted in one mode and never tried
in another** (the same error already made once with ProtST: noise as a feature,
+0.0305 as a retrieval space):

- **Learned k-WTA GO encoder**: refuted as a candidate-ADDER only; **untested as
  a retrieval space and as a reranker feature**. A harness in which the project's
  own indispensable generator scores -0.018 to -0.035 and a random-score control
  scores -0.063 is measuring the `prop=fill` tax of pool augmentation, not
  GO-representation quality.
- **STRING PPI**: **NULL as a candidate generator** (five of six deltas inside
  the 0.0034 floor, no CIs), **never tested as a reranker feature**. The untried
  cheap form belongs in section 5: a `string_partner_annotates_term` column over
  the EXISTING pool, which adds no candidates and therefore **pays no fill tax**.
- **Learned multi-layer mixing**: moved to section 5. The registry had it as both
  REFUTED (section 4) and UNMEASURED (section 5). Resolved to: naive equal-weight
  multi-layer concatenation is negative **on the weak local base**; a learned mix
  **on the production base has never been run**.

The pattern across the genuinely refuted: **the mechanism is often REAL, the
conversion is not.** Cross-modality consensus compounds precision ~23x and still
tops out at 2.5-3%. This is a characterisation of the calibration wall and
belongs in the thesis as such, not as an appendix of failures.

## 5. UNMEASURED (the real gaps, ranked by expected value)

1. **ProtST as the PRIMARY RETRIEVAL SPACE.** **ARM CORRECTED**: `protst_zscore`
   = 0.24849, **+0.0335 vs champion, wins 9/9**. But **RAW ProtST, which is what
   is deployed**, = 0.24547, **+0.0305, wins 8/9, losing nk-MFO by ~-0.0009**.
   Receipt: `storage/regen_headline/protst_repr/protst_repr_report.json`. Still
   the largest unexploited measured lever.
2. **Triple-combine at retrieval** `protst + protrek + d8979601` = 0.2650 vs
   champion 0.2213 = **+0.044 pre-reranker**.
3. **`emb_pca_query_0..15`: NEVER EVALUATED** (moved from section 3). 100% NaN,
   `nunique` 0 in BOTH exports on disk, because `use_embedding_pca` defaults
   False at all six declaration sites. "Gain exactly 0.000" is the arithmetic of
   a column LightGBM **cannot split on**. The project's own
   FEATURE_SCHEMA_API_AUDIT already corrected this and **forbade retiring it**;
   the draft re-committed the error. The flag must be split from a new emit-only
   switch before any retirement decision.
4. **KNN homology block: CONDITIONAL-UNTESTED, not obsolete** (moved to section
   2). The LOFO design **cannot see block weight**: the family is undefined on
   **59-71% of rows**, carries **~19% of positives**, and was dropped **one
   family at a time across 8 CORRELATED families, at one seed, with no CIs, under
   `objective=binary`** which section 4 itself lists as REFUTED. The
   "inside noise" bar was also applied inconsistently (`anc2vec_neighbor` sits
   inside the same band and was kept).
5. **`interpro_*` as a feature: never configured, not archived** (moved from
   section 3). A family **one unset env variable away from running** has not been
   measured. Producer live, declared, never configured at export time.
6. **Co-occurrence candidate expansion** (moved from section 4). Its one board
   number is **+0.0021 POSITIVE**, produced by `fuse_and_score.py` line 121,
   which is **literally the `rankpct` call** the registry elsewhere blames for
   manufacturing the 0.1255 baseline, **on both arms**. The true-frame cafaeval
   was never run. Argued against by a precision proxy only.
7. **8-PLM ensemble**: NONE-MEASURED. The METHOD_CARD carries no f_micro_w.
8. **`length_query`: partially observed, not dead** (corrected). NaN on 59-71% of
   rows in the LOFO export and 45% in the newer one, but **populated with 383 to
   1,694 distinct values elsewhere**; NaN **exactly when `knn_present == 0`**.
9. **Categoricals never enrolled**: `annotation_meta`, `plm_context`,
   `k_neighborhood`. AMENDED: an **out-of-contract `aspect_code` column IS
   enrolled in the per-cut PK model**, so it is a second signal outside the
   fingerprint alongside IA, and the schema-SHA guard cannot see it.
10. **`protst_text`**: a fourth declared-but-unenrolled family.
11. **`IA` itself**: computed, persisted, fed to boosters, **in no branch of
    `feature_schema`**.
12. **STRING as a reranker feature** (`string_partner_annotates_term` over the
    existing pool, no fill tax). Cheap, untried.
13. **Learned multi-layer mix on the production base.**
14. Prefilter-with-classifier-swap composition in the TRUE frame; sparse
    contrastive in the load-bearing form; per-aspect layer routing; the 8,195
    discarded `regulates` DAG edges; the t0-non-experimental trivial baseline.

## 6. INDISPENSABLE MECHANISMS

| Mechanism | Why it is load-bearing |
|---|---|
| **`-known groundtruth_PK_known.tsv` on PK cells ONLY** | Omitting it moves PK-BP 0.20132 -> 0.11666 (**-0.0847**). It SIGN-FLIPPED the headline lever (+0.02245 -> -0.01331). **The registry's best-supported claim and the template every weaker row should be held to** |
| **The temporal train/test gate** | Caught **THREE** in-window positives that fully reversed (transition, selective per-stratum, multi-PLM pool). **CORRECTED from four**: the fourth was caught by anchor reproduction, credited separately below, so counting it here double-credited this mechanism |
| **Per-category routing** | **NUMBER CORRECTED**: per-cell split 0.2017 vs **0.2177** (delta -0.016), and this is a **PK-BPO-only experiment whose own anchor precondition FAILED**. The 9-cell result: per-aspect splitting is **a wash on mean9 (+0.0008)**, and per-cell routing of per-category/per-aspect models gains. The blanket "per-cell splitting LOSES" (and the figure 0.2222, which belongs to a different receipt) is not what the board-frame receipt says |
| **`prop=fill` ancestor inheritance** | Free inherited ancestors arrive at weighted precision 0.2967 vs the arm's own 0.1801. WHY every low-precision channel floods |
| **cafaeval single global tau sweep** | The calibration wall itself |
| **PK pool restriction to `knn_present`** | **Sets the denominator of every PK number.** Removes 44% of PK rows |
| **Strict-union candidate merge** | The classifier can only ADD, never displace. This is WHY per-category routing works |
| **Ancestor-expansion ORDER** | Runs AFTER v6 enrichment so synthetic ancestor records inherit. Inverting it changes the feature distribution the booster trained on |
| **Classifier `top_n=100` / `min_score=0.01` suppression** | An **unswept cap** on the NK/LK recall ceiling |
| **Aspect-separated KNN** | Contract default `aspect_separated_knn=True` |
| **Leakage-clean pre-cutoff derivation of the NK/LK/PK category** | Without it the whole 9-cell frame is unsound |
| **`feature_schema_sha` guard** | Pins NAMES only: no types, no producers, no order, no values |
| **Anchor reproduction as a hard precondition** | Its ABSENCE produced two of the four big invalidations |
| **Row-alignment ASSERT instead of a dict join** | The dict join silently rewrote 71,574 of 863,748 rows (8.3%); duplicates differ by a MEDIAN of 3.60 |
| **10-fold disjoint-protein cross-fit gate** | **REWORDED**: produced **the PK-BP levers that survived**, each with a fold sd. It did NOT produce every surviving positive, and **the two largest claimed deltas (+0.0179 and +0.063) have no error bar at all** |
| **Shuffled-feature / fixed-score / random-order controls** | Demoted SSE's two apparent LK levers to noise |
| **Matched-volume + IA-precision** | A precision precondition is only checkable at matched volume |
| **Seed-averaging by convergence** | Classifier 0.343 -> 0.369 (3 seeds). **CURRENTLY DEAD IN SERVE, see section 7** |
| **Paired bootstrap CIs + declared noise floor (0.0034)** | What separates a result from a story |
| **Stratification by length x category x neighbour-identity** | Revealed the entire regime map |

## 7. DEFECTS (ranked; the first one gates everything above)

**0. THE GROUND TRUTH ITSELF IS TRUNCATED.** The v227->v230 ground truth this
entire registry is framed on rests on an eval set flagged truncated on
2026-07-27: **loaded -18.87% against an upstream GAF change of only -1.40%**,
eval set `6e41eb5b`. **Nothing in sections 1 to 6 is final until v230 is
reloaded.** This is a reason to preserve the procedure, not to prune.

**1. The lab artifacts backing the headline are UNTRACKED.** 30 untracked
entries under `results/`, 9 tracked. The lab README forbids committing model
binaries by policy, which means **the policy has no preservation path**.

A first archive pass was declared MITIGATED and **that claim was WRONG**: the tar
excluded `*.pt` and contained **zero checkpoints**, while the seven LIVE
two-tower heads existed in no tar, no dump and no repo. Without them two of the
seven won cells fall below board. Five further gaps were found and all are now
closed and md5-verified: `storage/two_tower_sparse/` (3.0G), `~/.secrets/`
(the operational definition of the deployed champion),
`storage/learned_encoders/`, the **`mlflow` database** (the cron dumps `protea`
ONLY), and MinIO `rerankers` + `eval_groundtruth` (the existing MinIO backup is
dated 2026-06-04 and predates the entire current frame). `datasets` (19G) and
`eval_artifacts` (25G) were deliberately NOT copied: derived results the clean
run regenerates.

**A claim of PRESERVATION is as dangerous as a claim of deletion.** "It is
saved" licenses the author to destroy the original. Never report an artifact as
backed up without reading it back OUT of the destination.
`LOCAL-ONLY-MANIFEST.txt` is an INVENTORY, not coverage, and must not be read as
a backup.

**2. Seed-averaging is silently dead in serve.**
`PROTEA_CLASSIFIER_SEED_DIR` points at a directory deleted on 2026-07-11.
**Cost ~0.01 (PARITY_AUDIT bounds it at up to 0.03), degrading NK and LK only,
not PK.** `PARITY_AUDIT.md` section 5 is itself now stale. **Fix template, taken
from the asymmetry with the two-tower: make `resolve_seed_paths` RAISE when the
env var is set but resolves to zero checkpoints.**

**3. The thesis has forked, and neither lineage survives whole.** The checkout is
on `thesis/validated-lafa-numbers-2026-07-02`; `origin/main` holds 7 commits it
lacks and it holds 5 that main lacks. **Verdict the draft withheld: merge
`origin/main` INTO the branch, keep the BRANCH's abstract (0.408 / 7-of-9, the
only framing matching the sealed 0.40765), and take MAIN's `defensa.tex`.** The
branch's `defensa.tex` asserts "CAFA #2" twice, violating the hard constraint
"CAFA 6 #19 (final ranking)", which alone forbids merging the branch over main.

**4. The feature contract is FORKED.** `origin/main` v6 = 78 features / 21
families; `origin/develop` v5 = 75 / 20. **No lint compares them**, so any
`ALL_FEATURES` digest differs by branch.

Corrected for the record: the two-tower SVD reproducibility blocker is **NOT
real** for the deployed artifacts. The frozen deterministic basis and saved
components exist; the memory claim was true only for the SUPERSEDED champion.

## 8. THE CLEAN TRAJECTORY

1. **Reload v230 first.** Defect 0 gates every number.
2. **Re-baseline the retrieval space.** Raw ProtST is +0.0305 (8/9) and the
   z-scored arm +0.0335 (9/9); the triple-combine is +0.044 pre-reranker. Every
   downstream number depends on the substrate. **But note the counter-evidence
   now in section 4: the learned k-WTA head does NOT transfer to ProtST**, so
   this is a base swap, not a recipe transplant.
3. **Keep four signal groups** into the reranker: the retrieval codes, the
   classifier (NK/LK) plus the two-tower (PK), the prior-knowledge trio
   (`association` + `anc2vec_query` + `lineage`, the last routed), and
   `go_context`. **REVISED from the draft: do NOT drop the homology block,
   emb_pca or interpro-as-feature.** All three are unmeasured, not refuted; the
   clean run is the occasion to measure them properly, once, with CIs.
4. **CRITICAL CORRECTION to the draft's "drop interpro"**: `knn_present` is
   declared INSIDE `FEATURE_FAMILIES['interpro']`, and it is the filter that
   **defines the PK evaluation denominator**. Dropping the family as declared
   would delete it. Either drop `interpro_hit..interpro_db_prosite` and KEEP
   `knn_present`, or move the two presence flags out of the family in
   `feature_schema.py` first.
5. **Restore seed-averaging in serve, or retire the parity claim.**
6. **Recompute the gain table on the same booster the LOFO used**, so gain and
   contribution stop being measured on different models.
7. **Measure the score-to-tree transversal** per cell.
8. **Report the refuted set as a characterisation of the calibration wall.**

## 9. THESIS RESTRUCTURE

- **Ch2 Biological Background**: KEEP nearly as is.
- **Ch1, Ch3**: rewrite the contribution list (omits the temporal dataset, the sparse retrieval encoder, the scale claim).
- **Ch4 + Ch5**: 52 pages, ~30% of the body, almost number-free. The argument-to-page distortion.
- **Ch6 Evaluation**: REWRITE. **Named blocker: the +0.1449 `anc2vec_query` contradiction is LIVE in two chapters and is the single largest number in the thesis that the 9-cell LOFO replaces.**
- **Ch7**: rewrite around surviving claims.
- **Appendix D**: 28 pages on retired frames. Cut or archive.
- **`defensa.tex`**: see defect 3.
- **MISSING ENTIRELY** (zero lines, receipts on disk): the learned k-WTA encoder, SSE plus the BP-frontier characterisation, the temporal-dataset contribution, the distributed/scale claim, the 9-cell LOFO regime map.
- Hard constraints: no em-dashes and no AI attribution are satisfied **in `chapters/` and `frontmatter/`**, which is what was checked. The branch `defensa.tex` violates the CAFA-6-#19 constraint.

## 10. OUTSTANDING WORK ON THIS DOCUMENT

- Attach a receipt path AND a frame descriptor to every row in sections 1 to 6.
- Recompute the gain table on the LOFO booster (see the governing lesson caveat).
- Re-measure the reranker delta and the classifier-alone swap WITH `-known`.
