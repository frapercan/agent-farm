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
  in `GOPrediction.features` (a JSONB blob). The **D45 seam** is that
  `feature_schema_sha` fingerprints the **declared schema** (family names and their
  column lists) and nothing else: not the values, not which producer wrote them, not
  whether a producer ran at all. A family can therefore be exported entirely
  zero-filled and the fingerprint will not move (see section 1.1 and the 0.3462
  incident).
- Consequence: numbers are not cheaply reproducible, provenance is implicit, and a
  new signal (e.g. a text->GO EvidenceScorer) has nowhere clean to live.

### 1.1 The seam, measured (2026-07-10, from the live DB and the producer code)

Vague description was hiding a much better fact. `go_prediction` is **101 GB over
52,235,220 rows**, and its rows are **already `(query protein, candidate GO)` pairs**
(84.8 rows per protein: the classifier emits `top_n=100` filtered at `min_score=0.01`).
The row carries ~50 **typed** columns plus two jsonb ones: `predictions_jsonb` (448 MB
in total) and `features` (**~75 GB**, averaging 1546 bytes per row).

`features` has 60 keys. **54 of them duplicate a typed column on the same row.** Only
**six live nowhere else**, and they are exactly the D45 signals:

```
classifier_score  self_prior_score  association_cross
association_total classifier_present association_present
```

Each is a **scalar per (protein, GO) pair**, not a vector. They are **already inside**
`feature_schema_sha` by name (`feature_schema.py` declares all six in `NUMERIC_FEATURES`
and in the `classifier`, `self_prior` and `association` families). Promoting them to
typed columns costs `6 x 8 B x 52.2M ~= 2.5 GB` and lets the redundant blob release
**~75 GB**. That is a storage win, not the D45 fix; see step 0 for what actually closes
the seam.

**So the store is a ~72 GB refund on this table, not a disk cost.** Under the
additive-only invariant the order is: add the six typed columns, backfill, verify
against the sealed numbers, and only then, as a separate reviewed step, drop the blob.

Numbers to not get wrong again: the classifier vocabulary is **29,461** GO terms (from
`storage/fullgo_models/classifier_m2_anc2vec.pt`), not the 757,250 rows of `go_term`
(that is all of GO including obsolete terms). Nobody ever proposed persisting a dense
per-protein vocab vector, and even that would be 36 GB rather than the "tens of TB" an
earlier reading of this document imagined. Database total: 214 GB logical / 238 GB on
disk; other large tables are `term_cooccurrence` 61 GB, `sequence_embedding` 26 GB,
`protein_go_annotation` 23 GB.

### 1.2 The seam, traced (2026-07-10, and it is not where this document said it was)

Section 1.1 measured the blob. It did not explain the drift. Tracing it to the code and
back to the data gives a different, sharper answer.

1. `compute_feature_schema_sha(families, drop)` hashes `"<family>=<sorted columns>"`,
   and `compute_schema_sha(columns)` hashes the sorted column names. The fingerprint
   covers **names and family membership**. It cannot see a value, a producer, or whether
   a producer ran.
2. `protea/core/_leaf_record_builder.py::_lafa_default_fields()` (line 342) returns all six
   as `0.0`, and says so in its own docstring: the classifier and association columns *stay
   zero until later lafa-integrate slices wire their producers. A well-defined zero, not
   NaN.* Only `self_prior_score` is overwritten, and only under the `compute_self_prior`
   payload flag.
   Two details in that same docstring sharpen the finding. First, it states the six are
   emitted unconditionally so that `_assert_canonical_columns` **and the contracts
   producer-coverage guard never fail the dump**: the guard whose job is to catch a missing
   producer was appeased with a constant. Second, the neighbouring
   `_reranker_default_fields()` (line 34) handles the KNN block **correctly**, writing `NaN`
   for "no KNN evidence, a missing measurement" and `0` only for "zero neighbours voted, a
   true absence", and explains the distinction in prose. **The right convention already lives
   twenty lines above the violation**, so fixing D45 is applying the file's own rule, not
   importing a new one.
3. The sealed run recorded the consequence: `results/clean_227230/comparison.json` reads
   `feature_exclusions: "association_* and classifier_* (zero-filled in export)"`.
4. The database is fine. Sampling 50,000 rows of `go_prediction.features` finds **0.0%**
   zeros for `association_total` and **0.0%** for `classifier_score`. The predict path
   writes real values; the export builds records from scratch and invents zeros.

**So D45 is a producer seam.** Three declared families shipped semantically null and
every fingerprint matched. What closes it:

- **No silent default.** Emit `NaN` (LightGBM already reads it as missing) when no
  producer ran, or refuse to write the row. A zero is a claim; missing is the truth.
- **A degeneracy check at export.** A declared family that is constant across a shard
  fails the job loudly instead of shipping.
- **Provenance per family.** Which producer, at which version, over which snapshot. That
  is `SignalConfig.source`, and it is why the store is the backend of explainability
  rather than a disk optimisation.

## 2. Signal taxonomy by provenance

Every signal has a **source** (a model / database / computation), a **cacheable
unit**, and a **version**. Five classes plus one absent:

| Class | Families | Source / producer | Cacheable unit | Today | Target |
|---|---|---|---|---|---|
| **A. PLM representation** | embeddings, emb_pca | 8 PLM backends (mean/chunk pool) | (protein, plm_config) | `SequenceEmbedding` cached | keep |
| **A'. Learned representation** | d8979601 k-WTA; protst-learned (future) | learned head on a base embedding | (protein, encoder_config) | `SequenceEmbedding` | keep + extend |
| **A''. Text-aligned representation** | protst_text, protrek_text | text-supervised PLM (ESM + PubMedBERT) via ProtDescribe / trimodal contrastive | (protein, text_model_config) | absent | -> SignalValue (halfvec), **VALIDATED 07-09** |
| **B. Full-vocab classifier** | classifier_score | `classifier_producer.py` (6-PLM concat, in_dim 8320 -> hybrid head over a 29,461-term vocab) | **(protein, candidate GO) -> scalar** (the head scores the whole vocab in GPU memory, then `predict` keeps `top_n=100` above `min_score=0.01`; the dense vector is never persisted) | JSONB blob (D45) | -> typed column |
| **C. Homology / neighbourhood** | knn, knn_distance, knn_vote, alignment_nw/sw, taxonomy_* | `knn_search.py` + NW/SW + NCBI taxonomy (query vs t0 reference) | (query, k, ref_snapshot) neighbour list; (query,neighbour) pairwise | on-the-fly | -> cache neighbour list + pairwise |
| **D. Prior-knowledge / association** | association_total/cross, self_prior, anc2vec_query | GO co-occurrence at t0; the protein's own t0 GO | global(t0_snapshot) matrix + (protein, snapshot) | JSONB blob (D45) | -> SignalValue + cached global matrix |
| **E. Domain** | interpro | InterProScan + InterPro2GO | (protein) | partial | -> SignalValue |
| **Context** | go_context (freq/IA), anc2vec/gotext basis, lineage | OBO + IA + term basis | global(OBO_snapshot) + per-GO | npz / on-the-fly | -> cache per snapshot |
| **F. [absent] Structure** | AFDB / FoldSeek 3Di | tested RED (structure conserves MF not BP) | -- | -- | out of scope |

### 2.1 Registered text-aligned signals (validated 2026-07-09)

Class A'' is not hypothetical. Two text-aligned PLMs were validated board-faithful
as orthogonal signals for GO transfer (kNN GO-vote, `f_micro_w`, 9-cell, query
7401 -> reference 15000, 3-axis stratified; receipts in
`storage/text_scorer/*_result.json`, writeup `storage/text_scorer/WRITEUP.md`).
They enter the store as two `SignalConfig`s, cached per-protein like embeddings:

| `SignalConfig.name` | base / source | dim | validated role | cutoff |
|---|---|---|---|---|
| `protst_text` | ProtST (ESM-1b + PubMedBERT, ProtDescribe function text), Apache-2.0 | 512 | **BP-wall lever + MF**: isolated text contribution (vs same ESM-1b base) +0.062 nk-BP (leakage-free), +0.072 lk-BP (the wall); survives hard-homology tail | model pub < t0=v227 |
| `protrek_text` | ProTrek (ESM2 + PubMedBERT, trimodal), MIT | 1024 | **CCO lever**: beats champion on all 3 CCO cells (+0.05/+0.07/+0.04), survives hard homology; does NOT reproduce BP (that lift is ProtST-specific) | model pub < t0=v227 |

Key facts the store must record in `SignalConfig.source`:
- **Provenance**: `{model, base_plm, text_encoder, training_text_source, license,
  pub_date}` so the leakage argument (model published before t0, NK proteins had no
  function text) is explicit and auditable, not tribal knowledge.
- **The two are complementary, not redundant**: equal-weight kNN combine
  `protst_text + protrek_text + d8979601` = 0.2650 vs champion-alone 0.2213
  (+0.044 raw, pre-reranker). So BOTH are registered, ProtST for BP/MF, ProTrek for CCO.
- **Storage**: per-protein dense `halfvec` (like embeddings), keyed
  `(protein, text_model_config, snapshot)`. The **text->GO EvidenceScorer** is a
  *consumer* (kNN GO-vote over the cached vectors), not a stored value -- the store
  holds the representation, the reranker/scorer fuses it.
- **Learned-head extension** (class A', principle in section 4): a learned k-WTA head
  on `protst_text` is a future `SignalConfig` (`protst_learned`), never raw-vs-raw.

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
5. **New signals** are added by registering one more `SignalConfig` + caching its
   values -- they slot into the dataset assembly automatically, gated by the
   orthogonality + leakage protocol. The **text-aligned signals** (`protst_text`,
   `protrek_text`, section 2.1) are the first such candidates already through the
   gate (validated 07-09); they are registered in this rerun, not bolted onto the
   old pipeline -- their board number is regenerated in the single frame with
   everything else.

## 6. Implementation sequence

0. **Close D45. It is a PRODUCER seam, not a storage seam** (traced to code and data on
   2026-07-10; the earlier text of this step was wrong and is corrected here).

   The six signals are **already inside the fingerprint**: `feature_schema.py` lists them in
   `NUMERIC_FEATURES` and in `FEATURE_FAMILIES` (`classifier`, `self_prior`, `association`),
   and `compute_feature_schema_sha` hashes family names together with their column lists.
   What the fingerprint cannot see is whether a producer ever ran. And one did not:
   `protea/core/_leaf_record_builder.py::_lafa_default_fields()` returns
   `classifier_*`, `association_*` and `self_prior_score` as a **well-defined `0.0`**, and
   its own docstring says the classifier and association columns *"stay zero until later
   lafa-integrate slices wire their producers"*. The sealed run recorded the consequence:
   `comparison.json` reads `feature_exclusions: association_* and classifier_* (zero-filled
   in export)`. Meanwhile the database is fine: sampling 50,000 rows of
   `go_prediction.features` finds **0.0%** zeros for `association_total` and
   `classifier_score`. The blob holds real values; the export invents zeros, and the sha
   stays identical because the column names never changed.

   So the fix is not a column type. It is three things:
   - **No silent default.** Emit `NaN` (which LightGBM already reads as missing) when no
     producer ran, or refuse to write the row. A zero is a claim; missing is the truth.
   - **A degeneracy check at export.** If a declared feature family is constant across a
     shard, the job fails loudly rather than shipping a semantically null column.
   - **Provenance per family.** Record which producer, at which version, over which
     snapshot, emitted each family alongside the dataset. That is exactly
     `SignalConfig.source`, and it is why the store is the backend of explainability rather
     than a disk optimisation.

   The storage win is real and independent: `go_prediction` is 101 GB over 52.2M rows, its
   `features` jsonb is ~75 GB, and **54 of its 60 keys merely duplicate typed columns on the
   same row**. Promoting the six blob-only scalars to typed columns costs ~2.5 GB and lets
   the redundant blob be dropped as a separate reviewed step (additive-only invariant).
   Do that for the disk, not for D45.
1. **Schema + migration**: `SignalConfig`, `SignalValue`, `SignalGlobalArtifact`
   (Alembic; halfvec for dense). ADR entry. Note the regimes: **per-pair scalars stay
   typed columns on `go_prediction`** (they are already keyed that way); `SignalValue`
   is for **per-protein dense** signals (learned codes, text embeddings, emb_pca) and
   `SignalGlobalArtifact` for the global ones (association matrix, IA, term bases).
2. **Producers write to the cache**: refactor `classifier_producer`, association,
   self_prior, interpro, anc2vec/gotext to `compute-or-load` (exact embedding-cache
   pattern); the on-the-fly path becomes a cache-miss filler.
   The **text producers** (`protst_text`, `protrek_text`; prototype extractors at
   `storage/text_scorer/extract_protst_both.py` + `extract_protrek.py`) become
   on-platform ops writing `halfvec` into the store like any PLM backend.
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
