# BP structural lever: results (2026-06-30, autonomous run)

Board-faithful throughout (cafa_eval OBO/IA/TOI, prop=fill, norm=cafa, no_orphans,
PK excludes PK_known; LAFA 227->230). Lab results/sparse_classifier/bp_structural_phase{0,1}/.
Nothing injected; board unchanged (PROTEA #1 in 7/9 cells). This is a rigorous NEGATIVE
with a clean diagnosis, valuable for thesis ch6.

## Diagnosis (where the gap is)
PROTEA loses only LK-BP (0.440 vs TransFew 0.512) and PK-BP (0.218 vs 0.294); we are #1
elsewhere including NK-BP (novel proteins, the hardest and most valuable). Board-faithful
PK-BP recall ceiling is 0.319 -> the loss is candidate-GENERATION-bound, on exactly the
proteins (LK/PK) rich in side-modalities that TransFew/FunBind exploit.

## Phase 0: union the two-tower clf candidates into the pool (generation)
Clean A/B (no-union base reproduces the champion exactly).
- PK-BP: ceiling rose +0.071 (reached the scorer) but Fmax REGRESSED 0.21631 -> 0.18971.
  Pure precision dilution: the reranker cannot value the new candidates.
- LK-BP: +0.013, but the ceiling stayed FLAT -> a feature effect, not generation.
Verdict: generation alone does NOT convert; the neck is scoring.

## Phase 1: learnable GCN GO-label encoder + joint (bi-encoder) scorer
DAG-aware label tower (init from fused sparse functional codes, message-passed over
go_parents), joint ProjHead x LabelGCN, ASL + DAG hinge, 3 seeds, in-frame per-cut.
- Standalone recall@100: GCN 0.690 vs our existing two-tower 0.718 (did NOT improve).
- Board-faithful PK-BP union+GCN = 0.19140 (+0.0017 over the naive union, still -0.025 vs
  champion, -0.103 vs TransFew). LK-BP 0.439 (flat).
Verdict: a bi-encoder (dot-product) joint scorer, even DAG-aware, does NOT convert PK-BP.

## Decisive diagnostic (why)
eval_standalone, AUROC of separating true vs false PK-BP candidates:
- On the clf-ADMITTED candidates (the ones that dilute precision): two-tower AUROC 0.523,
  GCN AUROC 0.536 -> both NEAR-RANDOM.
- On all in-vocab candidates: GCN AUROC 0.696 (moderate); the hard clf-only ones are at chance.

Conclusion: the wall is REPRESENTATION/EVIDENCE, not scoring architecture. The signal to
distinguish these deep BP terms on PK proteins is not in the sequence embeddings. Therefore
cross-attention (the originally-planned Phase 2) on the same representations would not convert
PK-BP either: it is a more expressive head over a representation that is already near-random
on these candidates.

## Recommendation (the plan, revised by evidence)
- DEPRIORITIZE Phase 2 cross-attention (evidence-against: candidates near-random-separable
  by current reps).
- The only lever that could inject the missing signal is ORTHOGONAL MULTIMODAL EVIDENCE
  (FunBind's approach): structure (FoldSeek 3Di) added to the text/InterPro arms we already
  have. This is a large new data+model effort with uncertain payoff and is a strategic call.
- Alternative: CONSOLIDATE. We are #1 in 7/9 including NK-BP; the 2 BP losses are now
  rigorously diagnosed as representation/evidence-bound. PK-BP 0.294 (TransFew's own best) is
  the field's hard wall. The diagnosis itself is a clean thesis contribution.

Strategic fork left for the author.
