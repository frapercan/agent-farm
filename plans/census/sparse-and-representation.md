# Census slice: sparse-and-representation

Auditor slice key: `sparse-and-representation`
Started: 2026-09-02

## Slice description
- `plans/sparse-classifier/`
- `plans/representation-science/`
- `plans/LEARNED-REPRESENTATION-ABLATION.md` (reported UNTRACKED in git -- verify)
- `plans/ABLATION-ARCHITECTURE.md` (reported UNTRACKED in git -- verify)
- The two-tower classifier, the learned k-WTA encoder, the encoder study.
- Separate PLATFORM-measured from LAB-measured (out-of-platform work does not count).
- Inventory `storage/encoder-study/` and `storage/encoder/`.

Decision dates: 2026-07-28 OS reinstall; **2026-08-27 experiment registry WIPED**.
Anything measured before 2026-08-27 is not evidence about the current window.

---
## F1. `plans/LEARNED-REPRESENTATION-ABLATION.md` and `plans/ABLATION-ARCHITECTURE.md` are UNTRACKED in git
verdict: CONFIRMED
first number: n/a (structural finding)
second number: `git status --porcelain plans/` in /home/xaxi/Thesis2/agent-farm returns exactly two entries:
  `?? plans/ABLATION-ARCHITECTURE.md`, `?? plans/LEARNED-REPRESENTATION-ABLATION.md`.
  `git ls-files --error-unmatch` fails for both; succeeds for SDR-PROGRAM.md and COLLIDING-A-NUMBER.md.
  These are the ONLY two untracked files in the whole canonical plan store.
date of evidence: 2026-09-02 -> window: post-wipe-current (the untracked state is current)
frame: n/a
population: n/a
platform gap: MURO -- git tracking is not an operation. But the consequence is operational:
  CLAUDE.md says "Assistant memory does not cross machines... If both machines must agree on
  something, commit it to a repository instead." These two documents are therefore INVISIBLE to
  the laptop/server and to any agent that clones agent-farm. The two ablation programmes that
  define the learned-representation science are the two documents not in the repository.
note: everything these two files assert is, by the project's own rule, uncommitted and
  machine-local. If this disk is reinstalled again they die exactly the way storage/ was
  supposed to die on 2026-07-28.

## F2. Both tracked plan directories in this slice are FROZEN PRE-REINSTALL; nothing in them was re-measured after the wipe
verdict: CONFIRMED
first number: `plans/representation-science/PLAN.md` header "born from the 2026-06-25 session";
  every RESULTS line in it is stamped 2026-06-25 (MLflow exp 30 / exp 31).
  `plans/sparse-classifier/RESULTS.md` line 1: "overnight results (2026-06-28)".
second number: filesystem mtimes are all `Jul 28 17:01` for both directories -- i.e. the
  reinstall-day restore timestamp, not an edit. Content dates 2026-06-25 and 2026-06-28.
  No file in either directory has been touched since.
date of evidence: 2026-06-25 / 2026-06-28 -> window: **pre-reinstall-lost** (both precede the
  2026-07-28 reinstall AND the 2026-08-27 registry wipe by two months)
frame: representation-science: LAFA FINAL_227_230 then eval_set `6e41eb5b` (built by
  experiment A, pivot 2025-07-22, delta 7575), metric f_micro_w, cafaeval -prop fill -norm cafa
  -no_orphans -toi, PK -known. sparse-classifier: recall@100 over 227->230 NEW terms, no cafaeval.
population: nine cells NK/LK/PK x MFO/BPO/CCO; delta 7575 proteins on the A frame.
platform gap: the MLflow experiments 30 and 31 that hold these results are NOT the experiment
  registry that was wiped, and are not in `storage/`. Search below.
note: every headline in this slice's TRACKED plan store is from a frame that no longer exists in
  the live database. The two documents that ARE from the current-ish window (2026-08-17) are
  precisely the two that are untracked (F1).

## F3. The "+40%" / "learned encoder" headline: the ONE measured quantity is a HELD-OUT TRAINING LOSS, and it was produced by a DIFFERENT harness from the one that carries its name
verdict: CONFIRMED (by the project's own untracked audit; I re-verified the source split below)
first number: `plans/representation-science/PLAN.md` line ~5 and `plans/sparse-classifier/PLAN.md`
  line ~5: "learned k-WTA encoder beat dense mean-pool +40%"; PLAN.md RESULTS:
  "The +40% lever is real on f_micro_w, not just proxy."
second number: `plans/LEARNED-REPRESENTATION-ABLATION.md` sec.1 (untracked, 2026-08-17) states the
  whole of the previous result as: held-out Spearman vs IC-weighted Lin **+0.168 -> +0.530**,
  and top-128 selection gives back 0.063 to land at **+0.467**; 4,000 held-out proteins, ~120,000
  pairs, on mean-pooled **esm2_150m** (640->2048 affine, MSE on code cosine vs Lin).
  Three independent corrections in that same section:
   (a) "Spearman against Lin is the training objective... That is held-out training loss, and only
       one arm family was ever given the target. `dense` and `pca256` were not."
   (b) "those three numbers do not come from `encoder_ablation.py` at all: that module computes no
       correlation and its only readout is `f_micro_w`. They come from
       `scripts/run_sdr_c_contrastive.py`, a different harness with a different split. The method
       card and the ablation module are two experiments wearing one name."
   (c) the 0.063 is NOT the cost of sparsity: the loss is computed on the dense projection
       `z = enc(Rt)` (lines 225-235) and `topk_real` appears only in `apply_encoder` (line 248),
       so the encoder is never trained through the selection. **"The 0.063 is the price of a
       train-and-apply mismatch, and it has never been a measurement of sparsity."**
date of evidence: original run pre-2026-06-25; audit 2026-08-17 -> window: **pre-wipe** for the
  audit, **pre-reinstall-lost** for the run.
frame: Spearman vs IC-weighted Lin over propagated GO closures; NOT cafaeval, NOT f_micro_w,
  NOT Fmax, no aspect filter, no NK/LK/PK split. `_max_common_ancestor_ic` applies no aspect
  filter -> supervision is probably MFO-dominated (the doc's O2 arm exists to test this and
  has not run).
population: 4,000 proteins outside the training pool, ~120,000 pairs. NOT nine cells.
  Substrate is esm2_150m, "the smallest model in the grid, chosen because it was smallest",
  while prot_t5 (0.3414) and ankh_large (0.3346) lead at K=3.
platform gap: the correlation harness `scripts/run_sdr_c_contrastive.py` is a LAB script with no
  registered operation. To be reborn writing to the database it would need an operation that
  computes and persists a held-out rank correlation of a code against an ontology similarity
  target -- no such operation exists (verified against the operation registry, see F8).
note: **"+40%" is a proxy-correlation ratio (0.168 -> 0.530 is +215% relative, +0.362 absolute;
  0.467/0.334 dense-at-K3-equivalent is not the same object either) that was later re-narrated
  as an f_micro_w lever in two tracked PLAN.md files.** The re-narration is the defect: a
  held-out-training-loss correlation became a score claim without the intermediate measurement
  being named. This is COLLIDING-A-NUMBER rule 3 exactly.

## F4. `encoder_ablation.py` cannot report anything on THIS machine, and writes `status: ok` anyway
verdict: CONFIRMED (asserted in the untracked plan; verified in the lab source below)
first number: n/a
second number: LEARNED-REPRESENTATION-ABLATION.md sec.1 final paragraph: "`gt_dir` at line 88 and
  the default Python path both point at `/home/frapercan`, missing since the reinstall, so the
  cafaeval subprocess fails into an error dictionary, every cell metric stays `None`, and
  `run.json` is still written with status ok."
date of evidence: 2026-08-17 -> window: pre-wipe (but the breakage is post-reinstall, so it is
  CURRENT unless the path was fixed)
frame: n/a
population: n/a
platform gap: MURO -- an out-of-platform script whose failure mode is a silent `status: ok`.
note: COLLIDING-A-NUMBER rule 4 in its purest form: a green run over an empty result. Any
  `run.json` from this module dated after 2026-07-28 is presumptively empty. **Check the date
  and the `status` of every encoder-ablation artifact before citing it.**

## F5. INVENTORY: `storage/encoder-study/` -- 131 scripts, 340 artifacts, 16 GB, ZERO of it in any git repository or in the platform
verdict: CONFIRMED
first number: n/a
second number: measured directly.
  - `storage/encoder-study/` 16 GB; `storage/encoder/` 2.6 GB; `storage/probe/` 347 GB (`du -sh`).
  - `ls scripts | wc -l` = **131**; `ls artifacts | wc -l` = **340**.
  - `git -C storage/encoder-study rev-parse --show-toplevel` -> NOT IN ANY GIT REPO. Same for
    `storage/encoder/` and `storage/probe/`.
  - Script window: oldest `01_prepare.py` **2026-08-19 00:16**, newest
    `115_panel_populations_experimental_baseline.py` **2026-08-26 21:53**.
  - Artifact window: oldest `gold_lafa.pkl` **2026-08-19 00:16**, newest `114_cross.json`
    **2026-08-26 16:49**.
  - Five design/result documents, all untracked, all inside `storage/`:
    RESULTS.md (281 lines, 2026-08-23), RUNG2-ENCODING-ABLATION.md (328, 2026-08-20),
    PRODUCTION.md (490, 2026-08-23), CAMPAIGN-LADDER.md (143, 2026-08-19),
    DEPLOYMENT-AUDIT.md (130, 2026-08-19).
date of evidence: 2026-08-19 to 2026-08-26 -> window: **pre-wipe by ONE DAY**. The last artifact
  is 2026-08-26 16:49; the registry was wiped 2026-08-27. **The entire encoder study is the
  eight days immediately before the wipe, and none of it is in the registry.**
frame: varies per script; see per-claim entries below.
population: varies; the panels are 9-cell, several scripts are on a 60k pool + LAFA split.
platform gap: **131 scripts is an entire research programme executed outside the platform.**
  Per CAMPAIGN.md 0bis and `feedback_integrate_in_platform_not_adhoc`, none of it counts and
  none of it survives this disk. `scripts/94_convert_controls_to_platform.py` and
  `105_publish_bundle_to_store.py` / `108_publish_two_tower_go_side.py` are the only three
  filenames that even gesture at the platform -- 3 of 131.
note: this is the single largest body of representation science in the project and it is
  simultaneously (a) the most recent, (b) entirely out-of-platform, (c) entirely untracked, and
  (d) stopped dead one day before the registry wipe. `storage/` was declared "deliberately not
  restored"; 16 GB of encoder study plus 347 GB of per-residue banks say otherwise.

## F6. The encoder study's own headline table was SUPERSEDED and RETRACTED inside its own file, twice, and the retraction is only in an untracked storage/ file
verdict: CONFIRMED
first number: `storage/encoder-study/RESULTS.md` "Every arm" table (44 arms, purity on 2,646
  held-out proteins): `residue-k4` 0.2570, **+0.0287 vs deployed**, "separates"; the axis
  summary row "order: sparsify per residue, against pooled at equal training +0.0358
  [+0.0336, +0.0381] separates".
second number: same file, section "**Superseded 2026-08-20: the order does not survive a real
  bank**". On the full cell, 3,031 queries against 85,982 donors with first-hand evidence at
  window start, twins excluded:
    budget 10: dense 0.6029 (+0.0012) / pooled 0.6009 (-0.0008) / residue 0.6017 (ref)
    budget 25: dense 0.6301 (+0.0048) / pooled 0.6307 (+0.0054) / residue 0.6253
    budget 50: dense 0.6808 (+0.0027) / pooled 0.6799 (+0.0018) / residue 0.6781
  "Nine aggregate comparisons and twenty-four by identity band, and not one separates."
  Largest difference anywhere +0.0138 [-0.001, +0.028].
  And the power argument, which is the part that matters:
    order of selection and pooling, twilight spread = **0.0006**
    choice of base protein language model, twilight spread = **0.0842**
  "Two orders of magnitude, one metric, one population."
  Then a SECOND retraction, 2026-08-23: "the best backbone had read the answer" -- ProtST is
  pretrained on ProtDescribe (sequence + Swiss-Prot function text). 9 of 9 paired intervals
  exclude zero among the 2,468 DESCRIBED proteins; **0 of 9 among the 547 UNDESCRIBED**, and it
  inverts against the two strongest rivals. Twilight backbone spread falls 0.0842 -> **0.0625**.
date of evidence: table 2026-08-19/23; supersession 2026-08-20; retraction 2026-08-23
  -> window: **pre-wipe** (all within the 8-day out-of-platform study)
frame: TWO DIFFERENT FRAMES, and that is the finding. The 44-arm table is **purity** = mean
  functional similarity to the 10 nearest neighbours over is_a/part_of-propagated GO closures,
  on a probe-shaped bank of pool proteins. The supersession is **reachability at a candidate
  budget** (10/25/50) against a real 85,982-donor bank, release-220 donor closures. Neither is
  Fmax, neither is f_micro_w, neither passed through cafaeval.
population: table = 2,646 held-out delta proteins (mixed categories; see residue-verdict.md F7:
  82.5% prior knowledge, 140 NK). Supersession = 3,031 NO-KNOWLEDGE queries -- a DIFFERENT
  population, which is the served one.
platform gap: MURO for the purity screen (no operation computes neighbour-closure purity).
  The reachability form is closer to `score_knn_transfer` but the study ran it in numpy from
  `scripts/89_arms_retrieval_by_band.py`.
note: the 44-arm table is still the most quotable object in the study and it sits ABOVE its own
  supersession in the same file. Anyone reading top-down cites `+0.0287` and stops. The two
  numbers that must travel together are **0.0006 (the axis the study was built on) and 0.0625
  (the axis nobody was funding)**. Cross-reference the sibling audit
  `/home/xaxi/Thesis2/storage/coordination/census/residue-verdict.md` for the full autopsy of
  the +0.0251/+0.0287 purity claim (its F4: "the entire gain is the denominator").

## F7. THE PLATFORM/LAB SPLIT, resolved. The residue encoder IS a platform operation and its five blocking gaps WERE closed; the two-tower classifier is a platform class that has NOT been touched since 2026-06-29 and is OFF by default
verdict: CONFIRMED
first number: `storage/encoder-study/RUNG2-ENCODING-ABLATION.md` sec.4, written 2026-08-19/20:
  "Five gaps, all in the merged operation, none of them found by its tests... **It cannot run in
  this topology at all.** The operation does its work inline in the process that consumes the
  operations queue. That process is on the server, which has no card."
second number: `git log` in `/home/xaxi/Thesis2/worktrees/protea-deploy` (HEAD a5de702, PR #920)
  shows every one of the five closed within 48 hours of that sentence:
    #828 2026-08-20 "the store address actually resolves"        -> gap 4 (artifact by identity)
    #831 2026-08-20 "a batch resumes after a partial commit"
    #832 2026-08-20 "the batch halves when the card refuses it"  -> gap 2 (device)
    #833 2026-08-20 "the pooled encoder takes a store address too"
    #834 2026-08-20 "a worker learns its batch size once"        -> new file
                       `protea/core/operations/_encode_residue_sparse_batch.py` = gap 1, the
                       fan-out to `protea.embeddings.batch`
    #835 2026-08-20 "a fitted encoder records the release it was fitted against"
    #838 2026-08-20 "a batch is a budget of residues, not a count of sequences"
    #840/#841 2026-08-21 oversized protein, EXISTS scoping
    #827 2026-08-20 + #863 2026-08-23 "the pooled encoder declares its order too, so the fence
                       has both sides" / "the order guard says how to find the answer"
                       -> gap 5, the contract hole
  So the RUNG2 document's blocking section is STALE and the operation is dispatchable.
  BY CONTRAST: `protea/core/two_tower_classifier.py` has exactly TWO commits in its whole life,
  **b4a9251 2026-06-28 (#690) and 45afbca 2026-06-29 (#692)**, and nothing since. It is gated on
  `PROTEA_CLASSIFIER_IMPL=two_tower_sparse`; `classifier_producer.py:93` says
  "The default (unset / `m2`) keeps the production M2 `hybrid_anc2vec` head".
date of evidence: 2026-08-20/21/23 (encoder), 2026-06-28/29 (classifier) -> windows:
  encoder = pre-wipe by days; classifier = **pre-reinstall-lost**
frame: n/a (code, not measurement)
population: n/a
platform gap: **the residue encoder has NO platform gap left; the two-tower classifier is
  entirely un-run in the current window.** The classifier's serving artifacts were staged at
  `storage/two_tower_sparse/` (vocab_go.npy) plus "7 head ckpts + go_sparse_codes in the lab"
  per sparse-classifier/RESULTS.md P5 -- see F9 for whether they exist.
note: the standing instruction "out-of-platform work does not count" bites ASYMMETRICALLY here.
  The residue/k-WTA encoder was productised (10+ PRs in 4 days) and the science that justified
  it was retracted (F6). The two-tower classifier's science (recall ceiling +0.068 on PK-BPO)
  was never retracted and was never productised past a draft-merged opt-in that nobody turned on.
  **The project shipped the arm whose result died and shelved the arm whose result stood.**

## F8. THE TWO-TOWER SPARSE CLASSIFIER: every artifact and every receipt is GONE. Only the scripts survived, in git.
verdict: CONFIRMED (negative check, and I state where I looked)
first number: `plans/sparse-classifier/PLAN.md` "Artifacts (durable, survive reboot -- NOT /tmp).
  All under `~/Thesis2/repositories/protea-reranker-lab/results/sparse_classifier/`:
  go_text_emb.npz, go_cooc_svd.npz, go_sparse_codes.npz, booster/encoder ckpts, smoke logs,
  comparison_9cell.json, SUMMARY.md."
  `plans/sparse-classifier/RESULTS.md` P5: "Serve artifacts staged durable (vocab_go.npy in
  storage/two_tower_sparse; 7 head ckpts + go_sparse_codes in the lab)."
second number: I looked in all five places the artifacts would be if they existed:
  1. `/home/xaxi/Thesis2/repositories/protea-reranker-lab/results/sparse_classifier/`
     -> `find . -type f | wc -l` = **85 files: 84 `.py` and 1 `.md`**. Extension histogram
     contains NO npz, NO npy, NO pkl, NO json, NO pt, NO ckpt, NO log. The single non-.py file
     is `percut_rerank/SUMMARY.md`. `p2/` (the two-tower trainer, `two_tower.py`) and `p2b/`
     hold four scripts each and nothing else. All mtimes 2026-07-29 01:48 = the restore.
  2. `/home/xaxi/Thesis2/storage/two_tower_sparse/` -> **does not exist**.
  3. `/home/xaxi/Thesis2/storage/fullgo_models/` -> **does not exist** (the anc2vec npz, the
     per_residue_v227 dir and the artifact map that representation-science/PLAN.md calls
     "existing assets to REUSE" all lived there).
  4. `find /home/xaxi -maxdepth 8` for `go_sparse_codes*`, `go_text_emb*`, `vocab_go*`,
     `anc2vec*` -> only SOURCE FILES (`protea_method/anc2vec.py`, `anc2vec_embeddings.py`
     across worktrees). No data file of any of those names anywhere under /home/xaxi.
  5. `find` for `*two_tower*` across storage/ and the lab -> three hits, all `.py`:
     `encoder-study/scripts/107_two_tower_atom_correspondence.py`,
     `encoder-study/scripts/108_publish_two_tower_go_side.py`,
     `reranker-lab/results/sparse_classifier/p2/two_tower.py`.
  The check could have failed: `storage/encoder-study/artifacts/` holds 340 files including a
  1.6 GB npz, and `storage/probe/` holds 347 GB, so this filesystem demonstrably keeps large
  lab artifacts. It kept none of the two-tower's.
date of evidence: results 2026-06-28 -> window: **pre-reinstall-lost**
frame: recall@100 of TRUE 227->230 NEW terms (a RETRIEVAL/CANDIDATE metric, not Fmax, not
  f_micro_w, no cafaeval, no -known exclusion, no propagation norm named). P4 is a recall
  CEILING over the union of a candidate pool -- an ORACLE quantity, not an achieved score.
population: nine cells; counts never published (the RESULTS.md gives only rates).
platform gap: the producers exist as lab scripts only. To be reborn writing to the database the
  project needs: `build_go_text_embeddings`, `build_go_cooccurrence` (this one EXISTS per
  sparse-classifier/PLAN.md B step 1: "`build_go_cooccurrence` for v225 ... On `protea.jobs`"),
  `build_go_sparse_codes` and `train_two_tower_head`. Three of four have no operation.
note: **the numbers in `plans/sparse-classifier/RESULTS.md` are now unfalsifiable.** No artifact,
  no receipt, no log, no `comparison_9cell.json`, and the frame that produced them (release 227
  as t0, 227->230 as the eval) is not the campaign's official 220->230 frame. RESULTS.md is
  nonetheless a TRACKED file in the canonical plan store, so it reads as current record.

## F8bis. CORRECTION to F8: the GO side WAS recovered on 2026-08-24 and published to the object store on 2026-08-26. The seven HEADS were NOT published, and `prep.npz` has no producer, so the two-tower CANNOT be retrained.
verdict: CONFIRMED
first number: F8's negative check (nothing on this disk) stands and is not wrong -- the artifacts
  are not on this disk.
second number: `storage/encoder-study/artifacts/108_published.json` (2026-08-26 00:29):
  prefix `two_tower/go-side-2026-06-29`, TWO objects only:
    `go_sparse_codes.npz` 165,052,242 bytes sha256 731c86c2...
    `vocab_go.npy`        1,161,208 bytes  sha256 9a1117de...
  shapes: vocab_go [29027], go_ids [39906], codes [39906, 1024].
  provenance field, verbatim: "recovered 2026-08-24 from the preserve partition taken
  2026-07-27/28 before the reinstall, at
  `archive/preformat-preserve-2026-07-27_preformat/two_tower_sparse/`, file dates 2026-06-28 and
  2026-06-29. **NOT rederivable: no script on disk builds them and the machine that produced
  them was formatted.**"
  consumed_by field: "results/sparse_classifier/p2/two_tower.py and generate.py, via **prep.npz,
  which is MISSING and has no builder**."
  And `scripts/108_publish_two_tower_go_side.py` docstring: "six scripts consume it, none writes
  it. That is the artifact-without-a-producer the campaign's own invariant forbids."
  THE HEADS ARE NOT IN THE PUBLISHED SET. `FILES = ["go_sparse_codes.npz", "vocab_go.npy"]`.
  The seven `heads/head_seed*.pt` are read by script 107 straight off
  `/mnt/protea-archive/...` and were never uploaded.
third check (mine, 2026-09-02): **`/mnt/protea-archive` is an EMPTY, UNMOUNTED mount point.**
  `df -h /mnt/protea-archive` reports `/dev/nvme0n1p2` (the root filesystem), `ls -la` shows two
  entries owned by root dated Jul 28 17:09, and `mount | grep -i archive` is empty.
  So the only surviving copy of the seven trained heads is on a partition that is not mounted.
date of evidence: 2026-08-24 recovery, 2026-08-26 publish -> window: **pre-wipe by 1-3 days**
frame: n/a
population: n/a
platform gap: `build_prep` / `build_go_sparse_codes` -- **the artifact-without-a-producer that
  CAMPAIGN.md section 0bis exists to forbid, caught red-handed.** The publish script says so in
  its own first paragraph. Two of the four pieces prep.npz needs "are not derivable at all".
note: this is the cleanest instance in the project of the invariant being violated and then
  documented. The GO side is now server-side and addressable; the PROTEIN side (the seven heads)
  is one unmounted partition away from total loss, and nothing can rebuild either.

## F9. The ONLY independent test of the two-tower ever run: it misses its own pre-declared threshold by 32x
verdict: CONFIRMED, and the pre-declaration is genuine
first number: `plans/sparse-classifier/RESULTS.md` P2/P3: temporal **recall@100** of true
  227->230 new terms, 554K-curated arm: NK 0.678, LK 0.716, PK 0.376 (vs 88K-experimental
  0.652 / 0.705 / 0.384), "BEATS in 7/9 cells".
second number: `storage/encoder-study/artifacts/107_atoms.json` (2026-08-26 00:22):
    proteins 2000, vocab 29027, heads 7
    mean_rank_real      **9378.48**  CI [9159.98, 9604.16]
    mean_rank_shuffled  14917.64     CI [14744.54, 15094.92]
    declared_threshold  **290**  (= 1 per cent of 29,027)
    separates_from_null true
    verdict "NO SIRVE sin reentrenar"  ["does not serve without retraining"]
  The threshold is genuinely PRE-DECLARED: `scripts/107_two_tower_atom_correspondence.py`
  docstring says "DECLARED BEFORE LOOKING, because deciding a threshold afterwards is choosing
  the definition that gives the answer we want", and it names the null as a PAIRED SHUFFLED
  control -- "That measures chance on this instrument instead of reasoning about 29,027."
  The scoring is read out of the platform, not reconstructed: "`two_tower_classifier.py:30`:
  score = temp * <proj(protein_code), go_code[term]> + bias[term], averaged over the seven seeds".
date of evidence: 2026-08-26 -> window: **pre-wipe by ONE DAY** (the most recent measurement in
  this whole slice)
frame: rank of a protein's TRUE terms among all 29,027 vocabulary terms, 2,000 proteins,
  protein side = rung-2 POOLED arm `9e7a11d4` (528,294 stored vectors), annotation set
  `ec9f5c2c` (release 227). NOT the original `d8979601` protein tower. **This is the confound
  and the script says so.**
population: 2,000 proteins, categories NOT stratified. No NK/LK/PK split, no aspect split.
  So it is one of the nine-populations violations, and it is on an aggregate.
platform gap: none for the measurement (it reads the platform's own scoring function and the
  platform's own embedding config), but the script opens `create_engine` against the live
  database directly, i.e. it is a lab script reading production.
note: **a mean rank of 9,378 of 29,027 is arithmetically incompatible with a recall@100 of 0.678,
  and the two numbers are 60 days apart with no receipt in between.** They are NOT a clean
  collision, because 107 pairs the heads with a DIFFERENT protein tower than the one they were
  trained on, which is exactly what the "signal is real, correspondence is not" verdict means.
  But the asymmetry to notice is this: the 0.678 is TRACKED in the canonical plan store with no
  surviving receipt, and the 9,378 is UNTRACKED in `storage/` with its full receipt, its
  pre-declared threshold and its paired null. **The weaker-evidenced number is the one in the
  plan store.**

## F10. THE K=3 "seven of eight": corrected once in an untracked file, and MY recount makes it six of eight -- but the whole argument rests on a field that is NOT a population
verdict: CONTRADICTED (three ways, in sequence)
first number: `plans/LEARNED-REPRESENTATION-ABLATION.md` sec.2 (untracked, 2026-08-17 09:19),
  used to FIX K=3 as the scoring constant of the entire plan: "the K ablation has since shown
  [K=30] is the worst available setting: that axis closed at **24 of 24**, **K=3 wins in seven
  of eight models**, and the decay is monotone in seven of eight."
second number: `plans/ABLATION-ARCHITECTURE.md` preamble (untracked, 2026-08-17 **09:27**, i.e.
  EIGHT MINUTES LATER, same author, same morning): "the honest statement is that **K equals 3
  wins in five of eight models on a matched cohort and is untested in three**, and the 'seven of
  eight' figure compares arms scored on different populations under the same column heading."
third number (MINE, recomputed from the raw artefact with python3/csv, no numpy):
  `agent-farm/plans/farm-platform/artefacts/knn_226_227_fmicrow.csv`, 216 data rows,
  status: 215 ok + 1 `no_positives`. Summing `n_proteins` over the 9 cells per (model, K):

    model         K=3            K=5            K=10
    ankh_base     5674           2238           5674
    ankh_large    1472 (8 cells) 5674           5674
    esm2_150m     5674           5674           5674
    esm2_3b       5674           5674           5674
    esm2_650m     5674           5674           5674
    esmc_600m     2238           2238           5674
    prostt5       2238           5674           5674
    prot_t5       5674           5674           5674

  Matched-sum K=3 comparisons and their outcome (mean f_micro_w over the 9 cells):
    esm2_150m  k3 0.4818 > k5 0.4668 (9/9 cells) and > k10 0.4425 (9/9)
    esm2_3b    k3 0.4711 > k5 0.4489 (9/9)       and > k10 0.4140 (9/9)
    esm2_650m  k3 0.4807 > k5 0.4641 (9/9)       and > k10 0.4385 (9/9)
    prot_t5    k3 0.4898 > k5 0.4710 (9/9)       and > k10 0.4518 (9/9)
    ankh_base  k3 0.4801 > k10 0.4472 (9/9)   [k5 sits on a different sum]
    esmc_600m  k3 0.3480 > k5 0.3327 (8/9)    [k10 sits on a different sum]  <-- MISSED
    ankh_large  no matched K=3 comparison exists
    prostt5     no matched K=3 comparison exists
  So the correct count is **SIX of eight on a matched cohort, untested in TWO**, not five and
  three. ABLATION-ARCHITECTURE.md overlooked the esmc_600m k3-vs-k5 pair, which is matched at
  2,238 on both sides.
FOURTH, and this is the one that matters: **`n_proteins` is not a cohort size at all**, so the
  entire "different populations" argument is built on sand. `project_scorer_absorbs_backbone_axis_2026_08_23.md`,
  written **six days after both plans**: "Per the note in
  `protea/core/operations/_run_cafa_artifacts.py` where the field is persisted, it counts
  proteins carrying a prediction *at the threshold where the metric maximised*, so it moves with
  the operating point as well as with coverage: a single tau step from 0.98 to 0.99 moved it
  **17 per cent** in rung 1 while the scored cohort was **provably identical across all 32
  runs**... **Never call that field a population.**"
date of evidence: CSV 2026-07-28 restore of a 226->227 run; both plans 2026-08-17;
  the refutation of the field 2026-08-23 -> window: **pre-wipe** throughout
frame: **`knn_226_227_fmicrow.csv` is the 226->227 window.** The campaign's official frame is
  220->230. The same memory warns: "Different windows: never print 0.357 beside 0.322 without
  naming both frames, since that 0.035 gap is the window and is fifteen times the backbone
  spread." Metric is f_micro_w (POOLED), not Fmax (per-protein) -- four statistics are called F.
population: 9 cells at ankh_base K=3, which I read off directly and which reproduce
  ABLATION-ARCHITECTURE.md exactly: nk-bpo 354, nk-cco 161, nk-mfo 243; lk-bpo 307, lk-cco 181,
  lk-mfo 180; pk-bpo 2382, pk-cco 809, pk-mfo 1057. Sum 5,674, of which 4,248 (74.9%) is PK.
platform gap: none -- the CSV is a platform artefact. The gap is that the correction never
  reached the plan store, because the two plans are untracked (F1) and were never edited again
  (mtimes still 2026-08-17 09:19 and 09:27).
note: **three layers, and only the innermost is right.** "Seven of eight" was wrong. "Five of
  eight" is closer but undercounts. And the reason given for the correction -- unequal
  populations -- was itself refuted six days later and the refutation never propagated, because
  the document holding it is not in any repository. The DECISION (K=3) survives all three
  layers: K=3 wins every matched comparison that exists, 6 of 6, 53 of 54 cells. But the
  JUSTIFICATION in the plan store is wrong at every level.

## F11. The power spine of `ABLATION-ARCHITECTURE.md` -- the "minimum cell population 129" and the nine-panel MDE table -- is A DEDUCTION FROM ONE REGISTRY LINE, not a measurement
verdict: DEDUCED-NOT-MEASURED
first number: `plans/ABLATION-ARCHITECTURE.md` sec.1: "**The minimum cell population for
  inference is 129 proteins.** I write it as 129 rather than rounding to 150, because a rounded
  floor invites the question of where the rounding came from and a derived one does not." It
  then gates the whole plan: "Below 129 a cell reports a point estimate... and is excluded from
  every difference claim and from the multiplicity family."
second number: the chain, which I reproduced exactly in python3:
  input = ONE line of `SIGNAL-REGISTRY.md:100`, "Prefilter `tau_pre = 0.4`: 10 of 10 disjoint
  folds chose 0.4, **+0.0092 sd 0.0034**". The registry itself (line 233) calls 0.0034 "the
  declared noise floor".
  step 1: assume 0.0034 is the sd of a FOLD-LEVEL MEAN difference, and that a fold is a tenth
          of the cohort -> sigma_d = 0.0034 * sqrt(5674/10) = 0.0034 * 23.8202 = **0.0810**
  step 2: n = (1.96 + 0.8416)^2 * sigma_d^2 / 0.02^2 = 7.849 * 0.006561 / 0.0004 = **128.7**
  step 3: MDE per panel = 2.8016 * 0.081 / sqrt(n). I recomputed all nine and they reproduce the
          published table to the last digit (pk-bpo 0.0046 vs published 0.0047, rounding).
  So the arithmetic is right. What is not a measurement is EVERY INPUT:
   (a) 0.0034 is a between-fold sd from a DIFFERENT study (a prefilter threshold), and the
       document says so: "sigma_d is a property of a contrast class, not a constant. The 0.081
       above comes from two arms that share their retrieval entirely and differ only in a
       prefilter threshold, so it is the low end." It then names the real measurement as a
       future deliverable: "Measuring sigma_d per contrast class is therefore the first
       deliverable of the census in section 4, and it is free". **It was never run** -- there is
       no census artifact anywhere in `plans/` or `storage/`.
   (b) the divisor 5674/10 = 567.4 is the count of protein-ASPECT UNITS, while the document's
       own rule three paragraphs earlier is "**Every bootstrap in this plan resamples proteins,
       not units**". On its own protein count of 6,216 the fold is 621.6, sigma_d is 0.0848 and
       the floor is **141, not 129**. The document derives its floor with the very quantity it
       forbids.
   (c) 5,674 is a sum of `n_proteins`, which per
       `project_scorer_absorbs_backbone_axis_2026_08_23.md` "is **not a cohort size**... Never
       call that field a population."
  The document even prices the fragility itself: "at sigma_d equal to 0.13 the floor is ... 332,
  and **six of the nine mandatory panels fall below it**."
date of evidence: 2026-08-17 -> window: pre-wipe. The 2026-08-23 refutation of the n_proteins
  field postdates it and never reached it (untracked, never re-edited).
frame: 226->227 window, f_micro_w, K=3, from `knn_226_227_fmicrow.csv`. The campaign frame is
  220->230.
population: nine panels, n from 161 to 2,382 (see F10).
platform gap: `measure_sigma_d_by_contrast_class` -- the census section 4 calls it free CPU over
  two banks that already exist. No such operation, no such artifact.
note: **this is the single most citable-looking number in the slice and it is a deduction whose
  every input is either from another study, from a forbidden field, or from the unit the
  document's own bootstrap rule excludes.** It is honestly labelled as provisional INSIDE the
  document ("the first deliverable of the census") -- but the sentence that will travel is the
  bolded one, and the document is untracked so the caveat cannot travel with it.

## F12. "the measured eight-model spread at K equals 3" is a FIVE-model spread. The number is right, the label is wrong, and three of the eight canonical backbones are missing.
verdict: CONFIRMED
first number: `plans/ABLATION-ARCHITECTURE.md` sec.1, table column heading: "measured
  **eight-model** spread at K equals 3"; body: "In prior-knowledge BPO the **eight-model** range
  is 0.0046 Fmax points; in prior-knowledge MFO it is 0.0046; in prior-knowledge CCO it is
  0.0082. In limited-knowledge CCO it is 0.0494 and in limited-knowledge BPO 0.0440."
second number: recomputed from the CSV. Spread = max - min of f_micro_w over models, per cell:

    cell      plan says   ALL 8 models   the 5 FULL-cohort models
    pk-bpo    0.0046      0.0284         0.0046
    pk-mfo    0.0046      0.1011         0.0045
    pk-cco    0.0082      0.1480         0.0082
    nk-bpo    0.0311      0.2371         0.0311
    lk-bpo    0.0440      0.2243         0.0440
    nk-mfo    0.0176      0.3137         0.0176
    lk-cco    0.0494      0.3018         0.0494
    lk-mfo    0.0057      0.5523         0.0057
    nk-cco    0.0285      0.2424         0.0285

  Every published value is the FIVE-model spread, to the last digit. The eight-model spread is
  5x to 97x larger. The five are ankh_base, esm2_150m, esm2_3b, esm2_650m, prot_t5.
  **ankh_large, prostt5 and esmc_600m are absent from every cell of that table** -- the three
  whose K=3 rows sit on partial sums (1,472 and 2,238), i.e. the same three that break the K
  comparison in F10.
  The document's own prose is internally inconsistent in adjacent sentences: "restricted to the
  five models whose K equals 3 row was scored on the full cohort. In prior-knowledge BPO the
  eight-model range is 0.0046".
date of evidence: 2026-08-17 -> window: pre-wipe
frame: 226->227, f_micro_w, K=3. Note the table's other column is headed "minimum detectable
  effect" in **Fmax** points while the spread column is **f_micro_w** -- two of the four
  statistics called F, compared directly. COLLIDING-A-NUMBER sec.3 names exactly this: "Four
  statistics are all called F. `fmax` and `fmax_w` average per protein; `f_micro` and
  `f_micro_w` pool."
population: as F10.
platform gap: none; the CSV is a platform artefact and the recount is free.
note: the forecast this table generates ("the model axis will resolve in no-knowledge BPO,
  limited-knowledge BPO, limited-knowledge CCO and no-knowledge CCO...") is stated as
  falsifiable and pre-registered. It is a forecast about EIGHT models made from FIVE, in a
  window that is not the campaign's, in a metric that is not the one in the adjacent column.

## F13. THE SUBSTRATE OF THE HEADLINE RESULT IS ankh-base AT 768 DIMENSIONS, NOT esm2_150m AT 640. The receipt is on disk and it contradicts the plan's own opening sentence.
verdict: CONTRADICTED
first number: `plans/LEARNED-REPRESENTATION-ABLATION.md` sec.1, FIRST SENTENCE OF THE DOCUMENT:
  "On mean-pooled **esm2_150m** vectors, a single affine map from **640** dimensions to 2048,
  fit by mean squared error of the code cosine onto the information-content-weighted Lin
  similarity... raises the held-out Spearman... from +0.168 to +0.530, and keeping the 128
  largest-magnitude coordinates gives back 0.063 to land at +0.467. Measured on 4,000 proteins
  absent from the training pool, over 120,000 pairs."
  Its sec.1 also: "The fit is **1.31 million parameters** against 60,000 references" and sec.3
  "the 1,312,768 being rejected is **640 times 2048 plus 2048**".
  Its sec.2 builds the entire plan on this: "It cannot be defended on substrate. It ran on **the
  smallest model in the grid, chosen because it was smallest**", and the three-rung ladder
  esm2_150m -> esm2_650m -> prot_t5 exists so that "esm2_150m | 640 | **bridge to the existing
  number**".
second number: the receipt, which is on this disk:
  `/home/xaxi/Thesis2/storage/encoder/VALIDATION.json` (and an identical copy at
  `storage/encoder/bundle/VALIDATION.json`), validated_at 2026-08-10T17:46:50Z:
      raw embedding    spearman_vs_lin **0.1675**  cos_mean 0.5515
      encoder dense    spearman_vs_lin **0.5299**  cos_mean 0.1844
      encoder top-128  spearman_vs_lin **0.4671**  cos_mean 0.0862
      holdout_proteins 4000, pairs 120000
  0.5299 - 0.4671 = 0.0628 -> the plan's "gives back 0.063". Every digit matches.
  `/home/xaxi/Thesis2/storage/encoder/MANIFEST.json`, same timestamp
  (trained_at 2026-08-10T17:46:26Z), arm `learned-k128-hardneg`, seed 42, ref_pool 60000,
  epochs 150, train_pairs 300000 -- all of which the plan also states -- declares:
      **"in_dim": 768**
  `/home/xaxi/Thesis2/storage/encoder/EMBEDDING_RECIPE.json`:
      **"model_name": "ElnaggarLab/ankh-base"**, display_name "ankh_base", layer_indices [0],
      pooling mean, max_length 2048, embedding_config_id 0868f1ff-907a-5e4a-9d73-c0f2ed3c2437
  `storage/encoder/bank/BANK.json`: "backbone": "ElnaggarLab/ankh-base", bank_rows 575,503,
  distinct_sequences 487,237 -- the same two counts the plan quotes for its leakage arithmetic.
THIRD, independent, from the weights themselves (no numpy needed):
  `storage/encoder/encoder.pt` is **6,301,669 bytes**.
      768*2048 + 2048 = 1,574,912 params -> 6,299,648 bytes float32 (+2,021 bytes of pickle
      header). MATCHES.
      640*2048 + 2048 = 1,312,768 params -> 5,251,072 bytes float32. Off by 1.05 MB. DOES NOT.
FOURTH, the mechanism, and the plan half-diagnosed it itself:
  `repositories/protea-reranker-lab/src/protea_reranker_lab/encoder_ablation.py:102`
      `embedding_config_id: str = "500a0c59-be09-424d-9d51-b7997629c95a"  # esm2_150m, 640d, smallest`
  `repositories/protea-reranker-lab/scripts/run_sdr_c_contrastive.py:7`
      "Model: z = ReLU(W e) , W: **768** -> D (dictionary)."
  The plan's own paragraph 4 says: "those three numbers do not come from `encoder_ablation.py`
  at all... They come from `scripts/run_sdr_c_contrastive.py`, a different harness with a
  different split. The method card and the ablation module are two experiments wearing one name."
  **That is exactly right, and it is why the numbers are 768-dimensional ankh-base. The plan
  then spends its opening sentence, its parameter count, its substrate ladder and its
  pre-registered interaction contrast reasoning from the OTHER harness's 640-dimensional
  esm2_150m.** It found the confusion and then kept both halves.
date of evidence: artifacts 2026-08-10; plan 2026-08-17 -> window: **pre-wipe**
frame: held-out Spearman against IC-weighted Lin over propagated closures. Annotation set
  `ec9f5c2c` = release 227, published 2025-09-04, ontology `releases/2025-07-22`. **Release 227
  sits INSIDE the official 220->230 window**, which is the leakage
  `project_learned_weights_must_declare_their_cut_2026_08_20` names. A sibling fit at
  `storage/encoder/fitted-226/` declares release 226 / ontology 2025-03-16 and scores
  0.1803 -> 0.5350 -> 0.4729, so the pair also prices the cut: +0.0058 of top-128 Spearman for
  seeing one more release.
population: 4,000 held-out proteins, 120,000 pairs. No category split, no aspect split.
platform gap: none for the artifact (it carries a full manifest, a validation, a recipe and a
  bank census, which is better provenance than anything else in this slice). The gap is that
  no operation produced it.
note: **the single most consequential correction available in this slice.** Everything the
  untracked plan says about substrate -- that the result was defended on the weakest backbone,
  that the interaction contrast between prot_t5 and esm2_150m is the pre-registered test, that
  esm2_150m is "the bridge to the existing number" -- is about a run that did not produce the
  number. The number was produced on ankh_base, which is the project's own settled development
  backbone (`project_backbone_choice_2026_06_25`). There is no bridge to build.

## F4-UPDATE. The silent `status: ok` was FIXED, on the same day the plan named it, and then the lab repository went silent.
verdict: CONFIRMED (supersedes F4's currency, not its content)
second number: `git log` in `repositories/protea-reranker-lab`:
    6640393 2026-08-17 feat(encoder-ablation): exclude donors by sequence, and separate what is
                       fit from what is retrieved (#119)      <- the plan's separations 1 and 2
    d45f568 2026-08-17 fix(encoder-ablation): make the run report, or stop, instead of
                       completing empty (#118)                <- the plan's step 2
  `git log --since=2026-08-01` returns **exactly these two commits**, and they are the
  repository's HEAD. `host_paths.py:79 ground_truth_dir()` now resolves
  `thesis_root()/CAFA_forever/data/releases/Sep_2025_Mar_2026` with a `PROTEA_LAB_GT_DIR`
  override, i.e. the hardcoded `/home/frapercan` is gone from that path.
  BUT `grep -rn frapercan --include=*.py src/ scripts/` still returns 10 live hits, including
  `scripts/run_sdr_length_stratified.py:80` and `scripts/run_pool_sweep_fmicro.py:35`, both
  `RESDIR = "/home/frapercan/Thesis2/storage/fullgo_models/per_residue_v227"` -- a directory
  that no longer exists on any user (F8, item 3).
date of evidence: 2026-08-17 -> window: pre-wipe
platform gap: n/a
note: **the shape of the whole slice, in two dates.** Steps 2 and 4 of the plan landed in the
  repository on 2026-08-17. Two days later, on 2026-08-19 00:16, the work restarted as
  `storage/encoder-study/`: 131 untracked scripts, 340 untracked artifacts, five untracked
  design documents, outside git and outside the platform, and the lab repository has had no
  commit since. **The programme was designed to be registrable operations
  (`train_functional_encoder`, `apply_functional_encoder`, `score_knn_transfer`,
  `evaluate_stratified`, the clustering) and was executed as a scratch directory.**

## F14. TWO learned encoders wear one name. The receipts belong to the one that is explicitly "NOT the champion".
verdict: CONFIRMED
first number: the tracked plan store speaks of exactly one learned encoder, the champion
  `d8979601`. `plans/sparse-classifier/PLAN.md`: "Reuse the learned champion encoder `d8979601`
  (k-WTA over ankh-base, already ingested as SequenceEmbedding, sparse) as the protein
  representation. NO re-embed". `plans/representation-science/PLAN.md`: "Learned encoder
  VALIDATED on the real f_micro_w frame (LAFA FINAL_227_230): learned-mean (`d8979601`) KNN-only
  BEATS the champion (mean+reranker) in NK/LK by +0.05..+0.13 (NK MFO 0.507 vs 0.398)"; and
  "CHAMPION number = **0.4937** (the 0.5074 was stale)".
second number: `storage/encoder-study/artifacts/106_published.json` (2026-08-23 20:48), the
  bundle actually put on the server, prefix
  `encoders/learned-k128-hardneg-0868f1ff-r227-20260810`, note field verbatim:
    "**NOT the champion d8979601.** Same architecture, fitted 2026-08-10 on embedding config
     0868f1ff at release 227. `encoder.pt` is the trained bytes and **does not declare its
     order, so the platform refuses it**. `encoder-order-stamped.pt` is the same weights with
     order declared, measured against this bundle's own codes, and is the dispatchable one."
  Objects: encoder.pt 6,301,669 B (sha dc77f7cf...), codes_idx.npy and codes_val.npy
  147,328,896 B each, accessions.npy 23,020,248 B, donors.tsv.gz 18,514,118 B, plus the four
  manifests. The stamped variant carries `"order": "pool-then-select"`.
  Cross-check, done by hand-reading the .npy headers of the local copies at
  `storage/encoder/bundle/` (no numpy on this python):
    codes_idx.npy  descr '<u2'  shape (575503, 128)   -> uint16 atom indices
    codes_val.npy  descr '<f2'  shape (575503, 128)   -> float16 values
    accessions.npy descr '<U10' shape (575503,)
  575,503 x 128 x 2 bytes + 128-byte header = 147,328,896 exactly, both files. So the published
  bank IS the full 575,503 bank rows of BANK.json, at 256 bytes per protein, matching the
  "256 bytes per protein for 128 atoms" the ablation plan quotes. (My first pass assumed int32
  and derived 287,752 rows; the header refutes it. Recorded because the wrong number was a
  deduction from an assumed dtype and the header is the measurement.)
where d8979601 is: NOWHERE on this disk as an artifact. `find /home/xaxi -maxdepth 7 -name
  '*d8979601*'` returns only DIRECTORY and SCRIPT names that reference it
  (`results/sparse_classifier/s2e_pure_d8979601/`, `research/cooc_experiment/export_d8979601.py`
  and their worktree copies). It is cited by name in **14 documents** across `agent-farm/plans/`
  (SIGNAL-REGISTRY, bp-structural-lever, thesis-clean-iteration x3, thesis-pillars,
  serve-offline-reconcile, representation-science, text-evidence-scorer, sparse-classifier x2,
  temporal-eval-alignment, productization) and exists as weights in none of them.
  `project_learned_encoder_published_and_order_proven_2026_08_23` says the same: "`d8979601` is
  not on this disk and 391 GB sit unmounted."
date of evidence: 2026-08-10 fit, 2026-08-23 publish -> window: pre-wipe
frame: 0868f1ff = ankh_base, layer [0], mean pooling, max_length 2048, release 227
  (ontology 2025-07-22). d8979601's frame is stated nowhere I found: no manifest, no recipe,
  no validation file exists for it.
population: the 0868f1ff bundle validates on 4,000 held-out proteins (F13). d8979601's
  "+0.05..+0.13 in NK/LK" and "0.4937" have no surviving receipt.
platform gap: none for 0868f1ff -- it is in the object store with digests, an order stamp and a
  full provenance chain, which is the best-provenanced object in this slice.
  **MURO for d8979601**: it is a champion by citation only.
note: **the encoder the thesis argues from and the encoder the receipts describe are different
  objects, and the only one with receipts is labelled "NOT the champion".** Every "+40%",
  "0.4937" and "NK MFO 0.507 vs 0.398" in the tracked plan store attaches to `d8979601`. Every
  Spearman, manifest, bank census and published digest attaches to `0868f1ff`. Do not let a
  reader assume they are one encoder because both are "the learned k-WTA sparse encoder over
  ankh-base".

## F15. Neither slice directory is indexed by `CATALOG.md`, the file whose job is to index the plan store
verdict: CONFIRMED
first number: `plans/CATALOG.md` is the canonical index; it lists ACTIVE plans, an ARCHIVED
  table (lafa-improve, lafa-number-one, reranker-vnext, score-ablation, lafa-levers,
  thesis-cuts), standing threads (executor, thesis-writer, doc-writer, farm-platform,
  bioinfo-quick), reference files, worktrees and open PRs.
second number: `grep -n -i "sparse-classifier\|representation-science\|two-tower\|two_tower\|
  k-WTA\|learned encoder\|learned sparse" CATALOG.md DECISION-LOG.md CAMPAIGN.md` returns
  **ZERO hits in CATALOG.md and ZERO in DECISION-LOG.md**; the only hits are three lines of
  CAMPAIGN.md, and two of those are the terminology table and a rung description.
  So `plans/sparse-classifier/` and `plans/representation-science/` are directories in the
  canonical plan store that the canonical catalog does not know exist -- neither active, nor
  archived, nor superseded.
date of evidence: 2026-09-02 (current state) -> window: post-wipe-current
frame: n/a
population: n/a
platform gap: MURO
note: combined with F1 (the two newest ablation documents untracked) and F5 (131 scripts and
  five design documents in `storage/`), the slice's paper trail is in four tiers of decreasing
  visibility: **CAMPAIGN.md (authoritative, mentions the rung) > two plan directories (tracked
  but unindexed, frozen at 2026-06-25/28) > two ablation plans (untracked, 2026-08-17) >
  131 scripts and five documents (untracked, in storage/, 2026-08-19 to 26)**. Recency and
  visibility run in exactly opposite directions.

## F16. "That question needs a disk before it needs a design" -- and three days later the disk held 277 GB of exactly that. The impossibility was a SCOPING error, and the correcting arithmetic was available when it was written.
verdict: CONTRADICTED
first number: `plans/LEARNED-REPRESENTATION-ABLATION.md` sec.7 (2026-08-17 09:19): "It will not
  answer anything about pooling, chunking or attention over residues. **The deepest observable
  this lab has is one mean-pooled vector per protein per config**; there is no layer column and
  no residue column in the embedding table. Residue retention for esm2_150m alone is 528,294
  sequences by 625 mean residues by 640 dimensions at two bytes, which is **423 gigabytes
  against 568 free, 74 per cent of the disk for one of eight models. That question needs a disk
  before it needs a design.**"
  (I confirm the arithmetic: 528,294 x 625 x 640 x 2 = 422.64 GB.)
second number: `storage/probe/`, dated **2026-08-19 18:38 to 2026-08-20 09:42**, 347 GB, 19 files:
    exp220.npy   276,932,143,232 B   header `{'descr': '<f4', 'shape': (45073591, 2, 768)}`
    nk220.npy      9,115,232,384 B   header `{'descr': '<f4', 'shape': (1483599, 2, 768)}`
    nk_extra.npy     396,192,896 B
    confirmation.npy                 header `{'descr': '<f4', 'shape': (1109436, 1, 768)}`
  I verified both sizes by hand from the headers, no numpy:
    45,073,591 x 2 x 768 x 4 + 128 = 276,932,143,232  -> EXACT
     1,483,599 x 2 x 768 x 4 + 128 =   9,115,232,384  -> EXACT
  `exp220.provenance.json`: population "corpus proteins with experimental evidence at GOA
  release 220", proteins **85,982**, residues **45,073,591**, layers **[10, 48]**,
  chunk_size 1024, chunk_overlap 128, also_evaluation_queries 19,467, and a note that is itself
  a small model of good practice: "fitting a map for MEASUREMENT must exclude the queries,
  fitting one for DEPLOYMENT cannot, since the query set is defined by events after the window
  start".
  `nk220.provenance.json`: "the NK cell of the 220 to 230 frame, proteins with gained terms",
  proteins **3,031**, residues 1,483,599 -- the same 3,031 that carry the supersession in F6.
THE RESOLUTION: the plan priced residue retention over **the whole 528,294-sequence corpus at
  one model**. The study retained residues for **85,982 donors plus 3,031 queries** -- the
  population the question actually needs -- and it cost 277 GB, which fit. At one layer and
  float16 the same extraction is **69 GB**. The deciding arithmetic (corpus versus donor bank)
  needed no new measurement and was available at the moment the sentence was written.
date of evidence: declaration 2026-08-17, refutation 2026-08-19/20 -> window: pre-wipe, and the
  banks are still on this disk today, untouched since 2026-08-20.
frame: ankh-base (768-dim), layers 10 and 48, float32, chunk 1024 / overlap 128, release-220
  donor set, 220->230 frame.
population: 85,982 donors; 3,031 NK queries; 19,467 of the donors are also evaluation queries,
  which is declared rather than discovered.
platform gap: none for the platform -- `encode_residue_sparse` computes residues transiently and
  stores one code per sequence, and the platform's embedding table is 2D by design. The 347 GB
  probe is a LAB object with no operation and no home. It is the largest single artifact in
  `storage/` and it is one `rm -rf` from being unrecoverable, since nothing produces it.
note: **a negative that failed COLLIDING-A-NUMBER rule 4.** "There is no disk for this" was a
  count over the wrong population, and the check could not have failed because it was never
  aimed at the population the question lives in. It cost three days, not more, because the same
  author overturned it -- but the sentence is still in the plan, unedited, and the plan is
  untracked, so the sentence is what a future reader inherits.

---

# SUMMARY OF THE SLICE

## Where the evidence lives, in four tiers of decreasing visibility and increasing recency
| tier | what | tracked? | dated | status |
|---|---|---|---|---|
| 1 | `CAMPAIGN.md` rung 2 | yes | current | authoritative, one paragraph |
| 2 | `plans/sparse-classifier/`, `plans/representation-science/` | yes, but UNINDEXED by CATALOG.md | 2026-06-25 / 06-28 | frozen, artifacts all lost |
| 3 | `plans/LEARNED-REPRESENTATION-ABLATION.md`, `plans/ABLATION-ARCHITECTURE.md` | **NO** | 2026-08-17 | plans, never executed as written |
| 4 | `storage/encoder-study/` 131 scripts + 340 artifacts + 5 docs; `storage/encoder/` 2.6 GB; `storage/probe/` 347 GB | **NO**, and not in any git repo | 2026-08-19 to 08-26 | the real body of work |

## Platform versus lab, decided
- **PLATFORM, real:** `encode_residue_sparse` (registered, 10+ PRs 2026-08-20/21, 21 tests, all
  five blocking gaps closed, order guard added #827/#863); `apply_learned_encoder`;
  `two_tower_classifier.py` (merged 2026-06-28/29, opt-in, default OFF, untouched since);
  the object-store bundles `encoders/learned-k128-hardneg-0868f1ff-r227-20260810` and
  `two_tower/go-side-2026-06-29`; the CSV `knn_226_227_fmicrow.csv`.
- **LAB, does not count by the project's own rule:** every measurement in this slice. The
  purity screen, the 44-arm table, the reachability supersession, the ProtST retraction, the
  layer curve, the quantisation curve, the Spearman validation, the atom-correspondence test,
  the 347 GB residue probe. 131 scripts, zero registered operations.
- **NOTHING in this slice has been touched since 2026-08-26.** `find storage -newermt
  2026-08-27` returns only `calibration-study/`, `ontology-drift/`, `logs/` and `throughput/`.
  **The current window (post-2026-08-27, 93 evaluation_result rows) contains no
  representation or sparse-encoder work at all.**

## The three things a reader must not miss
1. **F13** -- the headline learned-encoder result was measured on **ankh-base at 768
   dimensions**, and the plan that reasons about it says esm2_150m at 640, in its first
   sentence and in its whole substrate ladder. The receipt (`storage/encoder/MANIFEST.json`,
   `VALIDATION.json`, and the byte-size of `encoder.pt`) settles it three independent ways.
2. **F3 + F14** -- "+40%" is a held-out Spearman against the training objective, produced by a
   different harness from the module that carries its name, and it is attributed in the plan
   store to `d8979601`, an encoder that exists on this machine only as a string in fourteen
   documents. The encoder with receipts is stamped "NOT the champion d8979601".
3. **F8bis + F9** -- the two-tower classifier's science was never retracted and never shipped;
   its `prep.npz` has no producer and never did; its GO side survives only because someone
   hand-mounted a preserve partition on 2026-08-24 and uploaded two files on 08-26; its seven
   trained heads were NOT uploaded and live only on `/mnt/protea-archive`, which is **an empty,
   unmounted directory today**. The one independent test ever run on it missed a pre-declared
   threshold of 290 with a mean rank of **9,378 of 29,027**.

## What would have to exist for this slice to be reborn in the platform
`train_functional_encoder`, `apply_functional_encoder` (partly exists), `score_knn_transfer`,
`evaluate_stratified` (exists), `export_embedding_matrix` (binary), `cluster_sequences`
(MMseqs2 -- absent from this machine entirely, and the campaign's homology axis has no producer
without it), `measure_sigma_d_by_contrast_class`, `build_go_text_embeddings`,
`build_go_sparse_codes`, `build_two_tower_prep`, `train_two_tower_head`.
`build_go_cooccurrence` is the only one of the two-tower's four that already exists.
