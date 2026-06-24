# roadmap-from-zero

From-scratch roadmap to the highest reproducible CAFA/LAFA score and a 10/10 thesis,
built on a CLEAN, fully-reproducible evaluation frame. Combines the CAFA5/CAFA6
winning levers (ProtBoost top-2 ablation, PROTGOAT, GOCurator/CondProbMod, GOBeacon)
with our own validated, NOVEL lever: the learned GO-aligned k-WTA hard-neg retrieval
encoder (beats dense KNN ~40% reranked, no CAFA solution has it).

Driving lesson from the prior campaign: the score archaeology pain (could not reproduce
the 0.3745 champion because it was an external `job_id=None` artifact under an
unrecoverable propagation frame) means **every number must be born on-platform with full
provenance on a frozen, versioned frame.** That is F0, and it unblocks everything.

NOT a DB wipe: the 527k x 8-PLM embeddings are expensive and fine; the fix is a clean,
job-backed eval frame + provenance discipline, with backups as the safety net.

Lever menu (expected gain, source):
- learned encoder retrieval arm (OURS, +40% reranked) => the differentiator
- CondProbMod conditional-probability hierarchical training (+0.04, ProtBoost)
- GCN/meta stacking over evidence arms (+0.03, ProtBoost; = ADR-D43)
- soft Pmin-Pmax two-way propagation (parent >= child), multi-PLM ensemble
- taxonomy + GOA-IEA features (+0.02 each), literature TF-IDF (PROTGOAT), PPI (GOBeacon)
- sparse k-WTA index (efficiency: the encoder becomes faster AND better)

### R0.1 — Clean reproducible evaluation frame

```yaml
id: R0.1
phase: F0
loop: roadmap-from-zero
status: done
deps: []
acceptance: |-
  Eval set generated ON-PLATFORM via generate_evaluation_set (job-backed, NOT job_id=None);
  OBO t0/t1 + IA + TOI pinned via band_registry (asymmetric cross-OBO, per PR #671);
  a baseline dense-KNN reranked f_micro_w reproduced bit-identically across two independent runs;
  the exact eval invocation (params/OBO/IA/TOI) documented in a runbook;
  EVAL_LAFA_PARITY updated so /benchmark and a manual dispatch agree.
estimated_hours: 12
priority: P1
tags: [frame, reproducibility, eval, unblocker]
```

The unblocker. Without a frame where dense reproduces bit-identically, no learned-vs-dense
or learned-vs-leaderboard number is trustworthy (the exact problem that blocked the prior run).

### R1.1 — Learned encoder to production + sparse k-WTA index

```yaml
id: R1.1
phase: F1
loop: roadmap-from-zero
status: pending
deps: [R0.1]
acceptance: |-
  apply_learned_encoder operation merged (PROTEA PR #672) and learned codes materialised
  under a clean learned-code EmbeddingConfig;
  a sparse KNN backend (inverted index / sparse cosine over the k-WTA codes) added to
  protea-method knn_search (search_backend="sparse") so the encoder is faster AND better;
  learned vs dense benchmarked on the F0 clean frame -> reproducible reranked delta,
  PK precision AND recall reported separately.
estimated_hours: 20
priority: P1
tags: [encoder, learned, sparse-index, retrieval, novel]
```

Our differentiator. The learned k-WTA hard-neg retrieval representation (validated +40%
reranked on a consistent frame) becomes a first-class, efficient platform arm.

### R2.1 — CondProbMod + soft Pmin-Pmax hierarchical post-processing

```yaml
id: R2.1
phase: F2
loop: roadmap-from-zero
status: pending
deps: [R0.1]
acceptance: |-
  Conditional-probability hierarchical training (CondProbMod: train only on pairs with a
  non-zero parent; reconstruct via the recursive parent-product formula) implemented in
  protea-reranker-lab;
  two-way soft propagation (root-to-leaf Pmin + leaf-to-root Pmax, 0.7/0.3 blend, parent>=child)
  added as a post-processing pass;
  ablation delta on the F0 validation frame (target: reproduce ProtBoost's ~+0.04 region).
estimated_hours: 16
priority: P1
tags: [condprobmod, propagation, hierarchy, cafa5-lever]
```

The single biggest external lever in the ProtBoost ablation (+0.04). Hard label propagation
was already shown negligible for us; this is the SOFT, hierarchy-aware variant.

### R3.1 — Meta-stacking over evidence arms (GCN / ADR-D43) [= F-RERANK-UNIVERSAL]

```yaml
id: R3.1
phase: F3
loop: roadmap-from-zero
status: deferred
superseded_by: F-RERANK-UNIVERSAL
deps: [R1.1, R2.1]
acceptance: |-
  FUSED into farm-platform F-RERANK-UNIVERSAL (the same objective: the single pooled,
  aspect-conditioned, IA-aligned reranker = ADR-D43 meta-reranker). The executable
  decomposition lives there as F-RERANK-UNIVERSAL.1..6 (registry/IA bridge -> pooled
  multi-manifest view -> (protein,aspect) staging + VALID/TEST windows -> IA-weighted
  LambdaMART + leakage-audited negatives + seeded bounded-K -> full training + calibration
  + DAG correction -> selective-deploy measured per category with paired-bootstrap CIs).
  This roadmap milestone is COMPLETE when F-RERANK-UNIVERSAL.6 lands. The roadmap arms it
  must pool over (learned-KNN encoder = R1.1, sparse k-WTA index, CondProbMod = R2.1) are
  fed in as sources at F-RERANK-UNIVERSAL.2/.4. Do NOT execute this entry directly.
estimated_hours: 24
priority: P2
tags: [meta-reranker, gcn, stacking, adr-d43, fused]
```

### R4.1 — New evidence features: literature TF-IDF + PPI graph

```yaml
id: R4.1
phase: F4
loop: roadmap-from-zero
status: pending
deps: [R0.1]
acceptance: |-
  Literature TF-IDF (per-protein paper text, PROTGOAT lever) and PPI-graph features (GOBeacon)
  given a home in the feature schema (protea-contracts) and produced by a platform producer;
  per-feature ablation on the clean frame; ship a feature ONLY if its ablation is positive
  (no negative-feature shipping, per the no-archaeology / SOTA-testing norm).
estimated_hours: 24
priority: P2
tags: [features, tfidf, ppi, data]
```

### R5.1 — Consolidate #1: final ensemble + official reproducible eval

```yaml
id: R5.1
phase: F5
loop: roadmap-from-zero
status: pending
deps: [R1.1, R2.1, F-RERANK-UNIVERSAL.6, R4.1]
acceptance: |-
  Final ensemble assembled; the official LAFA/CAFA f_micro_w produced END-TO-END on-platform
  with full provenance (reproducible, no external artifact); leaderboard position established
  honestly under equal conditions; thesis numbers locked (only validated, UI-verifiable numbers);
  the 10/10 thesis story (novel learned retrieval + reproducible framework + decomposition science)
  written against these locked numbers.
estimated_hours: 20
priority: P1
tags: [consolidate, ensemble, thesis, leaderboard]
```
