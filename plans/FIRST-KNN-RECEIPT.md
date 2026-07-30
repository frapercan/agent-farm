# FIRST KNN RECEIPT: the smallest end-to-end run, and what it is not

The campaign starts from zero and scales up. This is the first rung of that
climb: one evaluation window, plain nearest-neighbour transfer, no reranker, no
learned encoder, no aspect separation. Its purpose is to prove the chain carries
a payload from dispatch to a number, and to produce a figure nobody in the
project can currently compute.

**It runs today with no code change and no infrastructure change.** Everything
below was verified against the live platform and the checked-out code rather
than inferred, and every claim carries its evidence.

`CAMPAIGN.md` stays authoritative for the campaign. This plan is deliberately
smaller than the campaign's gate, and section 2 says exactly how.

---

## 1. Why it is valid today

Three things had to be true, and each was checked.

**The ground-truth rule is correct for this window, even though the correct
builder is not wired.** `protea/core/first_appearance.py` has zero callers
outside its own test, so the live rule is the pairwise delta at
`protea/core/evaluation.py:333`. That rule is the one the project retired,
because the corpus contracts and a net delta counts a restoration as new. **But
on a window with exactly two cuts of history the two rules are provably
identical**, and the project's own test pins the equality:
`tests/test_first_appearance.py::test_two_cuts_are_enough_and_agree_with_the_pairwise_rule`
asserts `first_appearance(history) == pairwise_additions(*history)`. Release 226
is the earliest cut loaded, so the 226 to 227 window has exactly two cuts and the
retired rule cannot differ from the correct one. **The moment a third cut enters
the window, this stops being true**, which is why wiring the builder is a
blocker for the campaign and not for this receipt.

**The prediction stage needs no artifact store**, so it can run on the compute
node while the artifact-bound stages stay on the server. `get_artifact_store`
appears nowhere under `protea/core/operations/predict_go_terms/` except
`_reranker_scorer.py:250`, which is gated behind `_reranker_requested`. Its only
output is database rows, so which machine executes a batch does not affect
correctness.

**The nearest-neighbour search runs on the processor, not the card.** Project
policy forbids neighbour search on this graphics card, and the compute node's
environment sets `PROTEA_KNN_DEVICE=cpu`. So this work runs alongside the
embedding backbone that is using the card, rather than competing with it.

---

## 2. What this receipt is NOT

Stated first, because a number without these caveats beside it is worse than no
number.

**It is not the campaign's gate.** `CAMPAIGN.md` requires the gate to run through
the first-appearance builder. That builder is not wired. The equality in section
1 makes the output correct for this window, not the requirement satisfied.

**It is not stratified on the project's four axes.** The scorer stratifies on
category by aspect only. Length band and homology band have no producer:
`protea/core/strata.py` is imported by nothing but its own test. Two axes, not
four, so under the standing norm this cannot be reported as a result.

**It is not the champion recipe.** Last-layer mean-pool with plain L2, no
per-dimension standardisation, no sparsity, no learned encoder, aspect separation
off. The project's own layer ablation measured the last layer as the weakest
fixed choice by about nine percent on real GO transfer. This is the floor the
levers get measured against, chosen because it is the simplest thing that runs.

**Its neighbours are computed on an anisotropic space.** Measured on the stored
vectors: mean cosine between random protein pairs is 0.858 for one backbone and
0.594 for another, and centring changes about 37 percent of the thirty nearest
neighbours. Retrieval never centres. The number is therefore a faithful
measurement of what the platform currently does, and not of what the
representation can do.

Call the output a **mechanism receipt**.

---

## 3. The sequence

**Correction, 2026-07-30.** An earlier version of this section claimed the
artifact store is local filesystem on whichever machine executes, and therefore
that hosts are not interchangeable. **That was wrong, and the error is worth
recording because it is a method error rather than a reading error.** The claim
rested on three checks that were each true and together misleading: the default
backend is `local` (`settings.py:86`), the compose passes no storage variables,
and the secret bundle defines none. The third was checked against the copy
recovered from the 2026-07-27 archive, not against the live file. **The live
bundle on the server does define `PROTEA_STORAGE_BACKEND=minio`.** The two
diverged, and an archived config was treated as the running one.

Verified empirically instead of inferred: the server wrote the ground truth of
this very window to `s3://protea/eval_groundtruth/<id>/groundtruth.parquet`, and
the compute node **read that object back**, 9,004,385 bytes, bucket `protea`,
from its own machine. The store is genuinely shared.

So the placement rule is not "hosts are not interchangeable". It is narrower:

**Any stage can run on either machine once that machine is configured for the
shared store.** The server is. The compute node is not: its environment file
defines connection and tuning settings only, so an artifact written there today
would land on its local disk and be invisible, and the write would succeed
silently because `LocalFsArtifactStore.__init__` creates the directory. Configure
the node before giving it a stage that writes an artifact; until then, keep the
artifact-writing stages on the server.

The prediction stage is exempt either way, because it writes no artifact.

| step | where | operation | queue |
|---|---|---|---|
| 0 | server | seed scoring presets | none, synchronous HTTP |
| 1 | server | `generate_evaluation_set` | `protea.jobs` |
| 2 | either | read the ground truth back over HTTP | none |
| 3 | **compute node** | `predict_go_terms` | a private queue |
| 4 | either | verify the cohort counts agree | none |
| 5 | server | `run_cafa_evaluation` | `protea.evaluations` |
| 6 | either | read the metric and its denominator | none |

### Step 0: seed the scoring presets

`POST /v1/scoring/configs/presets`. Idempotent, presets matched by name are
skipped. Required because with a null scoring config the result row is silently
dropped from `/v1/benchmark/matrix`, and because step 5's endpoint auto-attaches
the baseline only if the row already exists.

### Step 1: generate the evaluation set

`POST /v1/annotations/evaluation-sets/generate` on the server.

```json
{
  "old_annotation_set_id": "41b31f10-7a23-430f-adee-af555c85e244",
  "new_annotation_set_id": "8f4d6c89-9188-4e56-924f-cb57af6fdf0e",
  "pivot_ontology_snapshot_id": "bfa1d095-d618-4c01-a8b2-62f3b5569f16"
}
```

**The pivot is the one irreversible decision in this plan.** The (old, new) pair
is unique and a re-dispatch silently returns the cached set while ignoring the
pivot, so it cannot be corrected later without a delete that also destroys the
artifacts. It must be the t0 ontology, `releases/2025-03-16`, and not the new
set's snapshot: only with the t0 pivot does the band guard pass for band `v226`,
and only then does the information-accretion weighted metric exist at all.

Pass nothing else. `window_role` must be omitted, because on step 5 it is
written onto the evaluation set and would permanently designate the board's own
comparable window as a protocol selection window on the strength of a smoke
test. The native snapshot overrides must be omitted too: setting either makes a
re-dispatch raise instead of reusing, which costs idempotency and buys nothing,
since they already default to each set's stored snapshot.

### Step 2: read the ground truth out of its destination

Not the write event. The read: `known-terms.tsv`, `ground-truth-PK.tsv` and
`delta-proteins.fasta`. This is what turns step 1 from a claim into evidence, and
it is where a misplaced host fails.

**Gate: stop if `delta_proteins` is zero**, because step 5 raises on an empty
cohort.

Record `removed_proteins` and `removed_annotations` here. This is the only
surface that reports them: the `removed` bucket has no download route and the
scorer path drops it silently.

### Step 3: the nearest-neighbour transfer, on the compute node

Dispatch the coordinator through `POST /v1/jobs` with an explicit `queue_name`
that only the compute node consumes. The dedicated routers hardcode their queues,
and `POST /v1/jobs` is the only path that takes a queue name, at the cost of
validating neither the operation name nor the payload. So the payload must be
checked before dispatch rather than after.

Cohort: the accessions from step 2's FASTA. Omitting them targets every embedded
protein, which is 528,294 queries.

Flags for the simplest possible pass: `aspect_separated_knn` false, and every
`compute_*` flag false. Aspect separation off avoids three per-aspect float32
copies and a full scan of a 5.9 million row annotation set.

**`search_backend` and `metric` are not enumerations.** Both accept any string
and fail only inside the batch, leaving an empty prediction set and failed
children. Spell them exactly: `numpy` and `cosine`.

**`ontology_snapshot_id` is the t0 snapshot**, the same `bfa1d095`, because GO
terms are scoped per snapshot and the donor annotations of set 226 resolve to
that snapshot's rows.

### Step 4: verify the cohort before scoring, not after

Three counts must agree: `delta_proteins` from step 2, the `queries` field of the
`load_queries_done` event, and the FASTA record count.

They can differ silently, and this is the shape of a defect the project has
already paid for. Ground truth is keyed by the annotation table's
`protein_accession`, which the loader filtered against
`Protein.canonical_accession`, while both the prediction cohort and the FASTA
filter on `Protein.accession`. Live counts are 616,846 proteins against 575,503
canonical, so 41,343 rows have an accession that differs from its canonical form.

After scoring the discrepancy is unrecoverable from the reported number.

### Step 5: score

`POST /v1/annotations/evaluation-sets/{id}/run` on the server, with band `v226`
and the information-accretion file, and `leakage_role` set to `probe`.

**Band and the accretion file travel together or not at all.** Passing the file
with a null band makes the guard a no-op, so a foreign corpus would silently
reweight the metric. And the guard only tokenises the path's basename: it never
checks that the file exists. **Confirm the absolute path on the executing host
before dispatching.**

### Step 6: read the number, and gate on the number

**Never gate on job status.** The scorer wraps its whole call in a bare
exception handler, emits a warning, returns an empty dict, writes the result row
anyway and reports success. A missing accretion file, an unreachable ontology
download and an allocation failure all present identically as a green job with no
metric.

Gate on a specific metric existing in the result.

---

## 4. What to report beside the number

Without these it is uninterpretable, and this is exactly how a baseline gets
manufactured.

**The denominator.** The scorer restricts the ground truth to predicted
accessions, which converts cohort loss into a smaller denominator rather than
lower recall. The before and after counts exist only in an event, and nothing
writes them onto the result row. Coverage in the metrics table is computed after
the restriction, so it is approximately one by construction and cannot catch it.
Copy the six numbers into the same table as the metric.

**The threshold.** Cosine distance is one minus cosine, so the score formula maps
neighbours into the upper part of the unit interval while the scorer sweeps the
threshold across all of it. Read the threshold column: if it sits at the top of a
plateau, the figure is threshold-limited rather than method-limited.

**The scorer's identity.** There is no scorer or version column on the result
row, and the provenance helper has no caller. Put the resolved scorer commit into
the job description at dispatch time, because it is the only writable surface
that needs no migration.

**Which pivot, and which recipe.** Both are choices this plan made, and neither
is recoverable from the result row.

---

## 5. What this unblocks, and what it does not

Passing this receipt earns the right to add one lever at a time and measure each
against it: per-dimension standardisation, an earlier layer, sparsity, the
learned encoder, aspect separation, the reranker.

It does not earn a campaign number. Four things stand between this receipt and
one, and they are the next slices rather than follow-ups:

1. **Wire the first-appearance builder**, without which any window with three or
   more cuts is built on the retired rule. This binds the moment release 230
   enters a window.
2. **A shared artifact store**, without which the compute node cannot take any
   stage that writes an artifact. MinIO already runs and nothing uses it: the
   platform's backend defaults to local and no configuration overrides it.
3. **Producers for the length and homology axes**, without which the output is
   two axes and cannot be reported as a result.
4. **Register the accretion table as an entity.** Today it reaches the scorer as
   a machine-local path with no producer in the operation registry, which is
   precisely the defect `CAMPAIGN.md` says the first gate exists to expose.
