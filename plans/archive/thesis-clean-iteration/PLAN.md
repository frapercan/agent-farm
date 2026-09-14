# Clean thesis iteration — the plan

Blueprint for one clean rewrite of the manuscript. Built from a three-agent audit
(evaluation / framing / platform) cross-checked against the validated research
frame. Companion to `../thesis-pillars/PILLARS.md`. Written 2026-07-08.

## The governing principle

> **One metric (IA-weighted micro-F, `f_micro_w`), one frame (sealed LAFA
> v227->v230), one spine (the four pillars). Every number board-faithful,
> reproducible, and live-verifiable.**

The audit's unanimous verdict: this is a **spine problem, not a numbers problem**.
The thesis has the right data but organizes around the *wrong* metric (macro
cafaeval-Fmax), the *wrong* frame (GOA 220->229/226->230), the *wrong* backbone
(ESMC-300M) and a *stale* ablation claim - so the real headline (`f_micro_w`
0.4063, first in 7 of 9 cells) is buried in a "historical pre-leakage" appendix.
Fix the spine and most of the numbers fall into place, because the clean numbers
already exist (this campaign produced them). Only ONE new heavy computation is
required.

## The intellectual fix: reframe RQ2

Replace the old RQ2 ("do alignment/taxonomy/anc2vec/PCA features add lift?") with:

> **RQ2': Which class of functional evidence is decisive in each
> knowledge x aspect regime, and where is the evidence-bound ceiling?**

This single reframe:
- promotes **Pillar 3** (the 9-cell grid as a *map of regimes*) from absent to a
  first-class research question;
- makes **Pillar 4** (the BP wall) the positive, evidence-bound-frontier
  contribution instead of a buried limitation;
- **kills the `anc2vec_query +0.1449` claim at its root** (replaced by the 9-cell
  LOFO: classifier dominates NK/LK, association+anc2vec_query carry PK, homology
  proposes but never discriminates) - so it need not be asserted-then-retracted-
  then-re-asserted across three chapters;
- pulls in the two currently-unwritten results (structural GATE, representation
  science) as the frontier + mechanism evidence.

## KEEP / REDO-CLEAN / CUT map

### KEEP (validated - foreground)
- **The headline**: `f_micro_w` 0.4063, #1 in 7/9 (Exp 13). But **relocate** it out
  of Appendix D ("historical pre-leakage") into the main Results.
- Exp 12 (homology-only 0.324, the 7,401-frame alignment audit), Exp 10 (universal
  reranker 0.387 ~= per-category 0.388).
- Platform design spine (decision-first): contracts-first plugin ecosystem;
  schema-drift canonical fingerprint (`compute_schema_sha` incident); the Operation
  abstraction + registry; the distributed job model (two-session, parent-child,
  RetryLaterError); leakage-free temporal protocol; aspect-separated KNN;
  GOA self-prior leakage-safe injection; the LAFA three-container ablation ladder.
- Chapter 2 (biological background) essentially whole. Appendix C (ADR log).
  Appendix D as an honest dead-ends record (minus the relocated flagship).

### REDO-CLEAN (real but stale -> restate with the clean numbers we already have)
- **Setup / Metrics**: one metric (`f_micro_w`), one frame (227->230), one primary
  backbone (Ankh-base), remove the pgvector-KNN prose mention, fix the ESM-2 set to
  150M/650M/3B (15B is not used).
- **Exp 8 feature-family ablation -> the 9-cell LOFO** (`lofo_9cell/result.json`).
- **9-cell baseline grid on `f_micro_w`**: NK 0.648/0.331/0.481, LK 0.559/0.354/0.467,
  PK 0.230/0.141/0.273 (replaces the 220->229 lab-Fmax baselines).
- **Abstract P3**: collapse the stale-lab-number wall; lead with 0.408.
- **Conclusion RQ2 + Future Work premises**: rebuild on the LOFO map (not +0.1449).
- **Appendix A/B**: reconcile to the sealed frame; eggNOG baseline re-run/re-stated.
- **Reconcile all inconsistencies** to one canonical value each: deploy modes = 5;
  primary/served/LAFA embedding model (state which is which); GOA snapshot count;
  repository count = 8 (or state the "7 plugin repos + the lab" split explicitly);
  Swiss-Prot reference size = 527k; add an **ADR for D40** (leakage-free temporal).

### CUT-PAJA (remove or compress)
- Exp 8 ablation table (the +0.1449), Exp 9 three-seed replication (0.7291 macro),
  Exp 11 self-prior speculation (fold one sentence into Exp 12's negative).
- **Chapter 5: ~40-50% compressible** - code listings (`session_scope`,
  `discover_plugins`, entry-point TOML, EmbeddingBackend interface), per-backend
  tokenizer trivia, the operations/routers/queues/process-roles enumerations,
  InterPro ORM detail, KNN shim, prediction export, testing strategy, half the
  complexity derivations -> tables or repo-doc references.
- **Chapter 4: ~25-30% compressible** - Queue Topology, Data Model field lists, the
  17-router enumeration, and the entire Internal Design Patterns section (cut).
- **Related Work: ~25-30%** - dedupe Ankh/ProstT5/TALE/Foldseek (described 2-3x),
  halve the MIL section.
- Internal loop/PR codes throughout (T-RES.1b, FARM-EXP.13, PR#..., F-DATA-PACK).
- Textbook Big-O derivations (keep the empirical complexity validation).

### MISSING (must WRITE - these are unwritten contributions, not paja)
- **The learned k-WTA retrieval encoder** (config d8979601, the +40% lever) has NO
  design section in ch4/ch5. This is the most novel contribution and it is absent.
  Write it as a first-class design + methods section.
- **The representation-science ablation** (learned-sparse >> fixed-sparse > dense;
  standardization rescues sparse; last layer suboptimal) -
  `storage/layer_ablation/WRITEUP.md`. The mechanism that explains the lever.
- **The structural GATE** (BP wall is evidence-bound; structure conserves MF not BP)
  - the Pillar-4 frontier evidence.

## The clean experiment / operation set (mapped to pillars)

Almost everything already exists from this campaign. Status:

| # | Experiment | Pillar | Status |
|---|---|---|---|
| 1 | 9-cell board-faithful headline (0.4063, #1-in-7/9) | 2/3 | DONE |
| 2 | 9-cell LOFO = map of regimes | 3 | DONE (`lofo_9cell`) |
| 3 | Reproducibility: native vs board (within 0.007) | 2 | DONE |
| 4 | Cumulative evidence ablation (homology->+clf->+assoc->full) | 1/3 | PARTIAL - re-run clean per cell |
| 5 | BP-wall frontier (structural GATE + RED levers) | 4 | DONE (`struct_gate`) |
| 6 | Representation science (learned-sparse >> fixed) | 1 | DONE (`layer_ablation`) |
| 7 | eggNOG external baseline (Appendix B) | 2 | RE-RUN on sealed frame |
| 8 | **8-PLM x K grid (Exp 9 empty table)** | 1 | **NOT RUN - the decision** |
| 9 | GO-text BP micro-lever (honest, modest) | 4 | DONE (`gotext`) |

## The one open decision: the 8-PLM x K grid (Exp 9)

The empty `tab:exp9-multiplm-grid` (24 `n/a`) is a hard deposit blocker and the only
heavy new computation. Two paths:

- **A (populate)**: run the full family-vs-size matched-parameter matrix (8 PLMs x
  K), board-faithful `f_micro_w`, with the Wilcoxon/Holm significance protocol. A
  real multi-day run. Gives the "state of the art in representation" muscle and a
  headline table. Recommended if the thesis wants to *demonstrate* the backbone
  result, not just assert it.
- **B (reframe)**: cut the empty table; state only the validated framing (family >
  size; Ankh beats ESM2-3B) as a focused result + future work. Cheaper, honest,
  less ambitious.

Everything else in the plan is restate-with-existing-numbers, relocate, compress,
or write-the-missing-section - no new heavy compute. This decision gates the
timeline.

## Deposit blockers (fix before any deposit)
1. Empty 8-PLM grid (24 `n/a`) - populate or cut.
2. The `anc2vec_query +0.1449` claimed/retracted/re-asserted contradiction - one
   consistent LOFO story across ch6 + ch7.
3. Metric/frame/backbone chaos - one metric, one frame, one backbone as the spine.
4. Flagship result housed in the "historical" appendix - relocate to main Results.
5. `--` em-dashes throughout (project hook trips on any `--`) - sweep the prose.
6. Verify `tab:feature-importance` is defined (possible dangling `\cref`).
