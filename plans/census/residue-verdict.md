# Slice: residue-verdict

Auditor slice key: `residue-verdict`. Started 2026-09-02.

## The claim under audit

"Residue-level sparsification WINS once the map is trained for per-residue use:
+0.0251 over the deployed champion, held out, with the advantage growing with k
(+0.0114 at k=1, +0.0289 at k=25)."

Cited to the project author as the single reason a whole research direction stays open.

Predecessor trail (killed run): `/home/xaxi/Thesis2/storage/coordination/rescued/wf_2b4f3e5f-f3b-a18c645b3cd84777a.md`

Status: IN PROGRESS. Findings appended below as established.

---
## F1. The script that names the mechanism: `73_architecture_on_the_task.py`
verdict: CONFIRMED (script found and read)
path: `/home/xaxi/Thesis2/storage/encoder-study/scripts/73_architecture_on_the_task.py`

Its docstring, verbatim (lines 1-8):

> "The claim the whole experiment rests on is that selecting atoms per residue and then
> pooling beats pooling first and then selecting, because the two do not commute. Every
> measurement of that was neighbour purity, and purity has since been shown not to be
> comparable across architectures: it divides by the neighbour's own annotation count, so it
> rewards retrieving sparsely annotated proteins.
> So the comparison is made again on maximum F-measure, with a pooled control fitted on the
> SAME proteins, with the SAME objective, the SAME budget and the SAME seed."

The mechanism named is the **purity denominator**: purity is not comparable across
architectures because its denominator is the retrieved neighbour's own annotation count.
The author of script 73 already knew the +0.0251 might be an artefact and rebuilt the
comparison on the task.

note: script 73 is dated 2026-08-20 02:19, ONE DAY after the 2026-08-19 memory that carries
the +0.0251 claim. The memory file was never amended with 73's result. It carries only a
"SUPERSEDED BY INSTRUMENT, 2026-08-26" block pointing at the architecture null, which is a
DIFFERENT (later, larger-bank) experiment. **73 is the direct, same-day, same-study
refutation and it is not cited in the memory at all.**

---

## F2. The same architecture contrast, measured on the TASK: 0 of 3, mean NEGATIVE
verdict: CONTRADICTED (the claim does not transfer to Fmax)
first number (the claim): purity `residue-k32` 0.2535, +0.0251 vs deployed champion,
  +0.0323 vs the pooled control -- `/home/xaxi/Thesis2/storage/encoder-study/RESULTS.md:33`
second number (INDEPENDENT, same study, same author, next day, on Fmax):
  `/home/xaxi/Thesis2/storage/encoder-study/artifacts/architecture_on_task.json`
  and `.../architecture_on_task.log`

```
                 pooled ctrl   per-residue   deployed   per-residue MINUS pooled   95% CI          separates?
MFO (F)            0.6357        0.6372       0.6423        +0.0015          [-0.0116, +0.0153]   no
BPO (P)            0.4469        0.4388       0.4377        -0.0081          [-0.0208, +0.0027]   no
CCO (C)            0.6845        0.6861       0.6796        +0.0015          [-0.0157, +0.0159]   no
                                                     mean:  -0.0017    wins 2/3, separates 0/3
```

Derived by me from the same JSON, per-residue MINUS deployed champion (the exact contrast
the +0.0251 headline is about): F -0.0051, P +0.0012, C +0.0065; mean **+0.0009**, i.e.
one fifth of the reproducibility floor of 0.0013 and two orders below +0.0251.

date of evidence: 2026-08-20 02:19 -> window: **pre-wipe** (before 2026-08-27)
frame: Fmax over a threshold grid `np.arange(0.01,1.0,0.01)`, similarity-weighted term
  vote over KNN=10, GO closures propagated is_a+part_of, aspect-split F/P/C, paired
  bootstrap 2000 draws, seed 42, dict 2048, K_SEQ 128, K_RES 4.
population: the **served no-knowledge cell, n=649**, prior-knowledge exclusion applied,
  bank = the 60,000-protein pool (`pool60k_last.npy`), and no arm fitted on any protein of
  the category it is judged on (training set 3,761 = split train minus NK).
platform gap: no registered operation produces either the purity screen or this Fmax
  comparison. Both are loose scripts under `storage/encoder-study/scripts/`, which is
  exactly the failure `feedback_integrate_in_platform_not_adhoc_2026_06_20` names. To be
  reborn writing to the database this needs an evaluation operation that scores an
  arbitrary encoder arm on a declared cell and persists an `evaluation_result`.
note: the purity screen and the task measurement are on DIFFERENT populations (2,646 LAFA
  probe proteins vs the 649 NK cell) and different banks (probe-shaped vs 60k). So this is
  not yet a clean sign flip on one population -- see F3/F4, where I test that.
## F3. WHAT THE +0.0251 METRIC ACTUALLY IS -- and it is not what the memory says
verdict: CONTRADICTED (the memory's own description of the metric is wrong)
receipt: `/home/xaxi/Thesis2/worktrees/lab-bundle/src/protea_reranker_lab/functional_proxy.py`
  functions `purity_per_protein` (lines ~157-176) and `jaccard` (line ~44), called from
  `/home/xaxi/Thesis2/storage/encoder-study/scripts/03_score.py:36`.

Two things a reader must not miss.

**(a) The metric is JACCARD, not the neighbour-normalised share.**
```python
def jaccard(a, b):
    union = len(a | b)
    return len(a & b) / union if union else 0.0
```
`project_purity_denominator_artifact_2026_08_19.md` describes purity as "the share of THAT
NEIGHBOUR's terms which the query also has", i.e. |q n| / |n|. The code computes
|q n| / |q u n|. Directionally the same complaint survives (the denominator still grows
with the neighbour's annotation count, so a sparsely annotated neighbour scores higher at a
fixed intersection), but **the memory's account of the formula is not the formula in the
code.** Anyone re-deriving the artefact from the memory alone would derive the wrong one.

**(b) The neighbours are NOT donors. It is self-retrieval inside the evaluation set.**
```python
    sim = unit @ unit.T          # codes of the 2,646 EVALUATION proteins against each other
    np.fill_diagonal(sim, -np.inf)
    top = np.argpartition(-sim, k, axis=1)[:, :k]
```
There is no bank. The "ten nearest neighbours" are ten OTHER held-out evaluation proteins.
kNN transfer in production retrieves from a 60k (or 85,982) donor bank. So the +0.0251 is
not measured on the retrieval problem the system solves; it is measured on the internal
geometry of a 2,646-protein set. This is the strongest possible form of the "probe-shaped
bank inflates a retrieval difference" caveat the memory itself records, and it is worse
than the memory admits: it is not a probe-shaped bank, it is NO bank.

frame: k=10, GO closures of release 227 propagated is_a+part_of, Jaccard, self-retrieval
  inside the eval set, paired bootstrap 4000 draws seed 42. No thresholds, no aspects, no
  precision/recall, no propagation of predictions, no NK/LK/PK split.
population: 2,646 LAFA probe proteins, unstratified, aspect-pooled (**a single number over
  what the project's own norm says are nine populations**).

---

## F4. THE DECOMPOSITION. The entire +0.0251 is the denominator. Recomputed from raw codes.
verdict: CONFIRMED (the artefact is real, measured by me, not quoted)
first number: purity `residue-k32` minus `champion-frozen` = **+0.0251**, RESULTS.md:33
second number (INDEPENDENT, my own recomputation from `artifacts/eval_codes.npz` +
  `artifacts/gold_lafa.pkl`, k=10, self-retrieval, 4000-draw paired bootstrap seed 42):

```
arm                purity   median   TRUE HITS/neigh   TERMS/neigh   UNION(denominator)
residue-k32        0.2535   0.2323        40.372          111.491         187.731
residue-k4         0.2570   0.2360        40.992          112.027         187.647
champion-frozen    0.2284   0.2106        40.160          130.876         207.328
control-pooled     0.2212   0.2013        37.724          119.900         198.787
residue-dense      0.2284   0.2111        39.631          127.171         204.152
residue-k128       0.2465   0.2233        40.046          114.511         191.076
(query closures: mean 116.6 terms, median 82)
```

`residue-k32` vs the deployed champion, paired, per protein:

```
purity            +0.0251  [+0.0229, +0.0273]   SEPARATES   <- the headline, reproduced exactly
true hits/neigh   +0.2119  [-0.1238, +0.5440]   DOES NOT SEPARATE   <- the numerator
terms/neigh      -19.3849  [-21.1476,-17.5800]  SEPARATES   <- 14.8% FEWER terms per donor
union            -19.5968  [-21.2104,-17.9532]  SEPARATES   <- the Jaccard denominator
```

**The numerator does not move. The denominator moves by 14.8 per cent. That is the whole
effect.** Arithmetic counterfactual on the ratio of means (0.21505 vs 0.19370, gap 0.02135):
- residue-k32's numerator over the CHAMPION's denominator -> 0.19472, gain **+0.0010** (5%)
- the champion's numerator over RESIDUE-K32's denominator -> 0.21392, gain **+0.0202** (95%)

**95 per cent of the purity gain is the denominator alone.**

note: this is not a subtle effect at the margin. The residue arm's advantage is that it
retrieves donors carrying 19 fewer GO terms each while finding no more correct terms.

---

## F5. THE SIGN FLIP, MEASURED. On what the transfer consumes, the residue arm LOSES.
verdict: CONFIRMED (this is the decisive claim, and it holds)
what I did: on the SAME 2,646 proteins, the SAME k=10 self-retrieval, the SAME codes, I
replaced the screen statistic with the two quantities kNN transfer actually consumes -- the
candidate term pool (the union of the 10 neighbours' closures, which is everything the
transfer can possibly emit) and the TRUE terms inside it (the recall ceiling of the transfer,
before any threshold or weighting). Script:
`/tmp/claude-1000/-home-xaxi-Thesis2/2530babf-865d-43bb-8976-f9e0b85ea3c8/scratchpad/transfer.py`

```
arm                candidate terms   TRUE terms reachable   recall ceiling   precision ceiling
residue-k32             533.63              85.09               0.7770            0.1734
residue-k4              528.82              85.33               0.7790            0.1754
champion-frozen         657.16              86.84               0.7920            0.1428
control-pooled          618.00              85.10               0.7783            0.1453
residue-k128            558.37              85.59               0.7803            0.1656
```

`residue-k32` minus `champion-frozen`, paired, 4000 draws:

```
screen  purity                +0.0251  [+0.0229, +0.0273]   SEPARATES   POSITIVE
task    candidate terms     -123.5295  [-132.69, -114.30]   SEPARATES   NEGATIVE
task    TRUE terms reachable  -1.7457  [-2.2827, -1.2018]   SEPARATES   NEGATIVE
task    RECALL CEILING        -0.0150  [-0.0186, -0.0114]   SEPARATES   NEGATIVE
        precision ceiling     +0.0306  [+0.0280, +0.0331]   SEPARATES   POSITIVE
```

**The sign flips and both sides separate.** The quantity is the recall ceiling of the
kNN transfer: the share of the query's true GO terms that are present at all in the ten
retrieved neighbours. The deployed champion puts 79.20 per cent of the answer within reach;
`residue-k32` puts 77.70 per cent within reach. The residue arm has strictly LESS to
transfer, and it cannot get it back downstream because it is a ceiling.

**And the loss is not noise.** -0.0150 is 11.5x the study's own stated reproducibility floor
of 0.0013 and 1.6x the ~0.0093 max-over-null-arms floor. The winner on the screen is a
separating LOSER on the ceiling of the task.

Why purity was fooled: purity gain +0.0251 and precision-ceiling gain +0.0306 are nearly the
same number. **Purity is a precision-flavoured statistic with no recall term at all**, and
the residue arm buys its precision by retrieving thin donors. Fmax has a recall term, which
is why script 73 found nothing on Fmax (F5 explains F2).

note: `control-pooled` is the clean read on the architecture. Against the champion its
recall ceiling is -0.0137 and residue-k32's is -0.0150: **the residue architecture does not
even improve the ceiling over its own pooled control** (-0.0013, at the floor). What the
residue architecture reliably does is shrink the candidate pool by 123 terms.

---

## F6. The k-sweep (+0.0114 at k=1 ... +0.0289 at k=25): NO RECEIPT EXISTS, but it reproduces
verdict: CONFIRMED as arithmetic / the ARGUMENT built on it is CONTRADICTED

negative check (what I searched, all of it): `grep -rn "0\.0114|0\.0289"` over
`storage/encoder-study/` (all .md/.json/.py/.log/.out including every artifact log),
`agent-farm/plans/`, `thesis/`, `repositories/`, and the memory store. The five-point sweep
appears in exactly ONE place in the whole project:
`/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/project_residue_order_wins_when_trained_2026_08_19.md`.
There is no script, no artifact, no log. `artifacts/k_sweep.json` is a DIFFERENT sweep (the
transfer's neighbour count per cell on Fmax, from `28_k_sweep.py`) and does not contain it.
**A load-bearing robustness claim with no receipt.**

I recomputed it from the raw codes
(`/tmp/claude-1000/-home-xaxi-Thesis2/2530babf-865d-43bb-8976-f9e0b85ea3c8/scratchpad/ksweep.py`):

```
 k   residue-k32  champion  control   purity k32-champ           RECALL CEILING k32-champ
 1     0.3770      0.3656    0.3660   +0.0114 [+0.0076,+0.0152] S   +0.0007 [-0.0043,+0.0057] ns
 5     0.2803      0.2603    0.2561   +0.0200 [+0.0175,+0.0225] S   -0.0107 [-0.0148,-0.0068] S
10     0.2535      0.2284    0.2212   +0.0251 [+0.0229,+0.0273] S   -0.0150 [-0.0186,-0.0114] S
25     0.2244      0.1955    0.1866   +0.0289 [+0.0270,+0.0307] S   -0.0117 [-0.0147,-0.0087] S
50     0.2048      0.1759    0.1659   +0.0289 [+0.0273,+0.0306] S   -0.0094 [-0.0120,-0.0070] S
```

All five purity points match the memory **exactly**. So the sweep is honest arithmetic.

**But the argument the memory draws from it is refuted by its own sweep.** The memory says:
"the advantage GROWS with it ... kNN transfer does not use one neighbour, so the gain lands
where it is used." The recall-ceiling column shows the opposite: at k=1, where the screen
advantage is smallest, the transfer ceiling is NEUTRAL (+0.0007, does not separate); at every
k the transfer actually uses, the screen advantage grows AND the ceiling loss appears and
separates. **The gain lands exactly where the loss lands, and they are the same effect seen
from two sides.** Growth with k is the signature of the artefact, not of the mechanism:
adding neighbours adds more thin donors, which raises the ratio and lowers the ceiling
together.

note: absolute purity falls from 0.3770 to 0.2048 as k goes 1 -> 50, so the "+0.0289 at k=50"
is a larger fraction of a smaller number. In relative terms the advantage goes 3.1% -> 16.4%,
which is what a denominator effect does, not what a retrieval-quality effect does.

---

## F7. The population under the headline: 82.5 per cent prior knowledge, 140 NK proteins
verdict: CONFIRMED (stratification the scoring script never did; `03_score.py` stratifies by
LENGTH only, never by knowledge category, in direct violation of the project's standing norm)
receipt: my recomputation joining `eval_codes.npz` accessions to
`artifacts/categories_227_230.pkl`
(`/tmp/claude-1000/-home-xaxi-Thesis2/2530babf-865d-43bb-8976-f9e0b85ea3c8/scratchpad/cat2.py`)

```
cell     n    query terms   champ pur   k32 pur   d PURITY                    d RECALL CEILING           d TERMS/neigh
NK     140       36.8        0.2133     0.2413   +0.0280 [+0.0188,+0.0382] S  -0.0102 [-0.0224,+0.0014] ns   -20.19
LK     324       60.4        0.2425     0.2702   +0.0277 [+0.0218,+0.0337] S  -0.0094 [-0.0197,+0.0006] ns   -26.47
PK    2182      130.1        0.2272     0.2518   +0.0246 [+0.0221,+0.0270] S  -0.0162 [-0.0202,-0.0120] S    -18.28
ALL   2646      116.6        0.2284     0.2535   +0.0251 [+0.0229,+0.0273] S  -0.0150 [-0.0186,-0.0114] S
```

- **2,182 of 2,646 (82.5%) are prior-knowledge.** The headline +0.0251 is 82.5 per cent a
  PK number, on a project whose own norm records that the served population is the NK cell.
- The served cell is **n=140**. The whole reason a research direction stays open rests, on
  the served population, on 140 proteins.
- The purity gain is **FLAT across the three categories** (+0.0280 / +0.0277 / +0.0246,
  intervals overlapping). A flat effect is the signature of a metric property, not of a
  functional mechanism, since NK/LK/PK differ by a factor of 3.5 in annotation depth
  (36.8 vs 130.1 query terms) and the effect does not care.
- The recall-ceiling loss is negative in all three cells; it only separates in PK because
  that is where the n is.

---

## F8. NEW DEFECT, not previously recorded: the "same objective, same budget" control is neither
verdict: CONTRADICTED (the declared control is false in the code and in the saved metadata)

**(a) The budget is not the same. 3,000 steps against 2,000.**
`/home/xaxi/Thesis2/storage/encoder-study/scripts/02_fit_all.py:42`
```python
TRAIN_RESIDUES, BATCH, RES_STEPS, POOL_STEPS = 256, 384, 3000, 2000
```
and line 111: `steps = RES_STEPS if residue_level else POOL_STEPS`.
The saved maps agree: `map_residue-k32.npz` steps=3000, `map_control-pooled.npz` steps=2000.
Every residue arm gets 50 per cent more optimisation than the control it is scored against.

Yet `RESULTS.md:36` says of `control-pooled`: "a pooled map on the same 3,964 proteins,
same objective, **same budget**", and `03_score.py`'s docstring says "a pooled map fitted on
the same proteins with the same objective and budget". **The declaration and the code
disagree, and no one checked.**

**(b) The objective is not the same either.** The residue arms sparsify INSIDE the loss
(`sparsify(Xres[rows] @ W + b, keep, weighting)`, 02_fit_all.py:118) and resample 4,096
pairs every step (~12.3M pair draws). The pooled control trains a fully dense projection
with no selection anywhere in the loss (`cos_loss(Xpool @ W + b, TI, TJ, Y)`, line 127)
against ONE fixed set of ~40,000 pairs reused for all 2,000 steps. Two different estimators,
two different objectives.

**(c) THE EXACT-PATH CONTROL, and it fails.** The project's own norm
(`feedback_exact_path_control_for_transforms_2026_08_20`) says: run the transform at a
setting where it MUST be the identity and require the baseline back. That setting exists in
this study and is already scored. `residue-dense` is the residue path with the per-residue
selection switched OFF (keep=None). For a LINEAR map, projecting each residue and then
averaging is algebraically the same function as averaging and then projecting:
mean_r(r W + b) = (mean_r r) W + b. I verified it numerically: running the POOLED path with
the `residue-dense` map reproduces the stored `residue-dense` codes at **top-128 support
overlap 0.9205 and code cosine 0.9484** (the residual is only the input L2 rescale
interacting with the bias). My reconstruction pipeline is sound: the same procedure
reproduces the stored `control-pooled` codes at **cosine 1.000000**.

So at the identity setting the two arms are the SAME FUNCTION CLASS trained differently.
And they still differ: `residue-dense` 0.2284 vs `control-pooled` 0.2212 = **+0.0071,
separating**. Their weight matrices have global cosine **0.7335** despite identical seed
and identical initialisation, because one saw 3,000 resampled-pair steps and the other 2,000
fixed-pair steps.

**Consequence.** The memory reads that +0.0071 as "the training handicap (3,964 proteins and
a plain loss against 60,000 with mined hard negatives)", i.e. as the CHAMPION's training
advantage. That reading is wrong: `residue-dense` was fitted on the same 3,964 proteins with
the same plain loss as the control and gets the same +0.0071. **The +0.0071 is the
step-budget and pair-sampling asymmetry inside the study, not the champion's corpus.** Which
means the "vs control" column that the memory calls the architecture isolation
(`residue-k32` +0.0323) carries at least +0.0071 of pure training bias before any
architecture is measured, and the memory's headline sentence -- "the training handicap is
worth 0.0071 and the architecture is worth 0.0323, mechanism beats a 15x larger training set
by more than fourfold" -- is built on a mislabelled term.

note: script 73 silently FIXED this. Its `control-pooled-clean` runs 979 steps to match
`map_clean3761`'s 979 steps, epochs=100 for both, same seed, same batch. With the budget
actually matched and the metric moved to Fmax, the architecture effect is 0 of 3 and mean
-0.0017 (F2). The two facts are one fact.

---

## F9. THE CLEAN ISOLATION nobody ran: `residue-k32` vs `residue-dense`, training exactly matched
verdict: CONFIRMED -- the sign flip survives in the one frame with no training confound at all
why this pair: both maps are fitted for 3,000 steps, seed 42, the same resampled-pair loss
estimator, the same 3,964 proteins; `map_residue-k32.npz` keep=32, `map_residue-dense.npz`
keep=None. **The only difference between them is the per-residue top-k -- the mechanism the
whole direction is about.** RESULTS.md scores both but never compares them to each other.

```
residue-k32 minus residue-dense, paired, n=2646, 4000 draws
  purity                          +0.0251  [+0.0231, +0.0272]  SEPARATES   <- equals the headline
  true hits per neighbour         +0.7412  [+0.4335, +1.0637]  SEPARATES   <- +1.9% relative, REAL
  terms per neighbour            -15.6799  [-17.3121,-14.0355] SEPARATES   <- -12.0%
  TRUE terms reachable (union)    -0.6833  [-1.2223, -0.1364]  SEPARATES   <- NEGATIVE
  RECALL CEILING                  -0.0083  [-0.0118, -0.0048]  SEPARATES   <- NEGATIVE

residue-k4  vs residue-dense: purity +0.0287 S, recall ceiling -0.0063 S
residue-k128 vs residue-dense: purity +0.0182 S, recall ceiling -0.0050 S
(the screen gain and the ceiling loss move together across k4/k32/k128: 0.0287/0.0251/0.0182
 against -0.0063/-0.0083/-0.0050. The more the screen likes an arm, the less the transfer
 can reach.)

by category, residue-k32 minus residue-dense:
  NK  n= 140  purity +0.0257 S   recall ceiling +0.0028 [-0.0109,+0.0180] ns
  LK  n= 324  purity +0.0307 S   recall ceiling -0.0070 [-0.0160,+0.0022] ns
  PK  n=2182  purity +0.0243 S   recall ceiling -0.0092 [-0.0133,-0.0052] S
```

**And here is the mechanism, which is worth keeping.** Per-neighbour true hits go UP
(+0.7412, separating) while the UNION of true terms across the ten goes DOWN (-0.6833,
separating). Per-residue selection retrieves donors that are individually slightly closer to
the query and much more REDUNDANT WITH EACH OTHER. Each neighbour is a little better; the
ten together cover less. Purity is a per-neighbour average, so it sees only the first half.
kNN transfer consumes the union, so it eats the second half.

note: on the SERVED cell (NK, n=140) the ceiling difference is +0.0028 and does not
separate. So on the population the system exists for, the mechanism is not shown to help and
not shown to hurt. It is not measured; it is underpowered.

---

## F10. The supersession was already written, in the same file, four lines of scroll away
verdict: CONFIRMED (internal inconsistency, already on screen, never propagated to the memory)

`/home/xaxi/Thesis2/storage/encoder-study/RESULTS.md` carries the +0.0251 at **line 33**.
The same file, **line 96**, is headed:

> "## Superseded 2026-08-20: the order does not survive a real bank
>  The table above is a record of what was measured on the study's own screen, and the first
>  two rows do not survive being measured on retrieval against a real donor bank.
>  The screen those rows used ranked candidates from a probe-shaped bank ... Repeated on the
>  full cell of 3,031 queries against 85,982 donors ... Nine aggregate comparisons and
>  twenty-four by identity band, and not one separates."

and at line ~124 it prints the axis table:

```
| axis, twilight band                        | spread |
| choice of base protein language model      | 0.0842 |
| order of selection and pooling             | 0.0006 |
```
> "Two orders of magnitude, one metric, one population. **The axis the study was designed
>  around is inert**; the axis nobody was funding carries the effect."

So the study's own results document declares the axis dead 63 lines below the number that
keeps it alive. The memory
`project_residue_order_wins_when_trained_2026_08_19.md` never records this supersession. It
records only a 2026-08-26 note pointing at the architecture-null memory, and frames even that
as "different populations, not a disagreement".

**Three independent refutations existed before this audit and none reached the claim:**
1. `73_architecture_on_the_task.py`, 2026-08-20 02:19, same study, budget-matched control,
   Fmax on the served cell: 0 of 3, mean -0.0017 (F2).
2. `RESULTS.md:96`, 2026-08-20, the same axis on a real 85,982-donor bank: 0 of 33
   comparisons separate, spread 0.0006 (this finding).
3. `project_architecture_null_survives_stratification_2026_08_20`, the full NK cell:
   0 of 24 bands.
The claim survived all three because each was filed as "a different population".

---

# ANSWERS TO THE SIX QUESTIONS

**1. What mechanism does 73's header name?** The purity denominator: purity "is not
comparable across architectures: it divides by the neighbour's own annotation count, so it
rewards retrieving sparsely annotated proteins." (F1)

**2. What is the denominator, and in what sense is the entire gain the denominator?**
The metric is Jaccard, |q n| / |q u n| (F3a); the denominator is the union, which grows
with the retrieved donor's annotation count. `residue-k32` vs the champion: numerator
(true hits per neighbour) +0.2119, does NOT separate; denominator -19.60, separates.
Counterfactual: swapping in the champion's denominator leaves +0.0010 of the +0.0214
ratio-of-means gap; swapping in residue-k32's denominator alone reproduces +0.0202.
**95 per cent of the gain is the denominator.** (F4)

**3. "Sign flip on the quantity the transfer consumes" -- what quantity, does it flip?**
The quantity is the **recall ceiling of the kNN transfer**: the share of the query's true GO
terms present anywhere in the ten retrieved neighbours, i.e. the most the transfer could
possibly emit correctly. It flips, and both sides separate:
purity **+0.0251** [+0.0229,+0.0273] against recall ceiling **-0.0150** [-0.0186,-0.0114].
It flips in the exact-training-matched frame too (residue-k32 vs residue-dense:
+0.0251 against -0.0083, both separating). **VERIFIED, not refuted.** (F5, F9)

**4. Does +0.0251 survive as a claim about anything?** Yes, but only about the screen, and
the honest residual is narrow and mechanistic:
> *Per-residue top-k selection retrieves donors that are individually slightly more
> functionally similar to the query (true hits per neighbour +0.74, +1.9% relative,
> separating) but substantially more redundant with each other, so the union of terms the
> ten neighbours make available shrinks (-0.68 true terms, -0.0083 recall ceiling, both
> separating). It buys per-neighbour precision and sells set coverage.*
That is a real and interesting property. It is not "residue-level sparsification wins", and
it is not a reason to keep a research direction open on its own, because the thing it sells
is the thing the transfer needs.

**5. Same measurement as the RETRACTED memory?** **DIFFERENT measurement, same research
program, and the retraction is what put the weight on this one.**
`project_sparse_residue_encoder_beats_deployed_on_fmax_2026_08_19` retracted an Fmax
measurement (k=30, 60k donor bank, aspect-split, no PK exclusion). This claim is a purity
measurement (k=10, self-retrieval inside the eval set, no bank, aspect-pooled). They are not
the same number. But the retraction's closing line reads: *"What survives: the RETRIEVAL
improvement, which is large and reproduced on two independent populations. What does not:
that it improves annotation."* **The "retrieval improvement" that the retraction preserved
IS the +0.0251, and it is 95 per cent denominator.** The retraction saved the wrong half.

**6. Metric, population, frame, floors.**
- metric: mean Jaccard to the 10 nearest, self-retrieval inside the eval set. Not Fmax, not
  precision/recall, no threshold grid, no aspect split, no propagation of predictions.
- population: 2,646 LAFA probe proteins; **82.5% prior knowledge, 140 NK** (F7). Aggregate.
- frame: reference release 227, ontology snapshot releases/2025-07-22, is_a + part_of
  closures, k=10, paired bootstrap 4,000 draws seed 42, no PK exclusion (there is nothing to
  exclude: it is not a prediction task). The official campaign frame is 220->230, so a
  227-basis result sits outside the declared cut
  (`project_learned_weights_must_declare_their_cut_2026_08_20`).
- floors: on the SCREEN, +0.0251 is 19x the 0.0013 reproducibility floor and 2.7x the
  ~0.0093 max-over-many-arms floor (RESULTS.md scores **45 arms** in one table), so it is a
  real screen effect. On the TASK it is +0.0009 vs the champion and -0.0017 vs the matched
  control, both BELOW the 0.0013 floor; and the recall-ceiling LOSS of -0.0150 is 11.5x the
  0.0013 floor and 1.6x the 0.0093 floor, so the loss clears both floors that the win fails.

**Dating.** Every artifact under `storage/encoder-study/` for this claim is 2026-08-19 and
2026-08-20 -> **PRE-WIPE**. None of it is among the 93 `evaluation_result` rows created
2026-08-27 to 2026-08-30. As evidence about the current window it does not exist.

**Platform gap.** Not MURO. The residue arm itself was published to the object store and is
dispatchable (`artifacts/95_published_arms.json`: `encoders/exp220-residue-k4-d2048-s128.npz`,
consumer `encode_residue_sparse`, order `select-then-pool`). What has no producer is the
MEASUREMENT: there is no registered operation that scores an arbitrary encoder arm on a
declared category-by-aspect cell against a declared donor bank and writes an
`evaluation_result`. Everything here is loose scripts numbered 01 to 115 under
`storage/encoder-study/scripts/`, a screen defined in a research worktree
(`worktrees/lab-bundle/src/protea_reranker_lab/functional_proxy.py`) that no CI compares
against the platform's scorer. That is the whole reason a metric with a denominator artefact
ran 45 arms and reached the author as a headline.

---

# VERDICT

**The +0.0251 is real arithmetic and a false claim. It is CONTRADICTED as stated and must
not be used to keep the residue-order direction open.**

It measures mean Jaccard to ten neighbours drawn from the evaluation set itself, on a cohort
that is 82.5 per cent prior-knowledge with 140 served-population proteins; 95 per cent of it
is the Jaccard denominator shrinking because per-residue selection retrieves thinly annotated
donors; its numerator does not separate; and on the one quantity kNN transfer actually
consumes -- the recall ceiling of the retrieved set -- the same arm on the same proteins with
the training exactly matched LOSES by -0.0083 to -0.0150, separating, at 6x to 11x the
project's own reproducibility floor. The k-sweep that was offered as robustness reproduces
exactly and refutes the argument built on it: the screen advantage and the ceiling loss both
grow with k, because they are the same effect. Three independent refutations already existed
in this project before this audit -- `73_architecture_on_the_task.py` (0 of 3 on Fmax on the
served cell), `RESULTS.md:96` (0 of 33 against a real 85,982-donor bank, spread 0.0006), and
the stratified architecture null (0 of 24 bands) -- and each was filed as "a different
population" rather than allowed to land.

**What may be kept, stated at the grain it was measured:** per-residue top-k makes each
retrieved donor slightly more functionally similar to the query (+1.9% true hits per
neighbour, separating) while making the ten donors more redundant with each other, so the
set's coverage falls. That is a property of the mechanism worth one sentence in the thesis
and worth zero further GPU hours until someone builds a registered operation that scores an
arm on a declared cell against a real donor bank on Fmax with the exclusion list applied.

**Additional defect found in this audit and not previously recorded** (F8): the study's
pooled control is not budget-matched (2,000 steps against the residue arms' 3,000) and not
objective-matched (dense loss with fixed pairs against sparsified loss with resampled pairs),
though `RESULTS.md:36` and `03_score.py` both declare "same objective, same budget". The
exact-path control proves the cost: at keep=None, where the residue path is algebraically the
pooled path, the two arms still differ by +0.0071, separating. The memory reads that +0.0071
as the champion's larger corpus. It is not; it is the study's own step budget.

---

## F11. ROBUSTNESS ON THE CATEGORY BASIS -- and on the OFFICIAL frame the loss separates in NK
verdict: CONFIRMED, and it strengthens the verdict
(this is the check the killed predecessor was running when it was stopped)

The study's stratification above used `categories_227_230.pkl`. Release 227 is not the
campaign's declared cut; the official frame is **220 -> 230**
(`project_learned_weights_must_declare_their_cut_2026_08_20`,
`project_temporal_discipline_two_cutoffs_2026_08_19`), and `categories_220_230.pkl` exists in
the same artifacts directory. Repeating `residue-k32` minus `champion-frozen` on both bases:

```
basis 227->230           n      purity                          recall ceiling
  NK                   140   +0.0280 [+0.0188,+0.0382] S   -0.0102 [-0.0224,+0.0014] ns
  LK                   324   +0.0277 [+0.0218,+0.0337] S   -0.0094 [-0.0197,+0.0006] ns
  PK                  2182   +0.0246 [+0.0221,+0.0270] S   -0.0162 [-0.0202,-0.0120] S

basis 220->230 (OFFICIAL)
  NK                   190   +0.0297 [+0.0215,+0.0386] S   -0.0131 [-0.0252,-0.0015] SEPARATES
  LK                   349   +0.0255 [+0.0201,+0.0311] S   -0.0065 [-0.0164,+0.0035] ns
  PK                  1938   +0.0247 [+0.0221,+0.0273] S   -0.0169 [-0.0214,-0.0125] S
  (none)               169   +0.0243 [+0.0155,+0.0337] S   -0.0137 [-0.0275,-0.0002] S
```

The purity gain is basis-invariant, as a metric property should be. The recall-ceiling loss
is basis-invariant in sign and magnitude, and on the OFFICIAL 220->230 basis it gains the 50
extra NK proteins it needed and **separates in the no-knowledge cell**: -0.0131
[-0.0252,-0.0015]. **On the served population, in the campaign's own declared frame, the arm
that wins the screen by +0.0297 loses the recall ceiling by -0.0131, and both separate.**

---

# VERDICT (final, one sentence)

**CONTRADICTED. `+0.0251` is a Jaccard-denominator artefact of a screen that retrieves
neighbours from the evaluation set itself: 95 per cent of it is donors carrying 19 fewer GO
terms each, its numerator does not separate, and on the recall ceiling of the actual kNN
transfer the same arm on the same proteins LOSES -- by -0.0083 with training exactly matched,
by -0.0150 against the deployed champion, and by -0.0131 in the no-knowledge cell on the
campaign's official 220->230 basis, all separating and all above the project's floors -- so
it must not be cited as a reason to keep the residue-order direction open.**
