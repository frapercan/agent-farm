# Unified evidence cross-encoder: design + verification (2026-06-30)

The BP wall (LK/PK-BP vs TransFew/FunBind) was diagnosed as representation/evidence-bound,
not scoring-architecture-bound: on the hard clf-admitted PK-BP candidates both the two-tower
and the GCN bi-encoder score near-random (AUROC 0.52-0.54). This design treats the data, the
model, and the verification as ONE system, with a data-level gate that can kill the build
before any heavy training if the signal is not in the data.

## 0. The whole (one abstraction)
score = f( EvidenceBundle(protein, snapshot) , GoTerm ) via a TRAINED CROSS-ENCODER.
- A protein is a SET of evidence tokens (not one pooled vector): PLM mean(s), learned k-WTA
  code, literature-sentence embeddings, InterPro-domain embeddings, prior-GO embeddings (LK/PK).
- A GO term is text(def) + graph(DAG) + IA, via a label encoder.
- Cross-attention lets the GO term attend to the SPECIFIC evidence token that supports it
  (a sentence, a domain), instead of cosine of pooled vectors (which was near-random).
- ONE piece serves literature + domains + structure + GO-graph scoring at once.
- Output feeds the existing meta-reranker (ADR-D43) as a new evidence score (complement, not
  replace) and/or as a candidate source. Same temporal frame, same board-faithful cafa_eval.

## 1. Data we handle, and how it is stored

### Protein-side evidence
| source | format | location | dim / shape | coverage | granularity | temporal |
|---|---|---|---|---|---|---|
| PLM embeddings (8 PLMs) | pgvector halfvec rows + .npy cache | PG `sequence_embedding`; `PROTEA/data/ref_cache/*_embeddings.npy` | 640..2560 | ~527k each (esm2_150m 66k, prot_t5_half 0) | per-chunk stored, MEAN consumed | seq-only / atemporal |
| learned k-WTA codes (d8979601) | npz | `sparse_classifier/{clf_protein_codes,_big,eval_protein_codes}.npz` | (N, 2048) f16 | 88,212 / 554,378 / 7,401 | mean-over-chunks | atemporal (frozen) |
| literature text | JSON dict | `sparse_classifier/literature_infame/uniprot_cache.json` (+ split caches) | desc, funcs[str], refs[{title,pmid,year,month,bucket}] | 61,450 | per-protein / per-ref | `date_bucket` precut/future vs T0; only precut used |
| InterPro domains | JSON dict | `sparse_classifier/interpro2go_test/{protein2ipr,valid_protein2ipr}.json` | acc -> [IPR] | 7,401 / 14,926 | set of IPR (no spans) | InterPro release snapshot |
| InterPro2GO | JSON | `.../ipr2go_prop.json` | IPR -> [GO] (propagated) | 14,803 IPR | term-set | EBI flat file |
| raw sequence | PG Text (MD5-dedup) | PG `sequence` | str | full corpus | per-protein | atemporal |

### GO-term side
| artifact | format | location | shape/vocab | how built | temporal |
|---|---|---|---|---|---|
| GO sparse codes | npz | `sparse_classifier/go_sparse_codes.npz`; serve `storage/two_tower_sparse/...` | (39906, 1024) = 768 BioBERT text + 256 PPMI-SVD | `build_go_sparse.py` (whiten+kWTA) | v227 t0 co-annotation |
| GO text emb | npz | `sparse_classifier/go_text_emb.npz` | (39906, 768) | BioBERT `name. def` mean-pool | atemporal |
| GO DAG | json | `sparse_classifier/go_parents.json` | 39903 keys | OBO `is_a` ONLY, child->[parents] | static (2025-07-22 OBO) |
| per-cut GO codes | npz | `storage/two_tower_sparse/per_cut/go_sparse_codes_v{160..227}.npz` | (39906,1024) | per-cut PPMI through FROZEN v227 SVD basis | 15 snapshots, leakage-clean |
| IA | tsv | `protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv` | 39906 | Clark-Radivojac | v227 t0 |
| OBO | obo | `protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo` | 48165 terms | release 2025-07-22 | t0 |

### Supervision + pools + eval
- Rolling-origin (ADR-D40): TRAIN snapshot_pairs v160-v165..v220-v225, VALID v225-v227,
  TEST v227-v230 (dates: v227=2025-09-04, v230=2026-03-04). Split on snapshot_pair ONLY.
- Label = temporal positive: 1 if (protein,GO) is a NEW annotation at vB absent at vA.
- Frozen parquets: `sparse_classifier/percut_rerank/{train.parquet (28.95M x 78), eval.parquet
  (863,735 x 78)}` + baseline/ (M2). Published analogue under `datasets/<name>/`.
- Candidate pools: KNN `eval_knn.parquet` (471,798); UNION `clean_227230/clfassoc/eval_scores.parquet`
  (1,198,440, ~60.7% NaN distance = clf/assoc-only = the recall to rescue). PK uses knn_present
  only; NK/LK use the full union.
- Feature schema: protea-contracts `feature_schema.py` v4, ~66 features in families (retrieval/KNN,
  alignment nw/sw, taxonomy, GO-context, anc2vec, emb_pca, interpro, classifier, self_prior,
  association, lineage). The cross-encoder must SUBSUME or COMPLEMENT these.
- Ground truth: `lafa_gt/groundtruth_{NK,LK,PK,PK_known}.tsv` + terms_of_interest. Board-faithful
  `score_cafaeval.py`: OBO/IA/TOI, prop=fill, norm=cafa, no_orphans, PK excludes PK_known,
  f_micro_w per (cat,aspect).
- Storage systems: Postgres = source of truth (live; HARD RULE never point agents at it; read
  the exported parquet/npz or the backups). MinIO/ArtifactStore = boosters + published datasets.
  Local parquet/npz under results/ + storage/ = what agents consume. Backups = nightly pg_dump.

## 2. Data gaps that shape the design (decisive)
1. PER-RESIDUE PLM embeddings are NOT persisted (only chunk-pooled). So cross-attention must be
   at EVIDENCE-TOKEN granularity (a small set of tokens per protein), not residue level, unless
   we recompute residue embeddings (expensive, 12GB GPU).
2. Literature is TITLES ONLY (no abstracts). The strong literature signal needs abstract bodies
   (a PubMed fetch). This is the single cheapest high-value data upgrade.
3. STRUCTURE is entirely absent (no FoldSeek 3Di, no AFDB; UniProt->AFDB not mapped). FunBind's
   structure modality is a NEW pipeline, out of scope for v1.
4. GO label encoder uses is_a ONLY; part_of/regulates/synonyms/xrefs are dropped. Cheap to enrich.
5. Two of the 8 PLMs are unusable (prot_t5_half 0, esm2_150m partial); ankh-base config_id
   ambiguity (lab 6542db1e vs ADR 08234f06) to reconcile.

## 3. How we EXPLORE the data (EDA), and the decisive kill-gate
The diagnostic already showed PLM-cosine is near-random on the hard candidates. So BEFORE
building the cross-encoder we run a data-level audit answering: is there separable signal in ANY
evidence for the hard candidates? If not, no architecture helps and we stop.

EDA-1 Coverage matrix: per evidence source x category x aspect, fraction of proteins/candidates
  with that evidence (literature precut, InterPro, each PLM, prior-GO). Focus on PK-BP and the
  clf-only (NaN-distance) rows.
EDA-2 Leakage re-audit: confirm per-cut honesty end-to-end (precut buckets, frozen SVD basis,
  snapshot labels) on a sample; confirm no future literature/annotation leaks.
EDA-3 PER-EVIDENCE SEPARABILITY (the kill-gate): on the hard clf-only PK-BP candidates (and
  LK-BP), compute AUROC/AP of true-vs-false using EACH single evidence source alone:
  (a) best-PLM cosine (baseline, known ~0.54), (b) literature max-cosine with TITLES, (c)
  literature with ABSTRACTS (after a small fetch), (d) InterPro2GO membership, (e) prior-GO
  co-association, (f) GO-text/IA priors. The question: does any source exceed ~0.6-0.65? If the
  best single evidence is still ~0.5, the signal is not in the data we can get -> STOP, consolidate.
  If e.g. abstracts or InterPro reach 0.65+, that is the evidence to build the cross-encoder on.
EDA-4 Ceiling-by-evidence: how much board-faithful recall ceiling each evidence adds on PK-BP.
EDA-5 Label/imbalance audit: positive rates (single-digit %), the temporal-positive definition,
  stratify by length x category x neighbor-identity (standing norm).

Deliverable: a separability/coverage report that GATES whether to build the model at all.

## 4. Cross-encoder architecture (if EDA-3 passes)
- Tokenize the protein into evidence tokens, each = vector + learned type-embedding:
  [PLM-mean(ankh-base, +maybe esm2-650m)], [k-WTA code], [literature sentences top-k (abstracts)],
  [InterPro domain embeddings], [prior-GO embeddings for LK/PK]. ~8-32 tokens/protein.
- GO term tokens: text(def, enriched with synonyms) + DAG/GCN embedding + IA scalar.
- A small cross-attention transformer: GO-term query attends over the protein evidence tokens
  (and a CLS pools the interaction) -> compatibility logit. Optionally bi-directional.
- Loss: ASL/focal on temporal-positive labels; in-frame multi-snapshot; per-cut honest evidence.
- Output: P(protein has GO) -> (i) reranker feature (complement feature_schema), (ii) candidate
  source (union). Frozen evidence encoders; only the cross-attention head trains (cheap, 12GB-safe).

## 5. Verification protocol (gates, cheap-first)
- GATE 0 (data): EDA-3 separability. If no evidence > ~0.6 AUROC on hard candidates -> STOP.
- GATE 1 (smoke): tiny cross-encoder trains, loss drops, beats best-single-evidence AUROC on a
  held-out slice.
- GATE 2 (in-frame): train on v160..v225, board-faithful 9-cell on v227-v230. Reproduce champion
  first (A/B), then add the cross-encoder score. Target: PK-BP > 0.218 toward TransFew 0.294.
- GATE 3 (stratified + ablation): gains hold on hard/twilight/remote; ablate each evidence to show
  what carries the gain (esp. abstracts vs InterPro vs prior-GO).
- Honest kill criteria at every gate; nothing injected without a non-regressive board-faithful win.

## 6. Phased plan
- Phase A (cheap, decisive): EDA + the per-evidence separability gate + fetch literature ABSTRACTS
  for the hard PK/LK-BP proteins. Decides if the signal exists. <1 day.
- Phase B: build the per-(protein,snapshot) evidence-token store (unify PLM/k-WTA/literature/
  InterPro/prior-GO + enrich GO label side with synonyms/relations).
- Phase C: cross-encoder smoke -> in-frame train -> board-faithful 9-cell + ablations.
- Phase D (optional, later): structure modality (UniProt->AFDB->FoldSeek 3Di) if Phase C shows
  the residual is structural.

## 7. Honest risks
- The EDA may show NO evidence separates the hard candidates (the signal is genuinely not in
  sequence+text+domains) -> then the BP wall is the field's wall and we consolidate. Phase A is
  designed to find this cheaply, before the heavy build.
- Structure is a large new pipeline; defer.
- The cross-encoder is a real build, but evidence encoders stay frozen so it is 12GB-tractable.
