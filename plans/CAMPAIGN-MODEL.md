# The campaign model: the universe the graph runs over, what a flow is, what a region is, and what channelling claims

## What this adds to `EXPERIMENT-GRAPH.md`, and what it does not repeat

`EXPERIMENT-GRAPH.md` carries the shape: nodes, edges, the five strengths, propagation, the fan
and its truncation, the terminal projection, and the separation between the affinity map and the
claim. All of that stands and none of it is restated here.

What that document does not carry is the layer of objects its edges quantify over. It says a
coordinate must never depend on the flow, and does not say what a coordinate is or what a region
is. It says affinity is a set of regions in which a flow contributes above that region's floor,
and does not define a flow, a floor, a contribution or a region. It says the map is published in
three colours, and does not say what makes a colour. It says floors are properties of comparisons,
and does not enumerate the comparison classes.

This document is that layer. It defines the universe, defines a flow and its two halves, defines
a region and the stratification rules, defines affinity as a set and the instrument that measures
it, defines the channelling policy and the single claim, and states the floors as properties of
contrast classes.

**It holds no numbers and no instance decisions on purpose.** Every population, every band edge,
every release pair, every floor value and every producer name lives in the instantiation. Where an
obligation exists but cannot be discharged abstractly, this document names the obligation and says
which document owes the value. Where a choice remains open it is named as a declared parameter with
a stated default and a stated cost, not left implicit.

Two amendments to the parent are made explicitly rather than silently, and both are marked in
place: the map is published in **five** inks rather than three (section 4.4), and the parent's two
statements about the terminal floor are reconciled in favour of the second (section 7.1).

---

## 1. The universe

Nine kinds of object, and every one is exactly one of three things.

**Declared.** A convention. Written down before anything runs, with no experiment, its value
chosen rather than discovered. Making a declared object a node fabricates a decision nobody takes
and stalls the graph behind a question with no answer.

**Measured.** Produced by a registered operation, carrying a population and a frame stamp. A
measured object without a stated population is not a measurement.

**Derived.** Computed from declared and measured objects with no remaining freedom, reproducible
from its inputs, and moving when they move.

| object | status | who fixes it |
|---|---|---|
| the frame | declared | the instantiation, once, stamped on every row |
| the corpus | measured | ingestion |
| the release series | measured | ingestion |
| a window | declared | the instantiation |
| a cohort | declared role, measured content | the instantiation declares the role before the window is generated |
| a unit | derived | the ground-truth builder |
| the mandatory partition | declared rule, measured membership | the rule is a definition, membership follows from the units |
| a coordinate | declared definition and reference bank, measured values | the frame declares, a producer measures |
| a region | declared family, measured population | the family is declared in full before any result is read |
| a source | declared | an inventory is a list, not a finding |
| a mechanism | declared | it is code |
| a flow | declared | source plus mechanism, both declared |
| a configuration | declared per run | the fields the mechanism exposes |
| a candidate | measured | a generator |
| the pool | derived | the union of the admitted flows' candidates |
| the combiner | declared form, measured parameters where fitted | the instantiation names the fitter or marks the node blocked |
| a floor | derived | from a measured variance on a declared contrast class and a declared population |
| affinity | measured | per flow, on the decision cohort only |
| the channelling policy | derived under a declared rule, fitted where the rule has a free parameter | the routing node |
| the claim | declared, then measured once | sealed before the holdout is read |

Two rows of that table need their status defended, because an earlier draft got both wrong.

**The policy is derived only when its admission rule has no free parameter.** A rule of the form
"admit every flow clearing the floor" is derivation. A rule of the form "admit the best few" or
"admit a fixed number per region" carries a fitted parameter, and a policy built from it is fitted.
The instantiation states which it uses and counts the parameter.

**A floor's population is declared, not measured from the run.** See section 3.2's corollary and
section 7.3.

### 1.1 Corpus, releases, windows, cohorts

The **corpus** is the set of proteins the campaign can represent: identity, sequence, length, and
where the machinery has run, a vector under some substrate. Membership is measured and moves when
ingestion runs.

The **release series** is the ordered sequence of annotation states of that corpus. It is
measured, and its most important property is that it is not monotone: a release can hold fewer
annotations than its predecessor. Ground truth is therefore built from what appears, never from a
net difference between two totals.

**"Appears" has two admissible definitions and they are not the same object.** The first is
absent at the window's opening and present at its closing. The second is present at the closing
and never present at any earlier cut in the series. The second is the stronger primitive, because
under the first a term withdrawn during the series and restored inside the window is scored as new
knowledge while the donor bank already holds it, which is a leak in the flattering direction and
is concentrated at the contraction points rather than spread evenly. The instantiation declares
which definition it uses, names the producer, and where it uses the weaker one it states the
residual as unmeasured rather than carrying an average as a correction.

A **window** is an ordered pair of releases, the earlier one its opening and the later one its
closing. It is declared. Everything the campaign scores is a statement about what a window added.

A **cohort** is a window plus a **role**, and there are exactly two roles.

- The **decision cohort** is where every comparison runs, every floor is estimated, every
  threshold is tuned, every value is chosen and every affinity is measured.
- The **holdout cohort** is read once, under a seal, and nothing is chosen after reading it.

The role is declared before either window is generated, because a window generated without its
role recorded is a window whose role can be assigned afterwards, which is the failure the role
exists to prevent. Where the platform allows a role to be stamped or rebound after generation, the
instantiation names that path and says how it is closed.

**Disjointness has two senses and the weaker one is not sufficient.** Two abutting windows are
temporally disjoint by construction, and their sets of gained protein-term pairs may be exactly
disjoint, while the same proteins appear in both. A protein whose units set a threshold in the
decision cohort and whose other units are scored in the holdout is not a fresh draw. Both senses
are asserted and both numbers are published, with their denominators. Where the protein overlap is
material the instantiation declares, before the seal, whether the holdout claim is made on all
units or on the protein-disjoint subset, and states that subset's population.

A third property is not disjointness at all and must be stated beside it: **the two windows may
differ in elapsed time**, and a difference in duration is a difference in how much annotation
accumulated, not a difference in sampling. Any statement of the form "the decision cohort is
larger" says how much of the ratio is duration.

### 1.2 The unit, which is not a protein

The **unit** is the atom of observation: a protein together with an aspect, or with a term where
the metric works at term granularity, which the window added. Three properties are load-bearing
and all three follow from the definitions.

**A protein contributes several units.** They share a sequence, a neighbourhood and a taxonomy, so
their errors move together. Every interval in the campaign resamples proteins and moves a
protein's units as a block. Inside one panel a protein usually contributes exactly one unit, so
that rule is inert there and must not be quoted as though it were doing work; it binds wherever
anything is computed across panels, including any declared aggregate used to construct a
comparator.

**The knowledge categories are not defined at one granularity.** The no-knowledge category is a
property of the whole protein at the window's opening; the other two are properties of a protein
within an aspect. The categories therefore partition the units and do not partition the proteins.
Any statement of the form "the proteins in this panel" is ambiguous unless it says whether it
means the units' proteins or the proteins whose every unit lands there. The model requires the
first reading and requires it to be stated.

**A unit's existence depends on the frame.** The pivot decides which terms carry an aspect at all,
and a term the pivot does not carry disappears silently. Panel membership is frame-dependent, not
only panel scoring, and when the frame moves the populations move with it.

### 1.3 Sources, mechanisms, flows, configurations

A **source** is where an annotation could come from: annotated donors, the label space itself, the
query's own prior, term co-occurrence, literature, an interaction network, a structure, the query's
own record. The inventory is declared. It is a list of evidence channels, not a list of models.

A **mechanism** is the procedure that turns a source into candidates for a query.

A **flow** is a source together with a mechanism. Section 2 does the work.

A **configuration** is an assignment of values to the fields a mechanism exposes. It is what the
graph's nodes vary.

### 1.4 The two banks, which share a word and are different objects

The **donor bank** is the set of proteins a retrieval mechanism may transfer from: an eligibility
policy over the corpus at the window's opening. It is a node of the graph, and edges move it.

The **reference bank** is the fixed set of sequences against which the reporting coordinates are
computed. It belongs to the frame. **No edge moves it.** If it moved with the donor bank, two
flows differing in donor eligibility would receive different band membership, and the bias would
run the flattering way, because admitting weaker donors raises the identity of the best annotated
neighbour without raising that of the best experimental one.

Two banks, two owners, one word. The instantiation states both cuts separately even when they
coincide, and states that the reference bank is a single object shared by both cohorts, since a
reference bank that differed between them would make the terminal projection a comparison of two
band memberships rather than of two systems.

---

## 2. Flows, formally

### 2.1 Identity: the source decides, the field test is a heuristic

A flow is the pair (source, mechanism). Two runs are runs of **the same flow** when they share
both members of the pair, however far apart their configurations sit.

**Identity is grounded on the source first.** Two runs whose candidates carry information from
different evidence channels are two flows, whatever field of whatever payload happens to switch
between them. This ordering matters because implementations acquire umbrella switches: a single
boolean that turns a whole second source on or off makes the two runs reachable from one another
by a field value, and a test that reads only fields would then classify a flow admission as a
configuration change and price the campaign's central contrast against the wrong variance.

Where the source is the same, the **field test** decides the mechanism half: is there a field, of
either mechanism, whose value carries one run to the other? If yes, one mechanism configured
differently. If no, two mechanisms and therefore two flows.

Applied: neighbour transfer over one representation and neighbour transfer over another are one
flow, and so are the same transfer at a different neighbourhood depth, over a different donor bank,
or scored by a different preset. A mechanism reading the query's own sequence features is a
different flow, because its source is different. A learned reordering of an existing candidate
list is **not a flow**: it proposes nothing, it has no source of its own, and it is a property of
the combiner.

### 2.2 Why the distinction is load-bearing, in four ways

**It is what the claim is about.** The claim is that different evidence channels are competent in
different regions. Varying a configuration measures a mechanism's sensitivity to a knob. Varying a
flow measures whether a channel carries anything the others do not.

**It is what the floors are about.** Two configurations of one flow share most of their machinery
and the variance of their difference is small. Two flows share almost none and the variance of
their difference is unmeasured and expected to be larger. A floor borrowed across that boundary
prices the wrong experiment.

**It changes what an edge carries.** A configuration is a level of a node and propagates as a
value or an ordered set of values. A flow is a member of the pool and propagates as an admission.
Conflating them makes "the winner" grammatical where no comparison was run.

**It fixes what can be counted.** Unique reach asks what would become unreachable if a flow were
removed. That is well posed for a flow and meaningless for a configuration, because removing a
configuration leaves the mechanism standing.

### 2.3 The two halves of a flow, and the two ways a half can be missing

A flow has a **generator half**, which proposes candidates, and a **scoring half**, which annotates
candidates already in the pool with a signal derived from its source.

The halves are independently buildable and independently missing.

**A source may be readable as a signal on somebody else's candidates long before anything can
propose from it.** That state is common and it must be recorded as what it is: a flow **whose
generator half is unbuilt**, carried as a blocked edge, not renamed a feature. Renaming it a
feature hides a generator opportunity behind a feature-selection question, and it makes the source
invisible to every reach quantity in section 4, all of which are defined on proposals.

**The mirror case is the one an earlier draft missed, and it is the more dangerous of the two.** A
generator half can exist and propose candidates that **no scorer in the system can read**. A
candidate carrying only a signal outside the scorer's vocabulary receives whatever the scorer does
with an absent signal, and every plausible implementation of that is wrong in a way that looks like
a result: it scores the candidate at the bottom of the ranking, or at the top, or renormalises the
weights of a different set of signals. In all three cases the flow's unique candidates are invisible
or spurious, the contrast reads as no signal, and the node reports that the source reaches nothing.

**The rule.** A flow is measurable only when both halves exist **and** the combiner's signal
vocabulary includes the flow's signal. Until then the edge is blocked, and the missing consumer is
named as its precondition exactly as a missing artefact would be. A node whose only consumer does
not exist cannot be measured, only prepared, and that applies to a generator with no scorer as
much as to a feature set with no booster.

**Only the generator half can be admitted or cut.** Admission is a statement about which candidates
exist. A scoring half is a question for the features node, not for the routing node.

### 2.4 Admitted, cut, mute, propagated

Four verbs, and three are routinely confused.

**Admitted in a region.** The flow's candidates enter the pool for units in that region and the
combiner may read its signals there. Admission is per region and per flow.

**Cut in a region.** The flow's candidates do not enter the pool there. A cut is a policy statement
about where a source is used. It is not a verdict that the source is worthless and the report must
never render it as one.

**Mute in a region.** The flow cannot produce output there for a definitional reason: its source is
empty for every query the region contains. Muteness is derived from the definitions of the flow and
of the region, before any measurement. It is not a cut, not a null and not an absence of signal.

**Muteness is derived from the flow's actual source predicate, never from the region's name.** A
region defined by the absence of one kind of evidence does not make mute a flow that reads a
different kind. Getting this wrong writes a live source out of the design before any measurement,
in exactly the region the thesis claim lives in. The instantiation lists each mute cell with the
code path that establishes it.

**A structural zero is a zero, and an absent value is not a zero.** A producer that emits an
explicit zero for an empty source is mute. A producer that emits a missing value renormalises the
combiner over the surviving signals, which changes the score rather than leaving it unchanged. The
two must not be filed under one heading, and which a producer does is a code fact the
instantiation records per flow.

**Propagated along an edge.** The graph's traversal carries this flow, or this set of
configurations, forward. Propagation is about the graph, admission is about the policy. A flow can
be propagated and then cut in most regions, and a flow cut in every region is still propagated to
the terminal so that its per-region result is published.

---

## 3. Regions and stratification

### 3.1 The mandatory partition

The **partition** is the cross of the knowledge categories with the ontology aspects. Its cells are
the **panels**. Panels never merge, never pool, and the partition never takes a third axis crossed
into it.

**Each panel is its own population.** A protein enters a panel only if the window gave it a unit of
that aspect under that category, so different aspects score different sets of proteins and the
panel populations differ by a large factor. The panels are separate experiments sharing a query
set, not one table read several ways.

**Panels do not partition proteins**, only units.

**There is no aggregate as a result.** Not as a headline, not as a tie-break, not as a convenience.
A quantity that pools panels weights the low-knowledge regions, which carry the claim, by the
population of the prior-knowledge regions, which do not.

**One exception, declared and narrow.** A comparator sometimes has to be a single system applied
everywhere, and defining one requires an ordering across panels. **A declared aggregate may define
a comparator. It may never carry a verdict.** The aggregate's form and weighting are fixed in the
seal before any panel number is read, it appears in the report only as part of the comparator's
definition, and no difference claim is ever stated in it. Without this exception the flat
comparator is unconstructible and the claim has nothing to beat; with it unrestricted, the
no-aggregate rule is void.

### 3.2 Coordinates, and the invariant

A **coordinate** is a function from a protein, the frozen reference bank and the frame, to a level
of a declared, ordered set of levels. A coordinate's definition, its level boundaries and its
reference cut are declared in the frame and frozen before any flow is scored. A level is never a
missing value: "no reference sequence qualifies" is a level with a name.

**The invariant, stated on membership and not only on values.**

> For every coordinate, every protein, every flow and every configuration, the coordinate's value
> is invariant under the flow and under the configuration. **And so is the protein's membership of
> its panel and of its region.**

The second sentence is the amendment, and it is where the parent's rule leaks in practice. A
stratifier that drops a protein it cannot place, because the run under test retrieved no usable
donor for it, produces a region whose population is a property of the arm. Two flows are then
scored under one heading on different populations, and the bias runs toward whichever flow
retrieves less, since the proteins it fails on are the hard ones. A coordinate may read the query,
the frozen reference bank and the frame, and nothing else; a **placement failure is a level**, and
where the implementation drops instead of placing, that is a defect with a named producer, not a
caveat.

**The failure mode has four faces** and they are worth naming once: two flows scored on different
populations under one column heading; a bias that runs the flattering way, because a better
representation promotes its own easy cases into the easy bands; a flow credited with competence on
the coordinate its own statistic defines; and an affinity map that records the machinery instead of
the flows. The last is the worst because it is invisible from inside the map.

**Corollary one, the population.** A region's population is a property of the ground-truth
artefact, computed once per cohort and joined in. It is never taken from a count of the rows a run
placed, or of the proteins a run predicted at its own maximising threshold, because such a count
moves with the operating point on a provably identical cohort. Any report-time floor that reads a
run-derived count is reading the thing under test.

**Corollary two, promotion.** A flow-dependent quantity is not discarded. It is **promoted to a
reported statistic** of the configuration that produced it, published per configuration and never
used to define a population. The sharpest, threshold-free and combiner-free form of the thesis
claim lives there: at what rank and at what identity a configuration first reaches a donor carrying
evidence of a declared kind.

**Corollary three, shared axes.** A flow may not be credited with competence along a coordinate
built from its own defining statistic. Which flow shares a statistic with which coordinate is
declared in the instantiation, and no competence claim is made along a shared axis, in either
direction.

**Corollary four, serving.** A channelling policy must be executable on a query whose truth is
unknown. Every coordinate the policy routes by must be computable at serving time, at a stated
cost, from the query, the frozen bank and the frame alone, and by a code path that does not read
the evaluation's own artefacts even where the two would agree numerically. A coordinate computable
only after the fact is a reporting coordinate: it may appear in tables and may not appear in the
policy. The instantiation marks each coordinate with its serving cost.

**Corollary five, calibration.** A coordinate's band edges may not be calibrated on the decision
cohort's own results, because the family must be declared before any result is read and a family
redeclared after the levels come back empty is not a family. Edges are set from the frame, from
mechanism boundaries, or from a population that is not the one under test.

**A coordinate whose level meaning depends on the configuration is not a coordinate.** Where a
level is defined by a property of the machinery, such as a boundary at a model's context limit,
its meaning is stable only across configurations that share that property. Such a coordinate is
usable inside a node whose levels all share it and is not usable across a node that varies it. The
instantiation says, per node, which coordinates are admissible.

### 3.3 What a region is, the depth rule, and the routing family

A **region** is either a panel, or a panel intersected with exactly one level of exactly one
coordinate.

**Crossing depth is one.** Two coordinates are never intersected with a panel at the same time in
any table that carries a difference claim. The full cross stays recoverable from the per-protein
records, so what is foreclosed is the claim, not the data, and the instantiation states the
retention requirement that keeps that true.

**The routing family must be a partition, not a cover.** The reporting family may contain a panel
and its sub-regions and sub-regions under several coordinates at once, because a report is a set of
tables. A policy is a function, and a unit that belongs to three regions with three different
admission sets has no defined behaviour. The routing family is therefore declared as **one
nominated coordinate**, giving a partition of each panel, plus the panel itself as that partition's
parent. Every other coordinate is reporting only. Where a policy is nonetheless defined over
several coordinates, the precedence order is part of the sealed plan and is counted in section
5.2's free-bit accounting.

**Collapse is hierarchical and deterministic**, so that no human choice enters after the numbers
are visible: a sub-region uses its own decision only where its population clears the admission
floor, and otherwise inherits its parent's, with the whole-population policy at the root. That
makes the levels one nested family rather than competing alternatives, and it makes the routed
system degenerate gracefully to the constant policy wherever the map could not see.

**The region family is declared in full before any result is read.** It is the multiplicity family,
and its size enters every floor in section 7.

### 3.4 The arithmetic of crossing

Crossing costs power, and worse than it looks, in four ways.

**The population divides.** A coordinate splits a panel into parts summing to the panel. Nothing is
gained; the units are the same units.

**The detectable effect scales as the inverse square root of the population**, so the smallest
effect a part can resolve, relative to the whole panel, grows as the square root of the panel
divided by the part.

**Skew governs, not the mean.** Real coordinate distributions are skewed, so one or two levels hold
most of the mass. The mean population per level is the wrong summary of the only distribution that
matters, and reporting it is how a crossed grid gets approved. The correct summary is the minimum
level population and the correct question is what the worst level can resolve.

**Multiplicity compounds.** The number of contrasts grows with the region family while the
populations shrink, and the two effects push the same way.

**And the counted population overstates the effective one.** Proteins within a region are
homologues rather than independent draws, especially in a region defined by homology, so the
effective population is a fraction of the counted one. The instantiation either estimates that
design effect, with a named producer, or declares a conservative inflation factor as a frame
parameter and applies it to every floor. Silence is not available: a critique of the map that rests
on the design effect and a defence of the claim that ignores it are the same argument used twice in
opposite directions.

Two rules follow.

**The floor is applied at report time and printed beside the row, never used upstream to merge
levels.** A floor depends on a variance that cannot be known before two systems are scored, so a
level structure frozen from population counts before anything runs is circular. Levels are frozen
raw at full granularity; the floor is a report-time parameter stamped on the output; a level below
it is **withheld with its population shown**, never dropped and never merged.

**Below the floor a region reports a point estimate, an interval and its population, and enters no
difference claim and no multiplicity family.** Below a second, lower bound where interval
estimation is itself unstable, it reports counts only.

The tension between "a coordinate is reported at all its levels or not at all" and "a level below
the floor is withheld" is resolved in favour of the second: withholding a level is a report-time
act with the population printed, and it does not remove the coordinate. What the first rule
correctly forbids is choosing which levels to report after seeing which of them separated.

---

## 4. Affinity

### 4.1 The definition

For a flow, its **affinity** is the set of regions in which it contributes above that region's
floor, measured on the decision cohort, against a declared reference pool, under a declared
multiplicity correction over the declared region family.

Four qualifiers, each load-bearing.

**On the decision cohort.** Never on the holdout, in any form, including by inspection.

**Against a declared reference pool.** A flow's contribution depends on which other flows are
present, so a contribution is conditional and the condition is named. The reference pool is
declared once, and the choice of pool is itself a degree of freedom counted in section 5.2.

**Above the floor of that region.** The floor for the flow-admission contrast class, not for any
other class.

**Under a declared correction** over the declared region family. Uncorrected, spurious affinity
concentrates in the small regions, which are the ones that motivate the design.

### 4.2 The instrument, which is not a single number

Membership is decided by quantities computed together, because no one of them separates the cases
that matter.

**Unique reach**, per flow per region: the share of that region's truth that this flow proposes and
no other flow proposes. Three properties are required of it and all three have been got wrong
before.

- **It is expressed in the currency of the metric.** If the campaign's metric weights terms by
  information content, an unweighted count of uniquely reached terms rewards a flow that proposes
  many shallow, high-frequency terms and reads as reachable truth the combiner is right to ignore.
  The denominator, the region's truth mass in the same currency, is printed beside it.
- **It is compared at a matched candidate budget.** Every candidate list is truncated, and the
  truncation is a knob. A flow given a larger budget has larger reach for that reason alone. The
  instantiation declares either an equal per-query budget across flows or a budget-indexed curve
  with the comparison taken at a declared point.
- **It is computed at the point where the pool is finally assembled, and on the executed
  configuration.** Where a mechanism can assemble candidates late, after the candidate table is
  written, a quantity computed on that table alone does not see it. And where a flow's declared
  status and its executed status can differ, because a producer can skip with a warning, the map
  reads the executed status. A source that never ran must never be published as a source that was
  measured and found worthless.

It requires that a candidate carry **which flows proposed it, as a set and not as a single value**,
because a candidate proposed by two flows is exactly the case that decides redundancy, and it must
be recorded as a proposal and not as an endorsement: a flag meaning "this flow also scored this
candidate" is a different quantity and counting it as reach credits a flow with proposals it did
not make.

**Total reach**, the same share without the uniqueness condition, so redundancy is readable
directly. **Reach precision**, a companion in the same currency, because a flow that proposes the
entire label space maximises reach trivially.

**Exploited fraction**, per flow per region: of the truth only this flow reaches, the share the
combiner places above the region's operating point. It is undefined, and reported as undefined
rather than as zero, when unique reach is zero. **The operating point it uses is declared, and the
declaration costs something either way**: a shared operating point makes a flow whose scores sit on
a different scale read as unexploited everywhere, which manufactures the very cell the design is
looking for; a per-region operating point is a fitted parameter per region and enters the free-bit
count. The instantiation names its choice and the cost it accepted.

**Marginal contribution**, the change in the region's metric when the flow is removed from the
reference pool. On its own it is the wrong instrument: a flow the combiner ignores reads as zero
whether it is useless or merely redundant, and the two have opposite consequences for channelling.

Read together they separate the states an empty measurement can be in.

| unique reach | total reach | exploited fraction | marginal | reading |
|---|---|---|---|---|
| none | none | undefined | zero | **no signal.** Nothing to channel |
| none | high | undefined | zero | **redundancy.** The source is covered by others. Removing it costs nothing; removing it and its partner may cost everything |
| high | high | low | zero | **unexploited.** The truth is reachable and the combiner throws it away. This is the case channelling exists for, and it is the case a leave-one-out reports as nothing |
| high | high | high | positive | **working** |

**Against the empty pool the instrument is a different object and does not carry the word
affinity.** With one flow in the pool, unique reach equals total reach by construction, marginal
contribution is the system's whole score against nothing, and redundancy is undefined. The
empty-pool measurement is a per-flow description reported as total reach, reach precision and
absolute score, in its own table with its own shape. Publishing it in the affinity map's columns
produces a map in which every flow is uniquely competent everywhere.

### 4.3 Affinity admits no global ordering

Affinity is a set. Two sets that are not nested are not comparable, and most pairs of flows will
not be nested, because the design's premise is that different sources are competent in different
places.

Every scalar summary reintroduces a hidden weighting. Counting regions weights a large panel and a
thin coordinate level equally. Averaging gains across regions weights by nothing and pools what the
partition forbids pooling. Taking the best region rewards the noisiest estimate. There is no
defensible scalar, so the model refuses one, and the refusal is what makes "the winning flow"
ungrammatical.

### 4.4 The statuses, which are five

**Amendment to the parent, which says three.** Per flow, per region:

**Mute.** Structurally undefined there, derived from definitions before any run. Not part of the
flow's affinity domain, so neither admitted nor refused, and reported in its own ink.

**Admitted.** Contribution clears the region's floor under the declared correction.

**Redundant.** Unique reach near zero with total reach high, and power present. The source is
carried by others in that region. This is a distinct reading with an opposite consequence from
"not admitted", and giving it the same ink is what makes section 6.1's joint-removal hazard
invisible.

**Not admitted.** The comparison had power, total reach is not high, and the contribution did not
clear the floor.

**Indeterminate for want of power.** The region could not have resolved the contribution whatever
it was, computed before the run from the class's variance and the region's population. The region's
minimum detectable effect is printed beside it.

A map published in two inks renders "we could not tell" and "we could tell it does not help"
identically, over a lattice whose power varies by an order of magnitude. A map published in three
renders redundancy as uselessness, which is the reading that gets a working source cut.

### 4.5 What a partial, empty or unpowered affinity set means

**Partial**, admitted somewhere and not admitted somewhere else, with power in both: the design's
premise realised, and the only state from which a channelling policy is anything other than a
global decision.

**Empty with power everywhere**: the flow adds nothing anywhere against that reference pool.
Against the full pool this may still mean redundancy, which is why the pool is declared and total
reach is printed.

**Empty because indeterminate everywhere**: the flow has **no measured affinity**, and no
channelling decision may be taken about it. It is admitted everywhere or cut everywhere by a
declared, uniform default, which is a convention recorded in the instantiation and never a finding.
The flow is carried forward as a request for data with the population that would be needed printed
beside it.

**Degenerate by construction**: with one flow in the pool, affinity is not measurable at all.
**Affinity requires at least two flows with built generator halves and a combiner that can read
both.** A campaign stage that varies configurations of one flow is not measuring affinity, whatever
the tables look like.

**And the whole map indeterminate is the expected first state, not a corner case.** The
indeterminacy test needs the flow-admission variance, and that variance needs a pair of runs
differing in flow admission and in nothing else. Until such a pair exists every region is
indeterminate, every flow takes the declared default, and the policy equals a comparator. The
consequence is an ordering constraint rather than a caveat, and it is stated in section 7.2.

---

## 5. Channelling

### 5.1 The definition

A **channelling policy** is a map from each region of the declared routing family to the subset of
flows admitted in that region, together with the combiner that reads them. It is derived from
affinity under a declared admission rule, and it is the output of exactly one node, the routing
node, which is the only node whose output is a policy rather than a value.

The policy is **total**: every unit of every panel must be served, so a policy with a hole is not a
system. Where a coordinate has no value for a query, the missing level is a level and the
hierarchical collapse of section 3.3 gives it a parent.

The policy is a **content-addressed artefact** and every result produced under it names it. A
routed result that cannot name the policy that produced it is unusable in the same way an unframed
result is.

Where a policy is expressed as a bitmask over a flow registry, the bit assignment is append-only
and pinned by a test that pins the **ordered** assignment, not a digest of an unordered set. A
digest that sorts its input cannot detect a reassignment, and a bitmask written under one release
and read under another that reassigned bits is a silently wrong policy whose failure looks exactly
like a result.

### 5.2 Degrees of freedom

Every one is declared before affinity is read, and every one spends power.

- **The flow set.** Which flows are candidates for admission anywhere.
- **The reference pool** against which affinity was measured. A binary choice that changes which
  flows the rule admits.
- **The routing family.** Which single coordinate, if any, is nominated. Finer families buy
  expressiveness and lose power at the rate section 3.4 derives.
- **The admission rule**, including any free parameter. A rule with a free parameter is fitted.
- **The default in indeterminate regions.** Declared, uniform, never region by region, because a
  per-region default is an unmeasured admission decision in a convention's clothing.
- **Whether the combiner is refit per region or held fixed.** Refitting multiplies the free
  parameters by the number of regions and is the fastest way to turn the claim into a fitting
  exercise. The default is a fixed combiner; refitting is declared and counted.
- **Whether admission carries weights or only membership.** Membership only by default.
- **Whether the operating point is per panel or per region** (section 4.2).
- **Any precedence order** where the routing family is not a partition (section 3.3).

The honest accounting is stated in the instantiation as a count: at most the flow set size times
the routing family size, plus the operating points, plus whatever the combiner adds. That count
will exceed what the small regions can support. **This is why the map is not the claim.**

### 5.3 Fitting discipline on the decision cohort

Everything is fitted on the decision cohort: the combiner, the thresholds, the admissions. If
affinity is then measured with that combiner on the same rows, exploited fraction is in-sample by
construction and every admission verdict is inflated, most in the small regions.

**The decision cohort is therefore split, or cross-fitted, and which is declared.** The
instantiation states a partition of the decision cohort into a fitting part and an evaluation part,
or a cross-fitting scheme in which every quantity read for a region is computed on rows the fit did
not see, together with the populations that split produces. Where the platform offers a
deterministic partition of the cohort, the instantiation names it and states its limitation, in
particular whether it clusters by sequence: a partition that puts near-identical sequences on both
sides scores a fit on its own training neighbours.

A partition costs power in exactly the regions that are already thin. That cost is stated rather
than avoided, and a campaign that cannot afford it says so and marks every admission verdict
in-sample.

### 5.4 The comparators

Two policies sit at the boundary of the policy space.

**Admit everything everywhere**, the flat pool with one combiner. What a system does with no
regional knowledge.

**Admit exactly one flow everywhere**, chosen on the decision cohort. Constructing it requires an
ordering across panels, which is the declared-aggregate exception of section 3.1: the aggregate's
form is sealed in advance, it defines the comparator and it reports nothing.

Both are members of the policy space, which is what makes the contrast well posed: a policy that
cannot beat the two simplest members of its own space has bought nothing with its degrees of
freedom. Where the admission rule is of a form that cannot express "admit everything", the
instantiation says so and defends the comparators on their own terms instead of on membership.

**The two comparators carry different selection intensities and the report says so.** The single
flow comparator takes one maximum. The policy takes one per region. Both are optimistic on the
cohort they were chosen on and the policy is more so, so the expected holdout contrast is smaller
than the decision-cohort contrast by an amount that grows with the size of the search. Stating that
direction in the seal is what stops a shrunken but positive result being read as a failure of
transfer, and a shrunken negative one being read as noise.

**A degenerate case worth naming.** If the routing family collapses to the panels, the policy and
the panel-granularity comparator are the same object and the contrast is identically zero. That is
a legitimate outcome of the arithmetic in section 3.4 and it must be pre-registered as a possible
result, not discovered and then narrated.

### 5.5 What makes it a claim rather than a fitting exercise

The policy is fitted. That is not deniable. What makes the campaign a claim is that **the claim is
not the policy**.

> **The claim is a single contrast: does the channelled system beat the not-channelled system, in
> each panel, on the holdout, under a plan sealed before affinity was measured?**

Against both comparators, per panel, never pooled.

Six properties are declared before any affinity number exists:

- the routing family, in full;
- the flow set, the reference pool and the admission rule including its parameters;
- the comparators, including the aggregate that defines the single-flow one;
- the metric, its weighting, its estimator and the per-panel reporting;
- the multiplicity family, its size and the correction;
- **the reading of every possible outcome**, which is section 5.6.

The seal makes those statements true rather than intended: the analysis is a registered operation
whose payload is content-addressed and committed before the holdout is read. A promise not to look
leaves the counterfactual available; a signed plan removes it. Where no such operation exists, the
seal is a blocked precondition with a named producer, not a discipline.

**The map is published beside the claim as a description, in five inks, with each region's minimum
detectable effect printed.** It is the mechanism, it is the worst-estimated object in the design,
and a design whose headline is its least identifiable object is indefensible however carefully it
is measured.

### 5.6 The reading of the outcome, which is where an earlier draft made the claim unfalsifiable

The parent document's rule that "the experimental leader stands" on disagreement is correct and it
governs **the ordering among propagated flows**: the holdout may not re-rank them, because
re-ranking is selecting. It does **not** govern the sign of the claim, and importing it there
removes the claim's only failure mode.

**Three outcomes, declared in the seal, per panel:**

- the difference is positive and clears the floor: the claim is upheld in that panel;
- the difference is negative and clears the floor: **the claim is refuted in that panel, and the
  refutation is the result**;
- the difference is inside the floor: the claim is unresolved in that panel, and unresolved is not
  upheld.

The seal also declares the compound rule over panels, how many panels of which set must uphold it,
and **the error rate that rule controls**, computed in advance under the dependence the panels
actually have. A compound rule stated without its error rate is a threshold nobody can fail.

**And the seal declares the null.** "Does channelling beat not channelling" needs a zero to be
measured against, and the natural one is a regional permutation: shuffle the region labels, refit
the policy under the same admission rule, and report the observed gain against that distribution.
Without it, a positive difference of any size is a number without a baseline.

### 5.7 Configuration channelling is not flow channelling

The same machinery admits a second, cheaper use, and the two must never be reported under one
heading.

**Flow channelling** admits different sources to different regions. It is the thesis claim. Its
contrast class is flow admission, whose variance is unmeasured.

**Configuration channelling** selects a different configuration of one flow per region. It is a
legitimate and much cheaper result, its contrast class is configuration-of-one-flow, and it
exercises every piece of the apparatus the thesis claim needs: the routing family, the report-time
floor, the inks, the multiplicity family, the fitting split, the seal and the outcome reading.

**Its correct name is a rehearsal.** It proves the machinery on a cheap node, it produces a
publishable regional result about one mechanism's sensitivity, and it produces **no affinity map at
all**, because a single-flow pool makes affinity degenerate. Reporting a per-region table of
configuration winners as an affinity map is the substitution this model exists to make impossible.

**A rehearsal runs at the routing node.** Section 6.2 forbids any node except routing from reading
regions, and that includes the node whose levels the rehearsal is routing. The scoring node still
closes per panel and carries its ordinary edge; the rehearsal takes that node's levels as its flow
set and asks the routing node's question of them. Of the two verbs a level can take, propagated
applies and **cut does not**: cutting is admission, admission is about sources, and a configuration
of one flow is not a source.

---

## 6. Cutting and propagating

### 6.1 Cuts are not independent

Removing a flow from a region changes the pool there, and every other flow's marginal contribution
is defined against that pool. A set of cuts cannot be assembled from marginal tests applied one at
a time and then assumed to compose.

**Affinity is measured against one declared reference pool, and all cuts derived from it are
applied simultaneously.** The result is one policy object, evaluated once, as the single contrast.
Sequential cutting, where each cut is measured against the pool left by the previous one, is a
search over orderings and carries a selection floor priced against the whole search.

**But simultaneous cutting has its own hazard and it needs one extra measurement.** Two flows that
agree in a region can each show zero marginal contribution while the pair carries that region
alone. Cutting both at once removes the region's entire coverage in one step, and the resulting
policy is worse than the flat pool in exactly the region the design cares about. **Before any
simultaneous cut of two or more flows whose total reach overlaps in a region, the joint removal is
measured once for that set.** That is a small, bounded number of extra contrasts and it is the
difference between a policy and an amputation. The redundant ink of section 4.4 is what makes those
sets visible.

**A cut is regional and reversible only by re-running.** Nothing downstream of the routing node
exists except the terminal projection, so the transitive closure of a cut is small. This is the one
place in the graph where a late decision is cheap, and it is why routing is asked once, at the end.

### 6.2 Regions do not enter graph propagation; panels do

**The graph's edge cardinality is a vector over panels, never over regions.** Coordinate-crossed
regions are reporting objects and inputs to the routing node. They do not gate any other node, they
do not widen any other node's fan, and no node other than routing reads them.

The reason is arithmetic. The fan a node evaluates is the union over panels of what each panel's
evidence carries. If sub-panel regions could widen it, every thinly populated coordinate level
would contribute a ranking drawn from a comparison that could not resolve, and a union of lotteries
approaches the complete set of levels. The fan would be widest exactly where the evidence is
weakest.

### 6.3 The unpowered rule, in both forms

**In the graph:** an unpowered panel never widens the fan. It carries the whole incoming set at
strength unpowered, and the fan the next node evaluates is set by the panels where the claim lives.

**In the policy:** an unpowered region never admits a flow and never cuts one. It takes the
declared default and is published as indeterminate with its minimum detectable effect.

Both are the same statement: a null from a comparison that could not have resolved anything is not
a negative result, and reading it as evidence of sameness is how a preference acquires the standing
of a finding.

**Its converse also holds and is easy to lose.** A panel with power and a null effect has resolved
something: it should collapse to the null level rather than fan. A rule that fans on "did not
resolve" without distinguishing the two makes the fan widest in the panels with the most evidence
whenever the effect there is genuinely small.

### 6.4 A flow cut everywhere, and a flow admitted nowhere

A flow **cut in every region with power** has a measured, empty affinity set. That is a result and
it is reported as one, with its reference pool named so the redundancy reading stays available.

A flow **admitted nowhere because every region was indeterminate** has no measured affinity. It is
not a result. It is a request for data, written as one, with the population that would be needed.

A flow **mute in some regions and admitted in others** is the ordinary case and is exactly what the
policy is for. Its muteness costs nothing to establish and is derived, not measured.

---

## 7. Floors, per contrast class

### 7.1 Why one floor cannot serve

A floor is derived from the variance of the paired difference between the two systems being
compared, and that variance is a property of **what differs between them**. The more machinery
differs, the more the two systems' per-protein outcomes decouple and the larger the variance. The
required population scales with the square of that variance, so borrowing a floor across contrast
classes is not conservative in either direction; it prices a different experiment.

**A floor lives on the edge being tested, is published with the name of its class beside it, and is
never borrowed by analogy.** Every unpowered declaration that borrows a floor is a declaration
about a different experiment, and is marked provisional until its own class is measured.

**Resolution against selection.** A comparison declared before it ran takes a resolution floor. A
value chosen because it came out best among several takes a selection floor, priced against the
size of the search that produced it. The same number takes opposite verdicts under the two.

**The maximum lives upstream.** The decision cohort is where the maximum over the search is taken
and where the selection floor applies. The holdout makes only declared comparisons and takes
resolution floors under the sealed family. **This resolves the parent's two statements about the
terminal floor in favour of the second**, and the resolution is stated rather than assumed: the
parent's earlier sentence, that the terminal is priced against the whole graph's search budget, is
correct about the claim that a flow is the best of what was searched, which belongs to the decision
cohort. The holdout's own comparisons were declared before they ran.

The holdout cannot resolve a tie, because resolving one is selecting, and it is smaller than the
cohort on which the tie was declared.

### 7.2 The contrast classes, and the order they must be measured in

Each class is defined by **what varies** between the two systems compared. Each needs its own
variance measured on pairs that differ only in that class, and a class whose defining difference
has never been produced has no floor at all.

**Class 0a, determinism.** The same configuration, the same index, the same seed, re-run end to
end. Where the pipeline is deterministic this is exactly zero and is a bound nothing can fail; it
is asserted once and not paid for again.

**Class 0b, instrument noise under a rebuilt instrument.** The same configuration with the index
rebuilt, an approximate search structure re-created, or a fit re-seeded. This is the class where
instrument noise actually lives, and it is not zero. It must be measured wherever the campaign uses
an approximate index or a learned component, and its replicate count is declared.

**Class 0c, implementation identity.** Two implementations of the same computation, for example two
search backends. Not a choice and not a claim: an identity to be asserted once, with a stated
tolerance.

**Class 1, one flow, one downstream field, retrieval shared.** A scoring weight, a threshold, a
preset, anything that reorders or re-thresholds a candidate list already written. The two systems
see identical donors. Expected to be the smallest non-zero variance.

**Class 2, one flow, retrieval changed.** The substrate, the depth, the donor bank, the
neighbourhood size, anything changing which donors are seen. The candidate lists differ, so
per-protein outcomes decouple substantially. Larger than class 1, and measured rather than assumed.

**Class 3, flow admission.** A whole source present or absent from the pool. **This is the class
the thesis claim runs on.**

**Class 4, the policy contrast.** The admission map across all regions at once, against a
degenerate comparator. The difference is a sum over heterogeneous regions, so its variance is not
the variance of any single-region contrast and cannot be assembled from them. It is measured on the
policy object, not on its parts.

**Class 5, the frame.** A convention varied with everything else held. Not a claim, and no verdict
is drawn from it, but it must be measured once because it bounds the meaning of every other floor.
If changing a convention moves a result by as much as a node moves it, a comparison across two
frames is not a comparison, and every floor is quoted at a fixed frame or not at all.

**Class 6, cohort transfer.** Nothing about the system varies, only the population it is scored on.
Its floors are resolution floors on smaller populations, computed at the contact because they
depend on populations not known until then, under the rule declared in the seal.

**The order these must be measured in is not the order they are listed in, and getting it wrong is
what makes the first map one ink.** Class 3's variance requires a pair of runs differing in flow
admission and in nothing else. The binding constraint on producing such a pair is a **second flow
whose generator half exists and whose signal the combiner can read** (section 2.3). Recording which
flow proposed a candidate is what makes unique reach computable once two such flows exist; it does
not by itself create the pair, and in a single-generator system it writes one constant in every
row. Both are needed and neither substitutes for the other. **Class 3 is measured before the
routing family is declared**, because the family's indeterminacy colouring is computed from it.

### 7.3 What every floor carries, and what estimator it is computed for

A floor is never a bare number. It is published with its class, the population it was computed on,
the effect it was declared to resolve, the multiplicity correction and its family size, and whether
it is a resolution or a selection floor. A floor without its class is the same category of object as
a number without its baseline.

**And a floor is computed for the estimator the rank actually uses.** The standard closed form,
a constant times a paired standard deviation divided by the square root of the population, is the
standard error of a **mean of per-unit differences**. A micro-averaged, weight-carrying metric is a
**ratio of sums**, dominated by the units carrying the most weight, with no per-unit decomposition
and a different sampling variance. Feeding a per-unit standard deviation into that formula and
comparing the result against a ratio-of-sums difference produces a floor and an interval that can
disagree at exactly the margins that matter.

**The rule.** Where the rank is a ratio of sums, the floor is the bootstrap standard error of the
paired difference of that ratio, resampling proteins, with each system's own operating point
re-selected inside each resample where the metric maximises over a threshold. Where the operating
point cannot be re-selected because the per-unit artefact was written at one threshold only, that
is a blocked precondition on the artefact's producer and not a licence to use the closed form.

**Multiplicity is declared with its family size and labelled for what it is.** A single fixed
inflation of the detectable effect corresponds to a fixed per-comparison level and is
Bonferroni-shaped; a step-up procedure has a rank-dependent threshold and no single equivalent
constant. The instantiation states the family, its size, the procedure and the resulting constant,
and does not import a constant computed for one family into another.

**A correction to a rejection rule is not a correction to a point estimate.** A winner selected as a
maximum over several levels is biased upward, and no multiplicity procedure removes that bias. Where
a selected point estimate is reported, the report says it is a maximum and the direction of the
bias.

---

## 8. Obligations this model creates, as a producer checklist

Abstract, because the names belong to the instantiation. Each line is an artefact or a code path
the model requires, so that an instantiation can be checked against it rather than searched.

- A ground-truth builder implementing the declared "appears" primitive, with its propagation graph
  selected explicitly at both ends of the window.
- A frame stamp on every result row, covering every convention the frame declares, not only those
  the schema happens to have columns for.
- A per-unit evaluation artefact carrying the metric's components across the whole threshold grid,
  so intervals can re-select the operating point.
- A paired interval producer, resampling proteins, emitting a point estimate, an interval, a
  population and a minimum detectable effect per region.
- A per-region population source that reads the ground-truth artefact and not the run.
- A candidate provenance record: which flows proposed, as a set, distinct from which flows scored.
- A combiner whose signal vocabulary covers every flow in the inventory, or a per-flow record that
  it does not.
- A flow registry with an append-only, order-pinned identifier assignment.
- An assembly producer that materialises a pool under a policy and evaluates it as one system.
- An affinity producer and a policy deriver, both read-only and content-addressed.
- A sealed terminal operation that refuses to run without a matching sealed plan and refuses to run
  twice against the same holdout.
- A retrieval-frame record on every prediction artefact, covering every field that changes which
  candidates exist.

Anything on that list without a producer is a blocked edge with a named precondition, and the
instantiation says which.

---

## 9. What this model will not do

**It will not make a small region large.** Crossing divides a population that was already the
binding constraint. The model makes the division visible and prices it before the run. A region
family that cannot be resolved is declared unpowered in advance rather than reported as a null.

**It will not decide which flows exist.** The source inventory is a declaration and the mechanisms
are code. A source with no producer is a blocked edge, and the model's contribution is to insist
the gap is recorded as a missing producer rather than as a measured zero.

**It will not turn the map into the claim.** The map is hundreds of contrasts over regions whose
power varies by an order of magnitude, least identifiable exactly where the design is most
interesting. The answer is structural, not statistical: publish the map as a description in five
inks, and stake the campaign on one pre-registered contrast that has power.

**It will not remove the conditionality of a contribution.** Unique reach is conditional on the
flow set and the budget, marginal contribution on the pool, exploited fraction on the combiner and
its operating point. Each condition is declared. None becomes unconditional, and a reader wanting
an unconditional statement of a source's worth will not find one, because there is not one to have.

**It will not protect a policy fitted after the numbers were seen.** The seal, the declared routing
family, the declared admission rule and the declared outcome reading are the whole of the
protection, and each is an obligation discharged before the fact.

**It will not price the effective population for free.** Homology clustering inside a region is
real and unestimated by default. Either it is estimated or a declared inflation is applied to every
floor, and the same argument is not used to demote the map and spared for the claim.

---

## 10. What the critiques got wrong

Recorded in one line each, with the reason, so they are not re-litigated.

**"Length satisfies the coordinate invariant."** Half right. The value is flow-independent; the
level's meaning is not, where the boundaries are model context limits. Handled in section 3.2 as a
coordinate admissible inside a node whose levels share the property and not across one that varies
it, rather than by discarding it.

**"The identity test collapses flow admission into a configuration contrast, because a payload
flag reaches from one to the other."** Correct as a criticism of a field-only test, wrong as a
reason to abandon the test. Section 2.1 grounds identity on the source and demotes the field test
to the mechanism half, which fixes the failure without losing the operational rule.

**"Marginal contribution is undefined against the empty pool, so the empty-pool reading is
incoherent."** Correct that the instrument degenerates, wrong that the reading is useless. Section
4.2 gives the empty-pool measurement its own name and its own table shape instead of dropping it.

**"The protein-level bootstrap rule is a no-op."** Correct inside a panel and wrong in general. It
is retained in section 1.2 with the scope stated, because it binds wherever anything crosses
panels, including a declared comparator aggregate.

**"Class 0 is redundant because the pipeline is deterministic, so it should be dropped."** Correct
about the deterministic case only. Section 7.2 splits it: determinism is asserted once, and the
class that matters is the rebuilt instrument, which is not zero and has never been measured.

**"The claim's comparator cannot be built without an aggregate, so the no-aggregate rule is
violated."** Correct that an aggregate is needed. Section 3.1 resolves it by permitting a declared
aggregate to define a comparator and forbidding it to carry a verdict, which is narrower than
either abandoning the comparator or abandoning the rule.

**"Section 6.2 forbids the rehearsal that section 5.7 authorises."** Correct as read, and the
resolution is that the rehearsal runs at the routing node with the scoring node's levels as its
flow set, stated in section 5.7. The scoring node itself still closes per panel.
