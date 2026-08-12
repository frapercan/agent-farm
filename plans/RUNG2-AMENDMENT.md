# Amendment: rung 1.5, rung 2, and the stratification that was never applied

Written 2026-08-12 against `CAMPAIGN.md`. It strikes two false statements from
rung 2, inserts a rung between 1 and 2, and turns the declared four-axis
stratification into something that touches a result.

Every number is measured or cited to a receipt. Where a claim is an estimate it
says so. Two adversarial reviews of the first draft are folded in, and the
places they changed the design are marked, because the changes are the
interesting part.

## Why this exists

Rung 1 sweeps backbones, neighbourhood sizes and score weightings while holding
the dense substrate at one recipe: last layer, no chunking, mean pooled,
L2-normalised, truncated at 2048. Rung 2 puts a learned sparse encoder on that
frozen substrate and asks whether learning beats tuning.

If rung 2 wins, the campaign as written credits learning. The gain could instead
come from the substrate, and **that exact error has already happened once with a
receipt**.

The layer ablation of 2026-07-08 reported the learned encoder beating the best
fixed representation by 61 percent. The same-base control three days later
decomposed it: the base embedding was worth about +0.075 mean-of-nine and the
learned head **+0.0111** on a matched base. The headline had credited the head
with the substrate's gain. It was caught only because somebody held the base
fixed.

That is the whole argument for the rung in between.

## Three facts measured on this machine

### The substrate rung 2 assumes does not exist

`CAMPAIGN.md` states, in rung 2:

> A chunked substrate already exists at a longer maximum length with overlap,
> which is what the chunk variants read.

False. Every one of the eight embedding configurations is `use_chunking=False`,
`layer_indices=[0]`, `max_length=2048`.

| backbone | complete |
|---|---|
| esm2_650m, esm2_8m, ankh_large, prot_t5, ankh_base, esmc_600m | 100% |
| prostt5 | 42.7% |
| protst | 25.6% |

Five of six rung 2 arms have no substrate. **Strike the sentence rather than
correct it**, because a plan that believes it owns an input will not schedule its
production.

### The stratification module has no callers

`protea/core/strata.py` implements the four axes with bands, and a `pooled_mean`
that refuses to run without population sizes because pooling has been reported
wrongly before. Its only importer in the tree is its own test.

Declared, tested, and touching nothing. The same shape as the first-appearance
module and the seven artifacts with no producer.

### The homology axis was never populated because nobody priced it

It needs sequence identity, and retrieval gives cosine in a learned code space,
which is a different quantity. The machinery exists:
`protea/core/feature_engineering.py` computes global and local identity through
parasail with BLOSUM62, and `identity_nw` and `identity_sw` are already consumed
by the scoring router, the metrics helpers and the reranker schema.

Measured here, 300 alignments over sequences of mean length 654:

| | |
|---|---|
| per alignment | **0.9 ms** |
| one core | 1058 per second |
| k=30 over 7,401 targets of one LAFA window | **3 minutes** |
| k=30 over the whole 528,294 corpus | 4.2 hours on one core |

Twelve cores put the corpus at half an hour. The axis was not omitted for cost.
It was omitted because the cost was never measured. A per-pair cache is worth
adding: the bank holds 88,306 rows duplicating another row's sequence, so a
conserved protein is aligned against its forty-one identical twins forty-one
times.

## Rung 1.5: the fixed-representation ceiling

Question: what retrieval does a non-learned transformation of the dense substrate
reach, at fixed backbone?

It is a rung and not a warm-up. Rung 2's claim, without it, is that a learned
head beats **the one recipe the project happened to serve**, which is a claim
about a default.

Two facts make the confound fatal rather than merely present:

- The best measured fixed-substrate gain, an early-mid layer with per-dimension
  standardisation and fixed k-WTA, was **+0.0124** mean-of-nine over the served
  recipe, on eight of nine cells.
- The clean learned-head benefit at matched base was **+0.0111**.

**Same order of magnitude.** Freezing the substrate would be defensible if the
head were worth ten times it. At parity, an unablated substrate does not
attenuate the head's effect, it can invent it.

There is a sharper reason specific to the sparse arms. The negative verdict on
naive sparse representation was substantially an artefact of applying top-k to
raw hidden states, where a few massive-activation dimensions dominate selection.
Standardising first reversed it. **Run the sparse ablations before fixing the
dense substrate and the layer and the normalisation enter the measurement as
properties of the sparsifier.** That is the same error one rung later, on the
author's own lead lever.

### Axes, at fixed backbone and fixed scoring

| axis | values | where it lives |
|---|---|---|
| depth | five points across the stack, last included | `layer_indices`, platform |
| chunking | off, and 512 residues with 64 overlap | `use_chunking`, platform |
| residue pooling | mean, max | `pooling`, platform |
| standardisation | raw, per-dimension z-score | lab-side, no compute |
| fixed sparsification | dense, k-WTA at 128 and 256 | lab-side, no compute |

The z-score is fitted **on the reference pool only, never on the query set**. The
prior measurement of this lever used a transductive fit and flagged it, and the
project has a standing decision against transductive projection.

### Corrected after review: the selection protocol

The first draft drew the boundary at "fits parameters to GO labels" and put rung
1.5 on the free side. **That line does not hold.** Rung 1.5 chooses depth,
chunking, pooling, standardisation and k by maximising a GO-derived retrieval
metric. That is fitting to GO by discrete search. The partition is between two
forms of GO supervision, not between supervised and unsupervised.

And the budgets are wildly unequal. The lab-side axes are free in compute and
therefore invisible in the cost table, but they multiply the arm count sixfold:
the argmax runs over roughly **120 arms**, not 20. Against the declared noise
floor of 0.0034, the expected maximum of 120 null arms is about 0.0094. **The
selection bias alone is the size of the entire clean head effect the case rests
on.** The head, meanwhile, is one configuration with no search.

`CAMPAIGN.md` section 8 disqualifies exactly this practice, for exactly this
reason, in the project's own past. Promoting it to the baseline would be doing
the thing the campaign already refused.

So rung 1.5 carries a selection protocol, and it is not optional:

1. **Two windows.** The argmax runs on a selection window. The reported ceiling
   is measured on a second, untouched window, and it is that second number rung 2
   is compared against.
2. **The search budget is reported** with the ceiling: how many arms were
   compared, so the number can be read as what it is.
3. **The head gets the same treatment.** If the substrate is chosen by search,
   the head's hyperparameters are chosen by an equally sized search on the same
   selection window, or the comparison is between a maximum and a single draw.

### Corrected after review: the ceiling is not unmeasured

The first draft called the fixed-representation ceiling unmeasured. It is not,
and the record cuts against the head.

`SIGNAL-REGISTRY.md` section 5 holds `protst_zscore` at **+0.0335 mean-of-nine,
winning nine of nine**, with a receipt, described there as the largest
unexploited measured lever. A per-dimension z-score over a dense substrate **is
rung 1.5's own standardisation axis**. So a fixed, non-learned transformation is
already on record at three times the clean head benefit.

The registry also holds that a learned k-WTA head on that same substrate **loses
to the raw substrate**, negative on eight of nine cells, at two dictionary sizes.
The head was refitted there and still lost.

Both facts belong in the amendment rather than in a footnote, because together
they change what rung 2 is asking.

## The carrier, and what "best average model" means

The author's phrase names an object the campaign forbids. Section 2 states that
an unweighted mean across the nine cells is itself a reweighting, that it moves
in the flattering direction, and that no number is reported pooled. Rung 1
produces a per-cell winner by design.

**There is no best average model.** Rungs 1.5 and 2 do not need one. They need a
frozen backbone to build substrate variants on. That object deserves its own name
and its own criterion.

**The object is the ablation carrier. The criterion is dominance, not mean.** A
carrier is a backbone not significantly beaten in any of the nine cells. If none
dominates, the tie-break is declared before the table is read and it is not an
average.

### Corrected after review: completion is not a carrier criterion

The first draft said an incomplete configuration cannot be a carrier, which
disqualifies ProtST at 25.6 percent. **ProtST is the one backbone whose record
would falsify rung 2**, since the registry holds it winning nine of nine as a
fixed transformation and the learned head losing on it.

A rule that excludes it on operational grounds selects the substrate that
protects the lever. That is not hygiene, it is the shape of a result being
arranged.

So: **completing ProtST is a precondition of the carrier decision, not an excuse
to skip it.** If the campaign cannot afford to complete it, the carrier is chosen
without it and the amendment records that the choice excluded the strongest
counter-candidate, in those words.

## The substrate, and what it costs

### Three facts that invert the assumption

**Chunking is free at the accelerator.** `chunk_and_pool` in
`protea-backends/_chunk_helpers.py` slices an already-computed residue tensor. A
chunked configuration costs the same accelerator time and differs only in rows
written.

**Every layer is already in memory during that pass.** The backends run with
`output_hidden_states=True`. All depths come out of one forward pass. The
platform bills one job per configuration, so five depths cost five passes today,
and there is no technical reason they must.

**So the binding constraint is the write stage and the server's disk, not the
card.** That inverts what the campaign has been assuming. It matters because the
write stage is the one that ran out of memory before, and the database now lives
on the memory-constrained laptop.

### The layer axis, with its indexing trap

Platform convention counts from the output: `[0]` is the last layer. The prior
ablation counted from the input. For an encoder with 48 blocks, depth `d` from
the input is `layer_indices=[48-d]`. The prior credible winner at depth 10 is
`layer_indices=[38]`. **The hidden-state count differs per backbone and the
mapping must be recomputed, not copied.** The input layer itself is excluded: its
own receipt flags it as amino-acid composition.

**A precondition, not an optimisation.** Ankh loads in bfloat16 deliberately,
because half precision collapses its normalisation to NaN. T5 and ESM load in
float16. Mid-layer activations on ankh-base were measured near 490,000 against a
float16 ceiling of 65,504. So mid-layer configurations are safe on ankh and
**unvalidated everywhere else**: run a hundred-sequence probe and assert every
value finite before any mid-layer job on a T5 or ESM backbone. Storage is half
precision too, and overflow there is avoided only because `normalize=True` puts
the pooled vector on the unit sphere before the cast. **Normalisation stays on.
It is a guard, not a preference.**

### Corrected after review: hold the context window fixed

Rung 2's text has the whole-sequence arms truncate at 2048 while the chunk arms
read a longer limit, and asks the run to report coverage per arm. That plans a
confound rather than removing it: it measures chunking and coverage at once, and
the length stratum is where the two are indistinguishable.

**Every arm in rungs 1.5 and 2 holds `max_length=2048`.** The longer window
becomes a separate, labelled experiment on the tail above 2048 residues, which is
about 1 percent of the corpus. It answers a different question, it costs nothing,
and it removes a confound the current plan would have paid for.

### Sizing and pruning

Corpus is 528,294 sequences: mean length 399, median 318, ninety-fifth 969.

At 512 with 64 overlap and a 2048 cap, chunks per sequence is about **1.42**, so
a chunked configuration writes roughly 750,000 rows against 528,294. At 768
dimensions in half precision that is about 1.2 gigabytes against 0.85, before
indexes. **Estimated from the length distribution, not measured.**

One full-corpus pass on a mid-weight backbone took about **fifteen hours** on the
pair. The instantaneous rate implies closer to seven, so roughly half goes to
write, queueing and interruption. That gap is unmeasured and should not be
planned around.

The naive grid on the carrier is five depths by two chunkings by two poolings:
thirty configurations, **450 accelerator-hours, nineteen days of the pair flat
out**, before a second backbone and before anything is trained. Not affordable
and not necessary.

| pruning | effect |
|---|---|
| screen on the stratified subsample the campaign already mandates | ~70,000 sequences, two hours per configuration, twenty configurations in **40 hours** |
| only survivors go to full corpus | rung 2 needs exactly two materialised substrates, the winner and the incumbent: **30 hours** |
| pooling goes first if anything must go | attention pooling lost three ways, mean was never beaten, `mean_max` doubles the write |
| the second backbone is a transfer check, not a grid | two configurations on the subsample, four hours |

Total: **about 75 accelerator-hours, roughly four days including write**, against
450.

**The residue arms cannot be stored, and that is arithmetic.** 528,294 sequences
by 399 mean residues is about 211 million rows and 324 gigabytes in half
precision. They stream inside the ablation and are never written.

### The one piece of compute code worth writing, and when

All depths, chunkings and poolings derive from a single forward pass. An
`embed_chunks_multi` in the backends plus a multi-configuration payload in
`compute_embeddings` would take the full grid from thirty passes to one.

It is not on the critical path: the subsample screen is affordable without it. It
becomes worth writing at exactly one moment, **when more than two configurations
need full-corpus materialisation**. Measure the forward-pass share of a job
before committing, because the whole argument rests on the forward pass
dominating and that has not been measured on this hardware.

## Rung 2, restated

The A to F table stands. It gains one axis and two constraints:

- Every arm runs at the substrate rung 1.5 selects, not at the last layer by
  assumption.
- Arm A is re-run over that substrate, so the comparison is at equal input.
- **Rung 2 is a two-factor design.** The head is trained and evaluated on both
  the rung 1.5 winner and the rung 1 incumbent. The head's effect is a paired
  difference at fixed substrate, the substrate's effect is at fixed head, and
  **the interaction is reported**. The claim that the two are redundant was drawn
  across two extraction pipelines whose same-protein cosine was about 0.28, so it
  is not evidence. Treat additivity as unmeasured.

What is configuration and what is new code, against
`protea-reranker-lab/src/protea_reranker_lab/encoder_ablation.py`:

| axis | status |
|---|---|
| dictionary size, top_k, objective, hard negatives, epochs, pairs, seed | parameterised in `ArmSpec` and `EncoderAblationSpec` |
| which embedding configuration to read | a single field, so a depth sweep is a loop over specs |
| chunk-level input | **new code**, the spec assumes one vector per protein |
| residue-level input, streamed | **new code** |
| aggregation order, sparsify before or after pooling | **new code**, and it is the whole question |

Two defects to fix in that module before it runs: its default
`embedding_config_id` is a hardcoded esm2_150m identifier that no longer exists
after the rebuild, and its default ground-truth path still points at
`/home/frapercan`, the pre-reinstall username.

**Transfer is checked, not assumed.** The registry's strongest counter-evidence
is that the learned sparse head does not transfer between base models. The rung 2
winner is replicated on exactly one second backbone, on the screening subsample.
If it transfers, the finding is a recipe. If it does not, the finding is that it
is a recipe fitted to a base, which the campaign already says it must state
rather than discover twice.

## The stratification, wired and extended

Five axes. Two are new and one of them is free.

**Homology band, populated.** Priced above at three minutes for a LAFA window.
The axis the campaign has always declared and never carried.

**Kingdom.** The `protein` table already holds `organism` and `taxonomy_id` for
**575,503 of 575,503 canonical proteins**, because `fetch_uniprot_metadata` has
always requested them. There are 14,898 distinct organisms, so the band is the
kingdom derived from the taxonomy identifier, not the organism string. Four or
five bands, each with population enough to cross with the others.

**Neighbourhood coherence, defined so it does not measure k.** Two failed
definitions are recorded so they are not proposed again:

- *Maximum agreement over terms* is degenerate. Over 7,401 queries, **91.2%
  reach exactly 1.000**, because every annotated neighbour carries the ontology
  roots.
- *Any count-based fraction* moves with the neighbourhood size: at k=5 one
  disagreeing neighbour costs a fifth, at k=30 a thirtieth. Rung 1 sweeps k, so
  such a measure reports the parameter.

What survives both is the **mean pairwise information-content-weighted Lin
similarity among the k neighbours' propagated closures**. A mean over pairs does
not scale with k, and it reuses `lin_pairwise`, the function the encoder is
trained against.

Coherence and homology are different questions and must not be merged. **A
neighbourhood of close homologues that disagree functionally is where homology
transfer misleads**, and the campaign cannot currently see that cell. Coherence
is also a per-protein confidence signal, which is the shape of thing the
calibration wall needs and does not have.

### The wiring is the deliverable

Adding axes to a module nobody calls makes it worse. The work:

1. Extend `protea/core/strata.py` with kingdom and coherence.
2. Give the evaluation path a producer for each axis value, so a result carries
   its stratum rather than being labelled afterwards.
3. Make `assert_stratified` load-bearing where results are recorded, so an
   unstratified number cannot be published.

Without step 3 this repeats in three months.

## Order of work

1. Land the open container work and clean `develop`.
2. Wire the stratification, homology band populated. No new substrate needed, and
   it changes how everything after is reported.
3. Finish rung 1, **including ProtST**, for the carrier decision.
4. Screen rung 1.5 on the subsample, with the two-window selection protocol.
5. Materialise the two surviving substrates at full corpus.
6. Write the chunk and residue readers in the ablation module.
7. Run rung 2 as a two-factor design over both substrates.

Steps 2 and 3 are independent and can run on the two machines in parallel.
Everything from 4 is serial.

## What is uncertain, stated as such

- Whether an intermediate layer helps this backbone. The prior ablation says the
  last layer won, under a different pooling and without chunking.
- Whether chunking helps retrieval or only coverage. It certainly helps coverage:
  216 of 7,401 targets of one LAFA window exceed 2048 residues, 2.9%, and the
  longest loses 77% of itself. Whether recovering that tail moves the metric is
  unknown.
- The forward-pass share of a job, on which the fan-out argument depends.
- Whether the fifteen-hour full-corpus figure survives the current write path.

## One thing the campaign cannot do as written

**There is no mechanism for the two machines to message each other.** No queue,
no mailbox, no remote trigger. Every agent-spawning script in the farm is
single-machine. `TOPOLOGY.md` says it: git is the only channel that crosses, and
nothing pulls.

So a plan that depends on real-time coordination has no mechanism behind it. What
works is this file: committed here, pulled there, read by whoever runs. Any
instruction that must reach the other machine belongs in a repository, and
somebody has to pull.
