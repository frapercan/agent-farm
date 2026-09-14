# representation-science

Length & representation-geometry research tracks (sparse.pdf science arm), born from the
2026-06-25 session. UNIFYING THEME (user): **how we handle protein length** can be a project
differentiator and a source of strong case studies; preserving local+global information for
giant/multidomain proteins via SDRs would be high-impact.

## Honest framing (do not repeat the deviation)
- These are **science / differentiator / case-study** contributions, NOT aggregate-score levers.
  Giants are ~1% of the corpus; the SDR/length work will NOT move the headline f_micro_w much.
  Sell it as method-novelty + provable failure of the SOTA on a regime, not as "+score".
- The **score spine stays separate and primary**: the validated learned-mean encoder, magnitude
  re-established on the clean frame = R1.1 benchmark (loop roadmap-from-zero). Do not let these
  tracks delay R1.1.
- Everything is **gated by cheap correlation proxies BEFORE any GPU/training**, and enters the
  thesis **only with validated signal** (the SDR-A negative is the cautionary precedent).

## Data context (verified 2026-06-25, see memory project_embedding_truncation_limits_2026_06_25)
- Cached PLM embeddings are `pooling=mean` and TRUNCATE per-config: ESM2 @1024 (4.4% of proteins),
  Ankh/ProtT5 mean @2048 (~1%), chunk ankh `6542db1e` @4096, per-residue npy sample maxL 1959.
- Length dist (527,858 seqs): mean 399, p50 318, p90 736, p95 969, p99 1831, max 35,991.
- Clean substrate comparisons MUST restrict to <=2048 (coverage-matched); >2048 giants are an
  untested regime needing full-length re-extraction.
- Existing assets to REUSE (no regen): mean `08234f06`, chunk `6542db1e`, per-residue
  `storage/fullgo_models/per_residue_v227/*.npy`, learned `d8979601`, frozen v227 bundle, and the
  lab correlation harnesses (`run_sdr_*`, `src/protea_reranker_lab/sdr.py`).

## RESULTS / STATE (2026-06-25 session) — see memory project_validation_findings_2026_06_25
- **Learned encoder VALIDATED on the real f_micro_w frame** (LAFA FINAL_227_230): learned-mean
  (`d8979601`) KNN-only BEATS the champion (mean+reranker) in NK/LK by +0.05..+0.13 (NK MFO 0.507 vs
  0.398). The +40% lever is real on f_micro_w, not just proxy. **PK = the wall** (no arm helps).
- **Proxy factorial (RS.0): chunk·learned > learned-mean**, gap grows with length (+0.178 Resnik long);
  residue·learned ~= chunk·learned. The strongest hypothesis = learned attention-pool over CHUNKS
  (off mean). Real-frame f_micro_w for chunk·learned is the active gate (RS.4 / experiment A).
- **Backbone settled** (project_backbone_choice): dev substrate = ankh-base; small ESM2 ruled out;
  family>size. No re-embedding needed for the optimal direction (chunk corpus `6542db1e` cached).
- **Reranker trio is STALE** (schema 7fcecf26 vs live b2a5cd46/73-feat) -> ~no-op; its contribution to
  the champion was minimal -> see RS.6.
- **cafaeval NK/LK dense-kernel bug** (sparse 250-10000x faster, identical Fmax) -> fix in flight,
  RS.7; cuts eval ~23min->~2min.

## A (keystone real-frame validation) RESULTS — 2026-06-25, MLflow exp 30
- The R0.1 frame did NOT exist (all 14 eval sets were orphans, wrong OBO). A BUILT it: eval_set
  `6e41eb5b`, job `81e71903`, pivot 2025-07-22, delta 7575. THIS is the canonical clean frame now.
- Champion mean-learned beats dense NK/LK (Δ NK +0.08/+0.06/+0.14, LK +0.13/+0.09/+0.12), tie PK -> win
  CONFIRMED on the real reproducible frame.
- **Reranker INERT here: reranked == raw-knn BIT-IDENTICAL** (both arms). Advantage is 100% the learned
  retrieval code -> RS.6 (retrain) is essential, not optional.
- **Length axis: FLAT, not growing** (mean-learned). The proxy's length-GROWTH was for chunk-learned
  (still untested -> RS.4c).
- **Identity axis (strategic, partly NEGATIVE): frame CANNOT probe twilight** (re-annotation of
  homologs; 0 remote). Champion advantage lives in HIGH identity, vanishes/reverses in twilight.
  -> the "beat homology where it fails" differentiator is UNCONFIRMED and needs a NEW low-identity
  holdout frame (RS.8, pending user decision).
- **chunk-learned RESOLVED (RS.4c done) + TESTED (RS.4b done), MLflow exp 31:** plumbing built
  (attention-pool op #688 + codes config `f4df03fe`); on the real frame **chunk-learned TIES
  mean-learned** (4/9 cells each, |Δ|<=0.008, NO significant NK/LK win). The proxy's +0.18 did NOT
  translate; length-growth IS directionally confirmed (sig LK/MFO P=0.991). DECISION: do NOT lock
  chunk-learned; mean-learned stays champion; chunk-learned is at most a length-conditioned arm for
  LONG proteins. CHAMPION number = **0.4937** (the 0.5074 was stale). Lesson: the GO-corr proxy
  OVERSELLS -> proxy-gated encoder refinements (RS.1->RS.3) are now LOW-confidence.
- **NEXT LEVER (recommended): RS.6** — retrain the INERT reranker over the learned-encoder candidates
  on the current 73-feat schema (real, non-proxy score lever; reranker proven inert on the clean
  frame). RS.8 (low-identity frame for twilight) and RS.3 (aspect) await user steer.
- cafaeval propagation FIX is permanent: cafaeval main `80d705a` (#21) + PROTEA poetry.lock bump
  (#689 merged) -> redeploys pull the correct cafaeval automatically.

### RS.0 — Factorial substrate x aggregation proxy (truncation-clean)

```yaml
id: RS.0
phase: RS
loop: representation-science
status: done
deps: []
acceptance: |-
  Factorial {substrate: mean,chunk,residue} x {aggregation: naive-bundle, learned-attention-pool}
  + dense baseline, ankh-base, RESTRICTED to sequences <=2048 (coverage-matched), Spearman vs
  GO-Resnik AND GO-Lin per length bucket (short<=318 / medium 319-969 / long 970-1959); very-long
  dropped (untestable). Isolates: (a) does chunking help vs mean at matched aggregation, (b) does
  learned aggregation beat naive at matched substrate, (c) does any substrate+learned beat the
  champion learned-mean, and where. Logged to MLflow sdr-factorial-substrate-agg.
estimated_hours: 4
priority: P1
tags: [sdr, proxy, aggregation, chunking, gate]
```

The cheap triage. Currently RUNNING (bioinfo-quick). Its result gates RS.3 and RS.4.

### RS.1 — Aspect + length stratification of the proxy

```yaml
id: RS.1
phase: RS
loop: representation-science
status: pending
deps: [RS.0]
acceptance: |-
  Extend the same correlation harness to stratify ALSO by GO aspect (MFO/BPO/CCO), within-aspect
  Resnik/Lin (Resnik is within-aspect already). Report Spearman per (aspect x length bucket) for
  the champion learned-mean code vs an aspect-conditioned variant. GATE question: does the code's
  GO-correlation differ materially by aspect (expect worse on BPO), and would an aspect-specific
  code correlate better WITHIN its aspect than the shared one? Cheap, mostly GPU-free.
estimated_hours: 3
priority: P1
tags: [sdr, proxy, aspect, gate]
```

Decides whether aspect-segregated encoding (RS.3) is warranted, and in which aspect it pays.

### RS.2 — Length-aware classifier (length + coverage feature, retrain head)

```yaml
id: RS.2
phase: RS
loop: representation-science
status: pending
deps: []
acceptance: |-
  The FullVocabClassifier (protea/core/classifier_producer.py) is blind to sequence length: its
  input is the standardized concat of MEAN PLM embeddings only (mean-pool already removed length),
  so on long/truncated proteins it is doubly blind (degraded truncated input + no length signal).
  Append `length` and a truncation/coverage feature (coverage_fraction = min(len, max_length)/len,
  or is_truncated) to the classifier input and retrain ONLY the head; rest of pipeline unchanged.
  Acceptance: per-length-bucket ablation (new vs current) on the clean frame shows the length-aware
  head does not regress overall AND improves (or honestly calibrates) the long-protein bucket;
  report classifier_score quality by length. PROTEA repo (classifier lives there); reranker already
  has length_query/length_ref so this closes the classifier-arm gap specifically.
estimated_hours: 8
priority: P1
tags: [classifier, length, truncation, calibration]
```

Concrete near-term honest fix; independent of the SDR proxies. Connects the length-differentiator
theme to the actual score pipeline (the classifier arm).

### RS.3 — Aspect-segregated sparse encoder (shared trunk + per-aspect heads)

```yaml
id: RS.3
phase: RS
loop: representation-science
status: pending
deps: [RS.1]
acceptance: |-
  GATED on RS.1 showing aspect-specific encoding helps. Build a shared PLM trunk + per-aspect
  sparse k-WTA heads (NOT three independent encoders: that splits data and loses positive transfer),
  trained with per-aspect contrastive (code-sim ~ within-aspect Resnik), with asymmetric capacity
  (larger code for BPO ~30k terms, smaller for CCO). Ablate per-aspect retrieval codes vs the shared
  champion code, within-aspect, on the clean frame. Ship a per-aspect code only where its ablation
  is positive. reranker-lab; composes with the aspect-conditioned reranker (F-RERANK-UNIVERSAL).
estimated_hours: 20
priority: P2
tags: [sdr, aspect, encoder, contrastive]
```

### RS.4 — Giant/multidomain SDR + late-interaction (the differentiator)

```yaml
id: RS.4
phase: RS
loop: representation-science
status: pending
deps: [RS.0]
acceptance: |-
  GATED on RS.0's aggregation winner. For giant/multidomain proteins (>2048, ~1%): full-length,
  NO-truncation per-residue embedding (chunked, transient) -> multi-resolution SDR (residue ->
  window/domain union+topk -> protein union+topk; length-invariant via union, capacity-graceful) +
  multi-vector late-interaction retrieval (ColBERT-style over domain SDRs). VALIDATE per-domain
  function recovery against InterPro/Pfam domain->GO ground truth (already available as interpro_*
  features): does domain-SDR localize the right function to the right domain, and does the protein
  union recover GO functions that mean-pool/truncation provably miss? CASE STUDIES: titin,
  dystrophin, mucins, multidomain enzymes, fusion proteins. Framed as science/differentiator (NOT
  aggregate-score); enters thesis only on validated per-domain recovery signal.
estimated_hours: 28
priority: P2
tags: [sdr, giants, multidomain, late-interaction, differentiator, case-study, thesis]
```

### RS.4b — chunk-learned real-frame validation (the active gate, experiment A)

```yaml
id: RS.4b
phase: RS
loop: representation-science
status: done
deps: [RS.0, RS.4c]
acceptance: |-
  BLOCKED on RS.4c (no platform op to ingest an attention-pool-over-chunks encoder; apply_learned_encoder
  is mean-pool-only). Once RS.4c materialises the chunk-learned EmbeddingConfig, run KNN+score on the
  clean frame (eval_set 6e41eb5b). Promote chunk-learned from proxy to the real f_micro_w frame: train the
  chunk attention-pool encoder (sdr_pool, OOM-guarded) on ankh-base chunk states (config 6542db1e),
  encode ref+query, KNN, and score f_micro_w vs {dense, champion mean+reranker, learned-mean} by the
  THREE axes (NK/LK/PK x aspect x length x neighbor-identity) with paired-bootstrap CIs. VERDICT: does
  chunk-learned's proxy advantage (+0.18, concentrated in long) translate to f_micro_w, and where
  (long bucket / twilight-zone)? Lock chunk-learned as the head iff it beats learned-mean on the real
  metric. NO re-embedding (chunk cached).
estimated_hours: 8
priority: P1
tags: [chunk-learned, real-frame, f_micro_w, validation, gate]
```

### RS.5 — Post-PLM alignment head scaled on UniRef cluster reps (data-scaling curve)

```yaml
id: RS.5
phase: RS
loop: representation-science
status: pending
deps: [RS.4b]
acceptance: |-
  Scale the learned post-PLM alignment head (the validated lever) beyond the 527k benchmark, on a
  SUBSET of UniRef cluster representatives, PLM FROZEN (no re-embedding the PLM; only the tiny head
  trains; cheap forward over reps). First step = a cheap DATA-SCALING CURVE on the GO-correlation proxy
  ({527k -> +reps}) to find where returns flatten (do NOT train on all UniRef). Optionally add a
  self-supervised cluster-membership contrastive term for coverage. Ship only if the scaled head beats
  the 527k-trained head on the real frame. NOT a PLM-from-scratch (that is a compute wall, ruled out).
estimated_hours: 16
priority: P2
tags: [encoder, scaling, uniref, post-plm, contrastive]
```

### RS.6 — Retrain the reranker on the current schema, over the learned-encoder candidates

```yaml
id: RS.6
phase: RS
loop: representation-science
status: pending
deps: [RS.4b]
acceptance: |-
  The production reranker trio (68f3232c/198baf99/f0669e41) is STALE: feature_schema_sha 7fcecf26 vs
  live b2a5cd46 (73 features), trained 2026-06-21, empty metrics; it fires only on its old families
  (blind to classifier/interpro/association/self_prior/plm_id/k_context) -> ~no-op, ZERO lift in PK.
  Retrain the reranker on the CURRENT schema (all 73 features) and the current frame, and CRUCIALLY
  over the LEARNED-ENCODER candidates (not raw-mean KNN) so it composes on top of the validated ~0.50.
  Acceptance: fresh reranker beats raw KNN per category on the real frame, esp. attacks PK (the wall);
  report by the three axes with CIs. Re-frames the 0.3745 champion (its reranker contribution was ~nil).
estimated_hours: 16
priority: P1
tags: [reranker, retrain, schema, pk, compose]
```

### RS.7 — cafaeval NK/LK sparse-kernel fix (eval perf, ~10x)

```yaml
id: RS.7
phase: RS
loop: representation-science
status: in_progress
deps: []
acceptance: |-
  Production run_cafa_evaluation runs the SPARSE kernel for PK (10s) but the DENSE kernel for NK/LK
  (602s/408s). A/B proved sparse is 250-10000x faster with IDENTICAL Fmax. Make NK/LK use sparse too
  (root cause: CAFAEVAL_SPARSE not reaching the NK/LK subprocess in _invoke_cafaeval_signal_safe, or
  the NK/LK use_sparse branch unwired). PERF-ONLY: Fmax AND f_micro_w must stay bit-identical. Cuts a
  full eval from ~23min to ~2min -> 10x faster experimentation loop. Fix in flight (executor 2026-06-25).
estimated_hours: 4
priority: P0
tags: [cafaeval, sparse, perf, eval, infra]
```

### RS.4c — Plumb the attention-pool-over-chunks encoder op (unblocks RS.4b)

```yaml
id: RS.4c
phase: RS
loop: representation-science
status: done
deps: []
acceptance: |-
  Experiment A revealed apply_learned_encoder (#672) is hardwired to topk_real(Linear(mean_pool(chunks)))
  = mean-pool only, so the chunk-learned AttnPoolEncoder (sdr_pool, additive single-head attention over
  per-chunk units) cannot be ingested. Add pooling=attention support (extend apply_learned_encoder or a
  sibling op) that applies a saved attention-pool artifact over the per-chunk vectors of source config
  6542db1e (739554 chunks, materialised), top-k, and ingests as a NEW learned-code EmbeddingConfig. Save
  the artifact to storage/learned_encoders/ankh_base_chunk_attnpool.pt. Materialise codes over the 527k
  ref set via the platform path. Report the new EmbeddingConfig id. PR (no auto-merge: new embedding op).
estimated_hours: 6
priority: P1
tags: [plumbing, attention-pool, chunk, embedding-op, unblocker]
```

### RS.8 — Low-identity / remote-homology eval frame (test the twilight differentiator) [USER DECISION]

```yaml
id: RS.8
phase: RS
loop: representation-science
status: pending
deps: []
acceptance: |-
  STRATEGIC, pending user go. Experiment A proved the LAFA-delta frame CANNOT probe the twilight zone
  (it is re-annotation of already-homologous sequences: 74% high-id, 0 remote) and the learned encoder's
  advantage lives in HIGH identity, vanishing/reversing in twilight. The project's headline differentiator
  ("beat homology where it fails") is therefore UNCONFIRMED and untestable on the current frame. To test
  it, build a deliberately LOW-IDENTITY / remote-homology holdout: queries whose best experimental neighbor
  is <30% identity (MMseqs2/CD-HIT split), evaluate all arms by f_micro_w on that regime. ONLY then can we
  claim (or refute) that the learned/sparse representation recovers function where homology fails. This is
  a new eval-frame design decision -> do NOT execute without explicit user authorization.
estimated_hours: 12
priority: P1
tags: [twilight, remote-homology, eval-frame, differentiator, user-decision]
```
