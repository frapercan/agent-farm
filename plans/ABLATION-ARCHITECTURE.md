# The complete ablation: axes that hold still, one pass that keeps its evidence, and a grid sized to what the benchmark can resolve

## Preamble: the number that reorganised everything

Before writing a line of this plan I read the project's own artefact at `agent-farm/plans/farm-platform/artefacts/knn_226_227_fmicrow.csv`, which carries a measured per-cell population for every one of the nine category-by-aspect cells. The counts are 354, 161 and 243 for no-knowledge BPO, CCO and MFO; 307, 181 and 180 for limited-knowledge; and 2,382, 809 and 1,057 for prior-knowledge. They sum to 5,674 protein-aspect units, of which 4,248 (74.9 per cent) are prior-knowledge. Every design that reached me assumed between 11,800 and 13,054 units, derived from an assumed 1.9 to 2.1 aspects per protein. The real figure is 0.913 aspects per protein, and the low-knowledge cells that carry the entire thesis claim hold between 161 and 354 proteins each.

From the same artefact I extracted the between-model spread at K equals 3, restricted to the five models whose K equals 3 row was scored on the full cohort. In prior-knowledge BPO the five-model range is 0.0046 Fmax points; in prior-knowledge MFO it is 0.0046; in prior-knowledge CCO it is 0.0082. In limited-knowledge CCO it is 0.0494 and in limited-knowledge BPO 0.0440. The representation effect is roughly ten times larger in the cells with two hundred proteins than in the cells with two thousand. That inversion, measured rather than assumed, decides the reporting geometry, the retention decision and the grid, and it is the reason this plan does not cross a third axis with anything.

While reading that file I also found that the K comparison the brief hands me as settled is not settled. For ankh_base the K equals 5 rows carry populations of 124, 69, 90, 145, 60, 99, 942, 308 and 401, summing to 2,238, against 5,674 for the K equals 3 rows. For ankh_large the K equals 3 rows sum to 1,472 and one cell is marked `no_positives`. For prostt5 and esmc_600m the K equals 3 rows are on the 2,238 subcohort while their K equals 10 rows are on the full one. Four models (esm2_150m, esm2_3b, esm2_650m, prot_t5) have all three K rows on the full cohort and K equals 3 wins in all four. One more (ankh_base) has a clean K equals 3 against K equals 10 and K equals 3 wins. The remaining three have no matched K comparison at all. So the honest statement is that K equals 3 wins in five of eight models on a matched cohort and is untested in three, and the "seven of eight" figure compares arms scored on different populations under the same column heading. That is precisely the failure this plan exists to make impossible, and it is why K becomes a free axis derived from stored neighbour lists rather than a constant chosen once.

---

## Erratum, recorded rather than corrected away

Two defects were found in the preamble above after it was written, both by the
other machine, and the section 1 power table is provisional until the second is
resolved. They are recorded here because a plan that quietly repairs itself
teaches nothing about how it failed.

The first is a mislabel and it is now fixed in place. The spread figures were
computed over the five models whose K equals 3 row was scored on the full cohort,
which is the right computation, and they were then described as the eight-model
range, which they are not. Over all eight models in the same file the ranges are
0.0284 in prior-knowledge BPO, 0.1011 in prior-knowledge MFO and 0.1480 in
prior-knowledge CCO. Read literally, the original label inverted the paragraph's
own conclusion, since 0.0284 sits six times above the stated detectable effect.
This is the same failure the plan warns about two pages later: a correct number
whose frame is mislabelled in the sentence carrying it.

The second is open and it governs the table. A matched re-run on the live store,
with the ground-truth restriction disabled, returned 27 of 29 cells bit-identical
to four decimals and coverage of 6,216 of 6,216 in every cell. So no ground-truth
protein is being dropped, the evaluated population is the full set at every K,
and `n_proteins` is not the scoring denominator there. If it is a diagnostic
counter rather than a population, then the five-model restriction was unnecessary
and the eight-model spreads apply, and the minimum detectable effects and the
floor of 129 are all computed from a quantity that is not the count it is named
after. Those two consequences push the conclusion in opposite directions, so the
table cannot be patched by adjusting either one alone.

What settles it is nine numbers: the distinct proteins holding ground truth in
each category-by-aspect panel at the cut, independent of model and of K, compared
against the `n_proteins` the rows carry. Until those land, section 1 is a method
for sizing the grid and not a sizing of it, and the forecast in it is not yet
pre-registered.

Note also that the artefact read here is a July export of the embedding registry
that the clean run replaced. It carries esm2_150m and esm2_3b, which the live
registry does not, and lacks esm2_8m and protst, which it does. It is therefore a
surviving record of configurations that no longer exist, which makes it evidence
rather than merely stale, and it should not be regenerated over.

## 1. The axis catalogue

### The mandatory partition

The unit of observation is the protein-aspect pair, and category and aspect together form a partition of nine panels that never merge, never pool, and never take a third axis crossed into them. That is not a preference. It follows from the population arithmetic below.

Category has three levels (no knowledge, limited knowledge, prior knowledge) and aspect three (BPO, MFO, CCO). One caution the technician must respect: no-knowledge is defined in `protea/core/evaluation.py` as a protein-level property, no experimental annotation in any namespace at the temporal cut, while limited and prior knowledge are per-namespace. A no-knowledge protein therefore contributes up to three units that share a sequence and a neighbourhood, and their per-protein differences are correlated by construction. Every bootstrap in this plan resamples proteins, not units, and where a protein contributes several units they move together. Treating them as independent would narrow the intervals in exactly the cells the thesis is about.

### The minimum cell population, derived

The comparison of two arms inside a cell is paired within protein, so the governing quantity is the standard deviation of the within-protein Fmax difference, which I will write as sigma_d. The project has measured it once, indirectly. `SIGNAL-REGISTRY.md` records the prefilter study as "10 of 10 disjoint folds chose 0.4, +0.0092 sd 0.0034". A fold covers a tenth of the cohort, so the standard deviation of a fold-level mean difference is sigma_d divided by the square root of 567.4, and sigma_d is therefore 0.0034 times the square root of 567.4, which is 0.0034 times 23.820, that is 0.081.

The sample size for a paired difference at ninety-five per cent confidence and eighty per cent power is n equals (1.9600 plus 0.8416) squared times sigma_d squared divided by delta squared, that is 7.849 sigma_d squared over delta squared. At sigma_d equal to 0.081 and a declared resolution delta of 0.02 Fmax points, n equals 7.849 times 0.006561 divided by 0.0004, which is 128.7.

**The minimum cell population for inference is 129 proteins.** I write it as 129 rather than rounding to 150, because a rounded floor invites the question of where the rounding came from and a derived one does not. Below 129 a cell reports a point estimate, a bias-corrected accelerated bootstrap interval and its own n, and is excluded from every difference claim and from the multiplicity family. Below 40 it reports counts only, because the acceleration term of that bootstrap is estimated by jackknife and is unstable there.

Two things about that floor must be said rather than buried. First, sigma_d is a property of a contrast class, not a constant. The 0.081 above comes from two arms that share their retrieval entirely and differ only in a prefilter threshold, so it is the low end. Two different backbones retrieve different neighbours and their sigma_d is larger. The floor scales as sigma_d squared, so at sigma_d equal to 0.13 the floor is 7.849 times 0.0169 over 0.0004, that is 332, and six of the nine mandatory panels fall below it. Measuring sigma_d per contrast class is therefore the first deliverable of the census in section 4, and it is free: the ankh_base and esm2_650m banks already exist at K equals 3 on the full cohort, and a paired bootstrap over their stored predictions costs CPU minutes and no GPU at all.

Second, the useful statistic is not the floor but its inverse, the minimum detectable effect per cell, which is 2.8016 times sigma_d divided by the square root of n, that is 0.22693 over the square root of n at the measured sigma_d. The nine panels give the following, and this table is the spine of the whole plan.

| panel | n | minimum detectable effect | measured five-model spread at K equals 3 |
|---|---|---|---|
| prior, BPO | 2,382 | 0.0047 | 0.0046 |
| prior, MFO | 1,057 | 0.0070 | 0.0046 |
| prior, CCO | 809 | 0.0080 | 0.0082 |
| no, BPO | 354 | 0.0121 | 0.0311 |
| limited, BPO | 307 | 0.0130 | 0.0440 |
| no, MFO | 243 | 0.0146 | 0.0176 |
| limited, CCO | 181 | 0.0169 | 0.0494 |
| limited, MFO | 180 | 0.0169 | 0.0057 |
| no, CCO | 161 | 0.0179 | 0.0285 |

Read the last two columns together. In the three prior-knowledge panels the spread is at or below the detectable effect, so there is nothing there to resolve, however many proteins they hold. In four of the six low-knowledge panels the spread is two to three times the detectable effect, so the model axis resolves. That is the nine-cell regime map restated in the currency of power, and it produces a falsifiable forecast published here before the grid runs: under Benjamini-Hochberg at q equal to 0.10 over a family of the seven models compared against a declared reference, within each panel, the multiplicity-adjusted detectable effect is 0.26354 over the square root of n, and the model axis will resolve in no-knowledge BPO, limited-knowledge BPO, limited-knowledge CCO and no-knowledge CCO, will be borderline in no-knowledge MFO (0.0176 against 0.0169), and will not resolve in limited-knowledge MFO or in any prior-knowledge panel. If the run contradicts that, the forecast was wrong and the thesis says so.

### The four new axes, all marginal

Because every panel would lose between half and two thirds of its resolving power to a three-level or four-level subdivision (no-knowledge CCO at three levels holds 54 proteins per level and a detectable effect of 0.031, larger than any representation effect the project has ever measured except the base recipe itself), **no axis is crossed with a third axis. Each of the four new axes is reported as a set of level rows inside each of the nine panels, with its own n printed on every row, and only rows clearing 129 enter a difference claim.** The full crossing stays recoverable, because the frozen coordinate table in section 4 carries every protein's complete axis vector and the stored per-protein curves let any subset be re-aggregated. What is foreclosed is the claim, not the data.

This is where I part company with the first design, which proposed a crossed core of three categories by six reach levels by three aspects, 54 cells at a stated mean population of 241, and called it "the largest crossed grid the benchmark can carry". The mean was the wrong summary of the only distribution that matters, and the real distribution is 161 to 2,382 with a minimum of 161 before any subdivision. There is no crossed grid the benchmark can carry.

**Length**, three inferential levels. At or below 512 residues, 513 to 1024, above 1024. The boundaries are mechanism boundaries: the default `chunk_size` is 512, the default `max_length` is 1022, and the ESM family was trained at 1024 positions. Populations come from a lognormal fitted to the two measured target quantiles: mu equals the natural log of 468, that is 6.14847, and sigma equals the natural log of 1181 minus the natural log of 468, divided by 1.28155, that is 0.92564 over 1.28155, that is 0.72229. That gives 54.95 per cent at or below 512, 31.13 per cent from 512 to 1024, 11.87 per cent from 1024 to 2048 and 2.048 per cent above 2048, or 3,416, 1,935, 738 and 127 of the 6,216 proteins.

The fit is validated against a fact it was not fitted to. The measured information-accretion mass shares are 53.22, 43.11 and 3.68 per cent for at or below 512, 513 to 2048 and above 2048. Dividing each mass share by the fitted count share and multiplying by the overall mean of 29 terms per protein gives 28.1, 29.1 and 52.1 terms per protein by band, against a stated long-protein mean near 53. The fit reproduces the 53-against-29 term-density fact to within 1.7 per cent. A second, independent route to the same place: if long proteins carry 53 terms against a mean of 29, then the count share above 2048 is 3.68 per cent times 29 over 53, that is 2.014 per cent, which agrees with the fitted 2.048 per cent to 0.034 percentage points.

**This corrects two designs in opposite directions and matters more than it looks.** The first design derived 2.5 per cent and 156 proteins from a lognormal it then overrode by hand; a refutation of it asserted that the measured mass share is the count share and produced 229 proteins and a claim that no-knowledge BPO would clear the floor in the long band. Both are wrong. The mass share is a share of information-accretion-weighted terms and long proteins carry 1.83 times the mean term count, so the count share is smaller, not larger. The consequence is that proteins above 2048 residues number 127 in the evaluation set, roughly 14 per panel, and **the above-2048 regime cannot carry an inferential claim in any panel of this thesis.** It is reported as a count-only line. Everything that any design proposed to build for it, input tiling, raised context, a sliding-window forward path, is therefore not built. Section 3 says so again with the wall clock attached.

**Nearest-donor identity**, four levels: no significant donor, at or below 60 per cent, 60 to 90, above 90. The edges are the conventional confident-transfer line and the near-identical line. The twilight line at 30 is not used as a level boundary, for the reason given next.

**Reach, the propagation gap.** This is the axis the author asked for and it needs its definition stated exactly, because both the definitions on offer were wrong in ways that would have produced a table of noise.

Fix a reference bank B at a stated temporal cut, and fix an aspect a. For a query q, let identity be defined as the number of matched residues divided by the length of the shorter of the two sequences, expressed as a percentage, taken from a single Smith-Waterman pass with statistics. Let S(q) be the set of donors in B whose alignment against q clears a Karlin-Altschul expectation value of one in a thousand, under lambda and K calibrated for this bank. Then:

I_any(q, a) is the maximum identity over donors in S(q) carrying any annotation in aspect a.
I_exp(q, a) is the maximum identity over donors in S(q) carrying at least one of the thirteen experimental evidence codes in `protea/core/evidence_codes.py`, in aspect a.
gap(q, a) equals I_any minus I_exp, in identity points.

The experimental donors are a subset of the annotated donors, so I_exp is never greater than I_any and the gap is never negative. Either quantity may be undefined, and undefined is a level, never a missing value. The reach axis has five levels: co-located, where the gap is zero and the nearest thing there is already carries experimental evidence; shadowed, where the gap is positive and at or below the interior edge; remote, where the gap exceeds the interior edge; orphaned, where significant donors exist and none of them is experimental, which is the population the author named; and void, where no donor clears significance at all.

The interior edge is not chosen by intuition. It is the median of the strictly positive gaps over the 6,216 queries, measured by the census, frozen before any arm is scored, and printed in the thesis. Setting it at the median makes the two occupied interior levels equal in size, which maximises the power of the single contrast that the axis exists to support.

**The significance gate is the correction that the refutations forced, and it is not a detail.** The current identity in `feature_engineering._parse_alignment` is matches divided by alignment length, and a design measured that over 487,237 random non-homologous pairs this statistic reaches 1.0000, because Smith-Waterman finds a short perfect local patch in any pair. That diagnosis is right and it means the existing `GOPrediction.identity_nw` and `identity_sw` columns must never be joined into this axis. That design's replacement, matches over the shorter length with a floor at 30 per cent and a claimed noise ceiling of 23.1, was then refuted by a direct measurement of the right statistic: the distribution of the per-query maximum over a bank, rather than the maximum over one pooled draw. Twelve queries against a bank of 50,000 composition-matched random sequences gave per-query maxima between 0.307 and 0.380 with a median of 0.342, and a Gumbel tail coefficient of 0.0269 per natural log unit of bank size puts the median per-query maximum at 0.342 plus 0.0269 times the natural log of 487,237 over 50,000, that is 0.342 plus 0.061, that is 0.403, at full bank size. **Every query's best raw identity against a bank of half a million random sequences is around 40 per cent.** No fixed identity floor can gate a maximum over that many alignments; that is what expectation values are for. Real proteins carry compositional bias and low-complexity regions that random draws do not, so the null must be calibrated on shuffled real bank sequences, and that calibration is a hard precondition of the sweep, not an afterthought.

**Taxonomy**, three levels: model organism, other eukaryote, non-eukaryote. Membership is by lineage containment, not taxid equality, so strain-level identifiers resolve, using the `ete3` machinery `feature_engineering._cached_lineage` already carries, keyed on `Protein.taxonomy_id`. The model-organism set is the Gene Ontology Consortium reference genomes at the frozen cut: 9606, 10090, 10116, 7955, 7227, 6239, 4932, 4896, 3702, 44689. Superkingdom is rejected: at corpus proportions Archaea is 3.23 per cent and Viruses 2.95 per cent, giving 201 and 183 proteins across the whole evaluation set, which is 22 and 20 per panel, dead before the category split. The variable that actually matters to the argument is curation density of the query's clade, because the most damaging critique of nearest-neighbour transfer over language-model embeddings is that it works only where a near-identical model-organism ortholog already sits in the bank, and that critique is answered inside Eukaryota, which is where the benchmark's mass is. Two type seams must be closed first: `Protein.taxonomy_id` is a nullable string while `QuerySetEntry.taxonomy_id` is an integer, so the two will not join in SQL without a cast and will join silently and wrongly in Python; and stale NCBI identifiers fail resolution silently through the cached lineage lookup. The census counts both, and if resolution coverage is low the taxonomy axis is cancelled rather than reported as one large unknown bucket plus noise.

### The one thing the stratifier must never be

Every axis above is a property of a protein, a sequence and a frozen bank, and none of them is a property of an embedding. If cell membership depended on which neighbours an arm retrieved, then two arms would be scored on different populations under the same column heading, and the bias would run the flattering way, since the better representation promotes its own easy cases into the easy bands. One design proposed to compute the propagation gap as "a second k-NN scan against the same vectors under that boolean mask, costing nothing in storage". Against the same vectors is the defect. The stratifier is frozen sequence-space.

The arm-dependent quantity is not discarded, it is promoted. Per configuration and per query the plan records the identity of the top-ranked retrieved donor, the identity of the top-ranked retrieved donor carrying experimental evidence, and the rank at which the first experimental donor appears. That is the sharpest available statement of the thesis claim, threshold-free and scorer-free: representation A recovers experimental evidence at rank three and 22 per cent identity where representation B needs rank eleven and 41 per cent. It costs a lookup against the frozen alignment table for donors already in it, and at most 6,216 times 30 times 0.2 alignments for the ones that are not, that is 3.7 million alignments at 8,692 per second per core, which is 0.12 core-hours.

---

## 2. What one forward pass retains

### The algebra, and the granularity it buys

Chunking happens after the forward pass. `_chunk_and_pool` receives the model's residue tensor of shape L by D and only then computes spans, and `_compute_chunk_spans` steps by `chunk_size` minus `chunk_overlap` from zero, so every span start is a multiple of the step and every span end is either a multiple of the chunk size offset from a step boundary or exactly the sequence length. It follows that if the chunk size and the overlap are both multiples of a granularity G, every span the production code emits is exactly the union of consecutive blocks of G residues, including the ragged final span. I take G equal to 128, which is the greatest common divisor of every geometry the campaign will run (chunk 256, 512 and 1024 with overlap 0, 128 and 256) and sits below the smallest structural domain, so no domain is split across more than two blocks.

Three reductions merge upward exactly. A mean over a union of blocks is the residue-count-weighted mean of the block means, which is why the residue count per block must be stored. An elementwise maximum over a union is the elementwise maximum of the block maxima, by associativity. And a mean of per-residue unit vectors is itself a count-weighted mean of block unit-means, which is the reduction that reproduces `normalize_residues`. The one design that built this substrate called `normalize_residues` "the sharpest single loss in the design ... unrecoverable from sums, from maxes, and from norms", and that claim is false: it is recoverable for the price of one more mergeable array, because the code applies the flag after layer aggregation and before pooling, so a per-rung unit-mean reproduces it exactly for every single-rung recipe, which is the preset under which the models are known to separate.

What does not merge is `normalize`, the per-window L2 that `_chunk_and_pool` applies inside the span loop. That is why it is a stored recipe knob rather than a reconstruction: with chunking on it equalises the length contribution of every window before the windows are combined, destroying magnitude before the vector reaches the store. The window bank makes it exactly reproducible, because you reconstruct the window mean first and normalise second, which is the code's own order.

### The dtype, and why not the one that was proposed

Store the window **mean** in fp16, not the window sum in bfloat16. The design that proposed the bank chose bfloat16 written as raw uint16 with the true dtype recorded in a manifest, arguing that summing 128 residues expands the range by seven exponent steps and fp16 would clip. It would, but the range expansion is created by the sum, and the counts are being stored anyway, so the mean and the sum carry identical information. The mean sits in the range the forward pass already produces, so fp16 applies at the same two bytes with a unit roundoff of 4.9 times ten to the minus four against bfloat16's 3.9 times ten to the minus three, eight times finer. And a plain fp16 `.npy` is self-describing, whereas a uint16 file whose real dtype lives in a sidecar returns plausible garbage to any reader that loses the sidecar, which is exactly the shape of artefact this project's own audit called a capability that dies with the disk.

### The storage arithmetic

The corpus length distribution is measured, at `agent-farm/plans/representation-science/PLAN.md`: 527,858 sequences, mean 399, median 318, p90 736, p95 969, p99 1831. That is the number to use, not the 597 that one design back-derived from the 646 gigabyte residue-storage figure. Over 528,294 sequences at a mean of 399 the corpus holds 210,789,306 residues. At 128 residues per block that is 1,646,791 full blocks plus one half-full trailing block per sequence, 264,147 of them, giving 1,910,938 blocks and an effective compression of 210,789,306 over 1,910,938, that is 110.3 to one.

The eight model dimensions sum to 640 plus 768 plus 1024 plus 1024 plus 1152 plus 1280 plus 1536 plus 2560, that is 9,984. One statistic at one layer rung across all eight models therefore costs 1,910,938 times 9,984 times 2 bytes, that is 38.16 gigabytes. The bank is four rungs of block mean, two rungs of block unit-mean, and one rung of block maximum, that is 4 plus 2 plus 1 equals 7 statistic-rungs, 267.1 gigabytes; plus one int16 residue count per block shared across all models, 3.8 megabytes; plus an fp32 L2 norm per block per rung per model, 1,910,938 times 4 times 8 times 4 bytes, that is 245 megabytes; plus a per-sequence sidecar carrying accession, sequence identifier, length, block offset, taxonomy identifier and a precomputed lineage tuple so no stratifier ever calls `ete3` at report time, at roughly 120 bytes per sequence, 63 megabytes. **The bank is 267.4 gigabytes against 568 free.**

Retaining every layer instead of four rungs would cost 1,910,938 times the sum over models of layers times dimension, which is 354,816, times 2 bytes, that is 1,356 gigabytes, two and a half times the free disk. Residue-level storage remains impossible at 646 gigabytes per model at dimension 1024. The bank is 4.2 per cent of what a single layer of residues for eight models would cost.

Writing it does not touch the wall clock. Per sequence per model the bank costs 3.617 blocks times D times 2 bytes times 7 arrays, that is 50.6 times D bytes, so 64.8 kilobytes at dimension 1280. Over 528,294 sequences that is 34.2 gigabytes for esm2_650m, written across a 9.6 hour pass, which is 987 kilobytes per second of sequential append. Computing the statistics on the card is bandwidth-bound rather than arithmetic-bound and must be written as one fused segmented reduction per rung emitting mean, unit-mean and maximum together, reading the retained stack once. At dimension 1280 with four rungs the stack for a mean-length sequence is 4 times 399 times 1280 times 2 bytes, that is 4.08 megabytes, read a small constant number of times, which at 360 gigabytes per second is eleven microseconds against a per-sequence forward cost of 32.6 milliseconds, under one tenth of one per cent. A literal loop over recipes would instead read 65.5 megabytes per recipe per batch and cost 130 milliseconds, which is the arithmetic that killed the on-the-fly recipe fan.

### The choice between the two substrates, and the reason

Two designs disagreed here. One retained the mergeable bank; the other retained nothing and evaluated a declared fan of recipes on the GPU while the residue tensor was still resident, arguing that the marginal recipe costs 1.6 per cent of a job. I take the bank, for three reasons.

The 1.6 per cent figure is the fixed non-forward remainder of one job, and multiplying it by hundreds of recipes gives 12.5 times the job, not 1.6 per cent; recovering the economy requires fusing the reductions, which puts new, untested, bandwidth-sensitive code on the critical path of a 204 hour pass. The bank moves that same arithmetic off the GPU and off the critical path entirely, where a bug costs a re-reduction rather than a re-pass. Second, the fan's recipe list is a one-way door: any recipe not declared at dispatch costs a full corpus pass for that model, and this project's own record is that the axes change, which is why this task exists. Third, the bank is regenerable by a registered operation and therefore satisfies the storage invariant, while being cheap enough that it never has to be regenerated.

### What retaining this forecloses

The bank forecloses any chunk geometry that is not a multiple of 128, corpus-wide and permanently, including every sub-128 window. It forecloses `normalize_residues` combined with multi-rung layer aggregation, because the flag is applied after aggregation and the maximum does not commute with the layer mean, so the two-rung and four-rung unit-means are not reconstructible from per-rung ones. It forecloses maximum pooling at any rung other than the one where the maxima are stored, which means the pooling ablation and the layer ablation are a fractional factorial with the pooling-by-layer interaction aliased, and the thesis must use those words rather than let the grid read as a full factorial. It forecloses residue-level late interaction at corpus scale, and every layer outside the four rungs. Above all it forecloses everything upstream of the residue tensor: `max_length`, the tokeniser, the model set. Those are pre-forward on every path, including the raw string slice in the ESM3c backend, and no storage recovers a residue the model never saw.

---

## 3. The ablation grid

### Passes

Eight full corpus forward passes, one per model, each emitting the bank. Plus a layer pilot of 20,000 sequences per model retaining all layers, which is 20,000 over 528,294, that is 3.79 per cent of a pass, times eight models, that is 0.303 corpus-equivalents, costing 20,000 times 3.617 blocks times 354,816 times 2 bytes, that is 51.3 gigabytes, transient and deleted the moment the rung probe emits its four rungs. Plus a rehearsal of the whole machinery on esm2_150m over five per cent of the corpus. **Total 8.35 corpus-equivalent passes.**

The pilot sample is not drawn at random and not stratified by length. It is the 6,216 evaluation queries plus their top-50 neighbours under the ankh_base bank that already exists, deduplicated and topped up to 20,000 from the corpus. The reason is that the pilot's only job is to rank layer rungs by retrieval quality, and retrieval quality on a sparse bank is a different regime from retrieval quality on a dense one, so a uniformly sampled 20,000 would rank the rungs under a neighbourhood density that never occurs in the run. The probe evaluates the rung ranking at bank subsets of 5,000, 10,000 and 20,000 and refuses to freeze the ladder unless the ranking has stabilised across them.

`max_length` stays where it is: the trained 1024 context for the ESM family, 2048 for the T5 family. **There is no input tiling and no raised context.** Two designs proposed one or the other, one arguing that "whole-protein coverage costs under ten per cent" and the other setting the T5 family to 4096 and building a new sliding-window forward path for ESM. The corrected length arithmetic kills both: the corpus mean is 399 with p99 at 1831, proteins above 2048 residues number 127 in the evaluation set and roughly 14 per panel, and the parity test that one design called non-negotiable, byte-identical agreement between the first tile and a truncated forward pass, cannot pass, because fp16 matrix multiplication is not associative and the library selects kernels by batch shape. Spending the novelty budget of the campaign on a regime that cannot carry an inferential claim in any panel is the definition of building the ruler before the thing it measures.

### Configurations

From the bank, per model, the post-forward cross is as follows. Layer setting has six levels, the four single rungs plus the mean of four plus the concatenation of two. `normalize_residues` crosses only the four single-rung settings, giving ten layer settings. Pooling contributes the mean everywhere and the maximum and mean-max only at the rung where maxima are stored, giving fourteen. Grouping has four levels, whole plus 512 with overlap 0, 512 with overlap 256, and 1024 with overlap 256. The per-window `normalize` is live only on the three chunked groupings, and the collapse choice, one row per window against a mean over windows, is likewise chunked-only, giving one plus three times two times two, that is thirteen grouping-and-collapse cells. Fourteen times thirteen is **182 configurations per model**.

The full 182 run on three models, chosen to span the two positional mechanisms and the anisotropy extremes: esm2_650m (rotary, dimension 1280, the measured cost anchor), ankh_base (relative position bias, dimension 768, the only non-monotone K curve in the eight and the only model with a chunked configuration already in existence), and prot_t5 (relative position bias, dimension 1024, best of the five full-cohort models in six of the nine panels at K equals 3). The remaining five models run at the declared reference recipe only, and all eight run again at the per-model champion once the screen resolves. That is 546 plus 8 plus 8, of which six duplicate screen entries, giving **556 distinct configurations**.

The ratio to defend at a viva: 556 configurations from 8.35 corpus-equivalent passes, a factor of 66.6. In wall clock, the three screened models cost 9.6, 18.9 and 33.8 desktop hours per pass respectively, that is 62.3 hours per configuration, so 182 configurations by the naive route would cost 11,346 hours, against 204. A factor of 56, or 475 days against 8.5.

The prior-knowledge exclusion list is a required, non-defaulted argument of the evaluation operation, and the stratified writer raises if a prior-knowledge row is emitted from a run where it was absent. That flag is the project's own most consequential recorded error and it does not get a default.

K is not a configuration. Retrieval stores the top 30 donors per query per aspect, at 6,216 times 3 times 30 times 12 bytes, that is 6.71 megabytes per configuration, 5.83 gigabytes over the grid, and every K from 1 to 30 is a truncation of that list. Scoring at four K values runs on the sixteen model-axis configurations only, at 120 seconds each, 1.6 hours.

The scoring preset is a declared factor, not a silent default. The brief's own measured fact is that models separate cleanly under a preset that isolates the embedding and do not separate under a mean over seven presets, which means an undeclared preset makes every cell uninterpretable. The sixteen model-axis configurations are scored under both the isolating preset, where the emitted score is the cosine itself, and a rank-valued deployed preset, where the score is the fraction of the K neighbours voting and is invariant to cosine scale. The representation claim is then stated as surviving or not surviving the move from a cosine-valued score to a rank-valued one. Cost, sixteen times two times 120 seconds, that is 32 minutes.

### Wall clock

The measured anchor is esm2_650m over 528,294 sequences in 4 hours 47 minutes, 4.79 hours, across both machines, with a desktop share of 49.7 per cent, so 9.64 hours desktop-only; and ankh_base at 9.41 hours, a ratio of 1.96. Scaling the remaining six by parameter count and layer depth gives esm2_150m at 0.25, esmc_600m at 1.10, prot_t5 and prostt5 at 3.5, ankh_large at 4.0 and esm2_3b at 5.0, that is 1.2, 5.3, 16.8, 16.8, 19.2 and 24.0 both-machine hours. The eight-model total is 97.5 both-machine hours. Since this desktop holds the graphics card and the laptop is the server, the planning figure is desktop-only: 97.5 over 0.497, that is 196.2 hours, plus the pilot at 3.7 both-machine hours, that is 7.4 desktop hours, plus the rehearsal, **204 GPU hours, 8.5 days**.

Evaluation is CPU. Per configuration the reduction reads roughly six gigabytes of bank and writes a 1.2 gigabyte reference matrix, sixty seconds; brute-force cosine retrieval is 2 times 6,216 times 487,237 times 1280 flops, that is 7.755 teraflops, which at 200 gigaflops of effective single-precision matrix multiply on this six-core part is 38.8 seconds, budgeted at ninety with top-K and transfer; and cafaeval is 120 seconds after the sparse-kernel fix that took it from 23 minutes to about 2. Two hundred and seventy seconds per configuration times 556 is 150,120 seconds, **41.7 hours**, plus 1.6 for the K sweep and 0.5 for the preset factor, **44 hours**.

The homology sweep is 6,216 times 487,237 alignments, that is 3,028,665,192, at a measured 8,692 alignments per second per core using the striped statistics kernel with a query profile built once and no traceback, that is 348,443 core-seconds or **96.8 core-hours**, plus a null calibration of 200 shuffled real bank sequences at 200 times 487,237 over 8,692, that is **3.1 core-hours**. On four of the six physical cores, leaving two to feed the GPU worker, that is 25 hours of wall clock, entirely overlapped with the forward passes.

**The campaign is 204 GPU hours plus 44 CPU hours with 25 hours of alignment hidden inside, that is 248 hours, 10.3 days.** If the laptop carries the 50.3 per cent share it carried in the recorded esm2_650m pass, it is 145 hours, 6.1 days. Everything is sharded so that no message exceeds fifteen minutes, which for the alignment sweep is 8,692 times 900 alignments, that is 7.82 million, that is sixteen queries against the full bank, giving 389 shards. A reboot of this machine costs fifteen minutes and no work.

---

## 4. The order of work, and what unblocks the most

**PR 0, the census, read-only, one afternoon.** Modelled on `audit_evaluation_frames`, which already exists as a registered operation for exactly this purpose. It measures sigma_d per contrast class by paired bootstrap over the two banks that already exist, which settles the floor that governs every reporting decision; the exact per-panel populations, so the table in section 1 stops resting on an artefact whose cohort may be narrower than the evaluation set; the corpus length distribution and the resulting block count, so the storage figure in section 2 stops resting on a plan file; taxonomy coverage and lineage resolution rate, with the authority to cancel the taxonomy axis; the string-against-integer taxonomy seam; and the cohort mismatch in the existing K rows, so that the K claim is restated correctly before it appears anywhere. Nothing downstream is safe to specify without it and it costs no GPU.

**PR 1, the retrieval and scoring seam. This unblocks the most and it should be built first after the census.** Today `evaluate_recipe_set` would go from vectors to a scalar in one operation, and the scalar is all that survives. Split it. `retrieve_configuration` reads a reference matrix, runs the aspect-partitioned nearest-neighbour search, and persists the top 30 donors per query per aspect as a registered artefact. `score_neighbour_sets` reads those lists, transfers terms, and persists the per-protein, per-threshold confusion curves before they are summed away: the cafaeval kernel already builds the per-protein arrays and collapses them one line later, and stopping one line earlier costs 6,216 times 99 times three arrays times four bytes, that is 7.38 megabytes per aspect, 22.1 per configuration, **19.3 gigabytes over the whole grid**. From those curves, for any subset of proteins, at any threshold, under any normalisation, you recover Fmax, weighted Fmax, the semantic distance, the per-protein oracle threshold, the calibration gap, the bootstrap distribution and the paired delta against any other configuration, because protein indices are shared and the pairing is exact by construction. That single artefact retires, at a cost of 0.5 per cent of the bank, every one of the following one-way doors that the designs listed as permanent: re-cutting a band edge, adding a fifth axis, sweeping K, choosing between micro and macro averaging, choosing a threshold policy, and recovering an interaction cell that the marginal report does not print. It also absorbs `scripts/bootstrap_fmax_ci.py` into the platform, which matters because that script currently reaches the object store by hand and its own test imports it by file path.

Two guards in the same pull request, because both fail silently rather than loudly. The evaluator asserts on every call that the prediction and ground-truth matrices share row count and identifier order, since the masked-cohort trick depends on an internal invariant of a pinned fork rather than a contract. And the bootstrap resamples proteins, not protein-aspect units, with a no-knowledge protein's units moving together.

**PR 2, the coordinate table and the reportable frame.** One table holding one row per protein with the full axis vector and the continuous values behind it, keyed on the protein alone for length and taxonomy and on the protein and the bank for the homology coordinates, so that recalibrating the homology floor does not invalidate the length and taxonomy rows. A content-addressed scoring frame whose digest covers the non-default subset of a versioned field registry, so that adding a field later with a declared default leaves every existing digest bit-identical, and whose homology bank identifier lives on the axis run rather than on the frame, for the same reason. And the floor is applied at report time and stamped on the output, never resolved upstream and frozen into the artefact. That last point is a correction: the first design proposed a merge ladder resolved from census counts before any arm is scored, but the floor depends on sigma_d, sigma_d cannot be measured before two arms are scored, and the ladder was to be frozen before that. The dependency is circular. Levels are frozen raw, at their full count; the floor is a report-time parameter with its value printed beside every table.

`strata.py` changes while it is still uncalled and therefore free to change: `TRUNCATED` is renamed, because whether a protein is truncated depends on the arm's configuration and a model-independent axis must not carry an arm-dependent name; the second homology distance and the reach level are added; `homology_band_for` gains a single point of unit conversion with a test, because `_parse_alignment` returns a fraction in the unit interval while the band function raises outside zero to one hundred, and 0.87 is a legal percentage, so the failure mode is a silent collapse rather than an exception; and `all_strata()` stops returning a Cartesian product and returns a declared reportable frame, so that `UnstratifiedResultError` means something instead of guarding a grid nobody reports.

**PR 3, the null calibration and the alignment sweep.** The calibration runs first and gates the sweep on its exit status, not on a narrated check. Retention is annotation-agnostic: keyed on the query sequence hash, the bank hash and the aligner parameter hash, storing every donor clearing the expectation threshold up to a cap of 2,000 per query with an overflow flag and the identity at the cap, at roughly 100 bytes per row and at most 12.4 million rows, that is 1.24 gigabytes. The evidence mask, the aspect restriction and the temporal cut are then group-by clauses, not rescans. This is a correction to two designs, both of which proposed six running heaps keyed on aspect and evidence class at one frozen annotation set. Sequence identity is a function of two sequences and knows nothing about an annotation set; keying the retention on the mask makes every release and every donor-policy change cost the full 96.8 core-hours again, and this campaign is a per-release series.

**PR 4, the emitter, leaf first.** `protea-backends` gains a call returning the selected layers un-aggregated, tokenising with `max_length`, which the existing per-residue path does not do. It tags; PROTEA pins the resolved commit with plain `poetry lock`. `EmbeddingConfig` gains a recipe digest with a unique constraint and, in the same migration, a producer column carrying the resolved backends commit, included in the digest input. Without the producer column, the same recipe tuple computed before and after the backends change collapses to one configuration identifier and two vector populations become indistinguishable, and `SequenceEmbedding` carries nothing else that could tell them apart. In the same series, the three reference-pool loaders that join on sequence and configuration with no chunk predicate are fixed, because a chunked configuration silently emits one pool row per window with the accession repeated, inflating K and turning retrieval into an accidental multi-vector search. That fix gates every chunked arm.

**PR 5, the pilot and the rung probe. PR 6, the eight corpus passes. PR 7, the reduction, the screen and the report.** The pilot is deleted the moment the probe emits, and the shard writer refuses to start when free space falls below sixty gigabytes.

Two critical paths run in parallel. The census through the seam through the coordinate table gates the reporting; the recipe digest through the backends pin through the emitter gates the grid. PR 1 gates the first and is the single change that makes every subsequent mistake cheap.

---

## 5. What this plan will not answer

It will not tell you whether a longer context helps. The ESM family stays at its trained 1024 positions and the T5 family at 2048, so the question of whether relative position bias buys anything beyond that is untouched, and the population that would answer it is 127 proteins, roughly 14 per panel, below every floor in this document. That is a deliberate refusal, made because the corpus mean is 399 residues and the ninety-ninth percentile is 1831, and the machinery two designs proposed for it was the most novel and least tested code in either.

It will not tell you anything about a chunk geometry that is not a multiple of 128, or about per-residue normalisation combined with multi-rung layer aggregation, or about maximum pooling at any rung except the one where maxima are stored, or about residue-level late interaction at corpus scale, or about any layer outside the four the pilot chooses. Each of those costs a fresh corpus pass for the model in question.

It will not resolve any representation difference inside the prior-knowledge panels. The measured five-model spread there is 0.0046, 0.0046 and 0.0082 Fmax points against detectable effects of 0.0047, 0.0070 and 0.0080, so the grid will confirm that nothing separates and will not be able to claim that something does. This sentence is the one most exposed to the erratum recorded in the preamble: over all eight models in the same file the prior-knowledge BPO spread is 0.0284, which would resolve, and which of the two figures applies depends on what `n_proteins` counts. Three quarters of the evaluation units live in those panels, which means three quarters of the benchmark is, for the purposes of this thesis claim, inert.

It will not resolve any post-forward knob in the low-knowledge panels. The largest previously measured post-forward effect, chunked against mean under the learned encoder, was at or below 0.008 in absolute Fmax, against detectable effects of 0.0121 to 0.0179 in those six panels. The 556-configuration screen therefore selects a champion, it does not certify a difference, and the thesis will say that in those words. If that survives the run it is itself a result, and a strong one: it locates the representation effect in the backbone rather than in the aggregation.

It will not support a claim about any two axes jointly. Length and reach together, taxonomy and reach together, category and reach together: all of them are recoverable from the frozen coordinate table and the stored curves as a group-by, and none of them is powered. The interaction that a reviewer will ask about, whether the low-knowledge deficit is a property of the query or of the bank, is exactly the one the cohort cannot answer at 6,216 proteins.

It will not touch the two largest measured unexploited levers on record, the text-aligned model as a primary retrieval space and the triple combination at retrieval. Both are outside a sequence-only language-model ablation and neither can ride the window bank, since one of the backends honours only the final normalisation. Naming the cost of that exclusion is more useful than pretending the grid covers it.

And it will not, on its own, make the low-knowledge panels large enough. What it will do is produce the number that fixes them. For every panel and every level of every axis the report prints the count, the detectable effect, and the number of additional targets required to bring that level to 129 proteins. No-knowledge CCO holds 161 and needs no more overall, but its smallest reach level will hold a few dozen and will need one to two hundred more. That list, published before the grid runs and updated after, is the input the campaign's directed case mining has been missing: the axis catalogue is not only a partition of the proteins we happen to have, it is a specification for the proteins we still need.
## A reporting rule the day produced, stated once so it is not rediscovered

Three separate results changed when read on the no-knowledge cells rather than
pooled, and they changed in both directions, which is what makes this a rule
rather than a caveat.

**The self hit dominates the pooled number.** At K equals 3, 73.6 per cent of
predicted rows come from the protein's own earlier annotations, retrieved at
distance zero. That contribution is identical for every model, because every
encoder finds the same identical sequence.

**It concentrates toward the top of the ranking.** By rank depth on prot_t5:
96.1 per cent of rows in the top two, 93.9 in ranks three and four, 89.6 in five
to seven, 83.1 in eight to ten, 68.3 in eleven to thirty, and 59.4 beyond thirty.
So any operation that keeps the highest-scoring predictions keeps a larger share
of the self hit than the population it was drawn from.

The three results:

| result | pooled reading | on no knowledge |
| --- | --- | --- |
| substrate separation | t between 5 and 10 | the same separation, carried by a quarter of the mass, so the effect within what can vary is roughly four times larger |
| `max_terms` cap | +0.0102 on prot_t5, 7 of 7 improve | +0.0024, six of seven improve, three quarters of the gain was concentration on the self hit |
| K equals 3 | wins on score | wins on score, and the margin is not a retrieval claim because the self hit falls from 73.6 to 17.4 per cent across K |

A fourth arrived after the rule was written and it is the sharpest, because it
survives the leak being removed entirely rather than merely being read around.
Bounding K survives leak removal in eight of eight models and gets SHARPER on no
knowledge, which is the opposite of what the cap does.

The mechanism separates them cleanly and is worth stating because it predicts
which other axes will behave which way. **K bounds donors. `max_terms` bounds
terms.** The self hit is one donor sitting at rank one, so lowering K keeps it
while discarding twenty-seven noisier neighbours: its share of the vote rises but
its absolute contribution does not move, and the gain is the noise leaving. The
cap works on the ranked terms instead, where the self hit's own terms sit at the
top, so tightening it retains them and discards everything else: the gain is the
leak staying.

So an axis that bounds WHO donates is measuring retrieval, and an axis that
bounds WHAT SURVIVES a ranking is measuring how much of the answer was already
present. That is a question to ask of every remaining axis before it is run, and
it costs nothing to ask.

The substrate result got stronger, the K result got sharper, and the cap result
got weaker. A rule that only ever deflated findings would be a scepticism habit;
one that moves in both directions is measuring something.

**So the rule is that no ablation axis is read on a pooled mean.** Every axis
reports on no knowledge, or reports the self-hit share of the surviving rows
beside its number, and preferably both. An axis that improves the pooled score
and not the no-knowledge score has improved the retrieval of answers the method
already had.

This is the same finding as the campaign's own nine-cell regime map arriving from
a different direction, and it is why that map is a map of regimes rather than a
stratification for tidiness.
