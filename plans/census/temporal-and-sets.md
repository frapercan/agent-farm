# Slice: temporal-and-sets

Auditor slice key: `temporal-and-sets`
Started: 2026-09-02

## Scope

- `plans/temporal-eval-alignment/`
- `plans/serve-offline-reconcile/`
- `plans/lafa-integrate/`
- the split registry in the deploy worktree (`split_registry`, `COMPARABLE_WINDOW`,
  `windows_for`, `RELEASES`)

## Questions to establish

1. Which annotation releases are actually loaded.
2. Which window the single `evaluation_set` uses.
3. Whether the competitive window for external comparison is v226 -> v227 rather than
   220 -> 227.
4. Whether the corpus is NOT monotone and contracts about 30 per cent twice.
5. Whether ground truth must be built from ADDITIONS, never a net delta.

## Log

(appended as findings are established)

---

## The temporal-eval-alignment PLAN's "Real DB inventory" is PRE-WIPE and PRE-REINSTALL

verdict: CONFIRMED (as a dating fact)
first number: `plans/temporal-eval-alignment/PLAN.md:26` "## Real DB inventory (resolved 2026-06-26)"
  listing GOA sets 220 `1559d9f7-...`, 226 `5e1a7285-...`, 227 `c905dffa-...`, 230 `2394b9a1-...`,
  plus "transversal train set ids 160..220 all present (5-spaced)".
second number: file mtime is 2026-07-28 17:01 (the reinstall-day mass restore); the resolution
  date it declares is 2026-06-26. Both precede the 2026-08-27 registry wipe AND the
  2026-07-28 OS reinstall.
date of evidence: 2026-06-26 -> window: **pre-reinstall-lost**
frame: n/a (an inventory, not a metric)
population: n/a
platform gap: none needed to re-establish; `refresh_goa_release_dates` + a read of
  `annotation_set` would rebuild it, but NOTHING in this plan store has re-verified the
  inventory after 2026-08-27.
note: **Every UUID in this plan is a claim about a database that has since been wiped.**
  The plan's own Phase 0 ingestion steps (GAF 225, OBO releases/2025-03-16) were PENDING
  at the time of writing, so the gap it names was never closed even in the old DB.
  Anyone citing "220/226/227/230 are loaded" from this file is citing pre-wipe state.

## The 226->227 cut was measured as ~4 months and REJECTED as the validation frame

verdict: CONFIRMED (the plan rejects it; see next entry for whether it is the competitive window)
first number: PLAN.md:57-61 "TEST 227->230 = ~6 months. VALID 220->227 = ~17 months (~3x too
  wide). 226->227 = ~4 months (close but short; only 215 new proteins vs the test's 325)."
second number: derived from the plan's own date table (PLAN.md:52) "220 ~2024-04, 226 ~2025-05,
  227 ~2025-09, 230 ~2026-03". 2025-05 -> 2025-09 = 4 months. 2025-09 -> 2026-03 = 6 months.
  2024-04 -> 2025-09 = 17 months. All three horizons reproduce exactly from the date table.
  So the horizons are ARITHMETIC FROM DECLARED DATES, not an independent measurement.
date of evidence: 2026-06-26 -> window: pre-reinstall-lost
frame: horizons in months; the 215 vs 325 protein counts are the only genuinely measured
  quantities here and their frame (aspect? category? propagated?) is UNSTATED.
population: "215 new proteins" vs "the test's 325" -- population definition NOT given.
  215 and 325 are implausibly small for a whole-window delta, which suggests a narrow cell
  (likely NK, or a query subset), but the file never says.
platform gap: `generate_evaluation_set` produces the delta; the counts would be reborn as
  `evaluation_set` row cardinality. The horizon arithmetic needs `refresh_goa_release_dates`
  to populate `source_published_at` -- which PLAN.md Phase 0 step 1 lists as PENDING.
note: **The plan's preferred validation frame is 225->227, and GAF 225 was NEVER INGESTED.**
  PLAN.md:66-69 makes ingesting it Phase 0 step 2, still pending. So the horizon-matched
  validation cut this whole plan exists to build did not exist when the plan was frozen.

## THE FRAME PROBLEM IS FULLY DOCUMENTED IN ONE FILE: PK-BPO 0.343 vs 0.117

verdict: CONFIRMED -- both numbers are real, both correct, different frames, SAME document
first number: `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:126` section 7,
  "pk-bpo 0.140->0.343" (reranker over raw-KNN champion), frame = internal 227->230 eval,
  cafaeval(prop=fill, norm=cafa, no_orphans, max_terms=500, th_step=0.001), OBO+IA v227
  `lafa_t0_Sep_2025`, population = the platform export's 471,798 eval rows / 10,034 positives,
  **NO `-known` flag**.
second number: `NIGHT-RUN-RESULTS.md:160` section 8 table, "PK-BPO ... 0.117", frame =
  CAFA_forever's own invocation `cafaeval <obo> <preds> <gt> -ia IA.tsv -toi terms_of_interest
  -prop fill -norm cafa -no_orphans` **PLUS `-known groundtruth_PK_known.tsv` for PK**,
  population = LAFA's official query set 7,401 proteins (NK 400 / LK 869 / PK 6,341),
  official LAFA ground truth for release `Sep_2025_Mar_2026`.
  Ratio 0.343 / 0.117 = 2.93x.
date of evidence: 2026-06-26 / 2026-06-27 -> window: **pre-reinstall-lost** (and pre-wipe)
frame: the ONLY difference the document names is `-known` (excluding already-known terms on PK)
  plus the population swap 471,798-row internal eval -> 7,401-protein official LAFA query set.
  The document itself draws the conclusion at :167: "the section-7 internal PK lift was partly
  known-term inflation".
population: PK-BPO. Internal frame population size NOT broken out per cell in section 7.
  LAFA frame: PK = 6,341 proteins (85.7% of the 7,401 query set).
platform gap: `run_cafa_evaluation` covers the internal frame. The `-known` scoring path is
  CAFA_forever's, invoked by hand -- **MURO for the LAFA-comparable number**: there is no
  registered operation that takes `groundtruth_PK_known.tsv` and produces a board-comparable
  cell. The whole of section 8 was produced by an ad-hoc invocation.
note: **Anyone quoting a PK number from this project must state whether `-known` was applied.**
  The two numbers are 2.93x apart on the same predictions, the same window, the same day.
  Note also section 7 CONTRADICTS section 4 of the same file (section 4: "PK REGRESSES,
  pk-bpo 0.446->0.274 (-0.173)"; section 7: "pk-bpo 0.140->0.343"). Section 7 explains this
  as a stale-schema artifact in section 4 -- but note the section-4 PK-BPO BASELINE is 0.446
  and the section-7 PK-BPO baseline is 0.140, a 3.2x difference in the *champion* on
  nominally the same wall. Section 4 is the 225->227 VALIDATION frame, section 7 the
  227->230 TEST frame; the file does not flag that the baselines are not comparable.

## Q3: IS THE COMPETITIVE WINDOW v226->v227 RATHER THAN 220->227? -- YES, in the current code

verdict: CONFIRMED, and it CONTRADICTS the 2026-06 run's own board comparison
first number: `worktrees/protea-deploy/protea/core/split_registry.py:292`
  `COMPARABLE_WINDOW = _VALIDATION_WINDOWS[0]`, where `_VALIDATION_WINDOWS` (line 238-241) is
  `consecutive_windows(RELEASES[RELEASES.index(release(BOARD_MARK)) - 1].identifier, RELEASES[-1].identifier)`
  with `BOARD_MARK = "v227"` (line 134).
second number: EXECUTED the module (read-only import, no DB) on deploy HEAD
  `a5de702707d807252b088219131d95db16551c3b` (2026-09-01 20:19:45 +0000):
    COMPARABLE_WINDOW = **v226->v227**, elapsed_days = **124** (2025-05-03 -> 2025-09-04).
    validation windows (8): v226->v227 (124d), v227->v228 (67), v228->v229 (24),
      v229->v230 (90), v230->v231 (37), v231->v232 (20), v232->v233 (33), v233->v234 (15).
    RELEASES table (9 entries): v226 2025-05-03, v227 2025-09-04, v228 2025-11-10,
      v229 2025-12-04, v230 2026-03-04, v231 2026-04-10, v232 2026-04-30, v233 2026-06-02,
      v234 2026-06-17.
date of evidence: code as of 2026-09-01 -> window: **post-wipe-current**
frame: n/a -- this is the frame definition itself.
population: n/a
platform gap: none; `split_registry` is in the platform and importable.
note: **v220 IS NOT IN THE RELEASE TABLE AT ALL.** `RELEASES[0]` is v226. So the "220->227"
  frame that appears throughout the plan store and in memory
  (`project_learned_weights_must_declare_their_cut_2026_08_20`: "the official frame is
  220->230") is **not expressible in the current registry**: `release("v220")` raises
  `UnknownReleaseError`. Any 220-based window is pre-wipe residue.

## COLLISION: the current registry's board window and the 2026-06 board comparison are DIFFERENT WINDOWS

verdict: CONTRADICTED (the two cannot both be the comparable point)
first number: current code, `COMPARABLE_WINDOW = v226->v227` = 2025-05-03 -> 2025-09-04,
  i.e. the window **ENDING AT** the board's mark. `split_registry.py:232-237` argues this
  explicitly: "The series STARTS at the window ending at the board's mark, not at the mark.
  That window is the one the board scored".
second number: `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:152-154` scored against
  "LAFA's official ground truth for release `Sep_2025_Mar_2026` (= 227->230; NK 400 / LK 869 /
  PK 6341 proteins)". Sep 2025 = v227 (2025-09-04), Mar 2026 = v230 (2026-03-04). That is the
  window **STARTING AT** the board's mark, i.e. `_VALIDATION_WINDOWS[1..3]` collapsed
  (v227->v228->v229->v230), a 181-day span, not the 124-day v226->v227.
date of evidence: registry 2026-09-01 (post-wipe-current) vs run 2026-06-27
  (**pre-reinstall-lost**)
frame: the leaderboard cells in NIGHT-RUN-RESULTS section 8 (NK-MFO 0.602, PK-BPO 0.117,
  "#1 in 5/9 cells", "beats TransFew/FunBind/GOA-nonexp") are ALL on 227->230.
  If COMPARABLE_WINDOW is authoritative, **none of those nine cells is on the comparable
  window**, and the entire external comparison would have to be recomputed on v226->v227.
population: LAFA query set 7,401 proteins for the 227->230 comparison. No comparable
  population is declared anywhere for v226->v227.
platform gap: **MURO.** I searched for any artifact or result on the v226->v227 window:
  `grep -rn 'v226' across plans/, repositories/, storage/coordination/, and the memory store`
  (see the search list at the end of this file). The registry DEFINES v226->v227 as the only
  comparable point and **nothing in this project has computed a metric on it.**
note: This is the single most consequential finding in my slice. The code says the comparable
  window is v226->v227; every published external comparison this project has is on 227->230.
  Both cannot be the headline. Reconciliation: EITHER the board mark moved (the LAFA board
  release advanced from `Sep_2025_Mar_2026` to something ending at v227), OR the registry's
  `BOARD_MARK` is wrong, OR the registry is a NEW design that has not yet been executed and
  the 2026-06 numbers are simply pre-design residue. The third is most likely given the dates,
  and it means **the project's headline external result is on a window its own current
  registry does not designate as comparable.**

## THE ADJUSTMENT MENU IS EMPTY AND NO CHAMPION CAN LEGALLY BE SELECTED

verdict: CONFIRMED by execution
first number: `split_registry.py:334` docstring: "The menu is currently **empty**, and that is
  not a defect in this function, it is the finding".
second number: EXECUTED: `adjustment_candidates()` returns `()` (empty tuple);
  `menu_is_sufficient()` returns `False`; `windows_for("train")` and `windows_for("adjustment")`
  both raise `SplitUndecidedError`. Derivation: the cutoff is
  `release(COMPARABLE_WINDOW.start).published` = v226's 2025-05-03, and the earliest window
  the table can express ends at v227 = 2025-09-04 > cutoff. So zero candidates, by
  construction, because RELEASES[0] IS COMPARABLE_WINDOW.start.
date of evidence: 2026-09-01 -> window: post-wipe-current
frame: n/a
population: n/a
platform gap: closing it needs `load_goa_annotations` for releases before v226 (v220..v225),
  then adding rows to `RELEASES`. `plans/temporal-eval-alignment/PLAN.md` claims v220 and the
  transversal 160..220 sets WERE loaded pre-wipe; none of them survive in the registry.
note: Two of three splits are undecided and one of them (adjustment) is UNSATISFIABLE from the
  current table. **Every hyperparameter, threshold and champion choice the project has made is
  therefore either pre-registry or made on a split the registry refuses to resolve.**
  `assert_may_inform("validation", "champion_choice")` raises `SplitLeakError` -- so selecting
  on the only split that HAS windows is explicitly a leak.

## Q5: GROUND TRUTH MUST BE BUILT FROM ADDITIONS, NEVER A NET DELTA -- the rule is CODED, the number behind it is an ECHO with a broken count

verdict: CONFIRMED as a decided rule and a working implementation;
         **the 63.7% that justifies it is NOT_FOUND as a receipt, and its stated
         population contradicts the release table**
first number: "as much as **63.7%** of apparent additions on all-evidence data had been seen
  before", over "**eleven consecutive releases**". Appears at, verbatim or near-verbatim:
    - `worktrees/protea-deploy/protea/core/first_appearance.py:14`
    - `worktrees/protea-deploy/protea/core/split_registry.py:383`
    - `agent-farm/plans/DECISION-LOG.md:102-103` (D-02, decided 2026-07-28)
    - `agent-farm/plans/CAMPAIGN.md:171-172`
    - and duplicated in `repositories/PROTEA/` + `repositories/agent-farm/` copies of all four.
  Six distinct file locations, ONE number, no breakdown anywhere: no per-release table,
  no namespace split, no count of apparent additions, no count of restored.
second number: **THE RELEASE TABLE CANNOT SUPPLY ELEVEN CONSECUTIVE RELEASES.**
  `split_registry.RELEASES` holds **nine** (v226..v234); `consecutive_windows` over the whole
  table yields **eight** windows. Executed and confirmed above. A probe over eleven
  consecutive releases therefore ran on a corpus history that is **not the one this campaign
  spans** -- most plausibly the pre-wipe v220..v230 series (11 releases if you count
  220,221,...,230 inclusive), which `plans/temporal-eval-alignment/PLAN.md:54-56` says were
  NOT ingested: "GAF releases are sequential (220,221,...,230); PROTEA ingested only
  220/226/227/230 in this range. 221-225 and 228-229 are NOT ingested."
  So the eleven-release probe used **release dumps read outside the platform**, not the
  ingested corpus. DECISION-LOG.md:102 says exactly that: "a probe over eleven consecutive
  release **dumps**".
date of evidence: on/before 2026-07-28 (D-02's decision date) -> window: **pre-wipe**, and
  the dumps it read are almost certainly **pre-reinstall-lost**.
frame: all-evidence vs experimental. The 63.7% is ALL-EVIDENCE. On experimental evidence,
  "the rate falls to about one percent" -- and **experimental is the operating regime**.
  So the headline number is on the population the project does not score.
  Also "as much as 63.7%" is a MAXIMUM over eleven releases, not a rate: the distribution
  behind it is never shown, and the same sentence says the rate is non-uniform and
  "tracks the contraction points".
population: unstated. Not per-namespace, not per-category, not per-release.
platform gap: `restoration_report` / `RestorationReport` in
  `protea/core/first_appearance.py:106-120` is EXACTLY the operation that would rebirth this
  writing to the database -- it carries `apparent_additions`, `genuine_first_appearances`,
  `restored`, `restored_by_namespace`. It exists as a pure function. I found **no registered
  operation that calls it and persists the report**, and no artifact anywhere holding a
  restoration report. See search list at end.
note: The RULE is well-founded independently of the number (an annotation withdrawn and
  restored is genuinely a leak under pairwise difference; `first_appearance` at line 85-103
  implements the union-of-all-prior-cuts correctly and `NotEnoughHistoryError` at line 93
  refuses to silently fall back). What is missing is the MEASUREMENT: the one figure that
  travels is a maximum, on the wrong evidence regime, over a release history the current
  registry cannot express, with no breakdown. By COLLIDING-A-NUMBER rule 2 it cannot be
  collided by anyone, and by rule 5 nobody has looked at its distribution.

## Q4: THE CORPUS CONTRACTS ~30% TWICE -- **DEDUCED-NOT-MEASURED. It is COMPRESSED FILE SIZE, and its own source says so.**

verdict: **DEDUCED-NOT-MEASURED** (the claim is true of `gaf.gz` bytes; it is NOT a
  measurement of annotations, and it is cited downstream as if it were)
first number: `agent-farm/plans/E2E-CANONICAL-RUN.md:92-100`, a table whose column is
  literally headed "**gaf.gz size**":
    v226 2025-05-03 21.10 GB (base) | v227 2025-09-04 14.58 GB **-30.9%** |
    v228 15.77 GB +8.1% | v229 16.50 GB +4.6% | v230 14.38 GB -12.8% |
    v231 14.33 GB -0.3% | v232 10.09 GB **-29.6%** | v233 10.58 GB +4.8% | v234 10.86 GB +2.7%
  Conclusion drawn at :106: "**The corpus contracts by roughly 30% twice**".
second number: recomputed from the table's own GB values:
    (14.58-21.10)/21.10 = **-30.90%**;  (10.09-14.33)/14.33 = **-29.59%**.
  Both reproduce to two decimals, so the ARITHMETIC is sound. What does not follow is the
  word "corpus". The quantity measured is the size of a **gzip-compressed** GAF file.
  Cumulative v226->v234 is **-48.53%**, i.e. the file has lost nearly half its bytes over
  the campaign span, which is a stronger and stranger fact than "two contractions" and is
  nowhere stated.
date of evidence: 2026-07-27/28 (E2E-CANONICAL-RUN.md, mtime 2026-07-28 17:01)
  -> window: **pre-wipe**
frame: file bytes, compressed, of `goa_uniprot_all.gaf.gz`. No evidence-code filter, no
  namespace split, no protein/annotation counts, no experimental subset.
population: the whole upstream GOA dump, i.e. ~95%+ IEA. NOT the scored population.
platform gap: `E2E-CANONICAL-RUN.md:123-131` names the missing operation itself:
  "**Decompose every window into ADDED and REMOVED**, not just net delta." Stage 0 of the
  concise path (:203-207) makes it the FIRST gate: "Decompose every window into ADDED and
  REMOVED. Diagnose the two ~30% contractions. GATE: the ground truth is trustworthy.
  **Nothing measured before this counts.**" I found no artifact of that decomposition.
note: **THE SOURCE DOCUMENT ITSELF DISCLAIMS THE NUMBER.** `E2E-CANONICAL-RUN.md:128-131`,
  point 3: "**Note that size is a proxy. File bytes are not annotation counts.** The
  decomposition in point 1 is the real measurement; **this table is the alarm that makes it
  necessary.**"
  And yet the disclaimer is dropped everywhere the number travels:
    - `worktrees/protea-deploy/protea/core/first_appearance.py:7-9`: "The corpus contracts as
      well as grows. **It has lost roughly thirty percent of its volume twice** in the
      release history this campaign spans." -- stated flatly, no proxy caveat.
    - `worktrees/protea-deploy/protea/core/split_registry.py:270-274`: the ADJUSTMENT split is
      left UNDECIDED partly BECAUSE "that window is **one of the two roughly thirty percent
      corpus contractions**, so selecting champions on it would tune against an anomaly".
    - `split_registry.py:350-352`: `menu_is_sufficient()`'s docstring repeats it as the reason
      the menu must have >= 2 windows.
  So a compressed-file-size delta, explicitly labelled a proxy and an "alarm", is now
  **load-bearing in shipped code**: it is one of the two reasons no adjustment split exists,
  which is why no champion can currently be selected. This is the COLLIDING-A-NUMBER rule 3
  failure in its purest form -- an alarm promoted to a measurement by being restated.
  A gzip size drop is additionally a proxy of a proxy: compressed bytes move with content
  redundancy, so a GOA release that bundles fewer source databases can shrink far more (or
  far less) than its annotation count does.

## THE ROLE OF v226->v227 DRIFTED: it is TUNE in the campaign doc and VALIDATION in the code

verdict: CONTRADICTED (the two authorities assign the window opposite, mutually exclusive roles)
first number: `agent-farm/plans/E2E-CANONICAL-RUN.md:107-108`: "**226 -> 227 is -30.9%**
  (**the TUNE window**)"; and :151-155 rule 2: "**The TUNE window is balanced** across the
  strata ... so that a threshold selected on 226 -> 227 is not merely the threshold of
  whichever stratum happened to dominate a 124-day window".
second number: `worktrees/protea-deploy/protea/core/split_registry.py:292`:
  `COMPARABLE_WINDOW = _VALIDATION_WINDOWS[0]` = **v226->v227**, in the VALIDATION split,
  whose `may_inform = frozenset()` (line 280) and `balanced = False` (line 283).
  Executed: `assert_may_inform("validation", "thresholds")` raises `SplitLeakError`.
  The registry's own comment at :234-237 states the opposite of the campaign doc:
  "It also fixes where the adjustment set has to stop: **strictly earlier**, or the champion
  would be selected on the window it is then validated against."
date of evidence: campaign doc 2026-07-27 (pre-wipe) vs code 2026-09-01 (post-wipe-current)
frame: same window (124 elapsed days, 2025-05-03 -> 2025-09-04), opposite roles.
population: n/a
platform gap: n/a -- this is a documentation/code divergence, not a missing operation.
note: The campaign document says thresholds are SELECTED on v226->v227 and that it must be
  BALANCED; the shipped registry says that window informs NOTHING and must NEVER be balanced
  ("reweighting it makes the number incomparable to anyone else's", :281-282).
  **If any threshold in this project was tuned on 226->227 per the campaign doc, the
  registry's definition of the comparable window is already leaked.** Nobody appears to have
  noticed the two documents disagree; E2E-CANONICAL-RUN.md is still cited as an authority in
  CLAUDE.md and in the memory index.

## Q2 / THE HEADLINE CONTRADICTION: the running rung holds the window at "GOA 220 to GOA 230"; the registry cannot express v220 at all

verdict: **CONTRADICTED** -- two post-wipe authorities, three days apart, name different windows
first number: `agent-farm/plans/rungs.yaml:238-241` (mtime **2026-08-29**, i.e. POST-WIPE),
  rung 1 "the weighted-score benchmark", `status: running`:
      held:
        - what: temporal window
          value: **GOA 220 to GOA 230**
          decided_by: campaign
  and rung 7 (`rungs.yaml:453-456`) holds "bank, queries, scoring, **temporal window** /
  value: identical to rung 1". So every arm of the ladder inherits 220->230.
second number: `worktrees/protea-deploy/protea/core/split_registry.py` at HEAD `a5de702`
  (**2026-09-01**). Executed: `RELEASES` = (v226, v227, v228, v229, v230, v231, v232, v233,
  v234). **There is no v220.** `release("v220")` raises `UnknownReleaseError`.
  `COMPARABLE_WINDOW` = **v226->v227**.
  So the window the running rung declares as HELD is not constructible in the module that
  owns window construction. `ReleaseWindow("v220","v230")` raises in `__post_init__`.
date of evidence: rungs.yaml 2026-08-29 (**post-wipe-current**); split_registry 2026-09-01
  (**post-wipe-current**). BOTH are inside the current window. This is not stale residue.
frame: 220->230 spans (per `plans/temporal-eval-alignment/PLAN.md:52`) ~2024-04 to ~2026-03,
  about **23 months**. v226->v227 spans **124 days**. A factor of ~5.6 in horizon.
population: rung 7's cost note (`rungs.yaml:449-451`, and again at :471) gives the concrete
  population actually in the machine: "**22,498 queries against 528,294 bank sequences**".
  Cross-check: `worktrees/run-ledger/plans/RUN-LEDGER.md:44-52` measures the ingested corpus
  at 616,846 proteins / 575,503 canonical / 557,481 with GO annotations. 528,294 is 91.8% of
  575,503, consistent with a donor bank drawn from the canonical corpus. So the bank is real
  and post-reinstall; the window LABEL on it is the thing that does not resolve.
platform gap: `split_registry` is the operation-side authority and it is not wired to
  `rungs.yaml`. **There is no check that a rung's declared `held: temporal window` resolves
  in the registry.** One import and one `release()` call would have caught this.
note: **This is the "n_proteins is not a population" defect one level up: a WINDOW is declared,
  recorded where a reader will trust it, and does not govern (or even resolve against) the
  module that defines windows.** Memory
  `project_learned_weights_must_declare_their_cut_2026_08_20` independently records "the
  official frame is 220->230", so the 220->230 label has already propagated into the
  durable record. Whichever of the two is right, every number rung 1 has produced carries a
  window label that the current code says does not exist.

## Q1 (FIRST PASS, SUPERSEDED): WHICH ANNOTATION RELEASES ARE LOADED -- "two, unnamed"

> **SUPERSEDED by "Q1 ANSWERED: FOUR annotation releases are loaded post-reinstall" below.**
> Kept because the reasoning below is where the "two releases" figure comes from and a
> reader will meet it in RUN-LEDGER.md. The count was correct for 2026-07-29 and stale
> by 2026-08-19.


verdict: NOT_FOUND (the count is measured; the identities are not recorded)
first number: `worktrees/run-ledger/plans/RUN-LEDGER.md:64-67`: "**Two GOA releases** were
  loaded at 10:36 and 12:37 UTC, **10.65 million annotations** between them, and 557,481 of
  the 575,503 canonical proteins now carry GO terms: 96.9 percent."
  Log line :734: "2026-07-29 12:37 | GO annotations loaded: **two releases**, 10.65 M
  annotations". Ontology side: :52 "ontology snapshots loaded | **10**, spanning 2024-03-28
  to 2026-01-23"; log :722 "2026-07-28 22:02 | ten ontology snapshots loaded".
second number: **the two releases are never identified.** I searched for their identifiers in:
  `worktrees/run-ledger/plans/RUN-LEDGER.md` (whole file, 734 lines, grep for
  v22x/v23x/"annotation set"/"release" -- the ONLY release-number hits in the file are in
  unrelated prose), `agent-farm/plans/*.md`, `agent-farm/plans/rungs.yaml`,
  `agent-farm/plans/DECLARED-REVISION.txt`, `storage/coordination/CHECKLIST.md`.
  The strongest available inference is v226 + v227, because `split_registry.RELEASES[0]` is
  v226 and `BOARD_MARK` is v227, and because two releases are exactly what
  `COMPARABLE_WINDOW` needs. **That is an inference, not a record.**
date of evidence: 2026-07-29 -> window: post-reinstall but **pre-wipe** (the 2026-08-27 wipe
  hit the experiment registry; whether it hit `annotation_set` is not established here and I
  may not query the DB to find out).
frame: "10.65 M annotations" is all-evidence, unfiltered. Compare
  `plans/temporal-eval-alignment/PLAN.md:47-49`, which recorded the PRE-reinstall v227 set at
  **5.88 M** and v230 at **4.77 M** total. 10.65 M for two releases is consistent in order of
  magnitude with two sets of ~5 M each.
population: 557,481 proteins with GO annotations of 575,503 canonical (96.9%).
platform gap: `refresh_goa_release_dates` exists (named in
  `plans/temporal-eval-alignment/PLAN.md:65`) and RUN-LEDGER.md:72 says "**release
  publication dates are not backfilled**" -- still true as of 2026-07-30. So the platform
  cannot currently answer "which releases are loaded, published when" from its own tables.
note: **The `RELEASES` table in `split_registry.py` carries nine hand-written dates
  (v226 2025-05-03 ... v234 2026-06-17) and the database's release dates are not backfilled.
  Those nine dates are therefore uncollided: nothing in the platform can be asked to agree
  with them.** Every `elapsed_days` in the campaign (124, 67, 24, 90, 37, 20, 33, 15) descends
  from that one unverified literal table.

## THE EVALUATION SET: as of 2026-07-30 the platform had produced NONE

verdict: CONFIRMED for 2026-07-30; the single set in the live DB was created later
first number: `worktrees/run-ledger/plans/RUN-LEDGER.md:604-607`, section 4 "Stages C
  through G": "**Not started.** Nothing in the platform has produced a reference cache, a
  co-occurrence structure, a domain-signature scan, an accretion weighting, **an evaluation
  set**, a candidate set, a feature table, a trained model or a score."
second number: the audit brief states the live DB holds 93 `evaluation_result` and 19
  `prediction_set` rows, all created 2026-08-27..2026-08-30. Those postdate RUN-LEDGER's
  last log line (2026-07-30 00:41) by four weeks. So the single evaluation set was built
  between 2026-07-30 and 2026-08-27, in a period the plan store does not narrate:
  RUN-LEDGER.md was never updated past 2026-07-30, and it is the file that exists
  specifically to record what was computed.
date of evidence: 2026-07-30 -> window: pre-wipe; the set itself -> post-wipe-current
frame: unknown for the set itself.
population: 22,498 queries (rungs.yaml:449) is the only post-reinstall query-set size on
  record and is the best candidate for the evaluation set's size.
platform gap: **the ledger that exists to track what has been computed stopped 28 days before
  the only surviving results were computed.** RUN-LEDGER.md:6-11 says it exists "because the
  platform does not answer it" -- and then it stopped answering too.
note: I could not establish which window the single evaluation set uses without querying the
  database, which I may not do. The two candidate labels on record are 220->230
  (rungs.yaml, 2026-08-29) and v226->v227 (split_registry, 2026-09-01). **A single read of
  `evaluation_set.old_annotation_set_id` / `new_annotation_set_id` / `window_role` settles
  it, and it is the highest-value single query in this audit.**

## **THE DECLARATION GAP, AGAIN: the whole temporal design is in code and NOTHING IMPORTS IT**

verdict: CONFIRMED by exhaustive whole-tree search
first number: D-02 (`DECISION-LOG.md:92-95`, decided 2026-07-28): "An annotation counts as
  ground truth for a window if it is present at the end of the window **and was never present
  at any earlier cut**. **The existing pairwise difference is retired.**"
  Implemented in `protea/core/first_appearance.py` (committed `7625999`, 2026-07-28 03:59 UTC,
  PR #747) and the splits in `protea/core/split_registry.py` (`57cecdc`, 2026-07-28 03:50 UTC,
  PR #744).
second number: **whole-tree grep of `worktrees/protea-deploy` at HEAD `a5de702`
  (2026-09-01) for `split_registry` and `first_appearance`, all file types, excluding the two
  modules themselves, returns ONLY `tests/test_split_registry.py` and
  `tests/test_first_appearance.py`.** Zero production importers. Additionally, a grep for the
  public names `restoration_report`, `RestorationReport`, `COMPARABLE_WINDOW`, `windows_for`,
  `assert_may_inform`, `exclusion_basis`, `ground_truth_requires_history` across all of
  `protea/` returns **nothing** outside the defining module.
  AND the live path still computes the retired rule. `protea/core/evaluation.py:342`, inside
  `_classify_protein_deltas`, which BOTH `compute_evaluation_data` (:388) and
  `compute_evaluation_data_reconciled` (:646) call, and which
  `protea/core/operations/generate_evaluation_set.py` is built on:

      delta_ns = new_ns - old_ns          # evaluation.py:342

  A two-endpoint set difference. Exactly the object D-02 retired thirteen months of
  reasoning ago. For NK the code is even blunter: `nk[protein] = new_all` (:337) -- the
  protein's ENTIRE new annotation set, with no history consulted at all.
date of evidence: code at 2026-09-01 -> window: **post-wipe-current**. The decision it
  contradicts is 2026-07-28.
frame: `_load_experimental_annotations_by_ns` restricts to experimental evidence, so the
  live path runs in the ~1% restoration regime rather than the 63.7% all-evidence one --
  which is the mitigating fact, and it is the same mitigating fact D-02 explicitly refused
  to accept ("One percent would be tolerable if it were uniform, and it is not: the leak
  tracks the contraction points, and the validation series crosses one").
population: every evaluation set the platform has ever produced, including the single one
  behind the 93 surviving `evaluation_result` rows.
platform gap: the missing wiring is one call: `generate_evaluation_set` would have to take a
  release HISTORY rather than an `(old, new)` pair, and route through `first_appearance`.
  Its payload (`GenerateEvaluationSetPayload`, generate_evaluation_set.py:26-44) takes exactly
  two annotation-set ids and cannot express a history. `restoration_report` would then be the
  per-release ADDED/REMOVED decomposition E2E-CANONICAL-RUN.md Stage 0 gates the campaign on.
note: **Both rules the project decided in July are tested and inert.** This is the pattern
  memory already records twice -- `feedback_testing_the_declaration_is_not_testing_the_path`
  ("green CI, four angles on the contract, and the path never entered once") and
  `project_declaration_gap_pattern` ("a parameter accepted, recorded, and inert", noted as
  the fourth instance). This is the fifth and sixth: `first_appearance` and the entire
  `split_registry`. `assert_may_inform` exists so the prohibition is "enforced where
  decisions are made rather than stated in a document nobody reads" (split_registry.py:359-361)
  and it guards no decision anywhere.
  PARTIAL CREDIT: `_classify_protein_deltas` DOES compute a `removed` bucket
  (evaluation.py:328-331), with a good comment about collecting removals before the early
  exit so "the largest losses" are not the invisible ones. So the ADDED/REMOVED split exists
  per protein per window. What does not exist is the per-RELEASE decomposition across the
  history, which is what both the first-appearance rule and the contraction diagnosis need.

## FOUR AUTHORITIES NAME FOUR DIFFERENT WINDOW VOCABULARIES, AND `temporal_window` IS FREE TEXT

verdict: CONFIRMED -- there is no single window vocabulary in this project
The four, all read directly:

| authority | file:line | window(s) it names | date |
|---|---|---|---|
| the split registry (code) | `protea/core/split_registry.py:115-134,292` | `v226..v234`, BOARD_MARK `v227`, COMPARABLE_WINDOW **v226->v227** | 2026-07-28 code, HEAD 2026-09-01 |
| the ORM + operation payload | `protea/infrastructure/orm/models/annotation/evaluation_result.py:64-67` and `protea/core/operations/run_cafa_evaluation.py:252-259` | **`"SELECT_220_227"`** (selection) and **`"FINAL_227_230"`** (report-once) | shipped, current |
| the rung ladder | `agent-farm/plans/rungs.yaml:239-241` | **GOA 220 to GOA 230**, `held`, `status: running` | written 2026-08-20 |
| the LAFA integration plan | `agent-farm/plans/lafa-integrate/PLAN.md` "Principles" | fit on **220 to 227**, seal on **227 to 230** | 2026-06-15 |

second number / the collision: `run_cafa_evaluation.py:252-256` declares
  `temporal_window: str | None = Field(default=None, description="... **Free text** so new
  windows need no schema change.")`, and the ORM column is
  `mapped_column(String(32), nullable=True)` (evaluation_result.py:144) with **no server
  default and no CHECK constraint**. I searched `protea/` for any validator, enum or
  cross-check binding this string to `split_registry.RELEASES`: **there is none.** So a row
  can be stamped `SELECT_220_227` while the module that defines windows cannot resolve v220.
date of evidence: all four read on 2026-09-02 from current trees -> window: **post-wipe-current**
frame: n/a
population: every `evaluation_result` row.
platform gap: a two-line validator in `run_cafa_evaluation`'s payload that parses the label
  and calls `split_registry.release()` on both ends would make this class of drift impossible.
  It does not exist.
note: **`temporal_window` is nullable with no default, which memory already records as a
  defect class**: `feedback_null_column_is_not_a_frame_2026_08_23` -- "`temporal_window IS
  NULL` pooled two windows and agreed with the truth on 497 of 513 rows. Select on the fact,
  never the hole." And `seal_evaluation_frames.py:5-9` states the current state plainly:
  "``evaluation_result.frame`` is nullable, has no default, and **nothing in the platform
  writes it**. Every result of this campaign carries null, and so did every result of the one
  before."

## THE WIPE DESTROYED ~1,200 EVALUATION RESULTS, and 396 were already unattributable

verdict: CONFIRMED (a size, from an operation docstring that quotes its own census)
first number: `protea/core/operations/seal_evaluation_frames.py:6-9`: "the census in
  ``audit_evaluation_frames`` found the column empty across the board and **396 rows of
  1,296** whose producing job was gone, which made them **unattributable for ever**."
second number: the audit brief states the live DB now holds **93** `evaluation_result` rows,
  all created 2026-08-27..2026-08-30. 1,296 - 93 = **1,203 rows lost**, i.e. 92.8% of the
  evaluation record. The 396 unattributable rows were a subset of the 1,296 and are gone too.
date of evidence: the 1,296 census predates the seal operation's authorship
  (`seal_evaluation_frames.py` is in the current tree) -> window: **pre-wipe**
frame: `audit_evaluation_frames.py:35-42` counts `n_rows, with_frame, with_window, with_role,
  with_arms, without_job`. The docstring reports `with_frame` = 0 ("empty across the board").
population: all stored evaluation results at census time.
platform gap: none -- `audit_evaluation_frames` IS the operation, and it is registered. It
  should be re-run now: it would answer, in one dispatch, the question this audit cannot
  (what window the 93 surviving rows declare). **That is the single highest-value action
  arising from my slice.**
note: The frame problem's canonical statement is in this same operation's docstring
  (`audit_evaluation_frames.py:5-9`): "the same reranker reads **0.3433** in one row and
  **0.117** in another and both are correct, because the frame differs in ontology, IA source,
  propagation, normalisation, term cap, threshold step, and above all **whether known
  annotations were excluded from the prior-knowledge cell**." I traced the 0.117 to
  `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:160` (PK-BPO, LAFA frame with `-known`).
  I could NOT locate 0.3433 in any surviving document -- the nearest recorded PK-BPO in the
  internal frame is 0.343 at NIGHT-RUN-RESULTS.md:126, which rounds to it. **So the canonical
  example of the frame problem is a pair of numbers from 2026-06-27, i.e.
  pre-reinstall-lost, and only the four-decimal one survives anywhere as 0.343.**

## THE HEADLINE CHAIN, RECONCILED: the "correct frame" pipeline is the WORST point on the board, and that closes exactly

verdict: CONFIRMED, and this one closes to five significant figures by two independent routes
first number: `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:181-182` (2026-06-27):
  "beats our deployed PROTEA-KNN in ALL 9 (mean 0.312 -> **0.359**). Per-category means:
  **NK 0.447, LK 0.429, PK 0.202**." Artifact named at :186:
  `protea-lafa-knn/predictions_7401_reranked.tsv`.
second number: I computed (0.447 + 0.429 + 0.202)/3 = **0.35933**. Independently,
  `memory/project_sealed_headline_is_a_projection_2026_08_24.md` states: "The lab per-aspect
  table's `current` column averages **0.35933**; the board scores
  **`predictions_7401_reranked.tsv`** at **0.35933**." Same file name, same five digits,
  reached from a per-CATEGORY mean here and a per-ASPECT mean there. **The chain closes.**
  The memory then gives the full chain on the identical board:
      predictions_7401_reranked.tsv      0.35933   <- the temporal-eval-aligned reranker
      predictions_percutgraft.tsv        0.38844   <- + InterPro graft
      predictions_protea.tsv (champion)  0.40765   <- the board's measurement of the champion
  and board cells NK 0.6637/0.3374/0.4770, LK 0.5638/0.4402/0.4615, PK 0.2416/0.2181/0.2655.
date of evidence: 2026-06-27 for the 0.35933 arm; 2026-08-24 for the reconciliation
  -> window: the arm is **pre-reinstall-lost**; the reconciliation is **pre-wipe** (3 days
  before 2026-08-27).
frame: LAFA board, v227->v230, `f_micro_w`, `-prop fill -norm cafa -no_orphans -ia IA.tsv
  -toi terms_of_interest`, `-known` on PK. Baselines cross-check EXACTLY between the two
  documents: TransFew LK-BPO **0.512** in NIGHT-RUN:172 and **0.5120** in
  `plans/prior-knowledge-wall/PLAN.md:4`; TransFew PK-BPO **0.294** and **0.2943**. Same board.
population: 7,401 LAFA query proteins (NK 400 / LK 869 / PK 6,341).
platform gap: the graft has a home (`_run_cafa_interpro_graft.py`, named in the memory), so
  the chain is reproducible. What has no home is the board scoring itself -- see the MURO note
  in the frame-problem entry above.
note: **The pipeline built by the temporal-eval-alignment plan -- the one whose whole purpose
  was the CORRECT, horizon-matched, leakage-free frame -- scores 0.35933, the lowest point of
  the three-step chain.** It is 0.032 below the "first place, mean 0.391" that
  `plans/THESIS-FINISH.md:34` records as "Science: DONE" (NK 0.477 / LK 0.482 / PK 0.215;
  I verify (0.477+0.482+0.215)/3 = **0.3913**, so "0.391" is likewise a mean of three
  CATEGORY means, the same aggregation). Cell by cell on the identical board:
      LK-BPO  0.4402 (sealed) vs 0.348 (night run)  = -0.0922
      PK-BPO  0.2181 (sealed) vs 0.117 (night run)  = -0.1011
      NK      0.477  vs 0.447  |  LK 0.482 vs 0.429  |  PK 0.215 vs 0.202
  The night run's own summary says it is "#1 of all methods in **5/9** cells"
  (NIGHT-RUN:180); every other document in the plan store says the project holds **7/9**
  (`bp-structural-lever/PLAN.md:4`, `prior-knowledge-wall/PLAN.md:4-5`,
  `serve-offline-reconcile/PLAN.md:3`, `thesis-pillars/PILLARS.md:99`,
  `thesis-clean-iteration/PLAN.md:44`). **5/9 and 7/9 are two different systems on one
  board, and no document in the plan store says so.** A reader who takes
  NIGHT-RUN-RESULTS.md at face value -- it is the results file of the temporal-eval slice --
  will conclude the horizon-matched frame delivered the headline. It delivered the floor.

## THE CONTRACTION MEASUREMENT IS AN HTTP HEAD REQUEST. Its source says so; every downstream citation dropped it.

verdict: **DEDUCED-NOT-MEASURED, now with the method named**
first number: `memory/project_goa_not_monotone_two_contractions_2026_07_27.md`:
  "**Verified 2026-07-27 by HTTP HEAD on
  `https://ftp.ebi.ac.uk/pub/databases/GO/goa/old/UNIPROT/goa_uniprot_all.gaf.<v>.gz`**"
  followed by the same nine-row GB table and the same -30.9% / -29.6%.
second number: the memory's own point 3, verbatim: "**Size is a PROXY. Bytes are not
  annotation counts; the decomposition is the real measurement. This table is the alarm,
  not the evidence.**"
  So the quantity is a `Content-Length` header on a gzip file. **No GAF was downloaded, no
  line was counted, no annotation was parsed.** The memory is honest about this. The
  degradation happens downstream: `E2E-CANONICAL-RUN.md` keeps the caveat (point 3), and then
  `protea/core/first_appearance.py:7-9` and `protea/core/split_registry.py:270-274,350-352`
  drop it and state the contraction as fact, where it becomes load-bearing.
date of evidence: 2026-07-27 -> window: **pre-wipe**
frame: HTTP `Content-Length` of `goa_uniprot_all.gaf.<v>.gz`, i.e. compressed bytes of the
  WHOLE GOA dump across all species and all evidence codes.
population: not the scored population by any definition. The scored population is
  experimental-evidence annotations on 616,846 ingested proteins.
platform gap: **MURO for the byte table** (an HTTP HEAD against EBI is not an operation and
  should not be one). NOT MURO for the real measurement: `restoration_report` +
  `pairwise_additions` in `first_appearance.py` are the exact primitives; what is missing is a
  `decompose_release_window` operation that walks the ingested history and persists
  ADDED/REMOVED per release per namespace. E2E-CANONICAL-RUN.md Stage 0 gates the whole
  campaign on it: "**GATE: the ground truth is trustworthy. Nothing measured before this
  counts.**" It has not been built.
note: The alarm was correct and worth raising. The defect is the *promotion*: an
  explicitly-labelled proxy became, in shipped code eleven hours later, one of the two
  stated reasons the adjustment split cannot be decided.

## THE AUTHOR'S FRAME AND THE CODE'S FRAME WERE FIXED ELEVEN HOURS APART AND DISAGREE ON v226->v227

verdict: **FRAME-UNKNOWN** -- I cannot establish which is right without the board's own
  release list, but the disagreement is certain and it is undocumented.
first number: `memory/project_goa_not_monotone_two_contractions_2026_07_27.md`, describing
  "the frame the author fixed on 2026-07-27": "**TUNE 226->227, COMPETE 227->forward**".
  Echoed in `plans/E2E-CANONICAL-RUN.md:107` ("226 -> 227 ... the TUNE window", committed
  2026-07-27 20:40:14 +0200).
second number: `protea/core/split_registry.py`, committed **2026-07-28 03:50:01 +0000**
  (PR #744) -- about eleven hours later. It puts v226->v227 in the **VALIDATION** split as
  `COMPARABLE_WINDOW`, `may_inform = frozenset()`, `balanced = False`, and argues the point
  explicitly at :232-237: "The series STARTS at the window ending at the board's mark, not at
  the mark. That window is the one the board scored".
  Under the author's frame COMPETE starts at v227->v228; under the code validation starts at
  v226->v227. **The same 124-day window is the tuning set in one and the untouchable
  comparable point in the other.** E2E-CANONICAL-RUN.md was never updated and is still cited
  as an authority by `CLAUDE.md` and by the memory index.
date of evidence: both 2026-07-27/28 -> window: **pre-wipe**; the code half is still HEAD
  as of 2026-09-01, so the disagreement is live.
frame: the deciding fact is which LAFA board release exists. As of 2026-06-27
  (`NIGHT-RUN-RESULTS.md:152`) the board's release was **`Sep_2025_Mar_2026`**, i.e. the
  window STARTING at v227, which supports the author's frame and contradicts the code's
  `BOARD_MARK`/`COMPARABLE_WINDOW` construction.
population: n/a
platform gap: the board's release list is external and nothing in the platform records it.
  `evaluation_result.frame` was introduced to hold `"lafa"` vs `"internal"` and
  `seal_evaluation_frames.py:5-7` says "**nothing in the platform writes it**".
note: **This is the decisive open question of my slice and it is answerable in one look:
  what release does the LAFA board currently score?** If it is still `Sep_2025_Mar_2026`,
  `BOARD_MARK = "v227"` with the window-ending-at-it construction makes
  `COMPARABLE_WINDOW` name a window nobody is scored on, and the "only point comparable to
  anyone else's number" is comparable to nothing.

## **COMPARABLE_WINDOW IS OFF BY ONE WINDOW. Three independent dates say the board's window STARTS at v227; the code says it ENDS there.**

verdict: **CONTRADICTED** -- and this is the highest-severity finding in my slice
first number: `protea/core/split_registry.py:232-241,292`. `BOARD_MARK = "v227"`;
  `_VALIDATION_WINDOWS` starts at `RELEASES[index(v227) - 1]` = v226;
  `COMPARABLE_WINDOW = _VALIDATION_WINDOWS[0]` = **v226->v227**. The stated justification
  (:232-234): "The series STARTS at the window ending at the board's mark, not at the mark.
  **That window is the one the board scored.**"
second number: three independent records, on three dates, all say the board's window STARTS
  at v227:
  1. 2026-06-27, `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:152-154`: scored against
     "LAFA's official ground truth for release **`Sep_2025_Mar_2026`** (= **227->230**)".
  2. 2026-07-27, `memory/project_goa_not_monotone_two_contractions_2026_07_27.md`: "the frame
     the author fixed on 2026-07-27 (TUNE 226->227, **COMPETE 227->forward**)".
  3. 2026-08-19, `memory/project_temporal_discipline_two_cutoffs_2026_08_19.md`, whose
     opening words are "**Dates, checked rather than assumed**": "release **227 published
     2025-09-04**, release **230 published 2026-03-04**, and the evaluation window is Sep
     2025 to Mar 2026. **So 227 is the window's START and 230 its end.**"
  A fourth, on the artifact: `memory/project_v230_annotation_set_underloaded_2026_07_27.md`
  records that the published nine-cell board file
  `storage/regen_headline/board_nine_cell.json` declares
  `source: CAFA_forever/data/releases/**Sep_2025_Mar_2026**`.
  In the registry's own terms, the board's window is `_VALIDATION_WINDOWS[1]` through `[3]`
  chained (v227->v228->v229->v230), **not** `_VALIDATION_WINDOWS[0]`.
date of evidence: the three records span 2026-06-27 to 2026-08-19; the code is HEAD at
  2026-09-01 -> window: the code is **post-wipe-current**, the records **pre-wipe**.
frame: `f_micro_w`, LAFA harness, `-known` on PK, official CAFA_forever release directory.
population: 7,401 query proteins.
platform gap: the registry has no way to check itself, because nothing in the platform
  records which release the board scores (`evaluation_result.frame` is the field for it and
  `seal_evaluation_frames.py:5-7` says nothing writes it).
note: **The consequence is worse than an off-by-one, because of WHICH window it lands on.**
  v226->v227 is the -30.9% corpus contraction. The registry therefore
  (a) designates as "the only point comparable to anyone else's number" a window on which,
      as far as I can find, no external method has ever been scored, and
  (b) simultaneously uses that same window's contraction as the reason the adjustment set
      cannot be decided (`split_registry.py:270-274`), which is why
      `adjustment_candidates()` is empty and no champion can legally be selected.
  One off-by-one both invents an incomparable headline and deadlocks selection.
  **I am not certain the code is the wrong one** -- a board can advance its release -- but the
  code cites no evidence for its claim and three dated records contradict it. It should be
  treated as wrong until the board's current release directory is read.

## CORRECTION TO MY OWN EARLIER ENTRY: v225 WAS ingested

verdict: CONTRADICTED (my earlier reading of PLAN.md as "never ingested" was wrong)
first number: my entry above, from `plans/temporal-eval-alignment/PLAN.md:66-69`, which lists
  ingesting GAF 225 as Phase 0 step 2, PENDING.
second number: `plans/temporal-eval-alignment/NIGHT-RUN-RESULTS.md:16-18` (2026-06-26) says
  the horizon-matched validation "**225->227 = 5.9 months (GAF 225 = 2025-03-08)**, which had
  to be ingested (**22 GB GAF**, robust local download)", producing validation eval set
  `63d2b433` (delta 14,926: NK 1,277 / LK 2,319 / PK 11,917).
  Independently, `memory/project_v230_annotation_set_underloaded_2026_07_27.md` names the row:
  "v225 (`38280963-c8cd-4a2b-95c9-fa682ecc232d`) has `source_published_at = null` because it
  was ingested from the local file server".
  So v225 existed pre-wipe, with a NULL publication date. **Its horizon (5.9 months) was
  therefore computed from a date the database did not hold** -- the 2025-03-08 came from EBI,
  not from the row.
date of evidence: 2026-06-26 / 2026-07-27 -> window: pre-reinstall-lost
note: the plan and its own results file disagree because the plan was frozen before the run
  and never updated. Read NIGHT-RUN-RESULTS.md, not PLAN.md, for what was actually ingested.

## THE TEST SET OF THE TEMPORAL PLAN WAS BUILT ON A TRUNCATED v230

verdict: CONFIRMED, with three independent indicators, and it invalidates sections 6-7 but
  NOT section 8 of the plan's own results file
first number: `memory/project_v230_annotation_set_underloaded_2026_07_27.md`: the v230
  annotation set `2394b9a1-21df-4c2b-89af-3da084318fab` is INCOMPLETE.
  Indicator 1: EBI `Content-Length` `goa_uniprot_all.gaf.227.gz` = **15,659,156,164 B** and
  `.230.gz` = **15,440,466,318 B**, i.e. **-1.40% upstream**, against loaded
  `annotation_count` **5,875,943 -> 4,767,114 = -18.87%**.
second number: I recomputed both from the raw byte counts and the raw annotation counts:
  (15,440,466,318 - 15,659,156,164)/15,659,156,164 = **-1.3966%**;
  (4,767,114 - 5,875,943)/5,875,943 = **-18.8709%**; discrepancy **17.47 points**, matching
  the memory's "17.5-point discrepancy" exactly.
  Indicator 2: over the complete 15-transition chain v160 (2016-11-01) to v230, the
  227->230 leg yields **1,281 delta proteins per month, the lowest of the whole series**
  (previous minimum 1,695 at 185->190; recent norm ~2,000-2,400).
  Indicator 3: its NK cell holds **501 proteins, the smallest in the series** (next
  smallest 638).
  Three indicators of three different kinds (upstream comparison, longitudinal rate,
  cell size). This is what a properly collided number looks like, and it is the best
  measurement work I found in my slice.
date of evidence: 2026-07-27 -> window: **pre-wipe** (and the set itself is pre-reinstall)
frame: `annotation_count` is all-evidence; the delta-per-month and NK-cell indicators are
  on the experimental/evaluation frame.
population: the whole v227->v230 evaluation set `6e41eb5b-df02-4400-95c5-9cef6c9029ed`.
platform gap: the memory names the fix as a registered operation --
  `POST /jobs {operation: load_goa_annotations}` then regenerate `6e41eb5b` -- so this one is
  NOT MURO. But the SANITY CHECK that caught it (loaded count vs upstream Content-Length) is
  not an operation and should be: it is the cheapest possible guard on an ingestion and it
  caught a 17-point defect.
note: **Scope of the contamination, and it is precisely bounded.**
  `NIGHT-RUN-RESULTS.md` sections 6 and 7 -- the "TEST 227->230 champion (THE LAFA NUMBER)"
  at pooled 0.276 / per-cell 0.365, and the reranker's headline **+0.183 pooled lift** that
  "REVERSES the C1/C2 PK-wall conclusion" -- are computed on eval pair `v227-v230` from OUR
  database, i.e. on the truncated set. Section 8, the board comparison, uses LAFA's external
  ground truth (`CAFA_forever/data/releases/Sep_2025_Mar_2026`) and is NOT contaminated by
  this. **The 2026-06-27 result that overturned a documented PK-wall finding was measured
  against a ground truth missing ~18% of its annotations, and the defect was found a month
  later by a different reader.** Seventeen defects, zero found by the producer; this is one
  more of the same shape.

## DECISIVE: `band_registry.py` and `split_registry.py` sit in the SAME DIRECTORY and disagree on the board's window

verdict: **CONTRADICTED**, inside one package, and only one of the two is wired
first number: `protea/core/split_registry.py:292` -- `COMPARABLE_WINDOW` = **v226->v227**,
  described (:288-291) as "The window other methods are scored on, and therefore the only
  point in the validation series that is comparable to anyone else's number."
second number: `protea/core/band_registry.py:131-144`, the adjacent module:
      "v227": Band(... t0_cutoff=date(2025, 9, 4),
          description="**Deployed LAFA window (GOA v227 to v230**, t0 2025-09-04). Congruent
          GO ontology = releases/2025-07-22 (the data-version in **LAFA's own
          lafa_t0_Sep_2025/go-basic.obo**). Canonical IA = lafa_t0_Sep_2025/IA.tsv (39906
          terms, **the on-record LAFA table**) ...")
  and, for the other band (:120-130):
      "v226": Band(... description="Historical benchmark cut (GOA v226, t0 2025-05-03) ...
          **Superseded by v227 for LAFA-comparable numbers; kept for history.**")
  So `band_registry` says the LAFA window is **v227->v230** and that **v226 is explicitly NOT
  the LAFA-comparable band**. `split_registry` says v226->v227 is the only comparable point.
  Two files in `protea/core/`, opposite answers.
  **This is my fifth and strongest independent record** that the board's window starts at
  v227 (with NIGHT-RUN-RESULTS 2026-06-27, the author's frame 2026-07-27, the
  dates-checked memory 2026-08-19, and `board_nine_cell.json`'s declared source).
date of evidence: both modules at HEAD `a5de702` 2026-09-01 -> window: **post-wipe-current**
frame: `band_registry` pins the frame concretely: v227 band = OBO `releases/2025-07-22`,
  IA `lafa_t0_Sep_2025/IA.tsv` (39,906 terms), and REJECTS the generic `IA_cafa6.tsv`.
  The v226 band = OBO `releases/2025-03-16`, IA `IA_cafa6.tsv`. **These are different IA
  tables, so a metric on v226->v227 is not on the same scale as one on v227->v230 even
  before the population changes.** `plans/temporal-eval-alignment/PLAN.md:112-115` flagged
  exactly this as open decision 1 and it was never closed.
population: n/a
platform gap: **`band_registry` IS wired and `split_registry` is not.** Exactly one
  production module imports `band_registry` -- `protea/core/operations/run_cafa_evaluation.py`
  (:13-14, calling `assert_band_consistency` at :692) -- and zero production modules import
  `split_registry`. So the authority that is enforced at scoring time says v227->v230, and
  the authority that is only tested says v226->v227.
note: **The tie-breaker is decided by which module runs.** Every evaluation this platform has
  scored went through `run_cafa_evaluation` and therefore through `band_registry`'s v227
  band = the LAFA v227->v230 window. `split_registry`'s v226->v227 has never governed a
  single number. Whoever reconciles these should start from the assumption that
  `split_registry.BOARD_MARK`/`COMPARABLE_WINDOW` is the newer, untested, off-by-one
  construction, and that `band_registry` carries the frame the results actually live in.
  Additional context from `band_registry.py:113-118`: "PROTEA had only ingested
  releases/2024-03-28 and releases/2026-01-23, so the **pre-registry v226/v227/v230
  eval_sets all shared releases/2026-01-23 (a ~6-months-too-late ontology); that
  snapshot-sharing IS the phantom-gap bug**." So before this registry, every eval set in the
  project was propagated under an ontology from the future of its own window.

## THE ONTOLOGY DRIFT RECEIPT IS ON 220->227, NOT 226->227

verdict: CONFIRMED (an artifact, dated inside the current window)
first number: `storage/ontology-drift/edge_drift.json`, written **2026-08-27 01:43** (the
  wipe day), compares `go-basic-2024-03-28.obo` -> `go-basic-2025-07-22.obo`:
    terms  old 42,309  new 39,903  added 350  removed 2,756
    edges  old 74,117  new 68,310  added 2,740  removed 8,547  net **-5,807**
    closure_grew 3,429   closure_shrank 11,670   common 39,553
    by aspect: BPO common 25,607 grew 2,564 shrank 10,488; MFO 9,950/624/997;
               CCO 3,996/241/185
second number: I recomputed the fraction the memory index quotes: 3,429 / 39,553 =
  **0.0867** = the "8.67% of terms still grow their closure" in
  `project_ontology_shrinks_but_growth_is_what_bites_2026_08_27`. Exact.
  **And the OBO pair identifies the window.** Per `band_registry.py:120-144`,
  `releases/2025-07-22` is the v227 band's OBO; `2024-03-28` is not v226's
  (v226's is `releases/2025-03-16`). So this receipt spans the **220 -> 227** ontology pair,
  which is the frame `rungs.yaml` and `lafa-integrate` name and which `split_registry`
  cannot express.
date of evidence: 2026-08-27 -> window: **post-wipe-current** (same day as the wipe)
frame: ontology only, unweighted by annotation counts -- `retired_exposure.json` says so in
  its own `note` field, which is good practice.
population: the GO DAG, 39,553 terms common to both snapshots.
platform gap: this ran as `measure_edge_drift.py` / `measure_retired_exposure.py` in
  `storage/ontology-drift/`, i.e. **outside the platform, in the tree the campaign invariant
  says is not carried between machines**. It is a two-file script pair with no registered
  operation. MURO-adjacent: `load_ontology_snapshot` exists and the DAG is in the database,
  so a `compare_ontology_snapshots` operation is a small piece of work.
note: `retired_exposure.json` contains a rare and valuable self-correction:
  `"alt_id_check_was_the_wrong_field": true`, with the note "The redirect field for an
  obsoleted term is replaced_by (automatic) or consider (advisory); **alt_id is the merge
  mechanism and answers a different question**". Of 2,756 obsoleted terms, 737 have a
  replaced_by with a live target, 151 are consider-only, and **1,868 have no target at all**.
  That is the honest distribution behind "2,756 terms retired".

## **CORRECTION TO MY OWN NEGATIVE CHECK: v226->v227 HAS BEEN COMPUTED. My earlier "MURO / nothing computed on it" was WRONG.**

verdict: my earlier entry is **CONTRADICTED by artifacts on disk**. Recording it rather than
  editing it out, because a wrong negative check is exactly what COLLIDING-A-NUMBER rule 4
  is about and my first search was too narrow (I had searched `plans/`, `repositories/`,
  `storage/coordination/` and the memory store, and NOT `storage/encoder-study/`).
first number (populations): `storage/encoder-study/artifacts/delta_windows.json`, written
  **2026-08-19 17:51**, produced by `storage/encoder-study/scripts/59_count_delta_windows.py`,
  with the run log preserved at `artifacts/delta_windows.log`:

  | window | NK | LK | PK | NK+LK | how |
  |---|---:|---:|---:|---:|---|
  | v227 -> v230 | 649 | 971 | 7,518 | **1,620** | reconciled, pivot on the NEW |
  | v226 -> v227 | 523 | 622 | 5,672 | **1,145** | reconciled, pivot on the NEW |
  | v220 -> v226 | 1,911 | 2,078 | 10,593 | **3,989** | same snapshot |

  I verify the script's own summary: 1,145 + 3,989 = **5,134** "delta material available
  BEFORE the cut", against 1,620 from the evaluation window. Exact.
second number (metrics): `storage/encoder-study/artifacts/101_weighting.json` (2026-08-23)
  holds per-arm spreads keyed `"rung 1 backbones, **226-227**|<scoring_config>|K{3,5,10,30}"`,
  n = 8 arms each, columns `spread_unweighted / spread_own / spread_fixed / rho /
  winner_moves`. So metrics on the 226-227 evaluation set exist and were analysed.
date of evidence: 2026-08-19 and 2026-08-23 -> window: **pre-wipe** (4 and 8 days before
  2026-08-27). Whether the underlying `evaluation_result` rows survive is unknown to me.
frame: **THE PIVOT IS THE WRONG WAY ROUND, AND THE SCRIPT SAYS SO IN ITS OWN COMMENT.**
  `59_count_delta_windows.py:43-46`: "Instantáneas distintas: el conjunto viejo se carga
  VACÍO con la función simple y entonces toda proteína parece sin conocimiento previo.
  **El pivote es la instantánea de la nueva, que es el universo contra el que se puntúa.**"
  (the pivot is the NEW snapshot, the universe scored against). Compare
  `plans/temporal-eval-alignment/PLAN.md:82`, which specifies the opposite:
  `pivot_ontology_snapshot_id: OBO_225   # scoring universe = t0 (band guard)`.
  Scoring against the t1 ontology is the **phantom gap** the whole cross-OBO machinery was
  built to close (`generate_evaluation_set.py:30-38` describes it: "t0 propagated under a
  churned graph that marks pre-window experimental annotations as new knowledge").
  Memory `project_pivot_default_routes_away_from_reconciled_2026_08_27` records this exact
  failure mode: "The pivot defaults to new_native, so the obvious fix picks the wrong path."
  **So the three population counts above are on the pivot the plan calls wrong**, and the
  220->226 row used `compute_evaluation_data` (not reconciled) only because 220 and 226
  share an ontology snapshot -- which is itself `band_registry.py:113-116`'s phantom-gap bug
  ("the pre-registry v226/v227/v230 eval_sets all shared releases/2026-01-23").
population: as tabulated. Note the NINE-CELL split is not in this artifact; NK/LK/PK are
  protein counts pooled over aspects, and `project_nine_cells_are_nine_populations_2026_08_23`
  warns that an aspect scores only the proteins that gained THAT aspect.
platform gap: `compute_evaluation_data` / `compute_evaluation_data_reconciled` are platform
  functions and the script calls them directly and honestly (`59_count_delta_windows.py:9-14`
  explains why it refuses to reimplement the criterion -- **good practice, and rare**). What
  is missing is that the script runs OUTSIDE the platform, against `PROTEA_DB_URL`, writing
  to `storage/`, so no `evaluation_set` row records these three windows.
note: **This is the single best-documented artifact I found in my slice**: a script that
  states its reasoning, refuses to reimplement the criterion, prints a log next to its JSON,
  and counts a known window first so the figure can be checked. Its one defect is the pivot,
  and the pivot is stated plainly in the comment, so it is checkable. That is what
  COLLIDING-A-NUMBER rule 2 asks for.

## Q1 ANSWERED: FOUR annotation releases are loaded post-reinstall -- 220, 226, 227, 230 -- and the UUIDs are all NEW

verdict: CONFIRMED, from hard-coded ids in four independent scripts plus a fourth via a
  `source_version` lookup
first number: `storage/encoder-study/scripts/112_panel_populations.py:21-23` (and identically
  in `113_panel_by_length.py:22-24`, `115_panel_populations_experimental_baseline.py:30-32`,
  and `104_dead_donor_split.py:31`):
      REL = {"220": "cbb35a32-44e4-4e39-b524-05b4b7433727",
             "227": "ec9f5c2c-cc1c-4e22-8cda-d1fe53ca86b3",
             "230": "9a14f9cc-a18f-47ed-8511-b0cd2ff29953"}
second number: **v226 is loaded too**, established a different way:
  `59_count_delta_windows.py:33-35` resolves sets by
  `SELECT id, source_version, ontology_snapshot_id FROM annotation_set` and then indexes
  `sets["226"]`; the run log shows the v220->v226 and v226->v227 rows completed in 19 s and
  31 s. A missing key would have raised `KeyError`. So four releases: **220, 226, 227, 230**.
  AND **every UUID is different from the pre-reinstall ones**. Pre-reinstall
  (`plans/temporal-eval-alignment/PLAN.md:28-32`): 220 `1559d9f7-...`, 226 `5e1a7285-...`,
  227 `c905dffa-...`, 230 `2394b9a1-...`. Post-reinstall: 220 `cbb35a32-...`,
  227 `ec9f5c2c-...`, 230 `9a14f9cc-...`. **Zero overlap.** Every UUID in every plan document
  in `plans/` is dead.
date of evidence: 2026-08-19 to 2026-08-26 -> window: **pre-wipe**, post-reinstall.
frame: n/a
population: n/a
platform gap: `refresh_goa_release_dates` still not run as of RUN-LEDGER's last entry, so
  `source_published_at` is presumed null and every date in `split_registry.RELEASES` remains
  uncollidable against the database.
note: **The loaded set is 220/226/227/230 and `split_registry.RELEASES` is v226..v234.**
  The overlap is exactly {226, 227, 230}. The registry enumerates FIVE releases that are not
  loaded (v228, v229, v231, v232, v233, v234 -- six, in fact) and omits the one that IS loaded
  and that the running rung and the LAFA plan both depend on (v220). So the registry's
  validation series of eight windows can be computed for **at most one** of them
  (v229->v230 needs v229: not loaded; v227->v228 needs v228: not loaded). Only v226->v227 and
  the chained v227..v230 are constructible from what exists, and the registry's own
  `_VALIDATION_WINDOWS[1..7]` are all unscoreable today.

## TWO EVALUATION SETS ARE NAMED, AND RUNG 1's IS 226-227 -- NOT the 220->230 rungs.yaml declares

verdict: **CONTRADICTED** -- rungs.yaml's `held: temporal window` does not match the
  evaluation set the rung's own analysis script reads
first number: `agent-farm/plans/rungs.yaml:239-241`, rung 1, `status: running`:
  `held: - what: temporal window / value: GOA 220 to GOA 230`.
second number: `storage/encoder-study/scripts/101_weighting_changes_nothing.py:32-35`:
      GRIDS={
       "rung 1 backbones, **226-227**": ("8763acda-c3b3-49f8-a5e1-b0955206ee3a", None),
       "rung 2 encodings, **220-230**": ("956ab4b3-56b1-47eb-adc5-8879bc25d98d", ...),
      }
  The script queries `evaluation_result ... WHERE er.evaluation_set_id = :es`. So rung 1's
  results live on evaluation set `8763acda-...`, labelled **226-227**, and rung 2's on
  `956ab4b3-...`, labelled **220-230**. rungs.yaml assigns 220->230 to rung 1 and rung 7
  inherits "identical to rung 1".
date of evidence: script 2026-08-23, rungs.yaml line written 2026-08-20 (blame
  `8b7c9bc5`, "make the ladder a claim something can refuse") -> both **pre-wipe**, three
  days apart.
frame: the two evaluation sets sit in different bands. Per `band_registry.BANDS`, a
  226-ending window is the v226 band (OBO `releases/2025-03-16`, IA `IA_cafa6.tsv`) and a
  227-based one is the v227 band (OBO `releases/2025-07-22`, IA `lafa_t0_Sep_2025/IA.tsv`).
  **Different IA tables, so rung 1's and rung 2's f_micro_w are not on one scale**, and
  `plans/temporal-eval-alignment/PLAN.md:112-115` raised exactly this as open decision 1
  ("IA discontinuity ... Absolute f_micro_w differs across bands") and it was never closed.
population: rung 1's set, if it is the 226->227 delta, is NK 523 / LK 622 / PK 5,672
  (delta_windows.json). `101_weighting_changes_nothing.py`'s docstring independently says the
  nine cells "span **1,003 to 6,901** scored proteins, a factor of 5.6" -- a different and
  larger range, so the scored population is not the delta population and the two must not be
  conflated.
platform gap: **nothing binds a rung's declared `held: temporal window` to the
  `evaluation_set_id` its results were computed on.** One field on the rung and one lookup
  would close it. This is the fourth instance in this slice of a declaration that does not
  govern.
note: If the script's label is right, then rung 1 -- the RUNNING rung, the one whose winner
  every later rung holds fixed -- was measured on **v226->v227, the -30.9% contraction
  window**, which is precisely the window `split_registry.py:270-274` says must never be used
  for selection. If the label is wrong, then rungs.yaml is right and the script mislabelled
  the grid it published from. **Either way one of the two documents that a reader would trust
  is wrong about the frame of the project's currently-running experiment.**

## **Q2 ANSWERED FROM THE WORKER LOG: the surviving evaluation set is a v220-based window. It is NOT v226->v227 and NOT v227->v230.**

verdict: **CONFIRMED by elimination, without touching the database**
evidence: `storage/logs/protea-lab-worker-protea.evaluations.log` (7.6 MB, 25,735 lines,
  worker started 2026-08-16, last entry 2026-08-29 03:54). Restricting to timestamps
  2026-08-27..2026-08-31, i.e. exactly the window in which the 93 surviving
  `evaluation_result` rows were created:

  **108 `cafa_eval` invocations, all with an IDENTICAL frame:**
      norm=cafa  prop=fill  th_step=**0.01**  n_cpu=1  weighted_only=False  n_tau=99
  **Ontology, all 108 runs identical:**
      biological_process 25,698 | molecular_function 10,154 | cellular_component 4,051
      -> total **39,903**
  **Three ground-truth populations, 36 runs each (108 = 36 x 3 cells):**

  | cell | BPO | MFO | CCO | exclude |
  |---|---:|---:|---:|---|
  | (A) | 1,214 | 943 | 821 | no |
  | (B) | 1,509 | 1,129 | 1,116 | no |
  | (C) | 5,810 | 3,292 | 3,201 | **yes** |

  (prediction-side counts agree to within one protein: 1,214 / 1,508 / 5,809 in BPO.)
  `compute_metrics` ran 432x in `nk_lk` mode and 216x in `pk` mode.

second number -- THE ELIMINATION: `storage/encoder-study/artifacts/delta_windows.json`
  gives pooled per-window protein counts, and a per-ASPECT count can never exceed the
  pooled one:
      226->227:  NK 523   LK 622   PK 5,672   -> cannot host (A) 1,214, (B) 1,509, or (C) 5,810
      227->230:  NK 649   LK 971   PK 7,518   -> cannot host (A) 1,214 or (B) 1,509
      220->226:  NK 1,911 LK 2,078 PK 10,593  -> hosts all three comfortably
  **Only a window whose t0 is v220 can supply 1,214 NK and 1,509 LK proteins in BPO alone.**
  So the surviving evaluation set is 220-based (220->226, 220->227 or 220->230).
  This CONFIRMS `rungs.yaml:239-241` ("held: temporal window / GOA 220 to GOA 230") and
  the ORM's `"SELECT_220_227"` vocabulary, and CONTRADICTS
  `split_registry.COMPARABLE_WINDOW = v226->v227` as a description of anything that has
  actually been scored in the current window.
date of evidence: 2026-08-27 to 2026-08-29 -> window: **post-wipe-current**. This is the
  only post-wipe frame evidence in my slice and it is first-hand, not an echo.
frame, stated in full because that is the point of this file:
  - ontology **39,903 terms = `go-basic-2025-07-22.obo`**, identified by exact term count
    against `storage/ontology-drift/edge_drift.json` (`"new": 39903`). That is the **v227
    band's** congruent OBO per `band_registry.py:131-135`. **For a 220-based window this
    ontology is 16 months in the future of t0**, i.e. the phantom-gap configuration, unless
    the pivot is deliberately v227.
  - `prop=fill`, `norm=cafa`, `weighted_only=False`, both weighted and unweighted computed.
  - **`th_step=0.01`, n_tau=99.** The 2026-06 champion runs used `th_step=0.001`
    (`NIGHT-RUN-RESULTS.md:136`). **The current threshold grid is 10x coarser than the one
    the headline numbers were computed on**, so a post-wipe number is not directly
    comparable to a pre-wipe one even at identical everything else.
  - **exclusion applied to PK only** (`exclude=yes` on cell C, `exclude=no` on A and B).
    This is D-03 / `exclusion_basis()` behaving correctly IN THE SCORING PATH, even though
    the `exclusion_basis` function itself is never imported. Good news, and worth saying:
    the rule holds; only its declaration is inert.
  - "proteins with no annotations in TOI: 8 / 10 / 11 / 12" per run -- a small orphan count
    is reported per cell.
population: 8,533 proteins at most in BPO (1,214 + 1,509 + 5,810), of which **68.1% are PK**.
  Per `project_serving_population_is_the_nk_cell`, the SERVED population is the NK cell:
  1,214 of 8,533 = **14.2%** in BPO, 943/5,364 = 17.6% in MFO, 821/5,138 = 16.0% in CCO.
  So an aggregate over this evaluation set is 82-86% non-served population.
platform gap: none needed -- `audit_evaluation_frames` would report this from the database
  directly and is a registered operation. **It has not been run since the wipe.**
note: I reached this without a database connection, from a worker log and a JSON artifact.
  A single `audit_evaluation_frames` dispatch would confirm or refute it in seconds and
  should be the first thing done. **The specific prediction to test: the 93 surviving
  `evaluation_result` rows point at ONE `evaluation_set` whose `old_annotation_set_id`
  resolves to source_version 220.**

---

# NEGATIVE CHECKS: what I searched, and where the thing would have been

Per COLLIDING-A-NUMBER rule 4, a zero counts only with its reach.

**1. A per-release ADDED/REMOVED decomposition, or any restoration report.** NOT FOUND.
Searched: `grep -rln "restoration|genuine_first_appearance|apparent_additions"` over
`storage/`, `agent-farm/`, `repositories/protea-reranker-lab/`, `worktrees/` -- the only hits
are third-party sources inside `storage/rescue/planb/env/` (a rescued conda/erlang/perl tree),
none in project data. Also `find storage -iname '*removed*' -o -iname '*added*' -o
-iname '*decompos*' -o -iname '*window*'`: the only relevant hits are
`encoder-study/artifacts/delta_windows.json` (three windows' NK/LK/PK counts, no
added/removed split) and `decompose_gap.json` (a neighbour-weights decomposition, unrelated).
Where it WOULD be: `storage/` next to `delta_windows.json`, or as an `evaluation_set`
artifact, or in `agent-farm/plans/`. **The Stage-0 gate of E2E-CANONICAL-RUN.md ("Nothing
measured before this counts") has never been passed.**
PARTIAL CREDIT: `removed` IS one of the six persisted buckets --
`evaluation.py:60`, `_GROUNDTRUTH_BUCKETS = ("nk","lk","pk","known","pk_known","removed")` --
so per-eval-set removals ARE written to the ground-truth parquet. The per-RELEASE series
across the history is what is missing, not the primitive.

**2. Any metric computed on v226->v227.** FOUND, after an initially wrong negative.
First search (`plans/`, `repositories/`, `storage/coordination/`, memory store) returned
nothing and I wrote "MURO". Second search including `storage/encoder-study/` found
`artifacts/101_weighting.json` (spreads keyed "rung 1 backbones, 226-227") and
`artifacts/delta_windows.json` (populations). **My first negative check was wrong because
its reach did not include the tree where a lab study writes.** Recorded above rather than
silently corrected.

**3. The v226-congruent OBO `releases/2025-03-16`.** FOUND on disk at
`storage/encoder/go-basic-2025-03-16.obo`. `plans/temporal-eval-alignment/PLAN.md:36` says
it was "NOT INGESTED -> GAP" pre-reinstall; the file exists now but I have no evidence it is
an `ontology_snapshot` row. The post-wipe evaluations do NOT use it (39,903 terms identifies
`2025-07-22`).

**4. A consumer of `split_registry` or `first_appearance` in production.** NONE.
`grep -rn "split_registry|first_appearance" .` over the WHOLE `worktrees/protea-deploy` tree,
all file types, returns only the two modules and their two test files. Where it would be:
`protea/core/operations/generate_evaluation_set.py` (window construction) and
`protea/core/evaluation.py` (ground truth). Both use the retired pairwise rule instead.

**5. Anything binding `evaluation_result.temporal_window` to `split_registry.RELEASES`.**
NONE. `grep -rn "temporal_window"` over `protea/` returns 20 hits, all read/write plumbing
(`benchmark.py`, `seal_evaluation_frames.py`, `run_cafa_evaluation.py`, the ORM). No
validator, no enum, no `release()` call. It is `String(32)`, nullable, no default, free text.

---

# ANSWERS TO THE FIVE QUESTIONS

**Q1. Which annotation releases are actually loaded?**
**Four: 220, 226, 227, 230**, with UUIDs 220 `cbb35a32-44e4-4e39-b524-05b4b7433727`,
227 `ec9f5c2c-cc1c-4e22-8cda-d1fe53ca86b3`, 230 `9a14f9cc-a18f-47ed-8511-b0cd2ff29953`
(226 established via a `source_version` lookup that succeeded). **Every one of these UUIDs
differs from every UUID in the plan store**, which still carries the pre-reinstall set.
Evidence is pre-wipe (2026-08-19..26); the wipe hit the experiment registry and I have no
evidence either way about `annotation_set`. `split_registry.RELEASES` enumerates v226..v234,
so it lists six releases that are not loaded and omits v220, which is.

**Q2. Which window does the single evaluation set use?**
**A v220-based window** (220->226, 220->227 or 220->230). Established by elimination from
the post-wipe worker log's three ground-truth populations (NK/LK/PK BPO 1,214 / 1,509 /
5,810) against `delta_windows.json`'s pooled per-window counts: no 226-based or 227-based
window is large enough. Scored under the **v227 band's ontology** (39,903 terms =
`go-basic-2025-07-22.obo`), `prop=fill`, `norm=cafa`, **`th_step=0.01`** (10x coarser than
the 2026-06 headline runs), PK-only exclusion applied.

**Q3. Is the competitive window v226->v227 rather than 220->227?**
**In the code, yes; in reality, almost certainly no.** `split_registry.COMPARABLE_WINDOW`
computes to v226->v227 and is the only place that says so. **Five independent records say
the board's window STARTS at v227 and runs to v230**: the 2026-06-27 board comparison
(`Sep_2025_Mar_2026`), the author's 2026-07-27 frame ("COMPETE 227->forward"), the
dates-checked 2026-08-19 memory ("227 is the window's START"), `board_nine_cell.json`'s
declared source, and -- decisively, in the same directory as the registry --
`band_registry.py`'s v227 band, described as "Deployed LAFA window (GOA **v227 to v230**)",
which is the ONLY one of the two registries any production code imports.
**Verdict: `COMPARABLE_WINDOW` is off by one window, and the window it lands on is the
-30.9% contraction.**

**Q4. Does the corpus contract about 30% twice?**
**Only as compressed file bytes.** -30.90% (v226->v227) and -29.59% (v231->v232) reproduce
exactly from the GB table, which was obtained by **HTTP HEAD on
`goa_uniprot_all.gaf.<v>.gz`** and which its own source labels "a PROXY ... the alarm, not
the evidence". The annotation-count decomposition that would make it a measurement has never
been run. The caveat is present in the memory and in `E2E-CANONICAL-RUN.md` and **absent from
`first_appearance.py` and `split_registry.py`, where the claim is now load-bearing** -- it is
one of the two stated reasons no adjustment split exists and therefore why no champion can
legally be selected.

**Q5. Must ground truth be built from ADDITIONS, never a net delta?**
**Decided yes (D-02, 2026-07-28), implemented, tested, and NOT WIRED.** The live path
computes `delta_ns = new_ns - old_ns` at `protea/core/evaluation.py:342` -- the retired
pairwise difference -- and for NK it does not even do that: `nk[protein] = new_all` (:337).
`first_appearance()` is imported by nothing but its own tests. The 63.7% that justified the
rule is an all-evidence MAXIMUM over "eleven consecutive release dumps", a history the
current registry cannot express (it holds nine releases and only four are loaded), with no
breakdown published anywhere. On experimental evidence -- the operating regime -- the rate is
"about one percent", and that figure has no receipt either.

---

# THE THREE THINGS A READER MUST NOT MISS

1. **`split_registry.COMPARABLE_WINDOW` is off by one window**, and `band_registry.py`, in
   the same package and the only one of the two that production code imports, says the
   opposite. The registry's headline window is the -30.9% contraction, on which nothing
   external has ever been scored.
2. **Both July decisions -- first appearance and the split registry -- are inert.** Zero
   production importers; the evaluation path still runs the pairwise difference the decision
   retired. Fifth and sixth instances of the declaration-gap pattern.
3. **The ~30% contraction is an HTTP `Content-Length` on a gzip file**, labelled a proxy by
   its own author, promoted to fact eleven hours later in shipped code, where it now
   deadlocks the adjustment split.

**The single highest-value next action:** dispatch `audit_evaluation_frames` (a registered,
read-only operation, unrun since the wipe). It reports `n_rows, with_frame, with_window,
with_role, with_arms, without_job` plus the distinct `(frame, temporal_window, leakage_role)`
combinations, and would settle Q1 and Q2 in one job. My testable prediction: the 93 surviving
rows point at one evaluation set whose `old_annotation_set_id` has `source_version = 220`.
