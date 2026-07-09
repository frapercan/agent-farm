# The Signal Store — foundation for the clean iteration

The data foundation for the clean thesis iteration. Every predictive **signal**
becomes a first-class, provenance-tracked, DB-cached artifact -- computed once,
versioned, reused -- exactly as PLM embeddings already are. This ends the ad-hoc
per-run feature computation and the untracked JSONB-blob seam (D45), and lets every
thesis number be regenerated cleanly from the same cached signals. Written
2026-07-08. Companion to `PLAN.md` and `../thesis-pillars/PILLARS.md`.

## 1. The problem being fixed

Today:
- **PLM embeddings ARE cached** (`SequenceEmbedding`, keyed by `embedding_config_id`,
  computed once and reused). This is the model to imitate.
- **Signals/features are NOT.** They are computed on the fly during
  `export_research_dataset` (KNN + feature generation), and some live per-prediction
  in `GOPrediction.features` (a JSONB blob). Several signals
  (`classifier_score`, `self_prior`, `association_*`, `IA`) sit in that blob
  **outside `feature_schema_sha`** -> the **D45 seam**: their values can drift
  between train and serve with no fingerprint catching it (the 0.3462 incident).
- Consequence: numbers are not cheaply reproducible, provenance is implicit, and a
  new signal (e.g. a text->GO EvidenceScorer) has nowhere clean to live.

## 2. Signal taxonomy by provenance

Every signal has a **source** (a model / database / computation), a **cacheable
unit**, and a **version**. Five classes plus one absent:

| Class | Families | Source / producer | Cacheable unit | Today | Target |
|---|---|---|---|---|---|
| **A. PLM representation** | embeddings, emb_pca | 8 PLM backends (mean/chunk pool) | (protein, plm_config) | `SequenceEmbedding` cached | keep |
| **A'. Learned representation** | d8979601 k-WTA; (ProtST text; future) | learned head on a base embedding | (protein, encoder_config) | `SequenceEmbedding` | keep + extend |
| **B. Full-vocab classifier** | classifier_score | `classifier_producer.py` (6-PLM concat -> ProjHead -> GO code) | (protein) -> vocab-score vector | JSONB blob (D45) | -> SignalValue |
| **C. Homology / neighbourhood** | knn, knn_distance, knn_vote, alignment_nw/sw, taxonomy_* | `knn_search.py` + NW/SW + NCBI taxonomy (query vs t0 reference) | (query, k, ref_snapshot) neighbour list; (query,neighbour) pairwise | on-the-fly | -> cache neighbour list + pairwise |
| **D. Prior-knowledge / association** | association_total/cross, self_prior, anc2vec_query | GO co-occurrence at t0; the protein's own t0 GO | global(t0_snapshot) matrix + (protein, snapshot) | JSONB blob (D45) | -> SignalValue + cached global matrix |
| **E. Domain** | interpro | InterProScan + InterPro2GO | (protein) | partial | -> SignalValue |
| **Context** | go_context (freq/IA), anc2vec/gotext basis, lineage | OBO + IA + term basis | global(OBO_snapshot) + per-GO | npz / on-the-fly | -> cache per snapshot |
| **F. [absent] Structure** | AFDB / FoldSeek 3Di | tested RED (structure conserves MF not BP) | -- | -- | out of scope |

Three storage regimes fall out:
- **Per-protein** (classifier, self_prior, anc2vec_query, interpro, emb_pca, learned
  codes): cache like embeddings, keyed `(protein, signal_config, snapshot)`.
- **Per-pair** (alignment, taxonomy, knn edges): cache `(query, neighbour)` OR cache
  the neighbour list per `(query, k, ref_snapshot)` + compute cheap pairwise.
- **Global** (association matrix, IA, GO frequency, term bases): cache one versioned
  artifact per `(t0/OBO snapshot)`.

## 3. The `SignalValue` schema (analogous to `SequenceEmbedding`)

```
SignalConfig                              -- the provenance/version envelope
  id                 uuid pk
  name               text        -- e.g. "classifier_m2_gotext", "protst_text", "association_cross"
  signal_class       text        -- A/A'/B/C/D/E enum
  producer           text        -- module + version, e.g. "classifier_producer@<git_sha>"
  source             jsonb       -- {model, base_embedding_config, db, release, cutoff_date}
  schema_sha         text        -- canonical fingerprint of the value shape/meaning
  created_at         ts

SignalValue                               -- the cached value (per-protein regime)
  id                 uuid pk
  signal_config_id   fk -> SignalConfig
  protein_accession  text        -- (or pair_key for per-pair; null for global)
  snapshot_id        fk -> AnnotationSet | OntologySnapshot   -- the t0/OBO the value depends on
  value              halfvec | jsonb   -- dense vector (halfvec, like embeddings) or structured
  unique (signal_config_id, protein_accession, snapshot_id)

SignalGlobalArtifact                      -- the global regime (association matrix, IA, bases)
  signal_config_id, snapshot_id, artifact_uri (ArtifactStore), schema_sha
```

Key properties (each mirrors the embedding cache):
- **Computed once, reused**: keyed lookup, skip-if-present (like embeddings).
- **Versioned + provenance**: `SignalConfig.source` records the model/db/cutoff;
  `schema_sha` fingerprints the value meaning -> **kills D45** (every signal is now
  inside a fingerprint, no silent blob skew).
- **Snapshot-scoped**: a signal that depends on t0 annotations or an OBO release is
  keyed to that snapshot -> temporal correctness is explicit, not implicit.
- **halfvec storage** for dense signals reuses the pgvector storage path (NOT for
  KNN -- KNN stays numpy/FAISS, hard rule).

## 4. Representation-learning as a first-class principle

Validated at +61% (learned k-WTA beats any fixed layer/sparsity/norm): a dense
representation is **never used raw** at the operating point. In the store this means
each dense representation admits **two cached forms** under two `SignalConfig`s:
- the **raw** form (baseline), and
- the **learned-encoded** form (the operating point: a k-WTA/attention-pool head
  trained toward function, e.g. d8979601 on ankh, protst-learned on ProtST).

New backbone candidates enter through the learned-head protocol, never raw-vs-raw.
The **reranker remains the learned fusion layer** over the heterogeneous signals;
representation learning lives at the embedding level, fusion learning at the
reranker level -- two learning layers with the signal store between them.

## 5. The clean-rerun flow

1. **Register** every signal as a `SignalConfig` (provenance + version).
2. **Compute + cache** all signals into the store (per-protein / per-pair / global),
   as tracked ops with MLflow, skip-if-present.
3. **Assemble** the reranker dataset by JOINING the store (no on-the-fly recompute,
   no JSONB blob) -> a clean, provenance-stamped feature matrix with one
   `feature_schema_sha` covering ALL signals.
4. **Re-run** every experiment board-faithful from that matrix -> every thesis number
   regenerated, one metric (f_micro_w), one frame (227->230), reproducible.
5. **New signals** (text->GO EvidenceScorer, future candidates) are added by
   registering one more `SignalConfig` + caching its values -- they slot into the
   dataset assembly automatically, gated by the orthogonality + leakage protocol.

## 6. Implementation sequence

1. **Schema + migration**: `SignalConfig`, `SignalValue`, `SignalGlobalArtifact`
   (Alembic; halfvec for dense). ADR entry.
2. **Producers write to the cache**: refactor `classifier_producer`, association,
   self_prior, interpro, anc2vec/gotext to `compute-or-load` against the store
   (exact embedding-cache pattern); the on-the-fly path becomes a cache-miss filler.
3. **Dataset assembly reads from the store** (replace the blob + on-the-fly join);
   one `feature_schema_sha` over all signal_configs -> D45 closed.
4. **Backfill** the current signals for the 227/230 snapshots into the store.
5. **Clean rerun** of the 9-cell + LOFO + ablations from the assembled matrix.
6. Only then: the thesis rewrite on regenerated numbers.

## 7. End-to-end coherence check (does this make sense start to finish?)

- **Why cache signals, not just recompute?** Reproducibility + provenance + D45. The
  embedding cache already proved the pattern; signals are the same shape of problem.
- **Does it change any result?** No -- it regenerates the SAME numbers deterministically
  with provenance; it removes drift, it does not move the science.
- **Does it fit the pillars?** Yes: Pillar 1 (the signal taxonomy IS the store's
  schema), Pillar 2 (the fusion reads the store), Pillar 3 (the LOFO runs over the
  cached signals), Pillar 4 (new orthogonal-signal candidates enter cleanly).
- **Risk**: scope. This is weeks of infra. Mitigation: the store is additive (the
  on-the-fly path still works as the cache-miss filler), so it can land incrementally
  without breaking the live pipeline, one signal class at a time (start with the
  D45-blob signals, the ones that actually drift).
