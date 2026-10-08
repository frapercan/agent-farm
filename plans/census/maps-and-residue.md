# Slice: maps-and-residue

Auditor slice: the PLAN STORE ITSELF as a document corpus.
Files: plans/CATALOG.md, CONCEPT-MAP.md, COMPOSITION-MODEL.md, REQUIREMENTS.md,
ROADMAP-NEXT.md, ROADMAP-THESIS-10.md, PLAN.md, SDR-PROGRAM.md, THESIS-FINISH.md,
plans/archive/, plus the hunt for PRE-CAMPAIGN RESIDUE THAT IS NOT IN archive/.

Method: for every file and directory under plans/, get (a) the date of its last
substantive content change and (b) the date of the EVIDENCE it cites. Output the
list of documents that LOOK current and are not. Name what to retire.

Two dates that decide everything:
- 2026-07-28 OS reinstall, storage/ nominally not restored.
- 2026-08-27 EXPERIMENT REGISTRY WIPED. Any measured result dated before this is
  not evidence about the current window.

Status: IN PROGRESS (appending as I go).

---

## FINDING 1: mtime in plans/ is a RESTORE ARTIFACT and hides a 3.5-month age spread

verdict: CONFIRMED
first number: `ls -la plans/` shows 15 of 24 top-level files with mtime `Jul 28 17:01`,
  identical to the second. Directory mtimes: all 22 slice dirs are `Jul 28 17:01`.
second number (INDEPENDENT, derived): `git log -1 --date=short` per file gives the real
  date of last substantive content change. Spread is 2026-05-16 to 2026-09-02.
date of evidence: 2026-07-28 (the reinstall restore) -> window: pre-wipe
frame: n/a (document metadata)
population: n/a
platform gap: MURO. This is a filesystem restore artifact, not a producible fact.
note: **Anyone who dates the plan store by `ls` will read the entire corpus as one
  cohort dated the reinstall day.** It is not. The uniform 17:01 is the moment the
  Thesis2-meta snapshot was unpacked. Use `git log`, never mtime, on anything under
  agent-farm/. This alone invalidates any staleness triage done by directory listing.

### The real content-date table (git, last substantive commit touching the file)

| file | last content change | commit | pre/post 07-28 reinstall | pre/post 08-27 wipe |
|---|---|---|---|---|
| plans/README.md            | 2026-05-16 | 8787928 | PRE  | PRE |
| plans/ROADMAP-THESIS-10.md | 2026-06-11 | 7fd365f | PRE  | PRE |
| plans/REQUIREMENTS.md      | 2026-06-16 | 7c05ec4 | PRE  | PRE |
| plans/THESIS-FINISH.md     | 2026-06-16 | 7c05ec4 | PRE  | PRE |
| plans/CATALOG.md           | 2026-06-22 | 13b7eeb | PRE  | PRE |
| plans/CONCEPT-MAP.md       | 2026-06-22 | 567ca98 | PRE  | PRE |
| plans/ROADMAP-NEXT.md      | 2026-06-22 | 364bf8a | PRE  | PRE |
| plans/SDR-PROGRAM.md       | 2026-06-22 | 364bf8a | PRE  | PRE |
| plans/PLAN.md              | 2026-07-17 | 6d66f12 | PRE  | PRE |
| plans/SIGNAL-REGISTRY.md   | 2026-07-27 | f0e50a6 | PRE  | PRE |
| plans/E2E-CANONICAL-RUN.md | 2026-07-27 | f0e50a6 | PRE  | PRE |
| plans/GENESIS-STATE.md     | 2026-07-28 | 8668180 | ON   | PRE |
| plans/SCORER-PROVENANCE.md | 2026-07-28 | 8668180 | ON   | PRE |
| plans/CAMPAIGN.md          | 2026-07-28 | 0263cfa | ON   | PRE |
| plans/COMPOSITION-MODEL.md | 2026-07-28 | 0263cfa | ON   | PRE |
| plans/DECISION-LOG.md      | 2026-07-28(c)/2026-08-29(mtime) | 0263cfa | ON | see F-x |
| plans/FIRST-BOOT.md        | 2026-07-28 | c56382a | ON   | PRE |
| plans/rungs.yaml           | 2026-08-23 | c76588a | POST | PRE |

**EVERY file in my slice (CATALOG, CONCEPT-MAP, COMPOSITION-MODEL, REQUIREMENTS,
ROADMAP-NEXT, ROADMAP-THESIS-10, PLAN, SDR-PROGRAM, THESIS-FINISH) last changed
substantively BEFORE 2026-08-27.** Not one of them has been revised since the
experiment registry was wiped. They describe a research state that no longer has
receipts in the database.
---

## FINDING 2: TWO large plan documents are UNTRACKED, residue in plans/, not in archive/, not in git

verdict: CONFIRMED
first number: `git status --porcelain plans/` returns exactly two lines:
  `?? plans/ABLATION-ARCHITECTURE.md`  (46,593 bytes, mtime 2026-08-17 09:27)
  `?? plans/LEARNED-REPRESENTATION-ABLATION.md` (42,459 bytes, mtime 2026-08-17 09:19)
second number (INDEPENDENT): these are the ONLY two files in the whole 24-file top level
  of plans/ whose mtime is NOT `Jul 28 17:01` and which are also absent from git. Every
  other non-17:01 file (COLLIDING-A-NUMBER.md, DECISION-LOG.md, ORCHESTRATION.md,
  TOPOLOGY.md, DECLARED-REVISION.txt, rungs.yaml) is tracked.
date of evidence: 2026-08-17 -> window: PRE-WIPE (10 days before 2026-08-27)
frame: see below, they declare their own and it is not the campaign's
population: see below
platform gap: MURO for the documents themselves; but they name the operations that
  would have to exist. See FINDING 3.
note: 89 KB of the most numerically dense design reasoning in the plan store is
  **outside version control on a machine that "gets rebooted without warning" and that
  CLAUDE.md says holds no state.** A `git clean` in agent-farm destroys both. They are
  not in `plans/archive/`, they are not on any branch, they are not referenced by
  CATALOG.md. They are the single most fragile artifacts in my slice.

### What they contain that nothing else does

`ABLATION-ARCHITECTURE.md` is a full re-derivation of the ablation geometry from a
measured per-cell population file, and it OPENS by contradicting the design that reached
it. Quoted from its preamble:

> "The counts are 354, 161 and 243 for no-knowledge BPO, CCO and MFO; 307, 181 and 180
>  for limited-knowledge; and 2,382, 809 and 1,057 for prior-knowledge. They sum to
>  5,674 protein-aspect units, of which 4,248 (74.9 per cent) are prior-knowledge.
>  Every design that reached me assumed between 11,800 and 13,054 units, derived from an
>  assumed 1.9 to 2.1 aspects per protein. The real figure is 0.913 aspects per protein"

That is a >2x population error in every prior design, caught by reading an artefact.
Source artefact named: `agent-farm/plans/farm-platform/artefacts/knn_226_227_fmicrow.csv`.

`LEARNED-REPRESENTATION-ABLATION.md` section 1 is an eight-paragraph demolition of the
+0.530 / +0.467 encoder result, each paragraph a separate defect with a line number.
---

## FINDING 3: the untracked ABLATION-ARCHITECTURE.md is RIGHT, and I reproduced it independently

verdict: CONFIRMED (its population claim, and its K claim)
first number: ABLATION-ARCHITECTURE.md preamble (untracked file, line 5): per-cell
  counts 354/161/243 (NK BPO/CCO/MFO), 307/181/180 (LK), 2,382/809/1,057 (PK),
  "sum to 5,674 protein-aspect units, of which 4,248 (74.9 per cent) are prior-knowledge",
  "The real figure is 0.913 aspects per protein".
second number (INDEPENDENT, my own recomputation): I parsed
  `/home/xaxi/Thesis2/agent-farm/plans/farm-platform/artefacts/knn_226_227_fmicrow.csv`
  (216 data rows, 215 ok + 1 `no_positives`) with csv.DictReader and summed
  `n_proteins` over the nine cells for `esm2_650m` K=3:
  354,161,243,307,181,180,2382,809,1057 -> **5,674**; PK = 4,248 = **74.9%**.
  0.913 aspects/protein implies 6,215 proteins; 5674/0.913 = 6,215.0 exactly.
  EVERY digit reproduces.
date of evidence: the CSV is `knn_226_227_fmicrow` = the 226->227 validation window.
  -> window: **PRE-WIPE and PRE-REINSTALL.** Its own .md header calls it "FARM-EXP.15".
frame: `f_micro_w`, IA-weighted micro-F, "v227 LAFA-aligned IA", KNN-only score =
  1 - cosine distance. NOT Fmax. Grid 8 PLM x K[3,5,10] x 9 cells = 216.
population: 6,215 proteins -> 5,674 protein-aspect units, 74.9% prior-knowledge.
  The SERVED (NK) cells hold 354/161/243 = 758 units, **13.4% of the total.**
platform gap: `knn_226_227_fmicrow.csv` is a flat file in a plan directory. No operation
  in the registry produces it. To be reborn writing to the database it needs a KNN-only
  baseline operation that emits per-cell (plm, K, regime, aspect, f_micro_w, n) rows to
  `evaluation_result`. It currently has none, so the file is the ONLY copy.
note: **The metric is f_micro_w, not Fmax.** Anything that quotes these numbers as Fmax
  has changed frame silently. Also `n_proteins` is here used as the cell population --
  see the memory note that `n_proteins` is NOT a population, it moves with tau.

## FINDING 3b: the population mismatch across K rows is REAL, and I quantified it

verdict: CONFIRMED
first number: ABLATION-ARCHITECTURE.md: "the 'seven of eight' figure compares arms
  scored on different populations under the same column heading."
second number (INDEPENDENT): summing `n_proteins` over 9 cells per (plm, K):

| plm | K=3 | K=5 | K=10 | K3-vs-K10 matched? |
|---|---|---|---|---|
| ankh_base  | 5674 | **2238** | 5674 | YES |
| ankh_large | **1472** | 5674 | 5674 | NO |
| esm2_150m  | 5674 | 5674 | 5674 | YES |
| esm2_3b    | 5674 | 5674 | 5674 | YES |
| esm2_650m  | 5674 | 5674 | 5674 | YES |
| esmc_600m  | **2238** | **2238** | 5674 | NO |
| prostt5    | **2238** | 5674 | 5674 | NO |
| prot_t5    | 5674 | 5674 | 5674 | YES |

Five of eight models have a MATCHED K=3 vs K=10 comparison. In all five, K=3 beats K=10
in **9 of 9 cells** (45/45 cells). Three models (ankh_large, esmc_600m, prostt5) have NO
matched K comparison: their K=3 row is scored on a 1,472- or 2,238-unit subcohort against
a 5,674-unit K=10 row. `ankh_large` K=3 is on **26% of the cohort**.
date of evidence: pre-reinstall (226->227) -> window: pre-wipe
frame: as above, f_micro_w
population: 5,674 vs 2,238 vs 1,472 -- three different populations under one heading
platform gap: MURO for the historical rows; the fix is a run-level population assertion,
  which is exactly the standing norm "Assert the population, never ORDER BY".
note: the direction of the K result SURVIVES (5/5 matched models, 45/45 cells), but the
  COUNT does not. "Seven of eight" and "24 of 24" are counts over a mixed population.
  This is the declaration-gap shape again: a plausible number over the wrong population.
---

## FINDING 4: "24 of 24" and "seven of eight" are ORPHAN CLAIMS with no findable source

verdict: NOT_FOUND (as a measurement); the claim exists only in an untracked document
first number: LEARNED-REPRESENTATION-ABLATION.md:17 and :39 assert
  "that axis closed at 24 of 24, K=3 wins in seven of eight models, and the decay is
   monotone in seven of eight" and "K equals 3, because the K ablation closed at 24 of 24".
second number (INDEPENDENT): on the only artefact that could support it
  (knn_226_227_fmicrow.csv, 8 models x 3 K x 9 cells), the matched-cohort count is
  **5 of 8 models**, and 3 of 8 have no matched comparison at all. 24 does not appear
  as any natural count of that grid: 8x3=24 rows-per-cell, but a "24 of 24" WIN count
  cannot be formed because K=3 vs K=10 gives 8 comparisons, K=3 vs K=5 gives 8, and
  9 cells x 8 models = 72.
WHERE I SEARCHED (a negative check counts only if you looked where it would be):
  - `grep -rn "24 of 24\|seven of eight\|7 of 8\|7/8"` over ALL of
    /home/xaxi/Thesis2/agent-farm/plans/  -> 3 hits, all inside the two UNTRACKED files
  - same grep over /home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/ -> 0 hits
  - same grep over /home/xaxi/Thesis2/repositories/ (all 8 repos) -> 0 hits
  - same grep over /home/xaxi/Thesis2/thesis/ -> 0 hits
  The nearest thing in the memory store is a DIFFERENT count:
  "Thirty neighbours is too many; use 3 to 10: **16 of 18** comparisons across two
   populations and two encoders" (2026-08-19).
date of evidence: 2026-08-17 (the assertion) -> window: pre-wipe
frame: unstated in the assertion. The artefact it would have to come from is f_micro_w
  on 226->227; the memory's 16-of-18 is a different study on different populations.
population: unstated
platform gap: MURO -- there is no stored K-ablation result to point at.
note: **The same untracked pair contains one document that catches this class of error
  (ABLATION-ARCHITECTURE.md, explicitly: "the 'seven of eight' figure compares arms
  scored on different populations") and another that repeats it twice as settled
  (LEARNED-REPRESENTATION-ABLATION.md).** Both are dated within 8 minutes of each other
  (09:19 and 09:27 on 2026-08-17). The correction was written and never propagated
  8 minutes sideways. If either is ever committed, commit the correcting one.
---

## FINDING 5 (THE HEADLINE): the retirement was DECLARED on 2026-07-27 and NEVER EXECUTED

verdict: CONFIRMED
first number / quote: `plans/E2E-CANONICAL-RUN.md:12-16` (committed 2026-07-27, f0e50a6):
> "It SUPERSEDES, for the definition of the scientific run, the June roadmaps
>  (`ROADMAP-THESIS-10.md`, `THESIS-FINISH.md`, `beat-lafa-1/`). Those carried the
>  old window convention (SELECT 220->227 / FINAL 227->230, a mixed-metric story)
>  and the pre-scale corpus. **They move to `plans/archive/` for provenance**;
>  their governing principles are inherited verbatim below."

second number (INDEPENDENT, my own filesystem check):
  `ls plans/archive/` returns exactly SEVEN directories:
  lafa-improve, lafa-levers, lafa-number-one, reranker-vnext, score-ablation, sdr,
  thesis-cuts. **None of the three named documents is among them.**
  `plans/ROADMAP-THESIS-10.md` -> still at the store ROOT (22,213 bytes)
  `plans/THESIS-FINISH.md`     -> still at the store ROOT (12,394 bytes)
  `plans/beat-lafa-1/`         -> still a TOP-LEVEL slice directory
  `git log -1` on each: 2026-06-11, 2026-06-16, (dir) -- i.e. no commit has touched
  them since the supersession was written. The move was never made, in git or on disk.
date of evidence: declaration 2026-07-27 -> window: pre-wipe; the documents themselves
  2026-06-11 / 2026-06-16 -> window: pre-wipe AND pre-reinstall.
frame: the superseded docs carry the OLD window convention, named in the supersession
  itself: SELECT 220->227 / FINAL 227->230, "a mixed-metric story", pre-scale corpus.
  The current frame is 220->230 (see the memory note that stored evaluations pool both
  cohorts). **So these documents are not merely old, they are in a DIFFERENT FRAME,
  and the supersession says so explicitly.**
population: pre-scale corpus (unstated size), against the current three-tier corpus.
platform gap: MURO -- this is a document-hygiene action, not a computation. It costs
  three `git mv`s and one CATALOG rewrite.
note: **This is the single most consequential thing in my slice.** A reader opening
  `plans/` today sees ROADMAP-THESIS-10.md and THESIS-FINISH.md sitting at the root
  next to CAMPAIGN.md, all with the identical mtime `Jul 28 17:01`, with nothing on
  their face marking them superseded, and with `CATALOG.md` -- the document that calls
  itself "Single entry point to the plan store" -- still listing
  `ROADMAP-THESIS-10.md` as "**Still the north-star roadmap**".
  The three files carry no `SUPERSEDED` banner (unlike archive/lafa-number-one/
  NEURAL-HEAD.md, which does carry one on line 1). The supersession is discoverable
  ONLY by reading line 12 of a fourth document.

## FINDING 6: CATALOG.md and CAMPAIGN.md cannot both be current, and CATALOG loses

verdict: CONFIRMED (CATALOG.md is stale and actively misleading)
first number: `CATALOG.md:1` "# Plan store catalog (2026-06-22)" and `CATALOG.md:16`
  "| **beat-lafa-1** | **ACTIVE - canonical** | The current campaign to surpass LAFA #1
   ... Best confirmed native = **0.3745** (EvalResult `b21b187c`). Bottleneck = PK
   precision. |" -- one canonical campaign, one number, one bottleneck.
second number (INDEPENDENT): `CAMPAIGN.md` (2026-07-28, 0263cfa) section 5 "THE
  EXPERIMENTAL LADDER" line 283: "Five rungs. Each has one question, one gate".
  Rungs 1-5 at lines 289, 347, 403, 416, 434. And `CAMPAIGN.md` §0bis: "No prior
  result is preserved as a number; results are regenerated."
  **CAMPAIGN.md never mentions beat-lafa-1 once** (grep over CAMPAIGN.md,
  SIGNAL-REGISTRY.md, GENESIS-STATE.md, DECISION-LOG.md, COMPOSITION-MODEL.md,
  rungs.yaml -> 0 hits). The only post-June documents that name it are CONCEPT-MAP.md
  (itself 2026-06-22) and E2E-CANONICAL-RUN.md, which names it *to retire it*.
date of evidence: CATALOG 2026-06-22 vs CAMPAIGN 2026-07-28 -> 36 days apart, both
  pre-wipe.
frame: CATALOG's 0.3745 is "native productized" f_micro_w on the OLD window (220->227
  select / 227->230 final). CAMPAIGN's ladder is gated on retrieval quality until the
  last rung, on the 220->230 frame. Different frames, different metrics.
population: CATALOG quotes an aggregate (0.3745). Per the standing norm, an aggregate
  over an evaluation set is ~95% prior-knowledge; the served NK population is ~5%.
  `beat-lafa-1/PLAN.md:5` does give the split: "0.3745 (NK 0.4645 / LK 0.4526 /
  PK 0.2065)" -- so the aggregate sits between LK and PK and describes no cell.
platform gap: the EvalResult id `b21b187c` cited by CATALOG.md is a database row.
  **The experiment registry was wiped 2026-08-27; the live DB holds only 93
  evaluation_result rows, all created 2026-08-27..30.** So `b21b187c` is a DANGLING
  RECEIPT: the catalog's headline number points at a row that no longer exists and
  which no operation reproduces. Under CAMPAIGN.md §0bis's own rule ("An artifact that
  cannot be produced cannot be cited"), 0.3745 is retired.
note: RETIRE CATALOG.md, or rewrite it. It is the store's declared "single entry
  point" and it points every reader at a campaign that a later document retired, with
  a headline number whose receipt was wiped.
---

## FINDING 7: the plan store cites 16 database row ids as receipts; ALL predate the wipe

verdict: CONFIRMED
first number: my own scan. `python3` walk over every `.md`/`.yaml`/`.txt` under
  `plans/`, regex `\b[0-9a-f]{8}\b` (excluding all-digit matches), 193 total
  identifier mentions across 30 files.
second number (INDEPENDENT, the tighter one that matters): requiring an ORM/table
  keyword on the SAME line (EvalResult|PredictionSet|AnnotationSet|RerankerModel|
  EmbeddingConfig|evaluation_result|prediction_set|annotation_set|run_id) leaves
  **16 lines citing a database row as evidence**:

| file:line | id(s) | what it is cited as |
|---|---|---|
| CATALOG.md:16 | b21b187c | EvalResult, "Best confirmed native 0.3745" |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:10 | b21b187c | same, "Best confirmed native number" |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:74 | cb77d55d | EvalResult, IA "+0.0033 TEST (0.3689->0.3722)" |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:96 | 1df357be | EvalResult, "clean-15 REFUTED, 0.3660 < 0.3722" |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:71 | 3f281105/71890148/15568a5b | RerankerModel trio |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:81 | d2dc467c/70ebcced/e9c946d9 | RerankerModel trio |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:90 | f0669e41, 198baf99/68f3232c | RerankerModel pk / nk-lk |
| beat-lafa-1/CAMPAIGN-DOSSIER.md:99 | ed589978/4ab529bc/7b4ff840 | RerankerModel trio |
| representation-science/PLAN.md:276 | 6542db1e | EmbeddingConfig, "739554 chunks, materialised" |
| temporal-eval-alignment/PLAN.md:80 | c905dffa | annotation_set, "GOA 227" |
| productization/PRODUCTIZATION-ROADMAP.md:15 | 7fcecf26 | live reranker trio, `is_active=true` |
| productization/PRODUCTIZATION-ROADMAP.md:16 | d8979601, 851849df | retrieval config + S2e trio |
| bioinfo-quick/PLAN.md:48,109 | 3517bc8b | Dataset row, "published 2026-05-14" |
| archive/score-ablation/STAGED-A-SCORE-prep.md:48,52 | 1559d9f7, a3be0a6d | annotation_set, eval_set |

date of evidence: every one of these documents last changed **before 2026-08-27**.
  The newest is representation-science/PLAN.md; the oldest cite 2026-05-14.
  -> window: **pre-wipe, all sixteen.**
frame: various and mostly unstated; the beat-lafa-1 ones are f_micro_w on the old
  SELECT 220->227 / FINAL 227->230 convention.
population: aggregates, except beat-lafa-1/PLAN.md:5 which splits 0.3745 into
  NK 0.4645 / LK 0.4526 / PK 0.2065.
platform gap: **this is the platform gap, stated as a count.** The live registry holds
  93 evaluation_result and 19 prediction_set rows, all created 2026-08-27..30. Every id
  above was created before that. To be reborn each needs a registered operation that
  regenerates the row; CAMPAIGN.md §0bis was written precisely to force this and says
  so: "several rows of the signal registry currently cite paths that no operation
  produces, and under this rule those rows are unsupported until the run regenerates
  them."
note: I did NOT query the database (hard constraint). I am dating the CITATIONS, not
  probing the rows. The claim is that every citing document predates the wipe, which is
  established from git alone. **A reader who follows any of these 16 ids to look up its
  receipt will find nothing, and the document gives no warning that it should.**
  The deltas at stake are small enough to matter: cb77d55d carries +0.0033 and 1df357be
  carries a REFUTATION at a 0.0062 margin, both below several of this project's own
  documented resolution floors (the encoder study's floor is 0.0013; stored metrics are
  rounded to four decimals).
---

## FINDING 8: CONCEPT-MAP.md declares itself a LIVING document and has ONE commit, ever

verdict: CONFIRMED
first number: `CONCEPT-MAP.md:1-9`: "# PROTEA / thesis concept map (living document)
  ... The complete conceptual map of the project, **held and updated at all times**
  ... Built 2026-06-22 ... **Keep it current as work proceeds**; cite section numbers
  when planning."
second number (INDEPENDENT): `git log --format=... -- CONCEPT-MAP.md` returns exactly
  ONE line: `2026-06-22 567ca98 plan(concept-map): living conceptual map of the whole
  project (#195)`. Zero revisions in the **72 days** to 2026-09-02. Compare
  COMPOSITION-MODEL.md (2 commits) and DECISION-LOG.md (revised through 2026-08-29).
date of evidence: 2026-06-22 -> window: pre-reinstall AND pre-wipe
frame: it carries the OLD headline pair: "LAFA: **0.391 offline** (sealed champion,
  source files deleted) / **0.3745 native**" (CONCEPT-MAP.md:22).
population: aggregate only.
platform gap: MURO (document hygiene).
note: it ships its own staleness vocabulary and never used it after birth. Its legend
  offers `[ok] [partial] [gap] [stale]`; the body carries 2 `[ok]`, 5 `[partial]`,
  1 `[gap]` and **3 `[stale]` markers that were already there on day one**. A document
  that marks three of its own fronts stale at birth and is then never touched is not a
  living map, it is a snapshot with a promise attached. **A reader is instructed by its
  own first paragraph to trust it as current.** Retire or re-date.

## FINDING 9: THREE different "sealed offline champion" numbers are live in the store

verdict: CONFIRMED (a live, unreconciled three-way disagreement)
first number: `CONCEPT-MAP.md:22` -- "**0.391 offline** (sealed champion, source files
  deleted)". Also `beat-lafa-1/CAMPAIGN-DOSSIER.md:14` "sealed OFFLINE champion =
  **0.391** (#1, ahead of TransFew), but frame-optimistic" and
  `archive/lafa-number-one/NEURAL-HEAD.md:1` "PROTEA reached first place on LAFA
  (mean 0.391, ahead of TransFew 0.381)".
second number: `thesis-clean-iteration/PLAN.md:17,44,102`, `AUTONOMOUS-RUN.md:36`,
  `NARRATIVE.md:198`, `productization/PRODUCTIZATION-ROADMAP.md:6,17` -- **0.4063**,
  and twice called **"immutable"**: "The sealed 0.4063 (#1 in 7 of 9 cells) is
  immutable" (AUTONOMOUS-RUN.md:36); "**The sealed 0.4063 is immutable.**" (NARRATIVE.md:198).
third number: `SIGNAL-REGISTRY.md:277` -- "the only framing matching the **sealed
  0.40765**".
INDEPENDENT check: `grep -rn "0\.4063\|0\.40765" plans/` -> 0.4063 in 6 places across
  4 files, 0.40765 in exactly 1 place (SIGNAL-REGISTRY.md). 0.391 in 12 places.
  **No document in plans/ reconciles them.** The memory store does
  (`project_sealed_headline_is_a_projection_2026_08_24.md`: "The sealed 0.4063 is a
  PROJECTION; the board measured 0.40765"), and **that reconciliation has never been
  written back into the plan store.**
date of evidence: 0.391 documents 2026-06-14..22; 0.4063 documents ~2026-07-09..;
  0.40765 note 2026-07-27 (SIGNAL-REGISTRY); the memory correction 2026-08-24.
  -> window: ALL pre-wipe.
frame: **this is the frame problem exactly.** 0.391 is described as "frame-optimistic";
  0.4063 as `f_micro_w`, 9-cell board-faithful, "#1 in 7 of 9"; 0.40765 as what the
  external board measured. thesis-clean-iteration/PLAN.md:14-17 names the wrong frames
  the thesis was organised around: "the *wrong* metric (macro cafaeval-Fmax), the
  *wrong* frame (GOA 220->229/226->230), the *wrong* backbone (ESMC-300M)".
population: 9 cells; "#1 in 7 of 9" is a per-cell win count, not an aggregate claim,
  and it is the only one of the three headlines that is stated per-cell.
platform gap: the 0.391 lineage is explicitly unreproducible -- CONCEPT-MAP.md:22
  "(sealed champion, **source files deleted**)" and CAMPAIGN-DOSSIER.md:147
  "Champion's offline sources are deleted -> 0.391 not byte-reproducible."
  0.4063's board injection is by hand: PRODUCTIZATION-ROADMAP.md:17 records the
  delivery mechanism as "**manual file write** via
  `protea-lafa-knn/score_and_inject_windows.sh`" -- i.e. no operation, direct violation
  of CAMPAIGN.md §0bis.
note: the word "immutable" applied to 0.4063 in two documents is the danger. A number
  that a later memory calls a PROJECTION is recorded in the plan store as immutable,
  in documents nobody has revised. **Anyone drafting the thesis from plans/ alone will
  write 0.4063 as a measured headline.**
---

## CORRECTION TO FINDING 2 (self-caught, and the correction is itself a finding)

verdict: FINDING 2 was TRUE WHEN OBSERVED and is now PARTIALLY MITIGATED. I am not
editing it away; the sequence is the evidence.

What happened, in order, with timestamps:
1. At the start of this audit, `git rev-parse --abbrev-ref HEAD` = **plans/orchestration**
   and `git status --porcelain plans/` returned exactly:
     `?? plans/ABLATION-ARCHITECTURE.md`
     `?? plans/LEARNED-REPRESENTATION-ABLATION.md`
   Both were genuinely untracked. Finding 2 is a correct observation of that moment.
2. Later in the same session, HEAD had moved to **plans/preserve-untracked-ablations**
   and `git status --porcelain plans/` returned EMPTY. Commit **bb06515**,
   `2026-09-02 01:44:27 +0200`, "plans: bring the two untracked ablation documents
   under version control", +351 lines, adds both.
3. `git branch -a --contains bb06515` -> only `plans/preserve-untracked-ablations`
   and its origin copy. **`origin/main` still does NOT contain either file**
   (`git cat-file -e origin/main:plans/ABLATION-ARCHITECTURE.md` ->
   "existe en disco, pero no en 'origin/main'"). origin/main tip is d06f75d.

So: the risk was real, another actor in this farm rescued the files onto a branch
mid-audit, and **they are still not on main.** A branch is not a delivery channel
(the project's own standing norm about internal deps says exactly this). Until that
branch merges, the two documents exist on main only as a disk copy on a machine that
CLAUDE.md says "holds no state" and "gets rebooted without warning."

**Two consequences a reader must not miss:**
(a) `git status` in agent-farm is NOT stable during a multi-agent session. My own big
    date table below was generated AFTER the move, so it reports the two ablation
    documents as **2026-09-02** -- that is the RESCUE COMMIT date, not the content date.
    Their real content date is **2026-08-17** (mtimes 09:27 and 09:19, and the mtime
    is trustworthy here precisely because it is NOT the Jul 28 17:01 restore stamp).
(b) This is a live instance of the project's own hard constraint: "ALWAYS check
    `git status -sb` before any merge/edit/build/restart (other agents may have moved
    HEAD between turns)." I checked at the start, acted on it, and the answer expired.
    **Re-check before quoting any git fact from this file.**
---

## FINDING 10: the slice execution system FROZE in June; the rendered master is honest, the CATALOG is not

verdict: CONFIRMED
first number: `PLAN.md:6` (the rendered master, last commit 2026-07-17):
  "**Status**: 1 in_progress · 3 blocked · 108 pending · 207 done · 14 deferred ·
   **total 333**"
second number (INDEPENDENT, my own parse): I re-implemented render.py's
  `SECTION_RX = ^### (.+?)\n```yaml\n(.+?)\n```` over all 19 `plans/<loop>/PLAN.md`
  and counted `status:` in the frontmatter. Result:
  **total 333, done 207, pending 108, deferred 14, blocked 3, in_progress 1.**
  Every figure matches PLAN.md exactly. **The render gate is holding; PLAN.md is NOT
  stale relative to its inputs.** (I did not run render.py, to avoid its writer path.)
THE REAL FINDING is what that stability means. Git dates of the five loops CATALOG.md
  marks ACTIVE:
  | loop | CATALOG status | last commit to its PLAN.md | days idle to 2026-09-02 |
  |---|---|---|---|
  | executor      | **ACTIVE** 78/119 | 2026-06-11 | 83 |
  | thesis-writer | **ACTIVE** 28/40  | 2026-06-07 | 87 |
  | farm-platform | **ACTIVE** 71/112 | 2026-06-24 | 70 |
  | doc-writer    | idle 16/16        | 2026-06-07 | 87 |
  | bioinfo-quick | idle 10/12        | 2026-05-18 | 107 |
  My independent per-loop counts reproduce CATALOG's numbers for 4 of 5 rows exactly
  (thesis-writer 28/40, doc-writer 16/16, farm-platform 71/112, bioinfo-quick 10/12).
  executor is the one mismatch: CATALOG says "78/119 done, 2 blocked", I count
  **done=76, blocked=2, pending=37, deferred=4**. 76+2=78, so CATALOG appears to have
  counted the two BLOCKED slices as done.
date of evidence: the loop files 2026-05-18..2026-06-24 -> window: pre-reinstall,
  pre-wipe. **Not one slice file has moved since 2026-06-24, i.e. 70 days.**
frame: n/a (slice bookkeeping)
population: 333 slices across 19 loops
platform gap: MURO -- but note the shape. CAMPAIGN.md's ladder (rungs 1-5) and
  rungs.yaml (2026-08-23) are where work actually happened after June. **The rung
  system and the slice system are two parallel plan mechanisms and they do not
  reference each other**: `grep beat-lafa` over rungs.yaml -> 0 hits; the slice loops
  contain no rung. The 333-slice machine is a second, abandoned planning surface.
note: CATALOG.md's counts are still *arithmetically* correct precisely BECAUSE nothing
  has moved. A stale document that agrees with reality because reality stopped is the
  hardest kind to spot by checking its numbers. **Check the DATE, not the number.**

## FINDING 11: 108 pending slices, and 13 of 19 loops report nothing pickable

verdict: CONFIRMED
first number: `PLAN.md:8-40` "## Next up (per loop)". `grep -c "nothing pickable"`
  = **13**, against 19 loops listed.
second number (INDEPENDENT): of the 108 pending slices, the six loops with pickable
  work are dag-scheduler (7 pending), executor (37), farm-platform (35),
  prior-knowledge-wall (7), representation-science (7), roadmap-from-zero (4) = 97.
  So **11 pending slices sit in loops that report nothing pickable** -- including
  thesis-writer, which CATALOG marks ACTIVE with 11 pending and 1 blocked, and which
  the render engine says has nothing pickable at all.
date of evidence: 2026-07-17 (PLAN.md render) over June inputs -> window: pre-wipe
frame: n/a
population: 19 loops, 333 slices
platform gap: the reason is recorded only as "blocked deps or all done /
  requires_human" -- the renderer collapses three distinct causes into one string, so
  a reader cannot tell a dependency deadlock from a human gate.
note: thesis-writer is the one that matters. The manuscript loop is marked ACTIVE in
  the catalog, has 11 pending slices, has not been touched in 87 days, and its own
  planning engine says there is nothing to pick up.
---

## FINDING 12 (THE RESIDUE): 16 substantive plan documents exist ONLY on unmerged branches, NONE on disk

verdict: CONFIRMED
method: `git ls-tree -r --name-only origin/main -- plans/` (70 files) versus the union
  of `git ls-tree` over every local and remote branch, `comm -13` under `LC_ALL=C`.
  28 paths appear on some branch and not on main; 12 of those are pre-move copies of
  files that now live under `plans/archive/` (lafa-improve, lafa-levers,
  lafa-number-one, reranker-vnext, score-ablation, thesis-cuts, lab-runner).
  The other **16 are documents that have never landed anywhere**:

| document | last commit | on disk? | lives only on |
|---|---|---|---|
| plans/RUN-LEDGER.md | 2026-08-02 | **NO** | plan/run-ledger, pr/239 |
| plans/FIRST-KNN-RECEIPT.md | 2026-07-30 | **NO** | plan/first-knn-receipt, pr/242 |
| plans/FARM-COORD.md | 2026-08-12 | **NO** | plan/rung2-amendment, pr/243 |
| plans/PEER-LOG.md | 2026-08-12 | **NO** | origin/peer/host-report |
| plans/RUNG2-AMENDMENT.md | 2026-08-23 | **NO** | plan/rung2-amendment, pr/243 |
| plans/GRAPH-AUDIT.md | 2026-08-26 | **NO** | origin/plan/graph-audited-against-this-campaign, pr/256 |
| plans/EXPERIMENT-GRAPH.md | 2026-08-26 | **NO** | plan/experiment-graph, pr/257 |
| plans/EXPERIMENT-GRAPH-INSTANCE.md | **2026-08-27** | **NO** | plan/experiment-graph, pr/257 |
| plans/CAMPAIGN-MODEL.md | **2026-08-27** | **NO** | plan/experiment-graph, pr/257 |
| plans/CAMPAIGN-INSTANCE-ZERO.md | **2026-08-27** | **NO** | plan/experiment-graph, pr/257 |
| plans/SURVIVOR-CASCADE.md | **2026-08-27** | **NO** | origin/plan/survivor-cascade, pr/257 |
| plans/archive/rungs.yaml | **2026-08-28** | **NO** | origin/chore/the-ladder-declaration-is-archived |
| plans/contextual-generation/PLAN.md | 2026-07-20 | **NO** | origin/plan/contextual-generation, pr/232 |
| plans/ORCHESTRATION.md | 2026-09-02 | NO(*) | plans/orchestration |
| plans/clean-campaign/DESIGN-STATE.md | 2026-09-02 | **NO** | origin/plans/clean-campaign-design-state |
| plans/structure-retrieval/PLAN.md | 2026-09-02 | **NO** | plans/structure-retrieval |
(*) ORCHESTRATION.md was on disk at the start of this session on branch
    plans/orchestration; HEAD has since moved (see the CORRECTION above).

date of evidence: 2026-07-20 through 2026-09-02. **Five of them are dated 2026-08-26
  to 2026-08-28, i.e. AT or AFTER the registry wipe** -- these are the only plan
  documents in the entire store written in the post-wipe window, and not one of them
  is on main or on disk.
frame: unknown for most; they were written to describe the post-wipe campaign model
  (their names say so: CAMPAIGN-MODEL, CAMPAIGN-INSTANCE-ZERO, EXPERIMENT-GRAPH-INSTANCE,
  SURVIVOR-CASCADE, GRAPH-AUDIT).
population: n/a
platform gap: MURO for the documents; but note what this implies -- the post-wipe
  planning work exists as open PRs (#239, #242, #243, #256, #257) and never merged.
note: **`RUN-LEDGER.md` is the sharpest case.** The user's own memory index
  (`MEMORY.md`, "START HERE: the campaign") lists it as authoritative:
  "**`RUN-LEDGER.md`** what has been computed, at what measured rate, and what the
  next stage waits on. [Why it is hand-built]: PROTEA publishes no operation metrics".
  **It is not on main and not in the working tree.** A reader following the memory
  index to the plan store finds nothing. The memory index and the plan store disagree
  about what exists.
note 2: the branch `origin/chore/the-ladder-declaration-is-archived` moves
  `rungs.yaml` to `plans/archive/rungs.yaml`. **`plans/rungs.yaml` is still live at the
  store root on disk (23,990 bytes, last commit 2026-08-23).** So the ladder's own
  retirement is, like the June roadmaps' retirement, DECLARED ON A BRANCH AND NOT
  EXECUTED. That is the same failure mode as FINDING 5, one month later.
---

## FINDING 13 (THE MOST IMPORTANT ONE): the decision that WIPED the registry is not in the decision log

verdict: CONFIRMED
first number: `plans/DECISION-LOG.md` **on disk** and **on origin/main** both contain
  exactly EIGHT decisions. `grep -n "^## D-"`:
  D-05, D-04, D-03, D-02, D-01, D-06, D-07, D-08 (D-08 = "No rehearsal. The long run
  starts, and the first window is the gate", the 2026-07-28 entry).
  `grep -c "D-09" plans/DECISION-LOG.md` -> **0**.
second number (INDEPENDENT): the branch `plan/decision-wipe-the-campaign-results`,
  commit **28d555c**, `2026-08-26`, "plan(decision): D-09, the campaign's stored
  results are deleted", `git diff --stat origin/main...` -> **1 file changed, 55
  insertions**, all of them `plans/DECISION-LOG.md`. It adds at line 470:
  "## D-09 The campaign's stored results are deleted, because they were measured on
   the holdout / **Decided 2026-08-26 by the author, on a presented inventory of four
   stores.**"
  `git branch -a --contains 28d555c` -> that branch only. **Never merged.**
date of evidence: decision 2026-08-26; the wipe itself 2026-08-27 -> window: this IS
  the boundary event. -> the log that should record it stops 30 days earlier.
frame: D-09 states the frame problem explicitly and quantitatively (see below).
population: quoted from D-09 verbatim:
  - "Four stores go: the candidate table, the evaluation results, the prediction sets
     and the evaluation object store. Roughly **49 GB and 128,191,567 candidate rows**.
     The `job` table stays."
  - "The **225 prediction sets** were built for the release pair 220 to 230, which is
     the **union of the experimental and competitive cohorts**. **594 of the 1,296
     results** sit on that union and **not one sits on either declared cohort**."
  - "Weighted by use, two thirds of every decision-bearing comparison in the campaign
     reads the window reserved as blind: **scoring preset 66.7 per cent, neighbourhood
     depth 65.0, representation 70.8.**"
  - "**The blind reserve was already read.** Neighbourhood depth, preset and
     representation were chosen on a window containing the competitive cohort, and no
     preservation fixes that. ... **no figure from those rows may seed a prior over the
     competitive cohort.**"
platform gap: D-09 names the three findings that were given producers BEFORE the
  deletion, so they survive: "the floor census, **11,664 rows**, one per result and
  panel, each carrying its full conditioning set beside its metric, and reproducible
  **from the file alone**; the coverage hole by panel, with its digest; the frame
  sensitivity, which lives inside the census as a column." It also records the gate:
  "The deletion was gated on reading those three back from disk and checking them
  against their manifest, **rather than on a claim that they had been written.**"
  (That is the project's "verify then act" norm, correctly applied.)
  Cost accepted: "Regenerating predictions costs roughly **150 dispatches**."
note: **This is the single highest-value retirement/merge action in my slice.**
  An auditor, an examiner, or a future agent reading `plans/DECISION-LOG.md` -- the
  canonical decision store, on main -- learns nothing about the wipe. They read D-08
  (2026-07-28, "the long run starts") as the latest state and will treat every
  pre-wipe number in the plan store as live. Every staleness problem in FINDINGS 5-12
  is downstream of this one document not being merged.
note 2: the on-disk `DECISION-LOG.md` has mtime **2026-08-29 12:06** but its last
  commit is **2026-07-28**. It was touched on disk after the wipe and D-09 still is
  not in it. mtime moved, content did not.
---

## FINDING 14: a GREEN CI CHECK on main enforces a campaign design its own author archived

verdict: CONFIRMED
first number: `plans/rungs.yaml` is live at the store root, 23,990 bytes, last commit
  **2026-08-23** (c76588a, "rung 2 closes the retrieval axis"). `git cat-file -e
  origin/main:scripts/check_rung_declaration.py` -> exists. `origin/main:
  .github/workflows/rung-declaration.yml` -> exists. Both present on disk
  (4,624 and 890 bytes) plus `tests/test_rung_declaration.py` (8,877 bytes).
second number (INDEPENDENT): branch `origin/chore/the-ladder-declaration-is-archived`,
  commit **ece04c9, 2026-08-28**, "the ladder declaration is archived, and its green
  check retired with it". `git diff --stat origin/main...` :
    .github/workflows/rung-declaration.yml |  28 ----- (deleted)
    plans/{ => archive}/rungs.yaml         |  18 +++   (moved + banner)
    scripts/check_rung_declaration.py      | 113 ----- (deleted)
    tests/test_rung_declaration.py         | 218 ----- (deleted)
    docs/features/rung-declaration.md      |  27 ++--
  **Unmerged.** `git branch -a --contains ece04c9` -> that branch only.
date of evidence: archive decision 2026-08-28 -> window: **POST-WIPE**, one day after.
  The live artefact it retires is dated 2026-08-23 -> pre-wipe.
frame: the banner the archive commit writes at the top of `plans/archive/rungs.yaml`
  states the succession in its own words, and it is worth quoting entire because it is
  the clearest statement of the current campaign frame anywhere:
  > "# ARCHIVED 2026-08-28. This declares the ladder, and the campaign is a graph.
  >  ... The experiment graph replaces the five rungs with **ten nodes**, each carrying
  >  an edge whose strength is one of **measured, chosen, inherited, unpowered or
  >  blocked**, and a **cardinality that is a vector over nine panels rather than a
  >  scalar.**
  >  Nothing reads this any more. scripts/check_rung_declaration.py and
  >  .github/workflows/rung-declaration.yml went with it, because **a green check that
  >  enforces a retired claim is worse than no check: it reports that the trunk agrees
  >  with a campaign nobody is running.**
  >  What should replace it is a declaration of the graph that a job can be refused
  >  against. **That does not exist yet, and saying so here is the point of keeping the
  >  file.**"
population: nine panels (the vector cardinality), against the ladder's scalars.
platform gap: **named by the document itself**: "a declaration of the graph that a job
  can be refused against ... does not exist yet." That is the operation to build.
note: the same banner records the incident that killed the ladder, and it is a
  measurement defect of exactly the kind this census hunts:
  > "on the night of **2026-08-19** a grid ran **48 arms of the declared rung 1 while
  >  varying two of its three axes, the third pinned by omission to the weakest
  >  available value**, and nothing objected. **Four hundred jobs** were then tagged
  >  with a rung number **invented at dispatch time** and nothing objected to that
  >  either. The failure was not that the design was missing. It was that the design
  >  was prose, and prose cannot refuse a job."
  This corroborates the memory note "Campaign drift, and the gate is wrong: CAMPAIGN.md
  declares 3 axes for rung 1 and we ran 2", and dates it.
  **Right now, on main, the retired check is still required.** Retire it.

## FINDING 15: the three artefacts D-09 gated the deletion on are NOT on this machine

verdict: FRAME-UNKNOWN (not lost -- not verifiable from the compute node)
first number: D-09 (unmerged branch) states three findings were materialised with
  producers before the deletion: "the floor census, **11,664 rows**, one per result and
  panel, each carrying its full conditioning set beside its metric, and reproducible
  from the file alone; the coverage hole by panel, with its digest; the frame
  sensitivity, which lives inside the census as a column."
second number (INDEPENDENT search of this machine):
  - `find storage/ -iname "*census*" -o -iname "*floor*"` -> only
    `storage/coordination/census` (this audit's own directory),
    `storage/encoder-study/scripts/39_real_reranker_floor.py` +
    `storage/encoder-study/artifacts/real_reranker_floor.json` (a different study),
    and conda/perl package noise under `storage/rescue/planb/`.
  - `find storage/ -maxdepth 4 -type f \( -name "*.csv" -o -name "*.jsonl" -o
    -name "*.tsv" \) -size +100k` then line-counting for 11,000-12,500 -> **zero hits.**
  - `grep -rl "11664\|11,664" storage/ agent-farm/` -> 10 files, all unrelated
    (`storage/probe/*.index.json` and perl/conda package data).
  - `ls storage/` top level: calibration-study, coordination, encoder, encoder-study,
    logs, ontology-drift, probe, rescue, scorecard, throughput, worktree_salvage.
    No campaign-census directory.
date of evidence: 2026-08-26/27 -> window: the wipe boundary itself
frame: nine panels; "its full conditioning set beside its metric" and a frame-sensitivity
  column -- i.e. it is exactly the frame-carrying artefact this audit needs.
population: 11,664 rows = one per (result, panel).
platform gap: D-09 says these three had producers, unlike the rows they replaced. If so
  they are reproducible; if the producer is also unmerged, they are not.
note: **I am NOT claiming they are lost.** `CLAUDE.md` and `TOPOLOGY.md` say the laptop
  is the persistent server and owns the object store; this desktop is the compute node
  and "holds no state". The correct reading is that these artefacts were never expected
  here. **But that is exactly the risk**: D-09's entire justification for deleting 49 GB
  and 128 million rows rests on three files whose existence cannot be checked from the
  machine where most of the analysis happens, and whose describing decision is unmerged.
  ACTION FOR WHOEVER HAS THE LAPTOP: read those three back and record the digest here.
---
---

# THE DELIVERABLE: documents that LOOK current and are NOT

Ranked by how badly a reader is misled. "Looks current" = sits at the plan-store root
or a top-level slice dir, carries no superseded banner, has the uniform `Jul 28 17:01`
restore mtime, and asserts its own authority in its first paragraph.

| # | document | content date | self-declared authority (quoted) | why it is not current | retire? |
|---|---|---|---|---|---|
| 1 | **CATALOG.md** | 2026-06-22 | "Single entry point to the plan store" | Declares `beat-lafa-1` "**ACTIVE - canonical**", which E2E-CANONICAL-RUN.md retired 2026-07-27. Headline 0.3745 cites EvalResult `b21b187c`, a row wiped 2026-08-27. Calls ROADMAP-THESIS-10 "**Still the north-star roadmap**". Loop counts still match only because nothing moved. | **RETIRE / REWRITE.** Highest priority: it is the front door. |
| 2 | **CONCEPT-MAP.md** | 2026-06-22 | "living document ... **held and updated at all times** ... Keep it current" | ONE commit ever, 72 days. Carries "0.391 offline / 0.3745 native" as the headline pair. Ships 3 `[stale]` markers that were there at birth. | **RETIRE or re-date.** Its own first line is the lie. |
| 3 | **ROADMAP-THESIS-10.md** | 2026-06-11 | "**Authoritative** sequencing overlay for finishing the doctoral thesis" | Explicitly superseded by E2E-CANONICAL-RUN.md:12 and ordered moved to `plans/archive/`. **The move was never made.** Status snapshot "2026-06-10: 298 slices, 199 done" vs my count today 333/207. | **MOVE TO archive/** (already decided 2026-07-27). |
| 4 | **THESIS-FINISH.md** | 2026-06-16 | "**Authoritative** finishing plan across every front ... Supersedes nothing" | Same supersession, same un-executed move. Written "after the LAFA first-place result (mean f_micro_w 0.391) was achieved" -- the frame E2E calls "old window convention ... a mixed-metric story". | **MOVE TO archive/** (already decided 2026-07-27). |
| 5 | **beat-lafa-1/** (PLAN.md + CAMPAIGN-DOSSIER.md) | 2026-06-22 | "The current campaign to surpass LAFA #1" | Same supersession, same un-executed move. Holds 7 of the 16 dangling DB-row citations. Its own dossier admits "Champion's offline sources are deleted -> 0.391 not byte-reproducible". | **MOVE TO archive/** (already decided 2026-07-27). |
| 6 | **REQUIREMENTS.md** | 2026-06-16 | "**the single source of truth** for the requirements" | Routes every requirement to an owning track in `THESIS-FINISH.md`, a superseded document. NFR-PERF still frames the target as "0.391 is not the ceiling ... PK cell (0.215 vs 0.230)". Its defence -- "Requirements are durable: they do not expire" -- is true of the REQUIREMENTS and false of the NUMBERS inside them. | **KEEP the FR/NFR spine, STRIP the numbers**, re-point owners. |
| 7 | **ROADMAP-NEXT.md** | 2026-06-22 | "the unified execution plan" | Derived from CONCEPT-MAP (stale) and REQUIREMENTS (stale); "sequences the work that `THESIS-FINISH.md` and `beat-lafa-1/` already started" -- both superseded. Its gate D-B waits on "SDR-A produces a validated signal". | **RETIRE.** Superseded transitively by CAMPAIGN.md. |
| 8 | **SDR-PROGRAM.md** | 2026-06-22 | "Design + ready-to-launch plan" | "## 1. Where we are (**2026-06-22**)". Its central result (k-WTA Tanimoto 0.2551 vs cosine 0.3153 on pooled ProtT5) and its diagnosis (pool-then-sparsify is the confound) are BOTH superseded by the settled memory "The frozen recipe cannot express the ORDER" (2026-08-20) and "Residue-level order WINS once the map is trained for it". | **ARCHIVE** -- the conclusion was reached, elsewhere, later. |
| 9 | **PLAN.md** (rendered master, 68 KB) | 2026-07-17 | render.py `--check` CI gate | **NOT stale relative to its inputs** -- I reproduced its 333/207/108/14/3/1 exactly. It is stale relative to REALITY: its 19 loops froze between 2026-05-18 and 2026-06-24, and 13 of 19 report "nothing pickable". | **KEEP** (it is honest), but mark the slice system dormant. |
| 10 | **rungs.yaml** | 2026-08-23 | machine-checkable, CI-enforced | Author archived it 2026-08-28 on an unmerged branch, with the workflow, script and 218 lines of tests. **The green check is still required on main.** | **MERGE the archive branch.** |
| 11 | **COMPOSITION-MODEL.md** | 2026-07-28 | "**This one says what the parts ARE**, which none of the others do" | The one document in my slice that is NOT conceptually stale. Still pre-wipe, so its worked examples cite wiped rows. | **KEEP.** Best document in the slice. |

## WHAT TO RETIRE, as a single ordered action list

1. **MERGE `plan/decision-wipe-the-campaign-results` (D-09) first.** Everything else is
   downstream. Without it the canonical decision log ends at D-08 (2026-07-28) and no
   reader learns the registry was wiped. One file, 55 lines.
2. **MERGE `chore/the-ladder-declaration-is-archived`.** Removes a required CI check
   that enforces a campaign nobody is running -- the author's own words.
3. **Execute the 2026-07-27 supersession that was declared and never done:**
   `git mv plans/ROADMAP-THESIS-10.md plans/THESIS-FINISH.md plans/beat-lafa-1
   plans/archive/`. Ordered by E2E-CANONICAL-RUN.md:15. Zero decisions required.
4. **Rewrite or delete CATALOG.md.** It is the store's front door and every claim on
   it is superseded. If rewritten, it must point at CAMPAIGN.md + the experiment graph,
   not at beat-lafa-1.
5. **Re-date or retire CONCEPT-MAP.md**, and either honour "held and updated at all
   times" or delete the sentence.
6. **Land the 16 branch-only documents** (FINDING 12), or archive them explicitly.
   `RUN-LEDGER.md` first: the user's own memory index treats it as authoritative and it
   is not in the working tree.
7. **Strip the three headline numbers (0.391 / 0.3745 / 0.4063) from every document
   that presents them as live**, or annotate each with its frame and its wipe status.
   Two documents currently call 0.4063 "**immutable**"; the memory store calls it a
   projection.
8. **Annotate the 16 dangling DB-row citations** (FINDING 7) as pre-wipe, or delete them.

## WHAT I SEARCHED (so the negatives count)

- `git log -1 --date=short` on all 74 tracked files under `plans/`; `git ls-tree` on
  `origin/main` (70 files) and on every local+remote branch, differenced under `LC_ALL=C`.
- `git status --porcelain plans/` at session start and again later (the answer changed).
- Full-text grep over `plans/` for: `beat-lafa`, `0.3745`, `0.391`, `0.4063`, `0.40765`,
  `TransFew`, `24 of 24`, `seven of eight`, `knn_226_227`, `D-09`, `rung`.
- The same greps for `24 of 24` / `seven of eight` over
  `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`, all of
  `/home/xaxi/Thesis2/repositories/`, and `/home/xaxi/Thesis2/thesis/` -> zero hits.
- Regex `\b[0-9a-f]{8}\b` over every `.md`/`.yaml`/`.txt` under `plans/` (193 hits),
  narrowed to ORM/table keywords on the same line (16 hits).
- Independent re-implementation of `render.py`'s slice parser over all 19 loop PLAN.md.
- Independent parse of `plans/farm-platform/artefacts/knn_226_227_fmicrow.csv`
  (216 rows) for populations and matched-cohort K comparisons.
- `find`/line-count/grep sweep of `storage/` for the 11,664-row floor census -> absent.

## WHAT I DID NOT DO
- No database connection of any kind. Every "wiped row" statement dates the CITING
  DOCUMENT from git; it does not probe the registry.
- I did not run `plans/render.py` (it has a writer path); I reimplemented its parser.
- I wrote nothing outside `storage/coordination/census/`.

STATUS: COMPLETE.
