# The neighbourhood dataset: what the two machines agreed, and the one open decision

Settled between the laptop and the desktop on 2026-10-10. `TOPOLOGY.md` says who runs what;
this says what we are building and what it costs. One decision is left to Francisco and it is
at the end.

## Why the shape changed

`analyze_annotation_evolution` over the 74 releases (job d6875a3c) found that the propagated
corpus of P shrinks 20% in ten years while the RAW pairs grow in all three aspects (C x1,64,
F x1,74, P x1,17). What fell is the graph: P keeps its terms (29.542 to 30.881) and loses 26,2%
of its `is_a`/`part_of` edges (61.412 to 45.326). Edges per term track propagated pairs per
protein at r=+0,978 over the series.

So a delta between two releases mixes annotation change with ontology change, and at some
transitions the ontology is all of it. Any dataset that stores propagated labels across the
series is measuring the graph. That is the constraint everything below is built around.

## What we agreed

**The graph is a read parameter, not a constant.** Labels are stored RAW; propagation happens at
read time with the ontology snapshot as a declared field of the query. The laptop first proposed
freezing the graph at release 156; the desktop objected that annotations to terms created after
2016 would be lost, and the measurement settled it: of the 9.403.205 events, 8,07% of all gains
and **12,69% of PK** land on terms absent from the 156 graph, and PK is half of everything that
enters. The decomposition identity holds under any fixed graph, so the falsification test below
survives this change.

**The substrate is a longitudinal census of neighbourhoods.** A fixed panel of queries and the
full roster of their donors at each of the 66 cuts before the v227 mark, so that every change in a
neighbourhood splits without remainder into "the donor set changed" and "their labels changed".

**It is falsifiable inside itself.** Five pre-mark transitions have two consecutive releases
sharing one `ontology_snapshot_id`: 156-157, 159-160, 177-178, 191-192, 202-203. In those five the
graph term of the decomposition must be EXACTLY zero. If the pipeline reports anything else it is
broken, and that is known without argument.

**On top of it, the event eve.** For each first RAW appearance of a (protein, aspect, term), the
neighbourhood observed in the release immediately before, plus the -2/-4/-8 ladder, which is the
only thing that answers "since when did they know" rather than "did they already know".

**Two clocks on the label.** The release of appearance is the task's label, because that is what a
predictor at r could see. `annotation_date` is for stratifying. The delay between them is not
noise to clean: it is the ladder's variable. Measured: 64,5% of first appearances in 226 to 227
carry an `annotation_date` before 2024, so a first appearance is mostly the file catching up.

**No chunking.** None of the eight D48 configs chunks: one row per (sequence, config), truncated
at 1022, which now affects 39.415 sequences of 663.590 (5,9%). Embedding rows are SEQUENCES, not
proteins; the census joins through `protein.sequence_id`.

**Sequences are today's.** `resolve_protein_sequences` fetched the CURRENT sequence, so a protein
whose sequence changed after cut r is represented at r by one that did not exist then.
`date_sequence_modified` is now populated, so the census carries a column "sequence modified after
r" to stratify or exclude. Reconstructing historical sequences from UniSave only if that fraction
turns out large.

**Division of labour.** Embeddings on the desktop's GPU. Everything else on the laptop, including
the KNN, which stays on CPU. One embedding pass and one KNN prefix at M=1024 serve every cut,
because an embedding is a function of the sequence and not of the release; after that, sweeping
the series is masking.

## What it costs

Measured on this database, proteins with a sequence, by evidence tier:

| Tier | Proteins | Sequences | Raw residues |
|---|---|---|---|
| With experimental | 188.259 | 180.744 | 102,42 M |
| T3 only (ISS and family) | 112.140 | 105.944 | 52,26 M |
| Neither (Swiss-Prot by `is_swissprot_entry`) | 407.697 | 332.171 | 132,84 M |
| Whole store | | 663.590 | 285,9 M raw, 259,1 M truncated (90,6%) |

The desktop's rate for the eight configs at batch 1 is 0,552 h per million truncated residues.
Applying the global 90,6% as an UPPER bound (the experimental tier averages 566,7 raw residues a
sequence, well above the store's 431, so it truncates more and its real factor is lower):

| Option | What it embeds | GPU, upper bound |
|---|---|---|
| 1. Restricted | experimental only, 8 configs | 51 h |
| 4. Restricted + T3 | adds the curated-inference tier, 8 configs | **77 h** |
| 3. Restricted + cheap model | 8 configs on experimental, `esm2_150m` on the rest | 56 h |
| 2. Fully permissive | everything, 8 configs | 144 h |

Wall clock is not GPU time: a machine that sleeps at night turns 50 GPU hours into four or five
calendar days. A shutdown costs only the batch of 64 in flight, because `skip_existing` filters by
sequence and config.

## The open decision, which is Francisco's

**What should the permissive axis of D48 mean?** The universe admits on four criteria, and the
fourth is not an evidence code: `is_swissprot_entry` admits an accession that was reviewed AT THE
RELEASE its GAF row comes from, whatever its evidence. That is why 407.697 proteins with neither
experimental nor curated-inference evidence are in the corpus, 406.077 of them carrying only IEA.

So "permissive" is two different hypotheses, not one price:

- **Option 4** — a donor may carry a CURATOR'S JUDGEMENT by sequence similarity even though it is
  not a measurement. This is the control `_universe_sources` describes in its own words: whether
  an embedding neighbourhood reaches where curated alignment reaches.
- **Option 2** — a donor may also be one NOBODY LOOKED AT, admitted for having been reviewed in
  its day while its only annotation is automatic.

Option 3 is cheaper than 4 but changes a pre-registered rule: D48 selects the bank by AVERAGING
the eight PLMs, and under option 3 a single model would decide it — the smallest, the one least
like the others. If it is chosen, D48 has to say so.

Both machines recommend **option 4**: 26 hours more than the restricted run, 67 fewer than full
permissive, the averaging rule untouched, and an axis that states a hypothesis someone can argue
with.

## Still to build

- A guard in `generate_evaluation_set`: nothing checks that the loads of BOTH sides finished.
  Eight of the 65 sets were built while their old release was still loading and had to be
  rebuilt on 2026-10-10; at 153 minutes of lag one of them saw 3,7% of its old release and
  reported its `nk` 430 times too high.
- `job.interrupted` on the shutdown grace, releasing the lease, treated as definitive by the
  reaper. Today a job killed by a shutdown stays RUNNING for up to `event_grace_seconds` = 2700 s
  because a recent event makes it look alive; that is the 42 minutes lost on 2026-10-09.
