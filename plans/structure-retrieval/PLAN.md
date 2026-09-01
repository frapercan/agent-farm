# Structure retrieval: AlphaFold as a second INPUT, not a second encoding

Slice opened 2026-09-02 by author decision. It fills rung 7, which has been
parked since 2026-08-20, with a third level on the axis that rung already
declares.

The line is: store a folded-structure representation per protein, retrieve
neighbours over it exactly as the sequence side does, and let the existing
transfer and scoring machinery consume the donors it returns. AlphaFold is the
source of structure. Alignment-based structural search is explicitly not part of
it, by author decision on 2026-09-02, so the mechanism stays vector retrieval and
no external search engine enters the dependency set.

## 1. The one claim that justifies opening this at all

Rung 2 is closed, and it closed hard. Four encodings, 104 arms per cell, and the
largest first-to-second margin is 0.0015 against a noise floor of about 0.0093.
In half the prior-knowledge cells the four encodings score identically to six
decimals, which the rung reads correctly: they retrieve the same neighbours and
transfer the same terms.

That result is about four transformations OF THE SAME INPUT. Dense pretrained,
dense fitted, sparse pooled and sparse per residue are all functions of one amino
acid sequence. What rung 2 measured, and measured well, is that the sequence does
not have more retrievable signal left to extract by re-encoding it.

An AlphaFold model is a different input. It carries co-evolutionary information
recovered from a multiple alignment across a sequence database, which the protein
language model never saw in that form. That is the whole of the claim, and it is
narrow on purpose: this line is worth running if and only if structure supplies
information the sequence does not already contain.

The corollary decides the encoder question. A structure representation predicted
FROM the sequence, ProstT5 being the obvious example, falls inside rung 2's
closure by construction, because it is one more transformation of the same input.
It may be used as a cheap control. It may not be used as the channel.

## 2. What is inherited from the measurement that already exists

The signal registry lists `structural gate (AFDB/FoldSeek)` under REFUTED. The
receipt behind it, as quoted in `thesis-pillars/PILLARS.md`, is a clean positive
control that finds the true functional neighbour **66.6 per cent of the time for
molecular function and 20.7 per cent for biological process**, residual 0.545.

Two different things follow, and conflating them is how this slice goes wrong.

**What survives, and is not negotiable: do not aim this at the biological process
wall.** The mechanism behind 20.7 per cent is biology, not method. A fold
determines an active site, it does not determine a pathway. Changing the encoder
does not change that, and re-running it with embeddings instead of 3Di in the hope
of a different answer would be re-litigating a mechanism with a new
implementation. The BP wall stays evidence-bound and this is not the evidence.

**What does not survive: the reading of the molecular function number.** A control
that finds the true functional neighbour two times in three is not a refutation.
It is a strong retrieval signal that was measured as a gate on the wrong aspect
and never converted into a retrieval space. The registry has this exact failure
mode written into it twice already, for ProtST and for the learned k-WTA GO
encoder: refuted in one mode, never tried in another.

**The receipt is not on this disk.** `struct_gate/` lived under `storage/`, which
is deliberately not restored. The 66.6 / 20.7 pair survives as prose in a plan.
Under the no-archaeology norm it is recomputed by gate 1 below rather than cited,
and until then it carries no weight in any argument.

## 3. Three measured findings that constrain the design

**3.1 The winning channel weights embedding similarity at exactly zero.** Rung 2
found that what separates arms is the channel, not the encoding: holding the
weighting fixed, the four encodings spread 0.0540 under `embedding_only` at K=30
and 0.0025 under `composite_no_embedding`, whose weight on embedding similarity is
exactly 0.0 and which wins 72.7 per cent of cells.

A second retrieval space is a second embedding similarity. Fed in as a similarity
weight it enters through a gate the champion holds at zero. So the structural
channel is designed as a **candidate generator** and as a **reranker feature**, and
never as a similarity weight. Its gate is recall and accretion coverage of the
candidate set, which is rung 1's own wording, not a score contribution.

**3.2 The bank must not be sampled from the embedding's own proposals.** Rung 7
already records this trap for the alignment retriever: the 2,059,944 pairs in the
alignment cache are exactly the pairs the embedding retriever proposed, so they
are a sample biased by the hypothesis under test and cannot serve as the search.
The identical error is one convenience step away here. Fetching AlphaFold models
only for proteins the embedding index already returns makes it impossible to
observe a donor the embedding cannot reach, which is the entire question. The
structural bank is defined by the cohort and its full candidate universe, never by
the embedding's top K.

**3.3 The payoff cannot come from ordering.** Re-weighting a donor set is worth
+0.0725 and permuting a fixed 30 donors is worth exactly 0, and 86 per cent of
what a no-knowledge protein gains is already reachable from 30 donors. A second
retrieval space therefore has to pay in donors the sequence index cannot reach at
all, in the twilight band, or it does not pay. This is why the primary gate is
disagreement and reach, not rank quality.

## 4. Where it enters the ladder

**Rung 7, `the retriever`, axis `retriever` on field `payload.search_backend`,
as a third level beside embedding and alignment.**

It is not rung 1 and not rung 2. Both of those vary `embedding_config_id`, which
is a representation of the sequence, and rung 2 closed that axis by measurement.
Structure is a different input reaching the same retrieval mechanism, and rung 7
is the rung whose declared subject is what generates the candidate set rather than
how it is encoded or scored.

One honesty note that has to be recorded rather than smoothed over. The rung's
axis note says the alignment level "requires a backend that is not vector search,
numpy and faiss are both vector search". A structural k-nearest-neighbour IS
vector search, so this level does not satisfy that note. The note describes what
the alignment level needs, not a property required of every level, and the axis is
the generator rather than the arithmetic. Recorded here so a reader meeting the
contradiction finds it already answered.

**The rung's secondary question is the one to run first, and it is not blocked.**
Rung 7 was reframed on 2026-08-20 to ask, beyond whether the top hit is right,
whether the neighbourhood a retriever returns AGREES, measured as consensus among
returned donors. Consensus is a property of the returned set, not of the score.
So it can be measured before the scoring axis names a winner, which is the
dependency that parked the rung.

**What stays blocked, and it is real.** The rung was parked because "it cannot be
read until the scoring axis names a winner to hold fixed", and rung 1 is still
`running` with its `score_weighting` axis unresolved. The primary question, does
structure propose better candidates at equal bank and equal scoring, inherits that
blocker unchanged. Gates 1 to 3 below are readable now. Gate 4 is not, and is not
scheduled until rung 1 closes.

## 5. What this is aimed at, stated as a cell

Not "add structure". The target is **no-knowledge, molecular function, twilight
homology band**: the population the system actually serves, the aspect where the
existing control already scored 66.6 per cent, and the band where sequence
identity stops separating and fold conservation does not.

That target is deliberately not where the board is lost. The two lost cells are
LK-BPO and PK-BPO, and section 2 says structure is not the tool for them. Stating
it this way keeps the line from being sold as a wall-breaker, which it is not, and
keeps the wall's characterisation intact as the fourth pillar.

### The one speculative exception, with a falsifiable prediction

AlphaFold publishes a predicted aligned error matrix, which is inter-domain
confidence, which is a domain decomposition available for free. That permits
retrieval **per domain** rather than per chain. A whole-chain 3Di alignment cannot
do that, so this is the single mechanism by which the new form could beat the old
20.7 per cent rather than reproduce it, since process-level function is carried by
domain combination more than by any one fold.

It is speculation until measured, and it is marked as such. The prediction that
makes it falsifiable: if per-domain retrieval helps biological process, the gain
appears on multi-domain proteins and is absent on single-domain ones. Stratify on
domain count. If the gain is flat across that split, the mechanism is not the one
claimed and the BP arm closes.

## 6. The second product, and the leak it carries

AlphaFold returns confidence as well as coordinates. Per-residue pLDDT identifies
disordered regions, and disorder is functionally loaded toward regulation,
signalling and binding. A disorder fraction is a per-protein scalar that adds no
candidates, so it pays none of the `prop=fill` tax that the pool-augmentation arms
paid, and it is a family the feature schema does not have: a sweep on 2026-09-02
found zero occurrences of alphafold, afdb, plddt or pae across the deployed
operations, the contracts and the plan store.

**It carries the failure mode that made the literature gate RED.** AlphaFold was
trained on solved structures, and what has been solved is what someone chose to
study, so pLDDT is a proxy for how well studied a protein is, which correlates with
the knowledge cell and therefore with the label base rate. That is a base-rate
leak of the same shape as the honest-prior gate. The control is the same: measured
within cell and within homology band, never pooled, with the NK cell reported on
its own. A pLDDT feature that helps only in aggregate is the leak, not the signal.

## 7. Frame and axes

The four axes apply without exception: category, aspect, length bucket, and
homology band split by whether the supporting evidence is experimental.
Confidence intervals on every difference.

The frame is declared in full on every number this slice produces, per the frame
problem: ontology and information-accretion version, `prop`, `norm`, `max_terms`,
`th_step`, and whether `-known` was applied to the prior-knowledge cells.

One temporal note in this line's favour. AlphaFold's database snapshot predates
every annotation release in the campaign frame, and AlphaFold was trained on
structures rather than on the ontology, so the structural channel carries no
annotation leakage by construction. This is the opposite of the text channel. The
pLDDT base-rate correlation in section 6 is the only leak vector, and it is a
correlation with the population rather than with the labels.

## 8. Producers that must be written

The campaign invariant is that no artifact exists without a registered operation
that produces it, and the governing principle of the genesis audit is that what
must survive is the procedure. Nothing here may live as a script under `storage/`.
Four producers do not exist anywhere today:

1. **Structure acquisition.** UniProt accession to AlphaFold model, cached, with
   provenance stamped. Must handle fragmentation: models above the per-entry
   residue ceiling are split into numbered fragments, so a per-protein artifact
   needs a fragment policy.
2. **Structure encoding.** Model to per-protein vector. The fragment pooling
   decision reuses the chunk-pooling decision already settled for the language
   models rather than inventing a second one. Batches are budgeted in residues,
   not in chains, for the same reason as the sequence side and more sharply,
   since geometric attention is quadratic in length.
3. **Structural index build and query.** Reuses the reference-cache and neighbour
   machinery if the vector shape matches, which is the intended design. Neighbour
   search stays on the processor. It never runs on the graphics card here.
4. **Confidence features.** Per-protein disorder fraction and whatever else
   section 6 justifies, emitted through the declared feature families with the
   schema guard able to see them.

## 9. The hardware envelope, which this line does not violate

The campaign restricts backbones to what runs on both machines, roughly six and a
half gigabytes usable on the companion machine, and gives up about a tenth of the
proxy to keep the grid homogeneous.

Structure encoders are small. Inverse-folding and geometric encoders are one to
two orders of magnitude below the language models in parameter count, so the
structural channel fits on both machines with room to spare and introduces no
heterogeneity. The cost moves from model memory to storage and acquisition, which
sits with the machine that owns state.

Two costs to count honestly before scaling past the cohort. The corpus is on the
order of half a million sequences, so a full structural bank is an acquisition and
storage project rather than a compute one. And the production index is already
10.83 per cent dead donors from isoform redundancy and uncharacterised entries; a
second index duplicates that waste unless the deduplication guards run on it
first.

## 10. Gates, cheapest first, each able to close the line

**Gate 1, the control, recomputed not cited.** On the target cohort, does the
nearest structural neighbour carry the query's true molecular function term, and
at what rate? This reproduces the lost `struct_gate` receipt and satisfies the
no-archaeology norm at no extra cost. Floor: it must clear the sequence retriever's
rate on the same cohort, or the channel has no claim.

**Gate 2, disagreement.** Overlap between the structural top K and the embedding
top K on the same queries, in the twilight band, per cell. The ceiling of any
fusion is bounded by the disagreement, so this is measured before any score.
Floor: if the donor sets substantially coincide, there is nothing to fuse and the
line closes here, for the price of a few thousand acquisitions.

**Gate 3, reach and consensus.** Of the donors only the structural retriever
returns, how many carry an annotation the embedding donors do not, and does the
structural neighbourhood agree with itself? This is rung 7's secondary question and
it does not need the scoring winner. Floor: candidate-set recall and accretion
coverage improve per cell at matched volume, with intervals.

**Gate 4, the primary question, blocked.** Does structure propose better candidates
at equal bank and equal scoring? Not scheduled until rung 1 names a scoring winner
to hold fixed. Entering it early repeats exactly the mistake rungs 1 and 2 both
made.

Scope discipline throughout: the cohort and its candidate universe, not the
corpus. The full bank is built only after gate 3, and building it earlier would
spend the acquisition before knowing whether the donors differ.

## 11. Naming collision to avoid

Stage C of the operation sequence is already called "structures" and means
reference caches, the co-occurrence structure and domain signatures. Folded
structure is a different thing. Acquisition belongs with the corpus stage and
encoding with the representation stage, and the word "structure" alone is
ambiguous in this plan store. This document says "folded structure" or
"conformation" where the 3D object is meant.

## 12. Placement under a clean campaign, and the split between the machines

Author instruction, 2026-09-02: this line is integrated now, the campaign is
restarted clean, and the two machines arrive at it gradually and in step.

That changes where this document claims to sit. Section 4 identifies rung 7 of
the CURRENT ladder as the correct slot, and the reasoning there holds on its own:
this is a question about what generates the candidate set, not about how the set
is encoded or scored. But the ladder itself is under renegotiation, so section 4
is a placement PROPOSAL and not an amendment. `rungs.yaml` is read by CI and a
job whose axes contradict its rung fails before it runs, so it is not edited
unilaterally from the node while the shape of the campaign is being agreed.
Whether this becomes a rung of its own or a third level on the retriever axis is
the first thing the two machines settle.

What does not depend on that decision, and can be built while it is settled:

- the acquisition and encoding producers of section 8, which are needed under
  any placement and are the campaign invariant's price of entry,
- gate 1 and gate 2 of section 10, which read on a cohort and answer whether the
  line survives at all,
- the four-axis strata, which every measurement needs regardless.

**The division of labour follows the topology and not preference.** The server
owns state, so acquisition, the object store, the index and the registered
operations are its half. The node owns the graphics card and holds nothing, so
encoding passes and the measurements that consume them are its half. The node
cannot hold the bank between reboots and must not try.

**Sequencing, so neither machine waits on the other.** The producers of section 8
are server work and are the long pole. The node's first useful contribution does
not need them: gate 1 and gate 2 run on a cohort small enough to acquire by
accession, and answering them decides whether the full acquisition is worth
scheduling at all. Building the bank before gate 2 reads would spend the
acquisition to learn something a few thousand fetches could have told us.
