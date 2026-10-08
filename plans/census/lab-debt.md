# lab-debt: protea-reranker-lab, the DEBT it holds against the platform

Slice: enumerate every capability the lab has that the platform does NOT.
For each: what operation would have to exist, what it writes to the DB, how hard.
Rank by dependence. Name explicitly what CANNOT move (a wall must be named).

Two questions the platform owner asked:
 (Q1) does the lab hold its OWN GO co-occurrence artifact? (platform tables
      term_cooccurrence / term_frequency empty, build_go_cooccurrence never dispatched)
 (Q2) does the lab hold a decomposition of annotation ADDITIONS and REMOVALS per
      GOA release, which the split registry needs to choose adjustment windows?

Status: IN PROGRESS (appending as findings land)
Started: 2026-09-02

---
## Q1 (part 1/3): the lab DOES hold co-occurrence CODE, in two independent implementations
verdict: CONFIRMED (code exists) / the ARTIFACTS are pre-reinstall-lost
first number: `research/cooc_experiment/` = 82 files, 1008K, all mtime 2026-07-29 01:48
  (that is the git-checkout date, one day AFTER the reinstall: PR #115 "preserve: track the
  research procedures that ran outside every repository" is what put them in the repo)
second number: two DIFFERENT co-occurrence builders exist and they are not the same object:
  (a) /home/xaxi/Thesis2/repositories/protea-reranker-lab/fullgo/assoc_feature.py:41
      `cooc = (Y[:, spec].T @ Y).tocsr().astype(np.float32)` then :43
      `cooc = cooc.multiply((1.0 / freq[spec])[:, None])` -- a SPARSE MATRIX
      cooc = Y^T Y over the training label matrix, row-normalised by term frequency.
      Produces `a_all = sum_k P(t|k)` and `a_cross` (cross-aspect only).
  (b) /home/xaxi/Thesis2/repositories/protea-reranker-lab/research/cooc_experiment/cross_aspect_channel_ceiling.py:98-105
      `cooc = collections.defaultdict(collections.Counter)` ... `cooc[k].update(BP[p])`
      -- a PYTHON DICT-OF-COUNTERS, known-term -> BP-term counts, built in-process.
      Same file is duplicated as cross_aspect_nodup.py (the dedup variant).
date of evidence: code committed 2026-07-29 (PR #115/#117), written earlier
window: the code is post-wipe-current (it is in git); the OUTPUTS are pre-reinstall-lost
frame: (a) is fit on the training split's label matrix Y AFTER propagation; the
  normalisation is 1/freq[k] i.e. P(t|k), NOT PMI, NOT lift, NOT Jaccard.
  (b) is raw counts with max and mean readouts (`cooc[k][t]/max(kfreq[k],1)`), same P(t|k).
population: (b) is explicitly CROSS-ASPECT: known terms in MFO/CCO -> candidate BP terms.
platform gap: the platform ALREADY has the operation. `build_go_cooccurrence` exists with
  a test (worktrees/protea-deploy/tests/test_build_go_cooccurrence.py) and a loader
  (tests/test_cooccurrence_loader_cache.py, test_cooccurrence_loader_pg.py) and a consumer
  (tests/test_association_csr_unit.py, test_apply_association.py). So this is NOT a missing
  operation. It is an operation that has NEVER BEEN RUN. See Q1 part 2.
note: the lab source files ALL point their working dir at
  `/home/frapercan/Thesis2/storage/cooc_experiment` (the PRE-REINSTALL username).
  `/home/frapercan` DOES NOT EXIST on this machine (`ls /home/` -> only `xaxi`), and
  `/home/xaxi/Thesis2/storage/` has NO `cooc_experiment` directory. Every derived
  artifact of that campaign is gone. The procedures survived; their outputs did not.
  This is the exact shape CAMPAIGN.md 0bis predicts.

## THE PLATFORM'S REGISTERED OPERATION SET, as the baseline the debt is measured against
verdict: CONFIRMED
first number: **40 operations** registered in
  /home/xaxi/Thesis2/worktrees/protea-deploy/protea/core/operation_catalog.py
  (`build_operation_registry()`, the single source both `scripts/worker.py:19`
  and the API build from). Full list, in registration order:
  ping, export_gate_bundle, audit_evaluation_frames, audit_per_protein_artifacts,
  seal_evaluation_frames, stratify_evaluation, compare_paired_panels,
  apply_learned_encoder, insert_proteins, fetch_uniprot_metadata,
  load_ontology_snapshot, load_quickgo_annotations, load_goa_annotations,
  load_interpro_go_mapping, run_interproscan_batch, generate_evaluation_set,
  run_cafa_evaluation, batch_rescore_evaluation, compute_embeddings,
  compute_embeddings_batch, measure_embedding_magnitude, store_embeddings,
  predict_go_terms, predict_go_terms_batch, store_predictions,
  predict_go_terms_from_interpro, refresh_goa_release_dates,
  build_go_cooccurrence, compute_information_accretion,
  archive_ontology_snapshot, count_backend_parameters,
  export_evaluation_targets, encode_residue_sparse, encode_residue_sparse_batch,
  export_research_dataset, export_coordinator, export_knn_batch,
  export_features_batch, export_write.
second number: the catalog carries its own confession, verbatim at
  operation_catalog.py:120-124 --
    "TrainRerankerOperation / TrainRerankerAutoOperation are no longer
     publicly registered: all re-ranker training moves to
     protea-reranker-lab. They remain importable as internal helpers"
  So the largest single item of debt is not an accident of history. It was a
  DECISION to move training out of the platform, and it is written in the
  platform's own registry file.
date of evidence: worktrees/protea-deploy HEAD `a5de702` (2026-09-01) -> window: post-wipe-current
frame: n/a (code inventory)
platform gap: the boundary is now exactly: the platform can EXPORT a research
  dataset (`export_research_dataset` + the four export minijobs) and can IMPORT a
  trained model by reference (`POST /reranker-models/import-by-reference`, cited
  at reranker-lab scripts/lr1_lineage_delta.py:20-24). Everything BETWEEN those
  two points -- staging, training, selection, calibration, scoring -- happens in
  the lab, on this disk, with no operation and no database row.
note: the campaign invariant "no artifact without a registered operation that
  produces it" is therefore violated by construction for every model the project
  has ever served. The nine `v226full_lineage_<cell>` RerankerModel rows were
  registered by reference on 2026-05-14 with external_source
  `protea-reranker-lab@28d9ce0-study_v23`; the row records a POINTER, and the
  producing procedure is a lab script.

## Q1 (part 2/3): the platform operation EXISTS and is a TRANSCRIPTION OF THE LAB FILE
verdict: CONFIRMED
first number: worktrees/protea-deploy/protea/core/operations/build_go_cooccurrence.py:1-25
  docstring, verbatim: "Algorithm (**mirrors ``protea-reranker-lab/fullgo/assoc_feature.py``**)".
  Op name at :171 `name = "build_go_cooccurrence"`; payload
  `BuildGoCooccurrencePayload{annotation_set_id, known_freq_cap=1000, write_batch_size=50_000}`;
  writes `TermCooccurrence` and `TermFrequency` by psycopg3 COPY (:396, :425),
  deleting the set's prior rows first (:380-382).
second number (independent, the collision): the constant matches. The lab file
  reranker-lab/fullgo/assoc_feature.py:18 sets `FCAP = 1000`; the platform payload
  default is `known_freq_cap: PositiveInt = 1000`. Same number, same meaning
  ("exclude known terms more frequent than this"). So this is a transcription,
  not an independent implementation, and it CANNOT collide the lab's number --
  agreeing with the source you were copied from is not agreement.
date of evidence: platform code at `a5de702` (2026-09-01); the lab file's own
  provenance is the pre-reinstall disk (PR #114/#115, committed 2026-07-29)
frame: platform = propagated is_a/part_of ancestor closure, EXPERIMENTAL,
  non-negated, leaf terms only, per AnnotationSet, freq(t) = DISTINCT proteins.
  lab = whatever Y the FRAME_NPZ carries; **the lab file does NOT propagate**,
  it takes `rows`/`cols` from the npz as given. TOPN=80 emission cap exists ONLY
  in the lab (assoc_feature.py:19) and has NO platform equivalent -- the platform
  stores every pair. Two frames, one claimed to mirror the other.
platform gap: NONE for the operation. The gap is that it has produced nothing
  reachable. See part 3.
note: THE LAB FILE CANNOT RUN TODAY. assoc_feature.py:17 hardcodes
  `OBO = "/home/frapercan/Thesis2/protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo"`.
  `/home/frapercan` does not exist on this machine. Same for every one of the 82
  files in research/cooc_experiment/, which all point at
  `/home/frapercan/Thesis2/storage/cooc_experiment`.

## Q1 (part 3/3): "never dispatched" is TRUE OF THE CURRENT DATABASE ONLY. It ran before, and its output was silently ZERO.
verdict: CONTRADICTED (as an absolute) / CONFIRMED (for the current window)
first number: the platform owner's claim -- term_cooccurrence and term_frequency
  empty, build_go_cooccurrence never dispatched.
second number (independent, and this is the finding): the alembic migration
  worktrees/protea-deploy/alembic/versions/d1e2f3a4b5c6_add_go_id_strings_to_term_cooccurrence.py
  (Create Date 2026-06-17) documents a defect that is only OBSERVABLE if the build
  had been run and consumed. Verbatim, :11-17:
    "The original term_cooccurrence / term_frequency tables keyed everything on
     those per-snapshot integer ids. That broke the association feature across
     snapshots: the offline build keys the cooccurrence on the annotation set's
     OWN snapshot int ids, but the training export candidates live in the
     export's snapshot, so candidate_term_id (build snapshot) never matched the
     export candidate int ids and **every association feature was zero for
     training rows**."
  and :26-28: "pre-existing rows keep their integer ids; the new string columns
     are NULL until a fresh build_go_cooccurrence run repopulates the set".
  "Pre-existing rows" is the platform's own testimony that rows existed.
date of evidence: 2026-06-17 (migration) -> window: **pre-reinstall-lost**.
  The OS was reinstalled 2026-07-28 and the registry wiped 2026-08-27, so both
  statements are compatible: it ran on the old database, and has not run on this one.
frame: the pre-2026-06-17 build was keyed on per-snapshot INTEGER go term ids.
  Any number ever quoted from an association feature computed BEFORE that
  migration is a number computed on an all-zero column.
population: training export rows, all cells.
platform gap: none missing; what is missing is a RUN. The whole chain
  build_go_cooccurrence -> _association_loader.py -> _post_knn_pipeline.py:322
  (`compute_association` flag) is present in code at
  worktrees/protea-deploy/protea/core/operations/predict_go_terms/ and is inert.
note: THIS IS A DECLARATION-GAP INSTANCE OF THE PROJECT'S OWN RECORDED PATTERN --
  a parameter accepted, recorded where a reader would trust it, and inert. The
  association feature family was in the feature list, had a producer, had a
  loader, and read zero. Anyone reading a feature-importance table produced
  before 2026-06-17 saw `association_*` at the bottom and would have concluded
  the SIGNAL was weak. The correct conclusion is that the COLUMN was empty.
  I did NOT verify that such a feature-importance table exists; that is the next
  reader's job (reranker-lab scripts/lm3_feature_importance.py,
  scripts/feature_importance_report.py).

## Q1 (ANSWER, part A): YES -- but the lab's co-occurrence is a PRODUCER, not a stored artifact, and the platform HAS run its own
verdict: CONFIRMED, with the owner's premise CONTRADICTED for the pre-reinstall window
first number: reranker-lab/results/clean_227230/clfassoc/SUMMARY.md:3-11, verbatim:
  "retrained on the NEW platform dataset `clean-learned-clfassoc-train227-test230`
   (learned encoder d8979601, train v160..v227, test v230, k=30, schema 775611822dd9),
   now **WITH compute_classifier (M2) + compute_association (CSR) ON**. The 5
   previously zero-filled features (classifier_score, classifier_present,
   association_total, association_cross, association_present) are populated
   (clf 60.7% nonzero, **assoc 80.6%**)"
  Dated 2026-06-28 in the file's own title line.
second number (INDEPENDENT of the migration, different document, different route):
  the 2026-06-17 alembic migration says rows pre-existed; this 2026-06-28 lab
  summary says an EXPORT carried the association columns at 80.6% non-zero. Two
  documents, two mechanisms, same conclusion: **`build_go_cooccurrence` HAS been
  dispatched, and its output reached a training export.** It cannot be 80.6%
  non-zero out of an empty table.
  A THIRD, from the other direction: reranker-lab/results/clean_a4/RESULTS-clean-A4-reranker.md:26
  records the state BEFORE that run -- "association_total, association_cross,
  classifier_score are ZERO-FILLED in this export (cooccurrence + classifier-seed
  compute flags were off)". So the sequence is documented on both sides of the fix.
date of evidence: 2026-06-17 (migration) and 2026-06-28 (lab summary)
  -> window: **pre-reinstall-lost** for the data, post-wipe-current for the code.
frame: dataset `clean-learned-clfassoc-train227-test230`, schema `775611822dd9`,
  k=30, learned encoder `d8979601`, train v160..v227, test v230, per-category
  LightGBM lambdarank, early stop on the v225-v227 cut, LAFA-exact scoring over
  the 7401 query set, cafaeval `-prop fill -norm cafa -no_orphans -toi`, PK adds
  `-known`, OBO/IA = LAFA t0 Sep 2025. 69 features (64 + the 5 restored).
population: eval 1,198,440 rows; the nine cells with the counts NOT given in this
  summary (they are given in clean_a4: nk-mfo 562, nk-bpo 811, nk-cco 660,
  lk-mfo 452, lk-bpo 1640, lk-cco 482, pk-mfo 1838, pk-bpo 8639, pk-cco 2765).
platform gap: **NONE for producing the co-occurrence.** The debt here is the
  reverse of what was assumed: the platform owns the producer and has run it;
  the LAB owns the CONSUMER (the training that turns it into a model) and the
  platform has none. See the debt table.
note: SO THE CORRECT STATEMENT IS: the tables are empty *on this database*, which
  is 2026-08-27-new. Nothing here says the operation is untested or unproven.
  What was lost is a RUN, and re-running it is a dispatch, not development.

## Q1 (ANSWER, part B): the ARTIFACTS of that run are GONE. Only the claim survives.
verdict: CONFIRMED
first number: the clfassoc SUMMARY.md's own "## Artifacts" section lists six:
  `boosters/booster_{nk,lk,pk}.txt`, `features.json`, `train_info.json`,
  `eval_scores.parquet`, `comparison_9cell.json`, plus the four scripts.
second number: `ls -la results/clean_227230/clfassoc/` returns **5 files**:
  SUMMARY.md, clfassoc_gate_pk.py, clfassoc_lafa.py, clfassoc_train.py,
  lafa_harness.py. All mtime 2026-07-29 01:48 (the re-clone). **Zero of the six
  named artifacts are on disk.** Same for results/clean_a4/: only
  RESULTS-clean-A4-reranker.md and results.json.
date of evidence: filesystem, 2026-09-02 -> window: post-wipe-current
platform gap: MURO-adjacent. The numbers in that SUMMARY (association_total is
  #2 in PK by gain, 1.10M; best_iter NK 186 / LK 87 / PK 4) cannot be collided
  by anyone, because the train_info.json that holds the importances is gone.
  They are now assertions with a method attached, not receipts.
note: **`best_iter` PK = 4.** A LightGBM booster that stops at 4 trees has
  essentially not trained. Any PK number in this table is the number of a model
  that did not fit, and the summary says so ("the PK booster barely trains").
  Also: "Mean (9 cells): 0.355 vs 0.359" is exactly the unweighted nine-cell mean
  CAMPAIGN.md:160-166 forbids, and it is what the verdict paragraph argues against
  itself -- the document reports the forbidden statistic and then explains it away.

## Q2 (ANSWER): NO. The lab holds NO per-release additions/removals decomposition. It holds ONE two-window ADDITIONS-ONLY count, and that file's own numbers imply removals it never reports.
verdict: NOT_FOUND (as asked) / CONTRADICTED-IN-PART (the file contains more than it says)
WHERE I LOOKED, so the negative counts:
  - repositories/protea-reranker-lab, whole tree, for: additions, removals,
    removed, withdraw, obsolete, delta, per release, per-release, release table,
    release history, restoration, restored, first_appearance, first appearance,
    monotone, contraction. (grep -rn over *.py *.md *.json *.csv)
  - results/ (105 files), experiments/ (334), research/ (314), fullgo/ (22),
    datasets/ (18), dataset_cards/ (8), scripts/ (77), src/ (78), tests/ (108).
  - /home/xaxi/Thesis2/storage/ (all 13 subtrees, 369 GB) for the same terms.
  - agent-farm/plans/ and the memory store.
  The only hits in the lab are `scripts/lr1_lineage_delta.py` (an Fmax delta
  between two MODELS, not a corpus delta) and `results/clean_227230/leak_check_overlap.py`
  (a train/eval PAIR-overlap leak check, 7.4%, not a corpus decomposition).
first number: the single closest artifact is
  /home/xaxi/Thesis2/repositories/protea-reranker-lab/experiments/lafa_ia_v227_protocol/band_shift.json
  (1568 bytes, "Computed read-only against the PROTEA DB on 2026-06-04"). It holds:
    annotation_pair_counts: v226 5,902,876 | v227 5,875,943 | v230 4,767,114
    distinct_proteins:      v226   556,468 | v227   556,447 | v230   552,967
    newly_true_pairs:       v226_to_v230 125,026 | v227_to_v230 79,199
  and its own SQL, quoted in the file, is a pure `EXCEPT`:
    "SELECT ... WHERE annotation_set_id='<v230>' EXCEPT SELECT ... WHERE annotation_set_id='<v226>'"
  That is the PAIRWISE DIFFERENCE that DECISION-LOG D-02 (2026-07-28) retired.
  It counts additions and is silent on removals.
second number (INDEPENDENT, and it is arithmetic on the file's own three counts):
  |new| = |old| - removed + added, so removed = |old| + added - |new|.
    v226 -> v230: removed = 5,902,876 + 125,026 - 4,767,114 = **1,260,788**
    v227 -> v230: removed = 5,875,943 +  79,199 - 4,767,114 = **1,188,028**
  So in the window the campaign calls VALIDATION, the corpus REMOVED
  **1,260,788 pairs while adding 125,026** -- removals are **10.1x** the
  additions (15.0x on the v227 band). The file reports the 125,026 as the
  headline and does not compute the 1.26M, though it printed every number
  needed to. **The decomposition Q2 asks for is one subtraction away from an
  artifact that already exists, and nobody did the subtraction.**
  A second, orthogonal reading of the same rows: distinct proteins fall only
  3,501 (0.63%) while pairs fall 1,135,762 (19.2%). The contraction is
  annotations being stripped from proteins that REMAIN, not proteins leaving.
  That distinguishes an evidence-class or source-DB withdrawal from a
  deproteome event, which is exactly the diagnosis CAMPAIGN.md slice 3 wants.
date of evidence: 2026-06-04 -> window: **pre-reinstall-lost** (the three
  annotation_set UUIDs it names -- v226 5e1a7285, v227 c905dffa, v230 2394b9a1 --
  are ids in a database that was reinstalled 2026-07-28 and wiped 2026-08-27).
frame: NO evidence filter (raw protein_go_annotation rows, so IEA included), NO
  aspect split, NO propagation stated, NO category split. Pairwise, not first
  appearance. The 10.1x figure above therefore inherits that frame and is an
  ALL-EVIDENCE number; it is NOT the experimental-evidence regime.
population: the whole corpus, 556k proteins. NOT the nine cells.
platform gap: **the operation does not exist, and this is real debt.**
  What the platform has: `protea/core/first_appearance.py` (a pure library:
  `pairwise_additions`, `restoration_report`, `RestorationReport.restoration_rate`,
  `NotEnoughHistoryError`) and `protea/core/evaluation.py:305-350`, which computes
  a `removed` bucket per protein for ONE window pair and carries it in
  `EvaluationData` (`removed_proteins`, `removed_annotations`, :136-141) and into
  the serialized ground-truth buckets (`_GROUNDTRUTH_BUCKETS` at :60).
  What the platform does NOT have:
   (a) no operation that walks the RELEASE HISTORY and emits a per-window row;
   (b) no ORM model and no column anywhere holding an additions/removals count
       (`grep -rn removed protea/infrastructure/orm/models/` returns three
       unrelated docstring hits -- user_quota, job.py x2 -- and nothing else);
   (c) `restoration_report` has NO caller in any operation.
  The operation that would have to exist: `decompose_release_deltas`, payload
  `{annotation_set_ids: [ordered], evidence_filter, propagate}`, writing one row
  per ordered pair to a NEW table (`release_delta`) with columns
  (from_set, to_set, aspect, evidence_regime, added, removed, restored,
  first_appearance_added, proteins_gained, proteins_lost, elapsed_days).
  Difficulty: LOW-MEDIUM. It is three set differences per pair over
  `protein_go_annotation`, which `band_shift.json` proves is a plain SQL EXCEPT;
  the only new work is the migration and the first-appearance pass, and the
  first-appearance logic is ALREADY WRITTEN and tested in first_appearance.py.
  Dependency rank: **HIGHEST IN THIS SLICE.** CAMPAIGN.md:466 slice 6 (the split
  registry) is explicitly blocked on it: "Runs AFTER slice 3, since the adjustment
  windows cannot be chosen before additions and removals are decomposed", and
  split_registry.py:267-275 refuses to name the adjustment windows for the same
  reason, in code, at runtime.
note: THE 63.7% IS AN ORPHAN. "Over eleven consecutive releases, as much as 63.7%
  of apparent additions on all-evidence data had been seen before" appears in
  four places -- agent-farm/plans/CAMPAIGN.md:172, agent-farm/plans/DECISION-LOG.md:103,
  protea/core/first_appearance.py:14-19, protea/core/split_registry.py:383-388.
  All four are the SAME sentence; three are ECHOES of the DECISION-LOG entry.
  I searched the lab, storage/ (369 GB), agent-farm/ and the memory store for the
  probe that produced it: **no script, no JSON, no CSV, no log holds it.**
  There is no eleven-release table anywhere on this disk. The number that
  retired the project's ground-truth rule is a summary with no surviving
  breakdown and therefore cannot be collided by anyone, which is the exact
  failure COLLIDING-A-NUMBER rule 2 exists to prevent.

## THE SEAM: exactly where the platform stops and the lab starts
verdict: CONFIRMED
first number: the platform's only outbound handoff is
  `export_research_dataset` (+ the four export minijobs `export_coordinator`,
  `export_knn_batch`, `export_features_batch`, `export_write`), which writes
  train/eval parquet + a manifest to MinIO. Its docstring
  (worktrees/protea-deploy/protea/core/operations/export_research_dataset.py:1-20)
  says outright: "Runs the same KNN + feature-generation pipeline ... **skips the
  LightGBM training stage**".
second number: the platform's only inbound handoff is the API, not an operation:
  `POST /reranker-models/import` (multipart, worktrees/protea-deploy/protea/api/routers/reranker_models.py:316)
  and `POST /reranker-models/import-by-reference` (:458-464). The lab's client is
  reranker-lab/scripts/upload_model.py, whose docstring names the endpoint.
  So a model enters the platform as a FILE plus metadata. Nothing in the platform
  produced it and nothing can reproduce it.
date of evidence: platform `a5de702` (2026-09-01) -> post-wipe-current
platform gap: the whole middle. Between the export and the import there is no
  operation, no job, no queue, no row.
note: the seam is also a TRANSCRIPTION seam, which is a second, quieter debt.
  worktrees/protea-deploy/protea/core/_universal_reranker.py:18-35 states that it
  "reproduces the lab's *authoritative* scoring path
  (protea_reranker_lab.pooled_staging._inject_src_features + _encode_cat_batch)
  **bit-for-bit**", and pins the sentinel `CAT_MISSING_CODE = -1` (:47-50) as a
  MIRROR of `protea_reranker_lab.bucket_io.CAT_MISSING_CODE`. It records a
  validation: "Validated 2026-06-08 ... bit-identical (max abs diff 0.0 over
  226590 rows)". That is a good collision -- BUT it is a POINT-IN-TIME one, dated
  2026-06-08, and nothing re-runs it. Two copies of a categorical encoder in two
  repositories, kept equal by a comment and a three-month-old check.

## THE LAB PIN IN PROTEA IS UNRESOLVABLE ON THIS MACHINE
verdict: CONFIRMED
first number: worktrees/protea-deploy/pyproject.toml:139
  `protea-reranker-lab = {git = "...", rev = "6d4dc2d4b5330485b8830b20f7789356af7be1d4"}`
  (test group, optional; pulled in because test_predict_go_terms.py and
  test_reranker.py assert schema parity with the offline trainer, :121-123).
second number: in /home/xaxi/Thesis2/repositories/protea-reranker-lab,
  `git cat-file -t 6d4dc2d4b5330485b8830b20f7789356af7be1d4` -> "fatal: could not
  get object info". Not on develop, not on main, not on any of the 17 remote refs
  in .git/packed-refs, not in `git rev-list --all` (198 objects abbreviated).
  WHY: the pin was set by PROTEA commit `2250dd1` on **2026-08-29**
  ("chore(deps): the contract reaches the fleet..."), and this lab clone's last
  fetch was **2026-08-18** (.git/FETCH_HEAD mtime, corroborated by the lab-state
  slice). So the pinned commit is eleven days newer than anything this machine has.
date of evidence: 2026-08-29 (pin) vs 2026-08-18 (last fetch) -> window: post-wipe-current
platform gap: none; this is an operational fact, not a missing operation.
note: SCOPE OF THE NEGATIVE -- I looked in the local clone only. I did NOT reach
  GitHub. So the honest statement is "unresolvable offline on the compute node",
  NOT "the commit does not exist". The consequence is real either way: PROTEA's
  test group cannot be provisioned here without network, and the lab checkout on
  this disk is NOT the version the platform declares it depends on.

---

# THE DEBT TABLE
# Every capability the lab has that the platform does not, ranked by how much
# depends on it. "Writes" = what the operation would put in the database.

## D1. RERANKER TRAINING (LightGBM, per-category and universal). RANK 1.
verdict: CONFIRMED, and it is a DELIBERATE removal, not an omission
lab surface: src/protea_reranker_lab/{reranker,runner,train,staging,splits,
  bucket_io,sequences,data,universal_runner,universal_train,pooled_staging,
  multi_source,k_augmentation,native_boosters,combiner,experiment,schemas}.py
  = 16 modules, ~5,900 lines, plus scripts/run_study.py, run_universal_booster.py,
  train_native_boosters.py, run_clean_a4_reranker.py, run_transversal_grid.py.
platform surface: NONE. operation_catalog.py:120-124 removed
  TrainRerankerOperation / TrainRerankerAutoOperation from the public registry
  with the comment "all re-ranker training moves to protea-reranker-lab".
the operation that would have to exist: `train_reranker`, payload
  {dataset_manifest_uri, cells|universal, objective, ia_weighted, k_augment,
   seed, num_boost_round, early_stopping_rounds, feature_schema_sha}.
writes: a `RerankerModel` row (the table already exists, with `external_source`,
  `feature_schema_sha`, `dataset_id`, metrics) + the booster into the artifact
  store. The DB SHAPE IS ALREADY THERE -- only the producer is missing.
difficulty: MEDIUM-HIGH. Not the algorithm (LightGBM is a dependency), but the
  STAGING: bucket routing by crc32(protein_accession) so a LambdaRank group never
  crosses a bucket, the (protein, snapshot_pair, aspect, plm_id) group key
  (splits.py:_compute_group_edges), streaming lgb.Sequence over sorted parquet,
  and the categorical vocabulary that _universal_reranker.py already mirrors.
  ~2,600 lines of the lab's staging layer is the real work.
what depends on it: EVERYTHING downstream. Every champion, every board number,
  rungs 4 and 5, and the reranker half of the thesis.

## D2. THE PER-RELEASE ADDITIONS/REMOVALS DECOMPOSITION. RANK 2.
See Q2 above. Neither side has it. `decompose_release_deltas` -> new
`release_delta` table. Difficulty LOW-MEDIUM. Blocks CAMPAIGN slice 6 (the split
registry) BY DECLARATION, in code, at split_registry.py:267-275.

## D3. LEARNED-ENCODER FITTING. RANK 3.
verdict: CONFIRMED, and this is the CLEANEST named seam in the project
lab surface: encoder_ablation.py (780 lines, the fit/apply split, PR #100
  "persist a production encoder (fit/apply split)"), chunk_attn_encoder.py (355),
  objectives.py (151), scripts/train_learned_encoder.py, run_encoder_ablation.py,
  run_attn_pool_learned.py, run_compose_pool_learned.py, run_softpool_learned.py.
platform surface: `apply_learned_encoder` ONLY. Its docstring
  (protea/core/operations/apply_learned_encoder.py:1-24) says "trained **offline
  in protea-reranker-lab**" and then enumerates the artifact format it must be
  handed: `{"state_dict": Linear, "meta": {in_dim, dict_dim, top_k}}` "from
  protea_reranker_lab.encoder_ablation", and the attention variant "from
  protea_reranker_lab.chunk_attn_encoder".
the operation: `fit_learned_encoder`, payload {source_embedding_config_id,
  objective, dict_dim, top_k, pooling, train_protein_set, seed}.
writes: an artifact + a new `EmbeddingConfig` row (model_backend="learned-code");
  `apply_learned_encoder` then materialises `SequenceEmbedding` rows. Again the
  consumer side is complete and only the producer is missing.
difficulty: MEDIUM. Torch on the GPU, which this node has. The constraint is the
  12 GB card and the residue-budget batching rule, not the algorithm.
what depends on it: rung 2 in full, and the learned-encoder datasets the
  clfassoc result was trained on (`learned encoder d8979601`).

## D4. PER-ASPECT SCORE CALIBRATION. RANK 4.
lab surface: calibration.py (303 lines), "Fits one calibrator per GO namespace
  (MFO, BPO, CCO) on the VALID window predictions".
platform surface: NONE. `run_cafa_evaluation` picks a threshold; nothing fits a
  calibrator, and the predict path applies none.
the operation: `fit_score_calibration` -> `apply_score_calibration`.
writes: a `ScoreCalibration` row (does not exist) keyed by
  (prediction_set, aspect, method) holding the fitted parameters.
difficulty: LOW. The maths is small; the frame discipline is the work (it must
  fit on the ADJUSTMENT split and never on validation).
what depends on it: the calibration wall, which the memory store records as
  "mechanism confirmed, effect below the DETECTION FLOOR" -- i.e. it has never
  been measured with power, and it cannot be while the producer is a lab script.

## D5. HIERARCHY POST-PROCESSING: hard true-path correction and soft Pmin/Pmax. RANK 5.
lab surface: hierarchical_correction.py (171), soft_propagation.py (180),
  condprobmod.py (260, "the single biggest external ablation lever reported by
  ProtBoost (~+0.04 IA-Fmax)"), propagation.py (83),
  scripts/apply_hierarchy_postproc.py, scripts/export_parent_map.py.
platform surface: propagation exists INSIDE the evaluator (cafaeval `-prop fill`)
  and inside build_go_cooccurrence's ancestor closure, but there is NO operation
  that post-processes a stored prediction set for hierarchical consistency.
the operation: `apply_hierarchy_postprocess`, payload {prediction_set_id, mode:
  hard|soft_pminmax|condprobmod, ontology_snapshot_id}.
writes: a NEW `PredictionSet` (derived), so the pair is comparable by
  `compare_paired_panels`, which already exists.
difficulty: LOW-MEDIUM. The DAG walk is the only cost and the snapshot is loaded.
what depends on it: a claimed ~+0.04 IA-Fmax lever that has never run in-platform.

## D6. CANDIDATE-RECALL CEILING PER CELL. RANK 6.
lab surface: recall.py (330 lines). "Recall is the CEILING metric for any
  reranker: it can only rank what the retrieval stage surfaced."
platform surface: NONE. `stratify_evaluation` stratifies a finished evaluation;
  nothing measures what fraction of the truth the RETRIEVAL stage ever offered.
the operation: `measure_candidate_recall`, payload {prediction_set_id or
  export manifest, evaluation_set_id}.
writes: rows on the nine cells (category x aspect) with
  (n_groups, n_truth, n_truth_in_candidates, recall_ceiling).
difficulty: LOW. It is a set intersection over the candidate pool.
what depends on it: every "the reranker did not help" verdict. Without the
  ceiling, a flat result cannot be attributed to the scorer or to the pool --
  and the clfassoc SUMMARY's own conclusion ("Cause is the candidate POOL, not
  the scorer") is exactly that attribution, made without the ceiling number.

## D7. THE SPARSE FUNCTIONAL CLASSIFIER (the prior-knowledge generator). RANK 7.
lab surface: results/sparse_classifier/ = 19 sub-studies, plus fullgo/
  train_classifier.py, train_classifier_m2.py, build_per_cut_codes.py.
platform surface: NONE for training. The predict path has a
  `compute_classifier` flag (the clfassoc summary names "compute_classifier (M2)"),
  so the CONSUMER exists and the producer does not -- the same shape as D3.
the operation: `train_functional_classifier`; writes a model artifact + a
  registry row of its own (no table exists).
difficulty: MEDIUM.
what depends on it: rung 3, and `classifier_score` which the clfassoc run found
  to be **the #1 feature in all three categories**.

## D8. STUDY ORCHESTRATION, CROSS-FIT AND CHAMPION SELECTION. RANK 8.
lab surface: experiment.py, runner.py, scripts/build_study_specs.py,
  run_study.py, summarise_study.py, evaluate_study.py, update_champions.py,
  phase3d_val227_champion_select.py, fullgo/select_cv.py, champions.md.
platform surface: NONE. There is no notion of a "study" in the platform;
  a job is one operation.
writes: a `Study` / `StudyArm` pair of tables that do not exist.
difficulty: HIGH -- this is a scheduler question, and the memory store already
  carries a backlog item for a DAG scheduler redesign.
note: CAMPAIGN slice 16 ("the cross-fit gate") is this.

## D9. SEED ENSEMBLING AND SEALING. RANK 9.
lab surface: fullgo/seed_average.py, ensemble_seal.py, rescorer_seal.py,
  fuse_eval.py, lb2_multiseed_sweep.py, v27_binary_multiseed_sweep.py,
  farm_exp_14_grid_sweep.py.
platform surface: NONE. `seal_evaluation_frames` seals a FRAME, not an ensemble.
what depends on it: rung 5 in full (all three ensembling forms).

## D10. THE SDR / COMPACTION STUDY HARNESS. RANK 10.
lab surface: sdr.py, sdr_pool.py, compaction_quality.py + 12 run_sdr_*.py.
platform surface: `encode_residue_sparse` (+ batch) exists, so the platform can
  PRODUCE per-residue sparse codes; it cannot measure how much signal a
  compaction preserves.
difficulty: MEDIUM.

## D11. IA SAMPLE WEIGHTING FOR TRAINING. RANK 11.
lab: ia_weighting.py (92 lines). platform: `compute_information_accretion`
  produces the IA TABLE; nothing turns IA(go) into a per-row training weight,
  because nothing trains. Folds into D1.

## D12. NEGATIVE-SAMPLING AUDIT. RANK 12.
lab: negative_sampling_audit.py (154 lines), "an explicit audit report that
  certifies" the balanced sampler. platform: none. Folds into D1 as its gate.

---

# THE WALLS: what CANNOT move into the platform, and why

## W1. MURO -- The board. The validation metric is not ours to compute.
verdict: CONFIRMED, in code
evidence: worktrees/protea-deploy/protea/core/split_registry.py:279
  `SplitName.VALIDATION: Split(..., scored_by="the board", may_inform=frozenset(), balanced=False, ...)`
  and :12-14 "validation is the board's window and everything after it. It is
  scored by the board, and it informs **nothing**."
reason: no operation can produce the comparable number. The platform can compute
  its own f_micro_w on that window and the campaign explicitly forbids treating
  it as the same object. The lab's `WE_DO_NOT_REPRODUCE_THE_BOARD.md`
  (reranker-lab/research/regen_headline/) is the lab's own statement of the same
  wall from the other side.
what this means for the invariant: "no artifact without a registered operation"
  cannot cover the headline number. The most important number in the thesis is
  produced by a third party, and the campaign is right to designate ONE point of
  the series as comparable rather than pretend otherwise.

## W2. MURO -- Exploration. A registry needs a declared payload; a probe does not have one.
verdict: DEDUCED-NOT-MEASURED, and marked as such
evidence: COLLIDING-A-NUMBER.md, closing paragraph: "None of this applies to
  exploration. Look at whatever you like, guess freely, run the wrong thing on
  purpose."
reason: an operation is a NAMED, VERSIONED, VALIDATED payload. The 82 files in
  research/cooc_experiment/ are named `sweep_diag.py`, `nan_the_lying_zeros.py`,
  `resolve_contradiction.py`, `technique_probe.py`, `parser_path_killtest.py`.
  Those are questions, asked once. Forcing each into a registered operation
  would cost more than the answer is worth and would make the registry a landfill.
the honest boundary: a procedure earns an operation when its OUTPUT is cited.
  The lab is right to exist; the debt is not "the lab exists", it is "results
  from the lab are cited as platform results". Everything in the debt table above
  is a procedure whose output IS cited.
note: this is a DEDUCTION from what an operation is, not a measurement. It needs
  colliding: the minimal case that would separate it is a script that was written
  as a one-off probe and then became load-bearing. `fullgo/assoc_feature.py` IS
  that case -- it was a probe, it became "the lever that took us past TransFew"
  (fullgo/RESULTS.md:49), and it was transcribed into `build_go_cooccurrence`.
  So the wall is real but the line moves, and nothing watches it move.

## W3. MURO (practical, not schema) -- the per-residue bank does not fit the database.
verdict: CONFIRMED
evidence: `SequenceEmbedding.embedding` is `pgvector.sqlalchemy.HALFVEC`, ONE
  vector per row (protea/infrastructure/orm/models/embedding/sequence_embedding.py:64),
  with `chunk_index_s`/`chunk_index_e` (:61-63) so per-CHUNK rows are legal.
  storage/probe/ holds 347 GB across 19 files; `confirmation.npy`'s header reads
  `{'descr': '<f4', 'fortran_order': False, 'shape': (1109436, 1, 768), }`
  (bytes 0-118 of the file, read by hand).
reason: the schema permits one row per chunk. It does not survive one row per
  RESIDUE at corpus scale, and the project's hard constraint forbids pgvector for
  neighbour search anyway. So D10 (compaction quality) and the residue half of D3
  keep their substrate on the filesystem whatever operation is written.
the operation that IS possible: an operation that CONSUMES a filesystem bank and
  writes only the derived code + the measurement rows. The bank stays an input,
  the way a GOA dump is an input.

## W4. NOT A WALL, but permanently lost: everything under /home/frapercan.
verdict: CONFIRMED
evidence: `ls /home/` returns exactly one directory, `xaxi`. The lab hardcodes
  `/home/frapercan/...` in at least: fullgo/assoc_feature.py:17 (the OBO),
  results/clean_227230/leak_check_overlap.py:10-13 (scratchpad, OBO, IA, and
  `PROTEA_PY = "/home/frapercan/Thesis2/repositories/PROTEA/.venv/bin/python"`),
  and all 82 files in research/cooc_experiment/ (working dir
  `/home/frapercan/Thesis2/storage/cooc_experiment`).
  Note the leak-check's working directory:
  `/tmp/claude-1000/-home-frapercan-Thesis2/afd2c43a-.../scratchpad` -- the
  champion's training and eval parquet lived in an AGENT SCRATCHPAD under /tmp.
reason: the reinstall changed the user name. The lab already recorded this exact
  wound and its mechanism, in src/protea_reranker_lab/host_paths.py:1-19:
    "That worked until the machine was reinstalled under a different user name,
     at which point the paths pointed at nothing. **Nothing raised**: the ground
     truth directory was passed to a subprocess that failed, the failure was
     caught and turned into an error dictionary, the metric became ``None``, and
     the run wrote ``status: ok`` with every cell empty."
  host_paths.py is the FIX (env var, then checkout-relative, then raise), and it
  is applied to four locations only -- thesis_root, ground_truth_dir,
  protea_python, ia_table. The 82 cooc_experiment files were never migrated to it.
note: this is the single most useful sentence in the lab for a platform owner.
  A silent `status: ok` with empty cells is the failure mode that ALSO applies to
  every operation whose input is a path. It is the same shape as the association
  columns reading zero.

---

# THE FINDING THIS SLICE DID NOT EXPECT
# A published feature-importance conclusion drawn from columns that were empty.

## 19 of the champion's 34 features have EXACTLY 0.0000 gain in ALL NINE cells, and the summary reads six of them as a result
verdict: CONFIRMED (the zeros) / the INTERPRETATION is a declaration-gap defect
first number: the published prose,
  /home/xaxi/Thesis2/repositories/protea-reranker-lab/experiments/lm3/feature_importance_summary.md,
  "### BPO" interpretation, verbatim:
    "The alignment family (identity_nw, alignment_score_*, etc.) **scores zero
     gain in every BPO cell, confirming that sequence-level similarity
     information adds nothing** once KNN vote and distance features are included."
second number (INDEPENDENT, computed by me from the raw CSV the summary cites):
  experiments/lm3/feature_importance_per_aspect.csv, 306 data rows = 34 features
  x 9 cells (matches champions.md's "34 features"). Counted with awk:
    - **189 of 306 gain values are exactly 0.0000 (61.8%).**
    - **19 of the 34 features are 0.0000 in ALL NINE cells (9/9):**
      alignment_length_nw, alignment_length_sw, alignment_score_nw,
      alignment_score_sw, gaps_pct_nw, gaps_pct_sw, identity_nw, identity_sw,
      similarity_nw, similarity_sw   <- the whole alignment family, 10 features
      taxonomic_common_ancestors, taxonomic_distance, taxonomic_relation,
      tax_voters_close_frac, tax_voters_mean_common_ancestors,
      tax_voters_same_frac                <- the whole taxonomy family, 6 features
      length_query, length_ref            <- protein sequence length
      aspect                              <- a reserved grouping key, correctly 0
  So **only 15 of 34 features ever split a tree in any of the nine boosters.**
WHY THIS IS NOT "no signal": three collisions, each of which could have failed.
  (a) `length_query` and `length_ref` are the protein's own sequence length.
      Protein length is AXIS 3 of this project's own mandatory stratification.
      A length feature with exactly 0.0000 gain in nine independently trained
      boosters is not a model declining a signal; it is a constant column.
  (b) The taxonomy family is 6/6 zero, and the SAME features appear as live
      evidence ports in a later run: results/clean_a4/RESULTS-clean-A4-reranker.md:29-33
      lists "taxonomy (`taxonomic_distance`)" inside "the per-category real
      evidence vector". A feature cannot be inert-by-nature in one export and a
      named evidence port in the next.
  (c) The zeros are EXACT (0.0000) and UNANIMOUS. Nine boosters, three seeds
      elsewhere, three aspects, three categories, and not one of 171 values is
      even a small positive. Gain from a weak-but-present feature is small, not
      identically zero across nine fits.
  WHAT WOULD FALSIFY ME: a single nonzero gain for any of the 19 in any cell
  (there is none, checked with `awk -F, '$5+0!=0'` -> 0 rows), or an export
  manifest showing `compute_alignments` / taxonomy on for `study_v23`. THE
  MANIFEST IS NOT ON DISK, so I cannot close this to CONFIRMED-MECHANISM. The
  zeros are confirmed; the empty-column cause is strongly indicated, not proven.
date of evidence: boosters registered 2026-05-14, summary + CSV committed
  2026-07-29 -> window: **pre-wipe AND pre-reinstall**. Not evidence about now.
frame: LightGBM gain (total information gain over all splits of all trees), seed
  42, `runs/study_v23`, the nine `v226full_lineage_<cell>` boosters, dataset
  `bench-v1-K5-v226-lineage-prostt5`, eval window v226-v230, cafaeval prop=fill,
  norm=cafa, no_orphans, max_terms=500, th_step=0.001. Aggregation in the summary
  is MEAN RANK across the three categories per aspect -- a rank average over three
  populations of different size, which the campaign's own rule forbids pooling.
population: all nine cells, counts NOT given in either file.
platform gap: `stratify_evaluation` and `compare_paired_panels` exist for
  METRICS. Nothing in the platform records a trained model's feature importances
  or, more importantly, **a per-column non-constant assertion on the export**.
  The operation that would have prevented this: a gate inside
  `export_research_dataset` (or a new `audit_export_columns`) that writes, per
  feature column, (n_rows, n_nonnull, n_distinct, min, max) to a
  `dataset_column_stats` table and FAILS the export when a declared feature is
  constant. Difficulty: LOW. It is one pass over the parquet at write time.
note: THE SUMMARY DID NOT NOTICE 13 OF THE 19. It explains the alignment zeros
  and says nothing at all about taxonomy, length_query or length_ref, which are
  equally and identically zero. This is the project's recorded pattern exactly
  (`project_declaration_gap_pattern_2026_08_18`, "seven defects, one shape: a
  plausible number over the wrong population") and COLLIDING-A-NUMBER rule 4
  ("a zero, a green suite, an empty diff... each is evidence only if the check
  could have failed"). The conclusion "sequence-level similarity adds nothing"
  should be treated as WITHDRAWN until an export with the alignment columns
  demonstrably populated is trained. It is currently a statement about a column.
cross-check for the reader: the lab README (PR #116, 2026-07-28) already
  withdraws all lab results -- "Nothing in this file should be cited as a
  result." But that withdrawal lives ONLY in README.md and champions.md.
  I grepped all 19 result/experiment markdown files under results/, experiments/
  and fullgo/ for withdraw|retract|not current|do not cite|superseded: **only
  experiments/farm_exp_10/multiseed_summary.md and champions.md carry any such
  marker.** feature_importance_summary.md, results/clean_227230/clfassoc/SUMMARY.md,
  results/clean_a4/RESULTS-clean-A4-reranker.md, fullgo/RESULTS.md and thirteen
  others read as current. A withdrawal that lives in one file is not a withdrawal.

## MECHANISM CLOSED: the 19 zeros are EXACTLY the two default-False export flags, plus the grouping key
verdict: CONFIRMED (this upgrades the previous entry from "strongly indicated" to mechanism-confirmed)
first number: my count from the CSV -- 19 features at 0.0000 gain in 9/9 cells.
second number (INDEPENDENT, from the platform + the contracts package, neither of
  which I had consulted when I counted):
  worktrees/protea-deploy/protea/core/operations/export_research_dataset.py:71-72
    `compute_alignments: bool = False`
    `compute_taxonomy: bool = False`
  and :78, the platform's own words: "feature values the predict path serves
  (**not the zero-fill defaults**)".
  Now the family partition, from protea-contracts `FEATURE_FAMILIES`
  (/home/xaxi/.cache/pypoetry/virtualenvs/protea-M-JALCmz-py3.12/src/protea-contracts/src/protea_contracts/feature_schema.py:180-205):
    alignment_nw = identity_nw, similarity_nw, alignment_score_nw, gaps_pct_nw, alignment_length_nw   (5)
    alignment_sw = identity_sw, similarity_sw, alignment_score_sw, gaps_pct_sw, alignment_length_sw   (5)
    length       = length_query, length_ref                                                            (2)
    taxonomy_pair   = taxonomic_distance, taxonomic_common_ancestors, taxonomic_relation               (3)
    taxonomy_voters = tax_voters_same_frac, tax_voters_close_frac, tax_voters_mean_common_ancestors    (3)
  and the length family's PRODUCER, from feature_docs.py:400-418:
    `producer = "..._alignment_fields (from pair features)"` -- length rides the
    SAME producer as the alignment family, so `compute_alignments=False` takes
    length_query and length_ref down with it. The docs say so for the alignment
    features in as many words: "Populated when the ``compute_alignments`` export
    flag is enabled; **null otherwise**."
  ARITHMETIC:  5 + 5 + 2 = 12  (compute_alignments)
               3 + 3     =  6  (compute_taxonomy)
               + 1 `aspect`, a RESERVED grouping key that is correctly never a feature
               = **19.  Exactly the 19 I counted, name for name, with nothing left over.**
date of evidence: platform code `a5de702` (2026-09-01) and contracts as installed;
  the CSV is the 2026-05-14 boosters -> window: pre-wipe / pre-reinstall for the run.
frame: as above (study_v23, bench-v1-K5-v226-lineage-prostt5, seed 42).
population: nine cells.
THE CONCLUSION, stated plainly:
  **The project's registered champion -- the nine `v226full_lineage_<cell>`
  RerankerModel rows, imported into the platform on 2026-05-14, and the
  configuration champions.md still names -- was trained on an export dispatched
  with `compute_alignments` and `compute_taxonomy` left at their DEFAULT False.
  Eighteen of its thirty-four declared features were structurally absent. It is
  a fifteen-feature model wearing a thirty-four-feature label.**
  And `experiments/lm3/feature_importance_summary.md` reads six of the absent
  eighteen as a scientific finding about sequence similarity.
platform gap: the operation that would have caught this at the source is a
  column-population gate. `export_research_dataset` ALREADY records the flags in
  its manifest (:350-351 `"compute_alignments": p.compute_alignments,
  "compute_taxonomy": p.compute_taxonomy`), so the export KNOWS. What is missing
  is (a) writing per-column population stats to the database, and (b) refusing to
  register a `RerankerModel` whose `feature_schema_sha` declares columns the
  producing dataset never populated. The RerankerModel row already carries
  `feature_schema_sha` and `dataset_id` (protea/api/routers/reranker_models.py:104,
  :169), so the join needed for the check exists. Difficulty: LOW.
  Rank: this belongs at **RANK 2** of the debt table, above everything but the
  trainer itself, because it is the cheapest guard that would have voided a
  wrong champion before it was served.
note: this is the FIFTH instance of the project's own recorded shape -- a
  parameter accepted, recorded where a reader would trust it, and inert. The
  previous four are named in COLLIDING-A-NUMBER.md section 4, and `own_k` is
  called out there as the fourth. This is the fifth, it is larger than the other
  four, and it sat inside the champion.
  I did NOT find the study_v23 export manifest on disk, so I cannot read the
  flags as dispatched. The mechanism is closed by the EXACT set match (19 = 12 +
  6 + 1, with no residual and no missing member), not by the manifest. A reader
  who wants the manifest should look for the dataset row
  `3517bc8b-4562-49e0-8c67-99afc5fdc67f` (named in reranker-lab
  scripts/lr1_lineage_delta.py:20-23) -- which is a row in a database that has
  been wiped, so it is very likely gone.

---

# CLOSING: what has to be rebuilt, in order, and what is simply gone

## The order the debt should be paid, and why this order
1. **`audit_export_columns` / the column-population gate** (LOW). Cheapest, and
   it retro-actively voids or confirms every model already registered. Nothing
   else should be trained until an export can prove its columns are populated.
2. **`decompose_release_deltas`** (LOW-MEDIUM). Blocks the split registry BY
   DECLARATION (split_registry.py:267-275 refuses to name the adjustment windows
   without it), and the split registry blocks every honest measurement after it.
   Q2's arithmetic (removals 10.1x additions in the validation window) says the
   answer will not be a formality.
3. **Dispatch `build_go_cooccurrence`** (ZERO development). The operation exists,
   is tested, has a loader and a consumer, and has run before. This is a job, not
   a project. It restores the feature the lab measured as #2 in PK and #3 in LK.
4. **`train_reranker`** (MEDIUM-HIGH). Everything downstream.
5. **`fit_learned_encoder`** (MEDIUM). Rung 2.
6. **`measure_candidate_recall`** (LOW). Without it, every "the reranker did not
   help" verdict is unattributable between the pool and the scorer -- and the
   clfassoc summary already made that attribution without the number.
7. Then D4 calibration, D5 hierarchy, D7 classifier, D8 studies, D9 ensembling,
   D10 compaction.

## What is simply gone, and cannot be recomputed from anything on this disk
- Every derived artifact of `research/cooc_experiment/` (82 procedures, all
  writing to `/home/frapercan/Thesis2/storage/cooc_experiment`, a path on a
  user account that no longer exists).
- The six artifacts the clfassoc SUMMARY names (boosters, features.json,
  train_info.json, eval_scores.parquet, comparison_9cell.json) and the clean_a4
  equivalents. The summaries survive as unfalsifiable claims.
- The eleven-release restoration probe that produced 63.7%. Four documents quote
  it; none holds it; nothing on this disk can regenerate it. It is the number
  that retired the project's ground-truth definition.
- The champion's training data, which lived in
  `/tmp/claude-1000/-home-frapercan-Thesis2/afd2c43a-.../scratchpad` (read
  straight out of results/clean_227230/leak_check_overlap.py:10). A /tmp path on
  a reinstalled machine.
- The three annotation-set UUIDs band_shift.json names (v226 5e1a7285,
  v227 c905dffa, v230 2394b9a1) and the dataset UUID the nine champion boosters
  point at (3517bc8b-4562-49e0-8c67-99afc5fdc67f). Rows in a wiped database.

## What SURVIVED and is worth more than it looks
- **`experiments/lm3/feature_importance_per_aspect.csv`** (306 rows). The one
  artifact in the lab that let a stranger overturn a published conclusion, and
  it survived only because it is 13 KB of text committed to git. Everything the
  same study asserted in prose is uncheckable; the one file with the breakdown
  in it is the one that broke. This is COLLIDING-A-NUMBER rule 2, demonstrated.
- **`src/protea_reranker_lab/host_paths.py`**. The lab's own post-mortem of the
  reinstall, with the failure mode named: a missing path expressed as a DEFAULT
  rather than a REQUIREMENT, producing `status: ok` with every cell empty. Four
  locations were migrated to it; the 82 cooc_experiment files were not.
- **`experiments/lafa_ia_v227_protocol/band_shift.json`**. Contains the removals
  decomposition implicitly and never states it. One subtraction from being the
  artifact CAMPAIGN slice 3 asks for.

## SEARCH LOG for this slice (so the negatives can be priced)
Read or grepped: the whole of repositories/protea-reranker-lab (1,213 files
across src/ 78, research/ 314, experiments/ 334, scripts/ 77, docs/ 55,
datasets/ 18, dataset_cards/ 8, results/ 105, fullgo/ 22, tests/ 108, plus git
log and all 17 remote refs); worktrees/protea-deploy operation_catalog.py,
build_go_cooccurrence.py, export_research_dataset.py, apply_learned_encoder.py,
compare_paired_panels.py, stratify_evaluation.py, compute_information_accretion.py,
first_appearance.py, split_registry.py, evaluation.py, _universal_reranker.py,
sequence_embedding.py, reranker_models.py, pyproject.toml, and two alembic
revisions; the installed protea-contracts feature_schema.py + feature_docs.py;
agent-farm/plans/{COLLIDING-A-NUMBER,CAMPAIGN,DECISION-LOG,GENESIS-STATE}.md;
storage/ (all 13 subtrees, du'd, and probe/ headers read by hand);
storage/coordination/{CHECKLIST.md,rescued/*}; the memory store index.
NOT done (out of scope or forbidden): no database connection of any kind; no
network; no read of the other auditors' census files beyond lab-state.md's head,
to keep this slice independent.

Status: COMPLETE. Written 2026-09-02.
