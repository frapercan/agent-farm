# THESIS-FINISH: precise plan to close the doctoral thesis at 10/10

Authoritative finishing plan across every front. Author: Francisco Miguel Perez
Canales. Written 2026-06-15 after the LAFA first-place result (mean f_micro_w
0.391) was achieved, validated, and partially productised. Supersedes nothing;
it sequences the remaining work onto one critical path plus parallel tracks with
exit criteria per track. The canonical per-slice catalog for the platform
integration is `plans/lafa-integrate/PLAN.md`.

This plan is REQUIREMENTS-DRIVEN: the work is organised around the requirements in
`plans/REQUIREMENTS.md` (functional FR-1..FR-4, non-functional NFR-UI / NFR-TEST /
NFR-INFRA / NFR-DOCS / NFR-ARCH / NFR-PROCESS / NFR-PERF / NFR-REPRO). Each track below delivers
one or more requirement IDs; the thesis carries a requirements-engineering framing
that enumerates them and shows the design and evaluation satisfy each. New work
should cite the requirement it advances.

## North star (the 10/10 bar)

Thesis defended and deposited, defensible at 10/10:
1. The method is complete, leakage-clean, reproducible, and fully operable from
   the UI.
2. The benchmark is selected without leakage on the SELECT window (GOA 220 to
   227) and the frozen system is scored once on the FINAL window (227 to 230) and
   externally validated on LAFA.
3. The manuscript tells one linear story; every number it reports is verifiable
   live in the application.
4. The 8 repositories are released at v1.0 with green Sphinx docs.
5. Bootstrap, infrastructure, container images, and the LAFA submission are
   public and reproducible by a third party from the docs alone.
6. The deep-learning track is parked behind a documented gate.

## State snapshot (2026-06-15)

- Science: DONE. First place on LAFA, mean 0.391 (NK 0.477 / LK 0.482 / PK
  0.215), validated leakage-clean on a SELECT-internal held-out split, persisted.
- Manuscript: Experiment 13 (first place) merged; abstract and conclusion
  updated; factual consistency fixed (CAFA 6 final ranking #19, feature schema
  unified to 56). Builds clean. GAPS: Experiment 9 (multi-PLM grid, all
  `\gridna` placeholders) and Experiment 10 (universal reranker, `\TODO`) need
  live `/benchmark` data.
- Native UI integration: INT-1 through INT-4 merged (contracts 0.5.0 on main;
  native self-prior; native cross-aspect association + co-occurrence table;
  native full-vocabulary classifier producer). All producers gated behind
  `compute_*` flags (off by default, so default behaviour is unchanged).
  REMAINING: INT-5 through INT-9.
- HuggingFace: DONE (XaxiPiruli/protea-lafa-fullgo). Zenodo: tooling ready,
  deferred. 8 repos: docs-CI green, LICENSE present (Unlicense), author-email
  standardised; remaining is the 1.0.0 bump and the PROTEA develop to main
  reconciliation. Tokens for GitHub/HF/Zenodo were pasted in chat and MUST be
  rotated.

## The decided parity rule (load-bearing)

The native pipeline must reproduce the headline number **0.3911**, and it must do
so **without depending on fixed or lucky seeds**, deterministically, and free of
winner's curse. The mechanism that satisfies all of this is **seed-averaging by
convergence**, not seed selection:

- The classifier is trained N times from N independent initialisations and the N
  outputs are pooled (consensus union of each run's top terms, score = sum / N).
  Averaging REDUCES variance; it is the opposite of picking the best run. This is
  the anti-winner's-curse property.
- The N seeds are arbitrary and sequential (e.g. 0..N-1), NOT cherry-picked. The
  result rests on the average having CONVERGED, not on any specific seed set.
  This must be demonstrated: show the sealed mean is stable across different seed
  sets and as N grows (the 5-seed to 7-seed step already showed convergence at
  ~0.390 to 0.391); report the residual seed-to-seed spread so the claim is the
  converged value plus a small, quantified band, not a three-decimal point pick.
- For native reproducibility, persist the N classifier checkpoints; the producer
  loads all N and averages them deterministically. Given the checkpoints, the
  served score is fully reproducible with no runtime randomness.
- Net: the reported native figure is "0.391 (mean of N seed-averaged runs,
  converged; seed-to-seed band +/- X)", reproducible from the persisted
  checkpoints, defensible as variance-reduced rather than seed-selected.

This rule applies to INT-4/INT-7 (the classifier producer and its artifacts) and
to how the thesis phrases the native number.

## Critical path

T1 (native UI integration) is the bottleneck for north-star criteria 1 and 3
(every number live in the UI). T2 through T6 are parallel tracks that feed the
defence.

---

## TRACK 1: native integration, the 0.3911 computed from zero in /benchmark

Each slice is one PR with strict local CI green (the project CI catches
discipline a local overlay misses: smell-budget <=60 LOC/method, the
registered-op negative-case matrix, em-dash, autodoc, mypy). Pattern proven on
INT-2/3/4.

- **INT-5: per-category combiner.** In `_reranker_scorer.py`, dispatch the three
  NK/LK/PK boosters instead of one. RESOLVE FIRST the category definition per
  aspect so it matches the benchmark partition: NK = no t0 experimental
  annotation in that aspect; LK = t0 experimental knowledge in some aspect but
  not this one; PK = t0 experimental in this aspect. Add `annotation_set_id` to
  the batch payload (otherwise the category silently defaults to NK). Each
  prediction's category is derived from the query protein's pre-cutoff known
  terms.
- **INT-6: export train/serve parity.** `export_research_dataset` must emit the
  classifier / self_prior / association columns, so the boosters are trained on
  exactly the features served at predict time.
- **INT-7: register artifacts + exact parity.** Register the three per-category
  boosters as `RerankerModel` rows (import-by-reference) and the classifier.
  Implement the seed-averaging parity rule above: re-train the classifier over N
  sequential seeds on the t0 frame, persist N checkpoints, average in the
  producer. Validate the served classifier reaches the converged standalone
  ~0.369 and the ensemble reaches ~0.391.
- **INT-8: end-to-end seal + UI.** Enable the `compute_*` flags, REDEPLOY (the
  maintainer authorised this; it also resyncs the live stack's contracts from
  0.3.0 to 0.5.0), run `build_go_cooccurrence`, then `predict_go_terms` plus
  `run_cafa_evaluation` over the 7401 frame, and validate against the offline
  reference `storage/fullgo_models/predictions_merged_7401.tsv` (scores 0.3911).
  Result: the native 0.3911 appears as a full-system stage on `/benchmark`,
  beside the homology 0.324.
- **INT-9: parity, tests, docs, ADRs.** A test asserting native == offline within
  the converged band, ADRs for the new producers, and the thesis reproducibility
  paragraph pointing at the live `/benchmark`.

Gates: the redeploy (authorised) and the seed count N + the convergence evidence
(part of the parity rule).

## TRACK 2: manuscript content gaps (needs the live stack)

- **Experiment 9, multi-PLM grid:** populate the 24 `\gridna` cells with real
  `/benchmark` data on the SELECT window 220 to 227 (PLM x K x score). This is
  the number-one content gap.
- **Experiment 10, universal reranker:** finish the 227 to 230 recompute and
  remove the `\TODO`.
Runs on the live stack, in parallel with T1.

## TRACK 3: public release

- **Zenodo (deferred, now unblockable):** re-register the 24-dataset grid in the
  DB (import-by-reference from MinIO, no recompute), then `upload_to_zenodo.py`
  creates drafts to review and publish. Token available.
- **LAFA submission of the first-place system:** once T1 makes PROTEA compute the
  reranked score natively, containerise that system and push to ghcr (token with
  write:packages available); submit. The old KNN container (0.312) already
  exists; this is the 0.391 system.

## TRACK 4: 8 repositories at v1.0

Coordinated bump to 1.0.0 and reconcile PROTEA develop to main (565 commits
ahead). Feature-freeze is a maintainer decision. docs-CI, LICENSE, and versions
are already in place.

## TRACK 5: third-party reproducibility (P1/P2)

`.readthedocs.yml`; docker-compose validation; the LAFA container contract bridge
(entrypoint flags vs the evaluator's flags); a step-0 infrastructure runbook; the
InterProScan binary prerequisite doc.

## TRACK 6: final hygiene

Rotate the three tokens (still exposed in chat). Final clean-tree audit and
memory consolidation.

## TRACK 7: documentation quality (every doc has a function, aligned to the goals)

Principle: every document is either maximum-quality and on the main research line,
or it is moved to a clearly-marked appendix, or it is removed. Nothing of genuine
value is deleted; secondary material is preserved and MARKED for later
recovery/improvement. The marking convention is a one-line banner at the top of any
deferred or secondary doc: `> [DEFERRED <date>: recover/improve/update later -
<reason>]` (or `[SUPERSEDED <date> by <pointer>]` for history kept for the record).

- **Thesis (mostly already clean, audited 2026-06-16).** The spine is correct:
  main chapters carry the leakage-clean experiments (8 to 13, including the LAFA
  first-place 0.391), and appendix D holds the pre-leakage-fix development trace
  (experiments 1 to 7), already marked with its caveat. Figures pass (no broken
  images, all data files present, no broken refs). The ONLY real gaps are the two
  known content placeholders, owned by Track 2: Experiment 9 multi-PLM grid
  (`\gridna`) and Experiment 10 universal reranker (`\TODO`). Remaining doc-quality
  work on the thesis is a final pass after Track 2 fills those: one linear read for
  any residual stale number, a `latexmk` undefined-ref check, and a confirmation
  that every reported figure points at the live `/benchmark`. NOTE: the local
  working checkout had drifted behind `origin/main` and must be kept in sync (a
  stale checkout produced a false "fourth place" audit reading on 2026-06-16; the
  real manuscript is first place 0.391).
- **Repository docs.** Audit the 8 repos so every doc (README, Sphinx pages, ADRs,
  RESULTS/REPRODUCE) has a clear function and no stale numbers. The lab `fullgo/`
  docs are already updated to 0.391; the READMEs are production-grade per the v1.0
  audit. Sweep for any residual superseded numbers or orphaned pages; mark or fix.
- **Plans store.** Stale plans whose goal is achieved are marked SUPERSEDED/DONE
  with a banner pointing at the current direction (done 2026-06-15 for
  `lafa-number-one/PLAN.md` and `NEURAL-HEAD.md`). Keep the catalog honest: one
  current direction, the rest clearly history.
- **Memory.** Consolidated 2026-06-15: one START HERE (the 0.391 result), the older
  date-blocks relabelled as history, three contradictory topic-file descriptions
  marked SUPERSEDED, index back under budget.

Exit: every doc is max-quality-and-on-the-spine, or appendix-and-marked, or removed;
the marking banner is applied to all deferred/secondary docs so nothing is silently
lost; the thesis tells one linear story with no errors and no low-relevance noise in
the main chapters.

## Recommended sequence

1. Maintainer decision pending: feature-freeze for the v1.0 / develop-to-main
   release (the parity rule is already decided: 0.3911 via converged
   seed-averaging, no fixed seeds). 
2. T1 (INT-5 to INT-8) in series to the redeploy = native 0.3911 in the UI. In
   parallel, T2 (Experiment 9/10 on the stack) and T3-Zenodo (re-register +
   drafts).
3. T4 (v1.0 release) after the freeze. T5 (reproducibility docs) in parallel.
4. T6 (rotate tokens) at publication close. INT-9 plus the manuscript final pass
   (every figure pointing at the live `/benchmark`) = 10/10 defence.

## Exit criteria (done means)

- `/benchmark` shows the native, platform-computed 0.391 (converged
  seed-average) beside the homology 0.324, reproducible from persisted
  checkpoints. Experiments 9 and 10 populated from that surface.
- Manuscript: one linear narrative, every number live-verifiable, builds clean.
- 8 repos at v1.0 with green Sphinx docs; develop reconciled to main.
- Datasets on Zenodo; the first-place system submitted to LAFA; bootstrap and
  infra reproducible from public docs.
- Tokens rotated; trees impeccable; DL track gated.
