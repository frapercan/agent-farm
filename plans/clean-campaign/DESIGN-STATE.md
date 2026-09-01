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
