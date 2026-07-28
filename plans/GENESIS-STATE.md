# GENESIS STATE: what must exist on the new machine

Third companion to `E2E-CANONICAL-RUN.md` and `SIGNAL-REGISTRY.md`. Written
2026-07-27, before the machine is reformatted, from a six-way audit that located
the code behind every stage of the champion pipeline and classified it.

**The governing principle, in the author's words: artifacts are disposable
because they regenerate; what must survive is the PROCEDURE, integrated in the
platform.** A procedure that lives only as a script under `storage/` is a
capability that dies with the format even if its output was archived.

## 0. The audit's verdict in one paragraph

The **operations layer is healthy**. Ingest, ontology and GOA loading, embedding
computation, reference caching, KNN prediction, feature production, dataset
export and cafaeval scoring are all registered, dispatchable operations with
provenance stamped on their outputs. The **training layer was not**: every
trainer behind the champion was untracked, and several inputs have no producer
anywhere. The gap is not between "documented" and "undocumented", it is between
"the platform can do it" and "one person did it once by hand".

Preservation has now been done (PRs: lab #114, lab #115, agent-farm #234).
**Preservation is not integration**, and the rest of this document is the gap
that remains.

## 1. Missing producers: the procedures that must be WRITTEN

**Nothing is imported. The author's instruction is that the campaign is a clean
run from the most primordial level, and that nothing is kept beyond the
procedures.** This section is therefore not a preservation list. It is a work
list, and every entry is a slice.

Seven artifacts were found with **no producer in any of the eight
repositories**. Under a from-scratch policy each one is regenerable, so the
defect is not the missing file, it is the missing procedure. Ordered by how much
of it has to be written.

| Artifact | What is actually missing | Slice |
|---|---|---|
| **`go_text_emb.npz`** (BioBERT embeddings of GO name + definition) | **A writer for this file exists NOWHERE.** A sweep of every `.py` on the machine found zero. This is the only entry with no code path at all. | Write the producer. It is small: embed name + definition per GO term with the pinned BioBERT, keyed by accession. Without it `build_go_sparse.py` cannot run, so the GO tower and therefore the PK generator cannot be rebuilt |
| **`IA.tsv`** (information accretion per band) | The generator EXISTS (`scripts/compute_ia_for_snapshot.py`) but is a CLI, not a dispatchable operation, so it violates the rule that every operation is UI-actionable. `band_registry.py` also pins the band to a host path. | Promote to an operation; make the band registry point at an operation output rather than a path |
| **`classifier_m2_anc2vec.pt`** (the served M2 head) | No script in any repo saves this file. The training algorithm IS versioned; only the persistence step is not. | Add the checkpoint-saving path to the tracked trainer. Retraining it is the campaign, not a loss |
| **`anc2vec_2020-10.npz`** | A third-party pretrained artifact, re-downloadable from the upstream cited in the loader docstring. The download step appears in no runbook. | Add a fetch step with a checksum |
| **InterProScan 5.77-108.0** | Re-downloadable from EBI. No installer script anywhere; 50 GB acquired by hand. | Write the installer |
| **`predictions_protea.tsv`** | An OUTPUT. It regenerates by running the pipeline. | Nothing to write; it falls out of the clean run |
| **The 8 canonical `EmbeddingConfig` UUIDs** | **Resolved, and the earlier alarm was wrong.** `embedding_config` IS a table in the database dump, so the identifiers are not lost. They remain unversioned as a seed migration, which is a robustness gap rather than a break. | Add a seed migration so the identifiers are declared in code, not only in a dump |

**Consequence for the format: none.** Nothing in this table has to survive the
disk. Six of the seven regenerate from procedures that already exist or from
upstream sources, and the seventh needs a script written that should have
existed anyway.

## 2. Capabilities that were never versioned and must be BUILT

Not lost, because they never existed in versioned form. Each is a slice.

1. **Stratification** (length x category x neighbour identity). A **standing norm
   of the project** with **no implementation anywhere in versioned code**. Every
   stratified table in the campaign came from an ad-hoc script. Axis B of the
   canonical run depends on it entirely.
2. **A window registry.** `band_registry.py` pins v227 to an OBO and an IA file
   as versioned constants with a CI guard. Nothing does the same for the temporal
   windows: TUNE 226 to 227 and COMPETE 227 forward are declared in prose only.
3. **The control family as reusable machinery**: shuffled feature, fixed score,
   random order, matched volume, IA precision. This is what separates a
   measurement from a story, and it was reimplemented per experiment.
4. **The cross-fit gate**: sweep on nine folds, apply blind to the tenth, report
   mean and fold spread. Deterministic protein folding is already a platform
   payload field; the gate around it is not.
5. **Paired bootstrap CIs in the board frame.** Two versioned implementations
   exist; both bootstrap Fmax rather than the headline metric, and neither runs
   inside the board frame.
6. **A row-alignment assertion.** The dict join that silently rewrote 8.3% of
   rows and corrupted two published results is a lesson in memory, not a lint.
7. **The board recipe as a versioned fixture.** The mechanism is a platform
   operation; the parameterisation that reproduces the published number is prose
   in a runbook. No YAML, no fixture, no pinned payload.
8. **IA computation as a dispatchable operation.** Currently a repo script, so it
   violates the project's own rule that every operation is UI-actionable.
9. **End-to-end orchestration.** There is no single dispatch that runs the chain.
   Each stage's output UUID is threaded into the next stage's payload by hand,
   and that sequence exists only in the operator's head.
10. **The registry-to-UI coverage test.** This is the literal acceptance
    criterion of FR-1 and it does not exist, which is why six user-facing
    operations drifted out of the interface.

## 3. Bootstrap order on a bare machine

Phases A and B are host and platform; C onward is the campaign.

**A. Host.** OS packages, Python 3.12, Poetry, Node 20, Docker. Covered by
`agent-farm/scripts/bootstrap-fresh-machine.sh`, which is an **orphan**: no doc
in any repo references it. Then, uncovered by anything: the NVIDIA driver (the
cu128 wheel set assumes it and no script installs or pins it), InterProScan,
the ngrok token and reserved domain, the five crontab entries (now recorded in
`agent-farm/observability/CRONTAB.md`), the `~/.secrets/protea.env` surface of
28 variables (no template, no `.env.example`), and creation of the
`worktrees/protea-deploy` runtime slot, which is **hardcoded in seven scripts**
and created by nothing.

**B. Platform.** Containers and volumes (`docker-compose.yml`), schema
(`init_db.py` + `alembic upgrade head`), services (`manage.sh`), self-heal
(`cold-boot.sh`, and note that **two divergent copies exist with incompatible
flags**; the agent-farm one is canonical and the docs point at the other).

**C. Corpus.** Ingest reviewed Swiss-Prot, fetch metadata, load the ontology
snapshot, load the GOA snapshots, backfill release dates. All class A. Two gaps:
the **exact ingest payload** that produced the corpus is recorded nowhere (the
only documented example is a toy human query), and the **snapshot sweep** that
enumerates version to GAF URL exists in no script, YAML or plan.

**D. Representation.** Compute embeddings for the canonical configs, then apply
the learned encoder head. Blocked on the `EmbeddingConfig` UUID gap above.

**E. Signals and training.** Reference cache, KNN predict and feature
production, co-occurrence, evaluation set, dataset export, then training. The
trainers are now preserved but remain outside the platform by design; the
contract that binds them (Dataset row, `feature_schema_sha`, RerankerModel row)
is strong and survives.

**F. Evaluation.** `run_cafa_evaluation` with the band recipe. Blocked on the IA
artifact.

## 4. What travels: only the procedures

**Superseded framing, corrected 2026-07-28.** This section was written as a
preservation question, which was the wrong question. The governing rule is the
invariant in `CAMPAIGN.md` section 0bis: **every artifact is produced by a
registered operation, lands in the object store, and is published from there.**
Nothing travels because nothing needs to: what does not have a producing
operation is not preserved, it is a defect to be closed, and section 1 above is
therefore the work list rather than an import manifest.

The text below is kept because its inventory is accurate, but read every
"travels" as "is regenerated", and read the safety copies made before the
reinstall as a hedge against total loss that the plan does not depend on and may
not cite.

**The author's instruction, verbatim in intent: erase everything, keep nothing
beyond the procedures. The campaign is a clean run from the most primordial
level.** That is the policy, and this plan is built on it rather than against it.

**Travels as code, and nothing else matters:** the eight repositories, including
the training and research procedures pushed on 2026-07-27 (lab #114, lab #115,
agent-farm #234) and the three planning documents. If a procedure is not in
GitHub it does not exist.

**Travels because it is not code and cannot be rederived from one:** the memory
store, and the operator's own credentials. Everything else is discarded.

**Regenerated, deliberately:** the corpus, every embedding, the reference
caches, the exported datasets, every prediction, every evaluation artifact,
every trained model, and the entire object store. This includes the expensive
things, and that is the point: an embedding set that only exists as a disk image
proves nothing about the procedure that made it.

**The disk layout as it stands** (relevant because it is what the format
destroys): `/home` has no separate partition and lives inside `/`, and the
Docker root is also on `/`, so a system reinstall removes the home tree and
roughly 306 GB of container volumes holding Postgres, RabbitMQ and object
storage. Under the policy above this is the intended outcome, not an incident.
Nothing in the clean-run plan depends on any of it.

## 5. The honest statement of reproducibility

The project's own requirement is that a third party reproduces the work from
public documentation alone. Against that bar, and stated plainly because the
thesis will be examined on it: a third party today would get through the
platform bring-up, stall at the corpus definition, and stop at the IA table and
the GO text embeddings. The end-to-end reproduction guide targets a frame two
campaigns old.

That is a fixable gap, and the fix is the list in section 2. It is also the
strongest argument for doing the clean run at all: **the run is what proves the
procedure, and the procedure is the contribution.**

---

## 6. What now exists in the platform (2026-07-28)

Five of the missing procedures stopped being descriptions and became code with
guards. Each is stated here by what it REFUSES, because that is the part that
survives contact with a tired operator at four in the morning.

**The pool identity is one value.** The reference cache is keyed by what the
cached pool contains, donor restriction included, and the identity cannot be
passed in part. This branch had already applied the restriction to the read
path and missed the write path, which stores a restricted pool under the
unrestricted name; bundling the identity makes that impossible to express.

**The temporal splits refuse to guess.** An unknown split raises and names the
ones that exist. A split whose windows are not chosen yet raises rather than
returning a placeholder, because a placeholder propagates into results that
look decided. The validation split may inform nothing, enforced at the call
rather than asserted in prose, and the adjustment set is cut off strictly
before the window the board scored.

**Ground truth is first appearance.** An annotation counts only if it was never
present at any earlier cut. Too little history raises rather than falling back
to the endpoint difference. The restoration rate is measured and reported per
sub-ontology, because the leak tracks the contraction points and the validation
series crosses one.

**The four axes refuse to pool.** Combining across strata requires the
population sizes, and there is no unweighted variant to reach for. Length
boundaries are the model context limits rather than corpus quantiles, and the
homology axis is crossed with donor provenance rather than standing alone.

**A join cannot lose rows silently.** Helpers that state the expectation and
fail when the data disagrees, plus a narrow check in the lint pipeline.

### Two findings this produced

**The adjustment set is not yet expressible.** With the releases the campaign
currently enumerates there are NO candidate windows at all: the table begins at
the comparable window's own start, so nothing earlier exists to select on. The
preceding releases have to be ingested before a champion can be chosen. The
registry reports this through a function the caller can gate on rather than
leaving it to be discovered mid-run.

**A join in the feature path depended on list order.** Indexing a group's leaf
predictions by term kept whichever record arrived last, so which row survived
could differ under another batch size or worker count. It now keeps the
closest, which is deterministic and is what the surrounding expansion already
assumed.

### What remains blocked

The query-side donor filter, on the contract fork recorded as an open author
decision. It must read the policy the caller sent, and that policy is a
contract type the platform cannot currently resolve.
