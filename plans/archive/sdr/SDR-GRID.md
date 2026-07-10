# SDR experimental grid: the full hypothesis space (T-CIENCIA)

A systematic grid covering every hypothesis in sparse.pdf, with explicit emphasis on the
NO-mean-pooling axis (per-chunk / per-residue) and the ordering question
(sparsify-then-bundle vs pool-then-sparsify). Supersedes the ad-hoc sequence; organises what
is done, what is runnable now, and what needs a per-residue embedding recompute. Intrinsic
Spearman vs GO-semantic (Resnik/Lin), v227 t0 leakage-clean, held-out for learned arms.
See [[project_sdr_a_result_2026_06_22]], `SDR-LEVER-VALIDATION.md`, `SDR-PROGRAM.md`.

## Hypotheses

- **H1 (sparsity is free):** a sparse REAL code (top-k + magnitudes) ~= dense. CONFIRMED (-0.01).
- **H2 (binarisation is the cost):** dropping magnitudes costs ~-0.13. CONFIRMED.
- **H3 (ordering):** sparsify-then-bundle > pool-then-sparsify. NAIVE: FALSE (both fail, identical).
  LEARNED: UNTESTED.
- **H4 (learned alignment):** a function-aligned binary code recovers/beats dense. CONFIRMED at the
  whole-protein-mean level (SDR-C learned-binary 0.34 > dense 0.22, held-out).
- **H5 (no collapse helps long/multi-domain proteins):** keeping per-chunk/per-residue units (not
  averaging) preserves multi-domain structure; a sparse code can fire multiple function-bits.
  UNTESTED.
- **H6 (the combination):** learned x no-collapse (per-chunk/residue, bundled) is the sparse-native
  ideal. UNTESTED -- the frontier.
- **H7 (intrinsic -> task):** intrinsic GO-correlation gains transfer to k-NN term-transfer f_micro.
  Partly tested (sparse-real Rung 1 efficiency); learned arms UNTESTED on the task.

## The factors

- **A. granularity / ordering** (the no-pooling axis):
  - A0 whole-protein MEAN  (pool-then-sparsify; one vector, the collapse).
  - A1 per-CHUNK, sparsify-then-bundle  (config `6542db1e`, one vector per chunk -- AVAILABLE NOW).
  - A2 per-RESIDUE, sparsify-then-bundle  (no pooling at all -- needs a per-residue embedding recompute).
- **B. method:** B0 naive magnitude k-WTA  /  B1 LEARNED (contrastive encoder, soft-Tanimoto).
- **C. code type:** C0 real-valued (cosine)  /  C1 binary (Tanimoto).
- **D. k (sparsity):** {32, 64, 128, 256}.
- **E. readout:** E0 intrinsic Spearman (Resnik+Lin)  /  E1 extrinsic k-NN f_micro  /
  E2 size-STRATIFIED (1-chunk vs multi-chunk) -- answers H5 directly.

## The core grid (granularity x method x type), intrinsic Resnik

| granularity \ method-type | naive real | naive binary | learned real | learned binary |
|---|---|---|---|---|
| **A0 whole-mean** (pool-then-X) | done ~0.22 (=dense) | done 0.09 (fail) | done 0.60 | **done 0.34 (WIN)** |
| **A1 per-chunk** (sparsify-then-bundle) | ~0.13 (fail) | done 0.13 (fail) | **TODO** | **TODO <- frontier (H6, runnable now)** |
| **A2 per-residue** (no pool) | TODO* | TODO* | TODO* | TODO* (the ultimate, *needs per-residue embed) |

Plus the sweeps: D (k) on every live cell; E0 always; E1+E2 on the winners.

## The ordering experiment, made explicit (H3)

The "sparsify-then-bundle vs pool-then-sparsify" question is the A-axis. To answer it cleanly for
BOTH methods on the SAME units:
- NAIVE: A0-naive (pool-then-sparsify) vs A1-naive (sparsify-then-bundle). DONE -> identical, both fail.
- LEARNED: A0-learned (pool-then-sparsify = the current SDR-C) vs A1-learned (sparsify-then-bundle =
  encode each chunk, learned top-k, bundle, train contrastive on the bundle). UNTESTED -> THIS is the
  decisive ordering test, and the one the user wants. If A1-learned > A0-learned, the no-pooling /
  sparsify-then-bundle ordering finally pays off WHEN combined with learning.

## Phases (cheap -> expensive; gate on signal)

### Phase 1 (RUNNABLE NOW, per-chunk + whole-mean): close the learned x granularity grid
1. **A1-learned-binary** (the frontier cell): a per-chunk learned encoder -> top-k -> bundle ->
   contrastive soft-Tanimoto on the bundled code. Held-out vs dense (0.22) and vs A0-learned (0.34).
2. **A1-learned-real** (control for C): same, real-valued bundle, cosine.
3. **k-sweep D** on the live learned cells {32,64,128,256}.
4. **E2 size-stratified readout** on A0-learned AND A1-learned: split held-out by chunk count
   (1 vs >=2), report the SDR-vs-dense advantage per stratum. DIRECTLY answers H5 (do large/multi-
   domain proteins benefit more, and does per-chunk help them specifically?).
5. **E1 extrinsic** on the best learned cell: k-NN GO-transfer f_micro vs dense (Rung-1 harness).

### Phase 2 (needs a prerequisite): per-residue, the true no-pooling
- **Prerequisite (GPU + code):** a per-residue embedding output (`pooling="none"` in protea-backends
  / a new EmbeddingConfig) so each residue has a vector; OR reuse the per-chunk as the finest unit we
  have. The per-residue recompute is the heavy step (a `compute_embeddings` job with per-residue
  output for the v227 pool).
- Then A2 cells: naive (sparsify-each-residue-then-bundle, the literal sparse.pdf section 2) and
  learned (the ultimate sparse-native code). E0/E1/E2.

### Phase 3 (only if a learned arm clears): productisation
- The `metric="tanimoto"` k-NN arm + an EvidenceScorer (ADR-D43), best learned sparse code, on
  /benchmark. Numpy/FAISS, NEVER pgvector. Only on a validated, generalising signal (D-B).

## Discipline
Intrinsic (cheap) filters every cell; extrinsic (task) + size-stratified confirm the winners.
Held-out eval for all learned arms (train/eval protein split) to separate generalisation from fit;
log the eval curve (early-stopping on generalisation, not train loss). MLflow-tracked, lab scripts,
leakage-clean (t0 train, 227-230 eval where extrinsic). Each cell = a number + a decision.

## First action
Phase 1.1 + 1.4: the per-chunk LEARNED bundle (A1-learned-binary) with a size-stratified readout,
held-out, vs the current SDR-C (A0-learned) -- the decisive sparsify-then-bundle-WHEN-LEARNED test.
