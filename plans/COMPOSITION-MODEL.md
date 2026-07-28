# THE COMPOSITION MODEL: what the method is made of

Author: Francisco Miguel Perez Canales. Written 2026-07-28.

Fifth companion to the planning set. `CAMPAIGN.md` says what will be run,
`SIGNAL-REGISTRY.md` says what each thing was worth, `E2E-CANONICAL-RUN.md` sets
the principles and `GENESIS-STATE.md` says what the machine needs. **This one
says what the parts ARE**, which none of the others do, and which turns out to be
the reason several of them were confusing.

---

## 0. The problem this fixes

The project has been calling everything a signal. A representation is a signal, a
candidate generator is a signal, a feature column is a signal, a score graft is a
signal, a threshold is a signal. They are not the same kind of thing, and the
damage is not vocabulary, it is measurement.

**Six different instruments have been reporting into one column.** A retrieval
representation is measured by how good the retrieved set is. A candidate proposer
is measured by what it adds to the pool at matched volume. A feature is measured
by removing it from the model. A score graft is measured by the blend delta. A
policy is measured at everything-else-fixed. **Those numbers are not
commensurable**, so a table that lists them in one column with one heading is
inviting exactly the comparison that cannot be made.

It also explains the confusion about where the classifier belongs. The classifier
is not in one place. **It enters twice, at two different joins, in two different
roles, and it is measured by two different instruments.** As a proposer it puts
candidates in the pool. As evidence it emits a column that travels to the
combiner. One name, two roles. The same is true of the domain-signature channel,
which is a proposer, a feature family and a post-score graft, all under one word.

---

## 1. Five layers

The method composes in a fixed order. Each layer accepts elements of exactly one
kind, joins at exactly one point, and is measured in exactly one unit.

| Layer | An element is | Joins at | Measured by |
|---|---|---|---|
| **1. Space** | a geometry over proteins | before retrieval | quality of the retrieved set (recall at k, accretion coverage) |
| **2. Proposer** | a producer of candidate pairs | the candidate pool | what it adds at matched volume (accretion precision, reachability) |
| **3. Evidence** | an attribute of a candidate pair | the feature row | removal from the model, per cell, with an interval |
| **4. Scorer** | a producer of a number per pair | the score | delta against the arm it replaces or blends into |
| **5. Policy** | a decision about what to submit | after scoring | delta with everything else fixed |

The order is real and not a convention: a proposer cannot propose what a space
cannot reach, evidence cannot describe a pair that no proposer proposed, and a
policy cannot rescue a score that no scorer produced. **Each layer's ceiling is
set by the layer above it**, which is why the ladder gates at retrieval first.

### Why the combiner is a scorer and not its own layer

The per-category model that consumes the feature row and emits a number is an
element of layer 4. So is the domain graft, which emits a number without
consuming the feature row at all. **A scorer is defined by what it produces, not
by what it consumes**, and that definition is what lets the two be compared and
blended at the same join.

---

## 2. The rule: an element declares five things

This is the pattern. Every element of the method, existing or proposed, declares:

1. **Layer**: which of the five. If it belongs to two, it is registered **twice**,
   as two elements, with two measurements. There is no such thing as one number
   for a thing that acts in two places.
2. **Join**: the exact point it enters. Two elements in the same layer are
   substitutable at that join; two in different layers are not alternatives at
   all, and comparing them is the category error above.
3. **Unit**: the instrument that measures it, from the table in section 1. A
   number without its unit is not a result.
4. **Provenance**: what produced the element and what produced its inputs, so a
   number can be traced to the code and the data behind it.
5. **Storage contract**: how its output is persisted and keyed, which is what
   makes distribution possible. See section 4.

An element missing any of the five is not registered, and an unregistered element
may not appear in a results table.

---

## 3. Where each existing part actually goes

Registered under the rule above. Note the parts that appear twice.

**Layer 1, spaces.** The base representation. The learned sparse head over it.
The text-aligned representation. Any further language model in the grid. These
are alternatives at one join and are compared with each other, never with
anything below.

**Layer 2, proposers.** Neighbour transfer over the champion space. The
full-vocabulary classifier. The sparse functional generator. Co-occurrence
expansion. Domain-signature transfer. The unreviewed-neighbour arm, once
provenance exists. These union into one pool, and the union is routed by cell.

**Layer 3, evidence.** Attributes of a candidate pair, and they subdivide by what
they depend on, which is worth making explicit because it predicts which ones can
be missing and why:
- on the query alone: length, projected components
- on the candidate term alone: term frequency, accretion weight
- on the query and the term: the query's known terms against the candidate,
  lineage relations, cross-aspect co-occurrence
- on the donor: neighbour rank, distance, alignment, taxonomy, donor evidence
- on a proposer: the classifier's score, the sparse generator's score

**That last group is the second appearance of the layer-2 elements**, and it is
the answer to where the classifier goes. It goes in both, and its two numbers
answer two different questions: how much better is the pool with it, and how much
worse is the model without its column.

**Layer 4, scorers.** The per-category combiner. The domain graft. Any future
independent predictor blended at the score.

**Layer 5, policies.** Withholding weak candidates. Per-protein normalisation.
The threshold sweep itself. The exclusion of already-known terms, which is a
property of the scoring frame rather than of the method, and is registered as a
policy of the frame so that it is never silently absent again.

---

## 4. Storage, and therefore distribution

Each layer has one storage contract, and they are all keyed so that work shards
by protein. This is what makes the run distributable, and it is worth stating as
a design property rather than discovering it under load.

| Layer | Persisted as | Key | Shards by |
|---|---|---|---|
| Space | representation rows | (protein, space) | protein |
| Proposer | candidate rows with a proposer tag | (protein, term, proposer) | protein |
| Evidence | columns on the candidate row | the declared contract | protein |
| Scorer | one score column per scorer | (protein, term, scorer) | protein |
| Policy | configuration | none | not data |

Three consequences follow, and all three are load-bearing.

**Every proposer tag must be written, not inferred.** A candidate that does not
record which proposer produced it cannot be attributed later, and a pool that
cannot be attributed cannot be ablated. This is the same defect as the missing
donor provenance, in a different place.

**A scorer is a column, not a replacement.** Storing each scorer's output beside
the others rather than overwriting is what makes blending, comparison and
post-hoc analysis possible without recomputing.

**The reference bank is the only global structure.** Everything else shards by
protein; the space's reference bank is shared by all shards, which is exactly why
its integrity is the campaign's most fragile point, and why it needs a
fingerprint rather than a convention.

---

## 5. Champions, per cell, per layer

This is what the author asked for, and the layering makes it precise. **A champion
is chosen per layer, per cell**, not once globally, because the nine cells are
different regimes and the evidence already shows the winner differs between them.

For each of the nine cells, the run selects:

1. the champion **space**, on retrieval quality;
2. the champion **proposer set** and its routing, on candidate-set quality at
   matched volume;
3. the champion **evidence set**, by removal with intervals;
4. the champion **scorer stack**, on the frame's own metric;
5. the champion **policy set**, at everything-else-fixed.

Selection happens on the adjustment windows with our own evaluator, and the
external board validates the frozen composition. **A champion at one layer is
frozen before the next layer is searched**, because searching two layers at once
is searching their product, and the product is where overfitting hides.

The author's two questions map exactly onto this: the best through scoring and
learned vectors is the champion at layers 1 and 4; the best through the
classifier and the rest is the champion at layers 2 and 3. They are different
selections with different instruments, and the composition model is what keeps
them from being averaged into one misleading number.

---

## 6. What this changes in the campaign

- **Results tables split by layer.** One table per layer, each with its own unit
  stated in the header. No table mixes layers, and no single ranked list of
  everything exists, because it would be a ranking across instruments.
- **The registry gains a layer column**, and the elements that act twice are
  split into two rows with two measurements.
- **The ladder is the layer order.** Rungs 1 and 2 select the space, rung 3
  selects proposers, rung 4 selects evidence and the scorer stack, rung 5 handles
  ensembling within a layer. That is not a coincidence, it is the same structure
  seen from the experimental side.
- **The short run exercises one element per layer**, which is the smallest thing
  that proves the composition works end to end.
- **Two known defects are reclassified.** Query length and projected components
  are layer-3 elements whose producer discards values that exist at the call
  site. They are not unmeasured evidence, they are a broken producer, and they
  move out of the unmeasured list entirely.
