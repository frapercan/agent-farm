# The clean campaign: what is measured, what is decided, and what is still open

Opened 2026-09-02. This file exists because the design phase was living in two
session transcripts and a session limit stopped both machines at once. Nothing
below was lost, but only because it was re-derivable; the second time it will
not be. Everything the design phase establishes lands here as it is
established, not when it is finished.

**Status: the design phase is OPEN.** No arm of the clean campaign has been
dispatched and none should be until D1-D8 below are closed. `CAMPAIGN.md`
remains authoritative for what a run IS; this file is the record of the
decision that produces the next one.

Division of labour, set by the author on 2026-09-02: the laptop owns the
platform and the instrument, sobremesa owns the lab and the map of every
research front to date. See `TOPOLOGY.md` for why the split is what it is.

---

## 1. What was measured, so nobody measures it again

All counts read from the live database on 2026-09-02 unless marked otherwise.
`pg_stat_user_tables.n_live_tup` is an ESTIMATOR and reports 0 for several
populated tables including `alembic_version`; every number here is a `count(*)`.

### The substrate is rich and the experiment layer is thin

    protein                616,846      go_prediction        38,246,372
    sequence               528,294      sequence_alignment    4,442,430
    go_term                432,070      protein_go_annotation 21,876,159
    sequence_embedding   6,867,762      go_term_relationship    703,670

    embedding_config  13     ontology_snapshot  9     annotation_set  4
    scoring_config     8     information_accretion_set  6

    prediction_set    19     evaluation_set     1     evaluation_result  93
    experiment_run     0     reranker_model     0
    interpro_annotation 0    interpro_go_mapping 0
    term_cooccurrence   0    term_frequency      0

Every `prediction_set` and every `evaluation_result` was created between
**2026-08-27 and 2026-08-30**. The campaign wiped on 2026-08-27 left nothing
behind, so no measurement predating that date is evidence about this window.

### Zero nodes are `measured`, and the cause is mechanical

`_graph_edges.strength_of` returns `MEASURED` only when a floor is declared AND
the comparison separates. The only place in the schema where a floor can be
declared is an `experiment_run` whose `config` holds `graph_node` and `floor`
(`_graph_reads._Q_FLOORS`). **`experiment_run` holds 0 rows.**

So: 19 prediction sets, 581 successful `run_cafa_evaluation` jobs, 93 results,
and **zero declared comparisons**. Nothing here is a failure of science. It is
that no experiment was ever declared to be one.

A second consequence, and it is a defect in the vocabulary rather than in the
record: `strength_of` returns `CHOSEN` both for "a floor was declared and the
comparison did not separate" and for "no floor was ever declared". A
well-powered null and a decision nobody took read identically. See D7.

### There is no replication anywhere in the record

With the arm named by every field it varies in, the 93 results hold **80
distinct arms**. Per panel: **612 (level, panel) cells at n=1, 108 at n=2, none
at n>=3**. Every one of the 108 duplicates has `count(distinct prediction_set_id) = 1`
— it is the same prediction set evaluated twice. Evaluation is deterministic
(117 of 117 metrics reproduce exactly), so those duplicates carry **no
information about noise**.

Consequence: the sigma floors the endpoint reports (`reporting` 0.081 n=129,
`routing` 0.13 n=332) are imported. Nothing in this record could have produced
them. See D2.

### The surface was five days stale, and it under-named what exists

`protea-api.service` had been up since **2026-08-28 16:14:45**.
`_arm_identity.py`, which adds `self_exclusion` and `code_revision` to the
fields an arm is named by, landed **2026-08-29 18:55** (PROTEA #893);
`_graph_panels.py` changed again 2026-08-30.

Restarted 2026-09-02 00:40. `/v1/graph` went from **30 distinct arm levels to
80** in one step. The stale surface was committing the project's own recurring
defect one level up: a level named by fewer fields than it varies in, so
between-level spread rendered as within-level spread.

**The check, before believing any screen:** compare
`systemctl --user show protea-api.service -p ExecMainStartTimestamp` against
`git log -1 -- <the routers that build that screen>`. The API and the workers
are separate systemd units, so restarting the API cannot touch a running job.

### Three confounds that stop the current record being a baseline

1. **Depth is confounded with self-retrieval.** The depth-10 prediction sets
   have `exclude_self_neighbour` unrecorded and the code default is `False`
   (five call sites, all `getattr(p, "exclude_self_neighbour", False)`); the
   depth-30 sets have it `true`. Under the temporal protocol the query retrieves
   itself at distance ~0, which `strata.py` warns "measures the protocol rather
   than the neighbourhood". Comparing 10 against 30 in this record is not a
   depth comparison.
2. **"Depth" names two different quantities.** The panel field coalesces
   `max_sequence_rank` (rendered "30seq") with `max_k_position` ("10") with
   `limit_per_entry`. Top-k candidates and top-N distinct sequences are not two
   levels of one axis.
3. **Code revision drifts inside the substrate sweep** (`bc7c423`, `d8bc801`,
   `8d15893`), and the entire permissive family is `unrecorded`, which
   `_arm_identity` documents as a level that "correctly refuses to share an axis
   with" a sha.

### The stratification instrument is built, ran 480 times, and lands nowhere

`protea/core/strata.py` is complete: **seven axes** — category, aspect, length,
homology, donor evidence, taxonomy, propagation — with reasoned cut points and
a measurement of its own (of 1,920 protein-level combinations, 77 are
populated). The author's five named axes are inside it, plus two more.

`stratify_evaluation` has run **480 times successfully**. It writes
`<setting>/strata.parquet` to the object store and **to no table**, and only
**16 of the 93** `eval_artifacts` prefixes carry that file.

`assert_stratified` and `reportable_strata` have **zero call sites** in
`protea/`, `scripts/` and `apps/`. The guard against publishing a number with
no stratum cannot fire.

The four axes that are not yet crossed need no recompute: `go_prediction`
carries `identity_nw`, `identity_sw`, `length_query`, `taxonomic_relation`,
`distance` and `evidence_code` across all 38.2M rows.

### The per-protein artifacts cannot reproduce the published metric

All 93 results carry `per_protein.parquet` and `per_protein_grid.parquet` per
category. Reconstructing micro-averaged `f_micro_w` from the per-protein
sufficient statistics reproduces the published number **exactly in 3 of 9
panels and fails in 6** (NK.BPO: rebuilt 0.1341, restricted to pred>0 0.1463,
published 0.1466).

The cause: `per_protein.parquet` is written at ONE tau (the best-F tau) while
the published `f_micro_w` is at its own best tau — the artifacts carry
`evaluation_best_f.tsv` and `evaluation_best_f_micro_w.tsv` separately.
`per_protein_grid.parquet` carries weighted and unweighted counts but no tau
column either.

So a paired bootstrap over proteins is available **today at a fixed tau**, and
is **not** available for Fmax or for f_micro_w-at-its-own-tau without a
per-protein x tau producer that does not exist. See D2.

---

## 2. What the census found, verified here

An eight-surface census ran on 2026-09-02 (10 agents, 787 tool calls). The
load-bearing claims were re-checked against the database before being written
down; the rest are marked.

**Verified here:**

- `compare_paired_panels` is registered (`operation_catalog.py:97`) and has
  **never run** (0 rows in `job`). The operation that would produce a paired
  interval exists and has never been dispatched.
- **The features axis has exactly ONE level.** All 19 prediction sets carry the
  identical `["compute_alignments", "compute_taxonomy", "compute_reranker_features"]`.
  The catalogue offers three families; one combination was ever computed. An
  earlier reading of "3 levels available" was wrong.
- `expand_votes_to_ancestors` is `false` on **19 of 19** sets. It is the
  cheapest second level the features axis can have: a payload flag, no
  artifact, no checkpoint.
- The bank node's `unpowered` is an artefact of counting. `_graph_nodes.py`
  sets `instantiated` from policy levels and `scored` from
  `distinct annotation_set_id`; one corpus in use forces `scored = 1 < 2`.
- **No queue named `protea.embeddings.batch` is declared or consumed.** No new
  representation can be embedded until a consumer exists. `protea.training`
  HAS a live consumer, so `export_research_dataset` has somewhere to run.
- 6 messages sit in `protea.dead-letter` with 0 consumers. Drain and read them
  before the new campaign starts; a dead-lettered predict batch leaves a
  prediction set silently short.

**Reported by the census, not re-verified here** (settle before relying on):

- 39 operations registered; 19 have `job` rows, 5 more ran only as ephemeral
  children, **15 have never executed in any form**.
- 78 of the 93 results were scored on a `neighbor_vote_fraction` that is not a
  fraction, and that includes the entire sealed body. The input divergence is
  measured; whether it moves a published `f_micro_w` is not.
- `evaluation_result` rows have been deleted and nothing records it: 161
  distinct prediction ids appear in job payloads against 19 surviving sets.
- A 5-level sealed depth ladder exists and is ready for `compare_paired_panels`:
  `9995651a`, composite, `max_sequence_rank` 2/5/10/20/30, all grid-carrying,
  all under one frame digest.
- `build_go_cooccurrence` has all its inputs in the database already (the
  21,876,159 annotation rows). It is a dispatch, not an ingest, and it is the
  only hard block on the `compute_association` feature level.
- `load_interpro_go_mapping` reads a 3 MB EBI file and needs no binary. It is
  the only generator prerequisite reachable today.

---

## 3. The datasets, which all converge on one missing thing

The author asked on 2026-09-02 for three sets to be projected properly: a wide
interval for adjusting configurations, the competitive set that goes to LAFA,
and the reranker's exported dataset that iterates the longitudinal axis while
changing the neighbourhood and the annotation set across the ontologies.

**The competitive set is already defined, and it is not the one we use.**
`split_registry.COMPARABLE_WINDOW` is **v226 -> v227**, and the module says why:
it is the only point comparable to anyone else's number. Our single
`evaluation_set` is **220 -> 227**, and `220` is **not in `RELEASES`** at all —
the release table begins at v226. We hold **zero evaluations on the window that
goes to LAFA**. Both corpora are loaded, so one `generate_evaluation_set` job
builds it; the cost is then re-evaluating every arm against it.

**The adjustment interval cannot be built today, and the registry says so.**
`windows_for('adjustment')` raises `SplitUndecidedError` deliberately. Its
recorded reason: nobody knows which windows are representative until additions
and removals have been decomposed per release, and the obvious choice — the
window ending at the board's mark — is one of the two roughly thirty percent
corpus contractions. Our 220->227 set records exactly that contraction:
**9,383 proteins and 115,435 annotations removed** against 14,032 delta
proteins. We adjusted on the anomaly.

`train` is undecided for a simpler reason, stated literally in the module:
*"Ingest the releases preceding the base release, add them to the table, then
partition freely."*

**The reranker dataset hits the same wall.** `ExportResearchDatasetPayload` is
exactly the longitudinal iteration the author described: `train_versions` (a
list, validator `at_least_two_train`, forms pairs) x `test_versions` x `k` (the
neighbourhood) x `ontology_snapshot_id` x the feature flags. But under the leak
rule training may use only corpora strictly earlier than the board's mark, and
we hold exactly **{220, 226}** — the bare minimum the validator accepts, one
pair, no longitudinal room at all.

Two payload notes: `compute_association` needs `term_cooccurrence`, which is
empty, so `build_go_cooccurrence` comes first; and `search_backend` defaults to
`"faiss"`, which contradicts the standing KNN-on-CPU rule and must be set
explicitly.

**All three needs converge on one action: ingest the GOA releases between 220
and 226 and register them in `RELEASES`.** That opens the adjustment interval,
opens the reranker's longitudinal axis, and leaves the competitive v226->v227
window clean and untouched. It is the largest data gap in the project and it
had not been named.

Loaded today: goa 220 (2024-04-16), 226 (2025-05-03), 227 (2025-09-04), 230
(2026-03-04). Known to the registry but not loaded: v228, v229, v231, v232,
v233, v234 — all of which are validation, being at or after the mark.

---

## 4. The eight decisions, and where each stands

None of these is closed. Each carries the laptop's position; sobremesa's
answers are outstanding.

**D1 - What binds from the previous campaign.** Position: nothing. Every row is
27-30 August, no floor was ever declared, no node reached `measured`. The clean
campaign starts with all ten nodes at `inherited`/`chosen`, and rungs 1, 2 and
7 become prior work that is cited and does not bind.

**D2 - How the floor is born inside instead of imported.** The pipeline is
deterministic, so replication cannot mean re-running; the only real variance is
cohort sampling, which asks for a paired bootstrap over proteins.
`compare_paired_panels` already exists for this and has never run — but its
verdict has nowhere to land (no `ci_low`/`ci_high`/`mde`/`n_resamples`/`seed`,
and `_graph_reads` does not read them). And the per-protein artifacts only
support a fixed tau (section 1). So the decision is: **(a)** declare the
campaign's primary metric at a fixed declared tau, which makes the floor free
and kills the undeclared max-over-tau selection, with Fmax reported as
secondary; or **(b)** build the per-protein x tau producer and keep Fmax
primary. Position: (a). This has thesis consequences because CAFA reports Fmax.

**D3 - One seat of declaration.** An `experiment_run` row written BEFORE
dispatch, carrying node, varying fields, held fields, floor and replication
scheme, and a dispatcher that refuses an arm whose varying set contradicts it.
This is `rungs.yaml`'s own lesson — *"the design was prose, and prose cannot
refuse a job"* — ported to the graph. Open question: retire `rungs.yaml`, or
keep it as the CI-checkable half? Position: one seat. Two declarations diverge,
and the graph only knows how to read `experiment_run.config`.

**D4 - Strata to a table.** A stratum-cell table plus a writer beside the
existing `store.put` in `StratifyEvaluationOperation._write`, the guard made
reachable, and the 77 uncovered results re-passed. Backfillable from artifacts
already in MinIO. This is the precondition of the author's whole stated goal.

**D5 - Where structure retrieval sits.** `flows.py` defines the same mechanism
over another representation as the SAME flow configured differently, and a
structural KNN enters as an `embedding_config` row, which is the **substrate**
axis. `search_backend` is `numpy` on all 19 sets and carries nothing. Position:
substrate. This is a modelling judgement, not a measurement. It costs the
structure slice nothing once D1 is settled, because rung 2 stops binding.

**D6 - Order of opening.** By measured cost: `reranker_model` at 0 blocks two
nodes and one row unblocks both with no candidate recompute; InterPro at 0
blocks three but needs an ingest and a second flow; structure needs four
producers that exist nowhere. Sobremesa holds the card and the lab and may have
a different order by interest.

**D7 - A sixth strength value.** For a comparison that was declared, powered
and did not separate. If we start declaring floors, most of our results land
exactly there, so this is not cosmetic.

**D8 - What only sobremesa can answer.** What in the lab is reproducible and
what died with `storage/`; the real cost of structural acquisition in fetches,
GB and card hours; which of the ~24 `plans/` directories are retired; whether
the lab holds its own co-occurrence artifact; which GOA releases between 220
and 226 are reachable and what each load costs; and whether the per-release
decomposition of additions and removals that the adjustment split requires
already exists in the lab.

---

## 5. The cheapest things that are true regardless of D1-D8

These need no decision. They are read-only or single-dispatch, and each removes
a reason the record cannot be read.

- Drain and read the 6 dead-lettered messages.
- `audit_per_protein_artifacts` (registered, never run, read-only) for an exact
  recompute census instead of a hand walk.
- `count_backend_parameters`, to fill `embedding_config.param_count`, NULL on 8
  of 13 configs, which removes a NULL-is-a-family bias from any capacity-ordered
  reading of the substrate sweep.
- Fix the bank node's level counting, one line.
- `seal_evaluation_frames`, which the census reports would seal 16 of 17
  unsealed results; all 9 prior runs finished in under 0.05 min.

---

## 6. Norms this campaign is held to

`COLLIDING-A-NUMBER.md` in full, and rule 4 in particular, which is what caught
the two premises this design phase had to withdraw: a claim about rung 2 that
rests on a wiped campaign, and a floor that no surviving row could have
produced. A negative check counts only if you looked where the thing would be
if it existed.

`DECLARED-REVISION.txt` governs what the workers run. It does not move while a
campaign is live, and the check before editing it is on the SERVER: no job in
QUEUED or RUNNING, and no prediction set being written.

---

## 7. Closed on 2026-09-02, and what closing them uncovered

Sobremesa answered D1-D7 and part of D8. What follows is the state after that
exchange, plus what the laptop measured while executing its half of day one.

### Decisions now closed

**D1 - nothing binds.** Agreed. Sobremesa withdrew the rung-2 closure from its
own structure-retrieval premise; the correction is in agent-farm #270.

**D2 - primary metric at a fixed declared tau.** Agreed, with a condition and a
warning, both sobremesa's. Condition: the thesis reports both, with Fmax
secondary and explicitly labelled a maximum over a grid, because CAFA reports
Fmax. Warning: sobremesa's calibration study found the optimal rule DIFFERS
between `f_micro_w` and Fmax and the two disagree in direction, so choosing the
primary changes which arm wins. This is a decision about the claim, not about
the arithmetic.

**And the tool does not implement it.** `compare_paired_panels` hardcodes
`operating_point = "reselected_per_resample"` at two sites and exposes no knob.
It re-selects the operating point on every resample, which is Fmax's selection
semantics. Choosing (a) therefore requires a change to the operation, not only
a declaration. Recorded because the decision reads as free and is not.

**D3 - one seat of declaration.** Agreed. `experiment_run` is it, and
`rungs.yaml` is retired. Two declarations diverge and the graph reads one.

**D5 - structure retrieval sits on substrate.** Agreed and already withdrawn
from the retriever axis in #270.

**D6 - order of opening.** Agreed on cost order, with one change by interest:
`build_go_cooccurrence` goes first. Not for its own value but because it is a
pure dispatch whose inputs are already in the database, it unblocks the
`compute_association` feature level, and it exercises the declaration loop end
to end. Pipe-cleaner and lever at once.

**D7 - a sixth strength value.** Agreed. "Nobody declared a floor" and "a floor
was declared and it did not separate" are the difference between not knowing
and knowing.

**The distinction already exists one layer down.**
`ComparePairedPanelsPayload.effect_of_interest` carries it: "a null is read
against this and never against the observed difference; without it a panel
whose interval covers zero is reported as `null_unread`". So the operation
separates a read null from an unread one and `strength_of` does not. The sixth
value is not a new idea, it is the graph catching up with its own kernel.

### D8, partly

Sobremesa's own front census died in the same session limit (18 agents, 0
results), so **D8.1 (what in the lab is reproducible), D8.3 (which plan
directories retire) and the per-release decomposition of additions and removals
remain open**. They were not improvised, which is the right answer.

**The GOA releases exist and the axis is not supply-limited.** 221 through 225
are all present as `goa_uniprot_all.gaf.NNN.gz` on the EBI FTP:

    221  17.40 GB  2024-06-14      (context: 220 = 19.03 GB)
    222  18.87 GB  2024-08-01                226 = 21.09 GB
    223  19.19 GB  2024-10-21                227 = 14.58 GB
    224  19.51 GB  2024-12-21
    225  20.62 GB  2025-03-08

95.6 GB compressed for the five, against 179 GB free on the desktop, so they do
not all fit at once without streaming. 150 releases are archived in total.

A free cross-check falls out of this: **227 is 14.58 GB against 226's 21.09,
so the roughly thirty percent contraction is visible in the file size before
anything is loaded.** The non-monotonicity the split registry refuses to adjust
on can be confirmed without ingesting a byte.

**Structural acquisition is affordable and is not the blocker.** Measured by
sobremesa 2026-09-02, after correcting its own first probe, which used
`model_v4` against an API reporting `latestVersion: 6` and returned 0 of 30 —
a tooling artefact read as absent coverage:

    AFDB coverage on an NK sample   30 of 30
    mean residues                   469
    mean global pLDDT               77.3
    latency per query               166 ms
    mean cif                        416 KB

Upper bound over the whole experimental bank: 89,263 fetches, about 37 GB, 4.1
hours serially or roughly 30 minutes at eight-way. The API returns
`globalMetricValue` and the pLDDT fractions without downloading the structure,
so a disorder column costs 89,263 queries and no storage.

**The blocker is that no queue named `protea.embeddings.batch` is declared or
consumed.** Nothing new can be embedded until a consumer exists. Sobremesa owns
it and has taken it as its first task.

### A premise that has to be withdrawn from the record

Sobremesa reports that per-residue embeddings ARE persisted on the desktop,
with an accession index and provenance: `storage/probe/exp220.npy`
(45,073,591 x 2 x 768, 276.9 GB), `pool60k_last.npy` (67.6 GB),
`lafa_last.npy` (14.2 GB), `nk220.npy` (9.1 GB) and two more — 74,436,929
positions, 369 GB total.

This refutes gap 1 of `DESIGN-cross-encoder.md`, which states that per-residue
embeddings are not persisted and therefore forces cross-attention to
evidence-token granularity. The premise that shaped that design is false.

**Not verifiable from the laptop**: `storage/` here holds only
`evaluation_artifacts/` and `upstream_receipts/`, so this is sobremesa's
measurement, attributed and not collided. Nothing should be built on it until
it is, but the false premise should be withdrawn either way.

---

## 8. What day one produced, and where it stopped

Three operations dispatched in-platform, all of which had been registered and
never run.

**`audit_per_protein_artifacts`** (job `bbe4918b`). Verdict over 93 results and
279 result-by-setting cells: `both` 63, `grid` 3, `legacy` 213, `absent` 0.
**22 results are fully readable, 71 are rejected.** So the grid-based path
covers under a quarter of the record.

**The six dead-lettered messages are one incident, and the guard held.** All
six are the same job `cd7862b4`, `predict_go_terms_batch` over prot_t5 at depth
30, rejected 2026-08-30 — the residue of the incident `DECLARED-REVISION.txt`
already describes. Its prediction set `c53eda1e` survived SHORT (1,319,713 rows
against its sibling's 2,216,376) but the job is `CANCELLED` and the set carries
**zero evaluations**. No published number rests on it. This is a check that
could have failed and did not, which is what makes it evidence. The messages
were read without consuming them; purging them is a separate decision and they
are currently the receipt.

**`compare_paired_panels` refused, correctly, and that refusal is the finding.**
Dispatched on the sealed five-level depth ladder (prediction set `9995651a`,
composite, `max_sequence_rank` 2/5/10/20/30, verified here as sharing the digest
`f-1c245d41f26ff70c3b0a9247`), it returned `PanelComparabilityError`:

> the two evaluation results do not both declare ['frame', 'temporal_window'],
> so they cannot be shown to share a frame. An unstamped marker is not a
> matching one. This refusal is not waivable by `allow_frame_mismatch`, which
> waives a DISAGREEMENT and not an absence.

**`audit_evaluation_frames`** (job `3dc21cad`) then gave the exact state, and it
is worse than the census reported:

    93 rows, 0 carry a frame, 71 carry a temporal_window, 93 recomputable,
    0 deletable-only
    leakage_role: 90 'select', 3 'probe', 0 'test'

Three things follow.

1. **Not one of the 93 results carries a frame.** Nine successful
   `seal_evaluation_frames` runs did not put one there. Whether sealing alone
   can set it, or whether the audit's "93 re-framable by recompute" means a
   recompute is required, is unresolved and is the next thing to settle — it
   decides whether the census's "cheapest action" is one dispatch or a
   re-evaluation of the whole body.
2. **One window carries two frame digests**, `f-631427d3657ff6c5f71638b8` on 71
   results and `f-1c245d41f26ff70c3b0a9247` on 5, with 17 carrying none. A
   panel level cannot express which, so two arms under one panel name may not
   share a frame.
3. **Nothing in the record is external validation.** 90 of 93 are `select` and
   3 are `probe`; there is no `test`. Everything we hold is selection material,
   which is consistent with holding zero evaluations on the LAFA-comparable
   window.

Day one stopped here on purpose. Sealing or recomputing 93 published rows while
two digests disagree inside one window is a design decision, not a chore, and
the design phase is what this file exists to finish.

### Day two, as agreed

Laptop: `generate_evaluation_set` on v226->v227, and the first GOA load (221).
Sobremesa: the `protea.embeddings.batch` consumer, the structural cohort of
v226->v227, and gates 0 and 1 — real coverage over the whole cohort, and the
positive control that recomputes the lost 66.6 / 20.7 rather than citing it.

**The first declared `experiment_run`: `expand_votes_to_ancestors` false against
true.** One varying field, artifacts that already exist, about seven minutes,
and it exercises declaration, dispatch and read-back against a real paired
floor. It is also the features axis's only reachable second level, which is
`false` on 19 of 19 sets today.

---

## 9. The first measured interval, and what the frame turned out to be

### `frame` was never unwritable. It was undeclared.

Sobremesa established that `seal_evaluation_frames` writes `frame_digest` and
not `frame`, that the two are different columns, and that the auditor's
`re_framable = recomputable - with_frame` subtracts across two populations that
do not speak to each other. All three verified here.

One correction: sobremesa concluded that a recompute would return the same NULL
because nothing in the evaluation path writes `frame`. **`run_cafa_evaluation`
does.** It carries `frame` and `temporal_window` as payload fields with a
validator on the vocabulary (`run_cafa_evaluation.py:242-302`) and returns them
for stamping at line 507; `batch_rescore_evaluation.py:297` does the same. In
581 evaluations nobody ever passed them.

So the fix was neither a mutation of published rows nor a recompute of the
body: **re-run the five ladder evaluations with the frame declared.** Five new
rows through the normal path, additive, about half a minute each.
`internal` is derived rather than chosen: `lafa` denotes the parity-locked
leaderboard-comparable harness, and `COMPARABLE_WINDOW` is v226->v227, so a
220->227 result cannot be that.

### The two digests were one undeclared field

After sealing, the partition is exact:

    f-631427d3657ff6c5f71638b8   temporal_window '220-227'   76 rows
    f-1c245d41f26ff70c3b0a9247   temporal_window NULL        21 rows
    NULL                         unattributable               1 row

The digest partition IS the `temporal_window` partition. The five re-run ladder
rows declared the window and joined the majority frame. So "one window carries
two frame digests" was never two harnesses; it was 21 rows that never declared
which window they were in. The seal is over six fields
(`evaluation_set_id`, `pivot_snapshot_id`, `information_accretion_set_id`,
`temporal_window`, `max_terms`, `max_distance`), and a NULL in one of them
makes a different address.

The one unattributable row is `c5baecef`: its evaluation set or accretion set
is missing, so it can be described and never reproduced.

**And the "9 seals against 480 stratifications" is not a coverage gap.**
`SealEvaluationFramesPayload` has no row selector — only `dry_run` and
`max_examples` — and the operation loops over a table-wide select. One job
seals the whole table, and `dry_run` defaults to true so a provenance rewrite
has to be asked twice. Nine successful jobs are nine full sweeps over ~93 rows.
`stratify_evaluation` takes a prediction set and a result and an axis list, so
it is one job per result per crossing, hence 480. The two counts are not
comparable and neither is evidence about the other.

### The interval

`compare_paired_panels`, 2000 resamples, BCa, seed 0, ia-weighted,
`effect_of_interest` 0.02, against the deepest arm as baseline.

    k=2 vs k=30                          k=10 vs k=30
    panel    delta  [ci_low, ci_high]    delta  [ci_low, ci_high]    mde(10v30)
    NK:MFO  +0.1234 [0.1037, 0.1442]   +0.0440 [0.0337, 0.0558]      0.0164
    NK:BPO  +0.0692 [0.0581, 0.0805]   +0.0269 [0.0202, 0.0343]      0.0104
    NK:CCO  +0.0767 [0.0603, 0.0929]   +0.0344 [0.0255, 0.0446]      0.0142
    LK:MFO  +0.0931 [0.0732, 0.1149]   +0.0395 [0.0293, 0.0553]      0.0194
    LK:BPO  +0.0712 [0.0585, 0.0840]   +0.0318 [0.0247, 0.0403]      0.0116
    LK:CCO  +0.0866 [0.0662, 0.1068]   +0.0319 [0.0200, 0.0426]      0.0161
    PK:CCO  +0.0582 [0.0507, 0.0675]   +0.0230 [0.0190, 0.0276]      0.0063
    PK:MFO  not_computed                not_computed
    PK:BPO  not_computed                not_computed

    resolved 7, refused 0, null_unread 0, underpowered 0, null_with_power 0

Every panel that computed says the shallower arm is greater, and the ordering
is monotone: the gap at k=2 is roughly twice the gap at k=10 on every panel.
The two PK panels were not computed because the artefact is absent for them on
one side, which is the same 22-of-93 readability limit the artifact audit
found, and the operation reports it as `absent` and never as a null.

**This is the campaign's first result that could have come out otherwise.** It
is also the first thing the retriever node could be `measured` on, once a floor
for it exists as an `experiment_run` row.

Two cautions travel with it. The comparison re-selects the operating point on
every resample (`tau_a` 0.57 against `tau_b` 0.59 on PK:CCO, with 26.85 percent
of proteins switching operating point between the two arms), which is exactly
the selection D2 voted to remove; under a fixed declared tau these numbers will
move. And the baseline is one arm of one prediction set, so this measures depth
within `9995651a` and not depth in general.

### Instrumentation owed, and it is the laptop's half

1. `operating_point` must become a declared field on `experiment_run` rather
   than a constant in `compare_paired_panels`, with re-selection as one
   declarable option. Until then D2's decision cannot be expressed.
2. `audit_evaluation_frames` must stop subtracting `with_frame` from
   `recomputable`. The honest quantity is a single query over rows that both
   lack a frame and have reachable parents — and it should not be called
   "re-framable by recomputing", because a recompute only supplies a frame if
   the payload declares one.
3. `seal_evaluation_frames.description` says it stamps `evaluation_result.frame`
   with a content digest. It stamps `frame_digest`, and a digest would violate
   `frame`'s own CHECK. The docstring 130 lines above says so correctly.
4. `frame_digest` has zero references in `protea/infrastructure/`. It is
   reachable only through raw SQL in two files, which is how two operations came
   to disagree about which column the seal lives in.

---

## 10. The first interval was withdrawn as a depth measurement

Sobremesa challenged section 9 on the ground that `rungs.yaml` already warned
this axis can produce "an arithmetic property rather than a finding", and asked
two questions the database answers.

**Question 1: does the ladder's scorer aggregate across neighbours?** Yes.
`scoring_config` `e6beac15` ("composite", linear) carries
`neighbor_vote_fraction: 0.2` alongside `embedding_similarity: 0.4`,
`identity_nw: 0.2`, `identity_sw: 0.1`, `taxonomic_proximity: 0.1`. So it is
branch B, not the zero-weight branch.

**Question 2: is the ladder among the 78 with a broken vote fraction?** Yes,
and barely. On `9995651a`: max 1.9333, **805 rows out of 2,441,584 above 1.0 —
0.033 percent**. For scale, `8a75f84e` reaches 4.9 with 52,398 rows out of
range and `d5b634b2` reaches 4.6 with 52,229. Three orders of magnitude apart.
805 contaminated rows in 2.4 million cannot produce deltas of +0.12.

**But the challenge holds anyway, for a stronger reason than the one raised.**

    _leaf_record_builder.py:435   "neighbor_vote_fraction": vote_count / runner.k_limit
    _base_frame_recount.py:84-87  max_sequence_rank -> DepthCut
    scoring.py:270                reads the STORED neighbor_vote_fraction

The vote fraction is computed **at prediction time**, over the full retrieval,
divided by the retrieval's own `k_limit`, and stored on the row.
`max_sequence_rank` is applied at evaluation time as a `DepthCut` — a filter,
not a rescoring. **So a candidate's score is identical at every cut**, and every
arm of the ladder carries scores that encode a thirty-neighbour neighbourhood.

The five arms are therefore not five retrieval depths. They are one K=30
retrieval, scored once, truncated at five points. Truncating earlier keeps only
the top-ranked candidates, which raises precision at a fixed threshold. That is
the arithmetic property `rungs.yaml` named, and the monotone factor-of-two
pattern fits it exactly as well as it fits a depth effect.

**The interval in section 9 is correctly computed and is withdrawn as a
measurement of the retriever axis.** What it measures is the evaluation-time
truncation of a fixed, fixed-scored candidate list. It is relabelled, not
deleted: it is still the campaign's first paired interval, and the machinery it
exercised — declared frame, seal, BCa intervals, a declared effect of interest,
7 of 9 panels resolved with absences reported as absences — all worked.

Sobremesa's proposed discriminator, matched candidate volume, does not apply
here, because volume is the ONLY thing that differs between these arms. The
real discriminator is two prediction sets built at different `limit_per_entry`,
which is a different retrieval rather than a different cut. Those exist at 10
and 30 and are confounded with `exclude_self_neighbour` and with donor policy
(section 1). **The retriever axis remains unmeasurable in this record.**

### The instrumentation this exposes, and it is the laptop's

The graph's panel `depth` field coalesces three different quantities into one
axis label:

    COALESCE(er.max_sequence_rank || 'seq', er.max_k_position, ps.limit_per_entry)

A retrieval depth, a per-protein rank cut and a per-sequence rank cut are not
three levels of one axis; two of them are reporting cuts over a fixed
retrieval and only the third changes what was retrieved. Rendering them under
one name is the same defect as naming a level by fewer fields than it varies
in, and it is what let a truncation ladder read as a depth ladder.

Added to the laptop's instrumentation queue, now five items:

1. `operating_point` as a declared field on `experiment_run`.
2. `audit_evaluation_frames` must stop subtracting across two populations.
3. `seal_evaluation_frames.description` names the wrong column.
4. `frame_digest` is invisible to the ORM.
5. The `depth` field must name which of the three quantities it carries, and a
   comparison must refuse to cross them.
