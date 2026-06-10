# ROADMAP: thesis to 10/10 (consolidated, end to end)

Authoritative sequencing overlay for finishing the doctoral thesis. This is
not a new plan system; it orders existing slices (see per-loop PLAN.md and the
rendered master PLAN.md) onto one critical path plus parallel tracks, with exit
criteria per phase. Author: Francisco Miguel Perez Canales.

Status snapshot 2026-06-10: 298 slices total, 199 done. Stack up (/health ok).
Thesis manuscript builds (155 pp), graded 90/100 by survey: the one blocking
content gap is the multi-PLM benchmark grid in Ch6 (Exp 9). 0/8 repos at v1.0.
The app has a `/benchmark` page but it does not yet show LAFA-frame results,
per-arm provenance, or the leakage-clean train/VALID/TEST story.

## North star

Thesis defended and deposited, defensible at 10/10. Concretely:
1. The PROTEA method is complete, leakage-clean, reproducible, and fully
   operable from the UI.
2. The benchmark (PLM x K x score) is selected without leakage on VALID and
   scored ONCE on TEST; the frozen champion is externally validated on LAFA.
3. The manuscript tells ONE linear story; every number it reports is verifiable
   live in the app.
4. The 8 repos are released v1.0 with green Sphinx docs.
5. The DL/neural track is explicitly parked behind a documented gate.

## Governing principles (non-negotiable)

- LINEAR STORY, NO VARIANTS. No V1/V2/vNext/"its cousin". One frozen champion,
  one set of numbers, one narrative. (memory: feedback_thesis_linear_ui_verifiable_2026_06_10,
  reinforces the no-vN-token linter rule.)
- UI IS THE SINGLE SOURCE OF TRUTH FOR RESULTS. The thesis cites what the app
  shows, with provenance (temporal split, arm, frame). An examiner reproduces a
  number by opening the page, not a spreadsheet. No manuscript number may exist
  that the UI cannot surface.
- NO LEAKAGE. Select on VALID(226->227), touch TEST(227->230) exactly once on
  the frozen champion. LAFA-frame f_micro_w / wFmax are the selection metrics.
- IMPECCABLE FORM. Clean trees, no orphan worktrees, no root cruft, every loop.

## Critical path to defense

A0 -> A1 -> A2 -> A3 -> A4 -> A5 -> (D1) -> D3.
Tracks B (UI), C (codebase), E (docs+releases), F (publication) run in
parallel and feed D. B1 is a co-requisite of D1 (numbers must be UI-visible
before the manuscript cites them).

---

## TRACK A: scientific spine (experimentation)

The user's sequence: different PLM x different K x different score, select the
best without leakage, train a classifier on the winners using their data, then
ensemble with InterProScan. DL is the stale tail.

### A0. Freeze the no-leakage protocol  [P0, on critical path]
Build the VALID(226->227) staging in LAFA-frame and lock the select-on-VALID /
touch-TEST-once gate. Today eval.parquet is TEST-only.
- Slices: F-EVAL-PROTOCOL.valid, F-EVAL-PROTOCOL.c (fresh-cutoff single-knob
  inference / LAFA submission generator), F-EVAL-PROTOCOL.
- Open decision: the user referenced selection on "220->227"; the current
  protocol uses VALID 226->227 (interim) with TEST 227->230. Confirm whether
  VALID is the single interim window 226->227 or a wider 220->227 multi-window
  selection. Default: 226->227 unless the wider window is wanted for power.
- Exit: VALID harness emits LAFA-frame f_micro_w per (category, aspect); TEST is
  sealed behind a one-touch guard; both frames documented as identical machinery.

### A1. Full benchmark grid, leakage-clean, LAFA-frame  [P1, critical path]
PLM(8) x K{3,5,10} x score{KNN raw, scoring-configs, reranker}, measured on
VALID in LAFA-frame. This is also thesis Ch6 Exp 9 (the #1 content gap).
- Slices: FARM-EXP.GRID-v226 (closed-set + coverage query), FARM-EXP.8
  (constrained grid execution), FARM-EXP.7 (8-PLM ensemble cell),
  FARM-EXP.11 (per-aspect results table for Ch6).
- Exit: coverage query green over the declared closed set; one
  f_micro_w per (PLM, K, score, category, aspect) cell, all visible in the app.

### A2. Selection without leakage  [P0, critical path]
Pick the best cells on VALID only. Record winners per aspect with their
provenance. No TEST numbers consulted.
- Exit: a frozen selection table (best PLM/K/score per aspect) committed and
  UI-visible, with a leakage-clean badge.

### A3. Train the classifier (universal aspect-conditioned reranker)  [P0, critical path]
One pooled, aspect-conditioned reranker trained on the winning cells' data
(supersedes per-cell phase3a). This is "train a classifier on the best ones".
- Slices: F-RERANK-UNIVERSAL and .1-.7. Gating sub-slices that decide the
  number: .5a (IA-feval early-stop fix + true pooled staging), .5d (correct
  LambdaRank group key + K-collapse). .5b/.5c are gated augmentation/HPO.
- Exit: single pooled artifact beats the KNN baseline on VALID via IA-weighted
  paired bootstrap across all 9 categories; frozen; selective-deploy map is a
  measured OUTPUT, not a hand-pick (.6).

### A4. Ensemble: Arm 2 (MLP tower) + Arm 3 (InterProScan)  [P1/P2, critical path tail]
Gated late-fusion per (category, aspect) in LAFA frame.
- Slices: F-METHOD-INTERPRO.perf (restore the EBI precalc match-lookup; today
  ~3h/7401 proteins via local-HMMER fallback, blocks fast InterPro),
  F-METHOD-INTERPRO (Arm 3 as a uniformly-optional gated arm), FARM-EXP.18
  (InterPro feature family), F-METHOD-MLP-TOWER (Arm 2 full-GO tower).
- OPEN SCIENTIFIC QUESTION (must resolve here): the InterPro late-fusion lift
  showed big TEST gains but did NOT replicate on a held-out VALID window (could
  be frame mismatch, crude blend, or genuine winner's curse). Resolve on a
  SAME-FRAME LAFA VALID with learned integration before shipping. If it does not
  hold leakage-clean, InterPro stays optional-and-off in the champion and the
  thesis reports it as an investigated-but-unconfirmed arm. (memory:
  project_interpro_arm3_result_2026_06_09.)
- Exit: gated ensemble >= core on VALID, each arm's contribution measured;
  ensemble composition frozen.

### A5. Freeze champion, score TEST once  [P0, critical path]
F-METHOD-CORE-K10 confirmed the uniform-K10 KNN+reranker core (per-aspect-K was
rejected on VALID). Freeze the full champion (core + any arm that survived A4),
run the single TEST pass, record final numbers. These become the thesis Ch6
numbers and the LAFA submission.
- Exit: exactly one TEST evaluation; frozen results stored and UI-visible.

### A6. LAFA external validation + submission  [P0/P1, parallel after A5]
- Slices: F-LAFA-SUBMIT.gpufix (pin container torch/CUDA to host driver, re-run
  on GPU; today CPU fallback wedges ~15h), F-METHOD-CONTAINER (own-reference
  external-volume packaging), F-LAFA-SUBMIT.knn (submit), F-LAFA-SUBMIT.reranker
  (second entry). requires_human for the actual server submission.
- Exit: external LAFA result within tolerance of the internal TEST number;
  documented as the same frozen champion (no separate story).

### A7. DL / neural head  [PARKED, gated]
Stale. ADR-D38 deferral stands. Keep project_neural_head_full_run data.
- Gate to revisit: only if a quantitative precondition is met (per ADR-D38) and
  the core thesis is otherwise complete. Otherwise it is documented future work,
  not a thesis chapter. Do NOT let it block the defense.

---

## TRACK B: everything from the UI (eval surface + benchmark consolidation)

The app has the pages; the gap is methodology clarity, not missing dispatchers.

### B1. Eval surface reformulation  [P1, co-requisite of D1]
Surface LAFA-frame results + explicit train/VALID/TEST window labels + per-arm
provenance badges (KNN / reranker / InterPro) + a leakage-hygiene marker
(select-on-VALID vs internal probe) on `/benchmark`. This consolidates the
benchmark screen (the original ask) and makes every Ch6 number UI-verifiable.
- Slice: F-METHOD-EVAL-SURFACE. The offline run.json already holds
  valid_band_metrics; this is presentation + schema, not new compute.
- Exit: an evaluator distinguishes publishable LAFA-frame TEST numbers from
  diagnostics, and each frozen number is reproducible from the page.

### B2. InterPro arm dispatchable from the UI  [P1]
run_interproscan_batch, predict_go_terms_from_interpro, load_interpro_go_mapping
are CLI-only today. Expose them so the full method (KNN+reranker+InterPro) can
be benchmarked from the app.
- Exit: the three InterPro operations dispatch from the UI like the other 10.

### B3. Experiment-run narrative + detail polish  [P1/P2]
Experiment-run narrative page (what decision drove a run; which feature/reranker
snapshot). Dataset detail is already comprehensive; job detail is thin.
- Slices: F-FEAT-WEB.DATASET-DETAIL (charts/nav), F-WEB-RUNNING-JOBS-WIDGET.
- Exit: each benchmark cell links to its run narrative and provenance.

### B4. UX sweep + form polish  [P2]
- Slices: F-UX-REVIEW-SWEEP, F-WEB-FORM-POLISH, reranker import-by-reference form.
- Exit: an external evaluator runs the full benchmark and reads leakage-clean
  results entirely from the UI, with no CLI step.

---

## TRACK C: codebase production-grade

### C1. Ops stability  [P0]
FIX-STACK-SELF-HEAL (boots robustly + stays up), FIX-REAPER-CTOR (reaper dead on
develop), FIX-ANNOTATE-BANNER-ACCURACY, FIX-ANNOTATE-CONFIG-SLOW, F-OPS-JOBS.1
(dedup + lease + SIGTERM), F-PRED-FASTPATH (predict < 10s).
- Exit: stack self-heals across restarts; predict_go_terms < 10s on small queries.

### C2. Pipeline perf + coherence  [P1]
F-EXPORT-MINIJOB.1-7, F-EXPORT-PIPELINE-DECOUPLE, F-MULTISTAGE-COHERENCE.1-4,
F-PERF-PROFILING. (F-EXPORT-MINIJOB.5 default-flip is requires_human.)
- Exit: export pipeline fast and resumable; multi-stage contract unified.

### C3. Ownership + API (needed for third parties)  [P1/P2]
F-API-OPENAPI-POLISH, F-USER-OWNERSHIP.1-3, F-USER-PUBLISH.1-2,
F-USER-SUBSCRIBE.1-2, F-OPS-JOBS.2-3 (pause/resume/cancel + DLQ UI),
F-AUTH-E2E, HARNESS-E2E-FIXTURES.1, UX-ADMIN-AUDIT.
- Exit: clean OpenAPI; per-user scoping; auth regression green.

---

## TRACK D: docs, the linear thesis

### D1. Close the Ch6 content gap  [P1, critical path, needs A1 + B1]
Incorporate the multi-PLM grid (from A1) into Ch6 Exp 9 with final numbers, each
traceable to a UI cell. Replace all "in progress" prose.
- Exit: Ch6 reports the full PLM x K grid; every table cell maps to a `/benchmark`
  result.

### D2. Strengthen claims  [P1]
Quantify PK-BPO mitigation (Ch7 limitation), re-run eggNOG-mapper on the
leakage-free split (the "pending LB.2" markers), fix the 8 TikZ legend warnings.
- Exit: no "pending" markers; eggNOG comparison on a shared leakage-free split;
  clean build log.

### D3. Defense + deposit  [P1, critical path tail]
TD.1 (final read pass + supervisor review; blocked on supervisors David
Orellana-Martin + Ana M. Rojas), TD.2 (defensa slides), TD.3 (deposit-ready PDF).
- Exit: supervisor-approved, deposit-ready PDF; thesis.pdf stays untracked,
  built from source.

Note: the complexity paper (10 chapters, done) and the thesis are kept as
separate but coherent artifacts; the complexity commit f9f585b lives on
pivot/big-o-spine-2026-05-26 in complexity-paper (no remote yet; give it one).

---

## TRACK E: Sphinx docs + versions + releases

### E1. Sphinx to a uniform 10/10  [P2]
Add docs CI (.github/workflows/docs.yml) to the 7 repos that lack it (only
PROTEA has it). Add CHANGELOG.md to the 6 that lack it. Fill the minimal
toctrees (protea-method, protea-reranker-lab: add quickstart/installation/
contributing). Standardize on the shibuya theme across all 8.
- Exit: every repo builds Sphinx in CI; published docs consistent.

### E2. Version/tag sync  [P1]
Bring pyproject version into line with the latest git tag in each repo; tag the
2 untagged repos (protea-reranker-lab, protea-runners).
- Exit: pyproject version == latest tag in all 8.

### E3. Coordinated v1.0.0 release  [P1]
After E2, bump all 8 repos to v1.0.0 simultaneously with dated CHANGELOG
entries and tags. This is PAPER-TMLR.9 (release tags v1.0 on 8 repos).
- Exit: 8 repos at v1.0.0, tagged, released.

---

## TRACK F: publication + reproducibility (parallel, not blocking defense)

- F1. F-DATA-PACK.5: Zenodo / Hugging Face dataset upload (requires_human).
- F2. FARM-INFRA.5: thesis-grade reproducibility ceremony (fresh-machine
  rebuild verification end to end).
- F3. TMLR paper PAPER-TMLR.0-10: optional parallel publication; .10
  (anonymization + OpenReview submission) is requires_human. Decide at
  PAPER-TMLR.0 whether to run this track before or after the defense.
- Exit: datasets archived with DOIs; repro verified on a clean box; paper
  decision recorded.

---

## Sequencing summary

1. A0 (protocol freeze) and B1 (eval surface) start first; B2 unblocks the
   full-method grid.
2. A1 grid (leakage-clean, LAFA-frame) runs and immediately populates Ch6 (D1).
3. A2 selection -> A3 reranker -> A4 ensemble -> A5 single TEST pass.
4. A6 LAFA submission validates the frozen champion externally.
5. C (ops) runs in parallel from the start; E (releases) once the method is
   frozen so versions capture the final code; F at the end.
6. D3 (defense + deposit) gates on D1 + D2 + supervisor availability.
7. A7 (DL) stays parked behind its gate; never on the critical path.

## What "10/10" requires that is not yet true

- A leakage-clean VALID harness in LAFA-frame (A0).
- The full PLM x K x score grid measured and UI-visible (A1 + B1).
- A single frozen champion scored once on TEST, no variant stories (A5).
- Every Ch6 number reproducible from the app (B1 + D1).
- 8 repos at v1.0 with green Sphinx docs (E1-E3).
- Supervisor sign-off and a deposit-ready PDF (D3).
