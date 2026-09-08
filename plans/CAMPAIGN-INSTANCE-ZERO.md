# Instance zero: the nodes along the pipeline, and the first run

`EXPERIMENT-GRAPH.md` carries the shape. `CAMPAIGN-MODEL.md` carries the universe the shape
quantifies over: flows against configurations, regions and coordinates, affinity as a set,
channelling as a policy, floors per contrast class. This document is the instance. When a cohort,
a release or a budget changes, this file is rewritten and both of the others stand.

**What this instance is.** The node specifications, arranged along the pipeline, with each node's
question, fields, levels, incoming edges, gate, evaluation context, cost class and producer. Then
the first concrete run: simple scoring over the experimental window, end to end.

**What that first run is, said plainly at the top because it is the thing most easily
misdescribed.** It has **one flow**, neighbour transfer over an embedding. The eight levels it
compares are eight configurations of that one flow, not eight flows. Channelling them per region is
therefore a **rehearsal** of the channelling machinery on a cheap node, exactly as
`CAMPAIGN-MODEL.md` section 5.7 defines it. It produces **no affinity map**, because affinity is
degenerate in a single-flow pool. Its real products are three: a candidate table born with the
provenance the campaign needs, a per-panel variance for the configuration contrast class measured
rather than borrowed, and **the first measured variance for a per-region policy contrast**, which
is a class nothing in this project has ever measured and which every later channelling claim needs.

Every code claim below was read from `/home/xaxi/Thesis2/repositories/PROTEA/` on 2026-08-27. No
database was read. Where something is a database fact it says so and is marked as a precondition to
assert rather than a fact to rely on.

---

## 1. The frame, declared

The frame is a convention, not a decision the campaign takes by experiment. Its whole obligation is
to be written once and stamped on every row.

| field | value | producer |
|---|---|---|
| release pair, decision cohort | GOA 220 to GOA 227 | `generate_evaluation_set` |
| release pair, holdout cohort | GOA 227 to GOA 230 | not generated in this instance |
| window role, decision cohort | `"valid"` | `generate_evaluation_set`, payload field, validated to `{"valid","test"}` |
| gained side | additions only, experimental evidence at both ends, the thirteen codes of `protea/core/evidence_codes.py` plus their ECO synonyms | structural, `protea/core/evaluation.py:264` |
| "appears" primitive | absent at the opening, present at the closing (the two-endpoint rule) | `compute_evaluation_data_reconciled`; see 1.2 |
| propagation graph, both ends | one graph, `releases/2024-03-28` | `load_ontology_snapshot`, then the two native-snapshot payload fields |
| pivot: term universe, aspect map, terms of interest, scoring DAG | `releases/2025-07-22` | `generate_evaluation_set` pivot; `run_cafa_evaluation` reads the scoring OBO and the terms-of-interest list from the **same** pivot (`run_cafa_evaluation.py:394-405`, `:520`) |
| information accretion | one set per cohort, computed on the decision cohort's t0 annotation set against the pivot snapshot, regime `lafa` | `compute_information_accretion` |
| excluded-known base | the prior-knowledge closure at t0, passed as cafaeval's exclusion | structural, `_run_cafa_eval_driver.py:337-365`, `:166` |
| reference bank for coordinates | frozen, at a stated cut, and **not** the Bank node | **blocked**, see 3.2 |
| metric and rank | information-accretion weighted micro F per panel, at that panel's own maximising threshold, never pooled | `run_cafa_evaluation` / `batch_rescore_evaluation` |
| threshold grid | `th_step` 0.01 | payload default |
| band | `None`, ad-hoc unbanded | see 1.3 |

### 1.1 The two release dates the design turns on, and the asymmetry nobody stated

`docs/BAND_REGISTRY.md:37` records the upstream publication dates: **GOA 220 = 2024-04-16, GOA 226
= 2025-05-03, GOA 227 = 2025-09-04, GOA 229 = 2025-12-04, GOA 230 = 2026-03-04.** `refresh_goa_release_dates`
is still dispatched, because a date in a document is not a date on a row and the congruence
argument has to be checkable from the database, but it is not the blocker an earlier draft called
it.

Those dates carry a consequence no plan document has stated. **The decision cohort spans about
16.6 months and the holdout cohort spans 6.0 months**, a ratio of 2.77 in elapsed time. Most of the
size ratio between the two cohorts is therefore accumulation, not sampling. Every sentence in this
campaign of the form "the decision cohort is three times larger" is required to carry that clause,
and the transfer claim at the terminal is a transfer across two different accumulation lengths, not
two draws from one process.

### 1.2 The ground-truth construction, which is the single most consequential choice in the instance

The platform offers two code paths and the payload chooses between them by an equality test:

```
same_snapshot = old_native == new_native == pivot_id      # generate_evaluation_set.py:121
```

with `compute_evaluation_data` on the true branch and `compute_evaluation_data_reconciled` on the
false one. They are not two spellings of one protocol.

**The `same_snapshot` path does not propagate and is not identifier-safe.** It resolves every
annotation row's `go_term_id` through `_load_go_maps`, which builds `{go_term.id: go_id}` **scoped
to one snapshot** (`evaluation.py:201-209`), and drops any row whose term id is not in that map
(`:274-277`). `go_term.id` is unique per `(go_id, ontology_snapshot_id)`, and this campaign's
annotation sets do not all hang from one snapshot. Under that path a set bound to a different
snapshot resolves nothing, its side goes empty, every protein classifies as no-knowledge, and the
run succeeds. It also applies no ancestor closure at either end, deferring propagation to cafaeval.

**The reconciled path is identifier-safe** (`_load_experimental_raw_go_ids` joins `gt.id =
pga.go_term_id` with no snapshot predicate and recovers the accession text, `evaluation.py:472-482`)
and it propagates each side under an explicitly named graph before intersecting with the pivot
universe (`_reconcile_experimental_side`, `:509-539`).

**The construction this instance uses.** `old_native_snapshot_id = new_native_snapshot_id =
releases/2024-03-28`, `pivot_ontology_snapshot_id = releases/2025-07-22`, `window_role = "valid"`.
The two native ids are equal to each other and different from the pivot, which is the only
assignment that is simultaneously reconciled, identifier-safe, and closed under **one** graph at
both ends.

Why one graph at both ends is the point: the defect the platform names in its own payload
docstring, "the phantom gap: t0 propagated under a churned graph that marks pre-window experimental
annotations as new knowledge" (`generate_evaluation_set.py:29-37`), is an **asymmetry**. Close both
ends under one graph and a protein whose experimental set is unchanged has identical closures at
both ends, so it gains nothing. That is the whole of the fix, and it is what the two override
fields exist for.

Why the older graph propagates and the later one supplies the universe: the universe must contain
terms created inside the window or the gained side is truncated, so the pivot is the graph
congruent with the window's closing. The propagation graph is the one congruent with the window's
opening, so that t0 knowledge is closed under a graph that existed when it was curated.

**Two honest limits of this construction, both stated rather than argued away.**

**The residual, and it is confined to prior knowledge.** The gained side is a difference taken in
the closure space of the propagation graph, and cafaeval re-propagates under the pivot before
scoring. A pivot-ancestor of a gained term, reached by a parent edge added between the two graphs,
can therefore enter the truth although the protein already held it at t0. In no-knowledge the
protein holds nothing, and in limited knowledge it holds nothing in that aspect, so the residual
cannot arise there; in prior knowledge the excluded-known file removes it only where the exclusion
set is closed under the pivot, which it is not. **The residual is a prior-knowledge quantity, it is
unmeasured, and its producer does not exist.** Its precondition is named in 3.4.

**The alternative was considered and rejected.** Propagating both ends under the pivot graph itself
would make the exclusion set pivot-closed and drive the residual to zero, and it is not
expressible: setting all three ids equal selects the non-propagating branch, and setting the pivot
to a third graph makes the universe either narrower (deleting terms created inside the window) or
no different in practice. The rejection is recorded so the choice is visible as a choice.

**The primitive is the two-endpoint rule, and the stronger one is not wired.**
`protea/core/first_appearance.py` implements "present at the closing and never present at any
earlier cut", and the only importer of it in the repository is its own test file, while
`generate_evaluation_set` consumes the two-endpoint builders. Under the two-endpoint rule a term
withdrawn during the series and restored inside the window is counted as new knowledge while the
donor bank already holds it, which is a leak in the flattering direction. The producing module's
own docstring puts the rate on experimental evidence at about one per cent and states that it is
not uniform and tracks the contraction points. **This instance does not close that, carries the
residual as unmeasured rather than as a corrected average, and records the precondition**: wiring
first appearance requires ingesting the intermediate releases, which is a corpus decision and not a
scoring decision.

### 1.3 The band, and why it stays unset

`resolve_band` raises on an unknown band and `BANDS` holds exactly two entries, `v226` and `v227`
(`protea/core/band_registry.py:119-146`). Neither covers a window whose t0 is GOA 220, so this
instance runs `band=None` and `_enforce_band` is a no-op (`run_cafa_evaluation.py:797`).

**Registering a band for this window is not a one-row change and it cannot be made congruent.**
The band guard resolves an information-accretion artefact from the payload's `ia_file` or the
snapshot's `ia_url` and never from `information_accretion_set_id` (`run_cafa_evaluation.py:785-786`),
so the traceable route this instance uses would be seen as an absent artefact and rejected. The
cutoff guard additionally refuses an ontology release later than the band's `t0_cutoff`, and this
frame's pivot is a release well after GOA 220's date. So a band for this window would reject this
instance's own frame.

**The consequence is not cosmetic and it is stated with the guard off.** Without a band, an IA
resolution failure falls back to uniform information content and publishes an unweighted number
under a weighted name. This instance therefore asserts, as a gate, that the resolved IA artefact is
the one the frame declares, and refuses the batch otherwise. The precondition that would replace
the assertion with a guard is named in 3.4.

---

## 2. The two cohorts

**Decision cohort: GOA 220 to GOA 227, `window_role="valid"`.** Every comparison, every floor,
every threshold and every choice is made here.

**Holdout cohort: GOA 227 to GOA 230, `window_role="test"`.** Not generated, not evaluated, not
inspected in this instance. Section 6 lists what that means operationally.

### 2.1 Populations, and why this instance publishes its own

Three routes have measured this window and all three are superseded by the construction of 1.2, so
**every figure in this subsection is orientation only and none may be carried into a table.**

The raw route, which took the difference without propagating the pivot, gives per-panel unit counts
of 1,509 / 1,140 / 1,115 for no-knowledge BPO, MFO, CCO, 1,215 / 941 / 821 for limited knowledge,
and 7,136 / 3,908 / 4,623 for prior knowledge, totalling 22,408 protein-aspect units. The
reconciled route, which closed each end under its own snapshot four months apart, gives 1,509 /
1,129 / 1,116, 1,214 / 943 / 821, and 6,680 / 4,023 / 4,847, totalling 22,282. The six
low-knowledge panels agree to within twelve units because both faults require a non-empty
experimental closure at t0 in the aspect being counted, which no low-knowledge panel has. **The
three prior-knowledge panels disagree materially and neither route's figure may be cited.** The
one panel that was decomposed is prior-knowledge MFO, bounded between 3,446 and 3,908; the bound
belongs to that panel and not to prior-knowledge BPO, which two published drafts have swapped.

Instance zero's construction is a **third route**. It publishes its own nine counts from its own
ground-truth artefact under `eval_groundtruth/{eval_set_id}/groundtruth.parquet`
(`evaluation.py:768-770`) and adopts none of the above. Every gate in section 5 is computed after
that artefact exists, not before.

For orientation, the holdout cohort's low-knowledge panels have been measured at 436 / 346 / 275
and 540 / 244 / 266 by one route and at 437 / 349 / 275 and 539 / 245 / 266 by the other; its
prior-knowledge panels disagree by more than a third between routes. None of this is used here.

### 2.2 Disjointness, in both senses

**Pairs.** The intersection of gained protein-term pairs between the two windows is exactly zero,
verified, and it is a property of the construction because the windows abut.

**Proteins.** 2,374 proteins appear in both cohorts, which is 26.6 per cent of the holdout cohort's
8,910 delta proteins. **The holdout is blind to the pairs it will be scored on and is not blind to
the proteins.** For roughly a quarter of holdout proteins, that same protein's units in the
decision cohort took part in every threshold and every choice. This belongs in the sealed plan
before the holdout is touched, together with the declaration of whether the transfer claim is made
on all units or on the protein-disjoint subset. Instance zero does not make that declaration,
because instance zero does not touch the holdout; it records the number so the seal cannot be
written without it.

### 2.3 What the previous campaign's numbers may and may not do here

Every stored evaluation result of the previous campaign is being deleted, and roughly two thirds of
its decision-bearing comparisons sat on the union window GOA 220 to GOA 230, which contains the
holdout. **No quantity measured on the union may seed a prior over the holdout cohort.** The floor
census figures quoted in section 5 are used to size expectations and to declare non-resolution in
advance; they are never used as floors, they are stated with the population they were measured on,
and they will not be reproducible after the wipe. That last property is a defect of the record, not
of the numbers, and it is one of the reasons instance zero measures its own variances.

---

## 3. The nodes along the pipeline

Strengths are as defined in `EXPERIMENT-GRAPH.md`: measured, chosen, inherited, unpowered, blocked.

### 3.0 Frame

Source node, cardinality one, edges to every other node. Declared in section 1. Its obligation is
the stamp, and the stamp is incomplete in the schema: `EvaluationResult` carries `frame`,
`temporal_window`, `arms_enabled` and `leakage_role` (`evaluation_result.py:143-146`) and has no
column for `window_role`, `protein_subset_label`, the fold triple, `max_terms`, `max_distance`, the
IA set or the band. The payload carries all of those and the job row is the only place they land,
and the job table is being deleted. **Code change C4 in 3.4 writes them into the result's existing
`results` JSONB.** Until it lands, a fold result and a full-cohort result are indistinguishable
after the fact, which is the exact failure the `protein_subset_label` validator was written to
prevent.

`leakage_role` derives from the evaluation set's `window_role` by `{"valid": "select", "test":
"test"}` (`run_cafa_evaluation.py:444-446`), so stamping the window once stamps every result. Its
vocabulary has a third value, `probe`, for exploratory runs; instance zero produces none and any
that are produced later must be declared, because a `probe` row is invisible to a guard that
counts only `select` and `test`.

`audit_evaluation_frames` counts `frame`, `temporal_window`, `leakage_role`, `arms_enabled` and
`job_id`. It is dispatched before stage C as the zero baseline and after stage C as a forward
guard. **The guard is on `leakage_role` and on the join to `window_role="valid"`, not on `frame`
alone**, because `frame` is a two-value harness label and a batch in which every row reads
`internal` passes a `with_frame == n_rows` check while carrying no cohort information at all.

### 3.1 Substrate

**Question.** Which stored vector space the neighbour transfer runs in, given a fixed bank and a
fixed retriever.

**Fields.** One payload field, `PredictGOTermsPayload.embedding_config_id`, which binds eleven
recipe fields on `EmbeddingConfig` (`model_name`, `model_backend`, `layer_indices`, `layer_agg`,
`pooling`, `normalize_residues`, `normalize`, `embedding_scale`, `max_length`, `use_chunking`,
`chunk_size`). They cannot be moved apart because the stored vector is their joint product and no
intermediate is stored: no per-residue tensor, no per-layer stack, no pre-pooling state. Changing
any of them is a corpus forward pass, not a re-read.

**Levels.** The pretrained representations complete over the corpus, plus the derived ones fitted
at the window's t0. Excluded by declaration rather than by measurement: the text-aligned
representation, whose retrieval advantage is text leakage (nine of nine paired intervals separating
on described proteins, zero of nine on the undescribed), which is reported and never ranked; any
configuration that is incomplete over the corpus, because a level scored against a smaller donor
bank is a bank comparison wearing a substrate label; and every chunked variant, which has no input,
since no configuration enables chunking and every stored row carries a null chunk end index.

**Incoming edges.** Frame (declared). Corpus inventory (the level set, at zero accelerator cost).
Closed prior axes, which reduce the level set rather than adding to it: last layer wins at every
measured depth, mean pooling, quantise after training. Retriever, which carries the depth the
comparison is read at, and Bank, which carries which donors exist to be retrieved.

**Gate.** Selection, because the winner is chosen after the numbers are visible. Class 2 of
`CAMPAIGN-MODEL.md` section 7.2, one flow with retrieval changed. Its variance has never been
measured and this node measures it from its own first pair before any verdict is taken.

**Two constraints that make this node's verdict a set rather than a winner, both known in
advance.** The median gap between adjacent levels on this class, measured on the previous
campaign's rows and therefore quoted as an expectation and not as a floor, was 0.0022 of
information-accretion-weighted micro F over 96 groups on the union window. Against the derived
minimum detectable effect on any panel of this cohort, that gap needs a population an order of
magnitude larger than the largest panel holds. **The honest closure is an admissible set, and the
count of proteins that would be needed to resolve the adjacent pairs is published beside it as a
request for data**, per `EXPERIMENT-GRAPH.md` section 8.

**A coordinate restriction specific to this node.** The length coordinate's boundaries are model
context limits, so its levels mean different things for configurations with different truncation
points. A substrate comparison across configurations with different `max_length` is a coverage
comparison inside every band above the smaller limit, not a representation comparison. This node
either restricts its levels to configurations sharing a `max_length` or reports length only over
the bands where every level saw the whole sequence, and says which.

**Evaluation context.** Bank and retriever at declared values; scoring at the identity level and
all levels reported as a robustness panel; no re-ranker, which is a severe conditioning and not a
neutral hold, since re-ranking the same neighbours is worth an order of magnitude more than the
encoder axis on this project's own record; every generator flag off.

**Cost class.** Expensive. One prediction set per level, each a coordinator dispatch fanning to
internal batch messages. This node may see the fan, because a substrate ranking measured against
one representative is not a ranking, and the efficient dispatch order is by configuration, since
the reference pool is cached per `(embedding_config, annotation_set, aspect separation, dtype
needs, policy discriminator)` and switching configurations on a warm worker evicts it.

**Producer.** `predict_go_terms`, then `batch_rescore_evaluation`, then `stratify_evaluation`. No
blocked artefact, given the frame chain of 5.1.

### 3.2 Bank

**Question.** Which annotated proteins, at the window's t0, may donate a term to a query.

**Fields.** `PredictGOTermsPayload.donor_policy`, with `reviewed_only`, `evidence_codes` and
`exclude_reference_prefixes`. The temporal cut is frame, not a level.

**Two findings that change what the levels mean, both verified in code.**

**The donor policy restricts which proteins may donate, not which annotations they donate.**
`_restrict_annotations` is called from exactly one place, `_reference_pool_query`
(`_batch_op_reference.py`), which takes a distinct over protein accessions. The annotations
actually transferred are loaded by `_collect_aspect_annotations` and by the unified path's
`_fetch_annotation_chunk`, and both filter on annotation set, aspect and the NOT qualifier and on
nothing else. So a policy naming experimental evidence codes admits a protein holding at least one
such annotation and then transfers everything that protein holds in the aspect, electronic
annotations included. **The level's name is "a donor holding at least one annotation of the named
kind, giving everything it has", and calling it an experimental-evidence bank without that clause
is a declaration gap.** The contract docstring promises annotation-level filtering, so contract and
implementation disagree and the gap is on the implementation side.

**Nothing excludes the query from its own donor pool.** `search_knn` in
`protea-method/src/protea_method/knn_search.py:71-108` takes query embeddings, reference
embeddings, accessions and a depth, with no identity argument and no exclusion, and nothing under
`protea/core/operations/predict_go_terms/` supplies one. The stratifier fixes it on its own side
and does so **by sequence and not by accession**, because two accessions can carry one sequence
(`_run_cafa_strata.py:26-31`, `:44`, and `Protein.sequence_id` is deliberately non-unique).

The consequence composes with the experimental baseline into a scored path, derived from code
rather than measured. A term the query held electronically at t0 and gained experimentally inside
the window is on the gained side; the query is therefore in the t0 annotation set and in that
aspect's index, since aspect membership ignores evidence; it retrieves itself at distance zero and
donates the term; and the excluded-known file removes only the query's **experimental** t0 terms,
so the promoted term is not excluded. **Promotions are one unit in five of this window: 7,002
protein-term pairs and 4,501 protein-aspect units against a total of 22,408 under the raw route or
22,282 under the reconciled one, either way about twenty per cent.** That is not a corner case and
it is not a Bank-node qualifier. It is a first-order threat to every number every node produces,
and it is handled as code change C8 in 3.4 rather than as a check to run afterwards.

**Levels.** A permissive pool, an evidence-gated pool, a reviewed-only pool, and a pool excluding
sequence-derived provenance, each with the clause above attached to its name. Three further levels
have no field at all and are blocked: deduplication of isoform-redundant donors sharing one
sequence, exclusion of uncharacterised canonical donors, and self-donor exclusion until C8 lands.
The first two together are a measured 10.83 per cent of a production index, 7.77 isoform-only and
3.06 uncharacterised, the latter enriched in the twilight homology band.

**The confound the record already paid for.** In the previous campaign the evidence regime never
moved independently of the window: one pool was attached to one window and the other to the other,
so regime and window were one axis and no comparison could attribute a difference. Two dispatches
at matched window separate them, and that is the one question this node can close. It cannot close
under C8's absence, because the two regimes differ in exactly whether an electronically annotated
protein is in the pool, which is exactly the population whose self hit carries a promoted term.

**Gate.** Declared comparison, not selection: the levels are named in advance. Class 2. The class
has no measured pairs and its variance comes from the first pair's per-protein artefacts.

**Cost class.** Must be measured against one substrate and one depth, because each policy
materialises and caches its own pool and each level retrieves largely different donors, so the
alignment cache does not repay across levels the way it repays across substrates.

**Producer.** `predict_go_terms` with the policy set, no code change, for the four levels that have
fields. Blocked for the three that do not, preconditions named above.

### 3.3 Retriever

**Question.** How many donors, and how far out, feed the transfer, given a space and a pool.

**Fields.** `limit_per_entry` (the depth), `distance_threshold`, `aspect_separated_knn`, `metric`.
They cannot be moved apart for three reasons. Aspect separation multiplies the depth, because with
it on the depth is drawn per aspect from three pools, so a stated depth is three times as many
donor slots. The threshold and the count define one neighbourhood, whichever binds first. And the
metric changes the ordering the count truncates.

**Depth is a field of this node and each depth is its own prediction set.** `neighbor_vote_fraction`
is written as `vote_count / k_limit` at write time (`_leaf_record_builder.py:435`), and
`vote_count`, `neighbor_mean_distance`, `neighbor_distance_std` and the taxonomic voter fractions
are aggregates over the whole retrieved list (`_knn_transfer_runner.py:479-517`). No payload field
on either evaluation writer caps the stored rank. **This corrects
`EXPERIMENT-GRAPH-INSTANCE.md` section 3, which states that every smaller depth is a truncation of
a list already written.** The correction is partial and the partial form is the useful one: the
candidate set at a smaller depth is exactly the rows whose stored rank is at or below it, and every
donor-anchored column is invariant under that truncation, because neighbours are consumed in rank
order and the first one carrying a term owns the row. **Depth is a free axis for the presets that
read only donor-anchored signals and a paid axis for the vote-weighted ones.** A re-read at a
smaller depth requires a payload field that does not exist, plus two refusals: one against pairing
it with a vote-weighted scoring config, and one against a prediction set whose reranker-feature
flag was off, since the stored rank then defaults to one on every row and the truncation is a
silent no-op.

**The gate has a structural hazard that must be stated before this node is measured.** Under a
scoring configuration whose only weighted signal is the embedding similarity of the winning donor,
increasing the depth appends terms to the tail of the ranking and changes nothing above it: a term
already carried keeps its nearest carrier, and a newly reachable term enters at a score no higher
than any term carried by a nearer donor. Every operating point available at the smaller depth is
still available at the larger one, so the panel maximum is non-decreasing in depth **by
construction**. Ranking this node under that configuration therefore selects the largest depth
before the run, and it does so for a reason that is a theorem rather than a measurement. This is
the retracted experiment of the previous campaign re-dispatched: that experiment ran with the
scoring configuration unset, and an unset configuration is numerically identical to the
embedding-only preset. **This node's rank is declared under a configuration that reads the vote
fraction, and the embedding-only result is reported as a robustness panel.**

A second hazard on the same signal: `vote_count` counts annotations rather than neighbours and the
fraction is clipped at one, so it saturates whenever donors carry a term under several evidence
codes. Saturation frequency depends on the donor pool's evidence composition, which is the Bank
node. The depth axis and the bank axis are therefore not independent on the very signal this
node's rank must read, and the instance reports the saturated share per level beside the rank.

**Cost class.** One prediction set per depth, plus an interaction check at two substrates and two
depths, since the depth optimum is substrate-dependent by measurement. Successive depths on one
substrate retrieve nested neighbour sets, so the alignment cache pays only for the pairs a larger
depth adds.

**Producer.** All fields are payload fields on a registered operation. The re-read cap is a code
change; the sweeps over evaluation-time post-filters are payload fields on a registered evaluation
operation and cost no accelerator.

### 3.4 Generator

**Question.** What proposes candidates that neighbour retrieval cannot reach, and in which regions
does each such source reach truth no other source reaches.

**This node is blocked, and the reason an earlier draft gave was not the binding one.**

Only two code paths in the entire tree append a candidate: `_merge_classifier_preds`
(`predict_go_terms/_classifier.py:211`) and `noisy_or_graft_bp` (`_interpro_graft.py:135`). Every
other post-retrieval mechanism, the self prior, term association and the lineage family, writes a
field on a candidate retrieval already found and proposes nothing. Those are flows **whose
generator half is unbuilt**, carried as blocked edges, not renamed features.

**The binding constraint is that no scorer can read a generator's signal.** `_vectorized_scores`
reads exactly ten named signals (`_run_cafa_artifacts.py:489-500`) and `_SIGNAL_TO_COLUMN` backs
six of them (`_scoring_validation_helpers.py:25-33`). `classifier_score`, `self_prior_score` and
the association columns are in neither list. A classifier-proposed candidate carries a not-a-number
distance and no vote fraction by construction (`_classifier.py:216-228`), so under any linear
configuration both its weighted signals are absent, the weight total is zero, and the score is
exactly zero, which in the evaluator is indistinguishable from a prediction never made. Under a
null configuration the same candidate scores the **maximum**, because the fallback treats a
not-a-number distance as zero distance (`_run_cafa_artifacts.py:479-480`). And any non-null
evaluation-time distance cap deletes every such candidate before scoring, because a not-a-number
comparison is false.

So the Generator node has three preconditions, not one, and they compose:

1. **A second generator half that runs.** Both existing ones are blocked on artefacts: the
   classifier on a term-embedding file with no producer anywhere in the checkout and a checkpoint
   not on this disk, the domain signature on a scanner that is not installed. The graft is
   additionally gated: without a per-setting re-ranker it is skipped with a warning while the
   declared flag still records it as on, so a source that never ran would be published as a source
   measured and found worthless.
2. **A combiner whose signal vocabulary reaches it.** Either the linear scorer's vocabulary is
   extended in all four places (`DEFAULT_WEIGHTS`, `_SIGNAL_TO_COLUMN`, `_resolve_signal_values`,
   `_vectorized_scores`), or a booster exists. Neither is the case.
3. **Candidate provenance as a set**, so unique reach is computable once two proposers exist.

**Ordering consequence, and it inverts a list two earlier drafts published.** Provenance is not
what everything waits behind. In a single-generator system a provenance column writes one constant
in every row and measures nothing. **The flow-admission contrast class is blocked on (1) and (2),
and provenance is what makes the resulting pair readable.** All three are needed and none
substitutes for another. Provenance is landed in instance zero anyway, and for a different reason:
the candidate table is the only accelerator-bound artefact in the instance, and a column added
later is a column backfilled by a re-run.

**A structural table this instance corrects.** The audit's structural-affinity matrix, and
`EXPERIMENT-GRAPH-INSTANCE.md` section 3bis, list the query's own prior as mute in no-knowledge and
limited knowledge. It is not. `apply_self_prior` reads the query's own **non-experimental**
pre-cutoff annotations (`_post_knn_pipeline.py:176-190`, `_own_nonexp_terms:257-279`) and applies
no aspect restriction, while no-knowledge is defined by the absence of **experimental** annotations
(`evaluation.py:11-22`). Its boundary is a coverage property orthogonal to the partition and must
be measured, not derived. Lineage and term association remain mute in no-knowledge, lineage by an
explicit zero and association because it scores against terms the protein holds. That distinction
matters downstream: an explicit zero leaves the combiner's weighted average unchanged, and a
missing value renormalises it over the surviving signals, which is a different score.

**Producer.** Blocked, with the preconditions above.

### 3.5 Scoring

**Question.** Given a fixed candidate list, which order and which operating point maximise the
panel's rank.

**Fields.** `scoring_config_id`, singular, passed as a list to `batch_rescore_evaluation`. Not
fields of this node: the neighbourhood depth, which belongs to the Retriever, and the
evaluation-time distance cap, which is a re-read knob and is internally inconsistent with any
vote-weighted configuration because it prunes candidates without recomputing the vote denominator.

**Levels.** `PRESET_CONFIGS` holds **seven**: `embedding_only`, `vote_fraction`, `alignment_only`,
`embedding_plus_alignment`, `embedding_plus_vote`, `evidence_veto`, `composite`
(`protea/services/_scoring_models.py:372-494`). The previous campaign's eighth database row was
numerically identical to `embedding_only`, which is what a null configuration also is, so counting
either as a level inflates the fan with a duplicate. Instance zero adds one declared eighth level,
defined in 5.4.

**Four weights in `DEFAULT_WEIGHTS` are untraversable and must be marked before anyone instantiates
them**: `coverage`, `ref_annotation_density`, `anc2vec_neighbor_cos` and `anc2vec_neighbor_maxcos`
are outside `_SIGNAL_TO_COLUMN`, so a configuration weighting them passes validation with no check
performed and returns zero. None of the seven presets weights any of them, so instance zero does
not fire it; the refusal is code change C7.

**A second gap in the same guard.** `compute_missing_signals` flags a signal only when its column
is null in every row and is reachable only from the API router, not from either evaluation
operation. A configuration weighting alignment identity against a prediction set built without
alignments therefore scores zero everywhere with no error. Instance zero sets the producing flags
explicitly and asserts them rather than relying on the guard.

**Preset and depth interact analytically, not merely empirically.** `embedding_only` places no
weight on the vote fraction so its score is independent of the depth; `vote_fraction` places all
weight there so its score is a pure function of the depth. A preset ranking read at one depth is a
statement about that depth. This node's outgoing edge therefore reports whether the ordering is
stable across at least two depths, or declares itself conditional on one and says so.

**Gate.** Resolution for each declared adjacent pair; selection if a leader is taken. Class 1, the
only class this project has ever estimated, and the estimate is indirect and single: a within-fold
standard deviation of 0.0034 over a tenth-cohort fold in a prefilter study, rescaled to a paired
standard deviation of 0.081, on a population and a metric the source does not state. The class the
presets actually run is a **third** class, since two presets can share no non-zero weight, so even
this estimate is a borrowing. Instance zero measures the class directly.

**What is known in advance about this node's resolution.** The median gap between adjacent presets,
measured on the previous campaign's rows over 100 groups on the union window, was 0.0030 of
weighted micro F, and the group spread of 0.0313 is dominated by two degenerate levels. Read
against the minimum detectable effect derived on this window's measured populations at the low end
of the contrast classes, that adjacent gap sits below the detectable effect in **all nine panels**.
**The expected outcome of this node is an edge of multiplicity, and resolution is the surprise.**
That is a legitimate node and a legitimate edge, and it is the reason this is the right node on
which to rehearse the channelling machinery rather than the wrong node to be disappointed by.

**Cost class.** Cheap once its precondition is met, and permitted to evaluate the whole incoming
set: one `batch_rescore_evaluation` dispatch takes one prediction set and a list of configurations,
loads ground truth, ontology and information accretion once, and re-scores in numpy. **The
precondition is the whole cost**: in the clean state there are no stored candidates, so the
cheapest node in the graph sits behind the most expensive stage.

**Producer.** `batch_rescore_evaluation`, registered. The configurations themselves are seeded by
an API endpoint and not by a registered operation, which is a hole in the storage invariant and is
recorded as one in 5.1.

### 3.6 Features

**Question.** Which signal families the scorer may read, and which contribute above their region's
floor.

**Blocked, and structurally rather than by scheduling.** The linear scorer reads ten named signals;
the feature schema declares families covering many more columns; and there is no scorer in the
platform that consumes a family list. **The consumer of this node's output is a booster, and there
is no booster.** A node whose only consumer does not exist cannot be measured, only prepared.

Preparation is nonetheless concrete, and per family. Available the moment a prediction set exists:
the neighbour, distance and vote families, length, annotation metadata, term context, the
principal-component family, and the alignment families at the cost of the alignment stage. Available
at one extra dispatch: the association family, behind `build_go_cooccurrence`. Available and
constrained by declaration: the text-aligned family, forbidden as a retrieval space on the leakage
finding and admissible only as a re-ranker feature with that constraint written into the level.
Structurally mute in no-knowledge: lineage, by explicit zero. Not mute in no-knowledge, correcting
the record: the query's own prior. Blocked with no producer: the term-embedding families, whose
input file has no writer anywhere and whose two implementations disagree, one computing the value
and the other returning a stub. Blocked on the Generator: the classifier and domain-signature
families.

**The instrument is replaced, not supplemented.** Leave-one-family-out measures marginal
contribution given a combiner. Where it is used at all, it is paired with unique reach and
exploited fraction computed on the candidate table before any combiner runs, and no family is
admitted on a marginal test alone.

### 3.7 Re-ranking

**Question.** What learned ranking adds over the tuned linear score at fixed candidates, and how
deep a shortlist it needs.

**Blocked in a different sense from the Generator**: the trainer and its inputs exist, and nothing
has been trained on this platform. Four seams close first, and three of them are structural rather
than missing files.

No training operation is registered in PROTEA at all; they were deliberately deregistered toward
the offline lab (`operation_catalog.py`). Registration of a trained model back into PROTEA is an
API endpoint, not an operation. Together with the preset seeding and the query-set registration
that is **three API-only seams**, which is a pattern and not three exceptions: either they become
operations or the storage invariant is amended to name them.

The fourth seam is the one nobody has stated: **a booster used to take decisions on the decision
cohort must not be fitted on that cohort's own labels**, and the split registry cannot even name a
window strictly before this cohort's t0, because its release list begins later. Two admissible
resolutions, which must not be conflated: ingest at least one release pair before the window's
opening and fit there, which is real ingestion work; or fit on a protein-disjoint internal split of
the window, declare it on the payload, and label every resulting number a within-window estimate.
The platform's internal split partitions by a hash of the accession with no sequence clustering, so
near-identical sequences land on both sides; that limitation is stated wherever the split is used.

**A silent-degradation trap on this node's own guard.** The predictor refuses a booster whose
expected feature schema does not match the live pipeline and falls back to no re-ranking. A booster
trained on families the payload does not produce therefore completes successfully and scores
nothing, and the result is indistinguishable from the reference level. A result row whose booster
fell back is refused, not stamped.

### 3.8 Combination

**Question.** Given several flows that reach a region, does combining their proposals beat the best
single one there, under a nameable mechanism.

**Blocked, and its own null level is the only computable one today.** Combination's levels are a
union of candidates scored by a maximum, a noisy-or, a fixed blend or a learned stacker over
per-flow scores after per-flow calibration. Three constraints, each of which has already cost this
project a result.

**The linear scorer cannot express any of them.** Its ten signals contain no flow score, and the
evaluator recomputes a score from the base frame's columns for every configuration it is handed. A
combined candidate set fed to the ordinary evaluator is therefore rescored by the neighbour scorer
and every combination level equals its own null level to the last digit, with the pipeline green. A
combination is a new artefact with its own producer, not a new preset.

**The base frame deduplicates on protein and term, keeping the smallest distance**
(`_run_cafa_artifacts.py:332-352`), and a not-a-number distance sorts last, so a candidate proposed
by two flows collapses to the neighbour row and the second proposer's contribution disappears
before scoring. That is exactly the fact unique reach reads.

**Any calibration ships an identity control**, run at the setting where the transform must be the
identity, reproducing the uncalibrated baseline exactly. This project has once manufactured a
baseline with a normalisation and invalidated every lever measured against it.

**Producer.** `assemble_combined_predictions`, a new registered operation writing one prediction
set whose candidate rows carry the union of their members' proposer bits. Blocked, with three
schema preconditions on the prediction set and the candidate row: the embedding configuration, the
ontology snapshot and the depth are all non-null on the prediction set, and the distance is
non-null on the candidate row, so a combined set has no honest value for any of them. The existing
domain-signature path fills the depth with a zero sentinel and a real configuration id, which is
the modelling failure to be fixed rather than the precedent to be copied.

### 3.9 Routing

**Question.** Should different regions be served by different flows, and does the resulting policy
beat the best constant policy.

**The only node whose output is a policy rather than a value, and the only node that reads
regions.** Its fields are the region granularity, the admission rule and the fallback. The
combination rule is held at the Combination winner and is not a field here, or the node becomes a
search over rules times regions.

**The routing family is a partition and not a cover.** Panels, then panels crossed with exactly one
nominated coordinate, with hierarchical collapse to the parent wherever a sub-region's population
does not clear the admission floor. Every other coordinate is reporting only.

**Two prohibitions, both definitional.** The region key must be computable at prediction time from
information available before the window's closing, through the leakage-clean path the platform
already has for the knowledge category, and never from the evaluation's own artefacts even where
the two agree numerically; a policy keyed on the benchmark's artefacts is unbuildable outside the
benchmark while producing identical numbers inside it, which is the worst kind of failure because
it is invisible. And a flow may not be credited with competence on the coordinate its own statistic
defines, which forbids any competence claim about neighbour transfer along a homology or reach
band, in either direction.

**The mechanism of channelling exists in the platform in two special cases**, both written by hand
rather than derived: a nested category-by-aspect mapping of re-rankers on the evaluation payload,
and a per-category classifier-head routing switch in the serve path. What does not exist is the
policy as a declared, derived, content-addressed artefact.

**Producer.** `measure_flow_affinity` and `derive_routing_policy`, both new, both read-only, both
content-addressed on the pattern an existing gate-bundle export already establishes. Blocked.

**In instance zero this node runs, and it runs on configurations rather than on flows.** That is
the rehearsal, section 5.6.

---

## 4. What has to exist before instance zero can be dispatched

### 4.1 Preconditions to assert, not to assume

| # | precondition | how it is settled |
|---|---|---|
| P1 | no `EvaluationSet` row exists for the pair (GOA 220, GOA 227) | database fact. The pair is UNIQUE at the schema level and `generate_evaluation_set` **raises** when a native-snapshot override is supplied and a row exists (`:194-199`). If a row survived the wipe, instance zero is blocked on a delete, and **no registered operation deletes an evaluation set**. Named precondition: a `delete_evaluation_set` producer, or confirmation the row is gone |
| P2 | annotation sets for GOA 220 and GOA 227 exist, with their own ontology snapshots recorded | database fact |
| P3 | the ontology snapshot `releases/2024-03-28` exists | `load_ontology_snapshot`, idempotent on the release header. Dispatched regardless |
| P4 | the ontology snapshot `releases/2025-07-22` exists | as above |
| P5 | embedding coverage of the window's delta proteins under the chosen configuration | the coordinator's own resolved-query count. Instance zero **freezes the query set to the intersection of the delta and the resolved queries** before dispatching, rather than refusing a level after the fact, so that every level is scored on one population by construction |
| P6 | the installed evaluator exposes the per-protein sink | code fact, and the two virtual environments on this machine disagree: one build contains the sink and the other does not. Every interval in section 5 depends on it. Assert the installed revision before stage C |
| P7 | whether the pairwise alignment cache survives the wipe | it is on neither the survivor list nor the deletion list of the brief. It is keyed on the two sequence hashes and on nothing else (`protea/core/alignment_cache.py:1-18`), alignments were profiled at 63 per cent of a prediction batch, and 1,063 of 1,216 pairs recurred across encoders on the previous grid. Instance zero runs one configuration so it pays the first fill either way; **the answer changes the cost of every later instance by roughly a factor of three and must be decided explicitly rather than by omission** |

### 4.2 Code changes, each with the stage it blocks

| # | change | blocks |
|---|---|---|
| C1 | the per-protein evaluation artefact writes the metric's components across the **whole threshold grid**, not at one threshold. Today the sink is sliced at the threshold taken from the unweighted protein-mean best frame (`parse_results`, `_run_cafa_artifacts.py:688-694`, consumed at `_run_cafa_eval_driver.py:220-226`), while the evaluator selects each metric's optimum independently (`idxmax` per metric). So the stored per-protein rows recompose the weighted micro metric **at the wrong threshold**, which is the disagreement `EXPERIMENT-GRAPH-INSTANCE.md` section 6 records without a cause. It is a threshold mismatch, not a formula error and not a corrupt file, and the fix is one line plus regeneration | stage C. Must land **before the first evaluation**, because after the wipe there is nothing to regenerate |
| C2 | `PredictionSet.meta` records the retrieval frame: donor policy, aspect separation, metric, backend, and every producer flag. Today the coordinator writes `meta={}` (`predict_go_terms/_coordinator.py:170-178`) and those values live only on the job payload, which is being deleted | stage B |
| C3 | `proposed_by` and `scored_by` on the candidate row, as append-only ordered bitmasks over a flow registry, with the donor accession made nullable and meaning only the donor; plus a golden test pinning the **ordered** assignment, since a digest over a sorted set cannot detect a reassignment | stage B, and it is landed now because the candidate table is the instance's only accelerator-bound artefact |
| C4 | a `provenance` block in the evaluation result's existing `results` JSONB carrying `window_role`, the fold triple, the subset label, the term and distance caps, the information-accretion set, the band and the observed proposer set; and `arms_enabled` derived from that set rather than hardcoded (`run_cafa_evaluation.py:448-462`) | stage C |
| C5 | the stratifier places a protein it cannot resolve into the named level rather than dropping it. Today `_strata_for_rows` skips any row with no length, no aspect or no non-self donor (`stratify_evaluation.py:100-108`), and the neighbourhood is computed from the run under test, so the reported population of a stratum is a property of the arm | stage D, or the length tables carry their own coverage denominator and are marked non-portable |
| C6 | `compare_paired_panels`, a registered read-only operation over two results' per-protein artefacts, emitting a bias-corrected accelerated bootstrap over **proteins** of the paired difference of the panel's ratio-of-sums, with each system's operating point re-selected inside each resample, and reporting the point estimate, the interval, the population and the minimum detectable effect. **No interval producer of any kind exists in `protea/` today** | stage E. Without it the gates in 5.5 cannot be read |
| C7 | two refusals in the scoring path: a configuration weighting a signal with no backing column, and a null `scoring_config_id` on any evaluation this campaign records | stage C |
| C8 | self-donor exclusion as a donor-policy field, applied **by sequence identifier and not by accession**, matching the rule the stratifier already applies | stage B, and it is a hard precondition rather than an improvement, for the reason in 3.2 |

Three of these are small. C1 and C6 are the instrument, C8 is a correctness fix on the population,
and C3 is the only migration.

### 4.3 Blocked, with named preconditions, and not attempted here

| edge | precondition |
|---|---|
| the ontology-drift residual of 1.2, per panel | `measure_ontology_drift`, a new read-only operation over two ontology snapshots and the t0 annotation set. It cannot be measured by generating a second evaluation set on the same release pair, because the pair is unique at the schema level |
| the flow-independent homology, reach and taxonomy coordinates | no producer. No sequence-search tool is installed on this machine and no registered operation runs a bank-wide sweep; a global alignment library is a declared dependency and nothing wraps it. Until then, homology, taxonomy and the propagation gap are computed from the donors the run retrieved and are **inadmissible as coordinates** in any node whose levels change which donors are retrieved |
| the flow-admission contrast class | a second generator half that runs, a combiner that can read its signal, and candidate provenance, in that order (3.4) |
| the sealed terminal projection | a registered operation that refuses to run without a matching sealed plan and refuses a second run against one holdout. None exists |
| the first-appearance ground truth | ingestion of the intermediate releases plus a consumer for the existing module |

---

## 5. Instance zero: simple scoring over the experimental window

### 5.1 Stage A, the frame chain

Seven dispatches, none accelerator-bound, in dependency order.

| # | artefact | operation | payload essentials |
|---|---|---|---|
| A1 | upstream publication dates on the annotation sets | `refresh_goa_release_dates` | default listing URL; idempotent, never inserts |
| A2 | ontology snapshot `releases/2025-07-22` | `load_ontology_snapshot` | the release URL; no-op if present |
| A3 | ontology snapshot `releases/2024-03-28` | `load_ontology_snapshot` | as above |
| A4 | the decision cohort's evaluation set and its ground-truth artefact | `generate_evaluation_set` | `old` = GOA 220, `new` = GOA 227, `old_native = new_native = <2024-03-28>`, `pivot = <2025-07-22>`, `window_role = "valid"` |
| A5 | the information-accretion table | `compute_information_accretion` | `annotation_set_id` = GOA 220, `ontology_snapshot_id` = the pivot, regime `lafa`. Its corpus gate refuses when too many of the corpus's terms are absent from the target snapshot; the drop rate for a cross-era pairing is **not known** and is read from the operation's own emission before the band question is settled |
| A6 | the query file and its digest | `export_evaluation_targets` | the evaluation set, the three categories, one output name. The removed-only category is refused by the operation itself |
| A7 | the zero baseline of the frame census | `audit_evaluation_frames` | default |

Plus two acts with no registered producer, recorded as holes in the storage invariant rather than
hidden: seeding the scoring configurations through the configuration endpoint, and registering the
query file as a query set through the annotation endpoint.

**The frame is then asserted, not narrated.** Before stage B: the evaluation set's `window_role`
reads `valid`; the ground-truth artefact's nine panel counts are published as this instance's
populations; the information-accretion set resolves to the artefact the frame names, since the band
guard is off and a failed resolution silently publishes an unweighted number under a weighted name.

### 5.2 Stage B, the retrieval pass

One prediction set. One `predict_go_terms` coordinator dispatch, which partitions internally into
batch messages of the payload's batch size, default 1024, so the message count is the delta protein
count divided by that and is reported by the coordinator rather than assumed. A4 has since run: the window holds
**14,032 delta proteins and 19,036 units**, so fourteen messages at the default batch size. Every
quantity below that is proportional to the cohort takes those numbers and not the superseded
16,906 and 22,282, which were measured on the drifted construction.

| field | value | why |
|---|---|---|
| embedding configuration | the deployed mid-size protein language model, mean pooled, last layer, context 2048 | complete over the corpus, not text-aligned, and the space in which the platform's own frame quantities are already expressed. **Declared, not measured**, and every result of this instance is conditional on it |
| annotation set | GOA 220 | the window's t0, so donors carry only pre-cutoff annotations |
| donor policy | permissive, written explicitly, with self-donors excluded by sequence under C8 | the frame records the policy rather than defaulting it, and the name carries the clause of 3.2 |
| ontology snapshot | the pivot | the graph the ground truth is scored under |
| query set | the artefact of A6, intersected with the resolved queries under P5 and frozen | one artefact, one digest, one population |
| depth | 10 per aspect, so 30 donor slots | inside the range this project's record prefers, and shallow enough to bound the saturation of the vote fraction better than the inherited value. **Declared with its reason and its cost**: it is not a measurement, and the Retriever node will measure it |
| aspect separation | on | guarantees candidates in all three aspects, which the nine-panel table requires |
| alignments, taxonomy, reranker features | on, explicitly | three presets weight alignment identity, one weights taxonomic proximity, three weight the vote fraction, and the reranker-feature flag is what populates the stored rank that a later depth re-read needs |
| every other producer flag | off, explicitly | each is a flow or a half-flow instance zero does not admit. Turning one on silently changes what is measured |
| evaluation-time caps | none | the previous campaign measured the term cap at 0.0129 and the distance cap at 0.0031 of weighted micro F on the union window; both are frame axes and both are pinned |

### 5.3 The one flow, stated so the instance cannot be misread

Source: annotated donors in GOA 220. Mechanism: aspect-separated nearest-neighbour transfer in one
embedding space. **That is one flow.** Every level below is a configuration of it. Unique reach is
degenerate, total reach equals unique reach, marginal contribution is undefined against an empty
pool, and **instance zero produces no affinity map**.

### 5.4 The levels

Seven presets, read verbatim from `PRESET_CONFIGS`, plus one declared eighth.

| level | formula | weights |
|---|---|---|
| `embedding_only` | linear | embedding similarity 1.0 |
| `vote_fraction` | linear | vote fraction 1.0 |
| `alignment_only` | linear | global identity 0.6, local identity 0.4 |
| `embedding_plus_alignment` | linear | embedding 0.5, global 0.3, local 0.2 |
| `embedding_plus_vote` | linear | embedding 0.5, vote 0.5 |
| `evidence_veto` | evidence weighted | embedding 1.0, multiplied by the resolved evidence weight |
| `composite` | linear | embedding 0.4, global 0.2, local 0.1, taxonomic proximity 0.1, vote 0.2 |
| `flat_consensus` | linear | the arithmetic mean of the six linear weight vectors: embedding 0.400, vote 0.283, global 0.183, local 0.117, taxonomic proximity 0.017 |

**Two things about the eighth level, because an earlier draft asserted an identity that is false.**
`compute_score` renormalises over the signals actually present on a row, dropping a missing signal
from both the numerator and the denominator, so **the mean of the six weight vectors is not the
mean of the six scores** on any row where a weighted signal is absent. `flat_consensus` is a
declared level in its own right, not a derived one. And it shares roughly ninety per cent of its
weight mass with `composite`, so if `composite` leads a panel the flat comparator is close to the
per-panel leader and the rehearsal's contrast is correspondingly small. Both facts are printed
beside its rows.

The null configuration is never used: it is numerically identical to `embedding_only`, and under it
a candidate with an absent distance would score the maximum, which is a trap that opens the moment
a second proposer exists.

### 5.5 The measurement

**The mandatory partition.** Nine panels. Every number is reported in all nine and in none other.
Populations come from A4's ground-truth artefact and never from a count of rows a run placed or of
proteins a run predicted at its own maximising threshold; the latter is known to move by seventeen
per cent with one threshold step on a provably identical cohort.

**The reporting coordinates.** One dispatch of `stratify_evaluation` per result with the axes
pinned to category, aspect and length. **The default axis list crosses homology into the panels and
must not be accepted**, both because homology as implemented is computed from the donors the run
retrieved and because the identity statistic behind it saturates on non-homologous pairs. The
taxonomy and propagation axes are excluded for the same reason, and the propagation axis
additionally because it is expressed in the distance units of the space under test, which is the
flow's own defining statistic.

Length is admissible **inside this instance** because all eight levels share one embedding
configuration and therefore one truncation point, so the band means one thing throughout. It is
marked non-portable across any node that varies that configuration.

`min_population` is passed as 129, the derived reporting floor, rather than the default of 30. The
artefact retains withheld cells with their population and a flag, so a stricter reading is a re-read
rather than a re-run. Until C5 lands, every length cell also prints the share of its panel's
proteins that the stratifier could place.

**The rank.** The information-accretion weighted micro F of the panel, at that panel's own
maximising threshold. This is the frame's declared metric and it is a **ratio of sums**, not a mean
of per-protein values.

**The estimator, and this is where the arithmetic in every earlier draft was wrong.** A floor of the
form "a constant times a paired standard deviation over the square root of the population" is the
standard error of a mean of per-unit differences. The rank is a ratio of sums, dominated by the
units carrying the most information mass, with no per-unit decomposition. **The floor and the
interval are both the bootstrap standard error of the paired difference of that ratio**, resampling
proteins, with each level's own maximising threshold re-selected inside each resample. That is what
C1 and C6 exist for, and it is why C1 must land before the first evaluation rather than fourth on a
list.

**Two population disciplines.** `restrict_gt_to_predicted` defaults to **true** on both writers and
drops ground-truth proteins absent from the prediction set; instance zero passes it **false** with
the query set frozen under P5, so all eight levels are scored on one population by construction.
And the precision half of the metric is averaged over the proteins covered at the reported
threshold while recall is averaged over all eligible ones, so two levels at two different
maximising thresholds carry two different precision denominators. That is a property of the
protocol, not a defect to be fixed here; it is printed beside every level as the covered-protein
count at its own threshold, so a difference driven by coverage is visible rather than attributed to
ranking.

**Resampling.** Proteins, never protein-aspect units. Inside one panel a protein contributes one
unit so the rule is inert there; it binds on the declared macro aggregate of 5.6 and on any
cross-panel statistic. The stronger dependence, that proteins inside a region are homologues rather
than independent draws, is **not corrected and not estimated**, and every population printed is a
counted population.

### 5.6 The gate

Declared before the run.

**Contrast class.** Every comparison here is one configuration of one flow against another,
sharing the retrieval entirely. That is class 1 of `CAMPAIGN-MODEL.md` section 7.2, and instance
zero measures it directly rather than borrowing the single indirect estimate on record.

**The family and the correction.** Six comparisons against the declared reference `embedding_only`
plus the flat consensus, within a panel, corrected across that declared family. The family size is
stated on the page and the constant is labelled for what it is: a fixed per-comparison level, which
is Bonferroni-shaped, and not a step-up procedure, which has no single equivalent constant. The
nine panels are corrected independently and the report says so.

**Three outcomes per panel.**

- **Resolved.** The declared contrast the panel names clears its floor after correction, computed
  as in 5.5. The panel names one level. The contrast is the winner against the **declared
  reference**, not against the runner-up: a best-against-second-best difference is doubly selected
  and is not in the declared family.
- **Branches.** Two or more levels are indistinguishable within the panel. The node emits a
  per-panel set. This is an edge of multiplicity and it is what the record expects.
- **Indeterminate for want of power.** The observed spread is below the panel's minimum detectable
  effect. The panel prints its effect and is excluded from the family, not silently dropped.

**The pre-registered expectation.** On the previous campaign's rows, over 100 groups on the union
window, the median gap between adjacent presets was 0.0030 of weighted micro F, and the derived
minimum detectable effect at the low end of the contrast classes exceeds it in all nine panels of
this window's measured populations. **The expected outcome is branches or indeterminate in most
panels.** Writing that down before the run is what stops a null being narrated afterwards as a
finding of equivalence.

**And a required-population line accompanies every unresolved panel**, per `EXPERIMENT-GRAPH.md`
section 8: the number of proteins that would resolve the adjacent pair, printed as a request for
data.

### 5.7 The channelling rehearsal, which is the instance's real product

**What it is.** The routing node's question asked of the scoring node's levels. Of the two verbs a
level can take, **propagated applies and cut does not**: cutting is admission, admission is about
sources, and a configuration of one flow is not a source.

**The region family**, declared before any level is scored: the nine panels, crossed with the
length bands as the single nominated coordinate, with hierarchical collapse to the panel wherever a
band's population does not clear the admission floor, and to the whole population wherever a panel
does not.

**Four systems, on the same candidate rows and the same ground truth.**

- **A0**, one level everywhere, selected by a **declared macro mean over the nine panels**. The
  aggregate's form is fixed here, before any number is read; it defines the comparator and it
  reports nothing, which is the narrow exception `CAMPAIGN-MODEL.md` section 3.1 permits.
- **B**, the per-panel leader, which is a policy at panel granularity.
- **C**, the flat consensus level of 5.4 applied everywhere.
- **P**, the per-region leader at depth one.

**The contrast**, per panel: P against the best of A0, B and C.

**The honest estimate.** P is chosen on the data it would otherwise be scored on, so the in-sample
difference is an upper bound and is labelled as one. The held-out estimate is computed offline from
the per-protein artefacts: partition the proteins deterministically into ten parts, choose each
region's level on the nine parts excluding one, score that assignment on the one, and average. **It
costs no extra dispatch once C1 has written the whole threshold grid**, because the complement's
panel value and its own maximising threshold are both recomputable from the stored components. The
platform's fold field selects one part and cannot select its complement, which is why the analysis
is offline rather than dispatched. The partition is by a hash of the accession with no sequence
clustering, so near-identical sequences fall on both sides; that limitation is printed with the
number.

**What it produces.**

1. The machinery exercised end to end: a region family frozen before scoring, a deterministic
   derivation, a held-out re-estimation, a multi-way contrast, and an explicit indeterminate colour
   with a printed minimum detectable effect per region.
2. A per-panel variance for the configuration contrast class, measured on this window rather than
   rescaled from a prefilter study on an unstated population.
3. **The first measured variance for a per-region policy contrast**, obtained from the standard
   deviation of the part-level difference between P and its comparator. It is reported with its
   degrees of freedom, and with two limits stated rather than discovered: it is a pooled quantity
   over the region family and not a per-panel one, since a tenth of the cohort puts the smallest
   panels below the reporting floor; and part-level estimates from a ten-part scheme share most of
   their selection data pairwise, so the estimator is biased downward and its interval at nine
   degrees of freedom is wide enough that it cannot separate the two anchors this project quotes.

**A pre-registered possibility that must not be narrated after the fact.** The length bands split a
panel with a heavy skew toward the shortest band, so the two longest bands will fall below the
admission floor in most panels and the family will collapse to the panels. **P then equals B and
the rehearsal's contrast is identically zero.** That is an arithmetic outcome, not a finding about
channelling, and if it happens the instance's product is items 1 and 3 above and nothing else.

**What the rehearsal does not license.** No claim about any flow. No claim about affinity. **No
transport of its floor**: a variance measured on configurations that share their retrieval is a
lower bound on the variance of admitting a whole source, and citing it in an admission-class power
statement is the resemblance fallacy this campaign has already paid for. And no terminal
projection, since the sealed operation does not exist.

### 5.8 Cost

| stage | dispatches | internal messages | produced |
|---|---|---|---|
| A, frame | 7 | none | 2 ontology snapshots, 1 evaluation set with its ground-truth artefact, 1 information-accretion table, 1 query file with its digest, 1 zero-baseline census |
| A, non-operations | 2 API calls | none | 8 scoring configurations, 1 query set |
| B, retrieval | 1 | the delta protein count divided by the batch size | 1 prediction set, one candidate table |
| C, scoring | 1 (`batch_rescore_evaluation` with 8 configuration ids) | none | 8 evaluation results |
| C, guard | 1 (`audit_evaluation_frames`, the after half) | none | the forward gate of 3.0 |
| D, stratification | 8 (one per result) | none | 8 strata artefacts |
| E, analysis | offline, `compare_paired_panels` | none | intervals, floors, the rehearsal, two variances |
| **total** | **18 dispatches and 2 API calls** | | 1 prediction set, 8 evaluation results, 8 strata artefacts |

Eight code changes land first (4.2). The only accelerator-bound work in the instance is the single
retrieval coordinator and its batch messages. **No wall clock is quoted, because none has been
measured for this configuration on this machine; the rate is published from the first dispatch
before anything downstream is committed.**

---

## 6. What instance zero does not decide, and what it must not touch

### 6.1 What it does not decide

It does not decide the substrate. One configuration is declared, with its reason, and every number
in the instance is conditional on it.

It does not decide the depth. One value is declared, inside the range the record prefers, and the
Retriever node will measure it. Three of the eight levels are read at a vote denominator this
project's record does not endorse, and that conditioning is printed.

It does not decide the bank. One permissive policy is declared, with the clause of 3.2 attached to
its name, and the evidence-regime confound the previous campaign created is not retired here.

It does not close the scoring node in the ordinary sense. The expected outcome is an edge of
multiplicity, and that is written down in advance.

It does not measure affinity, produce an affinity map, or say anything about any flow, because it
has one flow.

It does not measure the flow-admission contrast class, which is the class the campaign's claim runs
on, and it does not create a pair in that class.

It does not measure the ontology-drift residual of 1.2, nor the first-appearance residual, nor the
homology design effect. All three are named with their missing producers.

It does not fix the floors of any other contrast class, and nothing measured here may be quoted as
a floor for one.

### 6.2 What it must not touch

- **GOA 230.** No annotation set beyond GOA 227 is read, for any purpose, including a check that
  something ran.
- **The holdout window.** No `generate_evaluation_set` dispatch with `window_role="test"`. Its
  ground truth is not built here, so it cannot be inspected here.
- **No prediction set, query file, information-accretion table, stratification or coverage census
  on the holdout cohort.**
- **No union-window artefact.** If a ground-truth artefact for GOA 220 to GOA 230 survives the wipe
  as orphan bytes, it is not read. Half of that population is the blind reserve.
- **No previously stored evaluation number as an input to a decision here.** The census figures in
  5.6 and 3.1 are used to declare expectations in advance and are never used as floors. They were
  measured on 1,296 rows that are being deleted, roughly two thirds of them on the union window,
  and they will not be reproducible afterwards.
- **No second flow.** Every generator flag is off by an explicit false, not by default.
- **No second representation, no second bank, no second depth.** Those are three other nodes, and
  mixing one in would move the contrast class out from under the only variance the instance
  measures.
- **No seal.** The sealed plan governs the first contact with the holdout, and that contact needs a
  registered, content-addressed projection operation that does not exist.

### 6.3 What it hands to the next instance

A candidate table born with proposer and scorer sets, so that the moment a second generator half
and a scorer that reads it exist, unique reach is a group-by rather than a re-run. A prediction set
whose retrieval frame is on the row rather than on a deleted job payload. A per-protein artefact
sliced correctly and across the whole threshold grid, which is the instrument every later interval
depends on. A measured per-panel variance for the configuration class. A first measured variance
for a per-region policy contrast, with its bias and its degrees of freedom stated. And a ground
truth built under one propagation graph at both ends, with the one residual that construction
leaves named and priced as a missing producer rather than carried as a caveat.

---

## 7. What the critiques got wrong

One line each, with the reason.

**"GOA 220's publication date is not stated in any file on this machine."** Wrong, and the design
that said it also relied on the date two paragraphs later. It is at `docs/BAND_REGISTRY.md:37`,
together with the four other release dates, and it is what makes the duration asymmetry in 1.1
computable.

**"Setting the three snapshot ids equal closes both ends under one graph and removes the phantom
gap."** Wrong, and the critique that caught it is right: that assignment selects the non-propagating
branch and an identifier-scoped term lookup. But the critique's conclusion, that the intended
construction is not expressible at all, is also wrong: setting the two native ids equal to each
other and different from the pivot is expressible, reconciled, identifier-safe and closed under one
graph. That is the construction in 1.2.

**"The drift control is a second evaluation set on the same release pair."** Wrong, and the pair is
UNIQUE at the schema level with an explicit raise in the operation. The drift is measured by a
separate read-only producer that does not exist, and it is marked blocked in 4.3 rather than
dispatched.

**"Depth is a truncation of a list already written."** Wrong as a blanket statement and right in
part. The donor-anchored columns are invariant under truncation and the vote-derived ones are not,
so depth is free for four of the seven presets and paid for three. 3.3 carries the split rather
than either blanket.

**"`min_population` at 30 is the stratification landmine."** Half right. The larger default is the
axis list, which crosses homology into the panels by default, and homology as implemented is
computed from the run under test. 5.5 pins the axes explicitly and passes the derived floor.

**"The protein-versus-unit resampling rule protects the intervals."** Wrong where it is applied.
Inside one panel a protein contributes one unit, so the rule is inert there. It is kept with its
scope stated, and the dependence that does bite, homology clustering inside a region, is declared
unestimated.

**"The three prior-knowledge panels are non-resolving in advance, on the model-axis spread."**
Wrong twice: the spread quoted was measured on a different window with different panel sizes, and
one of the three panels' spreads exceeded its own quoted floor in the same table. This instance
declares nothing non-resolving in advance on a borrowed spread; it publishes a
required-population line instead.

**"The flat consensus costs no new code because a mean of linear scores is a linear score."**
Wrong: the scorer renormalises over the signals present on each row. `flat_consensus` is a declared
level with its own weights and its own limitations, printed beside it.

**"Candidate provenance is the smallest change and everything waits behind it."** Wrong as an
ordering claim. In a single-generator system the column writes one constant. The flow-admission
class is blocked on a second generator half and a scorer that reads it; provenance is what makes
the pair readable. 3.4 states the order.

**"The two registries disagree about which window the board scored."** Wrong. One names the window
by its opening and the other names the mark, and they agree. The genuine constraint, that the
release list cannot name a window strictly before this cohort's opening, survives on its own and is
carried in 3.7.
