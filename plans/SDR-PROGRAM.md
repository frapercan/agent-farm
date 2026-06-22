# SDR program: the dense<->sparse research track (T-CIENCIA)

Design + ready-to-launch plan for the sparse-representation research program
(sparse.pdf validated on PROTEA's k-NN GO-transfer benchmark). Lives under
`CONCEPT-MAP.md` section 2 and `ROADMAP-NEXT.md` (T-CIENCIA). Primitives ship in
`protea-reranker-lab` (`src/protea_reranker_lab/sdr.py`, PR #96 merged); the tracked
runner logs to MLflow `sdr-a-correlation`.

## 1. Where we are (2026-06-22)

- **SDR-A done, gate NEGATIVE but RE-OPENED by the operator steer.** Naive magnitude
  k-WTA + Tanimoto over the cached MEAN-POOLED ProtT5 vectors correlates with GO
  semantics WORSE than dense cosine over the same pooled vectors (Spearman vs Resnik:
  cosine 0.3153 vs Tanimoto 0.2551 at k=128).
- **The confound (operator + sparse.pdf section 2):** both arms started from the SAME
  mean-pooled vector. SDR-A did POOL-then-sparsify (binarise an already-smeared average).
  Mean pooling is the dense analogue of bundling, so binarising it is doubly lossy. The
  SDR-native route is SPARSIFY-then-BUNDLE (sparsify each residue, then bundle), which
  SDR-A never tested. So the negative is plausibly a POOLING artifact, not a verdict on
  the sparse idea. The gate is RE-OPENED until the fair-pooling test runs.

## 2. The fair re-test (the next decisive experiment)

Compare, on the SAME correlation harness (reuse `run_sdr_a_correlation` + `sdr.py`),
three representations of each protein against GO semantic similarity (Resnik/Lin):

1. **Dense baseline (fair):** richer pooling than naive mean (e.g. mean + max
   concat, or attention/CLS), cosine. Controls for "mean pooling smears".
2. **SDR-native (sparsify-then-bundle):** per-residue ProtT5 states -> k-WTA per
   residue -> bundle (thresholded superposition / OR with a density cap, length-
   normalised so active density does not saturate with sequence length, per sparse.pdf
   section 2 "must be length-normalised") -> protein SDR -> Tanimoto.
3. **SDR pool-then-sparsify (the SDR-A control):** the existing negative, for contrast.

Gate: does the SDR-native route close or beat the dense gap? If yes, the sparse idea
survives and we proceed to SDR-C; if it is still well below dense even with fair pooling
+ sparsify-then-bundle, the magnitude-sparsification family is genuinely weaker on this
benchmark and the value (if any) is only in the LEARNED arm (SDR-C). Either outcome is a
clean, publishable result.

## 3. SDR-C design (the learned arm, where sparse.pdf says the value lives)

A top-k sparse autoencoder (the mechanistic-interpretability SAE family) trained on the
cached ProtT5 embeddings (pooled and/or per-residue):

- **Architecture:** encoder `e -> z` with a top-k bottleneck (k active latents), decoder
  `z -> e_hat`. The active dictionary atoms of `z` are the SDR. Start small (dict size
  ~4-8k, k ~32-128) to avoid the v6 overfit trap.
- **Objective:** reconstruction L2 + an L1/top-k sparsity penalty. THEN the key lever
  (sparse.pdf 2 / A): add a CONTRASTIVE term so the code is steered toward FUNCTION, not
  reconstruction (positives = proteins sharing a low-level GO term at low sequence
  identity, the protein scaffold-hop; this strips reconstruction-only directions and
  realigns overlap with biology).
- **Readout:** same correlation harness (Tanimoto on the learned active set vs GO
  semantic), then, if it clears the gate, the full SDR-C k-NN arm on /benchmark via the
  `metric="tanimoto"` branch in `search_knn`, plugged in as an EvidenceScorer (ADR-D43).
- **Leakage discipline:** train the SAE on t0/SELECT data only; never t1.
- **Lives in:** `protea-reranker-lab` (a new `sdr_c` module + a `protea-runners` SAE
  training runner if it graduates), tracked in MLflow.

## 4. Embedding-recompute plan (READY to launch AFTER INT-8; NO GPU now)

The fair re-test (2) and SDR-C (3) need PER-RESIDUE ProtT5 embeddings, which the current
pipeline does not cache (it caches mean-pooled `(N, D)` only). Prerequisite + jobs,
ready to dispatch once INT-8 frees the GPU:

- **Code prerequisite (non-GPU, can be done now as a slice):** expose a per-residue /
  alt-pooling output from the embedding path. `EmbeddingBackend.embed_batch` already
  takes `pooling` ("mean"/"max"/"cls"); add a `pooling="none"` (per-residue `(N, L, D)`)
  or a `mean+max` concat mode, and a cache key that distinguishes it from the mean-pooled
  cache. This is a contracts + protea-backends + protea-method change (a normal slice),
  NOT a GPU run.
- **Embedding job (GPU, AFTER INT-8):** dispatch `compute_embeddings` via `POST /jobs`
  for the SELECT-window reference pool with ProtT5 and the new pooling, writing a new
  `EmbeddingConfig` + `SequenceEmbedding` rows. Parameters: ProtT5
  (`embedding_config` per the new pooling), SELECT pool, per-residue or mean+max. This is
  the heavy step; gate it behind INT-8 to avoid GPU contention.
- **Then:** run the fair re-test (2) on the new embeddings; if positive, train SDR-C (3).

## 5. Sequencing (gated, no GPU until INT-8 clears)

1. NOW (non-GPU): the code prerequisite (expose per-residue / richer pooling) can be a
   normal slice; the fair-re-test runner extension (sparsify-then-bundle) can be written
   against the existing `sdr.py` primitives.
2. AFTER INT-8 (GPU freed): dispatch the embedding recompute, then the fair re-test.
3. If the fair re-test clears the gate: train SDR-C (learned arm); else record the
   magnitude-sparsification ceiling and pivot to SDR-C directly (the learned arm is the
   real hypothesis either way).
4. Per decision D-B: nothing enters the thesis until a VALIDATED signal.

## Provenance
sparse.pdf section 2 (the ordering decision: pool-then-sparsify vs sparsify-then-bundle;
length-normalisation), Appendix A (PROTEA validation arm), Appendix B (k-WTA+Tanimoto).
Operator steer 2026-06-22 (the SDR-A negative may be a pooling artifact). See memory
`project_sdr_a_result_2026_06_22`.
