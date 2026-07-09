# Text-aligned EvidenceScorer de-risk (ProtST / ProTrek)

Evaluate whether a text-supervised protein representation adds orthogonal signal
for GO transfer -- primarily on the BP wall (LK-BPO / PK-BPO) -- as a text->GO
EvidenceScorer in the meta-reranker (ADR-D43), NOT as a primary kNN index.
Written 2026-07-08. Base: `main` (agent-farm). Companion: `../thesis-pillars`,
`../thesis-clean-iteration`, and the layer-ablation representation-science result.

## Candidates (post-gate)

| Model | License | Base / size | Leakage | Verdict |
|---|---|---|---|---|
| **ProtST-ESM2** | Apache-2.0 | ESM-2 (650M) + PubMedBERT text (ProtDescribe = Swiss-Prot function text) | Cleared by dates (ICML 2023 << t0=v227 2025-09); NK fully clean (no function text existed) | **IN** |
| **ProTrek-650M** | MIT | 650M seq + 150M struct + 130M text, trimodal contrastive | Cleared by dates (2024-25 << t0); NK clean | **IN** |
| PoET-2 (182M) | Non-commercial | retrieval/in-context | (clean) but non-commercial + not-an-embedding + fitness-not-GO | **OUT** (future research) |

## Leakage position (the corrected argument)

Test answers = GO gained in the sealed window t0=v227 (2025-09) -> t1=v230 (2026-03).
Both models were **published/trained before v227**, so the window annotations did
not exist at training -> **test-answer leakage is impossible**. NK proteins had **no
function text at t0** -> fully clean, zero asymmetry (the strongest, primary result
cell). For LK/PK the model may have seen the *t0* function text: a legitimate prior
available to any method, NOT test-answer leakage. Framing note: ProtST/ProTrek are
**supervised-on-function** representations vs ESM-C (self-supervised MLM); measuring
that difference is the point, not a confound.

## Method (de-risk first; do NOT skip the proxy)

Reuse the layer-ablation substrate: 7401 LAFA queries + 15k t0 reference (sequences
+ GO already assembled in `storage/layer_ablation/`). Apply the **representation-
learning principle** validated at +61%: never compare RAW -- the fair test is a
**learned functional head on each** representation.

1. **License/size gate** -- DONE (above).
2. **Extract embeddings** for the substrate: ProtST-ESM2 (protein_feature) and
   ProTrek-650M (get_protein_repr), plus ProTrek text encoder for GO-term text.
   float32 storage. Instrumented (MLflow run / tracked op), not ad-hoc.
3. **Proxy de-risk (cheap, decisive) = ORTHOGONALITY, not just quality.** On the
   functional-gold proxy (Spearman + top-k purity), ask: does the text-supervised
   representation add signal **over the champion we already have** (d8979601 learned
   k-WTA / ESM-C + classifier)? Residualize against the existing signal. If
   redundant -> stop before board-faithful (the test that killed the literature
   lever). **Start with the NK-clean subset** (zero leakage).
4. **Learned head** (if proxy GREEN): train a k-WTA/functional head on ProtST /
   ProTrek toward GO (t0-clean; for ProtST/ProTrek evaluate on data held out of
   their training), head-to-head vs learned-head-on-ESM-C. This couples the
   representation-learning principle with the leakage control.
5. **Board-faithful confirm** (only if proxy+head GREEN): kNN GO-transfer
   f_micro_w, 9-cell, vs the current baseline, as an EvidenceScorer arm.

## Discipline (non-negotiable)
- Stratify EVERY metric by the 3 axes: length (short<=318/med/long 970-1959),
  category (NK/LK/PK x aspect), neighbour-identity (high>=50/mod/twilight 20-30/
  remote<20, needs MMseqs2 vs the reference). CIs on deltas; never drop an axis.
- MLflow / tracked op; no ad-hoc scripts in storage or /tmp for the final receipt.
- numpy/FAISS for kNN, never pgvector, never torch-GPU-KNN on 12GB.
- Only VALIDATED numbers enter thesis/docs.

## Success criterion
A clear verdict with a reproducible receipt (result.json + MLflow run): does a
text->GO EvidenceScorer move LK-BPO / PK-BPO above noise (with CIs), stratified by
the 3 axes, on the board-faithful frame -- with the NK-clean cell as the leakage-
free anchor. If it moves: propose meta-reranker integration. If not: close as a
documented negative and the BP wall stays evidence-bound. Expectation calibrated
MODEST (prior: GO-text label-basis was modest LK-BPO-only; literature lever RED).
