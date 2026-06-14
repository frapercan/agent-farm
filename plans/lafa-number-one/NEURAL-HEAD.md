# NEURAL-HEAD — end-to-end full-label classifier toward LAFA #1

The retrieval+reranker family caps at ~0.330 sealed ([[project_learned_rescorer_lever_2026_06_14]]).
#1 (TransFew 0.381 f_micro_w) needs a different model class: an end-to-end LEARNED full-label GO
classifier. The `protea-neural-head` scaffold exists but DRIFTED to a per-pair reranker over KNN
candidates (inherits the ~0.53 recall ceiling; its "0.119" was a coarse non-IA grid, a measurement
artifact). The right design already exists at
`protea-neural-head/design/full_go_classifier_plan_2026_06_09.md`. This plan executes it under the
project's leakage-clean / sealed-on-7401 discipline.

## Target and realistic ceiling

Beat 0.330 and contest TransFew/FunBind (0.366-0.381). Explore estimate: a properly built full-label
classifier reaches ~0.35-0.42 f_micro_w IF label semantics + data scale + IA-aligned loss are done;
architecture-alone plateaus ~0.30-0.35. #1 is plausible but not assured.

## Milestones (each: train on t0 <= cutoff, validate SELECT 220->227, SEAL once on the 7401 frame, exact harness)

- **M0 GO/NO-GO (now): minimal full-label classifier.** A 1-2 layer MLP on our existing per-protein
  pooled PLM embedding (Ankh-base 768-d, already in `sequence_embedding`), multi-label over the t0
  experimental GO vocab (restricted to the benchmark terms-of-interest), IA-weighted BCE, propagated t0
  labels. Train on the v227 t0 pool, predict the 7401 targets, score with the exact harness. DECISION:
  if a bare full-label MLP already reaches ~0.33-0.36 it validates the class and justifies the full
  build; if it is far below (<0.25) the data/representation gap is too large and we stop. This removes
  the reranker recall ceiling (the scaffold's core defect) at minimal cost.
- **M1 IA-aligned + per-aspect.** ASL or IA-weighted BCE; separate heads/models per aspect (BP ~21k /
  CC ~3k / MF ~7k terms). Frequency-grouped heads (TransFew recipe) for rare terms.
- **M2 label semantics.** GO-definition text (BioBERT) + a GCN over the GO-DAG as label encoder; enables
  rare/zero-shot terms. anc2vec already gives a 200-d ancestor encoding as a cheaper first proxy.
- **M3 backbone + scale.** ESMC-600M / ESM2-650M; train on the full annotated proteome (500k+) with
  IEA weak-label pretraining, strict <=t0 cutoff.
- **M4 ensemble.** Fuse the classifier with the KNN composite + the 0.330 re-scorer (the classifier and
  retrieval are complementary: classifier removes the recall ceiling, retrieval anchors high-homology
  hits) via the learned re-scorer, sealed.

## M0 OUTCOME (2026-06-14)

Built the minimal full-label MLP (768 Ankh-base pooled -> 1024 -> 1024 -> 29461 TOI terms, IA-weighted
BCE, 88k v227-t0 proteins, propagated labels, 25 ep GPU). Sealed on the 7401 frame (exact harness):
**NK 0.324 / LK 0.301 / PK 0.134 / mean 0.253** -- BELOW the KNN composite (0.324) and the 0.330
re-scorer. Optimistic max-union with the KNN HURTS at every alpha (0.21-0.26 vs 0.324): the classifier
is **anti-complementary** in this minimal form. See [[project_neural_head_m0_2026_06_14]].

A minimal MLP underperforming a tuned KNN is expected (TransFew/FunBind are tuned classifiers at
0.38/0.37), but M0 gives NO early positive signal that the build is on track. Reaching competitive
(~0.35-0.42) requires the full multi-week M1-M4 effort with uncertain payoff. DECISION PENDING: commit
to the full build vs consolidate at 0.330/0.324. Do not proceed to M1 without an explicit decision.

## Discipline

Evaluate ONLY through cafaeval with the exact published harness (`-toi -known(exclude) -no_orphans`,
Sep_2025 OBO, LAFA IA) on the 7401 frame, never the scaffold's internal coarse grid. Strict temporal
cutoff (labels <= t0). Validate on SELECT, seal once on 7401, beat-or-revert at every milestone. Stop
if M0 is far below 0.25 or if no milestone beats 0.330 sealed.
