# THE CAMPAIGN: the clean run, defined

Author: Francisco Miguel Perez Canales. Written 2026-07-27.

Fourth and operative companion to `E2E-CANONICAL-RUN.md` (axes and principles),
`SIGNAL-REGISTRY.md` (what each signal is worth) and `GENESIS-STATE.md` (what the
new machine needs). Those three say what is true and what is missing. **This one
says what we are going to run, in what order, and what each step has to answer.**

---

## 0. NAMING DISCIPLINE (applies to all published prose)

**No release numbers, no identifiers, no configuration hashes anywhere in the
thesis, the README or the Sphinx narrative.** Prose names things by what they
are. Concrete identifiers exist only in tables and appendix lists, where they
belong, and are never load-bearing for the argument.

| In prose, always | Never |
|---|---|
| the reference release | the specific annotation release number |
| the evaluation cut | the cut identifier |
| the validation window | the external board window label |
| the base protein language model | the model configuration identifier |
| the learned sparse encoder | the embedding configuration identifier |
| the sparse functional generator | the internal component code name |

A reader must be able to follow the entire argument without meeting a single
identifier. The mapping from name to identifier lives in one appendix table and
one machine-readable registry. This is not cosmetic: a thesis whose argument
depends on remembering a code is a thesis that cannot be read.

---

## 1. THE CORPUS: three tiers, one spine

**Tier 1, the spine: reviewed sequences.** Experimentally curated entries remain
the reference set and the only source of ground truth. This does not change.

**Tier 2, scale: unreviewed sequences ingested at volume.** The pipeline ingests
millions of unreviewed sequences and computes their representations. This is a
**systems claim**: the environment is distributed and scales. It carries **no
accuracy claim** and is measured on throughput, correctness and reproducibility.

**Tier 3, the culmination: directed case mining.** For reviewed proteins whose
neighbourhood is thin, retrieve their nearest unreviewed relatives and admit
them as donors, each flagged by provenance. The hypothesis is that unreviewed
density lifts retrieval exactly where reviewed density fails, and nowhere else.

Every unreviewed row carries its evidence provenance, and the flag is
load-bearing. Unreviewed annotation is overwhelmingly electronic, and much of it
is itself derived from sequence similarity, so transferring it through a
sequence-similarity neighbourhood would restate a prediction as evidence. The
safe first cut admits only evidence that is not sequence-derived, and the
sequence-derived arm is measured separately against the domain-signature channel
already in the system. **Ground truth stays experimental. Always.**

---

## 2. THE TEMPORAL DESIGN

**One rule fixes everything: everything before the board's mark is ours for
fitting and for choosing champions, and the board is what validates.** There is
no internal held-out test competing with the board for that role, because
inventing one would mean holding out twice and reporting whichever came out
better. The board's window is never touched by any decision we make, which is
what makes it a genuine external validation rather than a second selection set.

| Split | What it is | Scored with | What it may inform |
|---|---|---|---|
| **Train** | The earlier cuts, freely partitioned | our scorer | model fitting |
| **Adjustment** | The windows before the board's mark, chosen for representativeness | our scorer | every hyperparameter, every threshold, every design choice, and the choice of champion |
| **Validation** | The board's window, forward | the board | nothing. Reported, never optimised against |

**The naming is deliberate and it inverts the usual convention, so it is worth
stating plainly.** What machine learning normally calls validation is here
called adjustment, because that is all it does: it adjusts and it selects. What
is called validation is the board, because the board is the only thing that
validates. A reader who meets the words in their usual sense would assume an
internal held-out test exists. It does not, on purpose.

**Choosing the adjustment windows is a decision, not a default.** The obvious
choice, the single window ending at the board's mark, is the worst available:
that window is one of the two roughly thirty percent corpus contractions, so
selecting champions on it would tune against an anomaly and then validate on
normal accretion. The adjustment set therefore spans several windows chosen for
representativeness, and **the choice is made after additions and removals have
been decomposed**, never before, because until then nobody knows which windows
are representative. The concrete release pairs live in the split registry, in
code, with a guard.

**The validation result is reported as a series, one point per release, from the
board's mark forward through the newest published release.** It crosses the
corpus contraction rather than stopping short of it, because a curve that shows
the discontinuity is more defensible than a single number that hides it.

Three conditions make the series readable, and without them it is a curve nobody
can interpret. Additions and removals are decomposed per release and plotted
beneath the metric, so a dip is attributable to the corpus or to the method and
never ambiguous between them. **One point is designated the comparable number,
the board's own window**, because that is the only point other methods are
scored on; every other point is characterisation and is labelled as such, since
a series with no designated headline invites the reader to choose the flattering
point. And the whole series is a property of the frozen champion, never a search
space, or the external validation is destroyed by the very mechanism the
temporal design exists to prevent.

**Sample balancing.** Cuts are wildly uneven, in elapsed time and in content, so
balance is a requirement rather than a refinement. **Train and adjustment are
balanced across the four axes; the validation window never is**, because the
metric there is computed over a real population and reweighting it makes the
number incomparable to anyone else's. Per-stratum sample sizes are reported
beside every tuned parameter, and per-window rates are normalised by elapsed
time, since the gaps between releases range from about two weeks to four months.

The same prohibition covers aggregates, and it has been violated in the past:
**an unweighted mean across the nine cells is itself a reweighting**, because the
cells hold populations that differ by more than an order of magnitude, and it
moves in the flattering direction because the smallest cells are the easiest
aspects. No number is reported pooled across categories or aspects. A mean or a
win count over the nine cells is permitted only with the nine cells and their
population sizes shown beside it.

**Additions and removals are decomposed, never netted.** The annotation corpus
contracts as well as grows, and a ground truth built from a net difference would
mix new curation with the inverse of a bulk removal. Ground truth is built from
additions only; removals are reported separately as a property of the corpus.

---

## 3. THE FOUR AXES

Fixed, and applied to every measurement without exception.

1. **Category**: no knowledge, limited knowledge, prior knowledge.
2. **Aspect**: molecular function, cellular component, biological process.
3. **Sequence length**, in buckets.
4. **Homology to the reference set**, in bands, split by whether the supporting
   evidence is experimental.

Category and aspect give the nine reported cells. Length and homology are the
explanatory axes inside each cell: they are what turns a number into a finding,
and they are what locates the prior-knowledge wall.

Every table in the thesis is stratified on all four, with confidence intervals
on differences. There is no such thing as an aggregate result in this campaign.

---

## 4. THE OPERATION SEQUENCE

What we actually dispatch, in order. Each stage is a platform operation with its
output registered and its provenance stamped.

**Stage A, corpus.** Ingest reviewed sequences; fetch functional metadata and
taxonomy; load the ontology snapshot; load the annotation releases across the
full temporal span; backfill release publication dates. Then ingest unreviewed
sequences at scale, flagged by provenance.

**Stage B, representation.** Compute base representations for every protein
language model in the grid; apply the learned sparse encoder head to materialise
the retrieval codes. Distributed across both machines as an extra worker pool.

**Stage C, structures.** Materialise the reference caches; build the
co-occurrence structure; load the domain-signature mapping and scan the corpus.

**Stage D, frames.** Compute the accretion weighting per cut; generate the
evaluation sets for each split; construct the four-axis strata.

**Stage E, candidates and features.** Neighbour retrieval and transfer; feature
production across all declared families; export the frozen research datasets.

**Stage F, models.** Train the generators and the combiners; register each
trained model into the platform with its schema fingerprint.

**Stage G, measurement.** Score every frozen candidate under the pinned recipe;
report stratified, with intervals; submit the frozen champion to the external
board.

---

## 4bis. THE SHORT RUN (runs BEFORE the long run)

**A complete end-to-end pass at small scale, on the new machine, before the
campaign proper begins.** Pick any one delta. Take its start of window. Retrieve
neighbours into the unreviewed corpus. Then apply every subsequent step through
the platform, dispatched as operations rather than run as scripts.

**It is not a result. It is a proof that the chain exists.** Nothing measured
here enters the thesis and no decision is taken from its numbers. What it
delivers is the answer to a question no amount of code reading can settle: does
the output of each stage actually feed the next when a real payload flows
through it?

Why it must precede the long run:

- **Every hop is exercised once, cheaply.** The readiness audit found stages
  that are individually sound while several consumers resolve their input from a
  filesystem path supplied by an environment variable rather than from a
  registered entity. That defect is invisible until something flows.
- **It is the first honest test of unreviewed ingestion and of retrieval into
  it**, which is otherwise a claim rather than a demonstration.
- **It gives the interface and the visualisations something real to render.**
  Polishing a surface against fabricated data is how a surface ends up
  describing a pipeline that does not exist.
- **It surfaces the fragile parts while they are still cheap to fix**, rather
  than eight hours into a full pass.

Exit criteria: one dispatch chain completes end to end, every intermediate is
registered with its provenance, the interface renders each stage, and the
fragile points are written down. Then the long run starts.

**The precondition, and it is not optional:** the environment is clean, prior
results are archived rather than carried forward, and noise is out of sight. A
smoke run through a dirty environment proves nothing, because any failure can be
blamed on the residue.

## 5. THE EXPERIMENTAL LADDER

Five rungs. Each has one question, one gate, and nothing advances carrying
unmeasured baggage. **The gate is retrieval quality until the last rung**,
because the board metric is a poor instrument for ranking mechanisms: many real
mechanisms have failed to convert, and spending a board evaluation to discover
that again is waste.

### Rung 1: the weighted-score benchmark

Question: across protein language models, neighbourhood sizes and score
weightings, which combination retrieves the best candidate set?

This is the honest form of the grid. It runs on a stratified subsample, is
gated on recall and accretion coverage of the candidate set, and produces a
**per-cell winner** rather than a global one, because the axes already tell us
the regimes differ.

Gate: one frozen substrate, chosen on validation, per cell.

### Rung 2: the learned representation as the lever

Question: does the learned sparse encoder beat the winner of rung 1 at equal
input?

The winner of rung 1 is a hand-weighted combination. This rung replaces the
hand weighting with a learned representation and asks whether learning the
space beats tuning the blend. It is the first half of the argument that
learning beats calibration.

Counter-evidence already on record and to be respected: the sparse head does not
transfer between base models. It is a recipe fitted to a base, not a
transplantable trick, and the campaign must state that rather than discover it
twice.

Gate: retrieval improvement per stratum, with intervals.

### Rung 3: the functional classifier

Question: what does a full-vocabulary classifier add that neighbour retrieval
cannot reach?

Retrieval can only propose what a neighbour already carries. The classifier
proposes from the whole vocabulary, and the registry shows it carries the
no-knowledge and limited-knowledge regimes almost entirely while contributing
nothing in the prior-knowledge regime, where a different generator wins. That
asymmetry is the finding, and the routing that exploits it is the mechanism.

Gate: candidate-set improvement per cell, at matched volume, with intervals.

### Rung 4: signal integration

Question: which signals compose, and where?

Each signal enters as a feature family and is measured by removing it, per cell,
with an interval. Families that never enter the top of any cell are reported as
such rather than quietly retained. Families that were declared but never
produced are either produced and measured or retired explicitly. **This rung
produces the signal registry, which is the deliverable, not a by-product.**

The transversal that justifies the architecture belongs here: show the ceiling
of a tuned hand-weighted blend of the same signals, then show the learned tree
crossing it. That is the second half of the learning-beats-calibration argument,
and it is why the combiner is a contribution rather than an implementation
detail.

Gate: composition measured, not assumed.

### Rung 5: ensembling

Question: does combining models beat the best single model, and by a mechanism
we can name?

Three forms, measured separately because they fail differently:

- **Seed ensembling**: several initialisations of the same model, pooled. This
  reduces variance and is the defence against selecting a lucky run. It must be
  measured, and it must be alive in what is actually served, not only offline.
- **Representation ensembling**: several protein language models combined at
  retrieval. Measured evidence already favours combining spaces over combining
  candidate pools, and the distinction matters: pooling candidates pays an
  inheritance tax that combining spaces does not.
- **Generator ensembling**: routing different generators to the regimes where
  each wins, rather than averaging them everywhere.

Gate: the final one. Only here does the board metric decide, and only for the
frozen champion.

---

## 6. SLICES

Ordered. A slice is done when its gate has a receipt.

**Foundation**
1. Corpus ingestion, reviewed spine, with the ingest payload recorded as a versioned configuration rather than folklore.
2. Temporal span loading, with the release sweep declared in one place.
3. Additions and removals decomposed per window; the two corpus contractions diagnosed.
4. Accretion weighting promoted to a dispatchable operation.
5. The four-axis stratification implemented as a versioned module. It is a standing norm of this project with no implementation anywhere, and every stratified table until now came from a script that no longer exists.
6. Split registry: train, adjustment and validation declared in code as ordered release pairs with a guard, as the band registry already does for the ontology binding. Runs AFTER slice 3, since the adjustment windows cannot be chosen before additions and removals are decomposed.

**Scale**
7. Unreviewed ingestion at volume, provenance-flagged.
8. Distributed representation computation across both machines; throughput, correctness and reproducibility measured.

**Rungs**
9. Rung 1, the weighted-score benchmark on a stratified subsample.
10. Rung 2, the learned representation at equal input.
11. Rung 3, the functional classifier and the routing it justifies.
12. Rung 4, signal integration and the blend-versus-tree transversal.
13. Rung 5, the three ensembling forms.

**Culmination**
14. Directed case mining: unreviewed donors admitted only where the reviewed neighbourhood is thin, gated per stratum.

**Measurement machinery** (built alongside, because without it nothing above is a result)
15. The control family: shuffled feature, fixed score, random order, matched volume, accretion precision.
16. The cross-fit gate: choose on the folds, apply blind to the held-out one, report the spread.
17. Paired intervals computed in the reported frame rather than an adjacent one.
18. A row-alignment assertion wherever two tables are joined on a non-unique key.

**Documentation** (see section 7)
19. Repository READMEs.
20. The Sphinx narrative.
21. The thesis chapters.

---

## 7. DOCUMENTATION DELIVERABLES

Three surfaces, one source. The rule that already governs the explainability
registry governs this too: one source, three renderers, one lint.

**READMEs, one per repository.** What this component is, what it consumes, what
it produces, and how to run it. Written for someone who has just cloned it and
has nothing else.

**The Sphinx narrative.** The operational and architectural account: the
operation catalogue, the data model, the evaluation frame, the decision record,
and the runbooks. This is where an examiner goes to check that a claim is
reproducible, so it carries the identifiers that the thesis prose does not.

**The thesis.** The argument. Four pillars: the environment and its temporal
datasets; the representation; the signals and their integration; and the
frontier, which is the characterisation of where the method stops and why. It
obeys section 0 absolutely: no identifiers, no release numbers, no codes in
prose, and every number stratified on the four axes.

**Length is not a target, and the ceiling is deliberately low: forty pages is
acceptable if forty pages is what is relevant.** This inverts the job. The task
is not to repair the existing manuscript but to decide what earns a page, and
the readiness audit supplies the test. An implementation chapter that is almost
free of results, while the four contributions this campaign actually produced
have no section at all, is not a long thesis. It is a misallocated one.
Operational detail belongs on the reference surface, where an examiner goes to
verify that a claim reproduces. The argument surface carries the argument and
then stops.

The three surfaces must agree, and the lint that checks they agree is itself a
slice. A number that appears in the thesis and not in the interface is a defect,
and a number that appears in both but differs is a worse one.

---

## 8. WHAT THIS CAMPAIGN IS FOR

The result to beat is the current standing: first in seven of the nine cells,
with the two losses both in the biological-process aspect, in the
limited-knowledge and prior-knowledge regimes.

The campaign has two honest outcomes and both are publishable. Either the
remaining two cells fall, or they do not and we deliver the sharpest available
characterisation of why: a separability and calibration frontier, with the
portion of the missing signal that no evidence available at prediction time can
reach. The second outcome is not a failure. It is the fourth pillar, and it is
the part of this work that no leaderboard position could replace.
