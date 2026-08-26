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

**The stratifier's reference bank belongs here and not to the Bank node.** Two flows differing in
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

Measured at the experimental baseline, each cohort against its own pivot, releases joined on the
ontology accession rather than the internal term id.

| panel | experimental | competitive | ratio |
|---|---|---|---|
| NK, BPO | 1,509 | 437 | 3.45 |
| NK, MFO | 1,140 | 349 | 3.27 |
| NK, CCO | 1,115 | 275 | 4.05 |
| LK, BPO | 1,215 | 539 | 2.25 |
| LK, MFO | 941 | 245 | 3.84 |
| LK, CCO | 821 | 266 | 3.09 |
| PK, BPO | 7,136 (route-dependent) | 3,920 | 1.82 |
| PK, MFO | 3,908 (route-dependent) | 1,081 | 3.62 |
| PK, CCO | 4,623 (route-dependent) | 1,680 | 2.75 |
| total | 22,408 | 8,792 | 2.55 |

**This is why the experimental window is the one it is, and the reason is power in the panels the
thesis is about.** The six low-knowledge panels hold between 821 and 1,509 units here. The window
the existing ablation architecture was sized against holds between 161 and 354 in the same panels,
so every one of them multiplies by between three and five. Against the floor that document derives
at the low end of its contrast classes all six clear it comfortably, and against the floor at the
high end all six clear it as well. Under the smaller window, none of that was true.

**The ratio that the power argument runs on is 3.19, not 2.55.** The global ratio is seven tenths
prior knowledge by construction, and prior knowledge is both the region the existing arithmetic
declares inert for the representation axis and the region whose counts depend on which route
measures them. Restricted to the six panels the thesis is about, the experimental cohort is
**3.19 times** the competitive one, 6,741 units against 2,111. Prior knowledge on its own runs
2.35. Quoting the global figure understates the design where it matters and launders the
route-dependence of the part that does not.

That ratio is route-independent by construction rather than by luck. Both of the faults that split
the prior-knowledge rows need a non-empty experimental closure at t0 in the aspect being counted,
and no low-knowledge panel has one. Measured on the reconciled route the numerator moves by nine
units and the ratio by four thousandths, from 3.193 to 3.189.

**The three prior-knowledge rows are marked because two routes disagree on them, and both routes
are wrong.** Measured against the reconciled ground truth rather than the raw annotations, the
same window gives 6,680, 4,023 and 4,847. Decomposed in the one panel examined so far, the
disagreement is two faults pointing opposite ways.

The raw route **overcounts** because it does not propagate the pivot: a term it records as gained
is already an ancestor of something the protein held at t0, so the gain is redundant rather than
new. The reconciled route **overcounts** because it closes each end under its own ontology
snapshot, and the two releases hang off snapshots four months apart: a protein whose experimental
set is byte-identical at both ends still acquires ancestors, because parent edges were added to
the ontology in between. Both faults require a non-empty closure at t0 in the gained aspect, which
is why both are confined to prior knowledge and why the six low-knowledge panels agree to within
twelve units.

The two only-sets are disjoint and each is homogeneous, verified over all of both rather than
sampled: all 577 units the reconciled route holds alone have no raw gain, and all 462 the raw
route holds alone have one. Their intersection is 3,446 units. **That number is an identity, not
a tie-out**, since subtracting each only-set from its own total must give the intersection by
construction; it carries no evidence on its own.

What it takes to make 3,446 the true panel is that both only-sets be error, and only one half of
that is settled. **The 577 are settled by measurement.** All of them, checked exhaustively rather
than sampled, hold an experimental set that is identical at both ends of the window, so nothing
about the protein's evidence changed and what the reconciled route records there is not new
knowledge. Closure monotonicity does not settle it and must not be quoted as if it did: nesting of
closures follows from nesting of the underlying sets only when both are taken under the same
graph, and the reconciled route takes one end under each of two ontology snapshots. That gap is
not a technicality, it is the drift itself, and an argument that proved the 577 away would be
proving away units that were counted.

**The 462 are open.** Calling them error requires that each one's gained term already sit in the
ancestor closure of what the protein held at t0, which is confirmed on four of them. Until that is
measured over all 462, the panel is bounded rather than known: **between 3,446 and 3,908**, at
3,446 if every one is absorbed and 3,908 if none is. The lower bound is thirteen percent below the
raw figure and seventeen percent below the reconciled one.

**The consequence is larger than a disagreement over a count.** Roughly one unit in seven of the
reconciled prior-knowledge panel is ontology drift rather than new annotation, which is a property
of the window rather than of a route: anything evaluated on it is being scored in part on the
ontology having been restructured. The design is protected only because the contamination is
structurally confined to the region it already treats as inert. Neither set of prior-knowledge
figures may be cited, and the reconciled route may not be adopted on the grounds of being the
evaluator's, since in the panel measured it is the less accurate of the two.
instantiation does not pretend it does.

### The stored evaluations do not respect this split

**The prediction sets already in the database were built for the pair 220 to 230, which is the
union of both cohorts.** Every quantity measured on them is therefore measured on a population
that contains the competitive cohort, including the dispersion floors of the floor census and the
decisions this campaign took on neighbour count, preset and representation.

This cannot be repaired by preserving anything, and it is not an argument for keeping those rows.
It is a fact about the campaign that preceded this instantiation: the window this design reserves
as blind was already read. The instantiation records it here so that nothing carries it forward
silently. **No quantity measured on the union may seed a prior on the competitive cohort**, and
the cohort table above, which is split, is the design's population rather than anything recomputed
from the stored sets.

**The table above replaces an undercount, and the cause was a definition rather than an error.**
The earlier count was 17,874 protein-aspect units gained between 220 and 227, against 22,408 here.

The difference is what the gained side is subtracted against. The earlier count treated a term as
gained only if it was absent at t0 under **any** evidence code, so a term that already sat on the
protein electronically and became experimental within the window did not count. Under the
experimental baseline it does. **The benchmark's protocol is the experimental baseline**, since the object of
prediction is the experimental annotation and the electronic one was already public at t0, so its
promotion inside the window is a real gain. The knowledge split carries the "it was easy to
predict" concern on its own, and is itself defined on experimental annotations alone.

The promotion rate has since been measured directly: **7,002 protein-term pairs, 4,501
protein-aspect units**, which accounts for the whole of the gap between the two counts. The
correction is therefore arithmetic rather than a matter of judgement, and the nine-panel table
above is the restatement.

**What the correction does not disturb is the ratio the power argument rests on.** Measured on the
same footing, each window against its own pivot, the experimental cohort is **2.55 times** the
competitive one: 22,408 units against 8,792. By aspect the ratio runs 2.01 in BPO, 3.58 in MFO and
2.95 in CCO. The 2.5 the table above reports survives its own absolutes being conservative, which
is the property that matters, since the panels are sized by ratio and not by count.

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
index, which means the control flow of the recorded aggregation-order question has no input, and
the flow cannot be scored until it does. **Blocked**, with a named precondition: three reference
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
Every flow ever run retrieved by embedding nearest neighbour. Every stored candidate row carries an
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
model tables are empty and the flow field carries a single value in every stored result. Not
blocked in the sense the generator is, since the trainer and its inputs exist; blocked in the
sense that nothing has been trained on this platform.

### Combination and Routing
Downstream of nodes that have not closed. Declared, not scheduled.

---

## 3bis. What the design can lean on, which is structure and not magnitude

**This section previously claimed the opposite of its own source, and every magnitude in it is
withdrawn.** It read the campaign's leave-one-family-out ablation as measured "on a clean frame
with the excluded-known base applied". The signal registry records that row as measured *without*
that base, in the frame the project itself declared invalid, and marks it as not citable until
re-measured. The same registry downgrades the query's own prior to unmeasured-in-frame, and the
withdrawn table listed it among the flows with measured affinity.

**And the deeper correction is that this campaign never ran the flows at all.** Two group-bys
settle it: the 225 prediction sets carry one identical feature list, and all 1,296 evaluation
results carry the neighbour flow enabled and every other flow disabled. The other families'
columns are not zero in those rows, they are entirely null. An ablation that removes a null column
does not measure a zero; it does not measure.

So the affinity map has no measured content yet. What it has is structure, and the structure comes
from code rather than from a run, which is why it survives.

**The structural zeros re-derive themselves.** The lineage producer sets all four of its features
to zero for a protein with no known terms, by explicit convention: no known terms means no lineage
relation to report. The evaluator defines the no-knowledge cell as a protein holding no
experimental annotation in any namespace at the cut. Composing the two, every flow that reads the
query's existing terms is mute by construction in that cell.

| flow | mute by construction in | because |
|---|---|---|
| lineage | no knowledge, all three aspects | the producer zeroes it when the known set is empty |
| term association | no knowledge, all three aspects | it scores a candidate against terms the protein holds, and it holds none |
| the query's own prior | no knowledge, all three aspects | same, and empty in any panel where no protein holds a term of that aspect |

A zero that follows from a definition is not a measurement of unhelpfulness. It is the boundary of
where the flow can exist at all, and the graph carries it as a structural edge rather than a weak
one. Nothing here says the flows differ anywhere they are all defined, which is the interesting
half and the unmeasured one.

**The instrument that produced the withdrawn numbers is also the wrong one, independently of its
frame.** Leave-one-family-out measures marginal contribution given a combiner, not competence. A
flow the combiner ignores reads as zero whether it is useless or merely redundant with what the
combiner already trusts, and the two cases have opposite consequences for channelling. Built with
that instrument alone, the affinity map would record the combiner's habits and call them the
flows' competence. The replacement is a pair of quantities that do not depend on a combiner:
unique reach, and the fraction of that reach the combiner exploits.

So the design's premise is unproven rather than supported. That is not a weakness of the shape:
the claim was never the map. The claim is the single contrast, channelling against not
channelling, and the map is the mechanism it needs. Measuring the flows where they are all defined
is therefore the campaign's first obligation, not a step it may inherit.
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

## 6. What to build first, and it is not what the ladder would have built first

An earlier version of this section listed what was unblocked. That is the wrong ordering
principle and it produced a concrete error: it named the floors census as the foundation without
naming **which contrast class** the floors belong to, and the census that was started measures the
wrong one.

**The order comes from what the claim needs.** The claim is that channelling beats not
channelling. Work backwards from it.

**First, a candidate must be able to say which flow proposed it.** No schema carries that today.
Every stored candidate row records the donor it came from and the distance that found it, which
is a complete description of one flow and no description at all of the others. Until a proposal
carries its source, unique reach cannot be computed, affinity cannot be measured, and the
difference between "no flow proposes this" and "we did not record who proposed it" is invisible.
This is the smallest change in the list and everything else waits behind it.

**Second, every result row must carry its frame.** The column exists and is empty in all of them,
and a substantial block of existing results cannot be attributed to a frame at all because the
jobs that produced them are gone. A number that cannot be attributed cannot be compared, and the
graph's central property, that reopening is computable, is worth nothing while the source node
has no stamped edges.

**Third, the scoring node, which is a re-read.** It needs neither accelerator nor new artefact,
and it addresses the axis the record says absorbs the ones above it. It is the one node that can
close with what exists.

**Fourth, and only fourth, the floors.** And here the correction matters more than the ordering.
A floor is a property of a contrast class. The class this campaign has measured, indirectly and
once, is **one configuration of a flow against another configuration of the same flow**: two
backbones, two depths, two encodings. **That is not the contrast the graph runs on.** Admitting a
flow into a region compares a system that has a whole source against one that does not, and
nobody has measured the variance of that difference. There is no reason to expect it to resemble
the one on record, and every unpowered declaration in section 5 rests on the resemblance.

So the census is not one census. It is one per contrast class the graph will actually run, and
the first of them is flow admission, which cannot be measured until a candidate carries its
source. That is the dependency the ladder's ordering hid.

**A separate blockage, which is real and belongs to the old contrast class.** The per-protein
artefact that a configuration-versus-configuration census would be built from does not reproduce
the score it should recompose, by an amount of the same order as the effects the graph must
resolve. The instrument that would have caught this is named in the producing code's own
docstring and was never written. Whatever is decided about that artefact, **the correct next step
is to write that check on a case where the answer is known by construction**, not to rebuild
anything: it costs an afternoon and decides between correcting a formula and regenerating
thousands of files. Until then this edge is **blocked**, and its missing producer is a
verification rather than a file.

**Two small separations that cost one run each.** Window from donor policy, since every set on one
bank is gated and every set on the other is permissive. And the identity control between the two
search backends, which should be asserted once rather than modelled as a choice.

## 7. What this instantiation does not decide

It does not choose a champion, and it does not rank anything. It records where each edge stands so
that the first node to close has somewhere to write its answer.

It does not fix the floors. It names the one that exists and says the rest are pending.

And it does not schedule. The order in section 6 is what the claim needs, worked backwards from
the contrast the campaign intends to run. What is unblocked is a different question and a weaker
one, and reading the list as an availability order is the error that sent the first floors census
at the wrong contrast class.
