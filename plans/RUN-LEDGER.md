# RUN LEDGER: what has been computed, at what rate, and what is left

Opened 2026-07-29, the night the reinstalled desktop joined the laptop as a
compute node. `CAMPAIGN.md` stays authoritative for what the run is FOR and
`SIGNAL-REGISTRY.md` for what each signal is worth. This file answers a
narrower question that neither of them tracks: what has actually been computed,
how fast, and what the next stage is waiting on.

It exists because the platform does not answer it. See "The instrumentation
gap" at the end, which is the finding this ledger was born from rather than an
afterthought.

**Rule for this file.** Every number here is measured and says how. Nothing is
carried over from a previous machine, and nothing is an estimate unless the
word estimate appears next to it.

---

## 1. The machines

| | role | device | joined |
|---|---|---|---|
| laptop | persistent server, owns all state | see open question below | before this ledger |
| desktop | compute node, no state | RTX 3060, 12 GB | 2026-07-29 01:14 UTC |

The desktop runs one `protea.embeddings.batch` consumer and nothing else. The
write stage stays on the server, which is the split the queue layout already
encoded.

---

## 2. Stage A, corpus

Complete for the reviewed tier. Measured from `/v1/proteins/stats` and the job
history on 2026-07-29 01:30 UTC.

| quantity | value |
|---|---|
| proteins total | 616,846 |
| canonical | 575,503 |
| isoforms | 41,343 |
| reviewed / unreviewed | 616,846 / 0 |
| with functional metadata | 575,503 |
| with GO annotations | 557,481 as of 15:50 UTC, was 0 at 01:30 |
| ontology snapshots loaded | 10, spanning 2024-03-28 to 2026-01-23 |

Sequence lengths, which decide the cost of every representation stage:

| statistic | residues |
|---|---|
| minimum | 2 |
| p10 | 100 |
| median | 296 |
| p90 | 665 |
| p99 | 1,537 |
| maximum | 35,213 |

525,782 of 575,503 sit below 706 residues, so 91.4 percent of the corpus is
short. The tail is thin but extreme: about twenty sequences exceed 10,000
residues. Any batch sized for the mean will fail on the tail, and any batch
sized for the tail wastes the card on the body. This is the single most
actionable fact in this ledger and it is picked up in section 5.

**Annotations landed during the day.** Two GOA releases were loaded at 10:36 and
12:37 UTC, 10.65 million annotations between them, and 557,481 of the 575,503
canonical proteins now carry GO terms: 96.9 percent. Ground truth exists.

That closes the gap this ledger flagged twice. The functional question in
section 3ter, whether centring returns better neighbours rather than merely
different ones, is now answerable and was not before.

**Still not done in stage A:** release publication dates are not backfilled, and
the unreviewed tier is not ingested at all.

---

## 3. Stage B, representation: the run in progress

The first real compute of the campaign.

| | |
|---|---|
| operation | `compute_embeddings` |
| backbone | ESM2 650M |
| recipe | max_len 2048, mean pooling, L2 normalised |
| fan-out | 8,255 batch messages of 64 sequences |
| dispatched | 2026-07-29 01:04 UTC |
| desktop joined | 2026-07-29 01:14 UTC, after 31 batches |

### Measured throughput

**The headline number is the share, not the rate.** The rate moves; see the
section immediately below, which is the important one.

Over the first 33 minutes of sampling, 01:32 to 02:05 UTC:

| consumer | batches/s | share |
|---|---|---|
| desktop, RTX 3060 | 0.181 | 51% |
| laptop | 0.172 | 49% |
| **combined at that point** | 0.353 | |

A 91 second spot measurement at 01:28 had read 0.319 and split it 48/52. Both
windows agree on the split and disagree on the rate, which is the first hint of
what the next section confirms.

The two machines are within five percent of each other, so the pool is balanced
and neither is the bottleneck. That much held all night.

**The rate is not constant. It rises monotonically, and the cause is known.**
Five consecutive twenty minute segments gave 0.349, 0.376, 0.405, 0.455 and
0.510 batches/s: 46 percent faster after 100 minutes, with no segment slower
than the one before it. The first half hour looked flat only because the window
was too short to contain the trend.

The mechanism was confirmed rather than guessed. Per-batch compute time on the
desktop, split into fifths of the 1,568 batches it had done, falls the same way:
5.04, 4.53, 4.01, 3.45, 3.25 seconds, with both the minimum and the maximum of
each fifth falling too. **The batches are genuinely getting shorter sequences.**
This is not warm-up, not contention and not the network, all of which would
leave compute time flat.

The sequences arrive shorter because of the order the corpus is read in, and
that order is accidental. `compute_embeddings` selects sequence ids with no
`ORDER BY` at all, so rows come back in whatever physical order the table
happens to have.

**The profile is a U, not a slope.** An earlier version of this section said the
order correlates with declining length. That holds for the first half and is
wrong for the second. Per-batch compute time on the desktop, binned by position
in the corpus and measured on both backbones over the same span:

| corpus position | ESM2 650M | Ankh base | ratio |
|---|---|---|---|
| 0 to 10% | 5.21 s | 12.94 s | 2.5x |
| 10 to 20% | 4.16 s | 10.93 s | 2.6x |
| 20 to 30% | 3.60 s | 8.34 s | 2.3x |
| 30 to 40% | 3.24 s | 6.27 s | 1.9x |
| 40 to 51% | 3.28 s | 6.24 s | 1.9x |
| 51 to 61% | 3.77 s | 8.63 s | 2.3x |

Cost falls to a minimum near 40 percent and climbs again after it, and **both
backbones turn at the same place**, which is what makes it a property of the
corpus rather than of either model.

Three consequences, and the third is the one that bites:

- **Any rate measured in one window misestimates the total, in either
  direction.** A rate from the first hour is too pessimistic; one from the
  trough near 40 percent is too optimistic. Quote a rate with the window it came
  from, and prefer the whole series.
- **A length-aware batch size would gain across the whole run.** A fixed batch
  sized for the opening is wrong in the trough and wrong again in the tail, and
  the U means no single constant is right anywhere for long.
- **Nothing guarantees this order holds.** It is a property of the current
  physical layout, not of the query, and a vacuum or a rewrite can change it
  without warning. If the run order matters, and the two points above say it
  does, then it should be an explicit `ORDER BY` rather than a coincidence that
  happens to be convenient today.

Per-batch timing on the desktop, from 20 consecutive batches: mean 4.92 s,
median 4.80 s, range 4.40 to 5.95 s.

**Overhead is smaller than it first looked.** The desktop delivers a batch every
5.52 s and computes one in 4.92 s, so fetch, acknowledge and result publication
cost about 0.6 s, or 11 percent of wall time. An earlier reading of 25 percent
came from the opening batches and was inflated by model load and warm-up. The
sample series is what corrected it.

Card occupancy on the desktop across the whole run, 262 samples covering 01:32
to 05:54 UTC: **82 percent average utilisation, 1,841 MiB average, 2,419 MiB
peak of 12,288**. The card was busy and nowhere near full, which is the pair of
facts that section 5 turns into a recommendation.

The series itself is kept at `storage/throughput/embeddings-run-2026-07-29.tsv`,
262 rows at one minute resolution. Sampling stopped when the run did, so the
file is the record of this run and not a rolling log.

Two rates that should not be trusted, recorded so nobody re-derives them:

- RabbitMQ's `ack_details.rate` reported 0.20 batches/s, which would have given
  11.1 hours. It is a lagging moving average and it was wrong by a factor of
  nearly two.
- Extrapolating from per-batch compute time alone gives 0.203 batches/s per node
  and ignores the delivery overhead.

There is no single rate to quote for this run. Use the sample series, which is
appended to `storage/throughput/embeddings-run-2026-07-29.tsv` at one minute
resolution, and say which window any figure came from.

### Progress

| when (UTC) | batches done | proteins with embeddings | remaining |
|---|---|---|---|
| 01:04 | 0 | 0 | 8,255 |
| 01:32 | 438 | 31,411 | 7,817 |
| 02:05 | 1,139 | 82,250 | 7,116 |
| 02:42 | 2,055 | 145,557 | 6,200 |
| 03:20 | 3,200 | 243,935 | 5,055 |
| 03:55 | 4,224 | 311,969 | 4,031 |

**The rise ended at about half the corpus.** Five consecutive thirty minute
segments gave 0.347, 0.406, 0.471, 0.511 and 0.500 batches/s: monotonic until
the fourth, then flat. That is what the length distribution predicts. Once the
run is into the body of the corpus, where 91.4 percent of sequences sit below
706 residues, there is little length left to shed and the rate settles.

Projected completion moved from 07:41 to 07:12 to 06:06 UTC while the rate rose,
and has held at about 06:09 since it flattened. Each earlier estimate was honest
at the time and each was too pessimistic, for the reason above.

The unit cost for this backbone, using the whole series rather than any single
window: **ESM2 650M over the reviewed corpus costs 4.8 hours on these two
machines together.** Section 3bis shows why that figure does not generalise, and
it was written after the second backbone made the point unavoidable.

### The run completed

| | |
|---|---|
| job status | SUCCEEDED, 8,255 of 8,255 |
| dispatched | 2026-07-29 01:04:02 UTC |
| finished | 2026-07-29 05:51:20 UTC |
| **wall clock** | **4 h 47 min** |
| desktop share | 4,102 batches, 49.7 percent |
| failures | none; dead letter queue empty, no requeues, no errors in either log |

Four hours and forty seven minutes beat every estimate made during the run, for
the reason in the previous section. **The unit cost to record for planning is
therefore under five hours per backbone over the reviewed corpus with both
machines**, and it is a floor for the heavier members of the grid.

### Two things the completed run exposed

**Coverage is reported as 104.58 percent.** The embeddings-by-model view divides
proteins carrying an embedding by canonical proteins only, so the ratio exceeds
one. A percentage above a hundred on the interface is a presentation defect and
should be an easy fix, but it is worth fixing rather than explaining, because it
is the surface an examiner reads.

**The reason it exceeds one is not cosmetic: isoforms were embedded too.**
`with_embeddings` equals 616,846, the full protein count including the 41,343
isoforms, not the 575,503 canonical. The operation selects every sequence row
with no restriction to canonical entries, so isoform sequences entered the bank
alongside their parents.

Whether that is wanted is a decision, not a bug, and it has not been made
anywhere in the plan documents. Two reasons it deserves one before the retrieval
stage runs:

- **Cost.** Roughly seven percent of this run, and of every backbone after it,
  goes to sequences that may not belong in the bank.
- **Neighbour quality, which matters more.** Isoforms of one gene are
  near-identical by construction. A reference bank holding both a protein and
  its isoforms gives nearest-neighbour retrieval a cluster of near-duplicates to
  return, which can crowd out genuinely informative neighbours and inflate any
  transfer that rewards close matches. The campaign's whole candidate stage
  rests on that retrieval.

Recorded rather than acted on. If canonical-only is the answer, the filter
belongs in the operation and the existing embeddings for isoforms can stay
without harm as long as the bank query excludes them.

---

## 3bis. The second backbone, and why one unit cost is not a grid cost

`compute_embeddings` was dispatched again at 06:21 UTC for **Ankh base**, same
recipe, same fan-out of 8,255 batches. The node picked it up with no
intervention, which is the topology working as intended.

Measured over the first 27 minutes, against the comparable early window for the
first backbone:

| | ESM2 650M | Ankh base |
|---|---|---|
| early-window rate, both machines | 0.353 batches/s | **0.121 batches/s** |
| card memory, average | 1,841 MiB | **3,008 MiB** |
| card memory, peak | 2,419 MiB | **4,262 MiB** |
| card utilisation | 82% | 96% |
| measured wall clock | 4.8 h | still running |

**Ankh base is slower and uses 1.7 times the memory**, at an identical recipe
and an identical corpus. Parameter count does not predict this: Ankh base is the
smaller model of the two.

On the multiple, two figures that are both right and mean different things. End
to end in the early window it read 2.9 times slower, but those windows were not
at matched corpus positions. Comparing pure compute at the **same corpus
positions**, in the table in section 3, the ratio sits between 1.9 and 2.6 with
no trend across the span, and averages about **2.2 times**. Use 2.2 for the
model comparison and the end to end figure only for scheduling.

The flat ratio also settles a question this ledger raised earlier and can now
close: Ankh base does not scale worse with sequence length than ESM2. It costs a
near-constant multiple, and the earlier appearance of worse scaling came from
comparing windows that sat at different places in the corpus.

### Both runs finished, and the estimate can be scored

| backbone | wall clock | mean rate | ratio to the first |
|---|---|---|---|
| ESM2 650M | **4.79 h** | 0.479 batches/s | 1.00 |
| Ankh base | **9.41 h** | 0.244 batches/s | **1.96x** |

Both completed 8,255 of 8,255 with no failures. Every protein in the reviewed
corpus now carries a vector under each of the two backbones.

**Two estimates were made during the run and one of them was much better.**

| method | predicted | error |
|---|---|---|
| extrapolate from an early wall-clock window | 14.0 h | **+49%** |
| the compute ratio at matched corpus positions | 10.5 h | +12% |

The reason the first failed is worth keeping, because it looks reasonable until
it is measured. It took the factor by which the first run's rate rose between
its early window and its whole-run average, 1.36, and applied it to the second.
The real factor for the second run was 2.01, not 1.36.

**A fixed window of time samples a different fraction of the corpus for every
model.** In 33 minutes the first backbone covered 8.5 percent of the corpus; in
27 minutes the second covered 2.4 percent. The second run's window sat entirely
inside the expensive opening described in section 3, while the first run's had
already reached cheaper batches. The correction factor was never a property of
the corpus; it was a property of how far into the corpus each window happened to
reach.

**The rule for the rest of the grid.** To estimate a new backbone, measure it
over a fixed **fraction of the corpus** and compare it against a known backbone
over that same fraction. Do not measure it for a fixed number of minutes. The
third member started at 15:52 UTC, so its cost can be predicted from its first
eight percent rather than waited out.

### The connection drops once per backbone, at model load

Two minutes into the second run the worker lost its AMQP connection with
`ConnectionResetError(104)`. Its own retry, twelve attempts with backoff,
recovered it and no work was lost. Worth understanding rather than filing as a
blip, because it is reproducible by construction.

The disconnect landed immediately after a batch that took **133.5 seconds**: the
one that downloads and loads the model. The library's connection is blocked for
the whole of a batch, so a batch that long misses its heartbeat and the broker
closes the socket. Every batch since has run between 4.5 and 26 seconds, median
13, none above 60, and there has been no second disconnect.

So the exposure is not the steady state. It is **the first batch of every new
backbone**, and it grows with the model, which means the largest member of the
grid is the one most likely to hit it hardest. Today the retry absorbs it. The
failure mode to watch for is a load slow enough to outlast twelve attempts, at
which point the batch is redelivered and computed twice.

Cheap ways to remove it, none applied here: load the model before the consumer
starts rather than inside the first message, raise the heartbeat, or send
heartbeats from a separate thread during inference.

### The link between the machines is weak, and it is measurable

The idle watch reported the server unreachable at 09:35 UTC. It was not: ping
came back at 0 percent loss, all five ports answered, and the worker had written
to its log in the same second. A request had simply timed out.

The link explains it. This desktop reaches the server over wifi at **-75 dBm**,
and the latency shows it: 0 percent loss but 39.7 ms average, 147 ms peak, 39.9
ms of jitter. The same machine pings the access point at 2.7 ms, so the slow hop
is the one to the laptop rather than ours.

Two things already in this ledger connect to it:

- **Part of the per-batch overhead is this link.** Section 3 measured 0.6 s per
  batch that is not compute. A batch needs several round trips to fetch,
  publish and acknowledge; at 40 ms each that is roughly 0.2 s, about a third of
  it.
- **It is the likeliest source of the failure that eventually costs something.**
  The one disconnect so far was absorbed by the retry. A link this weak is what
  produces a drop that outlasts twelve attempts, and then the batch is
  redelivered and computed twice.

A cable between the two machines removes this class of failure entirely and
returns part of the overhead on every batch of every backbone in the grid. It is
the cheapest improvement currently available to the run.

### What this costs the campaign

An earlier version of this ledger put a grid of eight backbones at roughly a day
and a half. **That was wrong, and it was wrong because it generalised from a
single measurement.** On the evidence of two backbones the spread is nearly
threefold, and the field still contains Ankh large, which is registered as a
configuration and is bigger than either model measured here.

The honest statement is that the grid cost is not known and cannot be projected
from one or two members. What can be said:

- **The cheapest member measured costs 4.8 hours. The next costs about three
  times that.** A grid of eight is therefore days, not a day.
- **Memory is the constraint that will bite first.** Ankh base peaks at 4,262
  MiB of a 12,288 MiB card. The campaign's envelope section reasons about a
  companion machine with roughly 6.5 GB usable, and a model that grows the way
  Ankh base grew over ESM2 will reach that ceiling before this desktop's.
- **Measure each member before committing the grid**, since neither parameter
  count nor family predicted the cost of the one measured here.

---

## 3ter. Are the stored vectors valid? Measured against the database

Asked directly of the stored rows on 2026-07-29, read-only, on a sample spread
across the whole corpus.

### Structurally: yes, without reservation

| check | ESM2 650M | Ankh base |
|---|---|---|
| rows stored | 528,294 | 102,528 and rising |
| dimension | 1,280 | 768 |
| non-finite values | none | none |
| zero vectors | none | none |
| duplicates in 1,500 sampled | none | none |
| L2 norm, mean | 1.000001 | 1.000002 |
| worst deviation from 1.0 | 2.6e-04 | 1.4e-04 |

Dimensions match each model, the L2 step is applied correctly, and the deviation
is exactly the noise `halfvec` storage predicts. **Nothing needs recomputing.**

Note in passing: embeddings are per SEQUENCE, and 616,846 proteins share 528,294
distinct sequences. That, not a bug, is why the coverage view exceeds 100
percent.

### Geometrically: they carry a large common direction, and retrieval keeps it

| | ESM2 650M | Ankh base |
|---|---|---|
| mean cosine between random pairs | **0.858** | 0.594 |
| norm of the mean direction | **0.927** | 0.773 |
| mean cosine after centring | 0.013 | -0.001 |

92.7 percent of every ESM2 vector is a direction every protein shares. Centring
removes it completely and leaves the space isotropic.

`knn_search` L2-normalises and does nothing else: there is no centring and no
standardisation anywhere in the retrieval path. So the common direction reaches
the benchmark untouched. Measured effect on the neighbours themselves, top 30:

| | ESM2 650M | Ankh base |
|---|---|---|
| top-30 overlap, raw versus centred | 0.634 | 0.623 |
| top-10 overlap | 0.703 | 0.700 |
| same nearest neighbour | 0.805 | 0.865 |
| spread of cos(v1) to cos(v30), raw | **0.0239** | **0.1891** |
| the same after centring | 0.2530 | 0.4434 |

**Centring changes about 37 percent of the thirty neighbours in both models.**

### Why this matters for a matched grid, and it is the third point that bites

The grid is matched in recipe, and deliberately so: all four configurations are
byte-identical apart from the model. It is not matched in the geometry that
recipe produces. The whole top-30 of ESM2 spans 0.024 of cosine while Ankh's
spans 0.189, an eightfold difference that says nothing about either model and
everything about how much common direction each carries.

That would be a curiosity if only the ranking were consumed. It is not. The
pipeline emits `min_distance`, `mean_distance`, `neighbor_distance_std`,
`neighbor_min_distance` and `neighbor_mean_distance` as features, and accepts a
`distance_threshold` that drops neighbours above a cut. So **the raw distance
value, on a per-model scale, is fed to the model downstream**, and a threshold
calibrated on one backbone means something entirely different on another.

### What was measured and what was not

Measured: that centring changes which neighbours are returned. Not measured:
that it returns better ones. That needs functional ground truth, and the GO
annotations are not loaded yet.

Pointing the same way, from the project's own record: the 2026-07-08 ablation
measured +9 percent on real GO transfer from standardisation, which subsumes
centring. Different layer, single model, so it is corroboration and not proof
for this grid.

All of it is fixable after the fact. Centring is a transform on stored vectors,
so none of the compute already spent is at risk.

---

## 3quater. The grid, measured: four backbones and a method that works

By the end of 2026-07-29 the rung 1 grid had three members measured end to end
and the fourth running, all at an identical recipe over an identical corpus.

| backbone | wall clock | ratio to ESM2 | card peak | batch size |
|---|---|---|---|---|
| ESM2 650M | 4.79 h | 1.00 | 2,419 MiB | 4 |
| ESM-C 600M | 4.84 h | 1.01 | 3,490 MiB | 4 |
| Ankh base | 9.41 h | 1.96 | 5,213 MiB | 4 |
| Ankh large | **about 15.4 h, predicted** | 3.21 on compute | **5,918 MiB** | **2** |
| **grid total** | **about 34.4 h** | | | |

**A grid of four costs a day and a half of continuous compute on these two
machines**, and the largest member alone accounts for 45 percent of it. The
estimate this ledger carried a day earlier, a day and a half for eight members,
was wrong by a factor of two, and it was wrong because it generalised from the
cheapest member.

### The estimation method, scored twice

| backbone | predicted | measured | error |
|---|---|---|---|
| Ankh base | 10.5 h | 9.41 h | **+12%** |
| ESM-C 600M | 4.4 h | 4.84 h | **-9%** |

Two predictions inside 12 percent **with the errors in opposite directions**,
which is what says there is no systematic bias. Both came from the same recipe:
compare per-batch compute time against a known backbone **over the same fraction
of the corpus**, then scale that backbone's measured wall clock.

The predictions also settle quickly. Ankh large read 3.23x over its first 2.3
percent of the corpus and 3.21x over its first 4.7 percent, so a usable figure
arrives within an hour of a fifteen-hour run rather than at the end of it.

**One correction that made things worse, recorded so it is not repeated.** After
the first score, this ledger proposed shaving 12 percent off future predictions.
Applied to ESM-C that would have given 3.9 h against 4.84 measured, an error of
-20 percent, worse than not correcting at all. Fitting a correction to a single
observation is overfitting even when the observation is real.

### Where the method's limit is

ESM-C's compute was measurably cheaper than ESM2's, 0.92x at matched positions,
yet its wall clock came out at 1.01x. The gap is per-batch overhead, which the
compute ratio does not see.

So the rule has a stated scope: **matched-position compute predicts wall clock
only while per-batch overhead is comparable between the models.** Ankh large is
exactly where that assumption is weakest, because its batch size was halved to
2 and it therefore pays the fixed per-batch cost twice as often. Its 15.4 h
should be read as a floor.

### The memory ceiling is now the binding constraint

Ankh large peaks at **5,918 MiB, 48 percent of a 12 GB card, already with the
batch size halved**. Read against the campaign's hardware envelope, which
reasons about roughly 6.5 GB usable on the companion machine, that is not
comfortable headroom: it is the edge.

This is the concrete form of the question `CAMPAIGN.md` raises and leaves open.
The envelope section asks which backbones the grid may consider given the
companion machine. The answer for the largest member is now measurable rather
than argued, and it is close enough to the limit that it should be measured on
the companion machine directly before the grid is fixed.

### Not done in stage B

The learned sparse encoder head has not been applied, so no retrieval codes
exist. Only one backbone of the grid has been computed.

---

## 4. Stages C through G

Not started. Nothing in the platform has produced a reference cache, a
co-occurrence structure, a domain-signature scan, an accretion weighting, an
evaluation set, a candidate set, a feature table, a trained model or a score.

The gate in `CAMPAIGN.md` section 4bis is the next structural event: the first
window goes through the entire chain, evaluation included, and everything stops
for inspection before the run widens.

**Worth resolving before that gate.** The run in progress computes
representations for the whole canonical corpus rather than for a first window.
Base representations are a substrate that every window needs, so this is
defensible, but it is worth stating out loud that the first end to end chain has
not yet been exercised and this run does not exercise it.

---

## 5. What the measurement says about open questions

### The hardware envelope, partly answered by observation

`CAMPAIGN.md` flags an open question it says should be settled before rung 1:
the companion machine has eight gigabytes, and it matters whether that is system
memory or graphics memory, because the answer changes which backbones the grid
may consider.

Tonight's run bears on it without anyone having to go and look. The laptop is
sustaining 0.165 batches/s on ESM2 650M, which is a 650 million parameter
forward pass over 64 sequences roughly every six seconds. A processor at single
precision does not do that; the same work on the desktop's card takes 4.9
seconds. **The evidence strongly favours graphics memory.** It is evidence and
not proof, so confirm it directly before the envelope decision rests on it, but
the burden has moved.

The same run also measures the envelope itself. The desktop holds the backbone
and its activations in **1,916 MiB at batch size 4**, against the roughly 6.5 GB
the campaign calls usable. The chosen backbone is not close to the ceiling.

### The batch size is sized against a different model than the one running

The payload carries `bs=4`, which leaves 84 percent of a 12 GB card untouched.
Reading the operation makes the picture more specific than "conservative".

The parameter's own default is **1**, and its documented reason is that the
largest backend in the field runs out of memory on a 12 GB card at anything
higher, at `max_len=2048`. The docstring invites callers on smaller models to
raise it. So `bs=4` is already a deliberate raise, and the ceiling it is being
measured against belongs to a model that is not the one running.

What the run measures is the actual figure for this backbone: **1,916 to 2,419
MiB of 12,288**, against a limit that was set for a much larger model. The
headroom is real and specific.

The fix is still not a larger constant, because the corpus is read longest first
by accident and a constant that fits the opening batches wastes the rest. It is
grouping by length so batch size follows the group. Recorded here rather than
acted on.

---

## 6. The instrumentation gap

This ledger is hand-built because nothing in the platform can produce it, and
that is a defect worth naming precisely.

**PROTEA publishes no operation metrics.** Its Prometheus endpoint exposes eight
series, all of them HTTP request counters, latency histograms and the database
pool gauge. There is no counter of jobs dispatched or completed, no histogram of
operation duration, no throughput of any kind. The cost of every stage of this
campaign is therefore unmeasurable after the fact.

**RabbitMQ publishes only aggregates.** `rabbitmq_queue_messages_ready` is a
single series summed across all eleven queues, with no queue label. Tonight it
happens to equal the depth of the embeddings queue because that is the only
queue with work. The moment two queues are active the number stops meaning
anything. Per-object metrics exist in the plugin and are switched off.

Both are small changes with a large consequence, because the thesis argues about
a productised environment and cannot presently state what that environment costs
to run. Until they land, the sampler under `storage/throughput/` is a stopgap
that writes to a tree the project deliberately does not carry between machines,
which is exactly the shape of defect the campaign's invariant exists to remove.

---

## 7. Log

| when (UTC) | what |
|---|---|
| 2026-07-28 22:02 | ten ontology snapshots loaded |
| 2026-07-28 22:0x | reviewed corpus ingested, functional metadata fetched |
| 2026-07-29 01:04 | `compute_embeddings` dispatched, 8,255 batches |
| 2026-07-29 01:14 | desktop joined as second consumer |
| 2026-07-29 01:28 | first spot measurement, 0.319 batches/s, later superseded |
| 2026-07-29 01:32 | continuous sampling started |
| 2026-07-29 02:05 | rate read as 0.353 batches/s over 33 minutes, thought stable |
| 2026-07-29 02:42 | 70 minute series shows the rate rose 17 percent, not flat |
| 2026-07-29 03:20 | rise confirmed monotonic and traced to declining sequence length |
| 2026-07-29 03:55 | past halfway; the rate plateaus at 0.50 batches/s as predicted |
| 2026-07-29 05:51 | run complete: 8,255 batches in 4 h 47 min, no failures |
| 2026-07-29 06:21 | second backbone dispatched, Ankh base, picked up automatically |
| 2026-07-29 06:23 | one AMQP disconnect at model load, absorbed by the retry |
| 2026-07-29 06:52 | Ankh base measured 2.9 times slower; the grid estimate corrected |
| 2026-07-29 09:20 | stored vectors verified valid; anisotropy differs per model and reaches the features |
| 2026-07-29 09:35 | false unreachable alert traced to a weak wifi link at -75 dBm |
| 2026-07-29 13:15 | corpus cost profile is a U, not a slope; the model ratio is flat at 2.2x |
| 2026-07-29 15:41 | Ankh base complete in 9.41 h; the 14 h projection was 49 percent high |
| 2026-07-29 15:52 | third backbone dispatched, ESM-C 600M, picked up automatically |
| 2026-07-29 20:41 | ESM-C complete in 4.84 h; the method's second score, 9 percent low |
| 2026-07-29 20:45 | fourth backbone dispatched, Ankh large, at half the batch size |
| 2026-07-29 22:00 | Ankh large predicted at 15.4 h; the grid totals about 34 h |
| 2026-07-29 12:37 | GO annotations loaded: two releases, 10.65 M annotations |
