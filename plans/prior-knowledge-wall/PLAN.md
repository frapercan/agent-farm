# The prior-knowledge wall: win LK-BPO and PK-BPO (loop `prior-knowledge-wall`)

DRAFT, pending greenlight. **Supersedes `plans/bp-structural-lever`**, whose headline
diagnosis is contradicted by its own receipt and by measurement (see §0). Goal: 9/9 on the
LAFA board, v227->v230, `f_micro_w`. We hold 7/9. The two open cells are LK-BPO (0.4402 vs
TransFew 0.5120, gap **+0.072**) and PK-BPO (0.2181 vs 0.2943, gap **+0.076**).

## 0. The plan we have been executing is built on a number that does not exist

`bp-structural-lever` opens with:

> *"The gap is candidate GENERATION, not ranking. PK-BP recall ceiling = 0.319 -> even
> perfect ranking caps at 0.32 IA-recall; 68% of informative BP mass is never generated.
> HARD generation wall."*

**Its own receipt, 25 lines later, says otherwise.**
`protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json` (n=4402, the exact
PK-BPO protein set):

| cell | knn ceiling | knn+clf ceiling |
|---|---|---|
| **PK-bpo** | **0.4695** | **0.5372** |
| LK-bpo | 0.7668 | **0.8227** |
| NK-bpo | 0.6985 | 0.7393 |

And the oracle on the current export's pool (`storage/cooc_experiment/atlas_rebuild.py`,
raw scores, board harness) says **0.7519**. The numbers agree once you notice they measure
pools of increasing richness: KNN only (0.47), KNN+classifier (0.54), the export's unioned
pool (0.75). **`0.319` appears in no receipt anywhere.**

**Consequence.** We deliver **0.2131** against a ceiling of 0.54 to 0.75: we extract about
**28%** of what the pool we already build allows. **The wall is RANKING, and it always was.**
Every lever the old headline commissioned was a generation lever, and every one came back
inert: co-occurrence expansion +0.0021, InterPro graft negative on BP, ProtST as a feature
+0.0016. Those were not bad luck. **We were pushing a door that was already open.**

And LK-BPO, the cell this plan must win, has the largest untouched headroom in the whole
grid: **ceiling 0.8227, delivered 0.4402.**

## 1. Three facts that say the cells are winnable

1. **We beat TransFew where nothing is known.** NK-BPO: PROTEA **0.3374**, TransFew 0.3005
   (fourth). We win MF and CC in all three regimes. We lose only where the protein already
   knows something. **This is not a field ceiling, it is a specific deficiency**: exploiting
   prior knowledge. (`storage/regen_headline/CROSS_ASPECT_CHANNEL.md`)
2. **The pool double-counts instead of merging.** 40,192 `(protein, term)` pairs appear
   TWICE in the pk-bpo pool: once as a `knn`-only row, once as a `classifier`-only row.
   Exactly 9 rows of 616,223 ever carry both flags. **When the two generators agree, we do
   not record agreement, we record two half-views**: the knn row has a distance and no
   classifier score; the classifier row has a classifier score and `distance = NaN`. The
   strongest signal an ensemble has is the one our pool destroys. This also explains the
   "114 vs 62 candidates per query": it is duplication, not enrichment.
3. **On PK-BPO the whole apparatus is worth +0.004.** Deployed pipeline **0.2131**; a plain
   neighbour vote fraction over half the pool, no reranker, no 72 features, no training:
   **0.2092**. Both scored against the same full ground truth. Consistent with LOFO
   (`classifier` contributes **0.000** on PK-BPO) and with lab #113 (the reranker
   **regresses** on PK, -0.027 to -0.173).

**Read together: we are serving a vote counter with extra steps, over a pool that fragments
its own best evidence, while a 0.54-0.75 ceiling sits overhead.** Every technique lever is
negative because the recipe is at the optimum *of a badly posed problem*.

## 2. Phase 0: repair the pool (this is a defect, not an experiment)

**P0.1 Merge the generators.** One row per `(protein, term)` carrying BOTH sources'
evidence, plus an explicit `agreed_by_both` flag. Today that flag is unrepresentable.
- Measure first: the positive rate of agreed candidates vs single-source ones
  (`storage/cooc_experiment/dup_evidence_split.py`). If agreement predicts truth, the split
  is costing us directly.
- Then re-export and re-measure `f_micro_w` on all 9 cells. **Additive**: a new column and a
  deduplication, no schema break.
- **Gate:** if the merged pool does not move PK-BPO, the defect is cosmetic and we say so.

**P0.2 Ask what cafaeval does with duplicate pairs.** We currently hand it two predictions
for the same `(protein, term)` with different scores, for 13% of rows. Whatever it does
(first, last, max), the deployed number depends on it and nobody has checked. This is one
read of the source.

**P0.3 Kill the `rankpct` class of bug at the source.** `fuse_and_score.py:76` cost 0.088
by rescaling a score before a threshold-swept metric. Add a lint or a docstring rule: any
transform applied between the model and `cafa_eval` is part of the measurement.
(`storage/cooc_experiment/anchor_deployed_recipe.py` reproduces both halves.)

## 3. Phase 1: the error atlas (never done, cheap, frozen data)

We have never looked at **which proteins we fail**. Aggregate stratification exists; a
per-protein loss attribution does not. For LK-BPO and PK-BPO, for every protein:
delivered `f`, the pool's **per-protein oracle**, and therefore **its individual headroom**.

Then cut that headroom by every axis we can reach from frozen data:

| axis | source | the question it answers |
|---|---|---|
| protein length | `length` features | do we fail on long/multidomain proteins? (a chunk-attn arm already exists as a candidate) |
| term IA | LAFA `IA.tsv` | do we lose informative terms or trivial ones? IA-weighted F says only the first matters |
| term depth in the DAG | `go-basic.obo` | are we shallow-safe and deep-blind? |
| count of t0-known terms | `anc2vec_query_known_count` | does more prior knowledge help or hurt us? |
| neighbour identity | `neighbor_min_distance` | the twilight zone |
| taxon | `taxonomy_*` | is the loss clade-specific? |
| **pool recall per protein** | oracle vs propagated gt | separate "unreachable" from "misordered". **MEASURED and it barely matters**: only **2.3%** of PK proteins are truly unreachable and excusing them is worth **+0.0007**. Unreachability is per-TERM, not per-protein: 52% of the FN IA mass is not in the pool at all |

**Deliverable:** the concentration curve. **DONE 2026-07-17, and the gate fired: there is no
subpopulation.** The top 20% of proteins carry 45.2% of the headroom against a random control
of 20.5%; 51% of them are needed for 80%; **4,309 of 4,402 have positive headroom**. Length is
flat, t0-known count is flat, neighbour identity is mildly inverse, and taxon is **not
measurable at all** (the query taxid is absent from every frozen input). The only axes with a
gradient are pool recall (2.7x) and pool size (2.5x), both **pool** properties rather than
protein properties, and **headroom RISES where the pool is RICH**, which is the signature of
misordering rather than of generation. The missed mass is ordinary: 77% sits in IA band 1-6
and 71% at DAG depth 3-6, not in exotic deep leaves.

So the remaining PK-BPO loss is a **broad ranking deficit spread over nearly every protein**,
not a fixable tail. That kills the "find the hard subpopulation" strategy and redirects this
plan at the pool-level and scale-level levers below.

## 4. Phase 2: run TransFew ourselves

**Author constraint, 2026-07-17: do not contact An Phan or anyone at the benchmark until
the thesis ships.** The host route is closed, and it turns out to be unnecessary.

`CAFA_forever/modules/local/predictions.nf` has `PREDICT_TRANSFEW`, but it needs a
`containers/*.sif` that does not exist on this box, with no recipe and no registry. So we
build from source instead. **TransFew is public and reproducible** (verified 2026-07-17):
code at `github.com/BioinfoMachineLearning/TransFew`, **trained weights** and test samples
at `calla.rnet.missouri.edu/rnaminer/tfew/TFewDataset`, paper *Bioinformatics Advances*
2024, `vbae120`. Inference on 7,401 targets, not training.

**And the paper reframes every negative we hold.** Its stated mechanism: ESM2-t48 for the
sequence, **BioBert over the GO terms' textual definitions**, and a **GCN autoencoder over
the GO hierarchy**, combined by **cross-attention**, claiming better prediction of **rare
terms with few annotations** by *"facilitating annotation transfer between GO terms"*. That
is our exact gap. We have tested each of those three components, **separately, each bolted
onto the reranker**:

| their component | our equivalent test | result |
|---|---|---|
| GCN over the GO hierarchy | DAG proximity as a feature | **AUC 0.5501** |
| annotation transfer between terms | term co-occurrence | **+0.0021** |
| BioBert over GO text | GO-text BioBERT label basis | **+0.012 on LK-BPO** |

He learns them **jointly with the sequence**; we measured the ingredients one at a time,
cold. **Our negatives do not refute the signal, they refute the bolt-on.** That is not proof
that joint learning works, but it is the first coherent account of why our decomposition
found nothing.

One more tell: their backbone is **ESM2-t48**, and our own ablation says **Ankh beats
ESM2-3B** (family over size). If their sequence arm is weaker than ours and they still beat
us where prior knowledge exists, **it is not the backbone: it is the label channel**.

**What Phase 2 buys:** the only direct answer to "what do they get that we do not".
Everything else in this plan is introspection.

## 5. Phase 3: levers, ordered by what the evidence supports

Only after Phase 1 says where the loss lives.

- **P3.1 Recency of the training window.** The deployed reranker trains on v160->v227 pairs
  and is judged on v227->v230. Measured tonight: training on the eval window's own
  distribution is worth **~+0.057** (0.2704 vs 0.2131). That exact number is not available
  in production (it would be leakage), but **recency weighting of the training pairs is**,
  and it has never been tried. Largest untested legitimate lever we have.
- **P3.2 The cross-aspect channel.** LK-BPO is by definition "has MF/CC, lacks BP".
  `anc2vec_query` is **mute there by construction**; `anc2vec_neighbor` **hurts** (-0.0012);
  the only channel is `association`, a first-order co-occurrence **counter**, worth
  **+0.0037**. Reading the known SET instead of counting marginals adds **+0.029** over a
  window-frequency artefact, with near-duplicates excluded. That +0.029 is **optimistic**
  (its source is post-t0); the clean test needs a t0 corpus export for the 523 LK targets.
- **P3.3 The per-category gate**, properly. Lab #113 recommended raw-KNN on PK and never
  tested it on TEST. **It is not directly available**: the KNN pool alone reaches only
  **21.9%** of PK-BPO positives. But P0.1 changes that arithmetic, so revisit after.

**Do NOT revisit** (measured, on the board harness): binary objective (-0.071 at deployed
scope), per-cell training split (-0.016), within-protein rank features (0.1465), class
weighting (0.1441), dropping classifier candidates (flat, costs coverage), GO-DAG proximity
(AUC 0.5501), L10-std in production (-0.027), attention pooling, protst as a feature
(+0.0016), InterPro graft on BP (negative).

## 6. The rules this loop runs under, earned the hard way

1. **f_micro_w decides. Never AUC.** On this cell AUC has ordered levers BACKWARDS **four**
   times: counting 0.9393 vs set-level 0.8569, with set-level carrying double the f.
2. **Reproduce the anchor before building on it.** 0.1255 was manufactured by our own
   normalisation; its replacement 0.2131 shipped to three surfaces from a `/tmp` heredoc
   that was then deleted. Both now have a script.
3. **One variable per arm.** Five arms in this campaign changed two things at once, and
   **every one first read as a win**: objective+scope, model+pool, head+embedding,
   layer+normalisation, transfer+window.
4. **A big number is a suspect.** The cross-aspect result went +0.2125 -> +0.0626 -> +0.029
   under three successive controls. Budget the control before the celebration.
5. **Ask what a zero is made of.** `emb_pca` was called dead when it was all-NaN and had
   never been measured.

## 7. Honest scope

The gap is +0.072 / +0.076. Nothing measured so far reaches it: P3.2 is +0.029 optimistic,
P3.1 is unquantified, P0.1 is unknown. **This plan does not promise 9/9.** It promises that
we stop attacking the wrong wall, and that the next negative costs hours rather than weeks.

The fallback is not failure: a **characterised** frontier with a measured ceiling, a located
channel and a named defect is a defensible doctoral result. But the ceiling is 0.54-0.61 and
we deliver 0.2131, so the ambition is warranted.

Receipts: `storage/regen_headline/{CROSS_ASPECT_CHANNEL,BP_WALL_CHARACTERIZATION}.md`,
`storage/cooc_experiment/*.json`, `protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json`.

---

# Slices

### PKW.0 — Measure what the generator split costs

```yaml
id: PKW.0
phase: PKW
loop: prior-knowledge-wall
status: done
deps: []
acceptance: |-
  Quantify the concatenation defect on the pk-bpo pool: how many (protein,term)
  pairs are duplicated, whether agreement between the two generators predicts
  truth, and whether each row is blind to the other source.
estimated_hours: 1
priority: P0
tags: [pool, defect, measurement]
note: "2026-07-17 DONE. 40,192 pairs duplicated (13.0% of rows); every one is exactly one knn-only row + one classifier-only row; only 9 rows of 616,223 ever carry both flags. Agreement is 1.77x more likely to be TRUE (0.0398 vs 0.0225). Worse than missing data: the classifier row carries votes=0 and distance=NaN for a candidate the knn row says 16 neighbours voted, so the split writes CONTRADICTORY evidence. Receipt: storage/cooc_experiment/dup_evidence_split.{py,json}."
```

### PKW.1 — Merge the two candidate generators into one row

```yaml
id: PKW.1
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: [PKW.0]
acceptance: |-
  One row per (protein, term) carrying BOTH sources' evidence plus an explicit
  agreed_by_both flag, which is unrepresentable today. Re-export, re-measure
  f_micro_w on all 9 cells against the 0.2131 anchor.
  GATE: if merging does not move PK-BPO, record the defect as cosmetic and say so.
estimated_hours: 6
priority: P0
tags: [pool, export, additive]
```

### PKW.2 — What does cafaeval do with duplicate pairs?

```yaml
id: PKW.2
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: []
acceptance: |-
  We hand cafa_eval two predictions for the same (protein,term) with different
  scores on 13% of rows. Read the source and state which one wins (first/last/max).
  The deployed number depends on it and nobody has checked.
estimated_hours: 1
priority: P0
tags: [cafaeval, measurement]
```

### PKW.3 — The per-protein error atlas

```yaml
id: PKW.3
phase: PKW
loop: prior-knowledge-wall
status: done
deps: []
acceptance: |-
  For every LK-BPO and PK-BPO protein: delivered f, the pool's per-protein oracle,
  and its individual headroom. Cut the headroom by length, term IA, DAG depth,
  count of t0-known terms, neighbour identity, taxon, and above all by per-protein
  pool recall, so "unreachable" is never charged to the ranker.
  Deliverable: the concentration curve.
  GATE: if the loss is uniform on every axis there is no subpopulation to attack.
estimated_hours: 4
priority: P0
tags: [analysis, stratification, frozen-data]
note: "2026-07-17 DONE. Receipts storage/cooc_experiment/atlas_rebuild.py + atlas_atlas.json + atlas_per_protein.json (4,402 rows) + atlas_controls.py. Reproduces the anchor 0.2131@tau=0.393 and the label-built oracle 0.6077 exactly. (a) CORRECTS THE ORACLE: it was built from eval.parquet.label (DIRECT annotations) but cafaeval propagates gt, so pool terms that are ANCESTORS of true terms score TP (35,293 rows). oracle 0.6077 -> 0.7519, capture 35.1% -> 28.3%, unreachable 34.6% -> 2.3%. Caveat unresolved: the BP root is an ancestor of everything, so 'reachable' may be too generous and the true ceiling is likely between the two. (b) NO SUBPOPULATION: top 20% carry 45.2% (random control 20.5%), 51% of proteins needed for 80%, 4,309 of 4,402 have positive headroom. (c) CUTS: length FLAT, t0-known count FLAT, neighbour identity mild inverse, taxon NOT MEASURABLE (the query taxid is absent from every frozen input). Only pool recall (2.7x) and pool size (2.5x) carry gradient, and both are POOL properties. Headroom RISES where the pool is RICH = the signature of misordering. Missed mass is ordinary: 77% in IA band 1-6, 71% at DAG depth 3-6. (d) NEW BUG: neighbor_min_distance is byte-identical to distance on every non-NaN row; misnamed and miscomputed; may affect PROTEA#710's degeneracy check."
```

### PKW.4 — Run TransFew ourselves and diff it against us, protein by protein

```yaml
id: PKW.4
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: []
acceptance: |-
  AUTHOR CONSTRAINT 2026-07-17: do NOT contact An Phan or anyone at the benchmark
  until the thesis ships. The host route is closed. It is also unnecessary.
  TransFew is public and reproducible: code at
  github.com/BioinfoMachineLearning/TransFew, TRAINED WEIGHTS and test samples at
  calla.rnet.missouri.edu/rnaminer/tfew/TFewDataset, paper Bioinformatics Advances
  2024 vbae120. This is inference on our 7,401 targets, not training.
  (CAFA_forever/modules/local/predictions.nf has PREDICT_TRANSFEW but needs a
  containers/*.sif that does not exist on this box, with no recipe and no registry.
  Build from the repo instead.)
  Deliverable: their per-protein, per-term predictions on our frame, then the diff
  against ours on LK-BPO and PK-BPO. Which proteins do they win, which terms, and
  do those terms share an IA band, a DAG depth, or a prior-knowledge count?
  This is the only direct answer to "what do they get that we do not". Everything
  else in this plan is introspection.
estimated_hours: 12
priority: P1
tags: [head-to-head, transfew, inference]
```

### PKW.4b — The architectural read: we tested their ingredients, never their reaction

```yaml
id: PKW.4b
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: [PKW.4]
acceptance: |-
  TransFew's stated mechanism (paper, verified 2026-07-17): ESM2-t48 for the
  sequence, BioBert over GO TEXTUAL DEFINITIONS, and a GCN autoencoder over the GO
  HIERARCHY, combined by CROSS-ATTENTION, claiming better prediction of RARE terms
  with few annotations by "facilitating annotation transfer between GO terms".
  That is our exact gap. And we have tested each of its three components
  SEPARATELY, each bolted onto the reranker, each weak:
    * GO-DAG hierarchical proximity as a feature -> AUC 0.5501
    * term co-occurrence (annotation transfer) -> +0.0021
    * GO-text BioBERT label basis -> +0.012 on LK-BPO
  He learns them JOINTLY with the sequence; we measured the ingredients one by one,
  cold. Our negatives do not refute the signal, they refute the bolt-on.
  Note their backbone is ESM2-t48 while our own ablation says Ankh beats ESM2-3B
  (family > size). If their sequence arm is weaker than ours and they still win
  where prior knowledge exists, it is not the backbone: it is the label channel.
  Deliverable: decide, on the PKW.4 diff, whether a jointly-learned label channel
  is worth building or whether the diff points somewhere cheaper.
estimated_hours: 3
priority: P1
tags: [transfew, architecture, decision]
```

### PKW.5 — Recency weighting of the training window

```yaml
id: PKW.5
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: [PKW.3]
acceptance: |-
  The deployed reranker trains on v160->v227 and is judged on v227->v230. Training
  on the eval window's own distribution is worth ~+0.057 (0.2704 vs 0.2131), which
  is leakage in production, but RECENCY WEIGHTING of the training pairs is not, and
  has never been tried. Largest untested legitimate lever we hold.
  Measure in f_micro_w on the board harness, one variable.
estimated_hours: 4
priority: P1
tags: [reranker, temporal, untested]
```

### PKW.6 — The cross-aspect channel, without the leak

```yaml
id: PKW.6
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: [PKW.3]
acceptance: |-
  Export the t0 corpus (protein -> terms + aspect) for the 523 LK targets; the
  benchmark freezes knowledge only for eval targets and covers 103 of them, which
  is why this ran on PK. Rerun the nested arm sourcing the transfer from t0 ONLY.
  Then +0.029 becomes a production lever or nothing.
estimated_hours: 6
priority: P2
tags: [cross-aspect, export, leakage]
```

### PKW.7 — Lint the transform-before-metric class of bug

```yaml
id: PKW.7
phase: PKW
loop: prior-knowledge-wall
status: pending
deps: []
acceptance: |-
  fuse_and_score.py:76 cost 0.088 f_micro_w by rank-percentile rescaling a score
  before a threshold-swept metric, assumed harmless because monotone. Add a lint or
  an enforced docstring rule: any transform applied between the model and cafa_eval
  is part of the measurement. anchor_deployed_recipe.py reproduces both halves.
estimated_hours: 2
priority: P1
tags: [method, lint, receipts]
```
