# The graph, audited against this campaign only

`EXPERIMENT-GRAPH.md` carries the shape and `EXPERIMENT-GRAPH-INSTANCE.md` carries the
instantiation. This document carries neither. It carries the audit: for every node, what this
campaign can actually show, and for every claim the instantiation makes, whether the evidence
behind it was produced by this campaign or by an earlier one.

**The rule this audit was run under.** The clean run begins 2026-07-30. Verified: the oldest row
of `evaluation_result`, `prediction_set`, `embedding_config`, `annotation_set` and `job` all carry
that date. Anything older belongs to a campaign that did not use this modelling system and is not
evidence here. Every fact below is dated, and anything that could not be dated is reported as a
gap rather than used.

---

## 1. The evidence the instantiation calls its strongest is residue

`EXPERIMENT-GRAPH-INSTANCE.md` section 3bis is titled "the affinity already measured, which is
the strongest evidence the design has". It rests entirely on work that predates this campaign.

Its sources are `PILLARS.md` (2026-07-09), `prior-knowledge-wall/PLAN.md` (2026-07-17),
`SIGNAL-REGISTRY.md` (2026-07-27) and `COMPOSITION-MODEL.md` (2026-07-28). None has been touched
since the campaign began. The receipt those documents declare, `lofo_9cell/result.json`, is not
locatable on this machine.

The live database refutes it four independent ways.

| check | result |
|---|---|
| `reranker_model`, `experiment_run` | 0 rows each |
| `evaluation_result.reranker_model_id` | NULL in all 1,296 |
| `arms_enabled` | one distinct value: `knn` true, `interpro`, `reranker`, `mlp_tower`, `interpro_graft` all false |
| job payloads mentioning `rerank` or `feature` | 0 of 1,546 |

And the arithmetic closes it. All 225 prediction sets carry the same three feature flags
(`compute_alignments`, `compute_taxonomy`, `compute_reranker_features`) with no variation
anywhere. `compute_self_prior`, `compute_association` and `compute_classifier` were never turned
on, so `self_prior_score`, `association_*` and `classifier_*` are zero in all 128,191,567 rows. A
leave-one-family-out ablation that removes families holding zero cannot measure anything. This is
not weak evidence. It is an impossible measurement.

One aggravating detail, because it is the kind that survives review. Section 3bis says the
ablation ran "on a clean frame with the excluded-known base applied". Its own source marks the
governing row `FRAME WARNING: measured WITHOUT -known, in the frame the project itself declared
invalid`. The document inverted the warning it was quoting.

**What survives.** Two things, and they are worth more than what was lost. The five-family schema
is real and live in the current checkout (`protea_contracts.feature_schema.FEATURE_FAMILIES` and
`protea/core/features/registry.py`), so the design's vocabulary is realisable rather than
invented. And several of the zeros are derivable from definitions rather than from experiment,
which section 5 below builds on. What does not survive is every magnitude, every ordering, the
"wide margin", the "first in two panels" and the "nine of ten disjoint folds".

---

## 2. The frame is not merely unstamped. It is wrong

The instantiation treats the frame as declared but unstamped. The stored data says worse.

`frame` is NULL in all 1,296 result rows, as the instantiation says. But the frame it declares and
the frame the data carries are different objects. The declared release pairs are 220 to 227 and
227 to 230. The database contains 226 to 227 and 220 to 230. Information accretion is declared at
the window's t0 and is taken at t1 for 593 of the 594 rows of the long window. `temporal_window`
is set to 522.

One correction in the other direction, and it is good news. The excluded-known base is not a
parameter that a run can omit. It is wired to the PK setting in the only two routes that write an
`EvaluationResult`, unchanged since 2026-05-08, so all 1,296 rows carry it. The instantiation
lists it as a risk that must be "always passed, never defaulted". It is neither passed nor
defaulted. It is structural, and that edge can be marked satisfied.

---

## 3. Node by node

### Frame
Broken as described above. `audit_evaluation_frames` exists as a registered operation (commit
4b1f757, 2026-08-17) and has never been dispatched. It is the cheapest action in the graph:
read-only, one payload field. Until it runs, the Frame node does not even have a census of the
damage.

### Substrate
Thirteen levels instantiated, twelve complete over the corpus. One is at 40.6 per cent and
running.

Among the ten pretrained configurations, only `model_name` and `layer_indices` have ever taken
more than one value, and `layer_indices` once, in one model. The apparent variation in `pooling`,
`normalize`, `max_length` and `layer_agg` across the full census is an artefact of the three
derived representations, which write those fields by construction. It is not exploration.

Five fields are hard constants across all thirteen rows: `normalize_residues`, `use_chunking`,
`chunk_size`, `chunk_overlap`, `embedding_scale`. By the shape's own rule that a knob with no
second reachable value is not a node, none may carry an edge. `layer_agg` is dead by construction
while `layer_indices` selects exactly one layer, which it does in all thirteen.

Chunking remains blocked, now with a number: 6,553,740 rows, every one with `chunk_index_s = 0`
and `chunk_index_e` NULL. The aggregation-order question has no input at all.

### Bank
Blocked, and mislabelled in the flattering direction.

The evaluated cross has two of three possible cells filled, on the diagonal: (226 to 227, bank
226, permissive, 702 results) and (220 to 230, bank 220, experimental, 594). Bank and window are
one node in the data that exists, so the Bank edge is blocked with a named precondition rather
than unpowered.

More seriously, the level called "experimental" is not the level it claims to be. The policy cuts
the donor pool from 556,306 to 86,068 proteins (15.47 per cent) but does not cut what those
donors give: roughly 30 per cent of the predictions in an "experimental" run come from an IEA
annotation and 56 to 62 per cent from a code outside the policy. The real level is "a donor
holding at least one experimental annotation, giving everything it has". Any comparison resting
on "one window uses experimental evidence and the other does not" is mislabelled, and the error
flatters the restrictive arm.

### Retriever
Inherited, and now measured rather than asserted. Cosine with aspect-separated KNN in all 225
sets, one distinct `arms_enabled` across all 1,296 evaluations, and zero candidates without a
donor in 128,191,567 rows, by full scan rather than by sample. This is the widest-reaching edge in
the graph and every result to date is a statement conditional on it.

### Generator
Blocked, confirmed by evidence owing nothing to earlier campaigns: the full candidate table
scanned without a single generator candidate, and 281 prediction jobs none of which enables the
flag that would produce one.

But the node is drawn wrong, and the correction changes what to build first. **The head is not the
binding constraint.** The protein tower exists and is paid for: three campaign embedding
configurations at 2048 dimensions, 528,234 residue codes, with the pooled and dense arms
rebuildable in 10 and 18 measured minutes, against 21,844,141 positives. A head can be retrained.

The **GO tower** cannot. Its two blocks, BioBERT text and PPMI/SVD co-annotation, have no producer
anywhere in the checkout; the only mention in all of `protea/` is a docstring. The single
surviving copy is residue from 2026-06-28 and 29, declared non-rederivable by its own record, with
t0 undeclared.

So the absent producer is the GO tower, and it deserves a node of its own upstream of the
generator. That is what "what to build first" should name, instead of the head.

A second correction: the `GENERATOR -> SUBSTRATE` edge should be labelled a trap rather than
simply satisfied. `two_tower_config_id()` is overridable by environment and the loader's only
check is `shape[0] == 2048`, so a mismatched tower loads silently.

### Scoring
The only node that can close with what exists, and the audit strengthens that rather than
qualifying it. Eight presets, 294 successful `batch_rescore_evaluation` jobs, and the six columns
the presets read are populated 97.9 to 100 per cent over 118,254,475 candidate rows. All eight
levels run today without producing anything.

Two findings the instantiation does not carry.

**Two levels are blocked and the guard does not notice.** `anc2vec_neighbor_cos` and
`anc2vec_neighbor_maxcos` are zero in 0 of 118,254,475 rows and are not covered by
`_SIGNAL_TO_COLUMN`, so a scoring config that weights them passes validation and silently returns
0.0. That edge must be marked untraversable before anyone instantiates it.

**`neighbor_vote_fraction` does not live in [0,1].** It is `vote_count / K` unclipped, and
`vote_count` counts annotations rather than neighbours. `compute_score` clips it at 1.0.

### Features, Re-ranking, Combination
No buildable edge, and the blockage is in the operation surface rather than in the data. No
training operation is registered in PROTEA at all: they were deregistered on 2026-04-29 toward
`protea-reranker-lab`. The one registered feature producer, `export_features_batch`, is disabled
by an environment gate and has no worker.

### Terminal projection
The sealed operation the shape's section 6 requires does not exist. The graph's terminal node has
no implementable edge.

---

## 4. The flow inventory: this campaign has exactly one flow

Everything above reduces to one sentence. **Every candidate PROTEA has ever produced in this
campaign was proposed by neighbour transfer**, and 32 of the 68 columns on the candidate table are
zero in all 128,191,567 rows.

The platform already has the vocabulary. `arms_enabled` names five arms: `knn`, `interpro`,
`reranker`, `mlp_tower`, `interpro_graft`. Four have never been true.

And the convention for a non-neighbour candidate already exists in the schema:
`ref_protein_accession` accepts the sentinels `''`, `'classifier'` and `'interpro'` in four places
in the code, with `distance` set to NaN. It has never been written. This narrows the first
instrumentation task: the question is not whether to invent a column but whether a sentinel in the
donor field is sufficient representation. It is not, for one reason that decides it: a sentinel
holds one value, and unique reach is the quantity "proposed by this flow and by no other", which
requires a set. That is the argument for the bitmask, and it is a better argument than the one
originally given.

---

## 5. Structural affinity, which costs nothing and is pre-registered by construction

Affinity has two layers and the design conflates them. Separating them is what makes the claim
testable without the residue.

**Empirical affinity** is measured, needs power, and is the object the shape itself calls "close
to unidentifiable in the regions that justify the design". In this campaign it does not exist at
all.

**Structural affinity** is derivable from what each mechanism can read. It costs nothing, it is
immune to the identifiability problem, and it has a property the empirical layer cannot have: **a
policy derived from structure is pre-registered by construction**, because it was never fitted to
any result. That removes the selection-floor problem at the terminal projection, since no maximum
was taken over regions.

| flow | what it reads | NK | LK | PK |
|---|---|---|---|---|
| neighbour transfer | an annotated neighbour | live | live | live |
| anc2vec neighbour | the neighbours' terms | live | live | live |
| classifier | the sequence alone | live | live | live |
| domain signature | the query's domains | live | live | live |
| sequence record | the query's own UniProt record | live | live | live |
| association | the query's terms, any aspect | **zero** | live | live |
| lineage | the query's known terms | **zero** | live | live |
| anc2vec query | the query's known terms | **zero** | live | live |
| self prior | the query's terms, same aspect | **zero** | **zero** | live |

The zeros are arithmetic, not measurement. A no-knowledge protein holds no experimental term in
any aspect, so every flow keyed on the query's own terms is mute there. A limited-knowledge
protein holds none in the aspect being scored, so the same-aspect prior is mute there too. The
implemented lineage family is keyed on known terms (`lineage_is_ancestor_of_known`,
`lineage_is_descendant_of_known`), which is why it is structurally mute in NK rather than merely
unhelpful.

**This layer reproduces three of the five rows of the residue table from definitions alone.** That
is the sense in which the design's premise survives the loss of its evidence: what was inherited
was mostly re-derivable, and the part that was not re-derivable is the part that should never have
been quoted.

---

## 6. The channelling directions

Read the matrix down the NK column. **Four of nine flows are structurally dead in no-knowledge.**
Of the five alive, two require finding an annotated neighbour, which is precisely what a
no-knowledge protein is least likely to have.

**Three flows can serve no-knowledge without an annotated homologue: the classifier, the domain
signature, and the sequence record. None of the three exists in this campaign.**

That single sentence is the design. The region where the thesis claim lives is the region where
the incumbent flow is structurally weakest, and every flow that could relieve it is unbuilt. It
also explains, without appeal to any measurement, why "channelling beats not channelling" is
worth testing: the incumbent is not merely worse in NK, it is worse for a reason that another
mechanism does not share.

Three directions follow, ordered by cost rather than by importance.

**Direction A, into LK and PK, costs a payload flag.** `apply_self_prior` and `apply_association`
exist in `_post_knn_pipeline` and are gated by flags that have never been on. This buys scoring
signal in six panels, not unique reach, and it is the cheapest thing in this document.

**Direction B, into all nine panels, is the sequence record.** `protein_uniprot_metadata` holds
575,503 rows fetched 2026-07-30, with `keywords` at 99.0 per cent coverage, `function_cc` at 89.1,
`ec_number` at 51.2, `catalytic_activity` at 48.6 and `pathway` at 22.4. UniProt keywords and EC
numbers map to GO through small public files the EBI maintains. It needs no accelerator, no
external install and no training, and it is donor-free, so it serves NK by construction.

It carries one hazard that must be measured rather than assumed, and it is disqualifying until it
is. The metadata was fetched on 2026-07-30, after 220, after 227 and after 230. Keywords and EC
numbers are curated alongside GO annotations, so a protein that gained an experimental term
between 220 and 227 very likely gained its keyword in the same curation pass. **As fetched, this
source is almost certainly leaky in the flattering direction.** It becomes usable by re-fetching
at the t0 release, which UniProt retains. That is a bounded task and it is the precondition on the
edge.

**Direction C, into no-knowledge, is the expensive one and the one the thesis needs.** The
classifier and the domain signature. The classifier is blocked on the GO tower, which is cheap in
compute and has no producer. The domain signature is blocked on an InterProScan installation which
the operation's own docstring defers to "post-defensa": no binary on this machine, no JVM,
`interpro_annotation` and `interpro_go_mapping` both empty, while the operation itself is complete
and resumable.

---

## 7. The floors, recomputed on measured populations

The instantiation's panel table does not come from the database. Recomputing the arithmetic of
`ABLATION-ARCHITECTURE.md` (2026-08-17, this campaign) on measured populations gives the
following, at the resolution floor of 0.02 and the two contrast classes that document names.

| panel | experimental | competitive | MDE at 0.081 | MDE at 0.13 | max tolerable sigma_d |
|---|---|---|---|---|---|
| NK BPO | 1,509 | 436 | 0.0058 | 0.0094 | 0.277 |
| NK MFO | 1,129 | 346 | 0.0068 | 0.0108 | 0.240 |
| NK CCO | 1,116 | 275 | 0.0068 | 0.0109 | 0.238 |
| LK BPO | 1,214 | 540 | 0.0065 | 0.0105 | 0.249 |
| LK MFO | 943 | 244 | 0.0074 | 0.0119 | 0.219 |
| LK CCO | 821 | 266 | 0.0079 | 0.0127 | 0.205 |
| PK BPO | 6,685 | 5,355 | 0.0028 | 0.0045 | 0.584 |
| PK MFO | 4,025 | 1,383 | 0.0036 | 0.0057 | 0.453 |
| PK CCO | 4,849 | 1,595 | 0.0033 | 0.0052 | 0.497 |

Two consequences, and the second is new.

**The window change moved six panels from unpowered to powered.** Against the population floor of
332 that the high contrast class implies, the old window cleared three of nine. The experimental
window clears **nine of nine**, and the weakest panel tolerates a paired standard deviation of
0.205, which is the noise budget available to a contrast that admits a whole source.

**Three panels of the competitive cohort cannot resolve anything at that contrast class.** NK CCO
at 275, LK MFO at 244 and LK CCO at 266 fall below 332. This is not a result, it is an
impossibility known in advance, and it belongs in the sealed plan before the holdout is touched.

---

## 8. What has to be agreed before anything is built

**Is a feature family a flow?** Association, lineage and the self prior are sources with
mechanisms, which is the shape's own definition, but each is implemented only in its scoring half:
they reorder candidates that retrieval already found and propose nothing. Either the graph calls
them flows whose generator half is unbuilt, or it calls them features and the flow set is much
smaller than the affinity matrix suggests. The answer changes what unique reach means.

**Does label semantics belong in the flow set at all?** It reorders and proposes nothing, so under
the unique-reach definition it has no affinity to map.

**Which second flow.** Direction B is cheapest and needs a temporal re-fetch to be legitimate.
Direction C is what the claim needs and costs either a written producer (GO tower) or a deferred
installation (InterProScan). They are not exclusive and the ordering is a budget decision.

**The three guards, in order.** A job declares the node it answers and fails if its varied axes
contradict it. No result row without a sealed frame. A node cannot close as measured with a weak
incoming edge.

**And the first action either way** is `audit_evaluation_frames`, which is read-only, exists, has
never run, and is the only thing standing between the graph and a source node with no sealed
edges.
