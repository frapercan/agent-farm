# LAFA-INTEGRATE: productise the first-place system into the platform

The offline laboratory (`protea-reranker-lab/fullgo/`) reaches first place on the LAFA
continuous benchmark (mean IA-weighted micro-F **0.391**, against 0.381 for the previous
leader), sealed on the September 2025 to March 2026 frame. That result is computed by
scripts outside the platform. This plan integrates it natively so that PROTEA itself
produces the reranked prediction and the standard evaluation reproduces 0.391, surfaced as
a new stage on `/benchmark`. The application becomes the single source of truth for the
headline number the thesis reports.

## What the first-place system is, in platform terms

The score combines four streams over a per-protein candidate set, then a learned per-category
combiner:

1. The existing nearest-neighbour (KNN) composite scorer. Already in the platform.
2. A direct full-catalogue predictor: a classifier over the six concatenated frozen protein
   representations that proposes terms across the whole vocabulary, so the candidate set is
   no longer capped by what neighbours carry. New to the platform.
3. A self-prior stream: the protein's own weaker (non-experimental) prior annotations. New.
4. A cross-aspect association signal: for a protein already partly characterised, how often a
   candidate term co-occurs in training with the terms the protein is already known to carry,
   with a cross-branch variant. New.

The combiner is the platform's existing per-category re-ranker (LightGBM, one model per
No-Knowledge / Limited-Knowledge / Partial-Knowledge setting), extended to consume the three
new feature streams. Candidates become the union of the neighbour terms and the classifier
terms; the self-prior and association streams contribute features (and candidates).

## Principles (non-negotiable)

- Do not reinvent. Reuse the existing producer / feature-family / reranker machinery
  (`protea/core/features/registry.py`, `RerankerModel`, `predict_go_terms`, the post-KNN
  pipeline). The classifier is a new candidate producer; self-prior and association are new
  feature families; the per-category reranker already exists and is extended, not replaced.
- Frozen representations only. No model fine-tuning. Fits a single 12 GB GPU.
- Leakage-clean. Every feature reads only data at or before the reference cutoff. The
  association and self-prior streams read the protein's own known terms at the cutoff, which
  is the same partition the benchmark uses to define the three settings; they are silent for
  No-Knowledge proteins by construction.
- Train on the earlier window, seal once on the later one. The three combiners are fit on the
  220 to 227 window and applied unchanged to the 227 to 230 frame.
- Green local CI before every push. Reversible migrations. PROTEA PRs base `develop`,
  contracts/lab as their own repos. No agent ever points at the live database. A dev-stack
  redeploy happens only with the maintainer's explicit go-ahead.

## Slices

### INT-1: contracts (feature families and payload flags)
Add three feature families to `protea-contracts`: `self_prior`, `association`, `classifier`,
with their feature names (`self_prior_score`; `association_total`, `association_cross`,
`association_present`; `classifier_score`, `classifier_present`). Add predict-payload flags
`compute_self_prior`, `compute_association`, `compute_classifier`. Keep `__all__` a superset
and never pin a `file://` path (avoids the major-bump cascade). Minor version bump.
Exit: consumer pytest (PROTEA, lab) green against the new contracts pin.

### INT-2: self-prior feature
Add `GOPrediction.self_prior_score` (nullable float) with a reversible migration. New compute
module that, for a query protein, reads its non-experimental prior annotations (propagated, at
the cutoff) and marks candidate terms that match. Bind it in the feature registry; wire it into
the post-KNN pipeline behind `compute_self_prior`.
Exit: unit tests; a small predict run shows the column populated; CI green.

### INT-3: co-occurrence table and association feature
New table `go_term_cooccurrence(aspect, term_a, term_b, count)` plus per-term frequency, built
by a new `build_go_cooccurrence` operation from the experimental annotations of a chosen
annotation set (strict cutoff). Add `GOPrediction.association_total`, `association_cross`,
`association_present` with a reversible migration. Compute module: for the query protein's known
experimental terms at the cutoff, the summed conditional probability of each candidate term, plus
the cross-branch-only variant; behind `compute_association`.
Exit: build operation produces the table; unit tests on a small fixture; CI green.

### INT-4: classifier producer
Register the trained full-catalogue classifier as a model artifact (a registry row with an
artifact pointer and a schema hash, mirroring how re-ranker models are registered). New
`ClassifierProducer` that loads the classifier, fetches the six frozen representations for the
query proteins, and emits its top terms per protein as additional candidates (synthetic
reference id), storing `classifier_score` on `GOPrediction` (migration). Wire it as a candidate
producer in the batch operation alongside the neighbour search, behind `compute_classifier`;
candidates become the union. Classifier training stays in the laboratory; the platform consumes
the trained artifact. (A platform-side retraining operation is optional later.)
Exit: a predict run with the producer enabled adds classifier candidates; CI green.

### INT-5: per-category combiner over the extended features
Extend the re-ranker scorer to apply the per-category combiner over the full feature set
(neighbour sub-features, classifier score, self-prior, association, plus term informativeness and
log frequency), splitting predictions by setting. Determine each prediction's setting from the
protein's known terms at the cutoff, per ontology branch.
Exit: applying a three-model binding reproduces the offline per-setting scores within noise on a
fixture; CI green.

### INT-6: export pipeline carries the new features
Extend `export_research_dataset` so the training table includes the classifier, self-prior, and
association columns, so the combiners are trained on exactly the features served at predict time
(train/serve parity).
Exit: an export run emits the new columns; manifest records the new families.

### INT-7: train and import the three combiners
Export the 220 to 227 training table with the new features; train the three per-setting combiners
in the laboratory; import them through the existing re-ranker import endpoint, tagged with the
extended schema hash.
Exit: three combiner model rows present, schema hashes aligned with the live feature set.

### INT-8: end-to-end seal and surface
Dispatch the prediction over the 7,401-target query set with all producers and the three
combiners, then run the standard evaluation against the LAFA ground-truth set. Verify the mean
reproduces about 0.391 and appears as a new full-system stage on `/benchmark`, next to the
neighbour-only 0.324. Requires one dev-stack redeploy (maintainer authorises) to load the new
operations.
Exit: an evaluation result tagged with the LAFA frame; `/benchmark` shows the full-system row at
about 0.391; the number matches the offline seal within run-to-run noise.

### INT-9: parity, tests, docs
Integration tests covering each producer and the per-category dispatch; a train/serve parity
check (platform features equal laboratory features on a sample); architecture decision records for
the new producers and features; user-facing documentation; update the thesis reproducibility
paragraph to point at the live `/benchmark` figure.
Exit: full local CI green across the touched repos; docs and ADRs merged.

## Sequencing and risk

INT-1 unblocks everything. INT-2 and INT-3 are independent and can proceed in parallel after
INT-1. INT-4 is the largest single piece (a new producer plus model loading) and is independent
of INT-2/INT-3. INT-5 depends on INT-2 through INT-4. INT-6 and INT-7 depend on INT-5. INT-8 is
the only slice that touches the live stack and needs the redeploy. INT-9 runs alongside from
INT-2 onward.

The main risks are train/serve feature parity (mitigated by INT-6 making the export emit exactly
the served features, and by the INT-9 parity check), migration safety (all reversible, no live-DB
agents), and the contracts cascade (mitigated by a superset `__all__`, no path pins, minor bump,
and verifying consumer pytest before chaining). The headline number carries the single-window
uncertainty already documented in Experiment 13; the integration reproduces the sealed result, it
does not re-open the measurement.
