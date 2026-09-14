# The Four Pillars of PROTEA

The thesis spine. This document exists to end the "lío experimental": the work
is not thirteen experiments in a list, it is **four load-bearing claims**, and
every experiment is evidence for one of them. Written 2026-07-08 as the skeleton
for the manuscript rewrite. Numbers are board-faithful (`f_micro_w`, OBO
2025-07-22, IA, TOI, prop=fill, norm=cafa, no_orphans, PK excludes PK_known)
unless marked otherwise.

## The one thesis

> Protein function is predictable from a **taxonomy of orthogonal evidence**,
> combined by a **calibrated fusion architecture**, measured on a **leakage-free
> temporal frame**. The resulting nine-cell benchmark is not nine numbers, it is
> a **map of which evidence wins in which regime**, and it has an **honest,
> evidence-bound frontier** that this thesis characterises rather than hides.

PROTEA is the reproducible, operationally auditable platform that makes every
step of that sentence live-verifiable.

---

## Pillar 1 — A taxonomy of functional evidence

A protein's function can be inferred from several **orthogonal** evidence
sources, each designed for a different failure mode. The 56/69-column feature
schema collapses into five classes plus one absent one:

| Class | Signal families | Rescues |
|---|---|---|
| **A. Homology / neighbourhood** | knn, knn_distance, knn_vote, alignment_nw/sw, length, taxonomy | a close annotated neighbour exists |
| **B. Learned representation** | emb_pca + the learned k-WTA encoder (d8979601) | the query's own function-aligned embedding |
| **C. Full-vocabulary classifier** | classifier_score (M2 hybrid) | **no neighbour** -> novel proteins (NK) |
| **D. Prior-knowledge / association** | self_prior, association_total/cross/present, anc2vec_query | **partly-characterised** proteins (PK) |
| **E. Domain (proto-structural)** | interpro | orthogonal signature -> GO |
| **F. [absent] Structure** | AFDB / FoldSeek 3Di | tested, does not help BP (Pillar 4) |

**Evidence:** the signal inventory (feature_schema.py) and the ablation that
proves each class is non-redundant (Pillar 3).

---

## Pillar 2 — A calibrated fusion architecture

The classes are combined, not concatenated, by a **stacked per-category
re-ranker** (ADR-D43): each signal becomes a calibrated EvidenceScorer, and a
shallow per-(category, aspect) combiner weights them. Candidate generation is
learned k-WTA retrieval; the classifier proposes across the whole vocabulary;
association adds the cross-aspect signal. Everything is trained and evaluated
under a **leakage-free rolling-origin temporal protocol** (ADR-D40): the frame
is selected on an earlier window, confirmed on a held-out split, and the sealed
measurement is never seen during model choice.

**Evidence:** the pipeline itself; the reproducibility result (native within
0.007 of the board); the collapse of gains under injected temporal leakage.

---

## Pillar 3 — The nine-cell grid is a map of regimes

The {NK, LK, PK} x {MF, BP, CC} grid is not nine arbitrary numbers. A
board-faithful **leave-one-family-out** ablation (retrain per cell, drop each
signal class, re-measure) shows a clean regime structure:

| Regime | Dominant evidence (LOFO delta) | Reading |
|---|---|---|
| **NK** (novel) | **classifier** +0.18..+0.25 | predict from the embedding directly |
| **LK** (little-known) | **classifier** +0.10..+0.16 | same engine, still dominant |
| **PK** (partly-known) | **association + anc2vec_query** +0.02..+0.03 | exploit prior knowledge |

Two results that reframe the field's intuition:
- **Homology proposes but does not discriminate.** knn is not in the top-2 of
  any cell; the discriminative work is done by the *learned* signals.
- **Each class is non-redundant in its regime**, which is exactly Pillar 1's
  claim, now proven by ablation.

**Evidence:** `lofo_9cell/result.json`.

---

## Pillar 4 — An honest, evidence-bound frontier

PROTEA is first in seven of the nine cells. The two it is not are **LK-BPO and
PK-BPO** (Biological Process, the harder proteins). This thesis characterises
that wall instead of overclaiming past it. Nearly every orthogonal lever is RED
for a *principled* reason, and the one that is not tells us what BP actually needs:

| Lever | Result on the BP wall |
|---|---|
| homology / sequence | 0.52 separability (fails on the hard cases) |
| literature gate / honest prior | RED (base-rate leak) |
| frequency prior | RED (evaporates out-of-sample) |
| cross-encoder / joint-GCN | NEGATIVE |
| GO-text label basis (BioBERT on GO definitions) | modest: seed-averaged LK-BPO +0.012, PK/NK ~0 |
| **structure (AFDB/FoldSeek 3Di, real)** | **RED** (residual 0.545; structure conserves MOLECULAR FUNCTION not BIOLOGICAL PROCESS: a clean positive control finds the true functional neighbour 66.6% of the time for MF vs 20.7% for BP) |
| **text-aligned representation (ProtST)** | **GREEN** (the first crack, see below) |

So the wall is **evidence-bound, not architecture-bound**: no amount of fusion
machinery crosses it, only *new evidence* does. `#1-in-7/9` is the ceiling on the
evidence the pipeline currently carries.

### The first crack: function-description-aligned representation

A board-faithful kNN GO-transfer confirm (2026-07-09) shows that **ProtST**, whose
protein encoder is contrastively aligned to Swiss-Prot *function descriptions*,
adds real signal exactly where the wall is. Isolated against the **same ESM-1b base**
(so the delta is the text alignment, not the backbone): **nk-BPO +0.062** (the
leakage-free anchor, those proteins had no function text at t0), **lk-BPO +0.072**
(the wall itself), pk-BPO +0.037. The lift **survives on the hard-homology tail**
(twilight, no-hit and remote neighbours: nk-BPO +0.053, lk-BPO +0.044), so it is
orthogonal to homology rather than a proxy for it.

**The lift is not a generic property of "text models".** A second text-aligned model
with a different base, **ProTrek** (ESM2, trimodal, structure-inclusive), does *not*
reproduce it: on BP it is flat to negative (lk-BPO -0.016) and clearly worse on MF,
while beating the champion on all three **CCO** cells (+0.05/+0.07/+0.04, also
surviving hard homology). Text alignment is therefore not monolithic: the *text
source* decides the signal. Function descriptions buy BP; broader trimodal alignment
buys localisation. The two are **complementary, not redundant** (equal-weight kNN
combine of ProtST + ProTrek + the champion reaches 0.2650 against 0.2213 for the
champion alone, +0.044 before any reranker).

**What this does and does not change.** It does not change the sealed `#1-in-7/9`:
the text signal is a validated *candidate lever*, not yet part of the measured
pipeline. It changes the *claim*: the frontier is evidence-bound, and this thesis
identifies the class of evidence that begins to cross it, namely a representation
supervised on descriptions of function rather than on sequence alone. Whether the
crack becomes a breach is answered on the regenerated frame, with the text signals
registered in the signal store, not by assertion here.

**One principled micro-advance** (2026-07-08): the classifier's *label
representation* is the frozen-2020 anc2vec (rudimentary DAG-ancestry). Replacing
it, per aspect, with **GO-text (BioBERT on the GO definition) for BP terms**
gives a **real but modest** classifier-level lift, **seed-averaged (5 seeds):
LK-BPO +0.012, PK-BPO ~0, NK-BPO ~0** (the single-seed reading of +0.024/+0.014
overstated it ~2x; anc2vec itself seed-averages well and closes most of the gap).
Principled because BP is a *process*, describable in text, which the ancestry
embedding and the functional-cooccurrence codes both miss (term-text sees BP
where structure and ancestry do not, the opposite face of the structural
result). It is **not a wall-breaker** and does not survive pipeline attenuation;
its lasting value is (a) it **defends the anc2vec choice with data** (the right
basis for MF/CC, and even seed-averaged the hard part of the field's ceiling
holds), and (b) it is a clean, honest characterisation of *where* a modern label
representation can and cannot help. The sparse functional codes were tested and
rejected as a label basis (worse than anc2vec).

**The two text results are the same physics, seen from both ends.** On the *label*
side, term-text sees BP where DAG ancestry does not (+0.012 on LK-BPO). On the
*protein* side, function-description alignment sees BP where sequence and structure
do not (+0.072 on LK-BPO). Biological process is a process: it is written down in
prose, it is not written in the fold, and it is only weakly written in the ontology's
ancestry. That is the mechanism behind the wall, and behind its first crack.

**Evidence:** `project_structural_gate_bp_wall_2026_07_07` (the wall),
`project_gotext_label_basis_bp_lever_2026_07_08` (label side),
`project_text_evidence_scorer_2026_07_08` (protein side; receipts in
`storage/text_scorer/*_result.json`, writeup `storage/text_scorer/WRITEUP.md`).

---

## Every experiment maps to a pillar (no orphans)

| Experiment | Pillar |
|---|---|
| 8-PLM backbone matrix; learned k-WTA encoder; compaction study | 1 (evidence sources) |
| meta-reranker (ADR-D43); leakage-free temporal (ADR-D40); reproducibility | 2 (fusion) |
| 9-cell LOFO; universal-vs-per-category; homology-only -> full | 3 (regime map) |
| structural GATE; literature/frequency/cross-encoder REDs; GO-text label basis | 4 (frontier) |
| serve<->offline reconciliation; /annotate cutover; platform/deploy modes | 2 (the platform that makes it live-verifiable) |

## The rewrite (chapter argument map)

- **Intro / methods** -> Pillars 1 + 2 (evidence taxonomy + fusion + temporal protocol).
- **Evaluation** -> Pillar 3 (the regime map is the result, not a table of nines).
- **Discussion / frontier** -> Pillar 4 (the honest wall + the GO-text advance).
- **Platform chapters** -> Pillar 2's operational face (the live-verifiable product).

## Open threads

1. ~~Seed-averaged confirmation of the GO-text BP lever~~ **DONE**: modest
   (LK-BPO +0.012 seed-averaged, classifier-level); NK/PK-BPO negligible.
2. ~~Pipeline propagation of the aspect-aware basis~~ **scoped out**: the
   classifier-level lever (+0.012 LK-BPO) is too small to survive re-ranker
   attenuation into a board-visible effect; not worth the full-dataset
   classifier-feature regeneration.
3. Fix the abstract's stale ablation claim ("anc2vec_query +0.1449", old schema)
   to the clean-frame reality (classifier dominates NK/LK, LOFO). **[thesis edit]**
4. Populate or reframe the empty 8-PLM grid table (deposit blocker). **[thesis edit]**
