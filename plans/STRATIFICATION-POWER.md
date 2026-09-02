# What a stratum can and cannot answer

Written 2026-09-02 for the clean campaign, on the experimentation side of the
split. It settles one question: given that the campaign stratifies every number
on four axes, what effect can a stratum actually detect, and what follows for
the evaluation standard.

The short answer is that the stratum floor and the effect of interest are two
numbers that were never compared, and they are fifty times apart.

## 1. The measured anchor, and the assumption it carries

The only per-protein paired variability measured anywhere in this project comes
from the first paired interval of the campaign: a BCa bootstrap over proteins,
2000 resamples, information-accretion weighted, on the corrected depth series.
Deriving the per-protein paired standard deviation from each published interval,
as half-width times the square root of the population over 1.96:

| panel | n | half-width | sigma |
|---|---|---|---|
| NK:MFO | 1,129 | 0.0202 | 0.3471 |
| NK:BPO | 1,509 | 0.0112 | 0.2220 |
| NK:CCO | 1,116 | 0.0163 | 0.2778 |
| LK:MFO | 943 | 0.0209 | 0.3267 |
| LK:BPO | 1,214 | 0.0128 | 0.2267 |
| LK:CCO | 821 | 0.0203 | 0.2968 |
| PK:CCO | 3,201 | 0.0084 | 0.2425 |

Mean 0.2771, range 0.2220 to 0.3471. Seven panels, and the two prior-knowledge
panels that could not be computed are absent rather than assumed.

**The assumption, stated because everything below rests on it.** That sigma was
measured on one contrast, neighbourhood depth, and depth is a large-effect
contrast. A different contrast may have a different per-protein spread, and
nothing in the record says whether it does. The between-result standard
deviations available from the floor census (scoring configuration 0.0609,
maximum terms 0.0231, maximum distance 0.0067) are a different object: they are
the spread of a metric across results, not the spread of a paired difference
across proteins, and the two must not be substituted for one another.

So the design rule that falls out first is cheap and compounds: **every declared
comparison publishes the per-protein paired sigma it observed**, so that the
next design can be sized from a measurement rather than from this one borrowed
number.

## 2. The arithmetic nobody had done

Minimum detectable effect at a two-sided five per cent level and eighty per cent
power is 2.802 times sigma over the square root of the population.

| population | detectable effect, mean sigma | at the worst panel's sigma |
|---|---|---|
| 30 | 0.1417 | 0.1776 |
| 50 | 0.1098 | 0.1375 |
| 100 | 0.0776 | 0.0973 |
| 161 | 0.0612 | 0.0766 |
| 347 | 0.0417 | 0.0522 |
| 1,000 | 0.0245 | 0.0308 |
| 1,509 | 0.0200 | 0.0250 |
| 3,201 | 0.0137 | 0.0172 |

The campaign's declared effect of interest is **0.02**. Detecting it needs about
**1,506 proteins**, and about 2,365 at the worst panel's spread.

**The declared stratum floor is 30.** It is short by a factor of fifty in
population, and the effect a stratum at the floor can actually see is 0.14,
which is seven times the effect the campaign says it cares about.

## 3. What that does to a single crossed axis

Take the panels above and cross them with one axis only, sequence length, at the
measured composition of the corpus (60.8 per cent at or below 512 residues, 28.7
per cent to 1024, 8.7 per cent to 2048, 1.8 per cent beyond).

| panel | <=512 | 512-1024 | 1024-2048 | >2048 |
|---|---|---|---|---|
| NK:MFO | 687, 0.030 | 324, 0.043 | 98, 0.079 | 21, below floor |
| NK:BPO | 918, 0.026 | 433, 0.037 | 131, 0.068 | 28, below floor |
| NK:CCO | 679, 0.030 | 320, 0.043 | 97, 0.079 | 20, below floor |
| LK:MFO | 574, 0.032 | 271, 0.047 | 82, 0.086 | 17, below floor |
| LK:BPO | 738, 0.029 | 348, 0.042 | 105, 0.076 | 22, below floor |
| LK:CCO | 499, 0.035 | 236, 0.051 | 71, 0.092 | 15, below floor |
| PK:CCO | 1,947, 0.018 | 919, 0.026 | 277, 0.047 | 58, 0.102 |

**Twenty-two of twenty-eight cells clear the floor. One of twenty-eight can
detect the declared effect**, and it is the prior-knowledge cell at the
commonest length, which is the least interesting cell in the grid.

So the floor admits twenty-one cells that are blind to the question the campaign
is asking. That is the defect, and it is not a defect of the floor's value. A
floor of thirty is a rule against printing an average of three things. It was
never a power threshold and must stop being read as one.

## 4. The consequence, which changes the standard rather than the numbers

**Stratification in this campaign is for explanation, not for detection.** Those
are different jobs and they need different rules.

- **Detection** happens at the panel. Only a panel reaches a population where the
  declared effect is visible, and only some panels even then.
- **Explanation** happens in the strata. A stratum locates where an effect lives
  and what it covaries with. It is a map, and a map does not need to be powered
  to be true; it needs to be honest about what it cannot resolve.

Reading a stratum as a test is the error, and the standard should make it
impossible rather than discourage it.

## 5. The design

1. **Every stratified number carries its own detectable effect.** Not the
   population, the detectable effect, next to the value, in the same row. A cell
   reading 0.03 with a detectable effect of 0.08 is reporting that it cannot
   resolve its own number, and the reader sees it without arithmetic.
2. **A null in a stratum is reported as "no evidence at this power"**, never as
   "no effect", unless the detectable effect is below the declared effect of
   interest. This is the difference between a measured null and an unread one,
   which is the sixth strength value the instrumentation side is adding.
3. **Depth is declared, never absorbed.** Where a window has to be deepened to
   populate a stratum, the depth is a fixed declared grid and it enters the frame
   descriptor beside the ontology version, the propagation and the exclusion
   rule. Two strata at different depths are never placed in one table without
   that stamp. Adaptive stopping on population is not used: the depth needed is
   a deterministic decreasing function of the stratum's rarity, so it is
   collinear with the thing being studied rather than merely confounded with it.
4. **Accumulation across releases filters on survival to the mark.** First
   appearance partitions appearance events, not the label set at the mark, and
   the corpus contracts about thirty per cent twice. An annotation that appeared
   and was withdrawn is not ground truth. The survival rate per depth is reported
   because it is a finding about the corpus and it is free.
5. **The wall is named, not bought.** The longest length band is 1.8 per cent of
   the corpus and falls below the floor in six of seven panels. It is not
   reportable in any window ending at the mark, and buying it with a deeper
   window buys a cell whose depth makes it incomparable to its own row. Say so.
6. **Every comparison publishes its per-protein paired sigma**, so the next
   design sizes itself from measurement.

## 6. What the platform has to carry

Three fields, and they are the same shape as the frame descriptor that the
census identified as the single structural fix.

- On the stratum row: population, detectable effect, and the sigma it was
  computed from.
- On the declared comparison: the effect of interest, the depth grid point, and
  the survival filter applied.
- On the guard: a refusal to publish a stratified table whose rows carry
  different depths without the stamp, in the same way a comparison already
  refuses two results that do not declare the same frame.

None of it needs new measurement. All of it is arithmetic over quantities that
the evaluation already produces, and the reason it is not there is that the
floor and the effect of interest were declared in different documents and never
divided by one another.
