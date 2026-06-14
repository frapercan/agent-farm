# LAFA-NUMBER-ONE — push for the #1 leaderboard position

## Target and honest framing

Current canonical: mean f_micro_w **0.324** (#4). Leaderboard #1 = TransFew **0.381**, #2 FunBind 0.366.
To reach #1 the mean must exceed 0.381. Matching the per-category BEST on the board
(NK 0.441 FunBind / LK 0.485 TransFew / PK 0.230 TransFew) yields 0.385 -> #1. So the target shape is
**NK +0.029, LK +0.091, PK +0.065**.

This is a stretch: it means out-engineering dedicated learned models (TransFew transfers via GO-term
embeddings; FunBind is multimodal) by ~18% relative on the mean. The dominant gap is **prior-knowledge
(LK, PK)**, and this session already showed that score-level fusion of a self-prior does NOT generalise
(maxblend + agreement both flat/negative on SELECT, [[project_selfprior_maxblend_refuted_2026_06_14]]).
The ONLY remaining path is a properly-trained **learned model** that exploits prior knowledge and
structure as features, not a blend. #1 is not guaranteed; the plan is to attempt it under the same
leakage-clean discipline and let SELECT decide, reverting any lever that does not generalise.

## Where each category's points must come from

- **LK (+0.091, biggest):** the protein's own t0 EXPERIMENTAL annotations in OTHER namespaces predict the
  target namespace via learned **cross-aspect GO association** (e.g. MFO "kinase activity" -> BPO
  "phosphorylation"). KNN transfers neighbour labels and can miss this intra-protein structure. This is
  TransFew's strength and is the one genuinely-untested signal. **Untested -> S1.**
- **PK (+0.065):** novel terms in a namespace the protein already knows. Needs the learned reranker with
  GO-DAG structure features (parent/child of known terms, IA, co-occurrence) + class-balanced loss for
  the sparse cells. **S4 (reranker).**
- **NK (+0.029):** homology ceiling. **Structure** (Foldseek/ProstT5 remote homologs) and a **multi-PLM
  ensemble** (8 PLMs already embedded) are the orthogonal levers. **S2 (multi-PLM), S3 (structure).**

## Execution order (each leakage-clean: fit SELECT 220->227, seal once on 7401, exact harness, beat-or-revert)

- **S1 (now): cross-aspect association for LK.** Build a co-occurrence/association model from the t0
  reference pool (P(target-term | source-term) across namespaces); score LK query proteins from their t0
  experimental source terms; test fusion with KNN on SELECT. If it generalises, it is the LK lever and a
  reranker feature; if not, LK is likely stuck and #1 is at risk -> report.
- **S2: multi-PLM ensemble.** Learned combination of the 8 per-PLM KNN score streams (we have the
  embeddings). Cheap; could lift all categories. (Note: a prior flat multi-PLM attempt did not help on
  the old frame; re-test as a LEARNED combination on the aligned frame.)
- **S3: structure modality for NK.** Foldseek over AlphaFold DB (or ProstT5 structure tokens) as a second
  KNN index -> features.
- **S4: assemble into a per-category learned reranker** over {KNN, cross-aspect, multi-PLM, structure,
  InterPro, GO-DAG/IA features}, proper training volume, per-protein rank_normalize calibration,
  focal/class-balanced loss for sparse PK-BPO. Seal once on 7401.

## Stop criterion

If S1+S2+S3 each fail to generalise on SELECT, #1 is unreachable with this method family; consolidate at
0.324 and record the negative result. Do not ship anything that does not beat composite on the sealed
7401 frame.
