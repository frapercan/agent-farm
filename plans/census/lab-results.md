# Slice: lab-results

Auditor slice key: `lab-results`.

Scope: `repositories/protea-reranker-lab` plus lab outputs under
`/home/xaxi/Thesis2/storage/` (encoder-study, encoder, probe, rescue,
scorecard, ontology-drift, calibration-study, throughput). Establish the
RESULTS: every number this lab produced that is cited anywhere in `plans/`
or in the memory store. For each: does the artifact still exist, what is its
date against the 2026-08-27 registry wipe, and was it produced in a frame
commensurable with the platform evaluation?

Deliverable: what of the lab is reproducible and what died.

Started: 2026-09-02.

---

## INVENTORY: what physically exists under storage/ for the lab

verdict: CONFIRMED (the documents saying storage was not restored are wrong for these trees)

```
5.6M  calibration-study/      (README + scripts + artifacts, mtime 2026-09-01 20:34)
2.6G  encoder/                (2026-08-10..12, the published sparse encoder bundle)
16G   encoder-study/          (2026-08-19..26, 115 numbered scripts, 340 artifacts)
82M   logs/                   (to 2026-08-30)
60M   ontology-drift/         (2026-08-27)
347G  probe/                  (2026-08-18..20, per-residue embedding banks)
3.7G  rescue/                 (2026-08-02, pgdata/minio salvage)
300K  scorecard/              (2026-08-21, a CV/scorecard, NOT a research artifact)
1.4M  throughput/             (2026-07-29..30)
48K   worktree_salvage/       (2026-08-19)
```

date of evidence: file mtimes, `ls -la`, `du -sh`
note: **scorecard/ is not lab output.** It contains
`1-Profile-PerezCanales.pdf`, `2-Scorecard-PerezCanales.tex`,
`Scorecard-FranciscoMPerezCanales.docx` -- a personal CV/profile document set
dated 2026-08-21. It produced no research number. Anyone reading the slice
list and expecting a "scorecard" of results will find a curriculum vitae.
Removing it from the lab-results question outright.

## THE DATE WALL: the entire encoder-study predates the registry wipe

verdict: CONFIRMED
first number: registry wipe 2026-08-27 (slice brief; 93 evaluation_result /
  19 prediction_set rows, all 2026-08-27..30)
second number: newest artifact in
  `/home/xaxi/Thesis2/storage/encoder-study/artifacts/` is
  `114_cross.json` / `114_run.out`, mtime **2026-08-26 16:49**. Newest script is
  `115_panel_populations_experimental_baseline.py`, mtime 2026-08-26 21:53,
  and **it has no artifact** -- script 115 exists, output 115 does not.
date of evidence: 2026-08-19 .. 2026-08-26 -> window: **pre-wipe** for ALL of it
note: every single encoder-study number is pre-wipe. Not one of the 340
artifacts was produced after the registry was wiped. So no encoder-study
number has a surviving platform-side evaluation_result to be collided
against; the platform rows that exist are all 2026-08-27..30 and were
produced after the last lab artifact. **The lab and the platform registry do
not overlap in time at all.** Every lab-vs-platform comparison in the
documents is therefore a comparison against numbers that no longer exist.

## The lab's headline metric is PURITY, the platform's is Fmax. The whole arm table is in the incommensurable frame.

verdict: CONFIRMED
first number: `storage/encoder-study/RESULTS.md:1-60` -- 44 arms ranked by
  "purity", defined there as "the mean functional similarity to the ten
  nearest neighbours, over GO closures propagated by is_a and part_of",
  held out on 2646 proteins. `residue-k4` 0.2570, `champion-frozen` 0.2284,
  difference **+0.0287** (the standing recipe over the deployed encoder).
second number: the platform registry evaluates Fmax via cafaeval. The memory
  file `project_confirmation_set_domain_not_selection_2026_08_19.md` records
  "**Purity is NOT a reliable proxy for Fmax**". So the lab's entire ranked
  table of 44 arms is in a metric the project has itself recorded as not
  converting to the platform's metric.
date of evidence: RESULTS.md mtime 2026-08-23 16:10, arm artifacts 2026-08-19
  -> window: **pre-wipe**
frame: purity @ k=10 neighbours; GO closure propagated by is_a + part_of;
  held-out 2646 of the evaluation delta; 776 fit proteins removed; paired
  bootstrap; **resolution floor 0.0013** declared in the document itself.
  NO -known exclusion, NO IA weighting, NO th_step, NO aspect split, NO
  category split. It is not an Fmax frame at all.
population: 2646 proteins "of the evaluation delta", UNSTRATIFIED by
  category or aspect. The nine cells are not separated anywhere in the arm
  table.
platform gap: an operation that scores a candidate encoder on the platform's
  own Fmax grid over the nine cells. None of the 115 lab scripts writes to
  the database; every one writes a `.json`/`.npz` into
  `storage/encoder-study/artifacts/`.
note: the document's own later sections RETRACT its top two rows (see next
  finding). The arm table is still the part that gets quoted.

## RESULTS.md retracts its own headline twice, in the same file

verdict: CONFIRMED
first number: `+0.0358` (order: sparsify per residue vs pooled at equal
  training) and `+0.0287` (the same vs deployed), `RESULTS.md` "What each
  axis settled" table.
second number: same file, section "**Superseded 2026-08-20: the order does
  not survive a real bank**": on the full cell of 3,031 queries against
  85,982 donors the residue/pooled/dense arms give
  budget 10: 0.6017 / 0.6009 / 0.6029; budget 25: 0.6253 / 0.6307 / 0.6301;
  budget 50: 0.6781 / 0.6799 / 0.6808. "Nine aggregate comparisons and
  twenty-four by identity band, and not one separates." Largest difference
  anywhere +0.0138 with interval [-0.001, +0.028].
  Then section "**Retracted 2026-08-23: the best backbone had read the
  answer**" removes ProtST and drops the twilight backbone spread
  **0.0842 -> 0.0625**.
date of evidence: 2026-08-19 (measured), superseded 2026-08-20, retracted
  2026-08-23 -> window: **pre-wipe** throughout
frame change that does the retracting: purity-on-a-probe-shaped-bank of 640
  NK proteins -> reachability at matched candidate budget on 3,031 queries
  vs 85,982 donors, release-220 donor closures, twins excluded.
  **The absolute level moves with the bank: 0.665 against the platform donor
  set vs 0.602 against this one** (RESULTS.md's own words). That is a stated,
  measured 0.063 frame offset between lab bank and platform bank on the same
  quantity.
platform gap: there is no operation that builds the donor bank the lab used
  (85,982 first-hand-evidence donors at window start). The bank exists only
  as `artifacts/89_bank_codes.npz` (2.1 GB, 2026-08-20 10:05).
note: **the retraction is INSIDE the file that carries the claim.** Anyone
  quoting the arm table without reading to the end of RESULTS.md quotes a
  superseded number. Check every citation of +0.0287 / +0.0251 / 0.0842 for
  whether it carries the supersession.

## The lab states its own incommensurability rule, in writing, on 2026-08-19

verdict: CONFIRMED
first number: n/a -- this is the frame rule itself.
quote: `storage/encoder-study/DEPLOYMENT-AUDIT.md` opening section, "The
  constraint that governs how any of these numbers may travel":
  "The evaluation sets of this run and of the previous campaign are not
  established to be comparable, so a sentence of the form 'this beats the
  previous campaign' is not a claim that can be checked, whichever direction
  it points... A number from this study may not be placed in a table beside a
  number from the earlier campaign, however alike the two metrics look. And
  work proceeding in parallel on the other machine, on dense embeddings over
  its own evaluation set, produces numbers that are equally incomparable."
  Restated in `CAMPAIGN-LADDER.md`: "Figures from two frames may not be
  placed in one table, however alike the metrics look, and this applies
  between machines of this project as much as between campaigns."
date of evidence: 2026-08-19 -> window: pre-wipe
note: **the defect class the requester asked me to hunt was named by the lab
  itself, in the lab's own documents, before any of the numbers travelled.**
  So every instance I find below is a violation of a rule that was written
  down in the same directory. That is the finding: the rule exists and is
  not enforced by anything mechanical.

## The lab's OWN audit says its purity screen is an order of magnitude too generous

verdict: CONFIRMED -- and this is the cleanest recorded instance of the
  incommensurable-frame defect in the whole lab.
first number: `DEPLOYMENT-AUDIT.md` "What not to do":
  "Do not set a rung gate from a purity number measured on a private screen.
  That screen reports the encoders gaining **0.0910** where the metric's own
  definition gives **0.007 to 0.015**, an order of magnitude, and a gate set
  from it would be an order of magnitude too generous."
second number: same ratio restated independently in `CAMPAIGN-LADDER.md`
  stage 2: "that screen reports the same encoders gaining 0.0910 where the
  metric's definition gives 0.007 to 0.015".
  Ratio: 0.0910 / 0.011 = **8.3x**.
date of evidence: 2026-08-19 -> window: pre-wipe
frame A (the generous one): purity, 10 nearest neighbours, closure propagated,
  no -known exclusion, no aspect split, probe-shaped bank.
frame B (the honest one): "the metric's own definition", i.e. neighbour
  quality measured against WHAT THE QUERY GAINED, -known applied.
population: the encoders, on the study's confirmation set.
platform gap: no operation converts a lab purity number into a platform Fmax
  number; the conversion is a lab script only (`scripts/32_conversion_curve.py`).
note: the 0.0910 is the number that reaches the memory store. See the memory
  file `project_confirmation_set_domain_not_selection_2026_08_19.md`, whose
  index line reads "in-domain training buys **+0.0910 of purity**" -- correct
  as written, but the index line for
  `project_retrieval_converts_at_slope_one_2026_08_19.md` reads "Under the
  study's own screen the gain was +0.0910", which is the same number carried
  forward. Any downstream reader who takes 0.0910 as an accuracy figure is
  8x out.

## Two DIFFERENT re-ranker ceilings, both from this lab, both in circulation

verdict: FRAME-UNKNOWN (pending receipt check below)
first number: `DEPLOYMENT-AUDIT.md`: "Re-ranking a shortlist of a thousand is
  worth **+0.1747** in the serving cell against a perfect re-ranker, and a
  crude one built here recovers two per cent of that in the serving cell and
  ten to thirteen elsewhere." Same in `CAMPAIGN-LADDER.md` stage 3, with the
  depth curve "88% at a thousand, 91% at three thousand, 95% at ten thousand".
second number: memory
  `project_reranking_beats_the_encoder_2026_08_19.md` index line:
  "**Re-WEIGHTING, not re-ordering, is worth +0.0725**... permuting a fixed 30
  is worth EXACTLY 0. Floor 0.0032, ceiling **0.0725**, and the ceiling reads
  the answer."
  0.1747 vs 0.0725 is a factor of **2.4** for "the re-ranker ceiling".
date of evidence: both 2026-08-19 -> window: pre-wipe
note: these are almost certainly two different frames (shortlist depth 1000
  vs a fixed 30; and possibly purity vs Fmax) but BOTH are quoted as "the
  room the re-ranker has". Receipt chase below.

## "Retrieval converts to Fmax at slope ~1" is a TWO-POINT ORACLE EXTRAPOLATION, not a measured conversion

verdict: **DEDUCED-NOT-MEASURED** (the strongest finding in this slice)
first number: "the conversion runs at **slope 0.94**"
  -- `storage/encoder-study/DEPLOYMENT-AUDIT.md:22`,
     `storage/encoder-study/CAMPAIGN-LADDER.md:53`,
     `storage/encoder-study/PRODUCTION.md:110` ("a **median slope of 0.94**").
  Memory index line: "**Retrieval converts to Fmax at slope ~1; the gains were
  just tiny** ... no dead stretch"
  (`project_retrieval_converts_at_slope_one_2026_08_19.md`).
second number: I refit the slope myself from the receipt
  `storage/encoder-study/artifacts/conversion_curve.json` (9 cells x 5 arms:
  dense, champion, recipe-pool, recipe-delta, oracle). Ordinary least squares,
  no numpy, per cell:

  | cell | slope, all 5 pts | slope, 4 REAL arms only | real-arm nq span |
  |---|---:|---:|---:|
  | NK_MFO | 0.841 | 0.348 | 0.0301 |
  | NK_BPO | 1.030 | 0.280 | 0.0165 |
  | NK_CCO | 0.661 | 0.281 | 0.0266 |
  | LK_MFO | 0.830 | **1.557** | 0.0226 |
  | LK_BPO | 0.948 | 1.296 | 0.0248 |
  | LK_CCO | 0.637 | **-0.063** | 0.0130 |
  | PK_MFO | 1.601 | 0.769 | 0.0094 |
  | PK_BPO | 2.121 | 1.350 | 0.0056 |
  | PK_CCO | 1.306 | 0.745 | 0.0075 |

  median with oracle = **0.9482** (reproduces the published 0.94 exactly)
  median WITHOUT the oracle = **0.7447**, and the per-cell values run
  **-0.063 to +1.557**.
  The dense->oracle two-point line alone gives median **0.9656**.
date of evidence: 2026-08-19 (`scripts/32_conversion_curve.py`, mtime
  2026-08-19 11:16) -> window: **pre-wipe**
frame: neighbour quality = mean functional similarity of the returned
  neighbours; Fmax on "the official frame" with `PK_known` exclusion read from
  `CAFA_forever/data/releases/Sep_2025_Mar_2026/groundtruth_PK_known.tsv`;
  KNN=30; THR = arange(0.02, 1.0, 0.02) so **th_step = 0.02**; DICT 2048,
  K_SEQ 128, K_RES 4. Nine cells kept separate. This IS an Fmax frame, and it
  is the only lab artifact I found that is.
population: the LAFA eval split, nine cells; per-cell n from
  `oracle_ceiling.json`: NK 50/88/70, LK 54/193/96, PK 410/1579/513.
platform gap: nothing. This is a lab script reading `.pkl` gold and probe
  `.npy` files; there is no operation that computes a conversion curve.
note: **the four real arms span 0.006 to 0.030 of neighbour quality; the
  oracle sits 0.28 to 0.50 away.** All the leverage in the fit is the oracle
  point. The slope is therefore a line drawn from where the system is to
  where an answer-reading oracle is, and it has never been measured in the
  interval an encoder can actually move through. The script's OWN docstring
  says the opposite of the conclusion it is cited for:
  "the conversion ... is not a ceiling, it is a curve **with a dead stretch at
  the near end**, and the useful question is where that stretch ends"
  (`scripts/32_conversion_curve.py:4-7`). The memory file title asserts "no
  dead stretch". The receipt cannot distinguish the two: with a 0.03 span and
  four points it has no power to see a dead stretch, and on the four real arms
  one cell (LK_CCO) already comes out NEGATIVE.
  **Everything downstream that gates on "the gain needed is 0.024 to 0.037"
  inherits this.** That gate is 1/slope times a target Fmax delta, so it is
  an oracle-anchored quantity presented as a measured requirement.

## The +0.1747 re-ranker ceiling reproduces exactly, but "ten to thirteen elsewhere" does not

verdict: first half CONFIRMED, second half **CONTRADICTED by its own receipt**
first number: `DEPLOYMENT-AUDIT.md` and `CAMPAIGN-LADDER.md`: "Re-ranking a
  shortlist of a thousand is worth **+0.1747** in the serving cell against a
  perfect re-ranker, and a crude one built here recovers **two per cent** of
  that in the serving cell and **ten to thirteen** elsewhere."
second number: from `artifacts/real_reranker_floor.json` (receipt for
  `scripts/39_real_reranker_floor.py`, mtime 2026-08-19 13:17), recomputed by
  hand:

  | cell | n | plain | reranked_cosine | gain | ceiling_1000 | headroom | recovered |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | NK | 208 | 0.5601 | 0.5634 | 0.0032 | 0.7348 | **0.1747** | **1.86%** |
  | LK | 343 | 0.5205 | 0.5498 | 0.0293 | 0.7447 | 0.2242 | **13.05%** |
  | PK | 2502 | 0.1612 | 0.1857 | 0.0245 | 0.6267 | 0.4655 | **5.26%** |

  0.7348 - 0.5601 = 0.1747 exactly. The headline reproduces.
  But "recovers ... ten to thirteen elsewhere" is **LK 13.05% and PK 5.26%**.
  The true range is five to thirteen. PK is overstated by a factor of 2.5.
date of evidence: 2026-08-19 -> window: **pre-wipe**
frame: Fmax-scale, pooled over aspects (NK plain 0.5601 sits between the
  three NK aspect values in `oracle_ceiling.json`: 0.633/0.435/0.663).
  Shortlist depth 1000. Three categories, **aspects pooled** -- so this
  number is NOT in the nine-cell frame the project's own norm requires.
population: NK 208, LK 343, PK 2502. Note NK is 6.7% of 3053, consistent
  with the "serving population is ~5%" rule.
platform gap: no re-ranker exists in the platform at all
  (`DEPLOYMENT-AUDIT.md`: "**There is no trained re-ranker in this
  environment**: the registry holds no model, the store holds no booster and
  no frozen dataset").
note: the `reranked_own` column tells a different story again -- PK
  `reranked_own` 0.2063 gives (0.2063-0.1612)/0.4655 = **9.7%**, which is
  probably where "ten" came from. So the sentence mixes the cosine-reranked
  number for one cell with the own-reranked number for another. Two columns,
  one range.

### addendum: the re-ranker floor table is a MAX OVER TWO WEIGHTING ARMS, per cell

verdict: CONFIRMED
first number: memory
  `project_reranker_floor_and_the_query_dependence_test_2026_08_19.md` table:
  NK +0.0033 (2%), LK +0.0293 (13%), PK +0.0451 (10%).
second number: `artifacts/real_reranker_floor.json` holds FOUR re-ranked
  columns per cell (`reranked_cosine`, `reranked_own`, `reranked_uniform`,
  and two baselines `plain` / `plain_uniform`). The memory's NK and LK rows
  are `reranked_cosine`; its PK row is `reranked_own`. The file's own stored
  `gain` field is cosine-minus-plain for all three, giving PK **+0.0245 /
  5.26%**, not +0.0451 / 10%.
date of evidence: 2026-08-19 -> pre-wipe
note: the memory DECLARES the switch ("in the prior-knowledge cell the
  model's own score is a better transfer weight than the code cosine"), so it
  is honest -- but the number that travels is still a per-cell maximum over
  two arms with no selection penalty, and `DEPLOYMENT-AUDIT.md` reproduces
  the range "ten to thirteen" without the declaration. The receipt's own
  `recovered` field says 1.86 / 13.05 / 5.26.

## "There is no dead stretch" is a deduction, and the memory file says so in its own title

verdict: **DEDUCED-NOT-MEASURED**
first number: memory
  `project_retrieval_converts_at_slope_one_2026_08_19.md` description field:
  "Neighbour quality converts to Fmax at slope ~0.94, so **there is NO dead
  stretch**." Body: "one unit of neighbour quality is worth about one unit of
  Fmax **all the way to the oracle**."
second number: the receipt has FOUR points inside a 0.006-0.030 window and one
  oracle 0.28-0.50 away. A dead stretch, if it exists, lives inside that
  0.03 window and the fit has no points to see it with. On the four real arms
  alone LK_CCO's slope is **-0.063** and NK_BPO's is **0.280** -- i.e. in
  three of nine cells the near-range slope is under 0.3, which is exactly
  what a dead stretch looks like.
note: the retracted hypothesis and the retraction rest on the same four
  points. "No dead stretch" is a property of a line drawn to an oracle, not
  a measurement of the near end. The script's docstring
  (`scripts/32_conversion_curve.py:4-7`) still asserts the dead stretch
  exists and that finding where it ends is "the useful question"; the
  conclusion filed in memory says it does not exist. **Same run, opposite
  conclusions, both on disk.**

# REPRODUCIBILITY: what the encoder-study is actually made of

## The 115 encoder-study scripts are in NO repository

verdict: CONFIRMED
first number: 115 python scripts + 15 chain shell scripts in
  `/home/xaxi/Thesis2/storage/encoder-study/scripts/`, mtimes 2026-08-19
  00:16 through 2026-08-26 21:53.
second number: `cd /home/xaxi/Thesis2/repositories/protea-reranker-lab &&
  git log --oneline --all -- '*encoder-study*'` returns **nothing**;
  `find /home/xaxi/Thesis2/repositories -name '32_conversion_curve.py' -o
  -name '39_real_reranker_floor.py' -o -name '89_arms_retrieval_by_band.py'`
  returns **nothing**. `storage/encoder-study/` is not itself a git repo (no
  `.git`).
where I looked: all 8 repos under `repositories/`, every branch
  (`--all`), and the storage tree itself.
date of evidence: repo HEAD `66403930` 2026-08-17 12:49 -- i.e. the repo was
  frozen **two days before the study started** -> window: pre-wipe
platform gap: **MURO.** Nothing in PROTEA's operation registry produces any
  of these. Every one writes a `.json`/`.npz`/`.pkl` to a local directory.
note: this is the single largest reproducibility exposure in the slice. The
  study that produced the layer axis, the order axis, the architecture null,
  the quantisation result, the conversion slope and the re-ranker floor is
  130 loose files on one disk.

## The library those scripts import is COMMITTED BUT NEVER PUSHED: 16 commits, one disk

verdict: CONFIRMED
first number: **85 of 115** scripts begin
  `sys.path.insert(0, "/home/xaxi/Thesis2/worktrees/lab-bundle/src")`
  (counted with `grep -ho 'sys.path.insert(0, "[^"]*")' *.py | sort | uniq -c`).
  Four more import `worktrees/sparse-encode`, three `protea-backends/src`,
  two `repositories/PROTEA`, one each `worktrees/pooled-uri` and
  `worktrees/pooled-order`.
second number: `worktrees/lab-bundle` is on branch `feat/gate-bundle-loader`
  at **d1ee10ba2be25ce2799a188e8573ee88b5d78c82** (2026-08-19 09:10).
  `git merge-base --is-ancestor d1ee10ba HEAD` -> **NO, not in develop**.
  `git merge-base --is-ancestor d1ee10ba origin/feat/gate-bundle-loader` ->
  **NO**. origin's tip of that branch is `0b2296bcea21c2da82badf738a7f7878fd72f221`.
  `git rev-list --count 0b2296b..d1ee10ba` = **16 commits that exist on no
  remote**, including:
    d1ee10b fix(lab): the four type holes and the refactor leftover CI found
    2d2b5ae feat(probe): keep the window boundaries...
    72cc278 feat(training): split the backward...
    a04f000 feat(architecture): the encoding routes as one object...
    afd0e7f feat(retrieval): measure whether a dictionary can serve as an index...
    5aba426 feat(sweep): report every score per length band...
    014e2fe fix(sweep): stream the probe from disk... after two OOM kills
    af04d64 feat(sweep): run the grid over the probe... paired interval on every gap
    ce2fecf feat(probe): extract per-residue, per-layer representations...
    f8a04e1 feat(probe): chunk long proteins instead of truncating them
    0021996 feat(probe): select and size the bounded residue probe...
    c817e20 feat(proxy): rebuild the functional screen, and close the two ways it can lie
    1415b9e feat(mechanism): the variant space...
    4040e69 feat(sparse): the order axis as operations...
  `src/protea_reranker_lab/probe_store.py` -- the module that reads every
  `storage/probe/*.npy` bank -- **does not exist on develop**
  (`ls src/protea_reranker_lab/probe_store.py` in the repo: No such file).
  It exists on `origin/feat/gate-bundle-loader` (so the file itself is
  recoverable) but the 16 head commits are not.
date of evidence: 2026-08-19 -> window: pre-wipe
platform gap: MURO. This is a lab library on an unmerged branch; there is no
  operation that consumes it.
note: **the encoder-study's entire substrate is unpushed work in an ephemeral
  worktree.** The project's own hard constraint says worktrees are ephemeral
  and that uncommitted work must be salvaged before removal. This work IS
  committed, so the salvage rule does not fire, and the branch ref lives in
  `repositories/protea-reranker-lab/.git` -- so pruning the worktree does not
  lose it. But nothing off this disk has it. A second reinstall takes the
  encoder study with it, scripts and library both.

# THE NUMBERS, ONE BY ONE, WITH A SECOND COMPUTATION

## "None of the nine cells separates" -- CONFIRMED, receipt survives, and it is the honest frame

verdict: CONFIRMED
first number: `PRODUCTION.md`: "on the official evaluation frame... split by
  knowledge category, **none of the nine category-by-aspect cells
  separates**."
second number: recomputed from
  `artifacts/fmax_by_category.json` (receipt for `scripts/25_by_category.py`):
  recipe minus champion, nine cells, 0 of 9 separating.

  | cell | n | recipe-champion | 95% CI | sep |
  |---|---:|---:|---|---|
  | NK_MFO | 50 | -0.0153 | [-0.0442,+0.0153] | no |
  | NK_BPO | 88 | -0.0014 | [-0.0192,+0.0303] | no |
  | NK_CCO | 70 | +0.0145 | [-0.0125,+0.0350] | no |
  | LK_MFO | 54 | -0.0344 | [-0.0733,+0.0107] | no |
  | LK_BPO | 193 | +0.0136 | [-0.0065,+0.0285] | no |
  | LK_CCO | 96 | -0.0053 | [-0.0317,+0.0284] | no |
  | PK_MFO | 410 | -0.0049 | [-0.0243,+0.0090] | no |
  | PK_BPO | 1579 | +0.0040 | [-0.0032,+0.0118] | no |
  | PK_CCO | 513 | -0.0027 | [-0.0191,+0.0162] | no |

  Total 3053 protein-by-aspect cells. **The recipe LOSES in five of nine and
  wins in four.** NK = 208 (6.8%), LK = 343 (11.2%), PK = 2502 (82.0%),
  LK+PK = 93.2%.
date of evidence: 2026-08-19 -> pre-wipe
frame: Fmax against what the protein GAINED over the window, prior-knowledge
  exclusion applied, aspect restricted, th_step 0.02, K=30.
platform gap: this is the one lab frame that IS commensurable with the
  platform, and no operation reproduces it. The gold comes from
  `CAFA_forever/data/releases/Sep_2025_Mar_2026/groundtruth_{NK,LK,PK,PK_known}.tsv`,
  flat files on this disk, not from the database.
note: PRODUCTION.md says the population is "95 per cent prior-knowledge
  cells". The receipt says **82.0% PK**, or 93.2% if "prior-knowledge cells"
  is read as "not NK". This is the exact ambiguity COLLIDING-A-NUMBER
  section 3 warns about: the sentence is true under one reading of its own
  words and 13 points off under the other.

## The RETRACTED +0.0214 on BPO: the receipt survives and the frame gap is 4.5x

verdict: CONFIRMED that it is an incommensurable-frame artifact; I derived
  the gap size, which the documents never state.
first number: `PRODUCTION.md`: "An earlier figure of **+0.0214 on biological
  process** was scored against propagated reference closures over a set that
  is 95 per cent prior-knowledge cells, with no exclusion applied."
  Memory: `project_sparse_residue_encoder_beats_deployed_on_fmax_2026_08_19.md`
  -- "**RETRACTED: the sparse encoder's Fmax gain was prior-knowledge
  credit**".
second number: the receipt is
  `artifacts/fmax_intervals.json` (`scripts/15_fmax_intervals.py`):
  BPO `k4-allpairs` 0.5293, `champion` 0.5079, `vs_champion` difference
  **0.021412**, CI [+0.01703, +0.02552], `"separates": true`.
  Also MFO +0.006534 [+0.00162,+0.01132] sep, CCO +0.009955 [+0.00598,+0.01400] sep.
  Population 2646 (length bands 1481+799+285+81).
  **My independent collision:** recompose the same BPO comparison from the
  nine-cell receipt, n-weighted over the three BPO cells:
  (88 x -0.0014 + 193 x +0.0136 + 1579 x +0.0040) / 1860 = **+0.00474**.
  Published +0.0214 against reconstructed +0.0047 -> **a factor of 4.5**,
  and the honest one does not separate in any of its three cells.
date of evidence: 2026-08-19 -> pre-wipe
frame A (the retracted one): Fmax against FULL propagated reference closures,
  categories POOLED, **no prior-knowledge exclusion**, population 2646.
frame B (the honest one): Fmax against gained terms, exclusion applied, nine
  cells, population 3053.
note: **both receipts are still on disk and neither is marked.**
  `fmax_intervals.json` carries `"separates": true` on all three aspects with
  no retraction stamp anywhere in the file. A reader who finds that JSON and
  not PRODUCTION.md reads a three-aspect win with intervals excluding zero.
  This is the defect class, physically instantiated, still live.
  Related: `PRODUCTION.md` measures the same effect on the exclusion alone:
  "Applying the exclusion alone drops the prior-knowledge measure from
  **0.53 to 0.13**" -- a 4x frame gap, matching the 4.5x above.

## "Thirty neighbours is too many, 16 of 18" -- CONFIRMED, recomputed exactly

verdict: CONFIRMED
first number: memory
  `project_neighbour_count_thirty_is_too_many_2026_08_19.md`: "16 of 18
  comparisons across two populations and two encoders". Same in
  `PRODUCTION.md` and `CAMPAIGN-LADDER.md`.
second number: I enumerated all 18 from `artifacts/k_confirmation.json`
  (6 groups: {champion, recipe} x {NK, LK, PK}, each K in {5,10,20} vs K=30):
  **16 wins, 2 losses**, both losses in `recipe_LK` (k=5 0.5385 and k=10
  0.5421 against k30 0.5442). Reproduces the claim exactly.
  Per-cell k10-k30 with intervals: champion_NK +0.0104 [-0.0044,+0.0236] no;
  champion_LK +0.0048 no; champion_PK +0.0028 no; recipe_NK +0.0182
  [+0.0035,+0.0312] **YES**; recipe_LK -0.0021 no; recipe_PK +0.0051
  [+0.0002,+0.0096] **YES**.
  And the SELECTION run `artifacts/k_sweep.json` separates in **0 of 9**
  cells, with argmax K wandering 2, 5, 10, 20, 60 across cells.
date of evidence: 2026-08-19 -> pre-wipe
frame: same official frame as above (gained terms, exclusion, nine cells for
  the sweep, three categories for the confirmation). Confirmation population
  3,964 proteins never used to choose K.
platform gap: **none, and this is the one item that is genuinely reborn-able
  today.** `limit_per_entry` is already a payload field on `PredictionSet`
  (`DEPLOYMENT-AUDIT.md`). Dispatching K in {5,10} beside 30 needs no code.
note: the direction was registered before the confirmation ran, which is why
  16-of-18 counts. The MAGNITUDE (2 to 10 thousandths) never separated in a
  single cell of the selection sweep, and the documents say so.

# WHERE THE LAB'S NUMBERS LIVE, AND WHERE THEY DO NOT

## The canonical SIGNAL-REGISTRY contains ZERO entries from the encoder study

verdict: CONFIRMED
first number: `agent-farm/plans/SIGNAL-REGISTRY.md` is titled "(receipt-backed,
  adversarially verified, **2026-07-27**)". Every date in the file:
  `grep -o '2026-0[0-9]-[0-9][0-9]' | sort | uniq -c` ->
  2026-06-04 x1, 2026-07-02 x1, 2026-07-11 x1, 2026-07-27 x2. **Nothing from
  August.**
second number: I grepped `agent-farm/plans/` for every headline encoder-study
  number: 0.0287, 0.0251, 0.0910, 0.1747, 0.0725, 0.0842, 0.0625, 0.0214,
  0.0313, 3031, 85982, 2646.
  **Hits in `plans/`: zero, for all twelve.** (0.0059, 0.0037, 0.024 and 0.94
  hit `plans/` but on unrelated rows -- LOFO, a knn CSV, rungs.yaml.)
  Every one of those numbers is found ONLY in
  `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`.
where I looked: all 22 slice directories plus the 20 top-level documents of
  `agent-farm/plans/`, recursively, including `archive/`.
date of evidence: 2026-07-27 (registry) vs 2026-08-19..26 (study)
platform gap: MURO.
note: **this is the single most consequential structural fact in the slice.**
  `agent-farm/plans/` is a git repository and is therefore the same file on
  both machines. The assistant memory store is, by this project's own
  CLAUDE.md, "per machine and nothing synchronises it". So the entire
  2026-08 encoder study exists, as knowledge, only in an unsynchronised
  per-machine memory store plus 130 untracked scripts on one disk. The
  document the project designates as the authority on "what every signal is
  worth" describes a lab generation that ended in July.

## SIGNAL-REGISTRY's own signals point at storage directories that do not exist

verdict: CONFIRMED (NOT_FOUND for the artifacts)
first number: `SIGNAL-REGISTRY.md:254` cites `storage/learned_encoders/`.
  `plans/prior-knowledge-wall/PLAN.md:204` cites `storage/cooc_experiment/*.json`
  and `storage/regen_headline/...`.
  `plans/CATALOG.md:60` cites `storage/fullgo_models/train_native_boosters.py`.
second number: filesystem check --
  `storage/learned_encoders`  **MISSING**
  `storage/fullgo_models`     **MISSING**
  `storage/cooc_experiment`   **MISSING**
  `storage/regen_headline`    MISSING (the content survives in the repo as
                              `protea-reranker-lab/research/regen_headline/`)
  `storage/encoder-study`     exists
  `storage/probe`             exists
  `storage/encoder`           exists
where I looked: `ls /home/xaxi/Thesis2/storage/` -- 12 directories, listed at
  the top of this file. None of the three is among them.
date of evidence: the 2026-07-28 reinstall took them -> window: **pre-reinstall-lost**
note: the surviving copies of the OLD lab's results are the ones that were
  committed into `protea-reranker-lab/{research,results,experiments,datasets}`
  (840K + 3.3M + 1.7M + 1.2M, all dated 2026-07-29 = the post-reinstall
  clone). Everything the old lab left in `storage/` is gone. The inversion is
  exact: **the old lab's numbers survive because they were committed; the new
  lab's numbers survive only because this disk has not been wiped again.**

## A canonical plan cites a receipt that has never existed anywhere

verdict: **NOT_FOUND**
first number: `agent-farm/plans/prior-knowledge-wall/PLAN.md:17` and `:204`
  cite `protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json`
  "(n=4402, the exact PK-BPO protein set)" as the receipt that CONTRADICTS
  the `bp-structural-lever` slice's opening claim. The table it backs:
  PK-bpo knn ceiling 0.4695 / knn+clf 0.5372; LK-bpo 0.7668 / 0.8227;
  NK-bpo 0.6985 / 0.7393. The plan's conclusion "the ceiling is 0.54 to 0.75
  and we deliver 0.2131" rests on it.
second number: `find /home/xaxi/Thesis2 -name 'p4_recall_ceiling*'` -> **no
  hits, anywhere on the machine**. `git log --oneline --all --
  '*p4_recall_ceiling*'` in `protea-reranker-lab` -> **no commit has ever
  touched that path**. `results/sparse_classifier/` holds 19 entries and none
  is `p4`. Grepping the repo for `4402` returns only coincidental substrings
  (`train_rows: 440222`, LK-BPO score `0.4402`).
where I looked: the whole `/home/xaxi/Thesis2` tree by filename; the full git
  history of `protea-reranker-lab` across all refs; the parent directory
  listing.
date of evidence: n/a -> window: **pre-reinstall-lost or never written**
note: this receipt is load-bearing for a REFUTATION -- it is the evidence
  cited to overturn a "hard generation wall" claim in another slice. The
  refutation currently stands on nothing checkable. Note also that the same
  paragraph is the source of the widely used framing "the ceiling is 0.54 to
  0.75"; that range is read off a table whose file does not exist.

# WHAT DIED: the two four-layer probe banks, and what they take with them

## `lafa_4layers.npy` and `pool60k_4layers.npy` are GONE. 33 of 115 scripts read them.

verdict: **CONFIRMED -- this is the largest single loss in the slice**
first number: `storage/probe/` holds
  `lafa_4layers.index.json` (326,479 B) and
  `lafa_4layers.provenance.json` (257 B), and
  `pool60k_4layers.index.json` (2,535,486 B) and
  `pool60k_4layers.provenance.json` (268 B)
  -- **but no `lafa_4layers.npy` and no `pool60k_4layers.npy`.**
  The index and provenance of both survive; the arrays do not.
second number, derived: from the provenance files, `lafa_4layers` is 7,401
  proteins / 4,622,985 residues / 4 layers and `pool60k_4layers` is 60,000
  proteins / 22,018,349 residues / 4 layers. Every surviving bank is float32,
  768-wide (I read all six `.npy` headers by hand -- magic, version, header
  length, ASCII dict -- and every file's size matches its declared shape to
  the byte):

  | file | shape | dtype | bytes expected | actual | match |
  |---|---|---|---|---|---|
  | lafa_last.npy | (4622985, 1, 768) | <f4 | 14201810048 | 14201810048 | yes |
  | pool60k_last.npy | (22018349, 1, 768) | <f4 | 67640368256 | 67640368256 | yes |
  | exp220.npy | (45073591, 2, 768) | <f4 | 276932143232 | 276932143232 | yes |
  | nk220.npy | (1483599, 2, 768) | <f4 | 9115232384 | 9115232384 | yes |
  | nk_extra.npy | (128969, 1, 768) | <f4 | 396192896 | 396192896 | yes |
  | confirmation.npy | (1109436, 1, 768) | <f4 | 3408187520 | 3408187520 | yes |

  So the two missing files were **52.9 GiB and 252.0 GiB, 304.9 GiB together**
  -- nearly as much again as the 345 GiB that survives.
  **Independent corroboration of the 252:** memory
  `project_reranking_beats_the_encoder_2026_08_19.md` says "a full session,
  five levers and a **252 GB extraction** produced nothing measurable in any
  cell". 252 GiB is `pool60k_4layers.npy` to the gigabyte. The document names
  the file that is no longer there.
where I looked: `ls -la /home/xaxi/Thesis2/storage/probe/` (the only probe
  directory on the machine); `find` for the basenames across `/home/xaxi/Thesis2`.
there is no fallback: `probe_store.ProbeStore._matrix` is
  `np.load(self.path, mmap_mode="r")` -- a missing file raises immediately.
date of evidence: index/provenance mtimes 2026-08-18 22:46 and 2026-08-19
  01:54; the arrays were removed later -> window: pre-wipe artifacts,
  deleted at unknown time
**scripts that cannot run any more (33 of 115), by what they produced:**
  - `25_by_category.py` -> the nine-cell null, `fmax_by_category.json`
  - `26_oracle_ceiling.py` -> `oracle_ceiling.json`, the per-cell oracle headroom
  - `28_k_sweep.py`, `30_k_sweep_pooled.py`, `36_k_confirm.py` -> the whole K result
  - `32_conversion_curve.py` -> **the slope 0.94 and the 0.024-0.037 gate**
  - `37_depth_vs_quality.py`, `38_depth_fast.py` -> **the +0.0725 / +0.1747 shortlist curve**
  - `39_real_reranker_floor.py` -> **the re-ranker floor 0.0032 / 0.0293 / 0.0245**
  - `14_fmax.py`, `17_quantisation.py`, `19_fmax_quantised.py` -> Fmax and quantisation
  - `16_freeze_recipe.py` -> **the frozen recipe itself**
  - `22/23/24_confirmation*.py` -> the confirmation-set results
  - plus 06, 07, 08, 10, 12, 13, 29, 31, 33, 34, 40, 41, 42, 44, 46, 48, 05
platform gap: MURO. There is no operation that extracts a per-residue,
  multi-layer probe. `encode_residue_sparse` computes per-residue transiently
  and stores one pooled code per sequence (established by the sibling
  rescued trail `wf_2b4f3e5f-f3b-a979bf1ba80cd7623.md`). The platform's own
  embedding cache is strictly 2D. Rebuilding these two banks means a fresh
  corpus pass on the card.
note: **every headline number of the encoder study is produced by a script
  whose input no longer exists.** The `.json` receipts survive and can be
  re-read; not one of them can be re-derived without ~305 GiB of forward
  passes. The surviving `exp220.npy` (276 GB) and `nk220.npy` support the
  2026-08-20+ retrieval work (scripts 77-99), which is exactly the work that
  SUPERSEDED the earlier results -- so what survives is the refutation and
  what died is the thing refuted.

# THE FRAME PARTITION OF THE LAB, COUNTED

## 35 scripts score against a CLOSURE at release 227; only 11 score against window ADDITIONS

verdict: CONFIRMED, and I counted it rather than took it on faith
first number: `storage/calibration-study/README.md`, section "What is measured
  on the wrong object, and must not be quoted":
  "Everything computed from `encoder-study/artifacts/fmax_percell.pkl` and
  `fmax_predictions.npz` is on a population selected by `01_prepare.py` as
  'LAFA probe accessions with an annotation at release 227', which is
  annotation-rich by construction and overlaps the campaign delta by **12.6
  per cent**. Its gold is the ANCESTOR CLOSURE at 227, not the additions:
  only **12.2 per cent** of the terms in `T_P` were gained in the window.
  That study is a neighbour-purity screen, not a CAFA additions evaluation,
  and reading it as one cost most of a day."
second number: I partitioned the 115 scripts by which gold they open.
  `grep -l "gold_lafa.pkl" *.py` -> **35 scripts** (ancestor closure at 227,
  built by `01_prepare.py`): 01,02,03,04,06,07,08,10,12,13,14,16,17,19,29,34,
  35,40,42,44,46,48,50,52,53,55,56,57,58,60,63,66,67,72,73.
  `grep -l "groundtruth_" *.py` -> **11 scripts** (the window's own
  additions, `CAFA_forever/data/releases/Sep_2025_Mar_2026/groundtruth_*.tsv`
  with `PK_known` exclusion): **25, 26, 28, 30, 31, 32, 36, 37, 38, 39, 41**.
  `01_prepare.py` confirms the population and the gold in its own docstring:
  "The gold is the ANCESTOR CLOSURE, propagated over is_a and part_of,
  because the screen is neighbour purity."
  `14_fmax.py` confirms it too: "the result is scored by Fmax per aspect
  **against the query's own closure**."
  `15_fmax_intervals.py` is the writer of `fmax_percell.pkl` -- so **the
  retracted +0.0214 is squarely inside the 35**, and the calibration study's
  "must not be quoted" is about exactly that number.
date of evidence: encoder-study 2026-08-19..26 (pre-wipe);
  calibration-study README 2026-09-01 (**post-wipe**)
note: the useful reading rule this gives a later reader, and it is mechanical:
  **an encoder-study artifact is in the platform-comparable frame if and only
  if its producing script is one of those eleven.** Everything else --
  including the entire 44-arm purity table, the quantisation study, the
  corpus-size curve, the in-domain lever, the five negative levers and the
  frozen recipe -- is a neighbour-purity screen on an annotation-rich
  population whose gold is 87.8% terms the protein already had.

## Even the eleven "official frame" scripts are on a DIFFERENT WINDOW from the campaign

verdict: CONFIRMED
first number: all eleven read
  `/home/xaxi/Thesis2/CAFA_forever/data/releases/**Sep_2025_Mar_2026**/groundtruth_*.tsv`.
  Memory `project_temporal_discipline_two_cutoffs_2026_08_19.md`: "release
  **227 published 2025-09-04**, release **230 published 2026-03-04**, and the
  evaluation window is Sep 2025 to Mar 2026." So the lab window is 227 -> 230.
second number: `agent-farm/plans/rungs.yaml:240` -- "what: temporal window /
  value: **GOA 220 to GOA 230**". Memory
  `project_learned_weights_must_declare_their_cut_2026_08_20.md`: "The rung 1
  evaluation set is **v220 (2024-04-16) to v230 (2026-03-04)**, delta 22,498
  proteins... Every map in the encoder study was fitted on release 227
  closures, and **227 is inside a 220-to-230 window**. The terms gained
  between 220 and 227 are part of the ground truth the frame scores, so an
  encoder trained to pull proteins sharing them together has seen the
  answer."
date of evidence: lab 2026-08-19, correction 2026-08-20 -> both pre-wipe
frame: lab = 227->230, 7,401 probe proteins, 60,000 bank at 227.
  campaign = 220->230, delta 22,498 proteins, donor bank at 220.
note: **so there are three frames, not two**, and the lab's own "official
  frame" is the middle one:
    (a) purity / closure at 227      -- 35 scripts, the retracted family
    (b) additions 227->230, -known   -- 11 scripts, the lab's "official frame"
    (c) additions 220->230, -known   -- the campaign, the platform registry
  A number from (b) is not a number from (c). The two memory files read
  together settle it: the study was "clean of label leakage **by luck, not
  design**" for its own window (b) and "**contaminated** for the official
  frame" (c). The 2026-08-20 file states the reconciliation explicitly, so
  this is recorded rather than latent -- but nothing in the artifacts
  themselves carries the window, and `fmax_by_category.json` looks like a
  campaign result and is not one.
platform gap: to make the lab commensurable one would need an operation that
  scores an arbitrary embedding configuration on the campaign's 220->230
  evaluation set with the exclusion applied. That is the `encode_residue_sparse`
  + registered-configuration path described in `DEPLOYMENT-AUDIT.md` step 3,
  which was never taken: the audit lists four blocking gaps in the merged
  operation (local path not ArtifactStore, hardcoded `cuda`, no backend
  capability check, no queue declared).

## The one lab study that IS post-wipe and IS commensurable: calibration-study

verdict: CONFIRMED
first number: `storage/calibration-study/` -- README 2026-08-31/09-01,
  95 scripts and 4 artifacts, all mtime **2026-09-01 20:34**.
  Result: "On the campaign's own population (**evaluation_result grids, NK
  cell, 2,413 proteins**), rescaling each protein's threshold to a fraction
  of its own maximum and applying it ONLY to the fifth of proteins that emit
  most: `f_micro_w` **+0.015 to +0.047**, eight of nine panel-by-artifact
  cells with the interval excluding zero, about 20 per cent relative on a
  base near 0.15. Fmax del banco: applying it to ALL proteins is better
  there, **+0.022 to +0.069**, nine of nine."
second number: its inputs are named and they are platform objects --
  "They read the per-protein grids from the object store under
  `eval_artifacts/{evaluation_result_id}/{NK,LK,PK}/per_protein_grid.parquet`.
  Nothing here touches the live database." Those `evaluation_result` ids are
  the post-wipe rows (93 of them, 2026-08-27..30). I did not open the object
  store; the artifacts on disk are `calib.json`, `calib2.json`, `pk13.csv`,
  `pk_all.csv` only, so the parquet grids are NOT cached in storage and the
  study is re-runnable only while the object store keeps them.
date of evidence: 2026-08-31 / 2026-09-01 -> window: **post-wipe-current** --
  the ONLY lab work in this slice that is.
frame: `f_micro_w` (pooled, IA-weighted) AND `Fmax del banco` (per-protein
  mean), and the README states outright that **"which rule is right depends
  on which statistic is optimised, and the two disagree in direction."** That
  is the frame problem stated as the result rather than discovered later.
  Controls that could have failed and did not: shuffled maximum (16 of 18
  positive vs 7 of 18, p about 0.0013); random targeting loses 9 of 9; a
  fixed top-k beats the rescaling on `f_micro_w` and loses on Fmax.
platform gap: `grid.py`, `regla.py`, `dirigida.py`, `ctrl.py` produce a
  calibration rule that no operation applies. There is no
  `apply_threshold_rule` / `calibrate_predictions` operation; the rule exists
  as 95 loose scripts.
note: this study did what the encoder study did not: it wrote itself to
  `storage/` with a README naming its population, its two statistics and its
  controls, and it explicitly quarantines the earlier lab's artifacts. Its
  own README says why: "a procedure outside the platform is a capability that
  dies with the disk, and this one nearly did."

# COLLISIONS AGAINST THE SURVIVING RECEIPTS

## CONTRADICTED: "the deployed sparse encoder declares no training release"

verdict: **CONTRADICTED**
first number: memory
  `project_learned_weights_must_declare_their_cut_2026_08_20.md`:
  "**The deployed sparse encoder declares no training release.**
   `encoder.pt meta = {pooling: mean, dict_dim: 2048, top_k: 128, in_dim: 768,
   backbone: ElnaggarLab/ankh-base}`. No temporal cut anywhere in it. It can
   therefore be **neither certified clean for any frame nor ruled
   contaminated, which is worse than either**, because an unfalsifiable
   artifact cannot be defended to an examiner or to CAFA."
second number: the checkpoint's meta is exactly as quoted -- I read
  `storage/encoder/encoder.pt` as a zip and pulled the strings out of
  `encoder/data.pkl` without torch, and the meta keys are pooling, dict_dim,
  top_k, in_dim, backbone and nothing else. So that half is right.
  **But two files sitting in the same bundle declare the cut explicitly:**
  `storage/encoder/MANIFEST.json` --
    `"annotation_release": "227"`, `"annotation_published": "2025-09-04"`,
    `"annotation_set_id": "ec9f5c2c-cc1c-4e22-8cda-d1fe53ca86b3"`,
    `"ontology": "releases/2025-07-22"`, `"ref_pool": 60000`,
    `"trained_at": "2026-08-10T17:46:26Z"`, `"epochs": 150`,
    `"train_pairs": 300000`, `"seed": 42`, `"arm": "learned-k128-hardneg"`;
  `storage/encoder/bank/BANK.json` -- the same release and publication date,
    plus `"bank_rows": 575503`, `"distinct_sequences": 487237`,
    `"donor_annotations": 5880402`.
  The same values are duplicated again in `storage/encoder/bundle/`.
date of evidence: bundle 2026-08-10, memory claim 2026-08-20 -> both pre-wipe
note: the artifact is **not unfalsifiable, it is falsified**. Trained against
  release 227, published 2025-09-04. Against the campaign's 220->230 window
  that is inside the window, so the deployed encoder is **ruled
  contaminated** by its own manifest -- the strictly worse conclusion the
  memory says it could not reach. The memory looked in the checkpoint and
  stopped; the manifest is two files away in the same directory. This is
  COLLIDING-A-NUMBER section 4 exactly: a negative check that did not look
  where the thing would be.
platform gap: the real gap the memory identifies still stands -- nothing
  ENFORCES `training_release <= window_start`, and the checkpoint format
  carries no slot for it. A registered `learned_encoder` row with a
  `training_release` column, checked at dispatch, is the operation that would
  make this mechanical.

## Receipts that reproduce their memory claim EXACTLY (spot checks)

verdict: CONFIRMED, six for six
- **10.83% dead donors, 7.77% isoform vs 3.06% uncharacterised.**
  `artifacts/103_dead.json` `base_rate` = 0.10830333109972856;
  `artifacts/104_split.json` `iso_base` = 0.07771619590606746 and
  `unc_base` = 0.030587135193661106. **0.07772 + 0.03059 = 0.10831** -- the
  two halves sum to the base rate, which is the independent check.
  Twilight ratio: `band_top10["crepuscular <=30"]` 0.17442 / 0.08084... ->
  the memory's "Twilight 2.12x" is 0.17442/0.08221; index size 528,294,
  queries 3,031.
- **ProtST removal: twilight 0.0842 -> 0.0625, other bands unchanged.**
  `artifacts/98_spread.json`: twilight con 0.08418478 sin 0.06251232 (n=778);
  distante, cercana and casi-identica have `con` == `sin` to the last digit
  (0.03153411, 0.01894014, 0.01077468). Band n's sum to
  778+1007+827+419 = **3031**, the full NK cell.
- **Two-tower atoms: rank 9,378 of 29,027 against a declared 290.**
  `artifacts/107_atoms.json`: mean_rank_real 9378.48 [9159.98, 9604.16],
  mean_rank_shuffled 14917.64, vocab 29027, declared_threshold 290,
  verdict "NO SIRVE sin reentrenar". Shuffle as a fraction of vocab =
  14917.64/29027 = **51.4%**, exactly the memory's "shuffle = 51.4%".
date of evidence: 2026-08-23 to 2026-08-26 -> pre-wipe
note: these are the honest end of the lab. Each has a receipt, each
  reproduces, and each is a NEGATIVE or a diagnostic rather than a win.

## Two small population drifts inside the ProtST retraction

verdict: CONTRADICTED (in the small)
first number: `RESULTS.md`: "Every one of the **3,031** no-knowledge targets
  is a reviewed Swiss-Prot entry"; its table headers say
  "described (**2,468**)" and "undescribed (**547**)"; and later
  "On the **550** proteins UniProt never described, the twilight spread is
  0.0835 with it and 0.0835 without."
second number: `artifacts/97_leak.json` says `n` = **3015**, `described` =
  **2468**. 3015 - 2468 = **547**. So three counts are in play for one
  population: 3,031 (the cell), 3,015 (what the leakage script scored), and
  550 (quoted for the undescribed where the receipt says 547).
date of evidence: 2026-08-23 -> pre-wipe
note: 16 proteins and 3 proteins. Nothing turns on it, but the retraction's
  own sentence "**None of nine** does among the undescribed" is a claim about
  a group of 547 that the prose calls 550 and the headline population 3,031
  that the receipt calls 3,015. When the paper is written the receipt count
  is the one to use.

## A truncation receipt that undercuts one arm of the backbone comparison

verdict: CONFIRMED, and I could not find it flagged anywhere
first number: `artifacts/111_truncation.json` (script
  `111_does_it_truncate.py`, 2026-08-26 04:36):
  model `facebook/esm2_t6_8M_UR50D`, `declared_max_length` 2048, a sequence
  of **8,384 residues**, `cos_full` 0.8567, `cos_truncated` **0.9999915**,
  verdict `"TRUNCA: lo guardado son los primeros 2048"`.
  i.e. what is stored for that protein is the first 2,048 residues and
  nothing else, and the stored vector is indistinguishable from the
  truncated one.
second number: `esm2 t6 8M` is one of the eight rivals in the ProtST leakage
  table in `RESULTS.md` (described +0.0391, undescribed +0.0064) and one of
  the arms in the twilight backbone spread of 0.0842 / 0.0625.
where I looked: `RESULTS.md`, `PRODUCTION.md`, `RUNG2-ENCODING-ABLATION.md`,
  `DEPLOYMENT-AUDIT.md`, `CAMPAIGN-LADDER.md`, and every memory file
  mentioning the backbone spread. **The truncation is not mentioned in any of
  them.** The project's own CLAUDE.md landmine list has
  `project_embedding_truncation_limits_2026_06_25` and
  `project_no_truncation_so_residues_are_the_batch_unit_2026_08_21`, so the
  hazard is known; this specific measurement, made three days after the
  backbone tables were written, appears nowhere near them.
date of evidence: 2026-08-26 -> pre-wipe
note: the direction is unfavourable to the weakest arm, which is the arm the
  spread is measured against, so the spread of 0.0842 / 0.0625 is a **maximum
  over a set containing at least one arm handicapped by truncation** rather
  than by representation. Whether it matters depends on how many NK targets
  exceed 2,048 residues, which `RESULTS.md`'s own length table says is 81 of
  2,646 on the purity population (3.1%). Small, but the spread is a max, and
  a max is sensitive to its worst member.

## THE FLAGSHIP COMPARISON IS ACROSS TWO PRODUCERS AND TWO BANKS: 0.0842 vs 0.0006

verdict: **CONFIRMED as an incommensurable-frame comparison.** This is the
  study's own headline table and it is the clearest live instance of the
  defect class in the slice.
first number: `storage/encoder-study/RESULTS.md`, the table that closes the
  supersession section:

  | axis, twilight band | spread |
  |---|---|
  | choice of base protein language model | **0.0842** |
  | order of selection and pooling | **0.0006** |

  followed by "Two orders of magnitude, **one metric, one population**. The
  axis the study was designed around is inert; the axis nobody was funding
  carries the effect."
second number: the two receipts, opened and compared.
  **0.0842 comes from `artifacts/87_bands_full.json` / `87_full.out`**, whose
  every model entry carries a `pset` UUID -- these are PLATFORM prediction
  sets (`4f8dd347-...` ankh-base, `e0ce080b-...` ankh-large,
  `3cda8935-...` ProstT5, `01ad41a1-...` prot_t5, `5c5500c4-...` esmc_600m,
  and three more). `87_full.out` prints RECORRIDO (range best-to-worst) in
  twilight as **+0.0842 at budget 10**, +0.0704 at 25, +0.0647 at 50,
  +0.0522 at 100. So 0.0842 is the **budget-10** figure, and the ProtST
  retraction table (`98_spread.json`, twilight con 0.08418 sin 0.06251) is
  also budget 10, while the ProtST leakage table in the same document is
  stated "at a 25-term budget".
  **0.0006 comes from `artifacts/89_arms.json`**, `"bank": 85982`, three arms
  (dense/pooled/residue) encoded from the LAB's own codes.
  **The two do not reach the same donors at the same declared budget:**

  | budget | 87 (platform psets) donors | 89 (lab bank) donors | 87 recall | 89 recall |
  |---|---:|---:|---:|---:|
  | 10 | 1.75 - 2.00 | 1.07 - 1.09 | 0.6437 - 0.6818 | 0.6009 - 0.6029 |
  | 25 | 4.18 - 5.38 | 1.41 - 1.45 | 0.7167 - 0.7522 | 0.6253 - 0.6307 |
  | 50 | 8.28 - 10.94 | 2.63 - 2.75 | ... | 0.6781 - 0.6808 |

  At a budget of 25 the backbone arms reach **4.97 donors on average and the
  order arms reach 1.41** -- a factor of **3.5**. The recall levels differ by
  **0.123** at that budget, which is larger than either effect being
  compared and larger than the whole 0.0842.
date of evidence: 87 and 89 both 2026-08-20 -> pre-wipe
frame: identical query population (3,031 NK, paired on accession) and
  identical band definition, so "one population" is TRUE of the queries.
  Different donor bank, different producer path (platform prediction set vs
  lab code + lab bank), and a "matched candidate budget" that matches the
  budget integer and not the donors it buys.
note: **RESULTS.md half-declares this and then draws the conclusion anyway.**
  Its own next paragraph says "The absolute level moves with the bank, from
  about **0.665** against the platform's donor set to **0.602** against this
  one... only the band structure transfers." Both figures are budget 10 and
  they reproduce exactly (87 ankh-base 0.66421, 89 residue 0.60173). But the
  donor-count difference is nowhere in the document, and having stated that
  only the band STRUCTURE transfers, the table then places two band
  MAGNITUDES side by side and reads a ratio off them.
  The honest version of the sentence is: the order axis is inert **on a bank
  that reaches 1.4 donors at budget 25**, and the backbone axis is worth
  0.0842 **on a bank that reaches 5.0**. Whether the order axis would stay
  inert on the richer bank is untested, and it is the test that matters,
  because a selection order can only express itself when there is something
  to select among.
platform gap: an operation that scores a lab-produced embedding
  configuration through the SAME retrieval path as a platform prediction set
  -- i.e. `DEPLOYMENT-AUDIT.md` step 3, "encode a bounded corpus and register
  the configuration", which was never done. Until it is, no lab arm and no
  platform arm can be put in one table.

## Two more population drifts, both toward a rounder number

verdict: CONTRADICTED (in the small)
- `RESULTS.md`: "The screen those rows used ranked candidates from a
  probe-shaped bank of pool proteins, over **640 NK proteins**". The receipt
  `artifacts/87_bands.json` says `"n_common": **637**`.
- `RESULTS.md` ProtST section: "**550** proteins UniProt never described";
  `artifacts/97_leak.json` gives 3015 - 2468 = **547**.
note: with `87_bands.json` (n=637) and `87_bands_full.json` (n=3031) sitting
  in the same directory under names that differ by one word, the risk is not
  the rounding, it is picking up the wrong file. The 637-protein version is
  the SUPERSEDED screen; the 3031 version is the one that supersedes it.

# THE DISTRIBUTION BEHIND THE HEADLINE (recomputed from raw, no numpy)

## +0.0287 and +0.0251 reproduce exactly. The median is HALF the mean and a third of proteins get WORSE.

verdict: CONFIRMED (the mean) / **the summary hides the shape**
first number: `RESULTS.md` arm table -- `residue-k4` 0.2570, `champion-frozen`
  0.2284, difference **+0.0287**; `residue-k32` 0.2535, **+0.0251**;
  `residue-k4` vs `control-pooled` **+0.0358**. Memory
  `project_residue_order_wins_when_trained_2026_08_19.md` carries the same
  table.
second number: I opened `artifacts/purity_per_protein.npz` as a zip and
  decoded each member's `.npy` by hand (magic, version, header length, ASCII
  dict, then `struct.unpack`). 47 arrays, all `<f8`, shape (2646,), plus
  `accs.npy` (`<U10`) and `lengths.npy` (`<i4`).

  | comparison | mean | **median** | p10 | p90 | **fraction of proteins improved** |
  |---|---:|---:|---:|---:|---:|
  | residue-k4 - champion | **+0.0287** | +0.0140 | **-0.0211** | +0.0982 | **69.5%** |
  | residue-k32 - champion | **+0.0251** | +0.0119 | **-0.0251** | +0.0923 | **65.5%** |
  | residue-k4 - control-pooled | **+0.0358** | +0.0211 | -0.0155 | +0.1089 | 74.1% |

  Arm means reproduce to four decimals: residue-k4 0.2570, champion 0.2284,
  control-pooled 0.2212, residue-k32 0.2535.
date of evidence: `purity_per_protein.npz` mtime 2026-08-19 08:03 -> pre-wipe
note: the paired bootstrap is on the MEAN and the mean is right. But the
  typical protein gains **half** the headline, the tenth percentile
  **loses**, and between a third and a quarter of the population is made
  worse by the winning arm. Nothing in `RESULTS.md`, `PRODUCTION.md` or the
  memory files reports a median, a quantile or a win rate for this
  comparison. COLLIDING-A-NUMBER section 5, on the study's own flagship
  number.

## The stratification the study never ran: the purity gain is FLAT across categories

verdict: **DEDUCED-NOT-MEASURED, now measured**
first number: `scripts/25_by_category.py` opens with "Fmax by KNOWLEDGE
  CATEGORY, **which is the axis this study never stratified on**... Every
  aggregate number in this study is dominated by the prior-knowledge cell and
  can say nothing about the cell that matters." The purity table is never
  split by category anywhere in the study; the scoring script
  (`03_score.py`) stratifies by LENGTH only. The natural inference -- stated
  as the retraction in memory
  `project_sparse_residue_encoder_beats_deployed_on_fmax_2026_08_19.md`
  ("**RETRACTED: the sparse encoder's Fmax gain was prior-knowledge
  credit**") -- is that the purity gain is prior-knowledge credit too.
second number: I ran the stratification. Joined
  `purity_per_protein.npz:accs.npy` (2,646 accessions) against
  `artifacts/categories_227_230.pkl` (keys `nk`, `lk`, `pk`, `pk_known`):

  | cell | n | share | mean gain | median | frac improved |
  |---|---:|---:|---:|---:|---:|
  | NK | 140 | **5.3%** | **+0.0311** | +0.0198 | 72.9% |
  | LK | 324 | 12.2% | +0.0310 | +0.0147 | 71.6% |
  | PK | 2182 | **82.5%** | +0.0282 | +0.0134 | 69.0% |
  | unassigned | 0 | -- | -- | -- | -- |

  Every one of the 2,646 falls in a cell, so the join is complete.
date of evidence: computed today, 2026-09-02, from 2026-08-19 artifacts
note: **the purity gain is NOT prior-knowledge credit.** It is flat: NK
  +0.0311, LK +0.0310, PK +0.0282, and if anything it is largest in the
  serving cell. So the retraction of the FMAX result does not carry over to
  the purity result, and the two must not be collapsed. What is wrong with
  the purity number is not that it is PK credit; it is that purity's gold is
  the ancestor closure at 227 (87.8% of which the protein already had) and
  that the same arms are inert on retrieval against a real bank. Two
  different objections, and the documents run them together.
  Note also the composition: **5.3% NK** in the purity population, which is
  the project's own "the serving population is about 5% of a window". n=140
  is too small for the purity comparison to say anything about the served
  cell on its own, and no interval for the NK sub-cell is published anywhere.

# THE FROZEN ARTIFACTS: the best-documented thing the lab produced, and one live landmine

## The recipe `.npz` files carry their own provenance, retraction and supersession

verdict: CONFIRMED -- and this is the model the rest of the lab should have
  followed
Every file in `storage/encoder-study/recipe/` is an npz whose members include
`recipe_note`, `provenance`, `order`, `aggregate`, `layer_indices`,
`k_residue`, `k_sequence`, `dict_dim`, `in_dim` -- and for the 220 family,
`training_release`. I read them by unzipping and decoding the `<U` arrays by
hand. What they say:

| artifact | train_release | train_proteins | status recorded IN the file |
|---|---|---:|---|
| `cut220-residue-k4-d2048-s128.npz` | **220** | 59,821 | "frame_check: training_release 220 <= window start 220, so this artifact is admissible for the 220 to 230 evaluation"; **"not_established: not yet scored on the official frame"** |
| `exp220-residue-k4-d2048-s128.npz` | **220** | 66,515 | same, plus "order_check: fitted and served in the same order, verified through the platform's own `load_frozen_encoder`, `topk_real` and `reduce_residues`"; **"not yet scored on the official frame"** |
| `residue-sparse-k4-d2048-s128-mean.npz` | (227, undeclared) | 3,761 | task: "TIES the deployed encoder; no aspect separates" (MFO -0.0051, BPO +0.0012, CCO +0.0065 on 649 NK proteins) |
| `residue-sparse-k4-d2048-s128-moments.npz` | (227, undeclared) | 3,964 | **"status: SUPERSEDED"** -- moments loses on the task -0.0100 / -0.0017 / -0.0119 and separates negatively in MFO |
| `residue-sparse-k4-d2048-s128.npz` | (227, undeclared) | 3,964 | **"status: SUPERSEDED"** -- "fitted on 3,964 proteins including 203 of the served category, so it is fitted on proteins of the category it would be judged on" |

Controls at 220 also exist: `artifacts/controls/{cut220,exp220}-{dense,pooled}-*.npz`
and `recipe/platform/*.pt` (torch form for the platform's loader).
date of evidence: 227 family 2026-08-20 12:21; 220 family 2026-08-21 00:32
  -> both **pre-wipe**
note: **the two admissible-for-the-campaign artifacts exist and have NEVER
  been scored.** `RUNG2-ENCODING-ABLATION.md` says the 227 family is
  "withdrawn" and "their replacements are fitted on release 220 and declare
  the release they saw". The replacements are on disk, they declare it, and
  their own provenance says "not yet scored on the official frame". That
  scoring is the single cheapest piece of unfinished lab work in the slice:
  the artifact exists, the operation exists, and the number does not.

## LIVE LANDMINE: the frozen recipe recommends 2 bits; the study later measured 2 bits as the one setting that BREAKS

verdict: **CONTRADICTED, and still uncorrected on disk**
first number: inside `recipe/residue-sparse-k4-d2048-s128-mean.npz`, the
  `provenance` member's `storage` block:
  `{"float16_bytes": 432, "q4_p99_bytes": 237, "q2_p99_bytes": 159,
    "deployed_encoder_bytes": 432,
    "recommended": "**2 bits** with a 99th-percentile margin, 159 bytes,
    loss -0.0008 which is below the 0.0013 resolution floor"}`
second number: `PRODUCTION.md`, "Addendum 2026-08-20: what ships is a sign
  bit", measured on the full cell (3,031 NK vs 85,982 donors):

  | margin | bits | bytes | against float32 | bands separating |
  |---|---|---|---|---|
  | p99 | 8 | 304 | +0.0014 [-0.0008,+0.0037] | 0 of 4 |
  | p99 | **4** | **240** | -0.0001 [-0.0029,+0.0027] | **0 of 4** |
  | p99 | **2** | 208 | **-0.0243 [-0.0311,-0.0177]** | **4 of 4** |
  | p99 | 1 | 192 | +0.0015 [-0.0028,+0.0059] | 0 of 4, but degenerate (8.4 donors tied at the cut) |

  "at two bits the signed grid is minus one, zero and plus one, so every atom
  below half the scale rounds to zero and the code loses its support. Atoms
  surviving out of 127.9: none deleted at one bit, **81.8 per cent deleted at
  two**." The recommendation in the document is **4 bits at 240 bytes**.
date of evidence: artifact 2026-08-20 12:21, addendum same day, later ->
  pre-wipe both
note: **the artifact was never re-stamped.** Anyone who loads
  `residue-sparse-k4-d2048-s128-mean.npz` and reads its own declared
  recommendation ships 2-bit codes, which the same study measured as losing
  0.0243 in every identity band -- eighteen times the resolution floor. The
  two byte figures also disagree (159 vs 208 for 2 bits, 237 vs 240 for 4),
  so the accounting differs as well as the verdict. This is the only defect I
  found in this slice that would cause a wrong deployment today rather than a
  wrong sentence.
platform gap: a frozen encoder artifact has no field the platform validates
  against a measurement. `load_frozen_encoder` reads the recipe and, per
  `RUNG2-ENCODING-ABLATION.md`, "refuses one that does not declare it" -- it
  checks declaration, not correctness.

## A SECOND conversion slope, measured, and different from the famous one

verdict: CONFIRMED, and I found no document that puts the two side by side
first number: "the conversion runs at **slope 0.94**"
  (`DEPLOYMENT-AUDIT.md`, `CAMPAIGN-LADDER.md`, `PRODUCTION.md`) -- neighbour
  QUALITY (Jaccard against what the query GAINED) into Fmax.
second number: inside `recipe/residue-sparse-k4-d2048-s128-moments.npz`, the
  `screen_caveat` member:
  "Neighbour **purity** ranks variants of THIS architecture correctly, **at
  slopes between 0.29 and 0.69** into Fmax. Do not use it to compare this
  architecture against another one."
  And in `-mean.npz`: "purity divides by the neighbour's own annotation
  count, so it rewards retrieving sparsely annotated proteins."
note: two screens, two slopes, and the ratio 0.94 / 0.29-0.69 is roughly the
  factor by which a purity gain over-reads. 0.0910 x 0.29 = 0.0264 and
  0.0910 x 0.69 = 0.0628, which brackets nothing useful, but 0.0287 x 0.29 =
  0.0083 -- squarely inside the "0.007 to 0.015" the audit says the metric's
  own definition gives. **The purity screen's own slope, taken from the
  artifact, reproduces the audit's order-of-magnitude correction.** That is
  an independent second route to the same conclusion and neither document
  cites the other.
  Corroboration of the size: `-mean.npz` provenance says "holding the
  population fixed and scoring against what it GAINED removes **five sixths**
  of it" (83%); my own recomposition of the BPO comparison from the nine-cell
  receipt removed **78%** (0.0214 -> 0.0047). Two routes, same magnitude.

## NINE different populations are all called "the no-knowledge cell"

verdict: CONFIRMED
Collected from the receipts I opened, every one of these is "NK" in some
document of this lab:

| n | what it actually is | source |
|---:|---|---|
| 50 / 88 / 70 | NK MFO / BPO / CCO protein-aspect cells, official-frame Fmax | `fmax_by_category.json`, `oracle_ceiling.json` |
| 140 | NK proteins inside the 2,646 purity held-out set | my join of `purity_per_protein.npz` x `categories_227_230.pkl` |
| 208 | NK protein-aspect cells, re-ranker floor and shortlist curve | `real_reranker_floor.json` |
| 294 | NK in the K confirmation, 3,964-protein population | `k_confirmation.json` |
| 637 (called "640") | NK against the superseded probe-shaped bank | `87_bands.json` |
| 649 | "the served no-knowledge cell" for the task measurement | provenance inside all three 227-family recipe npz files |
| 2,413 | NK cell of the campaign's own evaluation_result grids | `calibration-study/README.md` |
| 3,015 | NK targets the ProtST leakage script actually scored | `97_leak.json` |
| 3,031 | the full NK cell, retrieval against 85,982 donors | `89_arms.json`, `87_bands_full.json`, `98_spread.json`, `102_curve.json`, `99_layer38.json`, `103_dead.json` |

note: some of these are protein-aspect cells and some are proteins, which
  accounts for a factor of about 3, and some are held-out subsets. But
  **no document states which one it means**, and three of them (140, 649,
  3,031) differ by more than an order of magnitude while all being called
  "the served cell". Whenever a lab sentence says "in the serving cell",
  the first question is which of the nine.

# WHAT SURVIVED THE WIPE THAT NOBODY HAS NOTICED: 21 pre-wipe evaluation bundles

## `storage/rescue/minio/protea/eval_artifacts/` holds 21 complete pre-wipe evaluations

verdict: **CONFIRMED. This is the most useful positive finding in the slice.**
first number: the slice brief says the live registry holds only 93
  `evaluation_result` and 19 `prediction_set` rows, all 2026-08-27..30, and
  that anything earlier is not evidence about the current window.
second number: `/home/xaxi/Thesis2/storage/rescue/minio/protea/eval_artifacts/`
  contains **21 bundles**, 357 files, **464 MB**, all mtime **2026-08-02**.
  Every one of the 21 has the identical shape:
    `<evaluation_result_uuid>/{NK,LK,PK}/evaluation_all.tsv`
    `<...>/{NK,LK,PK}/evaluation_best_{f,f_w,f_micro,f_micro_w,s}.tsv`
    `<...>/predictions/predictions.tsv`
  The bundle ids are real evaluation_result UUIDs:
  01a4a2a6, 3ad19853, 4fab615f, 556476c2, 592237fa, 65c74ec0, 6769e4f2,
  77bceeb3, 8a404f4b, 8bcef049, 9b5c2108, 9c10d225, 9d6ac185, b11963f8,
  d2830cf6, d43133e5, d9e05813, dfe68692, e503c32b, f8482f99, fe24ac6d.
  Each `evaluation_best_f.tsv` carries the full cafaeval row: ns, tau, n, tp,
  fp, fn, pr, rc, cov, mi, ru, f, s, and the IA-weighted twins pr_w, rc_w,
  f_w, s_w, plus f_micro and f_micro_w and cov_max -- i.e. **all four F
  statistics the project's own COLLIDING-A-NUMBER warns are confused with one
  another, per aspect, per cell, at the best tau.**
date of evidence: **2026-08-02** -> window: **pre-wipe** (25 days before) and
  post-reinstall.
note: these are 21 measured evaluations that the live registry no longer
  knows about. They are complete on the number side.

## But the rescue's DATABASE dump never finished, so the 21 bundles have NO FRAME

verdict: **CONFIRMED -- the frames were lost and the numbers were not**
first number: `storage/rescue/dump.py` orders tables by
  `pg_total_relation_size` DESC and writes one `.csv.gz` per table plus a
  `MANIFEST.json` at the end, "para poder verificar la restauracion leyendo
  de vuelta en vez de suponerla".
second number: `ls storage/rescue/pgdata/` returns **exactly two files**:
  `protein_go_annotation.csv.gz` (243 MB) and `sequence_embedding.csv.gz`
  (2.2 GB). **There is no `MANIFEST.json`**, so by the script's own design
  the run did not reach its last line. `dump.log` is 74 bytes and holds one
  line: `protein_go_annotation 16,559,108 filas 243.1 MB 485.0s`.
  So no `evaluation_result`, no `prediction_set`, no `job`, no
  `annotation_set`, no `embedding_config`, no `reranker_model`, no `dataset`
  was captured. It stopped after the two largest tables.
where I looked: the whole `storage/rescue/` tree; `pgdata/` has no other
  files; `minio/protea/` has exactly one prefix, `eval_artifacts`, and no
  `models`, `datasets` or `encoder` prefix.
date of evidence: 2026-08-02 12:08 (first table) and 12:46 (second)
note: **this is the precise shape of the loss.** For those 21 evaluations we
  still have every number -- Fmax, F-weighted, micro, micro-weighted, S, per
  aspect, per knowledge cell -- and we have lost every fact about what
  produced them: which prediction set, which K, which scorer, which
  embedding configuration, which annotation set, which ontology snapshot,
  which temporal window. The bundle id is the only handle and there is no row
  to resolve it against.
  Given this slice's own subject -- the frame problem -- that is the worst
  possible way for data to survive: **21 numbers with no frames is exactly
  the object that produces the "same reranker reads 0.3433 and 0.117" defect.**
  They must be treated as unusable for any comparison until a frame is
  recovered from elsewhere (the `job` table on the laptop, or a plan document
  naming the same UUID), and I found no document in `agent-farm/plans/` that
  names any of the 21 UUIDs.
platform gap: the rescue was a hand-written script, not an operation. A
  `dump_registry` / `export_evaluation` operation that wrote the ROW beside
  the artifact -- or an artifact bundle that embedded its own payload -- is
  what would have made these 21 usable. `PROTEA` already writes
  `eval_artifacts/<id>/...`; adding the payload as a sibling JSON is the
  minimal fix and it costs nothing.

## Also on this disk, and also frameless: `storage/encoder/eval_*` and `cmp_*`

verdict: CONFIRMED (lesser)
`storage/encoder/` (2026-08-10..12) holds `eval_maxsim/`, `eval_vote/`,
`cmp_maxsim/`, `cmp_vote/`, each with `predictions/` and (for the eval pair)
`results_{NK,LK,PK}/`, plus `IA.tsv` (992 KB), `encoder.pt`, the bank
(`accessions.npy`, `codes_idx.npy`, `codes_val.npy`, `donors.tsv.gz`,
575,503 rows / 487,237 distinct sequences) and 18 docker build logs.
note: two scoring modes (`maxsim` and `vote`) were evaluated against each
other here on 2026-08-11 and the comparison appears in no document I found in
`plans/` or the memory store. `build_alias.log`, `build_baked.log`,
`build_cu121.log` etc. are container work, not results.

### negative check, stated: which of the 21 UUIDs is named anywhere

where I looked: `grep -rl` for each of the 21 eight-hex prefixes across
  `agent-farm/plans/` (all 22 slice dirs + archive), the whole memory store,
  `storage/encoder-study/` and `storage/calibration-study/`.
result: **exactly one hit.** `3ad19853` is named in memory
  `project_calibration_wall_never_measured_2026_08_11.md:37` --
  "The fill tax, measured on frozen eval artifact `3ad19853`: **76.9% of the
  BPO cells cafaeval scores are ancestors PROTEA never emitted**, carrying
  77.9% of BPO IA mass (MFO 53.2% / 50.5%). Each emitted BPO term is missing
  an average 10.93 of its ancestors from that protein's rows. Ablations that
  compare arms without closing the emitted support at the writer are
  comparing fill taxes."
note: so **1 of 21 rescued bundles has a recoverable frame, and it is
  recoverable only because one memory file happened to quote its id.** The
  other twenty are anonymous numbers. And the one that is identified is
  identified for a measurement about a DEFECT in the scoring, not about an
  arm -- which is a fair summary of the whole slice.

## ontology-drift reproduces exactly, and its own scope limit is honest

verdict: CONFIRMED, six figures for six
first number: memory
  `project_ontology_shrinks_but_growth_is_what_bites_2026_08_27.md`:
  terms 42,309 -> 39,903 (+350, -2,756); edges 74,117 -> 68,310
  (+2,740, -8,547), net -5,807; closure grew 3,429 of 39,553 common = 8.67%;
  shrank 11,670 = 29.50%; BPO growth 10.01% with 4,650 extra ancestors,
  MFO 6.27%, CCO 6.03%.
second number: `storage/ontology-drift/edge_drift.json` -- every one of those
  figures is in the file verbatim, and the three aspect percentages recompute
  from its own counts: BPO 2564/25607 = **10.01%**, MFO 624/9950 = **6.27%**,
  CCO 241/3996 = **6.03%**; overall 3429/39553 = **8.67%**, 11670/39553 =
  **29.50%**.
date of evidence: `edge_drift.json` mtime **2026-08-27 01:43**;
  `retired_exposure.json` **2026-08-27 10:50** -> window: **the wipe day
  itself**, i.e. the boundary. It reads no database ("Measured offline from
  the two OBO files, no database") so the wipe does not touch it.
frame: ontology only, `go-basic-2024-03-28.obo` (31.3 MB) against
  `go-basic-2025-07-22.obo` (31.4 MB), both present in the directory. Both
  OBO files are on disk, so this study is **fully reproducible today** --
  the only one in the slice of which that is true without qualification.
platform gap: none needed for the drift itself. The weighted version IS a
  gap: `measure_retired_exposure.py`'s own docstring says "Weighting by how
  many GOA 220 annotations actually sit on those terms **needs the database
  and is left to the machine that has it**", and the memory records it as
  "a named hole rather than a measurement".
note: `retired_exposure.json` also carries a self-recorded correction that
  the memory index does not: `"alt_id_check_was_the_wrong_field": true`, and
  the refined breakdown of the 2,756 retired terms --
  `replaced_by_with_live_target` **737**, `consider_only` **151**,
  `no_target_at_all` **1,868**, `redirected_via_alt_id` **0**. So of the 2,756
  retirements, **1,868 (67.8%) have no successor at all**, which is the
  number that bounds the loss mechanism and it is in no document.

## LIVE, RIGHT NOW: a throughput sampler is corrupting its own artifact

verdict: CONFIRMED (observed during this audit; I did not touch it)
first number: `storage/throughput/CURRENT_RUN` says `ankh_large-2026-07-29`,
  and the four TSVs are named for a 2026-07-29 throughput benchmark
  (ankh_base 556 lines, esm2_650m 263, esmc_600m 287).
second number: `ankh_large-2026-07-29.tsv` is **30,360 rows spanning
  2026-07-29T20:59:57Z to 2026-09-02T00:11:41Z**, and it grew during this
  audit (mtime 01:56 -> 02:11 while I was reading it).
  `ps` shows `bash /home/xaxi/Thesis2/storage/throughput/sample.sh
  ankh_large-2026-07-29`, **started 2026-09-02 00:14**, PID 2092.
  26,998 rows carry broker/db values and **3,362 are blank** in every column
  but `acked_total`; there are **215 transitions** between full and blank,
  the first at 2026-08-01T19:16:33Z. The last row with data is
  2026-08-29T19:59:47Z.
  A sibling `ankh_large-2026-07-29.tsv.corrupt-backup` (36 KB, 2026-07-30)
  records that this already went wrong once.
date of evidence: **2026-09-02, today** -> window: post-wipe-current
note: I did not stop it -- the project's rule is never to kill a long job --
  but the throughput measurement it is named for is 35 days and 30,000 rows
  in the past, and the file no longer distinguishes the benchmark from a
  month of idle polling. If anyone quotes an ankh-large throughput from this
  file they must filter to 2026-07-29/30 and to rows where column 2 is
  non-empty. The other three TSVs are clean.
platform gap: the memory file
  `project_run_ledger_and_instrumentation_gap_2026_07_29.md` already records
  why this exists -- "PROTEA publishes no operation metrics and RabbitMQ only
  cross-queue aggregates" -- so `sample.sh` is the substitute for an
  operation-level metric. It is exactly the "procedure outside the platform"
  the project's own invariant warns about, decaying in real time.

# ============ THE DELIVERABLE ============
# What of the lab is reproducible, and what died

## The one-line answer

**The commensurable half of the lab is exactly the unrunnable half.**
All ELEVEN scripts that score against the window's additions with the
prior-knowledge exclusion applied -- the only lab numbers that can stand
beside a platform number -- depend on `lafa_4layers.npy` or
`pool60k_4layers.npy`, and both files have been deleted. The 35 scripts that
score against the ancestor closure at release 227 are the ones whose inputs
mostly survive, and those are the numbers the lab itself says must not be
quoted.

Partition of the 115 numbered scripts, computed by grepping each file for the
probe banks it opens (`storage/encoder-study/scripts/`):

| status | n | what it means |
|---|---:|---|
| **BLOCKED by a deleted bank** | **33** | needs `lafa_4layers.npy` (52.9 GiB) or `pool60k_4layers.npy` (252.0 GiB); neither exists |
| runnable, its bank survives | 36 | uses `exp220`, `nk220`, `lafa_last`, `pool60k_last`, `nk_extra` or `confirmation` |
| no probe dependency | 47 | scoring, tables, publishing, ontology and cost scripts |

And the eleven that use the official-frame ground truth, every one blocked:

| script | what it produced | status |
|---|---|---|
| `25_by_category.py` | the nine-cell null, `fmax_by_category.json` | **BLOCKED** |
| `26_oracle_ceiling.py` | `oracle_ceiling.json`, per-cell oracle headroom | **BLOCKED** |
| `28_k_sweep.py` | `k_sweep.json`, K selection, 0 of 9 separating | **BLOCKED** |
| `30_k_sweep_pooled.py` | `k_sweep_pooled.json` | **BLOCKED** |
| `31_by_category_indomain.py` | `fmax_by_category_indomain.json` | **BLOCKED** |
| `32_conversion_curve.py` | **slope 0.94 and the 0.024-0.037 gate** | **BLOCKED** |
| `36_k_confirm.py` | `k_confirmation.json`, the registered 16-of-18 | **BLOCKED** |
| `37_depth_vs_quality.py` | **+0.0725 and +0.1747**, the shortlist curve | **BLOCKED** |
| `38_depth_fast.py` | `depth_vs_quality.json` | **BLOCKED** |
| `39_real_reranker_floor.py` | **the floor 0.0032 / 0.0293 / 0.0245** | **BLOCKED** |
| `41_code_as_feature.py` | `code_as_feature.json`, the two-consumer test | **BLOCKED** |

## Reproducible today, without a card

- **ontology-drift** (`storage/ontology-drift/`). Both OBO files are present,
  the two scripts read nothing else, and every figure recomputes.
  **Fully reproducible.** Date 2026-08-27, offline, wipe-immune.
- **Every JSON/NPZ receipt in `storage/encoder-study/artifacts/`** can be
  RE-READ and re-analysed (I did: the purity distribution, the K enumeration,
  the nine-cell recomposition, the conversion-slope refit, all without
  numpy). What cannot be done is re-DERIVING them.
- **The frozen recipe artifacts** (`storage/encoder-study/recipe/*.npz` and
  `artifacts/controls/*.npz`, plus `recipe/platform/*.pt`) are complete,
  self-describing, and loadable. The two 220-fitted ones are admissible for
  the campaign frame and have never been scored.
- **The deployed encoder bundle** (`storage/encoder/`): `encoder.pt`,
  `MANIFEST.json`, `VALIDATION.json`, `EMBEDDING_RECIPE.json`, `IA.tsv`, and
  the 575,503-row bank. Complete.
- **The 21 rescued evaluation bundles**
  (`storage/rescue/minio/protea/eval_artifacts/`, 464 MB, 2026-08-02): the
  numbers are complete, the frames are gone (20 of 21 anonymous).
- **calibration-study** (`storage/calibration-study/`): post-wipe, on the
  campaign's own grids. Re-runnable only while the object store keeps
  `eval_artifacts/<id>/{NK,LK,PK}/per_protein_grid.parquet`; nothing is
  cached in storage but `calib.json`, `calib2.json`, `pk13.csv`, `pk_all.csv`.

## Reproducible only after a card pass

- Anything needing `lafa_4layers.npy` or `pool60k_4layers.npy`: **304.9 GiB
  of forward passes** (7,401 + 60,000 proteins, 4 layers each, float32
  768-wide). `110_ceiling.json` puts a corpus pass with esm2-3B at 25.8 hours;
  ankh-base at 4 layers over 26.6M residues is the relevant cost and it is
  not recorded anywhere.

## Dead, with no producer

- `storage/learned_encoders/`, `storage/fullgo_models/`,
  `storage/cooc_experiment/`, `storage/regen_headline/` -- all cited in
  `agent-farm/plans/`, none exists. Taken by the 2026-07-28 reinstall. The
  old lab's results survive ONLY where they were committed, in
  `protea-reranker-lab/{research,results,experiments,datasets}`.
- `protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json` --
  cited twice in `plans/prior-knowledge-wall/PLAN.md` as the receipt that
  REFUTES another slice's central claim. Never existed in git, not on disk.
- The frames of 20 of the 21 rescued evaluation bundles.
- Any pre-2026-08-27 registry row: the rescue dump stopped after two tables
  and wrote no `MANIFEST.json`.

## At risk on this disk only, nowhere else

- The 115 encoder-study scripts + 15 chain scripts: **in no repository**.
- The library they import: **16 commits on `feat/gate-bundle-loader` that
  exist on no remote**, held in the worktree `worktrees/lab-bundle` at
  `d1ee10ba`. `probe_store.py` is not on develop.
- `worktrees/sparse-encode`, `worktrees/pooled-uri`, `worktrees/pooled-order`
  -- imported by six more scripts, same exposure.
- `storage/worktree_salvage/` (48 KB) already holds two rescues of exactly
  this kind: `sparse-encode-20260819-1440/encode_residue_sparse.py` and
  `sparse_bank_probe_2026-08-18/{README.md,bank_diag.py,bank_ksweep.py,collision_contrast.py}`.
  So the failure mode has fired twice already and been salvaged by hand.

## The four things a reader must not miss

1. **"Retrieval converts to Fmax at slope ~1" is a two-point line to an
   oracle.** On the four real arms the median slope is 0.7447 and the per-cell
   values run -0.063 to +1.557. Everything gated on "0.024 to 0.037" inherits
   it.
2. **The lab's flagship comparison (0.0842 backbone vs 0.0006 order) puts a
   platform-produced number beside a lab-produced one** at a "matched budget"
   that buys 4.97 donors on one side and 1.41 on the other.
3. **The frozen recipe still recommends 2-bit codes**, which the same study
   later measured as losing 0.0243 in 4 of 4 identity bands. It is the one
   defect here that would cause a wrong deployment today.
4. **The `agent-farm/plans/` store contains none of it.** SIGNAL-REGISTRY.md
   stops at 2026-07-27; every encoder-study number lives only in an
   unsynchronised per-machine memory store and in 130 untracked files.

## The operations that would let this be reborn writing to the database

In priority order, each named by what it unblocks:
1. `extract_residue_probe` -- a per-residue, multi-layer probe as a registered
   artifact. Without it the 33 blocked scripts stay blocked forever and
   nothing of this shape can be measured again. **MURO today:**
   `encode_residue_sparse` computes residues transiently and stores one code
   per sequence; the platform embedding cache is strictly 2D.
2. Close the four gaps in `encode_residue_sparse` (`DEPLOYMENT-AUDIT.md` step
   0: ArtifactStore instead of a local path, device from settings, backend
   capability check, queue declaration), then publish the recipe and register
   the configuration. This is what makes any lab arm scorable on the campaign
   frame at all.
3. Score `cut220-residue-*.npz` and `exp220-residue-*.npz` on the 220->230
   frame. Both artifacts exist and both say "not yet scored on the official
   frame". Cheapest open number in the slice.
4. Dispatch `limit_per_entry` in {5, 10} beside 30. No code at all; the field
   already exists on `PredictionSet`.
5. Write the evaluation payload beside every `eval_artifacts/<id>/` bundle,
   so a rescued artifact carries its own frame. The 21 anonymous bundles are
   the argument.
6. A `training_release` field on any registered encoder, checked against the
   window start at dispatch. `MANIFEST.json` already carries it; nothing
   reads it.
7. An operation-level throughput metric, so `sample.sh` can be retired
   before it corrupts another file.


---

## Bookkeeping correction, for internal consistency of this file

`storage/encoder-study/scripts/` holds **116 `.py` files**: 115 numbered
(`01_`..`115_`) plus `bank_cache.py`, and 15 `chain_*.sh` / `queue_*.sh` /
`gpu_queue.sh` / `run_all.sh`. The partition 33 blocked / 36 runnable /
47 no-probe sums to 116 and includes `bank_cache.py` in the no-probe group.
Where this file says "33 of 115" read "33 of the 116 python files". Script
`115_panel_populations_experimental_baseline.py` (2026-08-26 21:53) has no
artifact of its own -- it is the last thing written in the study and it
appears never to have produced output.
