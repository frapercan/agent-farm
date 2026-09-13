# The survivor cascade, and the six things a design of it has to carry

This supersedes the single-configuration shape of `CAMPAIGN-INSTANCE-ZERO.md`, which pins depth
at 10 and defers the neighbourhood axis. The campaign is not one instance of one configuration.
It is a cascade in four stages, and at each stage a set of configurations survives by consensus
across regions.

    S1  open the tap: K in {1,2,3,5,10,30} crossed with the scorings,
        consensus per stratum, X survive
    S2  over those X, other transformations (learned embeddings),
        scored the same way, consensus, X2 survive
    S3  two towers in several configurations, GENERATING candidates,
        over the best of the learned ones
    S4  from the best of the whole graph, by consensus, the re-ranker

Each of the six sections below comes from something verified rather than argued, and each one
closes a way the design could be read wrong.

---

## 1. What survives is a configuration and its whole annotation set

Never annotations picked inside a configuration. Channelling **routes whole configurations into
regions**; it does not merge them term by term.

Four things rest on that and all four break under the other reading. It is not an ensemble, and
an ensemble is the Combination node, which needs a named combiner. The threshold keeps its
meaning, because two configurations score on different scales and a term picked from one carries
no comparable confidence in the other. The arm count stays finite, because choosing annotations
opens an exponential space no floor can price. And the survivor has a producer, which a
hand-assembled set of terms does not.

And because the regions **partition** the units, the channelled system is the **disjoint union**
of its per-region choices, evaluated over exactly the same population as any single
configuration. **That is what makes the channelled against not-channelled contrast paired and
legitimate**, rather than a comparison of two different populations wearing one name.

## 2. There are more than nine regions, and the arithmetic says how many

Measured against the population floor of 332, over `storage/encoder-study/artifacts/113_length.json`
and `114_cross.json`:

| crossing | cells clearing the floor |
|---|---|
| panel x length, 36 cells | 15, and only 5 of 9 panels admit the split at all |
| panel x length x homology, 72 cells | **13 (18 per cent)**, median 71, minimum 1 |

**Eleven of those thirteen are prior-knowledge**, which is the region the arithmetic already
calls inert. So crossing everything erases the six panels where the thesis lives. The finest
partition is the least useful one, which is the opposite of the intuition.

The resolution is to **separate reporting from routing**. Reporting happens over all four axes,
always, because it is a group-by over stored rows and costs nothing. Routing happens over a
**hierarchy**: the panel is mandatory, and it refines by length only where the refined cells
clear the floor. That yields **fifteen routing regions**. A region that cannot resolve declares
itself **unpowered** and inherits its parent's decision rather than guessing.

## 3. Homology cannot route, for two independent reasons

The population reason is above. The fatal one is that today the homology band is computed from
the donors the run retrieved, and **K changes which donors are retrieved**, so in S1 the band is
a property of the arm. That breaks the coordinate invariant inside the routing node itself, and
the bias runs the flattering way, because a configuration that retrieves better promotes its own
easy cases into the easy bands.

Length is clean: a property of the sequence, identical under every arm.

Homology enters when a fixed-reference producer exists. Until then it is a blocked edge with a
named precondition, and it is reported beside every result without ever routing one.

## 4. The neighbourhood sweep is nearly free

Candidates are written to a fixed depth and every smaller depth is a truncation of a list that is
already stored. One accelerator pass at 30 and five re-reads, not six passes.

## 5. The K by scoring grid is not a rectangle

Verified at `protea-method/src/protea_method/pipeline.py:318`: the vote fraction is
`vote_count / ctx.k_div`. **At K equal to 1 it is 1.0 on every row**, a constant, and a constant
signal informs nothing.

So `vote_fraction`, `embedding_plus_vote`, `composite` and the flat consensus (0.283 of the vote
mass) are **mute or damaged at K equal to 1**, and partly so at 2. Those cells are mute by
construction and are removed **before anyone looks**, not explained afterwards.

## 6. The per-cell threshold is already the status quo

Verified at `protea/core/operations/_run_cafa_eval_driver.py:352`: `cafa_eval` is invoked once per
NK / LK / PK setting, and inside it the optimum is per namespace. **All nine cells already carry
their own tau.**

Do not introduce a global tau. It would depart from what the platform measures and make these
numbers incomparable with the board. And because the per-cell optimum is applied identically to
both arms, **it cancels in the paired difference**.

---

## What actually threatens the claim, and what fixes it

The channelled arm chooses **once per routing region, fifteen times**. The baseline chooses once.
**Channelling will win even when no affinity exists**, because it has fifteen chances to fish
noise out and the other has one. No floor repairs this: the bias is in the procedure, not in the
threshold.

**Cross-fitting the policy is what makes the claim falsable.** Split the experimental cohort into
folds, learn the channelling on the training folds, apply it to the held-out fold, and report the
**out-of-fold gain**. Out of fold, channelling can lose, which is the property the design needs
and does not currently have.

It is cheap: a re-read of the per-protein rows, no new predictions, **provided those rows carry
the threshold grid**. That is the dependency that makes the grid a precondition of the claim
rather than a refinement of the artefact.

---

## Open, carried forward

**Does the reconciliation path resolve `replaced_by`?** Of the 2,756 terms alive in the 2024
graph and retired by the pivot, 737 carry `replaced_by` to a destination alive in the pivot, 151
carry `consider`, and **1,868 have no destination at all**. If the path does not resolve
`replaced_by`, t0 annotations are being discarded that the ontology says explicitly where to send,
which inflates the gained side the same way the phantom gap did. It is a code read, not a query.

**The embedding similarity scale.** `1 - d/2` assumes cosine distance spans [0,2]; the empirical
range is [0, 0.154], so the signal is compressed into the top 7.7 per cent of the scale and the
threshold grid resolves 7 of its 99 steps against 91 for the other presets. Measured: the four
signals separate hits from misses almost identically (AUC 0.608 to 0.645), so the preset table
orders grid resolutions rather than signal quality. In a composite the embedding term contributes
0.3980 with a standard deviation of 0.0026, which is an offset and not a signal, and that is why
`composite` and `composite_no_embedding` differ by 0.0001.
