# E2E CANONICAL RUN: the single clean pass that covers the thesis

Author: Francisco Miguel Perez Canales.

This is the authoritative specification for ONE clean end-to-end run whose
purpose is to regenerate every number the thesis reports, at a defined and
frozen set of axes, and to select the trajectories that pass into the
manuscript. No prior result is preserved as a number; results are regenerated.
Trajectories (the decisions, mechanisms, and their measured place) are what
survives, in the thesis + the signal registry + memory.

It SUPERSEDES, for the definition of the scientific run, the June roadmaps
(`ROADMAP-THESIS-10.md`, `THESIS-FINISH.md`, `beat-lafa-1/`). Those carried the
old window convention (SELECT 220->227 / FINAL 227->230, a mixed-metric story)
and the pre-scale corpus. They move to `plans/archive/` for provenance; their
governing principles are inherited verbatim below.

## 0. Pre-flight (format gate, non-negotiable before wiping the box)

The machine is being formatted. Confirm each survives BEFORE the format:

- Memory store (`~/.claude/projects/.../memory/`, 1.2M, NOT git-tracked):
  already copied to `/mnt/protea-archive/.../preformat-preserve-2026-07-27/`.
  If the format touches `nvme1`, also push it to a private git remote.
- Postgres: dump `protea-2026-07-27.dump` (40G) is on the archive partition.
  Confirm the archive partition is out of the format scope, or replicate the
  dump off-machine.
- Repos (`thesis`, `agent-farm`, the 8 code repos): confirm `git push` is clean;
  they live on GitHub and survive.
- `storage/` (55G): almost entirely DERIVED results = noise to prune (see 6).
  Raw worth keeping: `protea-frozen-v227` (1.1G), `obo_cache` (30M).

## 1. Governing principles (inherited from ROADMAP-THESIS-10, non-negotiable)

- LINEAR STORY, NO VARIANTS. One frozen champion, one set of numbers, one
  narrative. No V1/V2/vNext.
- UI IS THE SINGLE SOURCE OF TRUTH FOR RESULTS. Every manuscript number is
  reproducible by opening the app, with provenance (temporal split, arm, frame).
- NO LEAKAGE, FIXED WINDOWS. Selection on VALID; the frozen system is scored
  ONCE on TEST. See 3.
- STRATIFY EVERYTHING (memory: always-stratify). Every measurement carries the
  four strata of axis B, with CIs on deltas.
- GATE AT RETRIEVAL, NOT THE BOARD (memory: pre-registration). Rank levers at
  the retrieval gate (recall@k, IA-coverage) on a cheap proxy before spending a
  board evaluation. ~15 documented channels were real mechanisms that did not
  convert; do not spend board compute to rediscover that.
- PUBLIC AND REPRODUCIBLE. Third party reproduces from public docs alone.
- IMPECCABLE FORM. Clean trees, no orphan worktrees, no vN tokens.

## 2. Axis A: corpus and scale

- Reference (evidence) set: reviewed / Swiss-Prot experimental. STAYS the
  spine. Document snapshot drift: new reviewed proteins may enter between cuts;
  the run records which reviewed set (accession list + count + snapshot) it used.
- TrEMBL, two SEPARATE concerns, do not conflate:
  - Directed case mining (SIGNAL): TrEMBL admitted only where the reviewed
    neighbour pool is thin (NK / dark region, long-protein arm, taxonomic gaps),
    each row carrying a provenance flag (reviewed vs unreviewed). Hypothesis:
    unreviewed density lifts retrieval where reviewed is sparse. Measured at the
    retrieval gate per stratum before it earns a place.
  - Scale ingestion (SYSTEM CAPABILITY): the pipeline must ingest several
    million embeddings and remain correct and operable. This is a scalability /
    distributed-system claim of the thesis, independent of whether that mass
    enters as signal. Prove throughput, correctness, and reproducibility at
    0.5M -> several M.
- Distributed compute: a second machine joins as an EXTRA WORKER POOL on the
  same queue and Postgres (minimal architectural change, maximal throughput).
  The run is the demonstration that the environment is distributed and scalable.

## 3. Axis: temporal frame (CONFIRM before locking)

Working assumption (current campaign, memory temporal_eval_run_2026_06_26):
VALID = 225 -> 227 (selection happens here), TEST = 227 -> 230 (frozen system
scored once), metric = f_micro_w, externally validated on LAFA.

DISCREPANCY TO RESOLVE: the June roadmaps fixed SELECT 220 -> 227 / FINAL
227 -> 230. This spec uses 225 -> 227 / 227 -> 230. Author confirms the window
before the plan is committed (leakage-critical). Also flagged in memory:
v230 annotation set is under-loaded (-18.87% vs -1.40% upstream) and truncates
the eval set; a reload may be required before TEST is trustworthy.

## 4. Axis B: stratification (fixed, applied to EVERY measurement)

category (NK / LK / PK) x aspect (MFO / CCO / BPO) x sequence length (buckets)
x homology band to the reference, split by evidence provenance (experimental vs
non-experimental). The 9 board cells = category x aspect. Length and homology
are the EXPLANATORY axes inside each cell; the homology-x-evidence axis gives a
coordinate to the prior-knowledge wall (where the protein already knows).

## 5. Axis C: ablations, and D: the signal registry

Ablations (ranked at the retrieval gate first, board only for the champion):
- PLM: the 8-PLM matched-parameter grid at retrieval level. Which PLM per cell.
- K: KNN neighbourhood size.
- Scores / signals: marginal contribution of each signal per cell (LOFO-style).
- SOA: the best composed solution vs TransFew / DeepGO-SE / etc., per cell.

Benchmark economy (author's decision): run the PLM x K x score grid on a
representative STRATIFIED SUBSAMPLE, gate at retrieval, and confirm the champion
on the full set. Do not run the full factorial everywhere. Log every truncation
(no silent caps).

Deliverable D, the signal -> mechanism registry (the constituted contribution):
each signal characterised by what it is, its mechanism, the stratum where it
helps, and where it is null or negative. One source, three renderers (UI, docs,
thesis), one lint. The registry is what constitutes the path from #7/9 to the
#9/9 objective, and it leaves the two BP cells (LK-BPO, PK-BPO) documented as a
cross-protein calibration frontier (memory: bp_frontier_characterized), not as
an unexplained gap.

## 6. Transversal E: score search -> decision tree

The pivot that justifies the tree reranker as a contribution, not an
implementation detail. Show, per cell: (1) the ceiling of hand-calibrated score
fusion under a proper hyperparameter search (documented to top out early), then
(2) the tree reranker crossing that ceiling. The transversal explorations are
designed to expose WHY a learned tree over the temporal features beats a tuned
blend of the same signals (memory: sparse-contrastive #2, temporal datasets).

## 7. Noise pruning (the archive pass)

- `storage/`: archive to `/mnt/protea-archive` every derived-result directory of
  a superseded trajectory (transfew, cooc_experiment, struct_gate, salvage,
  sse_* except the receipt, regen_headline, text_scorer, layer_ablation, ...).
  Carry to the clean machine only raw inputs (`protea-frozen-v227`, `obo_cache`)
  and the code. Nothing derived travels.
- `plans/`: move the superseded June roadmaps to `plans/archive/`; this file is
  the single authoritative scientific-run spec. Update CATALOG.md accordingly.

## 8. Exit criteria (what "done" means)

1. Every thesis number regenerated on the confirmed frame, UI-visible with
   provenance, leakage-clean.
2. The signal -> mechanism registry complete across the four strata.
3. The score -> tree transversal shown per cell.
4. The distributed / scale claim demonstrated (several M embeddings, two-machine
   worker pool, reproducible).
5. The path #7/9 -> #9/9 is either closed or its frontier documented per cell.

## 9. Open decisions (block committing this plan)

- Pre-flight: does the format wipe `/mnt/protea-archive` (nvme1)?
- Frame: confirm VALID 225->227 / TEST 227->230; and whether v230 needs a reload
  before TEST.
