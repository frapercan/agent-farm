# FRONTS

The research fronts of PROTEA: what each one asked, what it answered, where the
evidence lives today, and what would have to move into the platform for the
answer to be reborn as a row in a database rather than a sentence in a file.

Written 2026-09-02 by the `FRONTS` auditor, from the twelve slice reports in
this directory (`campaign-and-levers`, `lab-debt`, `lab-results`, `lab-state`,
`maps-and-residue`, `operational-and-findings`, `residue-verdict`,
`sparse-and-representation`, `temporal-and-sets`, `text-and-protst`,
`verdict-stores`, `walls`), each of which carries the per-claim receipts. Every
claim below cites a path. Where a claim rests on a document rather than on an
artifact, it says so.

---

## 0. What this is, and the two dates that decide everything

This is a census of fronts, not of numbers. A front is a question the project
opened, funded, and either closed, left open, abandoned, or never started. The
twelve sibling reports establish the numbers; this document establishes the
shape of the work and what happens to it next.

Two dates govern every row.

**2026-07-28, the operating-system reinstall.** The user account changed from
`frapercan` to `xaxi`, and `storage/` was nominally not restored. What died on
that date is everything that lived at an absolute path under the old home, in
`/tmp` (a tmpfs), or in a `storage/` subdirectory that nobody had committed.
What survived is what was in a git repository. The four `preserve:` commits of
2026-07-27 and 2026-07-28 rescued 434 files of procedure into
`repositories/protea-reranker-lab`, and they rescued them with the old
machine's absolute paths baked in, so what was preserved is the text of the
procedures and not the ability to run them:
`git grep -l 'home/frapercan'` returns 329 of 1,049 tracked files, 31.4 per cent
of that repository (`census/lab-state.md`).

Two corrections to the standing assumption. First, `storage/` is **not** empty:
it holds 369 GB, including 347 GB of per-residue embedding banks under
`storage/probe/`, 16 GB of encoder study under `storage/encoder-study/`, and
2.6 GB of a published encoder bundle under `storage/encoder/`
(`census/lab-results.md`, `census/walls.md`). Second, the archive partition the
recovery documents point at, `nvme1n1p5`, 391 GB, ext4, **is not mounted and has
no entry in `/etc/fstab`**, so a reboot will never bring it back
(`census/operational-and-findings.md` D1). Everything `FIRST-BOOT.md` names as
the recovery surface sits on it: the secret file that has no template in any
repository, every database dump, the object-store snapshot, the 144 archived
memory files, and `no-producer-artifacts/`.

**2026-08-27, the experiment registry wipe.** The live database holds 93
`evaluation_result` rows and 19 `prediction_set` rows, all created 2026-08-27 to
2026-08-30. Before the wipe there were 1,296 evaluation results
(`protea/core/operations/seal_evaluation_frames.py:6-9`), so **1,203 rows, 92.8
per cent of the evaluation record, are gone**. The deletion was deliberate and
reasoned: `D-09`, "The campaign's stored results are deleted, because they were
measured on the holdout", 2026-08-26, roughly 49 GB and 128,191,567 candidate
rows, taken because 594 of 1,296 results sat on the 220 to 230 union rather
than on either declared cohort and because preset, depth and representation had
been chosen with 65 to 71 per cent of decision weight reading the blind window.

**`D-09` is not in `plans/DECISION-LOG.md`.** The canonical decision store on
`origin/main` and on disk stops at `D-08` (2026-07-28). D-09 exists only on the
unmerged branch `plan/decision-wipe-the-campaign-results`, commit `28d555c`
(`census/maps-and-residue.md` FINDING 13). So the store whose own first
paragraph says "a decision that is not written here was not taken, it was
drifted into" contains no record of the largest deletion in the project's
history, and every staleness problem in this document is downstream of that one
unmerged file.

Three consequences that govern how to read the table.

1. **Any measured result dated before 2026-08-27 is not evidence about the
   current window**, however carefully measured. That retires, at a stroke, both
   verdict stores (`SIGNAL-REGISTRY.md` frozen 2026-07-27, `DECISION-LOG.md`
   frozen 2026-07-28), the entire 2026-08 encoder study (last artifact
   2026-08-26 16:49, one day before the wipe), and every number in
   `protea-reranker-lab` (newest commit 2026-08-17).
2. **Every UUID in every plan document is dead.** The post-reinstall annotation
   sets are 220 `cbb35a32`, 227 `ec9f5c2c`, 230 `9a14f9cc`; the plan store still
   carries 220 `1559d9f7`, 226 `5e1a7285`, 227 `c905dffa`, 230 `2394b9a1`.
   Zero overlap (`census/temporal-and-sets.md` Q1).
3. **Of the 93 surviving rows, at most 12 are both current-frame and
   undisputed.** 71 are declared non-comparable to any corrected run on four
   axes, one of which "moves without changing any recorded field"; five
   (`67fe2fa0`, `28621824`, `9de60449`, `53d68960`, `d0705d22`) are known-wrong,
   kept on purpose as the only measurement of their own defect, and sealed under
   the same frame digest `f-1c245d41f26ff70c3b0a9247` as the five corrected ones,
   with no supported way to mark them
   (`census/operational-and-findings.md` E1, E6). Any census that groups by
   frame digest is wrong by construction.

One more thing a reader must not miss before the table. **File modification
times in `agent-farm/plans/` are worthless.** Fifteen of twenty-four top-level
files carry `Jul 28 17:01` to the second, which is the moment the snapshot was
unpacked. Git is the only dating authority there, and it shows a spread from
2026-05-16 to 2026-09-02 (`census/maps-and-residue.md` FINDING 1). The whole
corpus reads as one cohort and is not one.

---

## 1. THE TABLE

`estado` uses a closed vocabulary: `cerrado-con-veredicto` (a verdict exists,
whether or not it is right), `abierto` (a live question with work still
attached), `abandonado` (worked on, then dropped, with no verdict), and
`nunca-empezado` (declared and never implemented). There is no "in progress".

Rows are sorted by whether the front still has evidence in the current window
(post 2026-08-27) first, then pre-wipe fronts whose evidence survives on disk,
then abandoned and never-started fronts last.

| frente | pregunta que hizo | estado | veredicto | donde vive la evidencia | que tiene que MOVERSE a la plataforma |
|---|---|---|---|---|---|
| **Neighbourhood depth (K)** | How many donors should a query transfer from? | cerrado-con-veredicto | Monotone, shallower is better, the winner is always the edge of the sweep, so there is no interior optimum and the true optimum lies below 2. Re-established after the wipe on the corrected donor policy, with coverage rising rather than falling, so it is not a precision-for-recall trade. Supersedes the pre-wipe "use 3 to 10", which counted depth in proteins rather than sequences and is a different unit. | `worktrees/protea-deploy/docs/incidents/2026-08-30-depth-series.md`; the five corrected rows `095b81eb`, `437b08a8`, `9f508370`, `3e1a47d8`, `aab5bfc6` | Nothing new to measure it: `run_cafa_evaluation` and `stratify_evaluation` exist. What is missing is a way to supersede a sealed `evaluation_result` (its five poisoned twins are unmarkable) and a `report_nine_cells` fixture: only five of the nine cells were ever published, and the commit message claims nine. |
| **The retrieval ceiling** | Is the missing performance a retrieval problem or a scoring problem? | abierto | Partly answered, and the earlier answer was wrong. "The whole gap is retrieval" does not survive: the retrieval-attributable gap is 17.9 points, not 36.8. The union of twelve arms reaches 77.9 per cent of new pairs, corrected upward from 55.8 when the ceiling was measured the way the scorer measures rather than by string match. One arm reaches 64.3, and its recall at the operating point is 0.22 to 0.61 across the nine cells. Zero of nine strata have a resolved winner among twelve arms. | `docs/incidents/2026-08-30-where-the-ceiling-comes-from.md`; `scripts/analysis/{ceiling.sql,carrier_signal.py,carrier_signal_propagated.py}` | `measure_candidate_recall`, writing per-cell ceiling rows. Also the analysis surface itself: `scripts/analysis/` was created 2026-09-01, is not an operation, reads three CSVs from `/tmp` that nothing persists, and hardcodes a laptop path (`/home/bioxaxi2/...`), so its own claim of reproducibility is false on this node. Four denominators for one measurement (56,816, 54,440, 53,605, 53,680) do not reconcile. |
| **Generation versus retrieval** | Can a generator (ontology entailment, sparse containment, frequency descent) produce candidates retrieval misses? | cerrado-con-veredicto | Provisional and self-labelled. Generation lands an order of magnitude below retrieval: `entail_kwta` 0.011 against an anchor of 0.144; sparse containment 0.016 against a deployed 0.196. The author states these are single measurements against a prior taken to decide whether to continue, not results-table numbers, and they are unstratified, hence roughly 95 per cent prior knowledge. | `docs/findings/2026-09-01-generation-lands-an-order-of-magnitude-below-retrieval.md`; branch `feat/subsumption-is-containment-in-a-sparse-code` tip `222b4a3` | Nothing new: two files landed on develop (PROTEA #919). What must move is the branch itself. 23 of its 25 files are reachable only through a ref deliberately not deleted, and a garbage collection takes them. |
| **Threshold calibration** | Does rescaling each protein's threshold to a fraction of its own maximum buy anything? | abierto | Measured once, post-wipe, on the campaign's own grids: targeted rescaling buys `f_micro_w` +0.015 to +0.047 on the NK cell (2,413 proteins), eight of nine panel-by-artifact cells with the interval excluding zero. Applied to all proteins it buys Fmax +0.022 to +0.069, nine of nine. **The two statistics disagree in direction**, which the study states as its result rather than discovering later. Controls that could have failed did: shuffled maximum, random targeting, fixed top-k. | `storage/calibration-study/` (README plus 95 scripts, `calib.json`, `calib2.json`, `pk13.csv`, `pk_all.csv`) | `fit_score_calibration` and `apply_score_calibration`, writing a `ScoreCalibration` row keyed by (prediction set, aspect, method). The rule exists as 95 loose scripts and is re-runnable only while the object store keeps `eval_artifacts/<id>/{NK,LK,PK}/per_protein_grid.parquet`; nothing is cached locally. |
| **Prediction-set hygiene and donor policy** | Does the declared donor policy govern what is actually donated? | cerrado-con-veredicto | It did not. On `a789582e`, 1,523,939 of 2,801,404 rows (54.4 per cent) were donated under evidence codes the set excludes; 133,866 rows self-donated under `exclude_self_neighbour: true`; 193,303 rows carry no donor ledger, written by a stale revision on this machine that reported success; the declared ontology snapshot is not the one its terms belong to. **1,300 no-knowledge (protein, aspect) cells were handed a prior from the protein's own IEA row**, in the panel that exists to measure prediction without a prior. | `docs/incidents/2026-08-29-prediction-set-a789582e.md`; PRs #890, #893, #896 | `audit_prediction_set`. The census is three hand-written SQL queries pasted into a markdown file. Also a running register of the accepted-recorded-inert class: three documents give three tallies (four, four, three) and the true count across the corpus is at least six. |
| **Ontology drift** | How much does the GO graph move between t0 and t1, and does that manufacture gained terms? | cerrado-con-veredicto | Net minus 5,807 edges and 2,756 terms retired, yet 8.67 per cent of common terms still grow their closure (BPO 10.01, MFO 6.27, CCO 6.03). Of the 2,756 retirements, 1,868 (67.8 per cent) have no successor at all. The net balance is the wrong statistic; growth is what bites. The annotation-weighted version is a named hole, not a measurement. | `storage/ontology-drift/{edge_drift.json,retired_exposure.json}` plus both OBO files, all on disk | `compare_ontology_snapshots`. `load_ontology_snapshot` exists and the DAG is in the database, so this is small. This is the one study in the whole census that is fully reproducible today, offline, with no card. |
| **The NOT / denial channel** | How often does the system predict a term a curator explicitly denied? | cerrado-con-veredicto | The verdict stands and the size of the correction is wrong in the repository. The fix shipped (`protea/core/operations/predict_go_terms/_denials.py`, PR #912). The published figure, a "2.5x understatement", compares denials against pairs, which are different objects; the real effect is 465 to 527 denials, plus 13 per cent. 1,190 pairs of 2,441,584 will not move a headline. The population is by construction curated, hence heavily prior knowledge. | `docs/findings/2026-08-30-what-a-curated-not-was-telling-us.md` (uncorrected); the retraction is at `agent-farm/plans/COLLIDING-A-NUMBER.md:55-58` and does not name the document it corrects | `audit_denial_violations`, keyed on (prediction set, annotation set, propagation policy). The fix is in the platform; the measurement is not. |
| **Selection order: per-residue top-k against pool-then-select** | Do selecting atoms per residue and then pooling commute with pooling then selecting, and does the first win? | cerrado-con-veredicto | **CONTRADICTED.** The +0.0251 reproduces exactly and is a Jaccard-denominator artefact: the numerator (true hits per neighbour, +0.2119) does not separate while the denominator falls 19.6 terms and does, so 95 per cent of the gain is the denominator. The screen is self-retrieval inside a 2,646-protein evaluation set with no donor bank at all, on a cohort that is 82.5 per cent prior knowledge with 140 NK proteins. On the recall ceiling of the actual kNN transfer the same arm loses by minus 0.0150 against the champion, minus 0.0083 with training exactly matched, and minus 0.0131 in the NK cell on the official 220 to 230 basis, all separating. | `census/residue-verdict.md`; `storage/encoder-study/{RESULTS.md,artifacts/eval_codes.npz,artifacts/architecture_on_task.json}`; `scripts/73_architecture_on_the_task.py` | An operation that scores an arbitrary encoder arm on a declared category-by-aspect cell against a declared donor bank, on Fmax, with the exclusion applied, writing an `evaluation_result`. Its absence is precisely why a metric with a denominator artefact ran 45 arms and reached the author as a headline. |
| **Base protein language model (backbone)** | Which base model should the retrieval space be built on? | abierto | The axis carries the effect and the leader had read the answer. Twilight-band spread 0.0842 across backbones, against 0.0006 for the order axis; remove ProtST, whose pretraining pairs sequences with Swiss-Prot function prose, and the spread falls to 0.0625. But the flagship 0.0842-against-0.0006 table compares a platform-produced number reaching 4.97 donors at budget 25 against a lab-produced one reaching 1.41, on two different banks, so the ratio is not a like-for-like. And one panel member (`esm2_t6_8M`) is measurably truncated at 2,048 residues, which is unflagged everywhere. | `storage/encoder-study/artifacts/{87_bands_full.json,89_arms.json,97_leak.json,98_spread.json,111_truncation.json}`; `census/lab-results.md` | The same evaluate-an-arm operation as the row above. Until a lab arm and a platform arm can travel through one retrieval path, no backbone number and no order number belong in the same table. Also `count_backend_parameters` exists and should be used to close the ESM-2 150M exclusion, which currently rests on prose. |
| **Layer depth** | Which transformer layer should the representation come from, and does mixing help? | cerrado-con-veredicto | Last layer wins, monotone in depth, no mid peak, and the penalty for a mid layer is largest in the twilight band. July's "mid layer wins" was the transform, not the depth: it compared a standardised layer 10 against a raw layer 48. Learned mixing weights converge monotone in depth (7.1 / 15.3 / 32.5 / 45.1 per cent) and lose 0.0028 to the last layer alone, which separates. | Memory store only; `storage/encoder-study/artifacts/99_layer38.json` and siblings | Nothing to decide. **But the substrate is gone**: `lafa_4layers.npy` and `pool60k_4layers.npy` were deleted, 304.9 GiB, and their index and provenance files remain. The bank whose own provenance says it supersedes the survivor is the one that is missing. Re-deriving means a fresh corpus pass. |
| **Quantisation of the sparse code** | How few bits can a published code carry? | cerrado-con-veredicto | Quantise after training, never during: quantisation-aware training is worse at 4, 2 and 1 bits. Four bits ship (240 bytes, minus 0.0001, zero of four identity bands separating). Two bits break: minus 0.0243, four of four bands separating, because 81.8 per cent of atoms round to zero. One bit measures free and is degenerate (8.4 donors tied at the cut). | `storage/encoder-study/PRODUCTION.md` addendum 2026-08-20; `storage/encoder-study/recipe/*.npz` | **A live defect, not a document defect.** `recipe/residue-sparse-k4-d2048-s128-mean.npz` still declares `"recommended": "2 bits"` in its own provenance. Anyone loading that recipe ships the one setting the same study measured as losing eighteen times the resolution floor. Re-stamp it. Then: a frozen-encoder artifact has no field the platform validates against a measurement; `load_frozen_encoder` checks declaration, not correctness. |
| **The learned sparse encoder ("+40 per cent")** | Does a learned k-WTA map over a pooled PLM vector beat dense mean-pooling? | cerrado-con-veredicto | Retracted in substance, never retracted in the plan store. The one measured quantity is a **held-out training loss**: Spearman against IC-weighted Lin, 0.168 to 0.530, and only the learned arm was ever given that target. It was produced by `scripts/run_sdr_c_contrastive.py`, not by the `encoder_ablation.py` that carries its name. The only concrete score pair ever published beside it (NK MFO 0.507 against 0.398) is +27.4 per cent, not +40, and it compares kNN-only against mean-plus-reranker, so two axes move at once. | `storage/encoder/{VALIDATION.json,MANIFEST.json,EMBEDDING_RECIPE.json}`; `plans/LEARNED-REPRESENTATION-ABLATION.md` (untracked until 2026-09-02, still not on main) | `fit_learned_encoder`. `apply_learned_encoder` exists, so the consumer is complete and the producer is missing. Also a `training_release` field checked at dispatch: `MANIFEST.json` already carries release 227, and nothing reads it. |
| **The reranker (per-category LightGBM)** | Does a learned fusion layer over the candidate pool help, and by how much? | cerrado-con-veredicto | Measured, and unreproducible on this machine. +0.1353 per-cell mean and +0.1083 for the frame-safe NK and LK half both reproduce exactly from the primary table. The PK part is +0.1894, 1.75 times the safe part, supplying 46.7 per cent of the headline from 33 per cent of the cells. The same run has a second published mean, +0.1828 pooled per aspect, which the file itself calls the deployment metric. Its own leakage check recorded a 7.4 per cent train/eval positive-pair overlap and wrote its verdict to a `/tmp` scratchpad. | `repositories/protea-reranker-lab/results/clean_227230/SUMMARY.md`; the inputs it read are gone | `train_reranker`. `reranker_model` has **0 rows**; no trained booster of any generation exists anywhere on this machine. The `RerankerModel` table already has the shape (`external_source`, `feature_schema_sha`, `dataset_id`, metrics); only the producer is missing, and its removal was a decision recorded in `operation_catalog.py:120-124`. |
| **The prior-knowledge / BP wall** | Is the wall a representation limit, an evidence limit, or a ranking limit? | cerrado-con-veredicto | **Ranking, and it always was.** The founding number of the generation-wall story, a PK-BP recall ceiling of 0.319, "appears in no receipt anywhere" (a negative check reproduced independently in this census). The corrected ceiling is 0.54 to 0.75 against a delivered 0.2131. Every lever the old headline commissioned was a generation lever and every one came back inert: "we were pushing a door that was already open". | `plans/prior-knowledge-wall/PLAN.md`; `thesis/chapters/06_evaluation.tex:843` (corrected 2026-07-16/17) | Nothing new for the verdict. `measure_candidate_recall` would make the ceiling a row instead of a lost JSON: the receipt the retraction cites (`p4_recall_ceiling.json`, n=4402) does not exist anywhere on this machine and never appears in the lab's git history. |
| **Text-aligned representation (ProtST, ProTrek)** | Does a model trained on sequence-plus-text beat a sequence-only backbone as a retrieval space? | cerrado-con-veredicto | Closed as leakage, and the verdict store still recommends the opposite. The advantage is substantially UniProt text exposure. On the NK cell split by whether UniProt carries a FUNCTION comment, the paired intervals separate on the described side and mostly collapse on the undescribed side. **But the received "0 of 9 among the undescribed" is refuted by its own receipt**, which prints nine rows: the ninth (ankh-base) separates at +0.0561 with interval [+0.037, +0.076]. The honest count is 8 of 9 collapsing, and the interaction was never bootstrapped. | `storage/encoder-study/artifacts/{97_leak.json,97_leak.log,97_run.out}`; `repositories/protea-reranker-lab/research/regen_headline/protst_repr/REPR_RESULT.md` | An operation reporting, for a constructed evaluation set, the fraction of each knowledge cell carrying `protein_uniprot_metadata.function_cc`. **It is one COUNT, and its absence let a false leakage clearance stand for 46 days across six documents.** Also `screen_retrieval_space`, since the +0.0335 headline's cited receipt does not exist on this disk. |
| **Temporal frame, windows and splits** | Which window is the comparable one, and which split may inform which decision? | abierto | Unresolved and live. `split_registry.COMPARABLE_WINDOW` computes to v226 to v227, the window *ending* at the board's mark; five independent records including `band_registry.py:131-135` in the same directory say the board's window *starts* at v227 and runs to v230. `band_registry` is the only one of the two any production code imports. The adjustment menu is empty by construction, `menu_is_sufficient()` is False, and two of three splits are undecided, so no champion can currently be selected legally. | `worktrees/protea-deploy/protea/core/{split_registry.py,band_registry.py}`; `census/temporal-and-sets.md` | Read the board's current release directory and fix whichever registry is wrong. Then wire one of them: **`split_registry` has zero production importers**, and so does `first_appearance`. A two-line validator parsing `evaluation_result.temporal_window` and calling `release()` on both ends would make this class of drift impossible; the column is free text, `String(32)`, nullable, with no default and no check. |
| **Ground truth from additions, never a net delta (D-02)** | Should an annotation count as ground truth only if it was never present at any earlier cut? | cerrado-con-veredicto | Decided and inert. Decided 2026-07-28, implemented in `protea/core/first_appearance.py`, tested, and **never wired**. The live path still computes `delta_ns = new_ns - old_ns` at `protea/core/evaluation.py:342`, the pairwise difference the decision retired; for NK it does not even do that (`nk[protein] = new_all`). The 63.7 per cent that justified the rule is an all-evidence maximum over eleven release dumps with no breakdown anywhere; on experimental evidence, the operating regime, the rate is "about one per cent" and that figure has no receipt either. | `plans/DECISION-LOG.md:102-108`; `protea/core/first_appearance.py`; `protea/core/evaluation.py:342` | `generate_evaluation_set` taking a release HISTORY rather than an (old, new) pair. Its payload cannot express a history. Then `restoration_report`, which exists as a pure function with no caller, becomes the per-release decomposition Stage 0 of `E2E-CANONICAL-RUN.md` gates the whole campaign on. |
| **Candidate generation channels** | Can co-occurrence, SSE, phylogenetic profiling, cross-modality consensus, annotation-space RAG, literature, ProtEx, DeepGO-SE or a multi-PLM union add candidates the retrieval stage misses? | cerrado-con-veredicto | Closed, and several of the closures are unsound. Twenty-eight entries sit in `SIGNAL-REGISTRY` section 4, "REFUTED (measured, negative, closed)". By the registry's own two tests, **nine more belong in section 5** and three were never measured at all: SSE Mode A ties its own random-order control to four decimals in all three PK cells; SSE Mode B is four ties and two positives killed by a shuffled control, with no measured negative anywhere; ProtEx is +0.0028 and +0.0071 with intervals spanning zero; phylogenetic profiling's selected arm is three to four times inside the declared noise floor on 15.9 per cent keying coverage; annotation-space RAG separates from the random control eight times more strongly than the arm the registry rescued. The modal population is {LK-BPO, PK-BPO}, two cells of nine, neither of them the served one. | `repositories/protea-reranker-lab/research/regen_headline/*.md`; `census/verdict-stores.md` master inventory | `screen_generation_channel(channel, k, cell)` with the random-score, shuffled-feature and matched-volume controls as first-class arms, writing one row per (channel, k, cell) with its interval. The best controls in the corpus live inside single loose scripts. |
| **Corpus scale and in-domain data** | Does more training data buy retrieval quality, and does domain matter more than volume? | cerrado-con-veredicto | Corpus size does not saturate, and budget and domain are multiplicative. In-domain data is 4.3 times steeper than the pool, but only 21,399 clean delta proteins exist; the axis is closed by arithmetic, because catching an in-domain fit needs 3.7 million proteins. On the served population four times the data buys +0.0037. | Memory store; `storage/encoder-study/artifacts/` | Nothing. The verdict is arithmetic and the arithmetic survives. |
| **The interface (FR-1: every operation UI-actionable)** | Can an operator dispatch the registry from the instrument? | abierto | Unmet by a factor of four and worse than recorded. The registry declares 39 operations; the web app dispatches nine hardcoded string literals, with a tenth appearing only in end-to-end mocks. **Thirty operations are dispatchable and not UI-actionable**, twenty-two of them after removing the plausibly internal ones, against the plan's "six drifted out". The interface documents its own gap in prose: `StrataPanel.tsx:254` tells the operator to run an operation the interface cannot run. | `worktrees/protea-deploy/protea/core/operation_catalog.py`; `apps/web/` | The registry-to-UI coverage test. It is three lines (import the registry, scan `apps/web`, assert) and it currently fails thirty ways. It is the literal acceptance criterion of FR-1. |
| **Two-tower sparse classifier (the prior-knowledge generator)** | Can a learned protein tower and GO tower generate candidates the neighbours miss? | abandonado | **The arm whose result stood and was shelved.** Merged opt-in and default off on 2026-06-29 and untouched since; `PROTEA_CLASSIFIER_IMPL` defaults to the M2 head. Its recall@100 numbers (NK 0.678 / LK 0.716 / PK 0.376) have no surviving receipt. The single independent test ever run on it missed a pre-declared threshold of 290 with a mean rank of 9,378 of 29,027, but paired the heads with a different protein tower than the one they were trained on, so it reads "signal is real, correspondence is not". | `storage/encoder-study/artifacts/107_atoms.json`, `108_published.json`; `plans/sparse-classifier/RESULTS.md` (tracked, receipts gone) | `build_go_text_embeddings`, `build_go_sparse_codes`, `build_two_tower_prep`, `train_two_tower_head`. `prep.npz` is consumed by six scripts and written by none, which is the artifact-without-a-producer the campaign invariant forbids, caught red-handed by its own publish script. The GO side survives only because a preserve partition was hand-mounted on 2026-08-24; the seven trained heads were never uploaded and live on the partition that is unmounted today. |
| **beat-lafa-1 levers L1 to L7** | Which post-processing and feature levers close the gap to LAFA #1? | abandonado | **Six of seven were never run.** Only L2 (soft Pmin/Pmax) executed, and it was refuted (minus 0.0026 on the official recipe, PK reversing from +0.0141 to minus 0.0126). L1, L3, L4, L5 and L6 have no implementation anywhere on this machine. The campaign's own highest-value lever, L6 (retrieved hard negatives), died on 2026-06-23 not on a result but on an unsent keystroke, recorded only in `agent-farm/observability/OBSERVATIONS.md:224`. | `plans/beat-lafa-1/{PLAN.md,CAMPAIGN-DOSSIER.md}`; `agent-farm/observability/OBSERVATIONS.md` | For L6, a real platform gap the dossier names: the export aggregates the per-neighbour rows the feature is defined on. For L3, the same seam as L2, which already exists as the opt-in `softprop` flag in `run_cafa_evaluation`. And the whole campaign is unmeasurable regardless: the 7,401-target query FASTA is gone and `protea-predict` requires `--query_file`. |
| **The meta-reranker (MR-0 to MR-5)** | Does a stacked scorer registry with a trained per-category combiner beat the monolithic booster? | abandonado | MR-0 and MR-1 landed on 2026-06-17 with ten scorer adapters and 400 lines of tests. **MR-2, the trained combiner that the architecture document calls "the single change that flips monolith to stacked", never landed**: both combiners on disk have literal no-op `fit()` methods. And nothing outside the module and its own tests imports any of it, verified across the whole 2026-09-01 tree. `CATALOG.md:17` lists the architecture as "ACTIVE, live reference". It is not live. | `worktrees/protea-deploy/protea/core/reranking/`; `plans/meta-reranker/ARCHITECTURE.md` | MR-2 itself: a training operation fitting a per-category combiner on out-of-fold scorer outputs and writing a sealed artifact, plus a serving path resolving scorers through `ScorerRegistry`. `reranker_model` holding 0 rows is the same fact from the database side. |
| **Structural gate (AlphaFold DB, FoldSeek 3Di)** | Does structural similarity retrieve functional neighbours that sequence misses, and does it help BP? | abandonado | A real FoldSeek run happened between 2026-06-30 and 2026-07-08, proved only by the tool's own auto-generated temp workflow scripts. Its number (66.6 per cent MF against 20.7 per cent BP, residual 0.545) is single-source, frame-less, population-less, covers no CCO, and is a retrieval hit-rate presented in a column of board-faithful `f_micro_w` deltas. Its named receipt does not exist on this filesystem. The lab itself called it "the earlier **qualitative** structural gate argument" on 2026-07-16; the registry filed it eleven days later under "REFUTED (measured, negative, closed)". | `plans/thesis-pillars/PILLARS.md:95`; `repositories/protea-reranker-lab/research/struct_gate/` (three FoldSeek temp scripts, no analysis code) | An AlphaFold-fetch plus FoldSeek-3Di backend operation writing donor hits, specified as Phase D of `DESIGN-cross-encoder.md` and never built. There is no FoldSeek binary, no structure database and no 3Di file anywhere on this disk, and the target database of the one run performed is not recoverable from what survives. |
| **Native target selection** | Should the native pipeline restrict to a target universe before classifying NK / LK / PK? | abandonado | The measurement is sound and internally consistent: official 7,401 against native 8,725, intersection 7,347, native-only 1,378, official-only 54, and the table closes exactly. The mechanism is identified (LAFA intersects targets before classifying ground truth; `compute_evaluation_data_reconciled` has no such restriction). **T3, the platform change, never landed**, and therefore neither did T4 or T5: `compute_evaluation_data_reconciled` still takes no target-universe parameter on the 2026-09-01 tree. | `plans/target-selection-native/PLAN.md`; `protea/core/evaluation.py:596` | A target-universe filter on `generate_evaluation_set`, applied before NK/LK/PK classification. Until then the reported native number is on 7,401 only because the evaluation set was externally imported: the native pipeline still produces 8,725 and would regress the frame. |
| **Cross-OBO native delta (the phantom gap)** | Does propagating t0 under the t1 ontology manufacture new knowledge? | abandonado | Diagnosed and specified, never executed on the campaign's window. The plan's own GATE 2 target frame verifies exactly against the files on disk (7,401 targets; NK 399 / LK 868 / PK 6,340, counted here), with one thing the plan does not say: the three buckets are not a partition, LK and PK overlap by 206 proteins, so summing them gives 7,607. All of the root-cause trace has no artifact on this disk, and the t1 OBO `releases/2026-01-23` is not here. | `plans/crossobo-native-delta/PLAN.md`; `CAFA_forever/data/releases/Sep_2025_Mar_2026/` | The plan's own A1, A2, A3 chain (`load_ontology_snapshot`, `generate_evaluation_set` with an explicitly different pivot, `run_cafa_evaluation`) is one of the few places where the platform path is already written down. It is blocked on ingesting a contemporary OBO, and for the campaign's 220 window that ingestion is still outstanding five weeks later. |
| **InterPro and domain signatures** | Do domain architecture features add anything? | abandonado | Dead in the current window on three counts at once: `interpro_go_mapping` is EMPTY, so the feature code has nothing to read; there is no InterProScan installer anywhere (50 GB acquired by hand, version pinned only inside the plan store); and the graft was measured actively harmful on BP (0.140 against 0.218). The three registered operations that consume it are green because they have nothing to fail on. | `docs/findings/2026-08-30-what-the-direct-method-has-to-get-right.md`; `research/regen_headline/BP_WALL_CHARACTERIZATION.md:49` | An installer with a pinned version and a checksum, then `load_interpro_go_mapping`. All three operations already exist; nothing has fed them. |
| **GO-text label basis and GO-DAG label encoder** | Do term text and ontology structure help on the label side? | abandonado | Abandoned and mis-filed. Both sit in `SIGNAL-REGISTRY` section 4, titled "measured, **negative**, closed". The GO-text BioBERT label basis measured **+0.012 POSITIVE on LK-BPO**, 3.5 times the registry's declared noise floor, and the thesis uses it as the mechanism of its fourth pillar. The GCN label encoder was refuted on AUC 0.5501, a statistic the registry itself bans four lines earlier, measured on a hand-built DAG-proximity scalar that is not a GCN. The project's own plan already drew the right conclusion: "our negatives do not refute the signal, they refute the bolt-on". | `plans/prior-knowledge-wall/PLAN.md:133-144`; `plans/thesis-pillars/PILLARS.md:94` | `screen_label_basis(basis, cell)` emitting `f_micro_w` per cell, so that three bolt-on ablations become comparable to each other and to the joint model they are standing in for. |
| **Per-release additions and removals decomposition** | How much does each GOA release add and remove, and where are the contractions? | nunca-empezado | Neither side has it. The closest artifact is a two-window additions-only `EXCEPT` count, and **its own three numbers imply the removals it never computes**: 5,902,876 + 125,026 minus 4,767,114 gives 1,260,788 removed against 125,026 added, a factor of 10.1, on all evidence. Distinct proteins fall only 0.63 per cent while pairs fall 19.2 per cent, so the contraction is annotations stripped from proteins that remain. | `repositories/protea-reranker-lab/experiments/lafa_ia_v227_protocol/band_shift.json` | `decompose_release_deltas` writing a new `release_delta` table. LOW to MEDIUM difficulty, and it is **the Stage 0 gate**: `E2E-CANONICAL-RUN.md` says "nothing measured before this counts", and `split_registry.py:267-275` refuses to name the adjustment windows without it, in code, at runtime. |
| **DAG scheduler** | Should the farm schedule by dependency frontier rather than by loop? | nunca-empezado | All seven F-SCHED slices `pending`, one `deferred`, one commit ever (2026-06-22). None of `find_frontier`, `lease_registry`, `node_registry`, `quarantined` exists. The handoff document is a prompt to paste into a live session and whether it was ever pasted is unrecoverable; the plan's own status fields say no. | `plans/dag-scheduler/{PLAN.md,HANDOFF.md}` | Everything. It is the backlog item the memory store already carries as a scheduler redesign. |
| **Donor-recency weighting, M3 IEA pretraining, SVD label embedding** | (three levers named in the refuted list) | nunca-empezado | **No trace of any measurement.** "donor-recency weighting" appears exactly once in the whole project, in the registry line that refutes it. "M3 IEA pretraining" is a milestone from `archive/lafa-number-one/NEURAL-HEAD.md`, a document superseded the day after its only outcome section was written, with M1 to M4 carrying no outcome at all. "SVD label embedding" appears under that name nowhere else; the nearest real object is the two-tower's SVD basis, which is recorded as a preservation failure, not a negative result. | `plans/SIGNAL-REGISTRY.md:129-130`; `census/verdict-stores.md` | Nothing, until someone decides they are worth running. They occupy REFUTED slots, which means the project will not fund them again, on the strength of a single occurrence of their own names. |

---

## 2. WHAT WAS DEDUCED AND COUNTED AS MEASURED

This is the section the project owner asked for, and it is the most valuable
output of the census. Each case is a claim that arrived by reasoning from a
definition, a policy, a file size, or another study's noise floor, and that was
later read as a measurement in a document, in shipped code, or in the thesis.
Ordered by what depends on it.

`COLLIDING-A-NUMBER.md` rule 3 is the rule these break: "a deduction from a
definition is not a measurement", and "a correct definition can group two
distinct things".

### 2.1 "NK proteins had no function text at t0", the clearance that authorised the whole text programme

**The deduction.** `agent-farm/plans/text-evidence-scorer/PLAN.md`, written
2026-07-08 (git `cc8eacc`), section "Leakage position (the corrected argument)":
"NK proteins had **no function text at t0**, fully clean, zero asymmetry (the
strongest, primary result cell)", and in the candidate table, for both
ProtST-ESM2 and ProTrek-650M: "NK fully clean (no function text existed)". No
citation, no query, no count. It infers from what NK MEANS (no experimental
evidence) to what UniProt CONTAINS (no prose). Those are facts about different
columns.

**Where it was cited as measured.** Six documents, two of which claim the
premise is auditable:
`memory/project_text_evidence_scorer_2026_07_08.md:20`;
`research/text_scorer/WRITEUP.md` Protocol and Result 1 ("nk-BPO +0.062,
leakage-free"); `research/regen_headline/protst_ab/AB_RESULT.md`, which makes it
the load-bearing sentence of the whole A/B: "the leakage-free NK-BPO anchor
moves the SAME direction and by the MOST, so **the lift is the ProtST TEXT
signal, not leakage**"; `plans/thesis-clean-iteration/SIGNAL-STORE.md`, which
records the premise as the thing to make "explicit and auditable, not tribal
knowledge"; and `plans/thesis-pillars/PILLARS.md`, which carries the
+0.062 / +0.072 figures forward into a thesis pillar without the qualifier.

**Measured, 46 days later, and false.**
`storage/encoder-study/artifacts/97_leak.log` line 2: "NK con comentario
FUNCTION en UniProt: **2481 de 3031 (81.9%)**". The producing SQL is
unambiguous, a count over `protein_uniprot_metadata.function_cc`.

**Consequence.** The anti-leakage control of the ProtST A/B does not control.
"Largest on NK" is exactly what ProtDescribe-style text exposure predicts. The
count that refutes the premise exists in one place and was never propagated back
into any of the six documents. Everything downstream inherits it: the +0.0335
retrieval screen, the reranker A/B, and the registry's number-one unexploited
lever.

**The check that would have caught it is one COUNT.** There is no operation that
reports text availability by knowledge category at set-construction time, which
is why a plan could declare a cell clean and nobody could contradict it for six
weeks.

### 2.2 "PK is precision-limited, not recall-limited: coverage 1.0", the diagnosis that ordered the entire campaign

**The deduction.** `plans/beat-lafa-1/PLAN.md:12-17`: "At PK's Fmax operating
point: recall ~0.25, precision ~0.15, **coverage 1.0**. NOT a
candidate-pool/recall ceiling, so the pool has plenty of candidates; PK ranks too
many plausible-but-FALSE terms high." Restated as durable learning at
`CAMPAIGN-DOSSIER.md:150-152`. Every one of the seven levers L1 to L7 was
prioritised by this sentence.

**Why it is a deduction and not a readback.** On 2026-06-21 the platform could
not publish coverage at the Fmax operating point at all. It stored `cov_max`,
the maximum of coverage over every threshold, under the name `coverage`, beside
`n` read from the best-tau row. The test that fixes it says so in its own
docstring: `worktrees/protea-deploy/tests/test_coverage_at_operating_point.py:1-15`,
added by `078586a`, PROTEA #804, **2026-08-20**, two months later. Its worked
example is `cov_max = 1.0` against `coverage_at_tau = 0.83`. A maximum over all
thresholds is 1.0 for essentially any predictor that emits anything at a low
enough threshold.

**Where the pair probably came from, and it is one cell of nine.** The
(recall, precision) pair reconciles with ADR-008's PK-**BPO** row on the
**220 to 230** benchmark in **Fmax**: precision 0.157, implied recall 0.2487
before the fix and 0.2680 after, coverage **0.97**. Reading it as the whole PK
category is a nine-populations violation (the same ADR shows PK-CCO at 0.366 and
PK-MFO at 0.291); reading it on the 227 to 230 LAFA frame the campaign was
optimising is a window error; reading Fmax where the ledger reports `f_micro_w`
is one of the four things called F; and 0.97 rounded to 1.0 is the step that
turns a diagnosis into a premise.

**Consequence, and its direction.** True coverage at tau is at most 1.0, so the
pool ceiling was UNDER-suspected, in the direction that would have made a recall
lever more attractive and the discriminative levers less so. Six of the seven
levers were never run, so the diagnosis is untested in both directions. It is
now cheap to settle: `parse_results` publishes `coverage_at_tau`
(`protea/core/operations/_run_cafa_artifacts.py:741`) and it is surfaced on
`/graph`.

### 2.3 "The corpus contracts by roughly 30 per cent twice", which is an HTTP HEAD on a gzip file

**The deduction.** `memory/project_goa_not_monotone_two_contractions_2026_07_27.md`:
"Verified 2026-07-27 by HTTP HEAD on
`https://ftp.ebi.ac.uk/.../goa_uniprot_all.gaf.<v>.gz`", with a nine-row table
whose column is literally headed "gaf.gz size". No GAF was downloaded, no line
was counted, no annotation was parsed. **The source labels itself**: "Size is a
PROXY. Bytes are not annotation counts; the decomposition is the real
measurement. **This table is the alarm, not the evidence.**"
`E2E-CANONICAL-RUN.md:128-131` keeps the caveat.

**Where it was cited as measured.** Eleven hours later, in shipped code, with the
caveat dropped:
`worktrees/protea-deploy/protea/core/first_appearance.py:7-9` ("It has lost
roughly thirty percent of its volume twice in the release history this campaign
spans", stated flatly) and `protea/core/split_registry.py:270-274`, where it is
**one of the two stated reasons the adjustment split cannot be decided**, and
therefore why `adjustment_candidates()` returns an empty tuple and no champion
can legally be selected. Repeated again at `split_registry.py:350-352`.

**Why the proxy is worse than it looks.** A gzip size drop is a proxy of a
proxy: compressed bytes move with content redundancy, so a release bundling
fewer source databases can shrink far more, or far less, than its annotation
count does. Cumulative v226 to v234 is minus 48.53 per cent, a stronger and
stranger fact than "two contractions" and one nobody has stated.

**What the real number probably is.** From `band_shift.json`, on the same
corpus: removals 1,260,788 against additions 125,026 over v226 to v230, a factor
of 10.1, with distinct proteins falling only 0.63 per cent. The decomposition is
one subtraction away from a file that already exists and nobody did it.

### 2.4 "63.7 per cent of apparent additions had been seen before", the number that retired the ground-truth rule

**The deduction, or at least the orphan.** `DECISION-LOG.md:102-108`, D-02:
"A probe over eleven consecutive release **dumps** found that on all-evidence
data as much as 63.7% of apparent additions had been seen before. On
experimental evidence, about one percent... the leak tracks the contraction
points, and the validation window crosses one."

**Where it was cited as measured.** Five places, all the same sentence:
`CAMPAIGN.md:172`, `DECISION-LOG.md:103`,
`protea/core/first_appearance.py:14-19`, `protea/core/split_registry.py:383-388`,
plus the duplicate agent-farm checkout. Two of the five are shipped code that
reads it as settled.

**What is missing.** No probe script, no output, no per-release table, anywhere
on this disk (searched across `storage/` 369 GB, `agent-farm/`, all eight
repositories, and the memory store). "As much as 63.7 per cent" is a MAXIMUM,
not a rate, and the claim that actually carries the decision is the
non-uniformity ("one percent would be tolerable if it were uniform, and it is
not"), which is exactly the part no breakdown exists to check. Eleven
consecutive releases is also a history the current registry cannot express: it
holds nine, and only four are loaded.

**Standing.** The RULE is well founded independently of the number, and
`first_appearance.py` implements it correctly and refuses to fall back silently.
What is deduced is the size of the problem it solves.

### 2.5 The structural gate, 66.6 / 20.7 / 0.545: a qualitative argument upgraded to a refutation

**The chain, in five dated steps.** 2026-06-30, the whole `bp-structural-lever`
directory says structure "is entirely absent (no FoldSeek 3Di, no AFDB;
UniProt to AFDB not mapped)" and hands the decision back to the author. Between
then and 2026-07-08 a real FoldSeek run happened, proved only by its own
auto-generated temp workflow scripts at
`repositories/protea-reranker-lab/research/struct_gate/tmp/`. 2026-07-08/09,
`plans/thesis-pillars/PILLARS.md:95` quotes "residual 0.545; a clean positive
control finds the true functional neighbour 66.6% of the time for MF vs 20.7%
for BP", citing memory `project_structural_gate_bp_wall_2026_07_07` at line 154.
2026-07-16, the lab's own successor receipt calls it "the earlier
**qualitative** structural gate argument"
(`research/regen_headline/BP_WALL_CHARACTERIZATION.md:5`). 2026-07-27,
`SIGNAL-REGISTRY.md:125` files it under "REFUTED (**measured**, negative,
closed)", with the number, the frame, the population and the receipt all
dropped.

**The deduction underneath.** The mechanism sentence, "structure conserves
molecular function not biological process", is a textbook proposition, and the
lab's own literature synthesis supplies exactly that argument from the
literature with no PROTEA run behind it. There is also a homonym doing work:
`BP_SOTA_RESEARCH.md` calls the BP wall "a recognized STRUCTURAL fact", meaning
a structural feature of the problem, not protein 3D structure.

**Standing today.** The cited memory file does not exist anywhere on this
filesystem; the archive that would hold it is an unmounted directory; the
numbers appear in no thesis file; and the consolidated 2026-07-22 Pillar-4
memory, which enumerates roughly fifteen tested channels, does not list
structure among them. **The registry's classification is the defect.** Do not
cite 66.6 / 20.7 / 0.545.

### 2.6 "+40 per cent": a held-out training loss re-narrated as a score lever

**The deduction, and it is a substitution.** The one measured quantity is a
held-out Spearman against IC-weighted Lin similarity, 0.1675 raw, 0.5299 dense,
0.4671 at top-128, on 4,000 held-out proteins and 120,000 pairs
(`storage/encoder/VALIDATION.json`). **Spearman against Lin is the training
objective**, and only the learned arm was ever given that target; `dense` and
`pca256` were not. The numbers came from `scripts/run_sdr_c_contrastive.py`, not
from the `encoder_ablation.py` that carries their name, so the method card and
the ablation module are two experiments wearing one name.

**Where it was cited as measured.** Seven documents:
`plans/roadmap-from-zero/PLAN.md` three times ("validated +40% reranked on a
consistent frame"), `plans/representation-science/PLAN.md:31` ("The +40% lever
is real on f_micro_w, not just proxy"), `plans/sparse-classifier/PLAN.md:7`,
`plans/thesis-clean-iteration/PLAN.md:87`, and two lab files.

**The second number.** The only concrete pair ever published beside it is
NK MFO 0.507 against 0.398, which is +27.4 per cent, not +40, and it compares
kNN-only against mean-plus-reranker, so two axes move at once. Its primary
receipt, memory `project_validation_findings_2026_06_25`, is not among the 210
memory files here; it was archived to the partition that is unmounted.

**And the substrate is wrong in every document that reasons about it.** The
plan that opens "On mean-pooled **esm2_150m** vectors, a single affine map from
**640** dimensions" is describing a run that did not produce the number:
`MANIFEST.json` says `in_dim: 768`, `EMBEDDING_RECIPE.json` says
`ElnaggarLab/ankh-base`, and `encoder.pt` is 6,301,669 bytes, which is
768 x 2048 + 2048 float32 plus a header and is not 640 x 2048 + 2048. Three
independent routes to the same correction. That voids the plan's entire
substrate ladder and its pre-registered interaction contrast.

### 2.7 "Retrieval converts to Fmax at slope about 1, and there is no dead stretch"

**The deduction.** A line drawn from where the system is to where an
answer-reading oracle is. Refitting `artifacts/conversion_curve.json` directly:
median slope **0.9482** with the oracle included, which reproduces the published
0.94 exactly, and **0.7447** without it, with per-cell values running from
minus 0.063 to plus 1.557. The four real arms span 0.006 to 0.030 of neighbour
quality; the oracle sits 0.28 to 0.50 away. All the leverage is the oracle.

**Where it was cited as measured.** `DEPLOYMENT-AUDIT.md:22`,
`CAMPAIGN-LADDER.md:53`, `PRODUCTION.md:110`, and memory
`project_retrieval_converts_at_slope_one_2026_08_19` whose own description says
"so there is NO dead stretch". **The producing script's docstring says the
opposite of the conclusion it is cited for**: `32_conversion_curve.py:4-7`
asserts the conversion "is not a ceiling, it is a curve with a dead stretch at
the near end, and the useful question is where that stretch ends". Same run,
opposite conclusions, both on disk.

**Consequence.** The rung gate "the gain needed is 0.024 to 0.037" is one over
the slope times a target Fmax delta, so it is an oracle-anchored quantity
presented as a measured requirement. And on the four real arms alone, three of
nine cells have a near-range slope under 0.3, which is what a dead stretch looks
like.

### 2.8 "The NK and LK half of the reranker delta is frame-safe"

**The deduction.** `SIGNAL-REGISTRY.md:71` warns correctly that the +0.1353
headline is a no-`-known`, `max_terms=500` frame in which the PK cells carry the
largest deltas, and then says "the NK/LK-only delta from the same table is
+0.108 and **IS frame-safe**". The reasoning is: NK means no experimental
annotation in any aspect, LK means experimental in some other aspect but not
this one, therefore the within-aspect known set is empty and `-known` is a
no-op there.

**Why it needs colliding.** There is an independent second source that agrees in
principle (`project_board_frame_reconstructed_2026_07_18`, "the exclusion list
applies to prior-knowledge cells ONLY"), and nobody has run the exclusion on NK
and LK and shown the delta is zero. The minimal case that would separate it is
cheap: run the same scoring with `-known` on and read the NK and LK cells. It
has not been run.

**What is measured, and reproduces exactly**: the frame-safe part is +0.1083,
the PK part +0.1894, and PK supplies 46.7 per cent of the headline from 33 per
cent of the cells.

### 2.9 "The minimum cell population for inference is 129 proteins"

**The deduction, three steps from one line of another study.**
`plans/ABLATION-ARCHITECTURE.md` section 1 gates the whole plan on this floor
and writes it as 129 "because a rounded floor invites the question of where the
rounding came from and a derived one does not". The chain reproduces exactly:
take `SIGNAL-REGISTRY.md:100`'s "+0.0092 sd 0.0034" from a prefilter-threshold
study, assume 0.0034 is the sd of a fold-level mean and that a fold is a tenth
of the cohort, get sigma_d = 0.0810, then n = 128.7. The nine-panel minimum
detectable effect table reproduces to the last digit.

**Why every input fails.** (a) 0.0034 is a between-fold sd from a different
contrast class, and the document says so and names measuring sigma_d per
contrast class as "the first deliverable of the census in section 4", which was
never run. (b) The divisor uses 5,674 protein-ASPECT units while the document's
own rule three paragraphs earlier is "every bootstrap in this plan resamples
proteins, not units"; on its own protein count the floor is 141, not 129.
(c) 5,674 is a sum of `n_proteins`, which
`project_scorer_absorbs_backbone_axis_2026_08_23` establishes is **not a
population**: it counts proteins carrying a prediction at the threshold where
the metric maximised, and moved 17 per cent on a provably identical cohort.
The document even prices its own fragility: at sigma_d 0.13 the floor is 332 and
six of nine mandatory panels fall below it.

**Standing.** Honestly labelled as provisional inside the document. But the
sentence that travels is the bolded one, the document is untracked and was never
re-edited, and the refutation of `n_proteins` postdates it by six days and never
reached it.

### 2.10 "PK-BP recall ceiling 0.319, a HARD generation wall"

**The deduction.** The founding number of `plans/bp-structural-lever/`, carried
in both `PLAN.md:13` and `RESULTS.md:11`, which commissioned an entire slate of
generation levers.

**Its own successor found it, and the negative check reproduces.**
`plans/prior-knowledge-wall/PLAN.md` section 0 is titled "The plan we have been
executing is built on a number that does not exist" and states "**0.319 appears
in no receipt anywhere**". Independently reproduced in this census: `grep` over
`agent-farm/plans/`, `protea-reranker-lab/research/` and `thesis/` returns
exactly four hits, the two documents that assert it and the two lines in the
document that refutes it.

**Standing.** `bp-structural-lever/PLAN.md` and `RESULTS.md` were never
corrected. Their last commit is a week before the retraction, and a reader
landing in that directory gets the refuted story with no marker.

### 2.11 The three PK rows of `champions.md` carry 0.0000 confidence intervals that are a policy, not a measurement

**The deduction.** `repositories/protea-reranker-lab/champions.md`, untouched
since 2026-05-23, prints nine cells with `paired_ci_lower` and `paired_ci_upper`.
The six NK and LK rows are real bootstrap intervals. The three PK rows read
exactly 0.0000 / 0.0000, and the prose says why: "PK cells carry zero delta **by
construction** (not a null result)", because the deployment policy leaves PK on
the KNN baseline. So three rows of a measurement column are a restatement of a
policy, formatted identically to six measured rows, and the
`champion_fmax_cafaeval` printed for them is the baseline's number.

**Where it matters.** The nine-cell mean 0.6215 reproduces to 4.4e-05 as the
plain unweighted average of the nine cells, so an equal-weight average over nine
populations of very different size, three of which cannot vary, is published with
a "95% CI half-width" attached to it in ADR D34, which is `Accepted` and still
live in the PROTEA documentation.

### 2.12 "Sequence-level similarity information adds nothing", read off columns that were empty

**The deduction, and the mechanism is closed.**
`repositories/protea-reranker-lab/experiments/lm3/feature_importance_summary.md`
concludes that the alignment family "scores zero gain in every BPO cell,
**confirming that sequence-level similarity information adds nothing**". In the
raw CSV the summary cites, 19 of 34 features have exactly 0.0000 gain in all
nine cells. That set is exactly {alignment 10 + length 2} union {taxonomy 6}
union {`aspect`}, which is exactly the two export flags `compute_alignments` and
`compute_taxonomy`, both defaulting to `False` at
`protea/core/operations/export_research_dataset.py:71-72`, with length riding
the same producer as alignment per the contracts package. 12 + 6 + 1 = 19,
name for name, with nothing left over.

**Consequence, and it is the sharpest single finding in the census.** The
project's registered champion, the nine `v226full_lineage_<cell>`
`RerankerModel` rows imported on 2026-05-14 and the configuration `champions.md`
still names, **is a fifteen-feature model wearing a thirty-four-feature label**,
and a published conclusion was drawn from its absent columns. The summary
explains the alignment zeros and says nothing at all about the other thirteen.

### 2.13 The exclusion of ESM-2 150M from the canonical grid

**The deduction, and it is honestly marked.**
`alembic/versions/e7a1c4f9b2d6_seed_rung1_matched_parameter_grid.py`, in the
roster section of its own docstring: "ESM-2 150M, excluded by CAMPAIGN section 5
as written. **The supporting measurement could not be located**; the researcher
chose to respect the document rather than re-derive it. Do not mint it here."
The neighbouring three exclusions in the same docstring all carry numbers (out
of memory at batch size 4, 81 per cent headroom at batch size 2, non-loadable
confirmed three ways). Three of four exclusions carry a measurement and one
carries a citation to prose.

**Standing.** The compliance is defensible; the citation of a campaign section
as if it were measured is not. `count_backend_parameters` now exists, so
re-measuring it is a dispatch.

### 2.14 "0 of 9 separate among the undescribed", where the receipt prints nine rows and one separates

**The deduction, and it is a dropped row plus a missing test.** The leakage memo
states "9 of 9 comparisons separate on described proteins, **0 of 9** on the 550
UniProt never described" and prints EIGHT rows.
`storage/encoder-study/artifacts/97_run.out` prints **nine**, and the missing
first row is `ElnaggarLab/ankh-base`: described +0.0949, undescribed **+0.0561
with interval [+0.037, +0.076]**, starred on both sides by the script's own
legend. It is the largest undescribed-side effect in the table by a factor of
six.

**And the interaction was never tested.** The script computes two independent
bootstrap intervals and never bootstraps the difference of differences. The
undescribed group is 547 against 2,468, so its intervals are 2.12 times wider
from n alone, and the observed half-width ratio confirms it at 2.36. Losing
significance on the undescribed side is substantially a power effect, which is
the thing the memo needed to rule out. An approximate interaction check gives
five of nine, not nine of nine.

**Related, in the same memo:** "it INVERTS against the two strongest rivals".
Both "inversions" have intervals spanning zero, and neither arm is the strongest
rival: the strongest is `rung2-pooled`, against which ProtST is +0.0041 on the
undescribed, not inverted.

### 2.15 "The deployed sparse encoder can be neither certified clean nor ruled contaminated"

**The deduction, and the negative check that did not look where the thing would
be.** `project_learned_weights_must_declare_their_cut_2026_08_20`: "The deployed
sparse encoder declares no training release... It can therefore be neither
certified clean for any frame nor ruled contaminated, **which is worse than
either**." The checkpoint's meta is exactly as quoted. But two files in the same
bundle declare the cut explicitly: `storage/encoder/MANIFEST.json` carries
`"annotation_release": "227"`, `"annotation_published": "2025-09-04"`, and
`storage/encoder/bank/BANK.json` repeats it.

**Consequence.** Release 227 sits inside the official 220 to 230 window, so the
deployed encoder is **ruled contaminated by its own manifest**, which is the
strictly worse conclusion the memory says it could not reach. The gap the memory
names still stands, and is a different gap: nothing enforces
`training_release <= window_start`.

### 2.16 "There is no disk for per-residue retention"

**The deduction, and it is a scoping error.**
`plans/LEARNED-REPRESENTATION-ABLATION.md` section 7, 2026-08-17: residue
retention "is 423 gigabytes against 568 free, 74 per cent of the disk for one of
eight models. **That question needs a disk before it needs a design.**" The
arithmetic is right (528,294 x 625 x 640 x 2 = 422.64 GB) and the population is
wrong: it prices the whole corpus at one model.

**What happened three days later.** `storage/probe/` holds 277 GB of exactly
that, extracted 2026-08-19 and 2026-08-20 for the population the question needs:
85,982 donors with experimental evidence at release 220, plus the 3,031 NK
queries. At one layer and float16 the same extraction is 69 GB. The deciding
arithmetic needed no new measurement and was available when the sentence was
written. The sentence is still in the plan, unedited.

### 2.17 Three smaller ones, recorded so they are not repeated

- **"The sealed 0.4063 is immutable."** Two plan documents state it in exactly
  that word (`thesis-clean-iteration/AUTONOMOUS-RUN.md:36`,
  `NARRATIVE.md:198`). The memory store records it as a PROJECTION; the board
  measured 0.40765. No document in `plans/` reconciles the three headline
  numbers 0.391, 0.4063 and 0.40765, and the reconciliation that exists in
  memory was never written back.
- **"Identical to four decimals in all nine panels"** (PR #904, the depth law).
  The commit's own table has four columns and the incident document's corrected
  table has five. LK.MFO, LK.CCO, PK.MFO and PK.CCO were never published, and
  they are the cells that carry the mass of any aggregate.
- **"M3 IEA pretraining" and "SVD label embedding" filed under REFUTED
  (measured, negative, closed).** Both are milestones from
  `archive/lafa-number-one/NEURAL-HEAD.md`, a document whose only outcome
  section is M0's and which was superseded the day after. A plan milestone read
  later as a measurement is the purest instance of the class in this audit, and
  "donor-recency weighting" is the same shape with no source document at all:
  one occurrence in the entire project, and it is the registry line itself.

---

## 3. WHAT WAS LOST

The two dates destroyed different things, and conflating them produces the wrong
recovery plan. The reinstall took **artifacts and procedures at absolute paths**.
The wipe took **registry rows and the frames attached to them**. A third
category, which belongs to neither date, is things that were cited and never
existed.

### 3.1 Died with the reinstall, 2026-07-28

**Whole storage subtrees, every one of them cited by a document that still
stands.** `storage/regen_headline/`, `storage/text_scorer/`,
`storage/fullgo_models/`, `storage/cooc_experiment/`,
`storage/learned_encoders/`, `storage/two_tower_sparse/`,
`storage/consensus/`, `storage/phylo_profile/`, `storage/sse_full/`,
`storage/kwta_go_encoder/`, `storage/ensemble_audit_2026_06_13/`, and the corpus
everything was frozen on,
`storage/protea-frozen-v227-2025-09-04/reference_annotations.parquet`. Not one
exists. The eleven directories `storage/` holds today are all post-reinstall
campaign material.

**The query population.** `protea-lafa-knn/lafa_queries_7401.fasta` and
`predictions_7401.tsv`. Because `protea-predict` requires `--query_file`, **none
of the seven `beat-lafa-1` numbers can be re-measured**, independently of the
wipe. What survived, at a path nothing points to, is the ontology and the
accretion table of that frame (`storage/encoder/lafa_t0/Sep_2025/`).

**Every trained model, in both generations.** The `fullgo` 0.391 ensemble
boosters, `feature_spec.json`, the five `native_boosters_*` directories, the
`clean_227230` lambdarank trio, the overlay npz files. A filesystem-wide search
for `*.lgb`, `*booster*.txt`, `*gbm*.txt` returns zero results. There is no
trained reranker artifact of any generation on this machine.

**Two things that were in `/tmp`, which is a tmpfs and did not even survive a
reboot.** The champion's training and evaluation parquet
(`{scratchpad}/rerank_out/eval_scores.parquet`, `{scratchpad}/ds227230/train.parquet`),
read straight out of `results/clean_227230/leak_check_overlap.py:10`; and eleven
of the thirteen inputs of `fullgo/ensemble_seal.py`. So +0.1353 and +0.108 are
not recomputable here, not because the code is missing but because its inputs
were tmpfs.

**Receipts whose numbers still travel.** `project_validation_findings_2026_06_25`
(the +40 per cent), `project_structural_gate_bp_wall_2026_07_07` (the 66.6 /
20.7 / 0.545), and 57 more: a link-integrity pass over the memory store finds
179 wikilink targets, 120 resolving and **59 dangling**, and eight to nine of
those dangling files were the sole evidence behind REFUTED or CONDITIONAL
registry entries.

**The FARM-EXP.15 golden artefacts**
(`agent-farm/results/executor-1780829216-57db/runs/prot_t5_K3_*`), so the golden
regression test pins against a number (0.5863, or 0.5849 in its own docstring,
two values 0.0014 apart in one file) that can never be reproduced or refuted
here.

**The t1 ontology.** `go-basic.obo` for `releases/2026-01-23`. Exactly one
`go-basic.obo` exists on this disk and it is the t0 side, so the crossobo
reproduction is blocked on a missing file.

**What survived, and the qualification that matters.** The four `preserve:`
commits of 2026-07-27 and 2026-07-28 rescued 434 files of procedure into git.
They rescued them with the old machine's absolute paths baked in: 329 of 1,049
tracked files carry 953 paths under `/home/frapercan`, which does not exist. So
**procedures survived and the ability to run them did not**, and the failure
mode is documented by the lab itself: a missing path expressed as a default
rather than a requirement, so the subprocess failed, the failure became an error
dictionary, the metric became `None`, and the run wrote `status: ok` with every
cell empty.

The preservation is also incomplete in a way its own README warns against. That
README says the refuted arms are "kept deliberately, because a refutation whose
code is gone cannot be defended", and lists `struct_gate/` among them. What was
actually caught for `struct_gate/` is three FoldSeek temp files and no analysis
code. The failure the commit was written to prevent happened inside the commit.

### 3.2 Died with the registry wipe, 2026-08-27

**1,203 evaluation results.** 1,296 before, 93 after, 92.8 per cent gone,
together with 225 prediction sets, the candidate table and the evaluation object
store: roughly 49 GB and 128,191,567 candidate rows. 396 of the 1,296 were
already unattributable before the wipe, their producing job gone.

**Every database identifier in the plan store.** Sixteen documents cite a
database row as evidence, from `CATALOG.md:16`'s "Best confirmed native 0.3745
(EvalResult `b21b187c`)" down to `bioinfo-quick/PLAN.md:48`. All sixteen citing
documents predate the wipe. A reader following any of those ids finds nothing
and the document gives no warning. The deltas at stake are small enough to
matter: `cb77d55d` carries +0.0033 and `1df357be` carries a refutation at a
0.0062 margin, both below several of the project's own documented resolution
floors.

**The inputs of the one measured ProtST result.** The leakage study read ten
backbone prediction sets over a fixed 22,498-protein population. Those sets are
gone, so the one result in that programme with a surviving receipt cannot be
re-run as written.

**Not the code.** The wipe took rows, not repositories. Everything that landed
in `worktrees/protea-deploy` survives, including the ten operations that landed
post-reinstall and the entire post-wipe narrative record.

**The decision itself is unrecorded.** D-09 sits on an unmerged branch, and the
three artefacts it gated the deletion on (an 11,664-row floor census reproducible
from the file alone, the coverage hole by panel with its digest, and the frame
sensitivity as a column inside the census) are not on this machine. That is not
a claim they are lost: `TOPOLOGY.md` says the laptop owns the object store and
this desktop holds no state, so they were never expected here. It is a claim
that **the justification for deleting 49 GB cannot be checked from the machine
where most of the analysis happens**, and the describing decision is not on main.

### 3.3 Never existed, and are cited as if they did

- `storage/regen_headline/protst_repr/protst_repr_report.json`. **The only
  receipt file the 331-line `SIGNAL-REGISTRY.md` cites, attached to its
  number-one ranked lever.** It is an echo of the source document's own
  "Artefacts" list: the registry copied a filename the source said it would
  write, and nobody re-checked. Systemically: the lab's `research/` tree holds
  314 files, 224 `.py` and 73 `.md`, and **zero `.json`**. Every "Receipt: X.json"
  in every lab writeup is a dangling pointer.
- `protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json`, cited
  twice in `plans/prior-knowledge-wall/PLAN.md` as the receipt that overturns
  another slice's central claim. No commit has ever touched that path.
- `go_text_emb.npz`. Twenty-four readers across four checkouts and **zero
  writers, ever, anywhere**. This is the only one of GENESIS-STATE's seven
  no-producer artifacts that is exactly as bad today as when it was written, and
  it blocks the GO tower and hence the prior-knowledge generator.
- `prep.npz`. Six scripts consume it; none writes it; two of the four pieces it
  needs "are not derivable at all", per the publishing script's own docstring.
- `install-all-crons.sh`. `agent-farm/observability/CRONTAB.md` says "this file
  is the record; `install-all-crons.sh` beside it reinstalls them". It was never
  written. A narrated recovery path that does not exist, in the document written
  on reformat day to prevent exactly that.
- The eleven-release restoration probe behind 63.7 per cent.
- `leak_check_overlap.json`, the verdict on the 7.4 per cent train/eval
  positive-pair overlap in the reranker study. The script exists; its output went
  to the vanished scratchpad; and the 7.4 per cent survives only inside a
  docstring.

### 3.4 Not lost yet, and one event away

This is the operative list. Everything here exists only on this disk, which
`CLAUDE.md` says holds no state and is rebooted without warning.

- **131 encoder-study scripts plus 15 chain scripts**, in no repository. A grep
  for their distinctive names across all eight repositories and `agent-farm`
  returns zero hits, not even a reference. This is a larger untracked body than
  anything the four preserve commits rescued.
- **16 commits on `feat/gate-bundle-loader` that exist on no remote**, holding
  the library those scripts import. `probe_store.py`, which reads every probe
  bank, is not on develop.
- **347 GB of per-residue banks** with no producer and no operation.
  74,436,929 residue rows, 120,994,119 stored vectors, verified byte-exact
  against the `.npy` headers. And the two four-layer banks are **already gone**,
  304.9 GiB, index and provenance surviving without data, and the one that is
  missing is the bank whose own provenance says it supersedes the survivor.
- **Sixteen substantive plan documents that exist only on unmerged branches**,
  five of them dated 2026-08-26 to 2026-08-28 and therefore the only post-wipe
  planning work in the project. `RUN-LEDGER.md` is among them, and the user's own
  memory index treats it as authoritative; it is not on main and not in the
  working tree.
- **Two ablation documents** (`ABLATION-ARCHITECTURE.md`,
  `LEARNED-REPRESENTATION-ABLATION.md`, 89 KB) that were untracked at the start
  of this census and were rescued onto a branch mid-session. They are still not
  on `origin/main`.
- **No database backup on this node and none scheduled.** `crontab -l` returns
  "no crontab for xaxi"; `~/Thesis2/backups/` does not exist; no `*.dump` exists
  anywhere under `/home/xaxi`; the only project systemd timer is
  `protea-node-sync`. All five recorded cron lines hardcode the dead username,
  and the nightly dump's own free-space guard runs `df` against
  `/mnt/protea-archive`, which is an ordinary directory on the root filesystem,
  so the guard would report PASS while measuring the wrong disk.
- **The 391 GB archive partition is unmounted and not in fstab**, and
  `complexity-paper`, a manuscript that exists in exactly two places in the
  world, has exactly one remote and it points into that partition.
- **A throughput sampler is corrupting its own artifact right now**, appending
  to a file named for a 2026-07-29 benchmark that now spans 35 days and 30,360
  rows, 3,362 of them blank, with 215 transitions between full and blank. It was
  not stopped, per the standing rule about long jobs.

---

## 4. CONTRADICTIONS AND WHAT WE RETIRE

Each entry names the document to retire, rewrite or amend. Ordered by how badly
a reader is misled by the current state.

### 4.1 RETIRE OR REWRITE: `plans/CATALOG.md`

It calls itself "single entry point to the plan store" and its content date is
2026-06-22. It declares `beat-lafa-1` "**ACTIVE, canonical**", which
`E2E-CANONICAL-RUN.md:12-17` retired on 2026-07-27. Its headline, "best
confirmed native 0.3745 (EvalResult `b21b187c`)", points at a row wiped on
2026-08-27, and every surviving mention of that id is an echo of one 2026-06-21
document. It calls `ROADMAP-THESIS-10.md` "still the north-star roadmap". Its
loop counts are still arithmetically correct only because nothing has moved
since 2026-06-24: a stale document that agrees with reality because reality
stopped is the hardest kind to spot by checking its numbers. **Check the date,
not the number.** This is the front door and every claim on it is superseded.

### 4.2 EXECUTE THE MOVE THAT WAS ORDERED: `ROADMAP-THESIS-10.md`, `THESIS-FINISH.md`, `beat-lafa-1/`

`E2E-CANONICAL-RUN.md:15` ordered all three to `plans/archive/` on 2026-07-27
"for provenance". **The move was never made**, in git or on disk. `archive/`
holds seven other directories and none of these. None of the three carries a
superseded banner, unlike `archive/lafa-number-one/NEURAL-HEAD.md`, which does.
The supersession is discoverable only by reading line 15 of a fourth document.
Three `git mv` commands and one catalog rewrite. Zero decisions required.

The same failure repeats one month later: `chore/the-ladder-declaration-is-archived`
(commit `ece04c9`, 2026-08-28) archives `rungs.yaml` and deletes the workflow,
the script and 218 lines of tests that enforce it, with a banner that says
exactly why ("**a green check that enforces a retired claim is worse than no
check: it reports that the trunk agrees with a campaign nobody is running**").
Unmerged. **The retired check is still required on main.**

### 4.3 MERGE FIRST: `plan/decision-wipe-the-campaign-results` (D-09)

One file, 55 lines. Without it the canonical decision log ends at D-08
(2026-07-28) and no reader learns the registry was wiped. Every staleness
problem in this document is downstream of that. The on-disk `DECISION-LOG.md`
has an mtime of 2026-08-29 and a last commit of 2026-07-28: it was touched after
the wipe and D-09 still is not in it.

### 4.4 AMEND: `plans/thesis-pillars/PILLARS.md`

Pillar 4, "the wall is evidence-bound, not architecture-bound: no amount of
fusion machinery crosses it, only new evidence does", was refuted by the
project's own measurement seven days later. **The thesis was corrected**
(commits `6aafc9f` and `93ce1dc`; `chapters/06_evaluation.tex:843` now reads
"the headroom is therefore one of ranking"). PILLARS.md was not; its last commit
is 2026-07-09 and it is still the document the plan store points to as the
thesis spine. It also contradicts itself on one page, labelling structure
`[absent]` at line 36 and `RED (tested)` at line 95, and the structural-gate row
is the one row of that table with no receipt.

### 4.5 AMEND OR MARK: `plans/bp-structural-lever/{PLAN.md,RESULTS.md}`

Both still assert the 0.319 PK-BP recall ceiling and "the loss is
candidate-GENERATION-bound", a week after the successor plan showed that 0.319
appears in no receipt anywhere. The directory name is also a trap: the two
results directories under it measure the two-tower classifier, not structure,
and the loop that actually ran a structural search has no plan file at all.

### 4.6 AMEND: `plans/SIGNAL-REGISTRY.md`

Three separate problems, all in one document that the project treats as "what is
settled" and that has exactly one commit, 2026-07-27.

- **Section 5 item 1 and section 8 step 2 recommend rebuilding the retrieval
  space on ProtST**, whose lead was shown on 2026-08-23 to be substantially
  UniProt text exposure. The refutation says in its own words "no thesis sentence
  may recommend ProtST on these numbers". The registry recommends it twice.
- **Section 4 is titled "REFUTED (measured, negative, closed)" and nine of its
  entries do not meet that description**, by the registry's own two tests, plus
  three that were never measured at all. One (`GO-text BioBERT label basis`) is
  measured **positive** at +0.012 on LK-BPO and is the mechanism the thesis uses
  for its fourth pillar.
- **It is now the most precise surviving carrier of numbers whose receipts are
  destroyed**, which makes it uncollidable by construction: one receipt path in
  331 lines and that file does not exist; every `storage/` path it names is gone;
  and the archive it declares "closed and md5-verified" is an empty unmounted
  directory. Its own paragraph three lines below that claim says "never report an
  artifact as backed up without reading it back OUT of the destination".

### 4.7 RESOLVE, THEN WIRE: `protea/core/split_registry.py` against `protea/core/band_registry.py`

Two modules in one package give opposite answers to "which window is the board's".
`split_registry.COMPARABLE_WINDOW` computes to v226 to v227, the window ending at
the mark; `band_registry.py:131-135` describes the v227 band as "Deployed LAFA
window (GOA v227 to v230)" and says v226 is "superseded by v227 for
LAFA-comparable numbers". Five independent records agree with `band_registry`,
including the 2026-06-27 board comparison against release `Sep_2025_Mar_2026`
and a memory whose opening words are "dates, checked rather than assumed".

**`band_registry` is the only one of the two that any production code imports.**
So the authority enforced at scoring time says v227 to v230, and the authority
that is only tested says v226 to v227. And the window `split_registry` lands on
is the minus 30.9 per cent contraction, which it simultaneously uses as the
reason the adjustment split cannot be decided. One off-by-one both invents an
incomparable headline and deadlocks champion selection.

### 4.8 RE-STAMP: `storage/encoder-study/recipe/residue-sparse-k4-d2048-s128-mean.npz`

Its own provenance declares `"recommended": "2 bits"`. The same study, the same
day, measured 2 bits as losing 0.0243 in four of four identity bands, eighteen
times the resolution floor, because 81.8 per cent of atoms round to zero. The
document's recommendation is 4 bits at 240 bytes. **This is the only defect in
the entire census that would cause a wrong deployment today rather than a wrong
sentence.** The byte accounting disagrees too (159 against 208 for two bits, 237
against 240 for four).

### 4.9 WITHDRAW PROPERLY: `repositories/protea-reranker-lab/champions.md` and the echoes in PROTEA's documentation

The lab formally withdrew its results on 2026-07-28 (`4a81079`, "withdraw the
results, keep the genealogy that explains them"), naming 0.7291, 0.6215 and
0.4562. **The withdrawal says "nothing in this file"**, so it covers README.md
and nothing else. `champions.md` is untouched since 2026-05-23 and still
publishes 0.6215, all nine per-cell champions, the three deduced zero intervals,
0.4562 twice unannotated, and nine live `RerankerModel` UUIDs. `fullgo/` is
outside the withdrawal entirely and still opens "how PROTEA reached first place".
And the withdrawn numbers are live in PROTEA's current documentation:
`docs/source/quality/index.rst:138` calls 0.7291 "a publishable statistical claim
for Chapter 6", and ADR D34 is `Accepted` and carries 0.6215. **A withdrawal that
lives in one file is not a withdrawal**, and nothing links a lab retraction to
the platform's docs.

### 4.10 CORRECT: `thesis/chapters/06_evaluation.tex:883-889`

The published sentence "a text-aligned representation adds +0.002 on this cell"
traces to `BP_TECHNIQUE_LEVERS.md:89` ("+0.0016 on PK-BPO"), measured against the
0.1255 baseline that `SIGNAL-REGISTRY.md:111` says was **manufactured by the
`rankpct` bug** and that "invalidated every technique lever measured against it".
The adjacent bullet in the same source list, co-occurrence at +0.0021, was
rehabilitated by the registry for exactly that reason and this one was not, and
the thesis publishes both in one sentence as the two hypotheses "eliminated by
measurement". This is on the argument surface, not the verification surface.

### 4.11 AMEND: `plans/GENESIS-STATE.md`, which contradicts itself

Items 1, 2 and 6 of its section 2 (stratification, a window registry, a
row-alignment assertion) were closed by code committed 2026-07-28 between 03:49
and 03:59 UTC, **before the document's own final commit at 08:54 UTC that same
day**, and its section 6 describes those very closures while section 2 above
still lists them as missing. Five weeks and ten landed operations later it has
had no commit. Its section 3F still says the evaluation phase is "blocked on the
IA artifact"; `compute_information_accretion` landed 2026-08-17 and the store
held one information accretion set on 2026-08-30.

### 4.12 CORRECT IN PLACE: `docs/findings/2026-08-30-what-a-curated-not-was-telling-us.md`

It carries the "2.5x understatement" that `COLLIDING-A-NUMBER.md:55-58` records
as retracted (the real effect is +13 per cent). The repo document is unchanged
and the retraction does not name the document it corrects. A reader of the code
repository, which is the surface an examiner reaches, gets the retracted number.

### 4.13 READ TO THE END: `storage/encoder-study/RESULTS.md`

Its 44-arm purity table sits 63 lines above its own supersession, which declares
the axis the study was designed around inert (spread 0.0006 against 0.0842 for
the backbone axis) and then, three days later, retracts the backbone result too
because "the best backbone had read the answer". Anyone reading top-down cites
+0.0287 and stops. Three independent refutations of the order claim existed
before this census (script 73 on Fmax on the served cell, 0 of 3; RESULTS.md's
own supersession against a real 85,982-donor bank, 0 of 33; and the stratified
architecture null, 0 of 24 bands) and each was filed as "a different population"
rather than allowed to land.

### 4.14 REWRITE OR RE-DATE: `plans/CONCEPT-MAP.md`

"Living document... held and updated at all times... keep it current as work
proceeds", with exactly one commit, ever, 72 days ago. It ships three `[stale]`
markers that were present on day one and carries the headline pair "0.391
offline / 0.3745 native". Its own first paragraph instructs a reader to trust it
as current.

### 4.15 A note on two documents that should NOT be retired

`plans/COMPOSITION-MODEL.md` is the one document in the plan store that is not
conceptually stale, and `PLAN.md` (the rendered master) is honest: its
333 / 207 / 108 / 14 / 3 / 1 slice counts reproduce exactly from its own inputs.
What both need is a banner saying the slice system has been dormant since
2026-06-24 and that the rung system, and now the experiment graph, is where work
actually happens. The two planning surfaces do not reference each other at all.

---

## 5. THE WALLS

A wall is something that cannot be reproduced inside the platform, with the
reason. Two kinds appear below: structural walls, where no operation could exist,
and cost walls, where an operation could exist and the input has to be
regenerated first. Both are marked. Anything that is merely missing an operation
is not a wall and belongs in section 6.

### W1. The board. STRUCTURAL.

The validation metric is not ours to compute. `split_registry.py:279` declares
validation "scored by the board" with `may_inform = frozenset()`, and the lab
states the same wall from the other side in a file whose name is the argument
(`research/regen_headline/WE_DO_NOT_REPRODUCE_THE_BOARD.md`). The consequence is
that the campaign invariant, "no artifact without a registered operation that
produces it", cannot cover the headline number. The campaign is right to
designate one point of the series as comparable rather than pretend otherwise;
what is wrong is that the code currently designates the wrong point (4.7).

### W2. The structural gate, as it was run. STRUCTURAL, and unrecoverable.

There is no FoldSeek binary, no structure database and no 3Di file anywhere on
this disk. What survives of the one structural search this project performed is
three of FoldSeek's own auto-generated temp workflow scripts, two of which are
byte-identical templates carrying no run parameters. `download.sh` branches on a
runtime `${SELECTION}` over eleven possible databases and **the chosen one is
not recorded**, so even the target of the run is not knowable. The capability
was specified (Phase D of `DESIGN-cross-encoder.md`: UniProt to AlphaFold DB to
FoldSeek 3Di as a backend) and never built. Rebuilding it is new work, not
reproduction.

### W3. The four-layer per-residue banks. COST, 304.9 GiB of forward passes.

`lafa_4layers.npy` (52.9 GiB) and `pool60k_4layers.npy` (252.0 GiB) are gone;
their index and provenance files remain. **Thirty-three of the encoder study's
scripts cannot run any more**, and, decisively, **all eleven of the scripts that
score against the window's additions with the exclusion applied are among them**.
So the commensurable half of the lab is exactly the unrunnable half, and the
half whose inputs survive is the half the lab itself says must not be quoted
(the ancestor closure at release 227, of which 87.8 per cent of the terms in the
gold are terms the protein already had).

There is also a schema reason this stays on the filesystem:
`SequenceEmbedding.embedding` is one vector per row, so per-chunk rows are legal
and per-residue rows at corpus scale are not, and the project's hard constraint
forbids a vector database for neighbour search anyway. The operation that IS
possible consumes a filesystem bank and writes only the derived code and the
measurement rows, the way a GOA dump is an input.

### W4. The 7,401-target LAFA query population. STRUCTURAL, until a file reappears.

`protea-predict` requires `--query_file` by standing norm, and the FASTA is gone.
Without it none of the seven `beat-lafa-1` evaluations can be re-measured, and
that is true independently of the registry wipe. The ground truth half of that
frame survived (`CAFA_forever/data/releases/Sep_2025_Mar_2026/`, and I confirm
the plan's predicted cell counts exactly: 7,401 targets, NK 399, LK 868,
PK 6,340), so this wall is one file thick.

### W5. The frames of twenty of the twenty-one rescued evaluation bundles. STRUCTURAL.

`storage/rescue/minio/protea/eval_artifacts/` holds 21 complete pre-wipe
evaluations, 357 files, 464 MB, dated 2026-08-02, each with all four F statistics
per aspect per cell at the best tau. **The rescue's database dump stopped after
two tables and wrote no `MANIFEST.json`**, so no `evaluation_result`,
`prediction_set`, `job`, `annotation_set` or `embedding_config` row was captured.
For those 21 we have every number and have lost every fact about what produced
them. Exactly one of the 21 has a recoverable frame, because one memory file
happened to quote its id. Twenty numbers with no frames is the object that
produces the "same reranker reads 0.3433 and 0.117" defect, and they must be
treated as unusable for any comparison.

### W6. `d8979601`. STRUCTURAL: a champion by citation only.

Cited by name in fourteen documents across `agent-farm/plans/` as the learned
champion encoder, and existing as weights in none of them. The encoder that does
have receipts, a full manifest, a validation, a recipe and a bank census is
`0868f1ff`, and the bundle that published it is stamped, in its own note,
"**NOT the champion d8979601**". Every "+40 per cent", "0.4937" and
"NK MFO 0.507 vs 0.398" attaches to the former; every Spearman, digest and
provenance chain attaches to the latter. Do not let a reader assume they are one
encoder because both are "the learned k-WTA sparse encoder over ankh-base".

### W7. The two-tower's protein side and `prep.npz`. STRUCTURAL.

The GO side was recovered on 2026-08-24 from a hand-mounted preserve partition
and published to the object store on 2026-08-26, with its provenance saying
plainly "**NOT rederivable: no script on disk builds them and the machine that
produced them was formatted**". The seven trained heads were not uploaded and
are read by script 107 straight off `/mnt/protea-archive`, which is an empty
unmounted directory today. `prep.npz`, which both the trainer and the generator
need, is consumed by six scripts and written by none, and two of the four pieces
it requires are not derivable at all. This is the artifact-without-a-producer
the campaign invariant exists to forbid, caught red-handed and documented by its
own publish script.

### W8. Everything under `/home/frapercan` and `/tmp` on the old machine. STRUCTURAL.

The reinstall changed the user name and `/tmp` was a tmpfs. The champion's
training data lived in an agent scratchpad under `/tmp`. This is not a wall in
the sense of "we could build it and chose not to"; it is a wall in the sense
that the only route back is re-measurement.

### W9. Exploration itself. STRUCTURAL, and the line moves.

An operation is a named, versioned, validated payload; a probe asked once has no
payload. `COLLIDING-A-NUMBER.md`'s closing paragraph says so, and forcing every
one-off into the registry would make the registry a landfill. **But the boundary
moves and nothing watches it move.** `fullgo/assoc_feature.py` was written as a
probe, became "the lever that took us past TransFew", and was later transcribed
into `build_go_cooccurrence`. The honest boundary is that a procedure earns an
operation the moment its output is cited, and there is no mechanism that notices
that moment.

### W10. Numbers whose only route back is re-measurement.

Not walls in the platform sense, listed here because they are frequently
mistaken for retrievable facts: 66.6 / 20.7 / 0.545 (the structural gate);
0.319 (the PK-BP generation ceiling); 63.7 per cent (the restoration probe);
0.24849 and the nk-MFO delta of the ProtST screen; the recall ceilings in
`p4_recall_ceiling.json`; 0.5849 and 0.5863 (the golden regression pins);
0.7291 and 0.6215 and 0.4562 (withdrawn, and still published elsewhere).

### W11. Not a wall, a mount.

The 391 GB archive partition behaves like a wall today and is not one. Mounting
it would make `no-producer-artifacts/`, the secret surface, every database dump,
the object-store snapshot and the 144 archived memory files readable again, and
would restore the only remote `complexity-paper` has. It is not in `/etc/fstab`,
so it will not come back on its own, and the mount exists only in one operator's
memory of one afternoon. **The artifacts being recoverable is precisely the
temptation the "no artifact without a producer" invariant exists to refuse**, so
mounting it is a recovery action and not a licence to import.

---

## 6. THE WORK LIST

Three groups, and the distinction between the first two is the point of the
section. Group A is dispatch: the code exists, is tested, and has never been
run against this database. Group B is development. Group C costs minutes and
changes what every future reader believes.

### 6.A Operations that ALREADY EXIST and were simply never dispatched

These are jobs, not projects.

1. **`audit_evaluation_frames`.** Registered, read-only, and unrun since the
   wipe. It reports `n_rows`, `with_frame`, `with_window`, `with_role`,
   `with_arms`, `without_job` plus the distinct (frame, window, role)
   combinations. **One dispatch settles which window the 93 surviving rows are
   on**, which is currently the single most consequential unknown in the project
   and which the temporal auditor could only reach by elimination from a worker
   log. The testable prediction on record: the 93 rows point at one evaluation
   set whose `old_annotation_set_id` resolves to source version 220.
2. **`build_go_cooccurrence`.** Exists, has a test, a loader and a consumer, and
   **has run before**: a 2026-06-17 migration describes a defect only observable
   post-run, and a lab summary records an export at 80.6 per cent non-zero
   association. The tables are empty on this database because it is new.
   Re-running is a dispatch. It restores the feature the lab measured as second
   by gain in PK.
3. **Score the two admissible frozen recipes on the official frame.**
   `recipe/cut220-residue-k4-d2048-s128.npz` and
   `recipe/exp220-residue-k4-d2048-s128.npz` both declare `training_release 220`,
   both carry a frame check saying they are admissible for 220 to 230, and both
   say in their own provenance "**not yet scored on the official frame**". The
   artifacts exist, the operation exists, and the number does not. Cheapest open
   number in the census.
4. **Dispatch `limit_per_entry` in {5, 10} beside 30.** No code at all; the field
   already exists on `PredictionSet`, and the post-wipe depth series says the
   optimum is at or below the edge of what was measured.
5. **Re-run one evaluation and read `coverage_at_tau`.** It has been published
   since PROTEA #804 (2026-08-20) and surfaced on `/graph`. This settles the
   campaign's founding diagnosis (2.2), which is currently a hypothesis
   supported by a misread statistic.
6. **`stratify_evaluation` on the depth series, and publish all nine cells.**
   Five were published; the four missing are the LK and PK non-BPO cells, which
   carry the mass of any aggregate.
7. **`compare_paired_panels`** on anything currently compared by hand. It landed
   2026-08-28, is protein-level, re-selects the operating point on each draw,
   reads its minimum detectable effect off the bootstrap distribution rather than
   a normal approximation, and has a `DEGENERATE` interval type.
8. **`load_ontology_snapshot` for a snapshot contemporary with GOA 220.** It is
   the stated precondition for the crossobo work and for routing
   `generate_evaluation_set` through a pivot that is not `new_native`. "Loading
   one is a precondition, not a detail."
9. **`count_backend_parameters`** to close the ESM-2 150M exclusion (2.13),
   which currently rests on a citation to prose.

### 6.B NEW operations, ranked by what they unblock

1. **`audit_export_columns`, or a gate inside `export_research_dataset`.**
   Per-column population statistics written to a `dataset_column_stats` table,
   and a refusal to register a `RerankerModel` whose `feature_schema_sha`
   declares columns the producing dataset never populated. The export already
   records `compute_alignments` and `compute_taxonomy` in its manifest, and the
   `RerankerModel` row already carries `feature_schema_sha` and `dataset_id`, so
   the join exists. **Difficulty LOW, and it retroactively voids or confirms
   every model already registered.** Nothing else should be trained until an
   export can prove its columns are populated. This is the cheapest guard in the
   census and it would have caught 2.12 before a fifteen-feature model was served
   as a thirty-four-feature one.
2. **A frame descriptor as columns on `evaluation_result`**: ontology and IA
   version, `prop`, `norm`, `max_terms`, `th_step`, whether `-known` was applied,
   the metric name, the window, the pool definition, the seed, the objective and
   the population count, plus a `control` column (none / shuffled / random-order
   / matched-volume) and a selection floor derived from the number of arms scored
   on that frame. This turns the PK-BPO table, which currently has at least
   thirteen distinct published values spanning a factor of 6.3, into a `GROUP BY`.
   Section 10 of the registry already asks for half of it and calls it
   outstanding. **It can no longer be done from records, only by re-running.**
3. **A way to retract or supersede a sealed `evaluation_result`.**
   `seal_evaluation_frames` seals and nothing un-seals or annotates, which is why
   five known-wrong rows sit indistinguishable from five correct ones under one
   frame digest.
4. **`decompose_release_deltas`**, writing a new `release_delta` table with
   (from_set, to_set, aspect, evidence regime, added, removed, restored,
   first-appearance added, proteins gained, proteins lost, elapsed days).
   Difficulty LOW to MEDIUM: three set differences per pair, and the
   first-appearance logic is already written and tested. **It is the Stage 0
   gate**, and `split_registry.py:267-275` refuses to choose adjustment windows
   without it, in code, at runtime, which is why no champion can be selected.
5. **`report_text_availability_by_category`**, one COUNT over
   `protein_uniprot_metadata.function_cc` restricted to the category table.
   Difficulty trivial. Its absence let a false leakage clearance stand for 46
   days across six documents and voided the load-bearing sentence of a whole
   programme.
6. **`train_reranker`.** MEDIUM to HIGH, and the difficulty is the staging
   (bucket routing so a LambdaRank group never crosses a bucket, the group key,
   the streaming sequence over sorted parquet, the categorical vocabulary),
   roughly 2,600 lines. The `RerankerModel` table already has the shape.
   `reranker_model` holds **0 rows** and there is no trained booster of any
   generation on this machine, so everything downstream waits on this.
7. **`evaluate_encoder_arm`**: score an arbitrary encoder arm on a declared
   category-by-aspect cell against a declared donor bank, on Fmax, with the
   exclusion applied, writing an `evaluation_result`. This is the operation whose
   absence let a Jaccard-denominator screen run 45 arms, produce a headline, and
   keep a research direction open for two weeks against three refutations that
   were already on disk.
8. **`fit_learned_encoder`.** MEDIUM. `apply_learned_encoder` exists and its
   docstring enumerates the artifact format it must be handed, so the consumer is
   complete and only the producer is missing. Add a `training_release` field
   checked against the window start at dispatch; `MANIFEST.json` already carries
   it and nothing reads it.
9. **`measure_candidate_recall`.** LOW: a set intersection over the candidate
   pool, writing the nine cells. Without it every "the reranker did not help"
   verdict is unattributable between the pool and the scorer, and at least one
   published summary already made that attribution without the number.
10. **`fit_score_calibration` and `apply_score_calibration`.** LOW maths, and the
    work is the frame discipline (it must fit on the adjustment split and never
    on validation). The one post-wipe lab result in the census is a calibration
    rule that no operation applies.
11. **`audit_prediction_set`, `audit_denial_violations`, `report_store_inventory`.**
    All three currently exist as hand-written SQL pasted into markdown, and the
    third does not add up (12 spaces times 528,294 is 528,234 short of the stated
    total; 13 times is 60 over).
12. **`compare_ontology_snapshots`** and **`apply_hierarchy_postprocess`**
    (writing a derived `PredictionSet` so the pair is comparable by
    `compare_paired_panels`). Both LOW to MEDIUM; the second is a claimed
    +0.04 IA-Fmax lever that has never run in-platform.
13. **`extract_residue_probe`**, a per-residue multi-layer probe as a registered
    artifact. Without it the 33 blocked scripts stay blocked forever. It is
    MURO-adjacent: the platform's embedding cache is 2D, so the bank has to stay
    a filesystem input and the operation writes only derived codes and
    measurements.
14. **The registry-to-UI coverage test.** Three lines. It currently fails 30 of
    39 ways and it is the literal acceptance criterion of FR-1.
15. **A `no-absolute-home-paths` lint.** Twelve sites in the deploy tree, three
    different home directories, two of which do not exist here, including an
    installer that copies from a directory that is not on the machine it installs
    onto. The repository already runs em-dash and row-alignment lints, so the
    shape exists.
16. **A declaration of the experiment graph that a job can be refused against.**
    The archive banner names it and says "that does not exist yet, and saying so
    here is the point of keeping the file". The incident it exists to prevent is
    on record: on 2026-08-19 a grid ran 48 arms of a declared rung while varying
    two of its three axes, the third pinned by omission to the weakest available
    value, and 400 jobs were tagged with a rung number invented at dispatch time,
    and nothing objected to either. **Prose cannot refuse a job.**

### 6.C Actions with no computation, which cost minutes

Do these first. Every one of them changes what the next reader believes.

1. Merge `plan/decision-wipe-the-campaign-results` (D-09). One file, 55 lines.
2. Merge `chore/the-ladder-declaration-is-archived`, removing a required check
   that enforces a campaign nobody is running.
3. Execute the 2026-07-27 move: `git mv plans/ROADMAP-THESIS-10.md
   plans/THESIS-FINISH.md plans/beat-lafa-1 plans/archive/`.
4. Land the sixteen branch-only plan documents, `RUN-LEDGER.md` first, since the
   user's own memory index treats it as authoritative and it is not in the tree.
5. Get the two ablation documents onto `origin/main`; they are on a rescue
   branch only.
6. Re-stamp the frozen recipe to 4 bits (4.8). The only live deployment defect.
7. Mount `nvme1n1p5`, add it to `/etc/fstab`, give `complexity-paper` a real
   remote, and schedule a database dump as a version-controlled systemd timer
   rather than a crontab (the pattern already exists for `protea-node-sync`).
   Then read the dump back out of its destination before reporting it saved.
8. Add `docs/findings/` and `docs/incidents/` to a Sphinx toctree. **Six markdown
   files are the entire narrative research record of the current window**, and an
   examiner following `CLAUDE.md`'s own instruction to the verification surface
   sees none of them; the last thing the Sphinx tree records is an ADR dated
   2026-08-17, ten days before the wipe.
9. Delete one of the two divergent `cold-boot.sh` copies (zero overlap on their
   distinctive flags), and delete or pin `repositories/agent-farm`, which is ten
   days stale and is the copy a recursive grep reads.
10. Write the five poisoned `evaluation_result` ids into a durable note until
    item 6.B.3 exists: `67fe2fa0`, `28621824`, `9de60449`, `53d68960`,
    `d0705d22`.

---

## Closing: the shape of the whole thing, in three sentences

**The project's visibility and its recency run in exactly opposite directions.**
The most authoritative documents (`CATALOG.md`, `CONCEPT-MAP.md`,
`SIGNAL-REGISTRY.md`, `PILLARS.md`) are the oldest and describe a campaign that
was retired; the real body of recent work is 131 untracked scripts in `storage/`,
16 unpushed commits in an ephemeral worktree, six markdown files in one
repository worktree that is not in any documentation build, and sixteen plan
documents on unmerged branches.

**Of the seventeen recorded measurement defects, zero were found by whoever
produced the number, and this census adds to that pattern rather than breaking
it**: the sharpest new findings (the Jaccard denominator, the fifteen-feature
champion, the off-by-one comparable window, the 81.9 per cent text availability,
the two-bit recipe) were each visible in a file the producer already had open.

**The single structural fix is the frame descriptor.** Almost every contradiction
in this document is one quantity read in two frames, and almost every loss is a
number that survived while the fact of what produced it did not. A row that
carries its own frame turns the archaeology into a query, and it is the one thing
that cannot be recovered from records now, only from re-running.

---

Written 2026-09-02 by the `FRONTS` auditor. Read-only throughout; the only file
written is this one. Sources: the twelve slice reports in this directory, plus
direct verification of the plan-store layout, `COLLIDING-A-NUMBER.md`, and the
archive directory listing.
