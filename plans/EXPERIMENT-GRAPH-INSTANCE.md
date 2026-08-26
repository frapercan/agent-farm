# The graph, instantiated: the frame this campaign declares, the two cohorts, and where every edge stands today

`EXPERIMENT-GRAPH.md` carries the shape and holds no numbers on purpose. This is the
instantiation. When a cohort, a release or a budget changes, this file is rewritten and the shape
stands.

Everything below is measured against the current database or cited to a file. Where a value is
not known yet it says so, because an instantiation that fills its own gaps is a plan pretending
to be a record.

---

## 1. The frame, declared

The frame is not a decision the campaign takes by experiment. It is a convention, and its whole
obligation is to be written once and stamped on every row.

| field | value |
|---|---|
| release pair, experimental | GOA 220 to GOA 227 |
| release pair, competitive | GOA 227 to GOA 230 |
| ontology pivot | the snapshot bound to the window's t1 |
| information accretion side | the window's t0 |
| excluded-known base | the prior-knowledge partition at t0, always passed, never defaulted |
| gained side | experimental evidence only, the thirteen codes the benchmark uses |
| metric and weighting | information-accretion weighted, per panel, never pooled |

**Two of these are corrections, not choices.** The excluded-known base is the flag whose omission
moved a published cell by more than the lever the same page was arguing for, so it is a required
argument of the evaluation and the writer refuses a prior-knowledge row from a run that lacked it.
And the gained side is experimental evidence only: counting every evidence code inflates the delta
by more than an order of magnitude, because electronic annotation churns, and a delta that
approaches the corpus is not a delta.

The frame is modelled as a source node with no levels and no experiment, whose edges reach every
other node, so that when it moves, and the record says it will, what is invalidated is computable.

**The stratifier's reference bank belongs here and not to the Bank node.** Two arms differing in
donor eligibility must not receive different band membership.

---

## 2. The two cohorts

**Experimental: the window from GOA 220 to GOA 227.** Decisions are taken here.

**Competitive: the window from GOA 227 to GOA 230.** Touched once, under a sealed plan.

**They are disjoint, verified rather than assumed.** Counting protein-term pairs newly gained in
each window, the intersection is **zero**. The two windows abut: the t1 of one is the t0 of the
other, so disjointness is a property of the construction and not a coincidence to be rechecked
each time.

**The competitive cohort is the benchmark's own window, not an invented second holdout.** That
matters for a rule the campaign already carries, which forbids a second internal holdout on the
grounds that it would mean holding out twice and reporting whichever came out better. There is
only one holdout here, and it is the one the field already uses.

### Panel populations, in units of protein by aspect

| panel | experimental | competitive | ratio |
|---|---|---|---|
| NK, BPO | 1,344 | 373 | 3.6 |
| NK, MFO | 797 | 224 | 3.6 |
| NK, CCO | 799 | 203 | 3.9 |
| LK, BPO | 985 | 418 | 2.4 |
| LK, MFO | 689 | 181 | 3.8 |
| LK, CCO | 505 | 193 | 2.6 |
| PK, BPO | 6,392 | 3,451 | 1.9 |
| PK, MFO | 2,964 | 827 | 3.6 |
| PK, CCO | 3,399 | 1,326 | 2.6 |
| total | 17,874 | 7,196 | 2.5 |

**This is why the experimental window is the one it is, and the reason is power in the panels the
thesis is about.** The six low-knowledge panels hold between 505 and 1,344 units here. The window
the existing ablation architecture was sized against holds between 161 and 354 in the same panels,
so every one of them roughly triples. Against the floor that document derives at the low end of
its contrast classes, all six clear it comfortably; against the floor at the high end, four of
six clear it and two are close. Under the smaller window, none of that was true.

The prior-knowledge panels remain three quarters of the units and remain the region where the
existing arithmetic says nothing separates. Enlarging the window does not change that, and the
instantiation does not pretend it does.

---

## 3. The nodes, and where each edge stands today

Strengths are as defined in the shape: measured, chosen, inherited, unpowered, blocked.

### Frame
Source node. Cardinality one. Edges to everything.

### Substrate
The backbone, the depth, the grain, the order of sparsification and aggregation.

Ten pretrained representations and three learned ones exist over the whole corpus, plus one in
production at the time of writing. Of the twelve fields that describe a representation, **two have
ever taken more than one value**: the model, and the depth, and the depth once, in one model. The
other ten are inherited: one carries a single value in every configuration including the one whose
own documentation says the field exists for it, and one is dead by construction, because layer
aggregation cannot differ while exactly one layer is selected.

Chunking has never been produced. No configuration enables it and no stored row carries a chunk
index, which means the control arm of the recorded aggregation-order question has no input, and
the arm cannot be scored until it does. **Blocked**, with a named precondition: three reference
pool loaders join without a chunk predicate, so a chunked configuration would emit one pool row
per window with the accession repeated and inflate the neighbourhood silently.

### Bank
Which donors are eligible.

The corpus is entirely reviewed, so the tier of unreviewed material the campaign declares has no
instance and the review flag has never discriminated anything. And the evidence regime is
**perfectly confounded with the window**: every prediction set built on one bank is gated and
every set built on the other is permissive, so in the data that exists, window and donor policy
are one axis. One run at matched window and two banks separates them.

### Retriever
Every arm ever run retrieved by embedding nearest neighbour. Every stored candidate row carries an
embedding distance and a named donor, so no other generator has ever produced a candidate and an
alignment score could only ever reorder donors the embedding already found. **Inherited**, and it
is the inherited edge with the widest reach, because every result to date is a statement about
scoring conditional on it.

### Generator
What proposes candidates retrieval cannot reach.

**Blocked, and comprehensively.** Every artefact of the recorded champion generator is missing or
unproducible: the head, the classifier checkpoint, the training bundle its trainer consumes, and a
term embedding for which no code path anywhere writes a file. The seven recovered projection heads
do not correspond to the surviving representation: measured against it, the rank of a protein's
true terms sits near the third decile of the vocabulary against a threshold declared in advance at
the first percentile, so the signal is real and the correspondence is not usable.

### Scoring
The order candidates take and where the threshold falls.

Eight presets exist and all have been applied at evaluation, never at retrieval. **This node is
the cheapest in the graph**: the stored candidate table carries every quantity the presets read,
including alignment identity, taxonomic relation and vote counts, so the whole node is a re-read.
Neighbourhood depth is not a level of this node either: candidates are stored to a fixed depth and
every smaller depth is a truncation of a list already written.

### Features
Which families the scorer may read. Their producers exist unevenly and their leakage audit is on
record. Cannot be measured before the re-ranking node exists.

### Re-ranking
What learned ranking adds over the tuned score at fixed candidates. **The layer is absent**: the
model tables are empty and the arm field carries a single value in every stored result. Not
blocked in the sense the generator is, since the trainer and its inputs exist; blocked in the
sense that nothing has been trained on this platform.

### Combination and Routing
Downstream of nodes that have not closed. Declared, not scheduled.

---

## 4. Which nodes may see the fan

**Cheap, and therefore permitted to evaluate a whole incoming set.** Scoring, in every one of its
levels, because it re-reads stored candidates. Any node whose evaluation is a group-by over the
stored candidate table.

**Expensive, and therefore evaluating the incoming set through a cheap surrogate and paying only
for the resolution.** Substrate, which costs a corpus forward pass per level. Generator and
re-ranking, which cost training.

The surrogate for the expensive nodes is retrieval quality over stored neighbour lists, which is
available for every representation that exists.

---

## 5. What is unpowered before it runs

Stated here rather than discovered, which is the point of computing it in advance.

**The three prior-knowledge panels.** The spread the model axis produces there is at or below the
effect the panel can detect, on the existing arithmetic, and three quarters of the units live
there. Any node whose only evidence would come from those panels emits an unpowered edge and a
request for data, not a fan.

**Every level of every reporting coordinate that falls below the floor after subdivision**, which
the report prints beside the level rather than hiding by merging.

**The above-context-length regime**, in every panel, in both cohorts.

---

## 6. What can run today

**The scoring node, entirely.** It is a re-read of a table that already exists, over presets that
already exist, at every neighbourhood depth up to the stored limit, stratified. It needs no
accelerator, no new artefact and no decision from any other node, and it addresses the axis the
record says the scorer absorbs the ones above it.

**The census that fixes the floors.** The floors of this graph are properties of the contrast
class and the campaign has measured only one, indirectly, at the low end. Measuring the rest is a
paired bootstrap over banks that already exist. Until it runs, every floor in this instantiation
is inherited from a single contrast and every unpowered declaration above is provisional.

**The separation of window from donor policy**, one run.

**The frame audit**, which exists as a registered operation and has never been dispatched. Its
first output should be the stored results that cannot be attributed to a frame at all, because the
jobs that produced them are gone.

---

## 7. What this instantiation does not decide

It does not choose a champion, and it does not rank anything. It records where each edge stands so
that the first node to close has somewhere to write its answer.

It does not fix the floors. It names the one that exists and says the rest are pending.

And it does not schedule. The order in section 6 is what is unblocked, not what matters most, and
those are different questions.
