# The experiment graph: what is decided, what is declared, and what a decision is allowed to carry forward

This replaces the linear ladder as the structure of the campaign. It does not replace
`CAMPAIGN.md`, which carries the reasoning, nor `ABLATION-ARCHITECTURE.md`, which carries the
arithmetic of what the benchmark can resolve. It carries the shape.

**This document is abstract on purpose.** It names objects, rules and edges. Every number lives
in the instantiation that follows it, so that a change of cohort, of release or of budget
rewrites the instantiation and leaves the shape standing. A shape that has to be rewritten when
the numbers move was never a shape.

## The vocabulary, because one word was carrying an argument

A **source** is where an annotation comes from: annotated donors, the label space itself, the
query's own prior, term co-occurrence, literature, an interaction network, a structure.

A **flow** is a source plus a mechanism of propagation. Neighbour transfer over an embedding is a
flow. Running the same transfer over a different embedding is **not another flow**, it is the same
flow configured differently, and failing to make that distinction is why two closed steps of the
ladder ended without a winner: they varied the space of one mechanism and never the mechanism.

**Affinity** is what gets measured: the set of regions in which a flow contributes above that
region's floor. It is a set, not a score, which is why it admits no global ordering.

**Channelling** is what gets built from it: the policy that admits each flow into its regions.

The word **arm** is retired. It comes from trial and bandit designs, where the variants are
interchangeable, one of them wins, and the comparison is global. None of those hold here, and the
term made it grammatical to write "the winning arm", which is a sentence this campaign has no
evidence for and has twice been unable to write honestly. A flow is not selected. It is channelled.

## Why the ladder is being replaced, in one paragraph

A ladder makes position mean dependency. Five consequences followed, all of them observed rather
than feared. A rung held "the winner of the rung before" when that rung had closed without a
winner, so a preference propagated wearing the clothes of an answer. Rungs measured a narrow axis
while holding a wider one still, three times, and the file that records the ladder says so itself.
A step whose result changed nothing downstream had nowhere to sit except the end. The largest
measured lever had no step at all, because the gate type was a property of depth rather than of
the question. And reopening had exactly one possible scope, everything above, because a list has
no other notion of downstream.

Each of those is a symptom of linearity, and a graph removes them structurally rather than by
convention.

---

## 1. The declaration: what is not a node

A node is a decision. Several things that look like decisions are not, and modelling them as
nodes fabricates choices nobody makes and blocks work on questions nobody asked.

**The frame** is declared, never measured. It is modelled as a source node with no levels, no
experiment and cardinality one, whose outgoing edges reach every other node. That costs nothing
and preserves the property that makes the graph worth having: if the frame moves, and the record
says it will, what is invalidated is computable rather than a judgement call. A frame that is
merely stamped gives attribution and not invalidation.

The frame includes the metric and its weighting, which are not decoration: with the rank declared
per panel, they are what orders every edge in the graph. And two of its members are reconstructed
at cost rather than chosen freely, the excluded-known base above all, whose omission moved a
published cell by more than the lever the same page was arguing for. The ontology pivot, the release pair, the side the
information accretion is taken from, the base of the excluded-known denominator: these are
conventions, and a convention's value is chosen and written down, not discovered. Making the
frame a node stalls the whole graph behind a question that has no experiment.

What the frame owes in exchange is absolute: **it is stamped on every row of every result.** The
project's current state is the argument for this rule rather than against it, since the frame
column exists and is empty everywhere, and a large block of existing results cannot be attributed
to a frame at all because the jobs that produced them are gone. An unstamped result is not a
cheap result, it is an unusable one.

**The mandatory partition** is not an axis. Category by aspect partitions the units and the
panels never merge, never pool and never take a third axis crossed into them. That follows from
population arithmetic, not from preference, and `ABLATION-ARCHITECTURE.md` derives it.

**The reporting coordinates** are not axes either. Length, homology, reach and taxonomy are
properties of a protein, a sequence and a frozen bank. They are printed beside every result and
never crossed into the partition.

**The stratifier's bank is part of the frame, and it is not the Bank node.** The two share a
word and are different objects. Reach and homology coordinates are keyed on the protein and on a
reference bank at a stated cut, so if the coordinate bank moved with the node, two flows differing
in donor eligibility would receive different band membership. Admitting weaker donors raises the
identity of the best annotated neighbour without raising that of the best experimental one, which
widens the gap and migrates proteins toward the levels the thesis is about. The bias runs the
flattering way, exactly as in the case the rule was written to forbid. No edge moves the
stratifier's bank.

Their governing rule is structural and it is the one most easily broken: **a coordinate must
never depend on the flow.** If membership of a band depended on which neighbours a flow retrieved,
two flows would be scored on different populations under one heading, and the bias would run the
flattering way, because a better representation promotes its own easy cases into the easy bands.
The stratifier is frozen sequence space. What is flow-dependent is not discarded, it is promoted
to a statistic of its own and reported as such.

**The floors** are declared before a comparison runs and are properties of the comparison, not of
the graph. Two flows that share their retrieval and differ in one downstream knob have a small
one; two flows that retrieve different neighbours have a larger one. A floor therefore lives on
the edge being tested, and a single global floor is a category error. Whether a comparison takes
a resolution floor or a selection floor depends on whether it was declared before it ran or is a
maximum over a search, and that distinction has already decided two opposite verdicts about
numbers of the same size.

**Knobs with no second reachable value** are not nodes. A field that can only take one value
under every configuration the system can express is a constant with a settings entry, and the
graph must not pretend otherwise. The audit that preceded this document found a substantial
number of them.

**External comparison is not a node.** Other methods run on their own inputs, under their own
temporal discipline or none, and no gate can be hung from them. They are a reporting surface and
belong in a section, not in the graph. That is a statement about structure and not about their
importance: the surface may be the most read page of the thesis.

---

## 2. The two cohorts

The graph runs on an **experimental cohort**, chosen for size, and its decisions are projected
onto a **competitive cohort**, which is a blind holdout touched exactly once.

Three consequences, and the third is the one that gets forgotten.

Everything is fixed inside the experimental cohort: floors, thresholds, neighbourhood depth,
preset choice, and every propagation decision. Nothing may be tuned on the holdout, including by
inspection.

The two cohorts must not overlap temporally, or the holdout is not blind. Overlap is checked and
asserted, not assumed, because the check is cheap and the failure is silent.

And the projection is a single terminal edge, which means **its floor is priced against the
search budget of the entire graph**, not against the last node's. A graph that explores widely
and projects once has made one maximum over everything it explored. Pricing that terminal against
a resolution floor would be the same error the campaign has already caught in a smaller form.

---

## 3. The nodes

A node is a decision about one field or one group of fields that cannot be moved apart. It
carries a question, the field or fields it varies, its incoming edges, a gate with a declared
type and floor, and the value or values it leaves decided. It also carries two things a linear
ladder kept and the first draft of this document dropped, and both are load-bearing.

**The rank**, the quantity the configured flows are ordered by, declared per panel. Without it the propagation
rule below silently requires one scalar over nine panels, and the only scalars available are the
aggregates this project has proscribed.

**The evaluation context**, the explicit value of every undecided downstream field held still
while this node is measured, each with its strength. A node measured without that declared
reproduces the campaign's own recorded failure, in which one unset scoring field made a
neighbourhood-depth axis measure something else entirely and made the unset axis worth several
times the one under study. Without this field that failure is available at every node, by
structure rather than by oversight.

**A node is not an experiment.** The experiment is how a node closes. One node may need several
runs, and one run may inform several nodes.

The graph's spine is the pipeline, because that is what makes it a graph rather than a list: each
stage consumes what the stage before produced, and a node lives at the stage whose behaviour it
changes.

- **Substrate.** What a protein becomes. The backbone, the depth, the grain and the order in
  which sparsification and aggregation are applied.
- **Bank.** Which donors are eligible. The evidence regime, the review status, the exclusions.
- **Retriever.** How neighbours are found in that bank. Held by every flow ever run and never
  declared as a choice, which makes it an inherited edge and not a constant.
- **Generator.** What proposes candidates that retrieval cannot reach, because retrieval can only
  offer what a neighbour already carries.
- **Scoring.** What order the candidates take and where the threshold falls.
- **Features.** Which signal families the scorer is allowed to read.
- **Combination.** Whether several models beat the best one, and by a mechanism that can be
  named.
- **Routing.** Whether different flows should serve different panels, which is the only node whose
  output is a policy rather than a value.

Two properties of this spine matter more than its contents.

**Adjacency is not dependency.** Substrate and bank sit at different stages and neither decides
the other, so they are measured in parallel. The pipeline orders the data, not the work.

**Cost is not uniform along it, and that changes what each node may be measured against.** A node
whose evaluation is a re-read of stored predictions can afford to evaluate an entire incoming
set. A node that costs a forward pass over the corpus cannot, and must be measured against a
single representative. **Which nodes may see the fan and which may not is therefore a property of
the graph, declared here, and not a decision taken per run.**

---

## 4. The edges

An edge says: this node holds that field at the value the node before it decided. It carries
three things.

**A value, or an ordered set of them.** The single value is the special case, not the norm.

**A strength**, of which there are five. **Measured**, where a declared comparison separated
against its floor. **Chosen**, where a comparison ran with power and did not separate, so a value
was picked and recorded as a preference. **Inherited**, where nobody ever decided and the value is
what it has always been. **Unpowered**, where the comparison could not have separated whatever the
truth was, because the population available was below the floor its own contrast class implies:
computed before the node runs, never discovered after, and emitting a request for data rather than
a fan. **Blocked**, where a level cannot be produced at all because its artefact has no producer,
which is this project's storage invariant expressed as a property of the graph.

The distinction between chosen and unpowered is the one most often lost and the most expensive to
lose. A null from a comparison that could not have resolved anything is not a negative result. It
measured nothing, and reading it as evidence of sameness is how a preference acquires the standing
of a finding.

That third strength is the one the ladder could not express, and it is the most common. It also
makes the graph's most useful query possible: **which conclusions rest on weak edges?** In prose
that question has an answer nobody reads. As a property of an edge it has an answer anyone can
compute.

**A cardinality, which is a vector over the panels and not a scalar.** Evidence is per panel, so
resolution is per panel, and one number cannot carry a verdict that differs across nine
populations. Collapsing it fails in both directions: resolving when any panel resolves imposes the
winner of a small panel on a large one, which is an aggregate result under another name; resolving
only when every panel does never collapses at all, because the arithmetic already says some panels
cannot resolve anything.

And because edges are typed, **reopening is computable.** If a node's answer changes, what is
invalidated is the transitive closure of its outgoing edges. Not everything, and not a judgement
call.

---

## 5. Propagation

**A node that does not resolve is not a failure. It is a branch.**

This is the rule the ladder could not express, and it changes what a negative result means. Two
of the campaign's closed steps ended without a separation and were recorded as choices made
without evidence. Under this rule they are edges of multiplicity, which is what the measurement
actually said.

**What an edge carries.** Where the node resolved against its declared floor, one value. Where it
did not, the top several by point estimate, ordered. The count is the edge's own parameter,
declared before the node runs.

**What an edge carries, per panel.** In a panel with power, the top several by that node's
declared rank. In a panel without power, the whole incoming set, at strength unpowered. What
propagates is the union over panels, and **an unpowered panel never widens the fan the next node
evaluates**, because a ranking drawn from a comparison that could not resolve is a lottery, and
nine lotteries unioned approach the complete set of levels. The fan is therefore determined by the
panels where the thesis claim lives.

**How the fan is kept finite.** Each node re-ranks the cartesian product of all its incoming sets
and its own levels, and keeps the top several again. The width of what travels does not compound
along a path; **the cost of computing it does**, at every node where two parallel branches meet,
and that cost is what decides whether the scheme runs at all. Which nodes are permitted to sit at
a confluence is therefore declared, not discovered per run.

**The truncation is stratified by what is still unresolved upstream.** At least one survivor is
kept for every value an incoming edge declares alive. Without that rule, a node can silently
settle a question belonging to a node above it: three tied substrates arrive, the top three of the
product all happen to carry the first, and the substrate has been decided by an experiment about
something else, with no gate, no floor and no record, while its edge still claims a cardinality it
no longer has. That is a preference propagated wearing the clothes of an answer, which is the
failure this document opens by naming, and the arithmetic says it is the expected case rather than
the rare one wherever an axis does not separate.

If the budget cannot hold one survivor per live value, the node declares that **it** is reducing
the incoming cardinality, and that reduction is a decision of its own with its own floor. The
effective width is reported as the smaller of the declared count and the number tied, so an edge
says when the parameter bit.

And where a node resolves in a panel, its outgoing edge collapses to one **in that panel**, so the
fan survives only where the data declined to decide.

**Where the fan may be evaluated.** Only at nodes whose evaluation is cheap. An expensive node
evaluates its whole incoming set through a cheap surrogate and pays the full price only for the
resolution itself. It may not simply take the leader: this project has measured three times that
the winner of one axis changes with the value of another, so a leader ordered under the previous
node's context can be the worst choice for this one, and the substitution would be unauditable
precisely where nothing else was evaluated.

Where an interaction between two fields has been measured, the two fields are one node, by the
rule this document already states: one field, or one group of fields that cannot be moved apart.

**Cost enters the order.** Among flows whose intervals overlap, the edge orders by ascending cost
and the point estimate breaks ties only at equal cost. Otherwise a flow that wins by a margin
smaller than its own floor, and costs a corpus pass more than the flow it beat, fixes an expensive
branch and the terminal projection with it.

**Evidence is always per panel.** A node resolves in a panel or it does not, and a node may
resolve in some and not others. The graph carries one traversal and the per-panel structure lives
in the evidence, not in the topology. Whether that structure should become a policy is the
routing node's question, asked once at the end, rather than nine traversals asked implicitly
throughout.

---

## 6. The terminal projection

The holdout is touched once, and the discipline that makes one contact worth having is not
restraint about how much crosses. It is that nothing is chosen after looking.

**Selection bias comes from selection, not from multiplicity.** Crossing many flows biases nothing
by itself. Choosing among them once their numbers are visible biases everything. So the whole
propagated set crosses, every flow is reported in every panel, and the analysis is fixed before the
contact rather than trusted afterwards.

**What is fixed in advance, and sealed.** Which flows cross. Which panels are reported. The metric
and its weighting. The rule that determines each floor, though never its value, since that depends
on per-panel populations not known until the contact. The one flow designated as the headline. The
multiplicity correction over the declared family. And what is done if the ordering disagrees with
the experimental cohort, which is that the experimental leader stands.

The seal is what makes those statements true rather than intended: the analysis is a registered
operation whose payload is content-addressed and committed before the holdout is read, so what it
emits was decided by someone who had not seen it. A promise not to look leaves the counterfactual
available; a signed plan removes it, because the headline cannot be changed afterwards without the
change being visible.

**What this buys.** Per-panel results for every propagated flow rather than a single number,
priced under a correction over a family declared in advance. An agreement statistic against the
experimental cohort. And a transfer claim, which is the thing the project has never had: whether a
decision taken on a large cohort holds on the one that counts.

**What it still refuses.** The holdout cannot resolve a tie, because resolving one is selecting.
It can describe whether the tie persisted, as a pre-registered observation from which no decision
follows. That distinction is the whole of the blindness, and it is also arithmetic: a tie was
declared a tie because a difference failed to clear a floor on the larger cohort, and the holdout
is not larger, so the same difference cannot clear a stricter floor on fewer proteins except by
noise.

**Two claims, two floors, two cohorts, and an early draft assembled them backwards.** The claim
that a flow is the best of what was searched belongs to the experimental cohort and takes a
selection floor, priced against the search budget of the whole graph. Each claim the holdout makes
is a comparison declared before it ran and takes a resolution floor, adjusted for the declared
family. The maximum lives upstream, never at the terminal.

**This supersedes the prohibition on a second holdout** recorded in the campaign, and the
supersession is stated rather than assumed. That prohibition exists because holding out twice
invites reporting whichever came out better. Under a sealed plan that is not available: the
headline was named first, every other flow was named first, and a flow that was not named cannot be
promoted. The rule was right about the failure it named, and this design closes that failure
rather than stepping around it.

## 7. What the campaign claims, and what the map is

This section exists because an earlier draft got the two backwards, and the error is the kind
that survives review by looking like rigour.

**The affinity map is the mechanism. It is not the claim.**

The map holds one decision per flow per region, and it is the worst estimated object in the
design: with several flows over a few dozen regions it is hundreds of contrasts, the standard
error grows as the region shrinks, so **spurious affinity concentrates in the small regions**,
and the small regions are the ones that motivate the design. Proteins in a region are homologues
rather than independent draws, so the effective population is a fraction of the counted one.
Corrected for multiplicity, the effect a cell must show to be admitted is larger than any effect
this project has ever measured in those cells. **In the regions that justify the design, the map
is close to unidentifiable, and a design whose headline is its least identifiable object is
indefensible however carefully it is measured.**

**The claim is a single contrast, declared before the holdout is touched: does channelling beat
not channelling?** Concretely, does the regional policy beat the best single flow applied
everywhere, and does it beat the flat consensus of all admitted flows. That is one comparison, it
has power, and it is what the projection is for. The map is how the policy is built, published
beside the claim as a description rather than as a result.

Three consequences follow and none of them is optional.

**The map is published in three colours, never two.** Admitted, not admitted, and
**indeterminate for want of power**, with each region's minimum detectable effect printed beside
it. Two colours over a lattice whose power varies by an order of magnitude is misleading by
construction: it renders "we could not tell" and "we could tell it does not help" in the same ink.

**An empty region has three explanations and the design must separate them.** No signal, no
power, or **redundancy**: several flows that agree can each fail a marginal test while the set is
strong, so a region can be empty precisely because everything works there. A leave-one-out
measurement cannot tell those apart, and the campaign's own record contains the trap already: one
flow measures exactly zero in a region and turns out, measured alone, to beat the full combiner
there. **Marginal contribution is not usefulness.** Whatever instrument builds the map must
measure both, or the map will record the combiner's habits rather than the flows' competence.

**And a flow may not be credited with competence on the coordinate that defines it.** One
reporting coordinate is built from the statistic that gives one flow its advantage, so routing by
it and then asking whether that flow is competent in those bands guarantees the answer. Which
flow shares a statistic with which coordinate is declared, and no competence claim is made along
a shared axis.

## 8. What this shape will not do

It will not make a small panel large. Where a panel lacks the population to resolve an axis, a
graph resolves nothing a ladder could not, and the arithmetic that says which panels those are is
already derived elsewhere and is not softened here.

It will not order the work by importance. It orders by dependency, and those are different. A
node that matters enormously may sit behind a node that matters little, and the graph makes that
visible instead of implying the order was a ranking.

It will not prevent a fan from being an evasion. A branch that never collapses is a decision
deferred forever, and the discipline that stops it is not structural: every unresolved edge is
reported with the count of proteins that would be needed to resolve it. A branch that is expected
to stay open is a request for data, and it is written as one.

It will not remove the need to declare. Nothing above works unless the frame is stamped, the
floors are named before the comparison, the cohorts are asserted disjoint, and the propagation
count is fixed in advance. The graph makes those obligations visible and computable. It does not
make them optional.
