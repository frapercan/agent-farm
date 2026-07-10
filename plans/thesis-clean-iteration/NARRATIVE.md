# How we tell the story

Three surfaces, one truth. The thesis argues it, the interface shows it happening, the
reference documentation explains how the machine produces it. Nothing is duplicated:
each surface points at the others. Written 2026-07-10, at the start of the autonomous
campaign, because a week of unattended work is won or lost in the planning.

## The one sentence

> Protein function is predictable from a **taxonomy of orthogonal evidence**, combined by
> a **calibrated fusion**, measured on a **leakage-free temporal frame**. The nine-cell
> benchmark is not nine numbers, it is a **map of which evidence wins in which regime**,
> and it has an **honest, evidence-bound frontier** that this thesis characterises rather
> than hides.

Everything below is a way of making that sentence checkable by a different reader.

## The three surfaces

| surface | reader | what it must deliver |
|---|---|---|
| **The book** (`thesis/`, LaTeX) | the tribunal | the argument, and only validated numbers |
| **The interface** (`protea.ngrok.app`) | anyone, including the tribunal | the same argument, live: every claim carries its receipt and the operation that regenerates it |
| **The reference** (Sphinx, `PROTEA/docs`) | an engineer who wants to reproduce or extend | the mechanism: operations, contracts, schema, ADRs |

The failure mode we are correcting is that the interface is currently an instrument
panel with a thesis PDF bolted on, and the thesis is a pile of experiments with a spine
somewhere in the middle. The instrument is not wrong, it is simply not the front door.

## The interface as a book, not a dashboard

The landing page is chapter zero, not a status widget. The instrument survives, one level
in, as the place where you go to *run* what the book *claims*.

Proposed shape:

- `/` **The argument.** The one sentence, the four pillars as four chapters, and the
  sealed headline stated with its frame (`f_micro_w`, v227 to v230, first in seven of
  nine cells). A link to `/thesis.pdf`, which is already served from the mount.
- `/pillar/1..4` **One page per pillar.** Each page has the same five parts, in this order:
  1. the claim, in prose, in one paragraph;
  2. the evidence, as a board-faithful table (never a lab metric, never a different frame);
  3. the receipt: the `*_result.json` and the script that produced it, downloadable;
  4. **reproduce it**: the operation, dispatched from the page through `POST /jobs`, which
     is what requirement FR-1 has been asking for;
  5. the caveats, stated by us before anyone else states them for us.
- `/score/:accession/:go` **How a score is made.** The reader's on-ramp: one protein, one
  GO term, walked from retrieval to calibrated probability, showing which evidence moved
  the number. Grounded in a measured fact: sixteen of sixty-four features carry ninety
  five percent of the gain, and the single largest driver is a base-rate prior, which we
  discuss rather than hide.
- `/instrument/*` the existing routes (`benchmark`, `datasets`, `proteins`, `reranker`,
  `scoring`, `farm`, `annotations`, `query-sets`), unchanged in function, moved one level
  down. The dashboard is a tab, not the entrance.

A claim with no receipt does not get a page. A receipt with no operation to regenerate it
is a promise, not a proof, and it stays in the appendix.

## The reference documentation

Sphinx already has the right skeleton (`abstract`, `introduction`, `results`, `insights`,
`architecture`, `adr`, `appendix`). What it lacks is the spine. Align it:

- `insights.rst` becomes the four pillars, each pointing at the same receipts the
  interface serves. It never restates a number that the thesis has not validated.
- `architecture/` and `reference/` keep the mechanism, and the pillar pages link *into*
  them rather than paraphrasing them. The canonical-source rule stands: point, do not copy.
- Every operation that a pillar page can dispatch has a page in `reference/` naming its
  payload and its receipt. If it cannot be dispatched, it is not in the book yet.
- New ADRs land for the decisions this campaign makes: the signal store, the closing of
  the D45 seam, the text-aligned representation as an evidence class.

## The chapter order of the book

The current manuscript orders by experiment. It should order by argument.

0. **How a score is made.** The on-ramp. One protein, one term, end to end.
1. **The frame.** The leakage-free temporal protocol, and why any number stated before
   this chapter would be untrustworthy. This is what earns the right to the rest.
2. **Pillar 1, the taxonomy of evidence.** And the distinction the data forced on us:
   *representations* are embeddings, keyed by model and recomputed; *features* are the
   per-candidate scalars the reranker consumes; and some evidence enters as neither, but
   as a **graft** (InterPro2GO, worth +0.0179, which is what secures seven of nine).
3. **Pillar 2, the calibrated fusion.** Learned k-WTA retrieval, calibrated evidence
   scorers, a shallow per-category combiner. Two learning layers with a signal store
   between them.
4. **Pillar 3, the map of regimes.** The nine cells read as a map: the classifier carries
   the novel proteins, prior knowledge carries the partly-known, and homology proposes
   without discriminating.
5. **Pillar 4, the frontier.** The BP wall, evidence-bound rather than architecture-bound,
   with its mechanism (structure conserves molecular function, not biological process) and
   its first crack (a representation supervised on descriptions of function).
6. **The instrument.** PROTEA as the reproducibility apparatus: contracts, operations,
   provenance, and the signal store that makes every number regenerable.
7. **Limits and what follows.** Ours, stated first.

## The alignment table

The point of this document. One row per claim; if a row cannot be completed, the claim is
not ready to be told.

| pillar | thesis chapter | interface route | reference page | receipt |
|---|---|---|---|---|
| on-ramp | ch. 0 | `/score/:acc/:go` | `reference/scoring` | booster gains, per category |
| frame | ch. 1 | `/pillar/frame` | `adr/D40` | leakage check, `leak_check_overlap.json` |
| 1 taxonomy | ch. 2 | `/pillar/1` | `reference/feature_schema` | `lofo_9cell/result.json`, InterPro2GO graft |
| 2 fusion | ch. 3 | `/pillar/2` | `adr/D43` | `clean_227230/comparison.json` |
| 3 regimes | ch. 4 | `/pillar/3` | `insights` | `lofo_9cell/result.json` |
| 4 frontier | ch. 5 | `/pillar/4` | `insights` | `struct_gate/`, `text_scorer/*_result.json` |
| instrument | ch. 6 | `/instrument/*` | `architecture/` | the signal store, once it lands |

## The rules that keep the three surfaces honest

1. **One metric, one frame.** `f_micro_w`, v227 to v230. A number in another metric or
   another frame does not appear on any surface without being labelled as such.
2. **No claim without a receipt.** The receipt is a `*_result.json` plus the script.
3. **No receipt without an operation**, or the claim lives in the appendix until there is
   one. This is how the interface stops being a brochure.
4. **The sealed 0.4063 is immutable.** Regenerated numbers are candidates until reviewed.
5. **We state our caveats first.** Every pillar page ends with what would falsify it.
6. **Point, do not copy.** The thesis cites the reference; the reference cites the code;
   the interface serves the receipt. A number lives in exactly one place.

## What this changes about the campaign

The tracks already running (signal store, the grid, the crowning experiment, the feature
necessity audit) are unchanged. What changes is what *done* means: a track is finished
when its claim exists on all three surfaces, with a receipt and an operation, not when
the number appears in a log.
