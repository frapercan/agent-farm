# Census slice: operational-and-findings

Auditor slice key: `operational-and-findings`
Started: 2026-09-02

## Slice description
plans/executor/, farm-platform/, dag-scheduler/, productization/, doc-writer/,
bioinfo-quick/, roadmap-from-zero/, FIRST-BOOT.md, GENESIS-STATE.md, plus
docs/findings and ADR directories across all eight repositories.

Specific charges:
1. GENESIS-STATE section 1 lists seven artifacts with NO producer in any
   repository. Verify that list is still accurate today; say which have since
   been written.
2. A previous agent found that the claim "information accretion has no
   dispatchable operation" is STALE because `compute_information_accretion`
   exists in the registry. Confirm, and hunt for other stale entries the same way.
3. Findings inside code repos are what a plan-store audit misses. Prioritise
   anything dated after 2026-08-27 (the registry wipe).

## Progress log
- [start] file created before investigation, per Rule Zero.

## READ THIS FIRST
The ranked answer is the **SUMMARY** section at the END of this file.
Parts: A = the seven no-producer artifacts; B = `docs/findings/` (post-wipe);
C = GENESIS-STATE section 2 re-checked item by item + the FR-1 UI gap;
D = FIRST-BOOT and the unmounted archive; E = `docs/incidents/` (post-wipe,
richest); F = my seven plan directories; G = crontab, backups, topology;
H = the record surfaces (ADR gap, Sphinx gap, where I looked).
Top three: G3 (no database backup here, none scheduled), E1 (five of 93
evaluation_result rows known-wrong and unmarkable), D1/D2 (391 GB archive
partition unmounted and not in fstab; the manuscript's only remote is on it).


---

# PART A. GENESIS-STATE section 1: the seven artifacts with "no producer"

Baseline text: `/home/xaxi/Thesis2/agent-farm/plans/GENESIS-STATE.md:31-46`,
written 2026-07-27. Audited against `/home/xaxi/Thesis2/worktrees/protea-deploy`
at `a5de702` (2026-09-01 20:19 +0000, PR #920), which is AHEAD of
`repositories/PROTEA` (`c28c4ae`, 2026-08-20). Repo heads at audit time:

    agent-farm         c76588a 2026-08-23   (repositories/ copy)
    cafaeval-protea    80d705a 2026-06-25
    PROTEA             c28c4ae 2026-08-20   (dev workspace, BEHIND deploy)
    protea-backends    47f0235 2026-07-28
    protea-contracts   bec71ff 2026-07-28
    protea-method      44ed948 2026-07-28
    protea-reranker-lab 6640393 2026-08-17
    protea-runners     f9b1e64 2026-07-28
    protea-sources     0b63719 2026-07-28

Note already worth flagging: SIX of the eight repositories have not moved since
2026-07-28. Only PROTEA, the lab and agent-farm have commits after the reinstall,
and only PROTEA has commits after the 2026-08-27 registry wipe.

## A2. `IA.tsv` has a producer, and GENESIS-STATE's claim is STALE
verdict: CONTRADICTED (the plan document is stale, not wrong-at-the-time)
first number (the claim): "The generator EXISTS (`scripts/compute_ia_for_snapshot.py`)
  but is a CLI, not a dispatchable operation" -- GENESIS-STATE.md:36. Restated as
  section 2 item 8: "IA computation as a dispatchable operation. Currently a repo
  script, so it violates the project's own rule that every operation is
  UI-actionable." -- GENESIS-STATE.md:107-108
second number (independent): `ComputeInformationAccretionOperation` is imported and
  `registry.register`ed in
  /home/xaxi/Thesis2/worktrees/protea-deploy/protea/core/operation_catalog.py:33-35,120.
  File `protea/core/operations/compute_information_accretion.py` first appears at
  commit 7448003, `git log --diff-filter=A` date 2026-08-17 13:20:39 +0000.
date of evidence: 2026-08-17 -> window: pre-wipe (but the CODE survives the wipe;
  code is not registry state, so this one is safe)
frame: n/a (capability existence, not a metric)
population: n/a
platform gap: CLOSED. The operation owns corpus, gates and artifact, writes an
  `InformationAccretionSet` row and an object-store key
  `information_accretion/{ia_set_id}/IA.tsv`.
note: the previous agent's report (rescued trail
  wf_2b4f3e5f-f3b-a979bf1ba80cd7623.md, block "GENESIS-STATE says IA has no
  dispatchable operation, yet the registry has compute_information_accretion")
  is CONFIRMED. GENESIS-STATE has not been amended in the five weeks since.
  This matters beyond bookkeeping: GENESIS-STATE section 3F says the whole
  Evaluation phase is "Blocked on the IA artifact". It is not blocked.

## A2b. A MEASURED number buried in that operation's docstring (findings-in-code)
verdict: CONFIRMED as written, FRAME-UNKNOWN as to provenance
first number: "A table computed that way over the full GOA corpus (89.8 percent
  IEA on v226) sits 8.8x further from the reference than one computed over the
  scored evidence regime, and nothing recorded which had happened."
  -- protea-deploy/protea/core/operations/compute_information_accretion.py:14-17
second number: the gate constants in the same docstring, presented as measured on
  the v226 pivot: 40214 terms, 69188 True Path Rule edges, 5907336 annotations,
  25644893 propagated pairs (lines 19-21).
date of evidence: 2026-08-17 -> window: pre-wipe
frame: ontology snapshot v226, evidence regime = "scored evidence regime" vs full
  GOA. Which of the TWO EXPERIMENTAL definitions (COLLIDING-A-NUMBER section 3:
  `evidence_codes.EXPERIMENTAL` = 13 codes vs `ia_regimes.EXPERIMENTAL_EVIDENCE`
  = 6) is in play is resolved here by module: this is `ia_regimes`, so SIX codes.
population: all GO terms in the v226 snapshot; not a protein population.
platform gap: none for the number; the receipt for "8.8x" is NOT in the repo --
  the docstring is the only place it appears. It is a claim about a measurement
  whose artifact is not committed anywhere I searched (see A2c).
note: this is exactly the class the requester asked for -- a finding written
  inside a code repo that a plan-store audit misses. It is also unverifiable
  from the repo alone.

## A1. `go_text_emb.npz` -- claim STILL ACCURATE, and now worse
verdict: CONFIRMED (the plan entry holds), with an aggravation the plan did not
  anticipate
first number (the claim): "A writer for this file exists NOWHERE. A sweep of every
  `.py` on the machine found zero. This is the only entry with no code path at
  all." -- GENESIS-STATE.md:40 (2026-07-27)
second number (independent, my own sweep, 2026-09-02):
  `grep -rl go_text_emb --include=*.py /home/xaxi/Thesis2` returns 24 files
  (6 distinct scripts x 4 checkouts: repositories/protea-reranker-lab plus
  worktrees lab-reporting / lab-gates / lab-bundle). EVERY one of the 24 is a
  READ: `np.load(... "go_text_emb.npz")` at
    repositories/protea-reranker-lab/results/sparse_classifier/build_per_cut_codes.py:86
    repositories/protea-reranker-lab/research/cooc_experiment/seq2ann_infonce/prep.py:52
    repositories/protea-reranker-lab/research/joint_model/real_diag.py:7
    repositories/protea-reranker-lab/research/joint_model/train_joint.py:36
    repositories/protea-reranker-lab/research/kwta_go_encoder/build_term_features.py:57
    repositories/protea-reranker-lab/research/cooc_experiment/seq2ann_aligner_ceiling.py:18 (a comment)
  I then checked each of those files for `np.savez`/`np.save(` and read every
  hit: all of them save DOWNSTREAM products (svd_basis.npz, vocab.npz,
  train_codes.npz, term_features.npz, cooc_graph.npz, bases.npz), never
  go_text_emb.npz. Zero writers.
  AND: `find /home/xaxi/Thesis2 -name 'go_text_emb*'` returns NOTHING. The file
  is not on the disk either.
date of evidence: 2026-09-02 -> window: post-wipe-current
frame: n/a
population: 39,906 GO terms x 768 dims per
  agent-farm/plans/bp-structural-lever/DESIGN-cross-encoder.md:36 (declared shape,
  BioBERT `name. def` mean-pool, atemporal)
platform gap: OPEN and unchanged. No operation, no script, no file.
note: where I looked (per COLLIDING-A-NUMBER rule 4): all eight repos, all
  worktrees, `storage/`, by filename and by symbol. If a writer existed it would
  be beside the readers in `protea-reranker-lab/results/sparse_classifier/` or
  `research/`, and it is not. This one entry blocks `build_go_sparse.py`, hence
  the GO tower, hence the prior-knowledge generator. The 2026-07-27 assessment
  is the only one of the seven that is exactly as bad today as it was written.

## A3. `classifier_m2_anc2vec.pt` -- claim CONFIRMED, plus a landmine the plan missed
verdict: CONFIRMED, and ESCALATED
first number (the claim): "No script in any repo saves this file. The training
  algorithm IS versioned; only the persistence step is not."
  -- GENESIS-STATE.md:42
second number (independent): grep for the symbol across repos returns exactly two
  loading sites and no `torch.save`. But the load site carries a hard defect the
  plan does not mention:
    worktrees/protea-deploy/protea/core/classifier_producer.py:74
      _DEFAULT_MODEL_PATH = "/home/frapercan/Thesis2/storage/fullgo_models/classifier_m2_anc2vec.pt"
    worktrees/protea-deploy/protea/core/classifier_producer.py:76
      "/home/frapercan/Thesis2/worktrees/protea-deploy/artifacts/anc2vec/anc2vec_2020-10.npz"
  `ls /home/` on this machine returns ONE entry: `xaxi`. There is no
  `/home/frapercan`. The default path cannot resolve on the compute node, and it
  is present at the deploy head a5de702 dated 2026-09-01, i.e. TODAY-minus-one.
  Neither file exists anywhere under Thesis2 (`find` by name returns nothing).
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: OPEN. Two gaps, not one: (i) no checkpoint-saving path, (ii) the
  consumer is pinned to a pre-reinstall absolute path under a username that no
  longer exists.
note: the same class as `band_registry.py` pinning a host path, which
  GENESIS-STATE DID flag for IA.tsv. It did not flag the identical defect one row
  below. Full sweep of `/home/frapercan` in the deploy tree gives SEVEN sites:
    scripts/hpo_champion_score.py:61
    tests/test_lafa_frame_parity.py:278 (_THESIS_ROOT)
    protea/api/routers/datasets.py:351,356,361 (three `file://` URLs)
    protea/core/classifier_producer.py:74,76
  The three `file://` URLs in the datasets router are the object-store-URL
  variant of the same problem and sit on a live API surface.

## A4. `anc2vec_2020-10.npz` -- claim CONFIRMED (no fetch step)
verdict: CONFIRMED
first number: "A third-party pretrained artifact ... The download step appears in
  no runbook. | Add a fetch step with a checksum" -- GENESIS-STATE.md:43
second number: the symbol appears in repositories/PROTEA at README.md,
  scripts/export_lafa_bundle.py, tests/test_anc2vec_path.py,
  protea/core/classifier_producer.py, protea/core/anc2vec_embeddings.py,
  docs/source/complexity/anc2vec.rst, and three runbooks
  (secrets-management.rst, deployment.rst, deployment-process-stack.rst).
  All consumers/references; `find` for the file returns nothing on disk.
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: OPEN, and now compounded by A3's dead absolute path.
note: it IS mentioned in three runbooks, which is more coverage than the plan
  credits; worth re-reading those three before writing a fetcher (see Part C).

## A5. InterProScan installer -- claim CONFIRMED
verdict: CONFIRMED
first number: "Re-downloadable from EBI. No installer script anywhere; 50 GB
  acquired by hand." -- GENESIS-STATE.md:44
second number: `grep -rlin interproscan` over the whole deploy tree returns 24
  files. Where I looked and what is there: one operation
  (`protea/core/operations/run_interproscan_batch.py`), one ORM model, one
  migration (`7b023568309d_ip2_interpro_annotation.py`), six tests, one script
  (`scripts/evaluate_external_tool.py`), poetry.lock, CLAUDE.md, and eight docs
  pages. ZERO shell scripts, zero Makefile targets, zero docker/compose service,
  zero ansible. The version string "5.77-108.0" appears in the whole tree only in
  `repositories/agent-farm/plans/GENESIS-STATE.md` and
  `repositories/agent-farm/plans/farm-platform/PLAN.md` -- i.e. only in the plan
  store, never in an installer, a lockfile or a runbook.
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: OPEN. Not even a pinned version outside the plan store.
note: a negative check with its reach stated: an installer would be a `.sh` under
  `scripts/`, a compose service, or a step in
  `agent-farm/scripts/bootstrap-fresh-machine.sh`. I grepped all three.

## A7. The 8 canonical `EmbeddingConfig` UUIDs -- claim now CLOSED (STALE entry)
verdict: CONTRADICTED (plan is stale)
first number (the claim): "They remain unversioned as a seed migration, which is a
  robustness gap rather than a break. | Add a seed migration so the identifiers
  are declared in code, not only in a dump" -- GENESIS-STATE.md:46
second number: three seed migrations now exist in
  worktrees/protea-deploy/alembic/versions/ (79 migrations total):
    e7a1c4f9b2d6_seed_rung1_matched_parameter_grid.py
    a1c9e4b7d2f8_seed_esm2_8m_pipeline_cell.py
    f2b8d1c6a94e_seed_t5_and_protst_cells.py
  All three first appear at commit 7448003, 2026-08-17 13:20:39 +0000 (the same
  commit that added compute_information_accretion -- one large merge).
date of evidence: 2026-08-17 landing, verified 2026-09-02 -> window: code
  survives the wipe; the DB ROWS the migrations create do not, but a migration
  re-creates them, which is the whole point.
platform gap: CLOSED.
note: the roster changed under the entry. GENESIS-STATE says "the 8 canonical
  EmbeddingConfig UUIDs"; the migrations seed a rung-1 grid of FOUR
  (ankh_base, esm2_650m, esmc_600m, ankh_large) plus one mechanism cell
  (esm2_8m) plus three T5/ProtST cells. "The canonical 8" of 2026-07-27 is not
  the seeded set of 2026-08-17. Anyone citing D35-canonical-8plm-embedding-configs
  is citing a superseded roster.

## A7b. AN EXCLUSION IN THE CANONICAL GRID RESTS ON A MEASUREMENT NOBODY CAN FIND
verdict: DEDUCED-NOT-MEASURED (and the code says so itself, which is to its credit)
first number: "ESM-2 150M -- excluded by CAMPAIGN §5 as written. The supporting
  measurement could not be located; the researcher chose to respect the document
  rather than re-derive it. Do not mint it here."
  -- worktrees/protea-deploy/alembic/versions/e7a1c4f9b2d6_seed_rung1_matched_parameter_grid.py,
     docstring, roster section
second number: none exists. That is the point. The neighbouring exclusions in the
  same docstring ARE measured and quantified:
    "ProtT5 and ProstT5 -- OOM at batch_size 4 and only 81% headroom at
     batch_size 2 on the 8188 MiB RTX 4060."
    "ESM-2 3B -- non-loadable on this card, confirmed three independent ways."
    "ankh_large is dispatched at batch_size 2 (5008 MiB; batch_size 4 leaves
     only 577 MiB)."
  So three of four exclusions carry a number and one carries a citation to a
  document that carries no number.
date of evidence: researcher decision 2026-07-29, migration Create Date
  2026-07-31, landed 2026-08-17 -> window: pre-wipe
frame: RTX 4060, 8188 MiB, batch-size fit. NOTE this is the LAPTOP-class card
  figure; CLAUDE.md says this machine's constraint is 12 GB. The 8188 MiB in
  the docstring does not match the 12 GB in the root CLAUDE.md -- one of the two
  is describing a different card, and the migration is the one that is
  load-bearing for the grid.
population: n/a (a model roster, not proteins)
platform gap: MURO for the ESM-2 150M exclusion -- there is nothing to re-run
  because nobody knows what was run. The honest fix is to re-measure it, which
  is a `count_backend_parameters` + a fit probe, both of which now exist as
  operations.
note: this is the single cleanest instance in my slice of the pattern the
  requester asked for. A roster decision that gates an entire rung is carried by
  prose in CAMPAIGN.md §5, and the person who implemented it looked for the
  receipt, failed to find it, wrote that down, and complied anyway. The
  compliance is defensible; the citation of §5 as if it were measured is not.

---

# PART B. `docs/findings/` -- the post-wipe findings that a plan-store audit misses

`worktrees/protea-deploy/docs/findings/` exists ONLY in the deploy checkout. It
is absent from `repositories/PROTEA` (which is at c28c4ae, 2026-08-20, before
the directory was created). Three files, ALL dated after the 2026-08-27 wipe:

    2026-08-30-what-a-curated-not-was-telling-us.md            5d3050b 2026-08-30 17:28 (#913)
    2026-08-30-what-the-direct-method-has-to-get-right.md      a2881d9 2026-08-30 18:04 (#914)
    2026-09-01-generation-lands-an-order-of-magnitude-below-retrieval.md  a5de702 2026-09-01 20:19 (#920)

These are post-wipe-current evidence and the ONLY narrative research record in a
code repository. Anyone auditing `agent-farm/plans/` alone will never see them.

## B1. THE NOT-PROPAGATION FIGURE IN THE REPO IS THE ONE THE PROJECT ALREADY RETRACTED
verdict: CONTRADICTED (repo doc carries a defect the plan store records as fixed)
first number: "So the visible violation, 478, is under half of the real one."
  -- worktrees/protea-deploy/docs/findings/2026-08-30-what-a-curated-not-was-telling-us.md,
     section "A denial is bigger than the term it names".
  The table it rests on: direct denials 943; denied (protein, term) pairs after
  descent 39,105 (41.5x expansion); "of those, predicted by the run 1,190".
  1,190 / 478 = 2.49, i.e. the "2.5x understatement".
second number (INDEPENDENT, from the project's own later correction):
  "I reported NOT propagation as a '2.5x understatement'. The 2.5 came from
   comparing denials against pairs, which are different objects. The real figure
   is 465 to 527 denials, plus 13 per cent. Caught by the other machine, from
   the breakdown, within the hour."
  -- agent-farm/plans/COLLIDING-A-NUMBER.md:55-58
  So the true effect is +13.3% (465 -> 527), not +149% (478 -> 1,190). An order
  of magnitude off in the size of the correction.
date of evidence: finding doc 2026-08-30 17:28; correction 2026-09-01 22:42
  (agent-farm d06f75d, PR #269) -> window: BOTH post-wipe-current
frame: prediction set `9995651a` at depth 30, bank `cbb35a32`, corpus as of t0.
  Propagation under `is_a` and `part_of` only. t0 has 5,603 NOT annotations,
  t1 has 5,397; the check reads only t0. 956 NOT annotations concern a query
  protein; 943 of those have a term in the run's own ontology.
population: query set of prediction set 9995651a. Per-aspect denial counts
  MFO 291 / CCO 213 / BPO 452, violated 167 / 145 / 166, i.e. 57.4% / 68.1% /
  36.7%, all 50.0%. NOT stratified by NK/LK/PK anywhere -- and a NOT annotation
  is by construction a curated experimental record, so this population is
  heavily prior-knowledge, not the served NK cell.
platform gap: the counts came from an ad-hoc analysis; the FIX
  (`protea/core/operations/predict_go_terms/_denials.py`, PR #912) is in the
  platform, the MEASUREMENT is not. There is no `audit_denial_violations`
  operation. To reborn this writing to the database you would need one, keyed on
  (prediction_set_id, annotation_set_id, propagation policy).
note: THE CORRECTION WAS NEVER BACK-PROPAGATED INTO THE REPO DOCUMENT. The
  repo file is unchanged since 5d3050b. A reader of the code repository -- which
  is the surface an examiner reaches -- gets the retracted number, and the
  retraction lives in a file (COLLIDING-A-NUMBER.md) that does not name the
  document it corrects. This is the highest-value single finding in my slice.
  Also: the doc's own closing caveat is correct and should be preserved -- "1,190
  pairs out of 2,441,584 will not move a headline metric". Both the 1,190 and the
  478 are diagnostic, not metric-moving; only the SIZE OF THE CORRECTION is wrong.

## B2. A single-run negative result, correctly self-labelled
verdict: CONFIRMED (as a measurement, with the author's own caveat intact)
first number: generation vs retrieval, `f_micro_w`:
  entail_kwta 0.011 vs anchor 0.144; sparse containment 0.016 vs deployed 0.196
  -- docs/findings/2026-09-01-generation-lands-an-order-of-magnitude-below-retrieval.md
second number: the arm-by-arm tables in the same file are the breakdown
  (COLLIDING-A-NUMBER rule 2 satisfied). Descent generator CCO: 0.0987 vs
  frequency-prior-top-1 0.1640; P 0.0636 vs 0.1301; R 0.2202 vs 0.2219;
  emitted 9,734 vs 10,836. Sparse containment: 0.0160 / 0.0082 / 0.0004 against
  frequency-prior-top-50 0.0852 and deployed 0.1955-0.2085.
date of evidence: 2026-08-30 to 2026-09-01 -> window: post-wipe-current
frame: test 227 to 230. Descent arm: 903 proteins, 3,736 true additions, run 2,
  60,000 training proteins, prior tuned on validation. Sparse arm: 1,023
  proteins, 10,905 additions, corpus 1,889,171 pairs / 40,214 terms / 40,000
  proteins. Metric is `f_micro_w` (POOLED and IA-weighted -- one of the four
  things called F; see COLLIDING-A-NUMBER section 3).
population: curated ADDITIONS between releases. NOT stratified by NK/LK/PK, so
  by the project's own norm these are aggregates, hence ~95% prior knowledge.
  The author says so obliquely ("Nothing here was cross-fitted or bootstrapped")
  but never says the word "stratified".
platform gap: the three arms ran on an abandoned branch
  `feat/subsumption-is-containment-in-a-sparse-code` tip `222b4a3`, deliberately
  not deleted. Only two files were salvaged to develop (PROTEA#919:
  `protea/core/ontology/sparse_containment.py`,
  `tests/test_subsumption_is_containment.py`). 23 files of the branch are
  reachable only through that ref. MURO if the ref is ever GC'd.
note: this document does the thing the requester is hunting for, correctly:
  "these are single measurements against a prior, taken to decide whether to
  continue, and they are not the kind of number that belongs in a results table."
  Anyone quoting 0.016 or 0.0987 as a result is quoting against the author's
  explicit instruction. Also carries a number worth chasing elsewhere: "The
  reranker sits at AUC 0.491 in PK-BPO against 0.6263 for a clean entailment
  signal" -- 0.491 is chance, and it is asserted here with NO receipt in the
  document.
note2: the four-defect list in it is a registry of the SAME defect class the
  project keeps hitting. Its own count: "This is the fourth time in this project
  that a parameter has been accepted, recorded where a reader would trust it, and
  not governed the computation" (`own_k`). That matches
  COLLIDING-A-NUMBER section 4's `own_k` entry exactly -- an ECHO, same author,
  same day, not independent corroboration.

## B3. THE STORE INVENTORY OF 2026-08-30 IS ARITHMETICALLY INCONSISTENT WITH ITSELF
verdict: CONTRADICTED (internal collision, found by arithmetic on the page)
first number: "sequence embeddings | 6,867,762 across 12 spaces, every space
  covering all 528,294" and "sequences | 528,294"
  -- worktrees/protea-deploy/docs/findings/2026-08-30-what-the-direct-method-has-to-get-right.md,
     section "What we have", explicitly headed "Measured on 2026-08-30, not assumed."
second number (INDEPENDENT, my arithmetic):
    12 x 528,294 = 6,339,528   -> 528,234 rows unaccounted for
    13 x 528,294 = 6,867,822   -> 60 rows SHORT of the stated total
  So the true shape is THIRTEEN spaces of which one is 60 sequences short, OR
  twelve spaces one of which massively over-covers. Either way the sentence
  "12 spaces, every space covering all 528,294" cannot be true as written.
date of evidence: 2026-08-30 -> window: post-wipe-current (this is the ONLY
  full store inventory in the current window that I found in any repository)
frame: n/a, these are row counts
population: the whole corpus
platform gap: no operation emits this inventory. It was produced by hand
  (presumably SQL) and typed into markdown. A `report_store_inventory` operation
  is what would let this be reborn writing to the database, and it does not exist.
note: 60 missing embeddings is exactly the shape of a partially-completed
  embedding run, which is a fact about the campaign's state, not a typo. This
  matters because the same document uses "every space covering all 528,294" to
  argue the representation axis is complete. It is 60 short in one space and one
  space is unnamed. Also note 12 or 13 spaces against GENESIS-STATE's "8 canonical
  EmbeddingConfig UUIDs" -- the roster has grown 50-60% and no document tracks it.

## B4. A 762x FACTOR THAT ITS OWN TABLE MAKES 379x
verdict: CONTRADICTED (factor of 2, from dividing by the vocabulary instead of by
  its own stated chance baseline)
first number: "The geometry carries a protein: a held-out true term costs 762
  times less than a random one, and the join places it at rank 53 of 40,214."
  -- same file, section "What the probe says about the target space"
  Its own table on the line above:
      join of the protein's other terms  median rank 53      h@10 37.6%  h@100 58.5%
      term frequency                     median rank 106     h@10 27.2%  h@100 49.4%
      chance                             median rank 20,107  h@10 0.02%  h@100 0.2%
second number (INDEPENDENT, arithmetic on that table):
      20,107 / 53 = 379.4     <- the factor against the document's own chance row
      40,214 / 53 = 758.8
      40,214 / 762 = 52.77    <- so 762 was obtained as vocabulary_size / rank
  The prose divided by the SIZE OF THE VOCABULARY (40,214) rather than by the
  MEDIAN RANK OF A RANDOM TERM (20,107), which its own table supplies two lines
  earlier. The correct statement is "379 times", and 20,107 is itself the right
  chance median (40,214/2 = 20,107, exact).
date of evidence: 2026-08-30 -> window: post-wipe-current
frame: hold-one-out over the FULL ontology of 40,214 terms; the same file warns
  that "against 500 sampled candidates the same measurement reads rank 2, which
  is ... not what the method is worth", so the author was alert to denominators
  in the very next sentence and still got this one wrong.
population: 795 query proteins with at least eight known terms. NOT the served
  population: the file states plainly "For the 2,413 NK proteins there are no
  known terms, so this prior is absent exactly where the method has the least to
  work with." So this measurement is 795 PK/LK proteins and is structurally
  inapplicable to the NK cell that is ~5% of a window and is what PROTEA serves.
platform gap: no operation. Hold-one-out over the ontology against a frequency
  and a chance baseline is exactly the "control family as reusable machinery"
  that GENESIS-STATE section 2 item 3 says was never versioned. Still true.
note: the document is otherwise the most careful in the repository -- it ranks
  its risks by "how likely each one is to produce a number that looks good and
  means nothing" -- and it is the one that contains a 2x arithmetic slip and a
  row-count that does not add up. Consistent with COLLIDING-A-NUMBER's thesis:
  care is not what catches these.

## B5. Load-bearing facts from that inventory worth carrying forward
verdict: CONFIRMED (as of 2026-08-30)
- `information accretion sets | 1`. This is the empirical proof that
  `compute_information_accretion` did not merely land, it RAN. GENESIS-STATE's
  "Blocked on the IA artifact" (section 3F) is doubly dead.
- **`interpro_go_mapping` is EMPTY.** "The feature code in
  `protea/core/_interpro_features.py` exists and has nothing to read. Domain
  architecture is not currently available." Two registered operations
  (`load_interpro_go_mapping`, `predict_go_terms_from_interpro`) plus a third
  (`run_interproscan_batch`) sit on an empty table. Combined with A5 (no
  installer, 50 GB by hand, version pinned only in the plan store), the entire
  InterPro arm is DEAD in the current window: no data, no installer, and the
  operations that consume it are green because they have nothing to fail on.
  This is a live instance of COLLIDING-A-NUMBER rule 4.
- All 575,503 UniProt metadata rows were loaded 2026-07-30, while "the bank is
  dated 2024-04-10 and the truth 2025-09-03". So EVERY metadata column is
  post-cutoff. 280,036 proteins carry an EC number, which is "a molecular
  function statement ... curated together, from the same evidence, by the same
  people" as the MFO annotation. This is a LEAK THAT HAS NOT HAPPENED YET, and
  it is correctly flagged as factor 1 before any model was trained on it.
- "Evaluation reproduces exactly, 117 of 117 metrics. Retrieval does not."
  A reproducibility floor statement, no receipt in the repo.
- "The corrected ceiling measurement says the union of twelve reaches 77.9 per
  cent of new pairs while one arm recovers 0.22 to 0.61 at its operating point."
  Note "the CORRECTED ceiling measurement" -- an earlier ceiling number was
  wrong and this file does not say what it was.
- "The window adds 56,816 new (protein, term) pairs read exactly and 179,135
  read with propagation" (3.18x). Cross-check against the memory index entry
  "the ontology SHRANK, but growth is what bites": different objects, no conflict.
- 616,846 proteins vs 528,294 sequences: 88,552 proteins (14.4%) share a
  sequence with another, consistent with ADR 006 (md5 dedup).

---

# PART C. GENESIS-STATE section 2 -- the ten capabilities, re-checked one by one

Method: for each item, find where the capability would live in
`worktrees/protea-deploy` if it existed, grep for it, and date the file with
`git log --diff-filter=A`. Stated so the negative checks have a reach
(COLLIDING-A-NUMBER rule 4).

FIRST, the structural fact that governs all ten: `plans/GENESIS-STATE.md` has had
exactly TWO commits, the last `8668180` at 2026-07-28 10:54:57 +0200. It has not
been touched in the FIVE WEEKS since, during which ten operations landed. Every
staleness below follows from that one fact.

| # | capability | 2026-07-27 verdict | 2026-09-02 verdict | evidence |
|---|---|---|---|---|
| 1 | Stratification (length x category x neighbour) | "no implementation anywhere in versioned code" | **CLOSED** | `protea/core/strata.py` (510 lines) added 2026-07-28 03:54:50 UTC `91d35e6`; operation `stratify_evaluation` added 2026-08-19 `38a53cd` |
| 2 | A window registry | "declared in prose only" | **CLOSED** | `protea/core/split_registry.py` (423 lines) added 2026-07-28 03:50:01 UTC `57cecdc` |
| 3 | The control family as reusable machinery | never versioned | **STILL OPEN** | grep for `shuffle_features`/`shuffled_feature`/`random_order`/`matched_volume`/`CONTROL_FAMILY`/`control_arm` over `protea/`, `scripts/`, `tests/`: ZERO hits |
| 4 | The cross-fit gate (9 folds, blind 10th) | not built | **PARTIAL / NOT A GATE** | `cross_fit`/`n_folds`/`fold_spread` hit only 3 files: `protea/core/operations/batch_rescore_evaluation.py`, `scripts/hpo_champion_score.py`, `tests/test_batch_rescore_evaluation.py`. No nine-fold sweep-then-blind-tenth gate anywhere |
| 5 | Paired bootstrap CIs in the board frame | "two implementations, both bootstrap Fmax not the headline, neither in the board frame" | **CLOSED, and properly** | `protea/core/operations/_paired_panels_bootstrap.py`: `paired_bootstrap` is protein-level and "re-selecting the operating point each time" (line 179), with an explicit MDE read "off the bootstrap distribution, not off a normal approximation" (line 362) and a `DEGENERATE` interval type. Operation `compare_paired_panels` added 2026-08-28 `08a2c2a` |
| 6 | A row-alignment assertion | "a lesson in memory, not a lint" | **CLOSED** | `protea/core/row_alignment.py` (122 lines) added 2026-07-28 03:49:05 UTC `4e79d8c`, plus `scripts/check_row_alignment.py` and `tests/test_row_alignment.py` |
| 7 | The board recipe as a versioned fixture | "prose in a runbook. No YAML, no fixture, no pinned payload" | **STILL OPEN** | `protea/config/runs/` holds exactly TWO run YAMLs: `insert_proteins.run.yaml`, `uniprot_metadata.run.yaml`. Neither is the board recipe. No `run_cafa_evaluation.run.yaml` |
| 8 | IA as a dispatchable operation | "currently a repo script" | **CLOSED, and it RAN** | see A2; and the store inventory of 2026-08-30 reads `information accretion sets: 1` |
| 9 | End-to-end orchestration (one dispatch for the chain) | "exists only in the operator's head" | **STILL OPEN** | no operation whose payload chains stages; `export_coordinator` chains only the three export minijobs |
| 10 | The registry-to-UI coverage test | "the literal acceptance criterion of FR-1 and it does not exist" | **STILL OPEN, AND MEASURABLY WORSE** | see C10 below |

So: FOUR of ten closed (1, 2, 5, 6, 8 -- five if you count 8 separately from the
section-1 row), FOUR still open (3, 7, 9, 10), one partial (4). **And items 1, 2
and 6 were closed by code committed 2026-07-28 between 03:49 and 03:59 UTC,
which is BEFORE GENESIS-STATE's own final commit at 08:54:57 UTC that same day.**
The document's section 6 describes exactly those three closures ("The temporal
splits refuse to guess", "The four axes refuse to pool", "A join cannot lose rows
silently") while section 2 above it still lists them as missing. GENESIS-STATE
contradicts itself internally, and has done since the day it was last saved.

## C10. FR-1 IS UNMET BY A FACTOR OF FOUR, AND THE UI ITSELF ADMITS IT
verdict: CONFIRMED and QUANTIFIED (the plan said "six drifted out"; it is now
  thirty)
first number: "The registry-to-UI coverage test. This is the literal acceptance
  criterion of FR-1 and it does not exist, which is why six user-facing
  operations drifted out of the interface." -- GENESIS-STATE.md:114-116
second number (INDEPENDENT, my own count, 2026-09-02):
  - The registry declares **39** operation names
    (`grep -rho '^\s*name = "..."' protea/core/operations/ | sort -u`, and
    `build_operation_registry()` registers 39 instances).
  - The web app dispatches by HARDCODED STRING LITERAL. I verified there is no
    dynamic path: there is no `GET /operations` endpoint in
    `protea/api/routers/`, and `createJob` in `apps/web/lib/api.ts:213` takes
    `operation: string` from its caller. So a literal grep IS the right check.
  - `grep -rhno 'operation: *"..."' apps/web/app apps/web/lib apps/web/components`
    returns exactly **NINE** distinct operations:
      run_cafa_evaluation (3 sites), ping (2), compute_embeddings (2),
      refresh_goa_release_dates, load_quickgo_annotations, load_ontology_snapshot,
      load_goa_annotations, insert_proteins, fetch_uniprot_metadata
    A tenth, `predict_go_terms`, appears ONLY in `apps/web/e2e/` mocks.
  - **9 of 39 = 23% coverage. 30 operations are dispatchable but not
    UI-actionable.** Removing the 8 that are plausibly internal-by-design
    (`*_batch` variants, `export_coordinator`, `export_knn_batch`,
    `export_features_batch`, `export_write`, `store_predictions`) still leaves
    **22** user-facing operations outside the interface, against the plan's "six".
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: the test itself. It is three lines: import
  `build_operation_registry`, scan `apps/web` for each name, assert. Nothing
  stops it being written today.
note: THE INTERFACE DOCUMENTS ITS OWN GAP IN PROSE.
  `apps/web/components/StrataPanel.tsx:254` renders "Not stratified yet. Run the
  `stratify_evaluation` operation" -- an instruction to run an operation the
  interface cannot run. `apps/web/lib/book.ts:356` says of the board number "The
  board number is regenerated by exporting the dataset
  (`export_research_dataset`) and scoring it (`run_cafa_evaluation`). Dispatch
  both from the instrument." Only ONE of those two has a dispatch site. The
  other six mentions of `export_research_dataset` in `apps/web` are all prose or
  type comments. So the six operations GENESIS-STATE said "drifted out" did not
  drift silently; the UI names them and tells the operator to run them elsewhere.
  Every one of the ten operations that landed post-reinstall
  (compute_information_accretion, archive_ontology_snapshot, export_gate_bundle,
  audit_evaluation_frames, count_backend_parameters, export_evaluation_targets,
  encode_residue_sparse, stratify_evaluation, seal_evaluation_frames,
  compare_paired_panels, audit_per_protein_artifacts) is in the zero column.

---

# PART D. FIRST-BOOT.md: the recovery surface is UNREACHABLE, and has been for 35 days

## D1. THE ARCHIVE PARTITION IS NOT MOUNTED AND IS NOT IN fstab
verdict: CONFIRMED (hard, from block devices)
first number (the claim): "The archive partition is a separate disk and survives
  the reinstall. Everything below lives under `/mnt/protea-archive/archive/`."
  -- agent-farm/plans/FIRST-BOOT.md, section 0
second number (INDEPENDENT, from the kernel):
    lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT   ->   nvme1n1p5   391G   ext4   (NO MOUNTPOINT)
    df                                     ->   only /dev/nvme0n1p2 (915G) at / and /boot/efi
    ls -la /mnt/protea-archive/            ->   EMPTY, `total 8`, root:root, mtime Jul 28 17:09
    grep -v '^#' /etc/fstab                ->   THREE lines: /, /boot/efi, /swap.img.
                                                NO entry for nvme1n1p5, none by UUID, none by label.
  The 391 GB matches the memory index's own note that "391 GB sit unmounted"
  (project_learned_encoder_published_and_order_proven_2026_08_23.md).
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: MURO for the moment -- nothing in any repository mounts it, and
  adding an fstab line is a root action outside this audit's write scope.
note: `/mnt/protea-archive` was created 2026-07-28 17:09 and the disk was
  mounted there at least once that day (the recovered clones prove it, below).
  It has been unmounted ever since, and because fstab has no entry, a reboot --
  which CLAUDE.md says happens "without warning" -- will never bring it back.
  The mount is a step that exists only in an operator's memory of one afternoon.

## D2. THE ONE-COPY-IN-THE-WORLD PAPER STILL HAS ONLY THE UNREACHABLE REMOTE
verdict: CONTRADICTED (root CLAUDE.md says the remote was created; it was not)
first number: root `/home/xaxi/Thesis2/CLAUDE.md`, Layout section:
  "complexity-paper/         # recovered 2026-07-28; remote created the same day"
  and FIRST-BOOT.md section 0: "It is the one thing that exists nowhere else:
  the repository has no remote, so the mirror is the only copy in the world. ...
  Then give the paper a real remote. Until it has one, every new commit sits
  exactly where the first thirteen sat."
second number (INDEPENDENT, `git remote -v` in the clone):
    complexity-paper:  mirror  /mnt/protea-archive/archive/preformat-preserve-2026-07-28-local-only-repos/complexity-paper.git  (fetch AND push)
    CAFA_forever:      origin  /mnt/protea-archive/archive/preformat-preserve-2026-07-28-local-only-repos/CAFA_forever.git
  ONE remote each, both pointing into the unmounted partition. No GitHub remote,
  no second remote of any kind. Head of complexity-paper is
  `6e23afc 2026-07-28 12:42:13 +0200 "style: replace the em-dashes ..."`, i.e.
  untouched since the reinstall day.
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: n/a, this is a `git remote add` plus a push.
note: this is the project's own "verify then act, never narrate a check you
  ignore" rule failing in the root CLAUDE.md itself. "remote created the same
  day" is true only if a bare mirror on an unmounted local partition counts as a
  remote, and FIRST-BOOT explicitly says it does not ("give the paper a REAL
  remote"). Right now `git push mirror` fails: the path does not exist.
  Severity: complexity-paper is a manuscript that exists in exactly two places on
  one machine, one of which is not currently addressable.

## D3. The seven no-producer artifacts ARE preserved -- on the unmounted disk
verdict: CONFIRMED, and it REFRAMES Part A
first number: FIRST-BOOT.md section 0 recovery table:
  | artefacts whose producer was never found | `preformat-preserve-2026-07-27_preformat/no-producer-artifacts/` |
  | the secret surface, no template exists in any repository | `.../secrets/protea.env` |
  | database dumps, newest first | `protea-dumps/` |
  | the object store snapshot | `.../minio/` |
  | assistant memory for this project | `.../claude-memory.tar.gz` |
second number: all five paths are under `/mnt/protea-archive/archive/`, which D1
  proves is not mounted. I could not read any of them.
date of evidence: 2026-09-02 -> window: post-wipe-current
note: so `go_text_emb.npz` (A1) and `classifier_m2_anc2vec.pt` (A3) are probably
  NOT destroyed -- they are in `no-producer-artifacts/`, one `mount` away. This
  does not weaken A1 and A3: GENESIS-STATE's own governing rule is that "a
  procedure that lives only as a script under storage/ is a capability that dies
  with the format even if its output was archived", and CAMPAIGN.md section 0bis
  forbids importing an artifact without a registered producer. The artifacts
  being recoverable is precisely the temptation the invariant exists to refuse.
  What IS newly established is the count of what an unmount currently costs:
  the paper's only remote, the 28-variable secret surface that has no template in
  any repository, every database dump, the object store, and the seven artifacts.

## D4. The deploy-slot script count: 7 vs 13 vs my 14
verdict: CONFIRMED that the plan store already caught its own error; my count
  differs again
first number: GENESIS-STATE.md section 3A: "creation of the
  `worktrees/protea-deploy` runtime slot, which is **hardcoded in seven
  scripts** and created by nothing". Root CLAUDE.md: "Thirteen scripts hardcode
  that path and nothing creates it".
  FIRST-BOOT.md already reconciles them: "Thirteen scripts hardcode that path and
  **nothing creates it**. The count is from a sweep of both script directories,
  not from an earlier document that said seven."
second number (INDEPENDENT, my sweep of the same two script directories):
  `grep -rl "worktrees/protea-deploy" agent-farm/scripts repositories/PROTEA/scripts`
  returns FOURTEEN distinct scripts: twelve under `agent-farm/scripts` (of which
  TWO are under `agent-farm/scripts/archive/`, i.e. retired) and two under
  `repositories/PROTEA/scripts` (`cold-boot.sh`, `deploy.sh`).
  Excluding the two archived: TWELVE live scripts. Including them: fourteen.
  Neither is thirteen.
date of evidence: 2026-09-02 -> window: post-wipe-current
note: the disagreement is small and harmless, but it is the same shape as
  every other defect here -- a count published without its denominator, so the
  next reader cannot tell whether "thirteen" counted the archive directory. The
  slot DOES exist on this machine today (it is what I audited against), so the
  operational risk is discharged; only the number is unreliable.

---

# PART E. `docs/incidents/` -- a directory NOT in my brief, and the richest thing in it

`worktrees/protea-deploy/docs/incidents/` holds SIX files. Three predate the
reinstall (2026-05-26 x2, 2026-05-29). THREE are post-wipe and none of them is
in the plan store:

    2026-08-29-prediction-set-a789582e.md          d65daba 2026-08-29 18:59 (#894)
    2026-08-30-depth-series.md                     4ef40e2 2026-08-30 04:30 (#906)
    2026-08-30-where-the-ceiling-comes-from.md     cb279f8 2026-09-01 10:54 (#911)

Note the third was committed under a `docs(findings):` subject but written into
`docs/incidents/`, so a search of either directory alone misses it.

## E1. FIVE OF THE 93 LIVE `evaluation_result` ROWS ARE KNOWN-BAD, KEPT ON PURPOSE, AND UNMARKABLE
verdict: CONFIRMED (this is the single most important operational fact in my slice)
first number: "Two series of five evaluations were run on prediction set
  `9995651a` on 2026-08-30, at sequence depths 30, 20, 10, 5 and 2. The first is
  not a series. **Both are sealed under the same frame digest
  `f-1c245d41f26ff70c3b0a9247`, and nothing in the record distinguishes them.**"
  -- docs/incidents/2026-08-30-depth-series.md
  The bad five: `67fe2fa0`, `28621824`, `9de60449`, `53d68960`, `d0705d22`
  (run 02:44-02:46). The good five: `095b81eb`, `437b08a8`, `9f508370`,
  `3e1a47d8`, `aab5bfc6` (run 04:06-04:08 on `73acf81`).
  "**Four of the five carry a depth label they did not score.** They cannot be
  told apart from the corrected series by the seal, they carry
  `leakage_role='select'`, and **there is no supported way to mark them.**"
  And from PR #904's message: "The five results are kept. They are a measurement
  of this defect and the only one. Deleting them would remove the evidence along
  with the mistake, which is the same reason `a789582e` was kept."
second number (INDEPENDENT, from the brief): the live database holds 93
  `evaluation_result` rows, all 2026-08-27 to 2026-08-30. Five of 93 = 5.4% are
  known-wrong. Any query selecting on frame digest `f-1c245d41f26ff70c3b0a9247`
  returns TEN rows of which FIVE are poisoned, and no column separates them.
  The only discriminator is the created_at minute (02:44-02:46 vs 04:06-04:08)
  and the five result ids listed above.
date of evidence: 2026-08-30, doc 2026-08-30 04:30 -> window: post-wipe-current
frame: prediction set `9995651a`, frame digest `f-1c245d41f26ff70c3b0a9247`,
  `leakage_role='select'`, depth counted in SEQUENCES not proteins.
population: NK 3,754 per-protein rows, LK 2,978, PK 12,303 -- identical at every
  depth, so the cohort is fixed and only candidate depth moves.
platform gap: a way to retract or supersede a sealed evaluation_result. The
  document says outright there is none. `seal_evaluation_frames` (2026-08-28)
  seals; nothing un-seals or annotates. **This is the platform gap I would rank
  first**: the project's own norm is that a defect becomes a guard, and here the
  guard exists (#904) while the five contaminated rows stay indistinguishable in
  the only database the campaign has.
note: ANY downstream census that reads evaluation_result and groups by frame
  digest is currently wrong by construction. Carry the five ids forward.

## E2. THE DEPTH LAW IS ESTABLISHED ON FIVE OF NINE CELLS, AND THE COMMIT SAYS NINE
verdict: DEDUCED-NOT-MEASURED for four of the nine populations
first number: PR #904's message: "Identical to four decimals in all **nine
  panels**, across an order of magnitude of input" -- but its table has FOUR
  columns: NK.BPO, NK.MFO, NK.CCO, PK.BPO (plus rows-in-frame).
  The incident doc's corrected table has FIVE: it adds LK.BPO, and concludes
  "Monotone in all **five cells** with no exception".
second number (INDEPENDENT, by counting): the project's own norm is that
  category x aspect is NINE populations. Reported: NK.BPO, NK.MFO, NK.CCO,
  LK.BPO, PK.BPO = five. NEVER reported in either document: LK.MFO, LK.CCO,
  PK.MFO, PK.CCO = four. The commit claims nine panels were identical; the
  incident claims five cells are monotone. Both describe the same two runs and
  neither publishes the four missing cells.
date of evidence: 2026-08-30 -> window: post-wipe-current
population: the four unreported cells are exactly the LK and PK non-BPO cells,
  which per the memory index carry ~95% of the aggregate mass.
platform gap: `stratify_evaluation` exists and produces the nine cells; the
  publication step selects five. A `report_nine_cells` fixture would close it.
note: the corrected table itself:
  | depth | NK.BPO | NK.MFO | NK.CCO | LK.BPO | PK.BPO |
  | 30 | 0.1462 | 0.2870 | 0.2721 | 0.1725 | 0.0579 |
  | 20 | 0.1546 | 0.3126 | 0.2815 | 0.1825 | 0.0599 |
  | 10 | 0.1731 | 0.3310 | 0.3065 | 0.2043 | 0.0640 |
  |  5 | 0.1848 | 0.3652 | 0.3268 | 0.2287 | 0.0706 |
  |  2 | 0.2154 | 0.4104 | 0.3488 | 0.2437 | 0.0789 |
  It is NOT a precision-for-recall trade and the doc proves it rather than
  asserting it: coverage 1.000/1.000/1.000/0.9987/0.996, and at NK.BPO depth 2
  beats depth 30 on precision (0.2602 vs 0.2094) AND recall (0.3427 vs 0.3139),
  with `coverage_at_tau` rising 0.6667 -> 0.7992. That is a properly collided
  result and should be treated as one of the few solid post-wipe measurements.
  The doc also disarms its own trap: "`n_proteins` is not monotone (1006, 928,
  1047, 991, 1206). It is a count at the optimum threshold, which moves, so it
  is not a cohort size and a correlation with it has no reading." -- which is
  the memory entry `project_scorer_absorbs_backbone_axis_2026_08_23` applied
  correctly by the same author, on the same axis, in the current window.

## E3. THE DEPTH RESULT SUPERSEDES THE STANDING "USE 3 TO 10" MEMORY
verdict: CONTRADICTED (the memory index is now stale on this)
first number: memory index entry -- "**Thirty neighbours is too many; use 3 to
  10**: 16 of 18 comparisons across two populations and two encoders"
  (`project_neighbour_count_thirty_is_too_many_2026_08_19.md`, PRE-wipe).
second number: docs/incidents/2026-08-30-depth-series.md -- "Monotone in all
  five cells with no exception: shallower is better, and the winner is at the
  edge of what was measured. ... **The optimum therefore lies below 2, in the
  territory of K=1**, which is a different regime rather than another level of
  this axis: one donor per (protein, aspect), announcing itself by two measured
  routes. The series does not cross into it on purpose."
date of evidence: memory 2026-08-19 (pre-wipe), incident 2026-08-30 (post-wipe)
frame: the post-wipe run is on the leak-free window with the corrected donor
  policy, sequence-based self-exclusion and depth counted in SEQUENCES. The
  pre-wipe one is not, and depth-in-proteins vs depth-in-sequences is a
  different unit (PR #882: "a neighbourhood is counted in sequences, not in
  proteins").
note: so the two are not even measuring the same axis in the same unit, and the
  post-wipe one is the one in the current window. The document is careful:
  "It reproduces ... a law measured before the 2026-08-27 wipe: depth is
  monotone, deeper is worse, and the winner is always the edge, so there is no
  interior optimum." This is one of the VERY FEW pre-wipe laws that has been
  re-established post-wipe. Flag it as such.
note2: "These five cannot share an axis with the 71 sealed results of the
  previous campaign. Four axes moved between them, **one of which changed
  meaning without changing any recorded field.**" -- so 71 sealed results from
  the previous campaign are NOT comparable to the current ten, and the reason is
  a silent semantic change. That is the frame problem stated by the project
  itself, in the current window, and it puts a hard wall between the pre-wipe
  and post-wipe evaluation records.

## E4. PREDICTION SET `a789582e` IS A THIRD REGIME, KEPT ON PURPOSE, WITH FOUR SEPARATE DEFECTS
verdict: CONFIRMED (and it carries an explicit RETRACTION of a circulated number)
source: docs/incidents/2026-08-29-prediction-set-a789582e.md, `d65daba` 2026-08-29
first numbers, all "counted directly against the store on 2026-08-29":
  `a789582e-fa6d-4d91-9fd3-0a6c4b649427`, **2,801,404 rows, 0 evaluation results.**
  1. **Out-of-policy donations: 1,523,939 of 2,801,404 rows = 54.4%.** The set
     declares a thirteen-code experimental policy and donated under
     IEA 787,716 / IBA 297,778 / ISO 215,571 / ISS 151,426 / NAS 46,142 /
     ND 16,722 / RCA 4,617 / ISA 2,186 / ISM 1,713 / IGC 68.
     (My check: those ten sum to 1,523,939 exactly -- see below.)
  2. **Self-donation: 133,866 rows over 6,012 proteins** with donor accession ==
     query accession, "under `exclude_self_neighbour: true`. **The flag was
     recorded and did not govern.**"
  3. **No donor ledger: 193,303 rows over 1,024 proteins, exactly one batch**,
     `donor_count` and `sequence_rank` NULL on every row. "The `job_event`
     stream stamps that batch's host as **`desktop-gpu`**. The compute node ran
     a revision that predated the change adding those columns, and the run
     reported success."
  4. **Declared ontology snapshot is not the one its terms belong to.** Declared
     `a24e7d91`; "Zero of its rows carry a term belonging to that snapshot;
     every term resolves to `36038118`. A consumer trusting that field gets
     nothing."
second number (INDEPENDENT, my arithmetic on their own breakdown):
  787,716 + 297,778 + 215,571 + 151,426 + 46,142 + 16,722 + 4,617 + 2,186
  + 1,713 + 68 = **1,523,939**. Matches the stated total EXACTLY, and
  1,523,939 / 2,801,404 = 0.54398 -> 54.4%. Both check out. This is a document
  that published its breakdown so it COULD be collided (COLLIDING-A-NUMBER
  rule 2 satisfied), and it survives the collision.
date of evidence: 2026-08-29 -> window: post-wipe-current
platform gap: the census is reproduced by three hand-written SQL queries printed
  at the end of the document. There is no operation. An `audit_prediction_set`
  operation writing an artifact is what would make this reborn in the database.
  MURO today.
note: defect 3 is THIS MACHINE. CLAUDE.md's whole framing is that the desktop is
  stateless and a reboot is harmless. That is true for throughput and false for
  provenance: a stale revision on `desktop-gpu` wrote 193,303 rows with a NULL
  ledger and reported SUCCESS. PR #893 added the guard
  (`protea/core/code_revision.py`, 235 lines, added 2026-08-29 18:55) and PR #896
  extended it ("the guard compares the siblings too, not just the repository").
  This is the concrete instance behind `feedback_a_stale_process_is_not_a_stale_tree`.
note2: defect 2 (`exclude_self_neighbour` recorded and inert) is a FIFTH member
  of the accepted-recorded-inert class, and NO document holds the running count.
  Three documents give three different tallies of the same class:
    - COLLIDING-A-NUMBER.md section 4: "`own_k` ... That is the fourth instance
      in this project of the same class"
    - docs/findings/2026-09-01-generation...: "This is the fourth time in this
      project that a parameter has been accepted, recorded where a reader would
      trust it, and not governed the computation" (also about `own_k`)
    - docs/findings/2026-08-30-what-the-direct-method...: "It has now happened
      with the depth cut, with the code revision, and with the denial filter's
      three writer paths"
  Enumerating what is actually named across the corpus: (1) `own_k`,
  (2) `max_sequence_rank` / the depth cut (#904), (3) the code revision (#893),
  (4) the denial filter's three writer paths (#912), (5)
  `exclude_self_neighbour` (#890), (6) the donor policy gating the pool but not
  the donations (#890). That is SIX, not four. **The project's own most-cited
  defect class is undercounted by a third in every document that cites it**, and
  there is no register. Recommend one.

## E5. A CIRCULATED MAGNITUDE FIGURE IS RETRACTED, AND THE SIGN REVERSES
verdict: CONTRADICTED (an explicit, dated retraction in the current window)
first number: "The magnitude figure of **20.70 to 12.13** that circulated is an
  internal before and after of this set."
second number, from the same document: "Against `d5b634b2`, which produced 63 of
  the 71, the same comparison is **NK 14.46 to 12.53 and PK 9.59 to 10.78, where
  the sign reverses. Do not reuse that trio.**"
date of evidence: 2026-08-29 -> window: post-wipe-current
frame: `a789582e` is "not 'the old baseline'. It is a third regime, and its
  numbers must never be reused as one. The only defensible use of them is an
  explicitly labelled before and after of the defect itself, never a shared axis
  and never a figure the new numbers beat."
population: NK and PK reported separately; LK not reported, and no aspect split.
  So even the correction is over 2 of 9 cells.
note: I searched the plan store and the memory index for "20.70" and "12.13" and
  found neither, so the retraction has not leaked into the documents I can see.
  But "that circulated" means it travelled somewhere. Anyone finding 20.70/12.13
  in another slice should treat it as RETRACTED and cite this file.

## E6. THE 71 SEALED RESULTS ARE FROM TWO PREDICTION SETS AND FOUR AXES MOVED
verdict: CONFIRMED, and it is a hard wall across the wipe
first number: "The 71 sealed evaluation results come from `d5b634b2` (63,
  permissive, k=10) and `8a75f84e` (8, evidence codes under pool-admission
  semantics, k=10). Four axes move between them and any corrected run: **depth
  10 to 30, the policy's value on 63 of 71, the policy's meaning on all 71, and
  self-exclusion. Only the third moves without changing any recorded field**,
  which is why the code revision is now one of the fields an arm is named by."
second number (INDEPENDENT, against the brief): the live DB holds 93
  evaluation_result rows and 19 prediction_set rows, all 2026-08-27 to
  2026-08-30. 71 sealed + the 10 depth-series rows of E1 = 81, leaving 12
  unaccounted. So the 71 are ~76% of the entire current evaluation record, and
  ALL 71 are declared non-comparable to any corrected run on four axes, one of
  them invisible in the schema.
date of evidence: 2026-08-29 -> window: post-wipe-current
note: read together with E1: of 93 rows, 71 sit on a superseded frame, 5 are
  known-wrong and unmarkable, 5 are the corrected depth series. **At most 12
  rows in the entire live database are both current-frame and undisputed**, and
  I could not identify which. This is the honest state of the evaluation record
  and it should lead any census summary.

## E7. THE CEILING DOCUMENT IS THE BEST-DISCIPLINED THING IN THE PROJECT, AND ITS DENOMINATORS STILL DO NOT RECONCILE
verdict: CONFIRMED as a correction; CONTRADICTED on population arithmetic
source: docs/incidents/2026-08-30-where-the-ceiling-comes-from.md, `cb279f8` 2026-09-01
the correction it publishes (this part is exemplary and should be cited as the
model for the project): "The first version of this document put the ceiling at
  **55.8 per cent**. That number matched a predicted term against a true term as
  strings. The evaluation does not do that: it propagates predictions up the
  ontology before scoring ... Measured the way the scorer measures, the ceiling
  is **77.9 per cent**."
  It then reproduces the superseded number as a control -- "The first row
  reproduces the superseded number exactly, which is how the reconstruction was
  verified" -- which is COLLIDING-A-NUMBER rule 1 done properly, and rare.
  It also explicitly separates what survives from what does not:
    SURVIVES: depth monotone, shallower better; **zero of nine strata have a
      resolved winner among twelve arms**; the embedding has several times less
      signal about missed pairs and orders a third of them worse than chance;
      encoder choice is a STEP not a gradient; the 4.2% unreachable is real
      (previously overstated at 5.7%).
    DOES NOT SURVIVE: **"The whole gap is retrieval."** The retrieval-attributable
      gap is 17.9 points, not 36.8.
    NEW: reach is no longer the binding constraint. union-of-twelve 77.9%,
      one arm (esm2_650m) 64.3%, that arm's recall at its operating point
      0.22-0.61 across nine cells, precision 0.087-0.496. "Between 'the right
      candidate is in the list' and 'the right candidate is scored above tau'
      the method loses more than it loses to retrieval."

MY INDEPENDENT ARITHMETIC, and where it fails to close:
  Decomposition table (denominator 56,816 new pairs):
      reached                      44,273  -> 44,273/56,816 = 77.92%  OK
      missed, term absent from bank 2,376  ->  2,376/56,816 =  4.18%  OK
      missed, term present         10,167  -> 10,167/56,816 = 17.89%  OK
      sum = 56,816 EXACTLY. This table closes.
  Signal table (the 7.10x vs 1.78x result):
      reached 43,174 + missed 10,431 = **53,605**
  These are DIFFERENT POPULATIONS and the document never says so:
      56,816 - 2,376 = 54,440 pairs whose term IS in the bank, which is what the
      signal test says it covers -- but the signal table has 53,605, **835 fewer**.
      reached falls 44,273 -> 43,174 (**-1,099**, and a "reached" pair by
      definition HAS a carrier, so this loss is unexplained).
      missed-present RISES 10,167 -> 10,431 (**+264**).
  And a fourth number: `scripts/analysis/carrier_signal_propagated.py` opens
      """The full measurement: **53,680 pairs**, reached and missed ..."""
      53,680 - 53,605 = **75** more than the published table.
  FOUR denominators for one measurement -- 56,816, 54,440 (implied), 53,605
  (published), 53,680 (the script's own docstring) -- and none reconciled.
date of evidence: 2026-08-30 measurement, 2026-09-01 commit -> post-wipe-current
frame: bank `cbb35a32` to 2024-04-10; truth `ec9f5c2c` to 2025-09-03; donor
  policy thirteen experimental evidence codes; query set 14,032 proteins; pool
  86,068; NOT-qualified annotations excluded from BOTH sides (which is why the
  new-pair count is 56,816 here against 56,895 in the first version, a 79-pair
  difference the document DOES explain); propagation `is_a` and `part_of` only,
  to depth 20.
population: nine cells named but the ceiling itself is not stratified by cell.
platform gap: **the whole analysis surface is unversioned-by-the-project's-own-
  definition.** `scripts/analysis/` was created 2026-09-01 and holds five files:
  ceiling.sql (142 lines), carrier_signal.py, carrier_signal_propagated.py,
  ontology_encoder_alone.py, protein_as_a_join.py. None is an operation, none
  writes to the object store, none has a payload, none appears in the registry.
  This is a NEW instance of exactly the defect GENESIS-STATE was written to
  close, created five weeks after GENESIS-STATE.
note (THE REPRODUCIBILITY CLAIM IS FALSE ON THIS MACHINE): the document ends
  "The measurement is reproducible from `scripts/analysis/ceiling.sql`, which
  builds every table above from the database and prints all of them". It does
  not. The two python arms read THREE files from `/tmp` that nothing persists
  (`/tmp/allcarriers.csv`, `/tmp/allqemb.csv`, `/tmp/allpairs_prop.csv`) and a
  hardcoded reference cache at
    `BASE = "/home/bioxaxi2/Thesis-laptop/PROTEA/data/ref_cache/"`
  `test -d /home/bioxaxi2` -> **MISSING**. That is the LAPTOP's home directory
  (`bioxaxi2`, `Thesis-laptop`), so the numbers were computed on the server node
  and the script cannot run on the compute node it is committed to.
note2 (A TABLE THE DOCUMENT ITSELF MARKS AS NOT RECOMPUTED): the five-encoder
  table (esm2_650m 1.64x, rung2-pooled 1.82x, esmc_600m 1.93x, esm2_t36_3B
  1.96x, esm2_8m 1.92x) carries its own blockquote: "This table was computed on
  the superseded split and **has not been recomputed** ... It should be read as
  indicative and not quoted as a measurement on the current split." Anyone
  quoting "encoder choice is a step, not a gradient" as measured is quoting a
  400-pair sample on a superseded split. The CONCLUSION is listed under
  "Survives"; the TABLE under it is not current. Both are true and the pairing
  is easy to misread.

## E8. THREE DIFFERENT HOME DIRECTORIES ARE HARDCODED IN THE DEPLOY TREE
verdict: CONFIRMED
first number: none published anywhere.
second number (mine): `grep -rho '/home/[a-z0-9]*'` over the deploy tree:
    7 x `/home/frapercan`   (the PRE-REINSTALL username on this machine)
    5 x `/home/bioxaxi2`    (the LAPTOP / server node)
    and the machine's actual home is `/home/xaxi` (`ls /home/` -> one entry).
  Sites:
    /home/frapercan: scripts/hpo_champion_score.py:61;
      tests/test_lafa_frame_parity.py:278; protea/api/routers/datasets.py:351,356,361;
      protea/core/classifier_producer.py:74,76
    /home/bioxaxi2: scripts/analysis/carrier_signal.py:17;
      scripts/analysis/carrier_signal_propagated.py:17;
      scripts/materialise_floor_census.py:32 and :123 (an OUTPUT path:
      "/home/bioxaxi2/Thesis-laptop/PROTEA/results/floor_census");
      deploy/systemd/install.sh:12 (SRC=... -- an INSTALLER)
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: a lint. `agent-farm` already runs em-dash and row-alignment lints
  in the pipeline; a `no-absolute-home-paths` check is the same shape and would
  have caught all twelve. GENESIS-STATE section 2 item 6 argued exactly this for
  the join defect and the argument generalises.
note: `deploy/systemd/install.sh` is the one that bites hardest -- an installer
  that copies from a directory that does not exist on the machine it installs
  onto. And per CLAUDE.md, systemd units are how workers survive this machine's
  unannounced reboots.

---

# PART F. The seven plan directories in my slice

Every one has mtime `Jul 28 17:01` (the restore) and a git last-touch that
PREDATES the reinstall. None has been amended in the current window.

| plan | git last touched | commits | slice states |
|---|---|---|---|
| executor/PLAN.md (122 KB) | 2026-06-11 `eea86fc` | 33 | 77 done, 37 pending, 4 deferred, 2 blocked |
| farm-platform/PLAN.md (204 KB) | 2026-06-24 `6287a34` | 72 | 71 done, 35 pending, 6 deferred |
| dag-scheduler/PLAN.md + HANDOFF.md | 2026-06-22 `364bf8a` | 1 | 7 pending, 1 deferred -- NEVER STARTED |
| productization/PRODUCTIZATION-ROADMAP.md | 2026-07-02 `9e14244` | 1 | no status fields at all |
| doc-writer/PLAN.md | 2026-06-07 `20e11fb` | 9 | 16 done, 0 pending |
| bioinfo-quick/PLAN.md | 2026-05-18 `640a595` | 9 | 10 done, 2 deferred |
| roadmap-from-zero/PLAN.md | 2026-06-24 `6287a34` | 2 | 1 done, 4 pending, 1 deferred |
| FIRST-BOOT.md | 2026-07-28 `c56382a` | 1 | -- |
| GENESIS-STATE.md | 2026-07-28 `8668180` | 2 | -- |

## F1. dag-scheduler: never started, and I nearly filed a false negative
verdict: CONFIRMED not-started; my first negative check was WRONG and I am
  recording the correction because it is the point of rule 4
first check (WRONG): I grepped `agent-farm/` for `stack_owner.sh`,
  `plan_parser.py`, `dispatch_with_lock.sh`, `deploy-keeper-tick.sh` at
  `scripts/` and found none, and was about to report the plan's prerequisites
  as missing.
second check (CORRECT): `find . -name` located all four one directory down --
  `scripts/lib/stack_owner.sh`, `scripts/lib/plan_parser.py`,
  `scripts/services/lib/dispatch_with_lock.sh`,
  `scripts/services/deploy-keeper-tick.sh`. The machinery EXISTS.
verdict on the plan itself: all 7 F-SCHED slices `status: pending`, one
  `deferred`, one commit ever (2026-06-22). Nothing implemented: grep for
  `find_frontier`, `lease_registry`, `node_registry`, `quarantined` across
  agent-farm hits ONE file, `scripts/coord/coord-tick.sh`.
note: the HANDOFF.md is a Spanish-language prompt to paste into a live
  conductor session. Whether it was ever pasted is unrecoverable; the plan's
  own status fields say the answer is no.

## F2. `cold-boot.sh` -- two divergent copies, INCOMPATIBLE FLAGS, still open
verdict: CONFIRMED, and I verified the incompatibility rather than the count
first number: GENESIS-STATE.md section 3B: "self-heal (`cold-boot.sh`, and note
  that **two divergent copies exist with incompatible flags**; the agent-farm
  one is canonical and the docs point at the other)."
second number (INDEPENDENT, md5 + flag extraction, 2026-09-02):
    agent-farm/scripts/cold-boot.sh              md5 39f893a37864b6914719e4cf63779bcb
    repositories/PROTEA/scripts/cold-boot.sh     md5 906c40e069d3f828ed714156c199a16e
    worktrees/protea-deploy/scripts/cold-boot.sh md5 906c40e069d3f828ed714156c199a16e  (same file, two checkouts)
  Flags unique to the agent-farm copy: `--deploy --force-deps --hard --max-time
    --restart --short --status --sync`
  Flags unique to the PROTEA copy:    `--fast --no-build --no-deps --no-ngrok
    --no-watchdog --value`
  **Zero overlap on the distinctive flags.** Invoking one with the other's
  documented flags fails.
date of evidence: 2026-09-02 -> window: post-wipe-current. STILL OPEN 36 days on.
platform gap: neither is an operation; both are shell. The fix is to delete one.

## F3. roadmap-from-zero: THE "+40%" HEADLINE IS AN ECHO, AND ITS RECEIPT IS GONE
verdict: DEDUCED-NOT-MEASURED / ECHO. This is a claim, not a measurement, in
  every place I can reach.
first number: `plans/roadmap-from-zero/PLAN.md` states it THREE TIMES:
  line 7  "our own validated, NOVEL lever: the learned GO-aligned k-WTA hard-neg
           retrieval encoder (**beats dense KNN ~40% reranked**, no CAFA solution
           has it)"
  line 18 "learned encoder retrieval arm (OURS, **+40% reranked**) => the differentiator"
  line 67 "The learned k-WTA hard-neg retrieval representation (**validated +40%
           reranked** on a consistent frame)"
  Echoed four more times outside my slice:
    plans/thesis-clean-iteration/PLAN.md:87 "(config d8979601, the +40% lever)"
    plans/representation-science/PLAN.md:31 "The +40% lever is real on f_micro_w, not just proxy."
    plans/sparse-classifier/PLAN.md:7      "encoder beat dense mean-pool +40%"
    repositories/protea-reranker-lab/research/layer_ablation/WRITEUP.md:19
    repositories/protea-reranker-lab/results/sparse_classifier/s2e_pure_d8979601/run.py:4
  SEVEN documents, ONE claim.
second number (INDEPENDENT, from the only place a concrete pair is published):
  `plans/representation-science/PLAN.md:28-31` -- "Learned encoder VALIDATED on
  the real f_micro_w frame (LAFA FINAL_227_230): learned-mean (`d8979601`)
  KNN-only BEATS the champion (mean+reranker) in NK/LK by **+0.05..+0.13**
  (**NK MFO 0.507 vs 0.398**)."
    0.507 / 0.398 = **1.274**, i.e. **+27.4% relative**, not +40%.
    +0.109 absolute, which is the TOP of the stated +0.05..+0.13 range.
  So the single published pair, which is the best case in the stated range,
  gives 27%. To reach 40% relative from a 0.398 base you need 0.557, which
  appears nowhere.
  THE PRIMARY RECEIPT IS UNREACHABLE: representation-science/PLAN.md:28 cites
  "see memory `project_validation_findings_2026_06_25`". I listed all 210 files
  in `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`; **that file is
  not among them.** It was archived in the 2026-07-27 curation to
  `/mnt/protea-archive/archive/memory-archive-2026-07-27/`, and
  `ls` of that path returns "No existe el archivo o directorio" -- it is on the
  unmounted partition of D1.
date of evidence: claim dated 2026-06-25 -> window: **pre-reinstall AND
  pre-wipe.** By the audit's own rule it is not evidence about the current
  window at all.
frame: "LAFA FINAL_227_230", learned-mean `d8979601` KNN-only vs champion
  (mean+reranker). Note the comparison is KNN-ONLY against MEAN+RERANKER, i.e.
  the two arms differ on TWO axes (representation AND whether a reranker runs),
  so even the 27.4% is not attributable to the encoder alone.
population: NK/LK only; "PK = the wall (no arm helps)" in the same entry. So the
  lever is claimed on 6 of 9 cells at best and the published pair is ONE cell
  (NK MFO).
platform gap: `apply_learned_encoder` IS a registered operation (added
  2026-06-24), so the encoder arm CAN be reborn on-platform. What cannot is the
  measurement: config `d8979601` is not on this disk (memory
  `project_learned_encoder_published_and_order_proven_2026_08_23`), and the
  storage tree only carries scripts that reference it
  (`storage/encoder-study/scripts/105_publish_bundle_to_store.py`,
  `106_stamp_order_and_verify.py`).
note: the current-window evidence points the OTHER WAY on the encoder axis:
  "Zero of nine strata have a resolved winner among twelve arms" and "Encoder
  choice is a step and not a gradient", spread 1.64x-1.96x across five encoders
  spanning a 375-fold parameter range
  (docs/incidents/2026-08-30-where-the-ceiling-comes-from.md); and
  `entail_kwta` scores 0.011 against an anchor of 0.144
  (docs/findings/2026-09-01-generation-...). Different tasks, so not a direct
  refutation, but nothing in the post-wipe record supports "+40%" and the plan
  that carries it is the roadmap to "the highest reproducible CAFA/LAFA score".
note2: roadmap-from-zero's R0.1 is `status: done`, and its acceptance includes
  "a baseline dense-KNN reranked f_micro_w **reproduced bit-identically across
  two independent runs**". The current-window statement is "Evaluation
  reproduces exactly, 117 of 117 metrics. **Retrieval does not.**"
  (docs/findings/2026-08-30-what-the-direct-method-has-to-get-right.md §9).
  Half the acceptance criterion is met and the plan is marked done.
note3: the plan's stated premise -- "NOT a DB wipe: the 527k x 8-PLM embeddings
  are expensive and fine" -- was overtaken by the 2026-07-28 reinstall and the
  2026-08-27 registry wipe. The document has not been amended.

## F4. productization/PRODUCTIZATION-ROADMAP.md has no status fields at all
verdict: NOT_FOUND (nothing to check)
It is the only plan in my slice with zero `status:` entries, one commit
(2026-07-02), and therefore no machine-readable state. `plan_parser.py` cannot
schedule it and nothing tracks whether any of it happened.

---

# PART G. The scheduled-jobs surface: ZERO of five installed, and no backup exists here

## G1. `crontab -l` -> "no crontab for xaxi"
verdict: CONFIRMED (all five entries absent, 36 days after the reinstall)
first number: FIRST-BOOT.md section 1, listed under "What it does not do, and
  nothing else does either. Each of these has to be done by hand": "**The five
  scheduled jobs**, recorded in `agent-farm/observability/CRONTAB.md`. One of
  them points into `storage/`, so it fails silently until that tree is restored."
  Same list in GENESIS-STATE.md section 3A.
second number (INDEPENDENT, from the host):
    crontab -l                  -> "no crontab for xaxi"   (ZERO entries)
    systemctl --user list-timers -> ONE project timer, `protea-node-sync.timer`.
                                   No pgdump timer, no restore-drill timer.
  So none of the five was ever installed, and nothing replaced them.
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: MURO by construction -- a crontab is host state, and the project's
  own invariant is that host state is not preserved. The right fix is a systemd
  timer under version control, which `agent-farm/scripts/services/` already
  demonstrates for `protea-node-sync`.
note: THREE separate reasons each entry would fail even if installed verbatim.
  (a) All five lines hardcode `/home/frapercan/...`, the dead username (see E8).
  (b) The nightly pg_dump gates on
      `df --output=avail -BG /mnt/protea-archive` -- the partition D1 proves is
      not mounted. `df` on a plain directory silently reports the ROOT
      filesystem (179 GB available here), so the guard would report PASS while
      measuring the wrong disk. That is COLLIDING-A-NUMBER rule 4 embedded in a
      cron line.
  (c) The conductor-monitor entry runs
      `/home/frapercan/Thesis2/storage/conductor-monitor/recorder.py`.
      `storage/conductor-monitor/` DOES NOT EXIST on this machine
      (the surviving copy is `agent-farm/observability/recorder.py`), and
      CRONTAB.md says the scratch path "is deliberate and must not be repointed
      without the operator's say-so". So the deliberate pointer points at nothing.

## G2. `install-all-crons.sh` DOES NOT EXIST
verdict: CONTRADICTED (the record cites an installer that was never written)
first number: `agent-farm/observability/CRONTAB.md`, lines 5-7: "only two had an
  installer script in this repository (`install-restore-drill-cron.sh`,
  `install-nightly-pgdump-cron.sh`), so the other three existed only in the
  running crontab and nowhere else. This file is the record; **`install-all-crons.sh`
  beside it reinstalls them.**"
second number (INDEPENDENT): `find agent-farm -name 'install-all-crons.sh'`
  returns NOTHING. The two named installers DO exist at
  `agent-farm/scripts/install-nightly-pgdump-cron.sh` and
  `agent-farm/scripts/install-restore-drill-cron.sh`. The third file, the one
  the document says covers the other three entries, was never written.
date of evidence: 2026-09-02 -> window: post-wipe-current
note: this is the exact shape of the seven no-producer artifacts of Part A --
  a document naming a producer that does not exist -- occurring in the very
  document written to prevent it, on the day of the reformat. It is also a
  narrated check nobody gated on: the sentence asserts a recovery path and the
  path is absent.

## G3. THERE IS NO DATABASE BACKUP ON THIS MACHINE AND NONE IS SCHEDULED
verdict: CONFIRMED (with a scope caveat I cannot close from here)
first number: the crontab of record schedules
  `pg_dump --format=custom --no-owner --file=.../backups/protea-$(date +%Y-%m-%d).dump`
  nightly at 03:00, plus a 03:15 rotation keeping three.
second number (INDEPENDENT):
    ls /home/xaxi/Thesis2/backups         -> "No existe el archivo o directorio"
    find /home/xaxi -maxdepth 4 -name '*.dump'  -> nothing
    crontab -l                            -> no crontab
    systemctl --user list-timers          -> no dump timer
  Zero dumps, no directory, no schedule.
date of evidence: 2026-09-02 -> window: post-wipe-current
SCOPE CAVEAT, stated because rule 4 demands it: `CLAUDE.md` and `TOPOLOGY.md`
  say the LAPTOP is the persistent server and owns the database, so the backup
  duty may have moved there with the topology split. I cannot see the laptop and
  I am forbidden from touching any database. What I can assert is exactly this:
  **on the compute node there is no dump, no backups directory, and no
  schedule**, and the crontab of record -- captured 2026-07-27, i.e. under the
  same topology -- put the dump HERE against `localhost:5432/protea`.
  Someone with laptop access must close this. If it turns out nobody dumps, the
  entire post-wipe campaign (93 evaluation_result rows, 19 prediction_set rows,
  2026-08-27 to 2026-08-30) has no copy, in a database that was already wiped
  once.
note: rank this first for action. Everything else in this report is a record
  defect; this one is the only live risk of losing the record itself.

## G4. `TOPOLOGY.md` differs between the two agent-farm checkouts
verdict: CONFIRMED
`diff -rq /home/xaxi/Thesis2/agent-farm/plans /home/xaxi/Thesis2/repositories/agent-farm/plans`
reports `TOPOLOGY.md` as DIFFERENT, plus five files present only in the root
copy (ABLATION-ARCHITECTURE.md, COLLIDING-A-NUMBER.md, DECLARED-REVISION.txt,
LEARNED-REPRESENTATION-ABLATION.md, ORCHESTRATION.md).
  root `/home/xaxi/Thesis2/agent-farm`        HEAD 07f90bf 2026-09-02 01:24 (current)
  `/home/xaxi/Thesis2/repositories/agent-farm` HEAD c76588a 2026-08-23 (10 days stale)
CLAUDE.md's own instruction is "**The shared description of the split is
`agent-farm/plans/TOPOLOGY.md`.** Read it rather than trusting this section: it
is in a repository, so it is the same file on both machines". That guarantee is
the reason the file is trusted, and it is false between two checkouts on THIS
machine, never mind between machines. Anyone reading
`repositories/agent-farm/plans/` gets a ten-day-old plan store INCLUDING a stale
GENESIS-STATE and no COLLIDING-A-NUMBER.md at all.
note: the root clone is the canonical one per CLAUDE.md. Recommend deleting or
pinning `repositories/agent-farm`.

## G5. A number from PR #890 that belongs in the census: the NK panel was handed a prior
verdict: CONFIRMED (measured, post-wipe, and it hits the SERVED population)
first number, from commit message of `#890` (2026-08-29, "fix(donors): the
  policy governs what is donated, not only who may donate"), measured on
  prediction set `a789582e`, 2,801,404 rows:
    rows whose winning donor's evidence code the policy EXCLUDES: 1,523,939 (54.4%)
    **`(protein, aspect)` cells with no experimental prior predicted from the
      protein's OWN IEA row: 1,300**
  "That last row is the one that matters most: **the panel that exists to
  measure prediction *without* a prior was being handed one**, through the
  protein's own non-experimental annotation."
second number: cross-checks exactly against the E4 census document, which was
  written the same day from the same set and gives the same 1,523,939 / 54.4%
  and the same ten-code breakdown. Same author, same set -- so it is
  CORROBORATION OF TRANSCRIPTION, not an independent measurement.
date of evidence: 2026-08-29 -> window: post-wipe-current
population: the NO-KNOWLEDGE cell, which per the memory index IS the served
  population and about 5% of a window. 1,300 contaminated cells.
note: the same message names a second thing worth carrying: "**ISO and ISS
  deserve naming apart from the volume.** Those 366,997 rows are annotations
  created by sequence similarity, transferred again by sequence similarity, and
  scored against an experimental truth. A donor of that kind that hits is not
  evidence of transferring experimental knowledge; it is agreement with another
  automatic method doing what this one does." That is a definitional argument
  about what a hit MEANS, not a measurement, and it is stated as such. 366,997 =
  215,571 (ISO) + 151,426 (ISS), which I checked and it is exact.

---

# PART H. The record surfaces themselves

## H1. THE ADR RECORD STOPPED ON 2026-08-17, TWO WEEKS BEFORE THE CODE DID
verdict: CONFIRMED
first number: 55 ADRs in `worktrees/protea-deploy/docs/source/adr/` (identical
  set in `repositories/PROTEA`). Newest two: `D46-information-accretion-as-tracked-artifact.rst`
  and `D47-archive-the-obo-behind-every-snapshot.rst`, both first committed
  2026-08-17 13:20:39 `7448003`. Nothing after D47.
  Lab ADRs (`repositories/protea-reranker-lab/docs/adr/`, 4 files) stop at
  2026-06-08. agent-farm decisions (`docs/decisions/`, 4 files) stop at D34.
second number (INDEPENDENT): `git log --oneline --since=2026-08-17` in
  protea-deploy returns **151 commits**, including at minimum these
  architectural changes with no ADR:
    the denial filter and its policy source of truth (#912)
    frame sealing (#877, #878, seal_evaluation_frames)
    the paired-panel bootstrap and MDE machinery (#877)
    depth counted in sequences rather than proteins (#882, #883, #884, #885, #886)
    the code-revision provenance guard (#893, #896)
    the donor policy governing donations, not just admission (#890)
    self-exclusion by sequence (#881)
    the cache key carrying an epoch (#891)
    an ontology encoder over GO's own structure (#914)
date of evidence: 2026-09-02 -> window: post-wipe-current
note: the project HAS a decision-record habit -- 55 ADRs over four months -- and
  it stopped exactly ten days before the wipe, in the period of heaviest
  architectural change. The `docs/findings/` and `docs/incidents/` directories
  opened on 2026-08-29/30 and are doing that job in a different genre. Nothing
  says the ADR line was retired; it simply stops.

## H2. THE POST-WIPE RESEARCH RECORD IS NOT IN THE PUBLISHED DOCUMENTATION
verdict: CONFIRMED (a negative check with its reach stated)
first number: root `CLAUDE.md`, "Published prose: no identifiers": "**The Sphinx
  operational reference is the exception and carries the concrete identifiers,
  because that is where an examiner goes to verify reproducibility.** The split
  is argument surface versus verification surface."
second number (INDEPENDENT): I grepped `docs/source/index.rst`, `docs/source/conf.py`
  and every `.rst` under `docs/source/` for `findings` and `incidents`. The only
  hits are unrelated prose and an ORM column name. **Neither `docs/findings/`
  nor `docs/incidents/` is in any toctree.** They are loose markdown outside the
  Sphinx tree, so they do not appear in the built documentation at all.
date of evidence: 2026-09-02 -> window: post-wipe-current
platform gap: two lines in a toctree.
note: the six documents in those two directories are, as far as I can find, the
  ENTIRE narrative research record of the current window: three findings
  (2026-08-30 x2, 2026-09-01) and three incidents (2026-08-29, 2026-08-30,
  2026-09-01, the last committed under a `docs(findings):` subject into
  `docs/incidents/`). They contain the ceiling correction, the depth series and
  its five poisoned results, the `a789582e` census, and the generation negative
  result. An examiner following CLAUDE.md's own instruction to the verification
  surface sees NONE of it. The last thing the Sphinx tree records is D47, dated
  2026-08-17, ten days before the wipe.
note2: `docs/EVAL_LAFA_PARITY.md`, cited by `roadmap-from-zero` R0.1's acceptance
  criteria, was last touched 2026-08-17 -- also before the wipe and before the
  depth-unit change that #882 made. Its parity claim has not been re-checked
  against the current frame.

## H3. Where I looked for findings/ADR directories, across all eight repositories
Stated so the negative is worth something (COLLIDING-A-NUMBER rule 4).

| repository | ADR / decisions | findings / incidents | docs last touched |
|---|---|---|---|
| PROTEA (deploy `a5de702`) | `docs/source/adr/` 55 files, newest 2026-08-17 | **`docs/findings/` 3 files, `docs/incidents/` 6 files (3 post-wipe)** | 2026-09-01 |
| PROTEA (`repositories/`, `c28c4ae`) | same 55 ADRs | **NEITHER directory exists** (predates them) | 2026-08-20 |
| protea-reranker-lab | `docs/adr/` 4 files, newest 2026-06-08 | none | `results/` and `research/` frozen at 2026-07-27 |
| agent-farm | `docs/decisions/` 4 files (D31-D34) | none | root clone 2026-09-02, `repositories/` clone 2026-08-23 |
| protea-method | none | none | 2026-06-03 (10 files) |
| protea-backends | none | none | 2026-05-12 (7 files) |
| protea-contracts | none | none | 2026-07-10 (21 files) |
| protea-runners | none | none | 2026-05-13 (6 files) |
| protea-sources | none | none | 2026-05-12 (6 files) |
| cafaeval-protea | none | none | 2026-06-24 (10 files) |

**Six of the ten checkouts have had no documentation change since before the
reinstall, and five have had none since May or June.** The lab, where all the
re-ranker science lives, has had NO commit at all since 2026-08-19 (repo head
2026-08-17; the newest lab worktree, `lab-bundle`, is 2026-08-19). Every lab
result in the repository is therefore PRE-WIPE, and by this audit's own rule
none of it is evidence about the current window.

Consequence for the census: the current window's entire narrative research
record is SIX markdown files in ONE repository, none of them in a published
documentation build, and the repository they live in (`worktrees/protea-deploy`)
is a worktree that `repositories/PROTEA` does not contain.

---

# SUMMARY: ranked, for the requester

## The three that matter most

1. **G3 + G1 + G2 -- THERE IS NO DATABASE BACKUP ON THIS MACHINE AND NONE IS
   SCHEDULED.** `crontab -l` -> "no crontab for xaxi"; `~/Thesis2/backups/` does
   not exist; no `*.dump` anywhere under `/home/xaxi`; the only project systemd
   timer is `protea-node-sync`. The recovery document names an installer
   (`install-all-crons.sh`) that was never written, and all five recorded cron
   lines hardcode the dead username `/home/frapercan`. The database that would
   be dumped holds the ENTIRE current campaign (93 evaluation_result rows,
   19 prediction_set rows, 2026-08-27 to 2026-08-30) and has already been wiped
   once. Scope caveat: the topology says the laptop owns the database, so
   someone with laptop access must confirm whether a dump runs there; what is
   certain is that nothing dumps here, and the 2026-07-27 crontab of record --
   captured under the same topology -- put the dump here.

2. **E1 -- FIVE OF THE 93 LIVE `evaluation_result` ROWS ARE KNOWN-WRONG, KEPT
   DELIBERATELY, AND CANNOT BE MARKED.** Result ids `67fe2fa0`, `28621824`,
   `9de60449`, `53d68960`, `d0705d22` are sealed under the SAME frame digest
   `f-1c245d41f26ff70c3b0a9247` as the five corrected ones and carry the same
   `leakage_role='select'`. The incident document says outright "there is no
   supported way to mark them". Read with E6 -- 71 of the 93 are on a superseded
   frame declared non-comparable on four axes, one of which "moves without
   changing any recorded field" -- **at most 12 of 93 rows are both
   current-frame and undisputed, and I could not identify which.** Every
   downstream census that groups by frame digest is wrong by construction.

3. **D1 + D2 -- THE ARCHIVE PARTITION IS NOT MOUNTED AND IS NOT IN fstab, AND
   THE ONE-COPY-IN-THE-WORLD MANUSCRIPT'S ONLY REMOTE POINTS INTO IT.**
   `nvme1n1p5`, 391 GB ext4, no mountpoint, no fstab entry; `/mnt/protea-archive`
   is an empty root-owned directory from 2026-07-28 17:09. `complexity-paper`
   has exactly one remote, `mirror`, pointing at a bare repo on that partition;
   root CLAUDE.md says "remote created the same day" and FIRST-BOOT says a bare
   local mirror is not a real remote. Everything FIRST-BOOT section 0 lists as
   the recovery surface -- the 28-variable secret file with no template, every
   database dump, the object store snapshot, the archived memory store, and the
   `no-producer-artifacts/` directory holding the seven artifacts of Part A --
   is on that disk. A reboot will never restore the mount.

## The stale-entry hunt (the requester's charge #2), answered

The previous agent's finding is **CONFIRMED**: `compute_information_accretion`
is registered (`operation_catalog.py:33-35,120`, file added 2026-08-17
`7448003`) and the store held one InformationAccretionSet on 2026-08-30, so
GENESIS-STATE's section 1 row and section 2 item 8 are both stale, and so is
section 3F's "Evaluation ... Blocked on the IA artifact".

Running the same test over every entry:

**GENESIS-STATE section 1 (seven artifacts), today:**
| artifact | 2026-07-27 | 2026-09-02 |
|---|---|---|
| `go_text_emb.npz` | no writer anywhere | **STILL TRUE**, and the file is gone from disk too (A1) |
| `IA.tsv` | CLI only, not an operation | **CLOSED** 2026-08-17, and it ran (A2) |
| `classifier_m2_anc2vec.pt` | no script saves it | **STILL TRUE**, plus the loader is pinned to `/home/frapercan/...` (A3) |
| `anc2vec_2020-10.npz` | no fetch step | **STILL TRUE** (A4) |
| InterProScan 5.77-108.0 | no installer | **STILL TRUE**, and `interpro_go_mapping` is EMPTY so the whole arm is dead (A5, B5) |
| `predictions_protea.tsv` | nothing to write | unchanged, it is an output |
| the 8 `EmbeddingConfig` UUIDs | no seed migration | **CLOSED** 2026-08-17, three seed migrations -- but the roster is now 12 or 13 spaces, not 8 (A7, B3) |

**GENESIS-STATE section 2 (ten capabilities), today:** 4 closed (1 stratification,
2 window registry, 5 paired bootstrap, 6 row alignment) + item 8 (IA); 4 still
open (3 control family, 7 board recipe fixture, 9 end-to-end orchestration,
10 registry-to-UI test); 1 partial (4 cross-fit gate). Full table in Part C.
**Items 1, 2 and 6 were closed by code committed 2026-07-28 between 03:49 and
03:59 UTC -- BEFORE GENESIS-STATE's own last commit at 08:54:57 UTC the same
day -- and section 6 of the document describes those very closures while section
2 above still lists them as missing. The document has contradicted itself since
the day it was written, and has had no commit since.**

**Section 3 spot-checks:** `bootstrap-fresh-machine.sh` orphan status unverified;
the two divergent `cold-boot.sh` copies are CONFIRMED with zero distinctive-flag
overlap (F2); the deploy slot exists but the "thirteen scripts" count is 12 live
+ 2 archived by my sweep (F4); the five crontab entries are NOT installed (G1).

## Deductions counted as measurements, and retractions not propagated

- **A7b** -- ESM-2 150M's exclusion from the canonical rung-1 grid cites
  CAMPAIGN.md §5 while the migration's own docstring says "The supporting
  measurement could not be located". Three of four exclusions in that docstring
  carry numbers; this one carries a citation to prose. The single cleanest
  deduction-as-measurement in my slice.
- **B1** -- the NOT-propagation "under half" / 2.5x figure in
  `docs/findings/2026-08-30-what-a-curated-not-was-telling-us.md` is the figure
  COLLIDING-A-NUMBER.md (2026-09-01) records as retracted; the real effect is
  465->527 denials, **+13%**. The repo document was never amended and the
  retraction never names it.
- **E5** -- "the magnitude figure of 20.70 to 12.13 that circulated" is retracted
  in `docs/incidents/2026-08-29-prediction-set-a789582e.md`; the corrected
  comparison is NK 14.46->12.53 and PK 9.59->10.78, "where the sign reverses. Do
  not reuse that trio." I found neither number in the plan store or memory, so
  it circulated somewhere I cannot see.
- **F3** -- "**+40% reranked**" is echoed in SEVEN documents. The only concrete
  pair published beside it (NK MFO 0.507 vs 0.398) is **+27.4%**, its primary
  receipt (`project_validation_findings_2026_06_25`) is NOT among the 210 memory
  files and is on the unmounted archive, the comparison is KNN-only vs
  mean+reranker so two axes move at once, and it is dated 2026-06-25, i.e.
  pre-reinstall AND pre-wipe.
- **E7 note2** -- the five-encoder table under "encoder choice is a step, not a
  gradient" carries its own "has not been recomputed" warning and is a 400-pair
  sample on a superseded split, while the conclusion it supports is filed under
  "Survives".

## Arithmetic that does not close (found by doing it)

- **B3** -- "6,867,762 sequence embeddings across 12 spaces, every space covering
  all 528,294". 12 x 528,294 = 6,339,528; 13 x 528,294 = 6,867,822, sixty MORE
  than the stated total. Thirteen spaces with one 60 short, or twelve that do
  not all cover.
- **B4** -- "a held-out true term costs **762 times** less than a random one"
  against its own table's chance median rank of 20,107 and observed 53:
  20,107/53 = **379**. 40,214/53 = 759, so the prose divided by the vocabulary
  size rather than by its own chance baseline.
- **E7** -- four denominators for one measurement: 56,816 (new pairs), 54,440
  (implied "term in bank"), 53,605 (the published signal table's reached+missed),
  53,680 (the producing script's own docstring). None reconciled.
- What DOES close, checked and passing: the `a789582e` evidence-code breakdown
  sums to 1,523,939 exactly and 1,523,939/2,801,404 = 54.4%; ISO+ISS = 366,997
  exactly; the ceiling decomposition 44,273+2,376+10,167 = 56,816 exactly;
  P+F+C = 26,037+10,154+4,023 = 40,214 exactly.

## Platform gaps my slice adds to GENESIS-STATE's list

1. **A way to retract or supersede a sealed `evaluation_result`.** `seal_evaluation_frames`
   seals and nothing un-seals or annotates. This is why E1 is unfixable today.
2. **`audit_prediction_set`** -- the `a789582e` census is three hand-written SQL
   queries pasted into a markdown file.
3. **`audit_denial_violations`** -- the NOT-violation counts have no producer;
   only the FIX (`_denials.py`) is in the platform.
4. **`report_store_inventory`** -- the 2026-08-30 corpus inventory was typed by
   hand and does not add up (B3).
5. **The registry-to-UI coverage test** (GENESIS-STATE item 10). It is three
   lines and would currently fail 30 of 39 ways.
6. **A `no-absolute-home-paths` lint.** Twelve sites, three different home
   directories, two of which do not exist on this machine (E8).
7. **`scripts/analysis/` (five files, created 2026-09-01) is a brand-new
   unversioned analysis surface** producing the ceiling numbers from `/tmp` CSVs
   and a hardcoded laptop path -- a fresh instance of the exact defect
   GENESIS-STATE exists to close, created five weeks after it.

## What was lost, precisely

- `project_validation_findings_2026_06_25`, the receipt for the +40% headline:
  archived 2026-07-27, on the unmounted partition.
- The receipt for "8.8x further from the reference" (A2b): only the docstring.
- The receipt for "the reranker sits at AUC 0.491 in PK-BPO against 0.6263"
  (B2): asserted with no artifact in the repository.
- The receipt for ESM-2 150M's exclusion (A7b): sought by the implementer, not
  found, and the exclusion applied anyway.
- 23 of 25 files of branch `feat/subsumption-is-containment-in-a-sparse-code`
  (tip `222b4a3`), reachable only through a ref deliberately not deleted.
- Everything under `/mnt/protea-archive/archive/`: the secret surface, every
  database dump, the object store snapshot, the archived memory (144 files
  across two directories), and `no-producer-artifacts/`.
