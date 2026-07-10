# SDR lever validation: the cheap-decisive ladder (T-CIENCIA)

Plan to validate whether the sparse-representation concepts yield a USEFUL LEVER, by a
ladder of cheap-and-decisive experiments where each rung is only run if the previous shows
signal. Derived from the 2026-06-23 decomposition result. Tracked in MLflow; scripts in
`protea-reranker-lab`. Leakage-clean (t0/v227 train, 227-230 eval). Only validated numbers
enter the thesis (decision D-B). See [[project_sdr_a_result_2026_06_22]],
`agent-farm/plans/SDR-PROGRAM.md`.

## Where we are (the findings that motivate this)

The dense-vs-sparse decomposition (ankh-base, v227, 5k proteins / 200k pairs) isolated the
three confounded variables and found:
- **Sparsifying is nearly free** (keep top-128 of 768 real-valued dims, cosine: -0.011 vs dense).
- **Binarising is the killer** (throw away the magnitudes: -0.13, 5-10x more costly).
- So a **real-valued sparse code ~= dense**; the whole gap was the magnitude loss.

This splits the question into TWO candidate levers with very different priors:
1. **EFFICIENCY lever** (likely): a sparse-real code matches dense accuracy at a fraction of the
   storage/compute. The data already supports it intrinsically; needs extrinsic (task) confirmation.
2. **PRECISION lever** (uncertain): a LEARNED binary code that recovers the -0.13 binarisation loss
   by encoding function in the bit pattern. Requires learning; gate it behind a cheap shallow test.

## Principle

Each rung is cheap and decisive, with a pre-declared decision rule. Ascend only on signal.
Never run the expensive learned model (SAE) blind. A clean negative at any rung is a publishable
result, not a failure.

## The ladder

| Rung | What | Cost | Decides | Gate to ascend |
|---|---|---|---|---|
| 0 | Intrinsic decomposition | DONE | sparsity free, binarisation kills | (done) |
| **1** | **sparse-REAL k-NN GO-transfer on the task (f_micro_w)** | low | is there an EFFICIENCY lever? | always run next |
| 2 | shallow LEARNED binary code, intrinsic correlation | low | does a learned binary recover function? | only if precision wanted |
| 3 | SDR-C deep top-k SAE + contrastive | high | the real precision arm | only if Rung 2 signals |

## Rung 1 (RUN NOW): the efficiency lever, on the real task

**Question:** does a sparse-REAL representation (top-k coords + magnitudes) transfer GO terms by
k-NN as well as the dense one, at much lower index cost?

**Harness (offline, in the lab; numpy + cafaeval, no production code change):**
- Reference pool: v227 t0 proteins with an ankh embedding AND >=1 GO annotation (annotation set
  `c905dffa`). Per-protein dense vector = mean of chunk vectors (config `6542db1e`).
- Queries: the 227-230 frame proteins (LAFA targets, query set `acc27f47`), held out from the pool.
- Retrieval: for each query, top `K_nn` neighbours (K_nn=30, PROTEA default) by similarity; transfer
  neighbours' propagated GO terms, score per term = sum of neighbour similarities (the KNN-transfer
  vote). Threshold sweep -> predictions.
- Metric: **f_micro_w** via the in-lab cafaeval, against the 227-230 ground truth (`34a634a8` / v230).
  This is a KNN-ONLY transfer (no reranker), so the absolute number is below the 0.3745 headline; the
  comparison is RELATIVE: dense-KNN vs sparse-real-KNN on the SAME harness.
- Arms: **dense** (full 768, cosine) vs **sparse-real** (top-`k_sdr` masked, cosine), `k_sdr` in
  {32, 64, 128, 256}. Report f_micro_w per arm + the index-size ratio (k_sdr/768) and the Tanimoto/
  sparse-dot latency.

**Decision rule:**
- If sparse-real f_micro_w is within noise of dense at a small k_sdr (e.g. 64-128) ->
  **EFFICIENCY LEVER CONFIRMED**: a smaller/faster k-NN index at the same accuracy. Worth shipping
  (sparse-real `SequenceEmbedding` variant + a sparse-dot search backend, numpy/FAISS, NEVER pgvector).
- If sparse-real already loses on the task -> the intrinsic "sparsity is free" does not transfer to
  retrieval; record it and stop the efficiency line.

**Deliverable:** lab script `scripts/run_knn_transfer_sparse.py`, MLflow experiment
`sdr-knn-transfer`, a table (arm x k_sdr -> f_micro_w + index ratio), a decision.

## Rung 2 (only if a PRECISION lever is wanted): shallow learned binary code

Test whether a learned binary code recovers the magnitude loss, BEFORE the expensive SAE.
- A linear map `768 -> D` + top-k binarise, trained by a contrastive loss on GO pairs (positives =
  proteins sharing a specific/low-IC GO term at LOW sequence identity, the scaffold-hop; negatives =
  random), t0/v227 only.
- Readout: the SAME intrinsic Spearman harness (Tanimoto on the learned bits vs Resnik/Lin), compared
  to the magnitude-binary baseline (~0.093) and dense (~0.23).
- Decision: if it closes a substantial part of the -0.13 -> the precision lever exists, build Rung 3.
  If it barely moves -> a learned linear binary cannot recover the magnitude; close the binary line
  (a real-valued sparse or a deeper nonlinear code is the only option).

## Rung 3 (only if Rung 2 signals): SDR-C deep top-k SAE

The full learned arm: a top-k sparse autoencoder (dict ~4-8k, k ~32-128), reconstruction + sparsity
+ the contrastive function objective. Readout = intrinsic correlation, then the full k-NN term-transfer
on /benchmark (the `metric="tanimoto"` branch + an EvidenceScorer, ADR-D43). Heavy; tracked; t0-only.

## Discipline

- Cheap before expensive; pre-declared decision rule per rung; close cleanly on a negative.
- Leakage-clean: t0/v227 for training/reference, 227-230 for eval. Never t1 in training.
- MLflow-tracked, lab scripts (not /tmp), numpy/FAISS for any k-NN (NEVER pgvector).
- Per D-B: nothing enters the thesis until a VALIDATED signal; but every rung is a clean, reportable
  result (the efficiency win, or the precise size of the learned recovery, or a clean negative).

## First action
Build the Rung-1 offline k-NN GO-transfer harness and report dense vs sparse-real f_micro_w.
