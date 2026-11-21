# Census slice: campaign-and-levers

Auditor slice key: `campaign-and-levers`
Started: 2026-09-02

## Slice description

- `plans/beat-lafa-1/` including `CAMPAIGN-DOSSIER.md`: for EACH lever L1..L7, run or not, dated.
- `plans/meta-reranker/`
- `plans/target-selection-native/`
- `plans/SCORER-PROVENANCE.md`
- CATALOG.md claims best confirmed native 0.3745 at EvalResult `b21b187c`: does that row still exist anywhere, or did it die on 2026-08-27?
- The reranker credited +0.1353 per-cell mean in a no-known max_terms=500 frame, with an NK/LK-only +0.108 that IS frame-safe: separate them.
- `reranker_model` has 0 rows in the live database.

Key dates: 2026-07-28 OS reinstall; 2026-08-27 experiment registry wipe.

---

## Files in the slice, and their dates

verdict: CONFIRMED
- `/home/xaxi/Thesis2/agent-farm/plans/beat-lafa-1/PLAN.md` (10493 B) and
  `/home/xaxi/Thesis2/agent-farm/plans/beat-lafa-1/CAMPAIGN-DOSSIER.md` (13765 B).
  Both have filesystem mtime `Jul 28 17:01` = the reinstall day, i.e. the mtime is the
  restore stamp, NOT the authorship date.
- CAMPAIGN-DOSSIER.md:1 self-dates `2026-06-20/21`. PLAN.md:3 self-dates `2026-06-21`.
- `meta-reranker/ARCHITECTURE.md`, `target-selection-native/PLAN.md`, `SCORER-PROVENANCE.md`
  all also mtime Jul 28 17:01.
date of evidence: 2026-06-20/21 -> window: **pre-wipe AND pre-reinstall**
note: EVERY number in this entire slice's primary documents predates the 2026-08-27
      registry wipe by more than two months, and predates the 2026-07-28 reinstall by
      five weeks. Nothing in beat-lafa-1 is evidence about the current window unless it
      was independently recomputed after 2026-08-27.

## The experiment ledger of CAMPAIGN-DOSSIER.md section 2

verdict: CONFIRMED as a document; the ROWS it points at are gone (see next section)
first number: seven EvaluationResult ids, all timestamped 06-20/06-21, at
  `agent-farm/plans/beat-lafa-1/CAMPAIGN-DOSSIER.md:30-36`:
    f42faad8  06-20 19:15  lean-31 baseline            NK .4524 LK .4362 PK .1992  MEAN .3626
    184579b6  06-21 08:30  + self_prior (string fix)   NK .4627 LK .4424 PK .2016  MEAN .3689
    cb77d55d  06-21 11:07  + IA ("both")               NK .4640 LK .4513 PK .2013  MEAN .3722
    1df357be  06-21 12:14  clean-15 curated            NK .4514 LK .4494 PK .1973  MEAN .3660
    7521ab8a  06-21 13:18  + S2 scale_pos_weight PK    NK .4640 LK .4513 PK .2065  MEAN .3739
    b21b187c  06-21 14:25  + S2 all aspects (BEST)     NK .4645 LK .4526 PK .2065  MEAN .3745
    b657e250  06-21 18:12  + L2 soft-prop (all)        NK .4657 LK .4560 PK .1939  MEAN .3719
frame: prediction set `f377adae-047a-4e52-9e79-b43d5e722a70` (7401 LAFA targets),
  eval set `34a634a8`, frame=lafa, official harness = TOI + PK-known exclusion,
  metric f_micro_w, cafaeval ia + prop=fill + norm=cafa + no_orphans + th_step=0.01,
  MAX-collapse per (protein, go_id), OBO+IA from `lafa_t0_Sep_2025`.
  (`CAMPAIGN-DOSSIER.md:54`)
population: 7401 targets, split NK/LK/PK; "MEAN" is the unweighted mean of the three
  per-category f_micro_w values, NOT a pooled number.
note: the "MEAN" column is a **mean of three cells**, so every delta quoted in this slice
      (+0.0063, +0.0033, +0.0023, -0.0026) is a per-cell mean delta, not a population
      quantity. See the CORRECTION section immediately below.

## CORRECTION (self-caught): the MEAN column IS the mean of its three cells

verdict: CONFIRMED by second computation
I first mis-added and wrote that the MEAN column did not equal the mean of its cells.
Recomputed all seven rows in python: every one matches the published MEAN to rounding.
    f42faad8 0.362600 vs 0.3626 | 184579b6 0.368900 vs 0.3689 | cb77d55d 0.372200 vs 0.3722
    1df357be 0.366033 vs 0.3660 | 7521ab8a 0.373933 vs 0.3739 | b21b187c 0.374533 vs 0.3745
    b657e250 0.371867 vs 0.3719
**So the headline 0.3745 is an UNWEIGHTED MACRO-AVERAGE OVER THREE KNOWLEDGE CELLS,
not a population f_micro_w.** That is the frame, and it is not stated in the sentence
that carries the number (`CAMPAIGN-DOSSIER.md:10` reads "f_micro_w = 0.3745" with no
mention that the three cells were averaged).
Consequence: PK carries weight 1/3 in the headline. Under the project's own norm the
SERVED population is NK (~5% of a window) and a window is ~70% PK by construction, so
0.3745 is neither the served number nor the population number; it is a third object.
Every delta in the ledger inherits the 1/3 weighting: the S2-PK move of +0.0073 on PK
alone (0.1992 -> 0.2065) enters the headline as +0.0024.
note: this correction is COLLIDING-A-NUMBER rule 1 applied to my own first number, and
      it is recorded rather than silently deleted.

## Does EvalResult `b21b187c` (best confirmed native 0.3745) still exist anywhere?

verdict: **CONTRADICTED as a live row. It is dead. Every surviving occurrence is an ECHO of
the same 2026-06-21 document.**
first number: `plans/CATALOG.md:16` "Best confirmed native = **0.3745** (EvalResult `b21b187c`)"
second number (independent): an exhaustive grep of the whole tree for the string `b21b187c`
  returns hits in exactly THREE kinds of place, none of which is a stored result:
   1. `plans/beat-lafa-1/CAMPAIGN-DOSSIER.md` (lines 10, 35, 38, 92, 211) and its ~20
      identical copies under `worktrees/*/plans/` (git worktrees of agent-farm).
   2. `plans/CATALOG.md:16` and its worktree copies -> quoting (1). ECHO.
   3. `docs/source/runbooks/lafa-native-parity.rst:24` in the PROTEA worktrees, incl.
      `/home/xaxi/Thesis2/worktrees/protea-deploy/docs/source/runbooks/lafa-native-parity.rst:24`
      -> prose citing the id, no value stored. ECHO.
  Plus the agent transcripts under `~/.claude/projects/` (this and the killed audit).
  **Zero hits in `storage/`, zero parquet/json/csv holding the row, zero SQL dump.**
where I looked (the negative-check reach): `/home/xaxi/Thesis2` recursively (all repos, all
  worktrees, `storage/`, `thesis/`, `complexity-paper/`, `CAFA_forever/`), and
  `/home/xaxi/.claude/`. If a dump of the pre-wipe experiment registry existed on this disk,
  a grep for its own primary-key string would have found it. It did not.
date of evidence: created 2026-06-21 14:25 -> window: **pre-wipe, and pre-reinstall**
frame: see the ledger frame above (macro-mean over NK/LK/PK, f_micro_w, TOI + PK-exclusion,
  prediction set f377adae, eval set 34a634a8 = `34a634a8-5739-4b04-923c-26db9eaab21e`).
population: 7401 LAFA targets.
platform gap: to be reborn writing to the database this needs (a) the prediction set
  `f377adae` regenerated by `protea-predict` on the LAFA query file, (b) the three
  RerankerModel rows `198baf99 / 68f3232c / f0669e41` re-registered -- and `reranker_model`
  has **0 rows** in the live database, so the boosters that produce 0.3745 are not
  registered anywhere the platform can see -- and (c) `run_cafa_evaluation` dispatched via
  `POST /jobs` against eval set `34a634a8`. All three are gone.
note: **CATALOG.md still advertises 0.3745 as "best confirmed native" with a pointer to a row
      that no longer exists.** The number is not wrong; it is unverifiable and un-refreshable
      on this machine, and the document does not say so. Anyone reading CATALOG.md today is
      being handed a June number as if it were current state.

## The ledger was ALREADY selectively pruned, two months before the wipe

verdict: CONFIRMED, and this is the single most damaging finding in the slice
first number: `worktrees/*/observability/OBSERVATIONS.md:196` (e.g.
  `/home/xaxi/Thesis2/worktrees/exp-graph/observability/OBSERVATIONS.md:196`), dated
  2026-06-22 ~10:54Z:
    "INT-8 SCORE LANDED = 0.3462 native frame=lafa = REGRESSION from 0.3745 (NOT an
     improvement; PK did not rise). Diagnosis: TRAIN/SERVE SKEW -- the trio was trained
     WITHOUT association, so serving association live without retraining hurts. ...
     Conductor DELETED the regression from /benchmark (result 204), kept 0.3745 baseline
     (clean). => That is why my DB query only found yesterdays b657e250: the INT-8
     eval_result was deleted as a regression. ... MONITOR LESSON: grep the conductor
     transcript for the result conclusion, not just the DB (results can be deleted)."
second number: 0.3462 -- an eighth evaluation on the same frame, on the same prediction set
  family, that is **absent from the CAMPAIGN-DOSSIER ledger of "every eval"**
  (`CAMPAIGN-DOSSIER.md:23` literally says "every eval on prediction set f377adae").
date of evidence: 2026-06-22 -> window: pre-wipe, pre-reinstall
note: the dossier's ledger is therefore a SURVIVORSHIP TABLE, not a census. A losing arm was
      deleted from the registry by an automated conductor, on the day after the ledger was
      written, and the ledger was never amended. Two consequences a reader must not miss:
      (1) the "BEST CONFIRMED 0.3745" was best over a set from which at least one worse
      result had been physically removed, so any max-over-arms correction is understated;
      (2) the 2026-08-27 wipe is not the first time results left this registry -- deletion
      was an ordinary operation here. Anything reasoning from "how many arms did we try"
      cannot use this table.

## Collateral from the same OBSERVATIONS line: the thesis had claimed 0.391 natively

verdict: CONFIRMED (as a recorded correction, not as a measurement)
first number: 0.391 "sealed offline champion", `CAMPAIGN-DOSSIER.md:14-15`, explicitly
  "frame-optimistic and its source files are DELETED (`/tmp/canon_composite.tsv` etc.,
  not byte-reproducible)".
second: OBSERVATIONS.md:196 -- "INT-8 confirmed native=0.3745 -> thesis claiming 0.391
  native is FALSE -> conductor spawned thesis-writer to reframe (0.391=offline-research,
  native=0.3745)".
date of evidence: 2026-06-22 -> window: pre-wipe, pre-reinstall
note: 0.391 was in the thesis as a NATIVE number and had to be reframed. It is the clearest
      instance in this slice of a frame-optimistic offline number travelling as if it were
      the platform number. Its sources are deleted, so it is not byte-reproducible and never
      will be.

## THE LEVER TABLE: L1..L7 of beat-lafa-1, run or not, dated

The plan (`plans/beat-lafa-1/PLAN.md:48-107`) prioritises seven levers. Here is what
actually exists on this disk for each. "script exists" = a file that implements it;
"result exists" = a number with a receipt.

| Lever | What it is (PLAN.md line) | Script? | Result? | Verdict | Date |
|---|---|---|---|---|---|
| **L1 CondProbMod** | :61 training-variant + post-proc + ensemble | NO | NO | **NEVER RUN** | n/a |
| **L2 soft Pmin/Pmax** | :78 exact ProtBoost 4.5 formula | YES `l2_softprop_pk.py` | YES, REFUTED | **RUN, refuted** | 2026-06-21 |
| **L3 low-prob clipping** | :76 per-aspect threshold before Fmax sweep | NO | NO | **NEVER RUN** | n/a |
| **L4 freq-bucket GBM feature** | :85 log-annotation-count per candidate | NO | NO | **NEVER RUN** | n/a |
| **L5 GCN stacker over scores** | :92 shallow GCN over the score vector | NO (as a stacker) | NO | **NEVER RUN** | n/a |
| **L6 retrieved hard-negatives** | :52 the plan's OWN highest-EV lever | NO | NO | **NEVER RUN** | n/a |
| **L7 GO-def text cross-encoder, PK-only** | :98 PubMedBERT GO-def vs protein text | partial, in a DIFFERENT slice | partial | **NOT run as L7** | 2026-07+ |

verdict: **six of seven levers in the canonical campaign plan were never executed. Only L2
was, and L2 was refuted.** The one lever the plan itself names "best next bet" (L6) has no
implementation anywhere on this machine.

where I looked (the negative-check reach), for each of L1/L3/L4/L5/L6:
  - `grep -rni` over `repositories/` and `agent-farm/plans/` for: `CondProbMod|cond_prob`,
    `low.prob clip|clipping`, `freq.bucket|freq_group|frequency.bucket|annotation.frequency`,
    `gcn`, `hard.negative|hard_negative|hardneg`, `cross.encoder|pubmedbert|go_def`.
  - the entire lab experiment directory
    `/home/xaxi/Thesis2/repositories/protea-reranker-lab/research/fullgo_models/` (29 entries,
    the only surviving home of the campaign's scripts) plus its four subdirectories
    `lever_experiments/`, `lean_ia_p_experiment/`, `parity_audit/`, `native_boosters_*/`.
  - `storage/` in full.
  These are exactly the places the other levers' code DID live, so a script would have been
  found if one existed.
first number: for L1/L3/L4 the ONLY hits in the whole tree are the two plan documents
  themselves and their ~20 worktree duplicates. There is no third document, no script, no
  artifact. For L1 there is additionally `plans/roadmap-from-zero/PLAN.md:70` R2.1
  "CondProbMod + soft Pmin-Pmax hierarchical post-processing", carried in
  `plans/PLAN.md:388` with status **"pending"** -- an independent second source that agrees
  L1 never ran.
date of evidence: plan authored 2026-06-21; the last campaign activity in
  `agent-farm/observability/OBSERVATIONS.md` is 2026-06-23 -> window: pre-wipe, pre-reinstall
platform gap: none of L1/L3/L4/L5/L6 has a registered operation. L3 and L2 are the only two
  that would be cheap: L2 already exists in-platform as the opt-in `softprop` flag in
  `run_cafa_evaluation` (PROTEA #666), so L3 (a per-aspect clip) is the same seam. L6 is
  blocked by a real platform gap that the dossier itself names
  (`CAMPAIGN-DOSSIER.md:173-174`): "needs neighbour-level data exposed (the export aggregated
  it away)". That is a MURO for L6 as specified: the export destroys the per-neighbour rows
  the feature is defined on.
note: **the campaign died two days after its plan was written, and it died on a UI
      interaction, not on a result.** `agent-farm/observability/OBSERVATIONS.md:224`,
      2026-06-23 ~03:21Z: the conductor sat idle ~25 min on the user's UNSENT typed line
      "Acepta 0.3745... pivota a hard-negatives"; the keystroke never landed because the
      user's tmux client was attached and focused. Then at ~09:19Z (line 228) the user gave a
      new direction ("disena SDR-C, el encoder sparse aprendido") and the same line records
      "(Note: hard-negatives product lever still pending after the SDR/interview-doc
      thread.)". L6 was never picked back up. This is the actual cause of death of
      beat-lafa-1, and it is recorded nowhere in beat-lafa-1's own documents.

## Name collision: two different "hard negatives" (COLLIDING-A-NUMBER rule 3)

verdict: CONFIRMED
`hardneg` is all over `repositories/protea-reranker-lab/` -- `scripts/train_learned_encoder.py`,
`encoder_ablation.py:92` `ArmSpec(name="learned-k128-hardneg", ...)`,
`chunk_attn_encoder.py:11`, `run_sdr_c_taskaware.py:158`,
`repositories/PROTEA/docs/source/runbooks/serve-learned-code-retrieval.rst:46` (`ankh_base_hardneg.pt`).
Those are hard negatives INSIDE a contrastive objective for the sparse encoder: embedding-near
/ GO-far pairs, up-weighted in a training loss.
L6's "retrieved hard-negatives" is a completely different object: GBM FEATURES computed at
scoring time from the KNN neighbours that carry an aspect annotation but LACK the candidate
term.
note: a reader grepping "hard negative" to ask "did we do L6?" gets ~10 confident hits and
      would conclude yes. The answer is no. Same words, two objects, one of them shipped and
      one of them never started.

## The reranker's +0.1353 vs its frame-safe +0.108: SEPARATED, with the receipt

verdict: **CONFIRMED, and the receipt survives.** Both numbers reproduce exactly from a
primary table that is still on this disk. The frame warning in SIGNAL-REGISTRY is
arithmetically correct and, if anything, understates the concentration.

first number: `agent-farm/plans/SIGNAL-REGISTRY.md:71` --
  "Per-category LightGBM lambdarank reranker | The fusion layer | vs raw-KNN champion,
   per-cell mean 0.5006 vs 0.3653 = **+0.1353**. FRAME WARNING: this is a no-`-known`,
   `max_terms=500` frame in which the three PK cells carry the largest deltas ... The
   **NK/LK-only delta from the same table is +0.108 and IS frame-safe**. Do not present
   0.5006 alongside 0.3884 / 0.40629 as commensurable"

THE PRIMARY RECEIPT (not an echo -- it is the table the registry row summarises):
  `/home/xaxi/Thesis2/repositories/protea-reranker-lab/results/clean_227230/SUMMARY.md`
  (also in worktrees lab-reporting / lab-gates / lab-bundle; the repo copy is canonical)
  lines 22-33, per-cell, champion -> reranked -> gate:
      nk-mfo 0.5549 -> 0.6367   d +0.0818
      nk-bpo 0.3619 -> 0.4607   d +0.0988
      nk-cco 0.4281 -> 0.5488   d +0.1207
      lk-mfo 0.4416 -> 0.5654   d +0.1238
      lk-bpo 0.3764 -> 0.4870   d +0.1106
      lk-cco 0.3905 -> 0.5044   d +0.1139
      pk-mfo 0.3017 -> 0.4707   d +0.1690
      pk-bpo 0.1401 -> 0.3433   d +0.2032
      pk-cco 0.2925 -> 0.4886   d +0.1961
  and lines 13-18, a SECOND aggregation of the same run, "pooled-per-aspect (one
  threshold/ns = the LAFA deployment number)": mfo 0.3570->0.5185, bpo 0.1602->0.3626,
  cco 0.3105->0.4949, MEAN 0.2759 -> 0.4587 = **+0.1828**.

second number (mine, recomputed in python from the nine cells, independent of the file's
own MEAN row):
      champion mean9   0.365300   (published 0.3653)  match
      reranked mean9   0.500622   (published 0.5006)  match
      gate mean9       0.437478   (published 0.4375)  match
      delta all 9      0.135322   (published +0.1353) match
      delta NK/LK only 0.108267   (published +0.108)  match
      delta PK only    0.189433   (NOT published anywhere)
      gate delta       0.072178   (published +0.0722) match

**THE SEPARATION, stated plainly:**
  - frame-safe part (NK + LK, six cells): **+0.1083**
  - frame-contaminated part (PK, three cells): **+0.1894**, 1.75x the safe part
  - PK's three cells supply 0.5683/9 = **0.0631 of the 0.1353 headline, i.e. 46.7% of the
    credit from 33% of the cells.** That over-weighting (1.40x) is the exact size of the
    frame problem, and it is not stated in the registry row or anywhere else.
  - the headline is a MACRO-MEAN OVER NINE CELLS, so it is not a population quantity and
    does not correspond to any served number. Nine cells are nine populations.

date of evidence: the file was committed 2026-07-27 20:46:30 +0200 by the author in
  `protea-reranker-lab` commit `de880a1`, message "preserve: track the champion training and
  scoring procedures (#114)" -- i.e. it was RESCUED INTO GIT ONE DAY BEFORE THE REINSTALL.
  The measurement itself is therefore on or before 2026-07-27.
  -> window: **pre-wipe AND pre-reinstall.** Not evidence about the current window.
frame (from `SUMMARY.md:3-9`, quoted in full because this is the whole finding):
  dataset `clean-learned-train227-test230`; learned champion embedding `d8979601`;
  `schema_sha 775611822dd9`; metric **f_micro_w** via canonical cafaeval;
  **prop=fill, norm=cafa, no_orphans, max_terms=500, th_step=0.001, IA/OBO v227**;
  reranker = per-category LightGBM **lambdarank**, one model per NK/LK/PK; **64 real
  features** (`association_*` and `classifier_*` EXCLUDED as zero-filled); grouped by
  (snapshot_pair, protein, aspect); trained v160..v227 with v225-v227 held out for early
  stopping; eval pair v227-v230.
  **`-known` (prior-knowledge exclusion) NOT applied.** `th_step=0.001`, which is ten times
  finer than the beat-lafa-1 harness's `th_step=0.01` -- the two campaigns in this slice do
  not even share a threshold grid.
population: nine cells of the v227->v230 window; per-cell counts are NOT given in the file.
platform gap: the number is produced by two standalone lab scripts in the same directory,
  `train_rerank_227230.py` and `score_rerank_227230.py`, running outside the platform. To be
  reborn writing to the database it needs a registered training operation (there is none --
  the procedure-integration audit already recorded the training layer as unversioned) and
  the `d8979601` learned encoder, which project memory records as **not on this disk**.
  `reranker_model` has 0 rows in the live database, so nothing about this reranker is
  registered platform-side.
note (three things a reader must not miss):
  1. **Is +0.108 really frame-safe? That is a DEDUCTION FROM A DEFINITION, not a
     measurement.** It rests on: NK = no experimental annotation in any aspect, LK =
     experimental in some other aspect but not this one, therefore the within-aspect known
     set is empty for NK and LK and `-known` is a no-op there. There is an independent
     second source that agrees -- project memory
     `project_board_frame_reconstructed_2026_07_18.md` is indexed as "the single most
     consequential flag in the project: the exclusion list applies to prior-knowledge cells
     ONLY". But nobody ran the exclusion on NK/LK and showed the delta is zero. Under
     COLLIDING-A-NUMBER rule 3 this is a hypothesis with a strong prior, not a measurement,
     and the minimal case that would separate it is cheap: run the SAME scoring with
     `-known` on and read the NK/LK cells. It has not been run.
  2. **The same run has TWO published means and they differ by 0.0475.** Per-cell mean
     +0.1353; pooled-per-aspect mean +0.1828. The file itself (`SUMMARY.md:38-39`) calls the
     pooled one "the deployment metric" and recommends the submission on it, while
     SIGNAL-REGISTRY quotes the per-cell one. A reader who takes "the reranker is worth
     +0.1353" from the registry and "+0.1828" from the summary is reading one experiment.
  3. **The file's own verdict names the risk and then does not discharge it**
     (`SUMMARY.md:52-53`): "The large lift warrants a one-shot leakage re-check before the
     LAFA submission, but the split and exclusions are clean." I searched
     `repositories/protea-reranker-lab/results/clean_227230/` (which contains
     `leak_check_overlap.py`) and the whole tree for an output of that check. **The script
     exists; no result file from it exists anywhere.** A named check that was written and
     whose output cannot be found is COLLIDING-A-NUMBER rule 4: the zero here is the reach
     of my search, and I looked in the directory the script lives in, in `storage/`, and
     across all four worktree copies.

## The +0.1353 study's INPUTS were in an agent scratchpad on the old machine, and are gone

verdict: **CONFIRMED. The scripts were preserved; the data they read was not.**
first number: every script in
  `/home/xaxi/Thesis2/repositories/protea-reranker-lab/results/clean_227230/` hardcodes
      S = "/tmp/claude-1000/-home-frapercan-Thesis2/afd2c43a-ede7-46dc-94dd-9745808d2194/scratchpad"
  and reads its inputs from there:
      `train_rerank_227230.py:22`, `score_rerank_227230.py:20`, `champ_227230_v2.py:19`,
      `leak_check_overlap.py:10`, `per_aspect/{run_variants,train_per_aspect,run_blend,
      validate_baseline}.py`, `clfassoc/{clfassoc_lafa,clfassoc_gate_pk,clfassoc_train}.py`,
      `bpo_levers/bpo_levers.py:37`.
  `leak_check_overlap.py:60-62` names the two specific artifacts:
      `{S}/rerank_out/eval_scores.parquet`  (the reranked scores -- the measurement itself)
      `{S}/ds227230/train.parquet`          (the training dataset)
  and `leak_check_overlap.py:78` writes its verdict to `{S}/leak_check_overlap.json`.
second number (independent check): `/tmp/claude-1000/` on this machine contains exactly one
  entry, `-home-xaxi-Thesis2`, created 2026-09-02. There is no `-home-frapercan-Thesis2`.
  `/home/` contains only `xaxi`, created 2026-07-28 16:21 (the reinstall). `/tmp` is a
  **tmpfs** (`df -h`: `tmpfs 31G /tmp`), so it did not even survive a reboot, let alone the
  reinstall. `find / -name leak_check_overlap.json` returns nothing.
date of evidence: scripts committed 2026-07-27 20:46 (`de880a1`); the scratchpad they point
  at died no later than 2026-07-28 -> window: **pre-reinstall-lost**
note: the "preserve" commit saved the PROCEDURE and lost the EVIDENCE. This is the exact
      failure `CAMPAIGN.md` section 0bis is written against ("a procedure outside the
      platform is a capability that dies with the disk") -- except here even the procedure
      cannot run, because its inputs were in /tmp.
      Concretely: **+0.1353 and +0.108 are not recomputable on this machine.** Not because
      the code is missing, but because `eval_scores.parquet` and `ds227230/train.parquet`
      were tmpfs.

## The named leakage check was WRITTEN, its result went to /tmp, and the 7.4% it was checking is now unbacked

verdict: **NOT_FOUND (the output), CONFIRMED (that a check was designed and its number quoted)**
first number: `leak_check_overlap.py:1-4` docstring --
  "Leakage confirmation: re-score pooled-per-aspect f_micro_w for champion (1-distance) and
   reranked (reranker_score) on (a) the FULL eval and (b) the CLEAN eval with all
   train-positive (protein,go) pairs removed. **If the reranker lift survives on clean, the
   7.4% pair overlap is not driving it.**"
  So a 7.4% train/eval (protein, go) POSITIVE-PAIR OVERLAP was measured, and named in the
  docstring of the script written to test it.
second number: none exists. The 7.4% appears nowhere else on this disk -- I grepped the
  whole tree. It is a number surviving only inside a comment. And the check's output file
  (`leak_check_overlap.json`) was written to the vanished scratchpad.
where I looked: `results/clean_227230/` and its three subdirectories, the whole
  `protea-reranker-lab` repo, all four worktree copies, `storage/`, `/tmp`, and a
  filesystem-wide `find` for the output filename.
date of evidence: <= 2026-07-27 -> window: pre-reinstall-lost
note: **`SUMMARY.md:52` tells the reader "the split and exclusions are clean" while
      `leak_check_overlap.py:4` records a 7.4% positive-pair overlap between train and
      eval on the same study.** Those two sentences are in the same directory and they do
      not agree in tone. The delta the check would have quantified is unknown, in the
      direction that would REDUCE +0.1353. This is the clearest open exposure on the
      slice's headline reranker number.

## The 7401-target LAFA query population is not on this disk

verdict: **CONFIRMED gone**
first number: every beat-lafa-1 EvalResult is "7401 targets" on prediction set `f377adae`
  (`CAMPAIGN-DOSSIER.md:10,25`). The lab harnesses name the files:
  `per_aspect/lafa_harness.py:18-19` and `clfassoc/lafa_harness.py:18-19`
      QFASTA = "/home/frapercan/Thesis2/protea-lafa-knn/lafa_queries_7401.fasta"
      KNN_FALLBACK = "/home/frapercan/Thesis2/protea-lafa-knn/predictions_7401.tsv"
second number: `find /home/xaxi -name "*7401*"` returns only browser caches, shell snapshots
  and git object hashes that coincidentally contain the digits. Neither file exists.
  `/home/frapercan` does not exist.
what DID survive, at a different path nothing points to:
      `/home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/IA.tsv` (991,280 B, 2026-08-11)
      `/home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/go-basic.obo` (31,428,837 B)
      `/home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/train_terms.tsv`
      `/home/xaxi/lafa-e2e/data/Sep_2025/go-basic.obo` (byte-identical size)
  So the ONTOLOGY and the ACCRETION TABLE of the frame survive; the QUERY POPULATION and the
  baseline predictions do not.
date of evidence: reinstall 2026-07-28 -> window: pre-reinstall-lost
platform gap: `protea-predict` REQUIRES `--query_file` (standing norm
  `feedback_query_population_must_match_lafa`). With the 7401 FASTA gone, the LAFA query
  population cannot be reconstituted from anything on this machine, so **none of the seven
  beat-lafa-1 numbers can be re-measured**, independently of the registry wipe.
note: `/mnt/protea-archive` exists as an empty mount point (created 2026-07-28 17:09) and
      `df -h` shows NOTHING mounted there. The archive partition project memory refers to is
      not available, so "it might be on the archive" is not checkable from here and must not
      be asserted either way.

## plans/target-selection-native/: measured residual, plan NEVER EXECUTED

verdict: measurement CONFIRMED and internally consistent; **execution CONTRADICTED (T1-T5 all
unbuilt, still unbuilt in the newest tree)**
first number: `plans/target-selection-native/PLAN.md:17-24`, native reconcile on the live
  v227->v230 pair (old=`c905dffa`, new=`2394b9a1`), t0 under OBO `releases/2025-07-22`:
      official 7401      = 7401
      native (fixed t0)  = 8725
      intersection 7347 | native-only +1378 | official-only 54
second number (mine, arithmetic on the table itself): 7347 + 54 = 7401 and
  7347 + 1378 = 8725. The table closes exactly, so it is a real count, not a rounded summary.
  Recovery of the official frame = 7347/7401 = **99.27%**, matching the prose "99.2%" at
  `PLAN.md:5`. Native excess = 1378/8725 = **15.8% of the native delta is outside LAFA's
  target universe.**
root cause, and it is a MECHANISM not a guess (`PLAN.md:28-41`): LAFA runs
  `INTERSECT_TARGETS` BEFORE `CLASSIFY_GROUNDTRUTH`
  (`CAFA_forever/workflows/evaluate_window.nf`), i.e. it restricts to proteins present in
  BOTH timepoints' curated `test_sequences` universe and only then splits NK/LK/PK.
  `compute_evaluation_data_reconciled` has no such restriction.
**Did it land? NO.** I checked the NEWEST tree, `worktrees/protea-deploy` at
  `a5de702707d807252b088219131d95db16551c3b`, 2026-09-01 22:19:45 (ahead of
  `repositories/PROTEA`):
   - `grep -rn "target_accession_source|target_universe|target-universe|target_set_id"`
     over every `.py`: **zero hits**.
   - `protea/core/evaluation.py:596` `def compute_evaluation_data_reconciled(session,
     old_annotation_set_id, new_annotation_set_id, old_native_snapshot_id,
     new_native_snapshot_id, pivot_snapshot_id) -> EvaluationData` -- **no target-universe
     parameter**, fourteen months of plan later.
  So T3 (the platform change) never happened, and therefore T4 (the GATE) and T5 (durable
  wiring) cannot have happened either.
date of evidence: plan written ~2026-06-23/24 (it cites PROTEA PR #671 and memory
  `project_phantom_gap_crossobo_2026_06_23`); non-landing verified against a 2026-09-01 tree
  -> window: the measurement is pre-wipe; the NEGATIVE is post-wipe-current.
population: v227->v230 window; 7401 official targets vs 8725 native.
platform gap: this IS the platform gap, named precisely by the plan itself. The operation
  that would have to exist is a target-universe filter on
  `compute_evaluation_data_reconciled` / the `generate_evaluation_set` payload, applied
  BEFORE NK/LK/PK classification. It does not exist.
note: the consequence is stated at `PLAN.md:83-87` and is the thing to carry forward: the
      reported native number is on 7401 only because the eval set `34a634a8` was
      **externally imported**. The native pipeline still produces 8725 and would REGRESS the
      frame if used. So "the on-platform native number" has never been native end to end;
      the ground truth for every beat-lafa-1 number came from outside the platform.

## THE DIAGNOSIS THAT DROVE THE WHOLE CAMPAIGN: "PK is precision-limited, NOT recall-limited"

verdict: **DEDUCED-NOT-MEASURED, and the one statistic it leans on meant something else at
the time it was read.** This is the most consequential finding on the slice, because every
lever L1..L7 was prioritised by it.

first number: `plans/beat-lafa-1/PLAN.md:12-17` --
  "**The bottleneck is PK precision, and it is the field's open problem.** At PK's Fmax
   operating point: recall ~0.25, precision ~0.15, **coverage 1.0**. NOT a
   candidate-pool/recall ceiling -> the pool has plenty of candidates; PK ranks too many
   plausible-but-FALSE terms high."
  Restated as durable learning at `CAMPAIGN-DOSSIER.md:150-152`.
  The inference chain is: coverage is 1.0 -> every target got predictions -> the candidate
  pool is not the limit -> the problem is discrimination, not retrieval -> therefore build
  discriminative levers (L6 hard-negatives, L1 CondProbMod) and NOT plausibility priors.

DEFECT 1 -- **"coverage 1.0" was `cov_max`, the maximum over ALL thresholds, not coverage at
the Fmax threshold.** Independent source, in the PLATFORM's own test suite, at
  `/home/xaxi/Thesis2/worktrees/protea-deploy/tests/test_coverage_at_operating_point.py:1-15`
  (module docstring, verbatim):
   "cafaeval's best-frame row carries both ``cov``, the coverage at the tau that maximised
    Fmax, and ``cov_max``, the maximum of coverage over every tau. **We stored only cov_max,
    under the name ``coverage``**, beside ``n`` read from the best-tau row. Those describe
    different points, and read as a pair they say something false. In rung 1 a single
    0.98 -> 0.99 step in the optimal threshold moved n by 17 per cent while coverage sat at
    1.0, which reads as the scored population having shrunk."
  That file was added by commit `078586a`, **2026-08-20 02:56:53 +0200**, PROTEA #804,
  "fix(evaluation): publish coverage at the threshold Fmax landed on".
  The test's own worked example is `cov_max = 1.0` with `coverage_at_tau = 0.83`.
  **So on 2026-06-21, when the diagnosis was written, the only coverage the platform could
  publish was the max over thresholds, which is 1.0 for essentially any predictor that emits
  anything at a low enough threshold.** Reading it as "coverage at the Fmax operating point"
  is exactly COLLIDING-A-NUMBER rule 3: a correct definition of "coverage" grouping two
  distinct quantities, and the reasoner picturing the wrong one. The sentence in PLAN.md
  even says "At PK's Fmax operating point ... coverage 1.0", which is the specific reading
  the platform could not support for another two months.
  Effect direction: the true coverage at tau is <= 1.0, so the pool/recall ceiling was
  UNDER-suspected, in the direction that would have made a recall lever more attractive and
  the discriminative levers less so.

DEFECT 2 -- **the quoted (recall, precision) pair does not reconcile with any PK number in
the campaign's own ledger.** My second computation:
      F1(recall 0.25, precision 0.15) = 2*0.25*0.15/0.40 = **0.1875**
  The PK cells actually recorded are 0.1992 / 0.2013 / 0.2016 / 0.2065 / 0.1973 / 0.1939
  (`CAMPAIGN-DOSSIER.md:30-36`). To reach the BEST one, 0.2065, at recall 0.25 needs
  precision 0.1759, not 0.15; at precision 0.15 it needs recall 0.3313, not 0.25.
  The pair is written with tildes, so this is not a contradiction on its own -- but it means
  the pair is not a readback of any stored row, and no row it could be a readback of exists.
where I looked: the ONLY occurrences of `recall ~0.25` / `precision ~0.15` /
  `coverage 1.0` in the whole tree are `beat-lafa-1/PLAN.md:13` and
  `beat-lafa-1/CAMPAIGN-DOSSIER.md:150-151` plus their ~20 worktree duplicates. No script
  computes them, no artifact stores them, no other document quotes them from a source. I
  also searched `repositories/protea-reranker-lab/` (where the campaign's scripts live) and
  `storage/`.
date of evidence: claim 2026-06-21; the contradicting platform fix 2026-08-20
  -> window: claim is pre-wipe/pre-reinstall; the correction is post-reinstall, pre-wipe.
frame: unstated in the source. The dossier's own methodology section
  (`CAMPAIGN-DOSSIER.md:52`) warns that the validation recipe is OPTIMISTIC (no-TOI,
  no-PK-exclude) and only the TEST recipe is official; the diagnosis does not say which
  recipe produced its p/r/coverage. **FRAME-UNKNOWN.**
population: PK cells only; count not given.
platform gap: the diagnosis needs a per-cell precision/recall/coverage-at-tau readout at the
  Fmax operating point. That readout NOW EXISTS -- `parse_results` publishes
  `coverage_at_tau` (`protea/core/operations/_run_cafa_artifacts.py:741`) and it is surfaced
  on `/graph` (`protea/api/routers/graph.py:54`,
  `protea/api/routers/_graph_reads.py:284`). So this is one of the few things on the slice
  that is REBORN-READY: re-running an evaluation today would publish the honest number.
  What is missing is the prediction set to run it on.
note: **the campaign's entire lever ordering was chosen by this diagnosis, and six of the
      seven levers were never run, so the diagnosis is untested in both directions.** If a
      reader takes one thing from this slice: "PK is precision-limited, not recall-limited"
      is currently a hypothesis supported by a misread statistic, and it is cheap to settle
      now that `coverage_at_tau` exists.

## The dossier's own memory pointers are dead

verdict: CONFIRMED gone
first number: `CAMPAIGN-DOSSIER.md:204-205` names three memory files as the campaign's
  durable record: `project_beat_lafa_1_plan_2026_06_21.md`,
  `project_native_gap_diagnosis_2026_06_20.md`,
  `feedback_native_reranker_procedure_2026_06_21.md`.
second number: the live store
  `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/` holds 210 files. **None of the
  three is there.** The store was curated 2026-07-27 and the archived remainder went to
  `/mnt/protea-archive/archive/memory-archive-2026-07-27/`, which is an EMPTY, UNMOUNTED
  mount point on this machine.
date of evidence: curation 2026-07-27 -> window: pre-reinstall-lost (recoverable only if the
  archive partition is remounted)
note: so for the campaign in this slice, the plan documents are the ONLY surviving record.
      The three memories that held the diagnosis detail -- including, most likely, whatever
      produced "recall ~0.25, precision ~0.15" -- are not readable from here.
      `IMPROVEMENTS-BACKLOG.md` (rows H4-*) and `RESUME_2026-06-21.md`, also cited at
      `CAMPAIGN-DOSSIER.md:203`, do not exist anywhere on this disk either.

## THE MEASURING INSTRUMENT CHANGED TWICE, AND THE CAMPAIGN SITS BETWEEN THE TWO CHANGES

verdict: CONFIRMED. Dated timeline from `repositories/cafaeval-protea` git log (a primary
source, not a document):
    2026-04-13   the fork's first public release
    **2026-04-23 12:36:47  `cec8ccd`  "fix: PK coverage > 1 -- restrict `n` row count to
                 post-exclusion population"**  (ADR-008)
    2026-06-10 13:38:56  `299e265`  docs-only commit -- **the resolved pin under which every
                 beat-lafa-1 number was produced**
    2026-06-20/21          the seven beat-lafa-1 evaluations
    2026-06-24 19:28:39  `52acad7`  sparse eval (CSR + sparse GO DAG) -- bit-identical
    **2026-06-25 06:19:47  `80d705a`  "fix(graph): propagation fill bit-parity to main"**
    2026-09-01 15:21:33  `e937e0e`  "A protein with no scoreable truth is not a false
                 positive (#26)" -- the CURRENT pin (per `plans/DECLARED-REVISION.txt` and
                 `storage/coordination/CHECKLIST.md`: PROTEA #917 repinned to it)
So the campaign's numbers were made with an instrument that has since been corrected TWICE,
and the second correction was itself made four days after the campaign ended.

### Change 1: the PK coverage bug (ADR-008), and what it does to "coverage 1.0"
first number: `worktrees/protea-deploy/docs/source/adr/008-cafaeval-pk-coverage-fix.rst`,
  dated 2026-04-23. Upstream `cafaeval` counted `metrics['n']` over the PRE-exclusion
  population while dividing by the POST-exclusion `ne`, so **PK coverage came out at 1.3-1.9
  on every PROTEA benchmark run**, and, silently, `precision` under `normalization='cafa'`
  was under-divided. The ADR's own words: "On the 220->230 PROTEA benchmark this drags PK
  Fmax from its true value down by 30-40 %."
  Measured effect after re-running the 15 PK evaluations:
      PK BPO Fmax       0.130 -> 0.198   (+0.068, +52.3%)
      PK CCO Fmax       0.301 -> 0.366   (+0.065, +21.6%)
      PK MFO Fmax       0.210 -> 0.291   (+0.081, +38.6%)
      PK BPO coverage   1.94  -> 0.97
      PK BPO precision  0.088 -> 0.157

**AND THIS IS ALMOST CERTAINLY WHERE THE CAMPAIGN'S DIAGNOSIS CAME FROM.** My arithmetic:
    - ADR-008 PK-BPO after the fix: Fmax 0.198 with precision 0.157
      => implied recall = 0.198*0.157/(2*0.157-0.198) = **0.2680**
    - ADR-008 PK-BPO before the fix: Fmax 0.130 with precision 0.088
      => implied recall = **0.2487**
    - the campaign's diagnosis: "recall ~0.25, precision ~0.15, coverage 1.0"
  precision 0.157 -> "~0.15"; recall 0.2487/0.2680 -> "~0.25"; **coverage 0.97 -> "1.0"**.
  I cannot prove the provenance (the three memory files that would say are gone), so mark it
  FRAME-UNKNOWN, but no other source of a PK (recall, precision) pair exists on this disk,
  and this one reproduces the quoted pair.
  If that is the provenance, then the campaign's founding diagnosis is:
    (a) **ONE CELL (PK-BPO) presented as the whole PK category** -- nine cells are nine
        populations, and the ADR's own table shows PK-CCO at 0.366 and PK-MFO at 0.291,
        which are nothing like PK-BPO's 0.198;
    (b) on the **220->230** benchmark, NOT the **227->230** LAFA frame the campaign was
        actually optimising;
    (c) **Fmax**, not the `f_micro_w` the campaign's ledger reports -- two of the four
        statistics COLLIDING-A-NUMBER warns are all called "F";
    (d) with coverage **0.97 rounded up to 1.0** and then used as the premise for "NOT a
        candidate-pool/recall ceiling".

### Change 2: the propagation-fill fix, whose own commit message understates it 13x to 32x
first number: `plans/SCORER-PROVENANCE.md:28-46` (written 2026-07-27, "the only moment both
  scorer generations could be run side by side on the same frozen inputs"):
      molecular function   shift -0.063808  (-22.7%)   [absolute cells LEFT BLANK]
      cellular component   shift -0.046425  (-15.4%)   [absolute cells LEFT BLANK]
      biological process   0.2013197 -> 0.1754609  (-0.025859, -12.8%)
  and the prior-knowledge exclusion delta:
      without exclusion  0.2013197218518963 -> 0.1754608900289470
      with exclusion     0.1166555161572292 -> 0.1088951774478088
      delta              -0.0846642          -> -0.0665657
second number (mine): the blank cells are RECOVERABLE by division, and I recovered them --
      MF at `299e265` = 0.063808/0.227 = **0.281093** (0.280475..0.281713 given the
         3-sig-fig relative) -> at `80d705a` = **0.217285**
      CC at `299e265` = 0.046425/0.154 = **0.301461** (0.300485..0.302443)
         -> at `80d705a` = **0.255036**
      BP relative recomputed from the full-precision pair: **-12.8447%** (published -12.8%)
      exclusion-delta shrink recomputed: **21.38%** (published 21.4%)
  and the understatement factor of the commit's own claim. `git log -1 80d705a` says
  verbatim: "Metric-changing (**tiny, ~0.002 Fmax**) but strictly more correct."
      MF 0.063808 = **31.9x** that claim
      CC 0.046425 = **23.2x**
      BP 0.025859 = **12.9x**
date of evidence: 2026-07-27 -> window: pre-wipe, but ONE DAY before the reinstall
note (what a reader must not miss):
  1. **`0.2013197` (SCORER-PROVENANCE's BP-without-exclusion at `299e265`) and `0.2013`
     (the ledger's PK cell for EvalResult `cb77d55d`, the IA headline) agree to four
     decimals.** They are supposed to be different objects: one is an aspect on a
     no-exclusion frame, the other a knowledge category on a frame the dossier says applies
     TOI + PK-known exclusion. Per COLLIDING-A-NUMBER, two rows that should differ agreeing
     exactly is machinery, not luck. **I could not resolve this** -- the prediction file
     SCORER-PROVENANCE ran on is not named in the document, and neither file survives. It is
     the single highest-value follow-up on this slice, because if they ARE the same number
     then the ledger's PK column is a no-exclusion number and the whole "official harness"
     claim at `CAMPAIGN-DOSSIER.md:10` is wrong.
  2. SCORER-PROVENANCE's own conclusion (`:50-54`) is the load-bearing one and it is
     correct: "**The recorded per-cell tables and the leaderboard constants in the
     frame-parity test are `299e265` numbers.** They were not produced by the current branch
     tip and will not reproduce against it. A fresh install that resolves the branch will
     silently produce different numbers and no check will notice."
     The pin has since moved AGAIN, to `e937e0e` (2026-09-01), so the gap is now two
     corrections wide, not one.
  3. Publishing a table with the absolute cells blank for 2 of 3 aspects is
     COLLIDING-A-NUMBER rule 2 in miniature. They are recoverable by division, which is the
     proof that withholding them bought nothing and cost the reader a collision.

## A SECOND documented mass-deletion of evaluation results, 2026-04-23

verdict: CONFIRMED
first number: ADR-008, "Operational implication": "``EvaluationResult`` rows persisted
  before the fix carry the buggy ``cov`` / ``precision`` values and **must be discarded**
  (DELETE via ``/annotations/evaluation-sets/{id}/results/{rid}``; the endpoint cascades to
  MinIO artifacts). The launcher re-fires new runs automatically for any ``prediction_set``
  that loses its eval."
date of evidence: 2026-04-23 -> window: pre-wipe, pre-reinstall
note: combined with the conductor's 2026-06-22 deletion of the INT-8 regression, the
      experiment registry has now been shown to lose rows on at least THREE occasions:
      2026-04-23 (policy, mass), 2026-06-22 (one losing arm), 2026-08-27 (the wipe).
      Deletion was a designed operation, not an accident. Any claim of the form "we tried N
      things" or "this was the best of N" cannot be supported from the registry.

## plans/meta-reranker/: MR-0 and MR-1 landed; MR-2..MR-5 did not; the module is UNWIRED

verdict: **partially CONFIRMED (the ports exist), CONTRADICTED as a working fusion layer.**
The architecture beat-lafa-1 section 3 says every lever plugs into is real code that nothing
in the product calls.

what landed, with dates from `worktrees/protea-deploy` git log on
`protea/core/reranking/`:
    `d48b9bc` 2026-06-17 17:06  PROTEA #645  "meta-reranker foundation -- ports + registry
                                 + producer scorer adapters (MR-0+MR-1)"
    `d3a0638` 2026-06-17 19:41  PROTEA #646  base-evidence scorer ports
                                 (alignment / taxonomy / label_embedding / interpro /
                                 term_frequency)
    `9d90acb` 2026-07-11 17:25  PROTEA #729  LAFA + IA features jsonb -> typed columns
    `03714ec` 2026-07-12 16:20  PROTEA #733  ProtST text-to-GO producer + `ProtstTextScorer`
  Ten scorer adapters exist (`protea/core/reranking/scorers.py`): Alignment, Taxonomy,
  LabelEmbedding, Interpro, TermFrequency, KnnSimilarity, Classifier, SelfPrior,
  Association, ProtstText.

what did NOT land:
  - **MR-2, the trained per-category combiner over the score vector.** This is THE slice --
    `ARCHITECTURE.md:57-58` calls it "the single change that flips monolith -> stacked, and
    it directly fixes calibration/PK". The only combiners on disk are `PassThroughCombiner`
    and `LinearCombiner` in `protea/core/reranking/combiners.py`, whose own docstring says
    "Trivial reference :class:`Combiner` implementations (**MR-0 only**) ... Neither learns
    from data: the trained, OUT-OF-FOLD, calibrated per-category combiner is MR-2." Both
    `fit()` methods are literal no-ops ("No-op: the pass-through combiner has no
    parameters").
  - MR-3 (calibration layer), MR-4 (UI integration), MR-5+ (expansion) -- nothing.

**AND NOTHING CALLS ANY OF IT.** `grep -rn "core.reranking|default_scorer_registry|
ScorerRegistry|PassThroughCombiner|LinearCombiner|ProtstTextScorer"` over every `.py` in the
newest tree returns hits in exactly two places: inside `protea/core/reranking/` itself, and
`tests/test_reranking_ports.py`. **Zero production call sites.** No API router, no operation,
no producer, no evaluation path imports it.
where I looked: the entire `worktrees/protea-deploy` checkout at `a5de702` (2026-09-01),
  which is ahead of `repositories/PROTEA`; I searched by module path AND by every exported
  class name, so a call site under any import style would have been found.
date of evidence: module last touched 2026-07-12; absence verified against a 2026-09-01 tree
  -> window: post-wipe-current for the negative.
platform gap: MR-2 is the missing operation. Concretely: a training operation that fits a
  per-category combiner on OUT-OF-FOLD scorer outputs and writes a sealed artifact, plus a
  serving path that resolves scorers through `ScorerRegistry` instead of the monolithic
  booster. Neither exists. `reranker_model` having **0 rows** in the live database is the
  same fact seen from the database side: there is no registered fusion model at all, of
  either generation.
note: the ports are good code with careful docstrings and 400 lines of tests, and they are
      inert. This is COLLIDING-A-NUMBER rule 4 in a different key: a green test suite over a
      module that never enters the path. Compare the project's own recorded lesson
      "**Testing the declaration is not testing the path**". The architecture document is
      listed in `CATALOG.md:17` as "**ACTIVE -- live reference**". It is not live.

## The 0.391 target the whole campaign chased: what it is, and what it is worth held out

verdict: CONFIRMED as a document with a full breakdown; **its margin over TransFew is
DEDUCED-optimistic by the study's own held-out check, roughly by half.** The champion's own
`RESULTS.md` says so and nobody in `beat-lafa-1` carried the caveat forward as a number.

first number: `/home/xaxi/Thesis2/repositories/protea-reranker-lab/fullgo/RESULTS.md:7-18`
  (git-tracked; `32fc9ca` 2026-06-15, the trajectory landed over `45384e0..32fc9ca` on
  2026-06-15). Header (`:3`): "All numbers are f_micro_w (IA-weighted micro-F, mean over 3
  namespaces), sealed on the official 7401 frame with the exact published cafaeval harness."
      KNN composite (PROTEA baseline)          NK .412 LK .394 PK .165  mean .324
      classifier standalone                    NK .406 LK .389 PK .182  mean .326
      classifier + M2 anc2vec                  NK .414 LK .420 PK .195  mean .343
      + KNN-classifier ensemble (1 seed)       NK .446 LK .423 PK .204  mean .358
      + seed-avg classifier + self-prior       NK .464 LK .465 PK .215  mean .381  "ties #1"
      + cross-aspect association + 5-seed      NK .472 LK .481 PK .217  mean .390  "outright #1"
      **+ 7-seed avg  CHAMPION**               NK .477 LK .482 PK .215  **mean .391**
      FunBind (#2)                             NK .441 LK .451 PK .205  mean .366
      TransFew (#1)                            NK .428 LK .485 PK .230  mean .381
second number (mine): all nine rows recompute as the unweighted mean of their three
  category cells, to rounding -- .32367/.32567/.34300/.35767/.38133/.39000/.39133/.36567/
  .38100. So **0.391 is a mean over three KNOWLEDGE CATEGORIES, each of which is itself a
  mean over three namespaces: it is a macro-mean of nine cells**, exactly like beat-lafa-1's
  0.3745. The two ARE commensurable with each other. Neither is commensurable with the
  reranker's +0.1353 frame (`max_terms=500`, `th_step=0.001`, no `-known`).

**THE MARGIN, RE-DERIVED FROM THE STUDY'S OWN HELD-OUT SPLIT.**
`RESULTS.md:24-43` is unusually candid: "The one residual exposure is *which levers to
include* being read off the sealed TEST mean (adaptive feature selection across a handful of
binary choices)." It then reports `select_cv.py`, which re-decides the levers on a 50/50
protein split WITHIN SELECT, never touching TEST:
      KNN + 7-seed clf + self-prior (no association)   0.4424
      + association v1                                  0.4450   (+0.0026)
      + association v1, 7-seed avg                      0.4477   (+0.0027)
  and states the rule that makes the comparison legal: "**only the cross-config delta
  transfers**".
  Applying that rule, which the document states and then does not apply:
      the same two changes on TEST moved 0.381 -> 0.391 = **+0.0100**
      the same two changes held out inside SELECT are  **+0.0053**
      TEST overstates by **1.89x**
      champion re-estimated on held-out deltas = 0.381 + 0.0053 = **0.3863**
      versus TransFew 0.381 -> margin **+0.0053, not +0.0100**
  So "OUTRIGHT #1, ahead of TransFew" is a +0.005 margin under the study's own leakage
  discipline, on a nine-cell macro-mean, with no interval anywhere.

**AND THE MARGIN IS ENTIRELY ONE CELL-GROUP.** My decomposition of the champion against
TransFew, per category:
      NK  0.477 vs 0.428  -> champion **wins by +0.049**
      LK  0.482 vs 0.485  -> champion **loses by -0.003**
      PK  0.215 vs 0.230  -> champion **loses by -0.015**
  NK alone contributes +0.0163 to the mean; LK and PK together give back -0.0060. **The
  entire "we beat #1" claim is the NK cell**, which is the SERVED population but only ~5% of
  a window. `RESULTS.md:20-22` says this in prose ("NK 0.477 is #1 by a wide margin ... PK
  0.215 still trails TransFew (0.230) but the mean wins") -- it is honest, and it is exactly
  the shape the project's own memory records for the later 0.391 champion
  (`project_offline_champion_0391_is_three_cell`: "win NK, tie LK, lose PK").
date of evidence: 2026-06-15 -> window: pre-wipe, pre-reinstall
frame: LAFA `Sep_2025_Mar_2026` 7401 frame; f_micro_w; fit on SELECT 220->227, sealed once
  on 227->230; "exact published cafaeval harness". The cafaeval pin is not recorded in the
  file, and the PK coverage fix (`cec8ccd`) had landed 2026-04-23, so this is post-fix.
platform gap / reproducibility: `fullgo/ensemble_seal.py` survives in git, and its docstring
  is a complete recipe. But its INPUT paths are:
      /tmp/select_knn_composite.tsv   /tmp/sel_m2_seedavg7.tsv   /tmp/select_gt_{cat}.tsv
      /tmp/v220_exp_aspect.tsv        /tmp/canon_composite.tsv   /tmp/m2_seedavg7_pred.tsv
      /tmp/v227_exp_freq.tsv          /tmp/select_selfprior_leaf.tsv
      /tmp/goa_nonexp_7401.tsv        /tmp/assoc_sel.tsv         /tmp/assoc_7401.tsv
  **Eleven of its thirteen inputs are /tmp paths on the old machine.** The two that are not
  (`CAFA_forever/data/releases/Sep_2025_Mar_2026/groundtruth_*`) DO survive: I confirmed
  `/home/xaxi/Thesis2/CAFA_forever/data/releases/` holds `Sep_2025_Mar_2026`,
  `Sep_2025_Dec_2025`, `Sep_2025_Nov_2025`, `Nov_2025_Dec_2025`, `Nov_2025_Mar_2026`,
  `Dec_2025_Mar_2026` plus `catalog.json`. Its OUTPUT path
  `/home/frapercan/Thesis2/storage/fullgo_models` does not exist.
note: the dossier's summary of this ("frame-optimistic and its source files are DELETED")
      is true but loses the two facts that matter: the optimism is QUANTIFIED at 1.89x by
      the study itself, and the ground truth half of the inputs SURVIVED.

## The dossier's artifact map (section 8) is almost entirely dead

verdict: CONFIRMED
I checked every artifact named in `CAMPAIGN-DOSSIER.md:186-205` with a filesystem-wide
`find` (excluding /proc and .git internals):
      storage/fullgo_models/                       ABSENT (the directory itself)
      ensemble_gbm_{NK,LK,PK}.txt (0.391 boosters) ABSENT
      feature_spec.json                            ABSENT
      native_boosters_both_serve/                  ABSENT
      native_boosters_selfpriorfix_serve/          ABSENT
      native_boosters_clean15/                     ABSENT
      native_boosters_pk_s2/                       ABSENT
      native_boosters_nklk_s2/                     ABSENT
      selfprior_ia_experiment/{train,eval}_overlay.npz   ABSENT
      {train,eval}_descprior.npz                   ABSENT
      selfprior_fix_data/nonexp_annotations.tsv    ABSENT
      /tmp/canon_composite.tsv                     ABSENT (declared deleted already)
      IMPROVEMENTS-BACKLOG.md, RESUME_2026-06-21.md ABSENT
      the three cited memory files                 ABSENT
  What DID survive, all of it code in git, none of it data:
      `repositories/protea-reranker-lab/research/fullgo_models/` -- 29 entries including
        `train_clean15.py`, `train_pk_s2.py`, `train_nklk_s2.py`, `build_descendant_prior.py`,
        `train_score_descprior_pk.py`, `l2_softprop_pk.py`, `train_native_boosters.py`,
        `score_azucar_validation.py` -- i.e. **every script the dossier names**
      `repositories/protea-reranker-lab/fullgo/` -- the 0.391 recipe, README, REPRODUCE.md,
        RESULTS.md, config.yaml, container/
      `repositories/protea-reranker-lab/results/clean_227230/` -- the reranker study
      the `native_boosters_v5/` and `native_boosters_azucar/` directories exist but hold
        only scripts and a README; **no model files**
note: the split is total and clean: **procedures survived, artifacts did not.** Not one
      trained booster, not one overlay, not one dataset. So even before the registry wipe,
      no beat-lafa-1 number could have been reproduced from artifacts -- only re-derived by
      re-running scripts against data that no longer exists.

## The supersession was DECLARED and never EXECUTED: beat-lafa-1 is still "ACTIVE - canonical" on main today

verdict: **CONTRADICTED between two canonical documents, and the contradiction is live.**
first number: `plans/E2E-CANONICAL-RUN.md:12-17` --
  "It SUPERSEDES, for the definition of the scientific run, the June roadmaps
   (`ROADMAP-THESIS-10.md`, `THESIS-FINISH.md`, **`beat-lafa-1/`**). Those carried the old
   window convention (SELECT 220->227 / FINAL 227->230, a mixed-metric story) and the
   pre-scale corpus. **They move to `plans/archive/` for provenance**; their governing
   principles are inherited verbatim below."
second number: I checked `origin/main` at `d06f75d`, **2026-09-01 22:42** (the newest
  commit on the plan store):
   - `git ls-tree -d origin/main plans/` still lists **`plans/beat-lafa-1`** at the top
     level. `plans/archive/` holds lafa-improve, lafa-levers, lafa-number-one,
     reranker-vnext, score-ablation, sdr, thesis-cuts -- **beat-lafa-1 is not among them.**
   - `git show origin/main:plans/CATALOG.md` line 16 still reads:
     "| **beat-lafa-1** | **ACTIVE -- canonical** | The current campaign to surpass LAFA #1
      ... Best confirmed native = **0.3745** (EvalResult `b21b187c`). Bottleneck = PK
      precision. |"
   - `plans/beat-lafa-1/` has not been touched by a commit since `13b7eeb`,
     **2026-06-22 03:18**, "plan(store): harmonize plan store + status catalog (beat-lafa-1
     canonical) (#194)".
date of evidence: supersession declared 2026-07-28; non-execution verified against
  2026-09-01 -> window: post-wipe-current
note: so the plan store simultaneously says beat-lafa-1 is superseded and that it is the one
      canonical research campaign, and the catalog's entry advertises a dead EvalResult id
      as current state. **A reader who opens `CATALOG.md` first -- which is what it is for,
      "single entry point to the plan store" -- gets the June picture with no warning.**
      This is the cheapest fix on the slice and it has been open for five weeks.

## A 0.3745 that is NOT the campaign's 0.3745

verdict: CONFIRMED numeric coincidence, flagged so nobody merges them
`plans/rungs.yaml:99` carries "near-identical >90   best 0.3745  worst 0.3664   spread
0.0081". That is a per-cell task metric at K=1 in the NO-KNOWLEDGE cell, split by sequence
identity band, from the 2026-08-20 stratification lesson -- an entirely different object
from `CAMPAIGN-DOSSIER.md`'s macro-mean f_micro_w of 0.3745 on the 7401 LAFA frame.
note: `0.3745` now appears in the plan store as two unrelated quantities. Anyone grepping
      the number will find both.

## Is any of this alive in the current window? NO.

verdict: CONFIRMED, and this is the closing fact of the slice
where I looked: `find /home/xaxi/Thesis2/storage -newermt "2026-08-27" -type f`. Everything
  post-wipe is `calibration-study/` (scripts, 2026-09-01), `ontology-drift/`
  (2026-08-27), worker logs and `node-sync.state`. **Nothing touches the LightGBM reranker,
  the beat-lafa-1 levers, the LAFA 7401 frame or the fullgo champion.**
`find / -name "*.lgb" -o -name "*booster*.txt" -o -name "*gbm*.txt" -o -name "*.lightgbm"`
  (excluding /proc, site-packages, .git internals): **zero results.** There is no trained
  reranker artifact of any generation on this machine.
corroborating independent source, project memory
  `project_reranker_floor_and_the_query_dependence_test_2026_08_19.md`:
  "**There is no re-ranker here to measure.** `reranker_model` 0 rows, `dataset` 0 rows, and
   the artifact store holds no booster and no parquet, only evaluation artifacts, ontology
   snapshots, ground truth and accretion. The model that reached first place in Experiment
   13 lived on the previous machine and `storage/` was deliberately not restored."
note: this closes the loop on the slice's brief. `reranker_model` having 0 rows is not a
      database accident; it is the last visible consequence of a chain -- artifacts never
      registered, procedures kept in scratchpads, a registry that was designed to be
      deletable -- that has now removed every trained fusion model this project ever built,
      in both the platform generation (the S2 trio `198baf99/68f3232c/f0669e41`) and the lab
      generation (the `clean_227230` lambdarank trio and the `fullgo` 0.391 ensemble).

---

# SUMMARY OF THE SLICE

**1. Six of the seven levers were never run.** Only L2 (soft Pmin/Pmax) executed, and it was
refuted (-0.0026 on the official recipe, PK reversed from +0.0141 to -0.0126). L1, L3, L4,
L5, L6 have no implementation anywhere on this machine; L7 exists only as different work in
a different slice. The campaign's own highest-EV lever, L6, was blocked by a platform gap
the dossier names (the export aggregates neighbour-level data away) and then died on
2026-06-23 when a conductor could not deliver the user's own unsent keystroke.

**2. `b21b187c` and its 0.3745 are dead, and CATALOG.md still advertises them.** No row, no
dump, no artifact; every surviving mention is an echo of one 2026-06-21 document. The
7401-target query FASTA is gone, so the number cannot be re-measured even if the registry
were intact. The ledger it sits in was already selectively pruned (a losing INT-8 arm at
0.3462 deleted 2026-06-22; a mass discard of pre-fix PK rows mandated 2026-04-23).

**3. The reranker's +0.1353 and +0.108 both reproduce exactly, and the frame warning is
right but incomplete.** Frame-safe NK/LK part +0.1083; frame-contaminated PK part +0.1894,
1.75x larger, supplying 46.7% of the headline from 33% of the cells. "Frame-safe" is itself
a deduction from the NK/LK definitions that nobody measured. The study's own leakage check
recorded a 7.4% train/eval positive-pair overlap and wrote its verdict to a /tmp scratchpad
that no longer exists.

**4. The campaign's founding diagnosis is the most likely defect.** "PK is precision-limited,
NOT recall-limited: recall ~0.25, precision ~0.15, coverage 1.0" reproduces from ADR-008's
PK-**BPO** row on the **220->230** benchmark in **Fmax** -- one cell of nine, the wrong
window, the wrong statistic -- with coverage **0.97 rounded to 1.0**, on a metric that
PROTEA did not publish at the operating point until PR #804 on 2026-08-20 (before which
"coverage" was `cov_max`, the max over all thresholds). Every lever priority follows from it.

**5. The measuring instrument moved twice around the campaign** (`cec8ccd` 2026-04-23 PK
coverage; `80d705a` 2026-06-25 propagation fill, whose commit message calls its own effect
"tiny, ~0.002 Fmax" when it is 12.9x to 31.9x that), and again on 2026-09-01 (`e937e0e`).
The campaign's numbers are `299e265` numbers and will not reproduce.

**6. The meta-reranker is inert.** MR-0/MR-1 ports and ten scorer adapters landed 2026-06-17;
MR-2 (the trained combiner, the slice that "flips monolith to stacked") never did, both
combiners have no-op `fit`, and **nothing outside the module and its own tests imports it**
in the 2026-09-01 tree.

**7. Procedures survived, artifacts did not.** Every script the dossier names is in git;
not one booster, overlay, dataset or trained model is on disk, in either generation.
