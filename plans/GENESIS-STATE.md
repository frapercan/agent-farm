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

## 1. Cannot be regenerated: must be imported or rebuilt

These have **no producer in any of the eight repositories**. Losing the file
means losing the capability, not just the artifact. Ordered by consequence.

| Artifact | Status | What it blocks |
|---|---|---|
| **`go_text_emb.npz`** (BioBERT text embeddings of every GO term) | **NO WRITER EXISTS.** A sweep of every `.py` on the machine for a writer of this file found zero. | The GO tower of the two-tower, therefore the PK generator that wins PK-MFO and PK-CCO. `build_go_sparse.py` is tracked but cannot run without it. **The most consequential single loss in the audit.** |
| **`IA.tsv`** (v227 band, 39,906 terms) | Host file in a gitignored directory. `band_registry.py` pins the band to it and **explicitly rejects** the tracked alternative. | The weights behind every `f_micro_w` in the thesis. `scripts/compute_ia_for_snapshot.py` can regenerate one, but it is a CLI, not a dispatchable operation, and its output is not byte-identical to the pinned file. |
| **`classifier_m2_anc2vec.pt`** (160 MB, the default served M2 head) | **NO PRODUCING CODE FOUND** anywhere, in any repo or under `storage/`. | The live serve fallback for the NK/LK classifier. An orphan artifact whose producer was never written down. |
| **`anc2vec_2020-10.npz`** (32 MB) | Third-party pretrained artifact, no builder anywhere. Upstream cited in a docstring. | The M2 classifier label basis and the whole `anc2vec_*` feature family, which the LOFO shows carries PK. Re-obtainable, but the download step is recorded in no runbook. |
| **`predictions_protea.tsv`** (the champion board submission) | **Already gone.** No repo ever tracked it. | The headline PK-BP figure. A reconstruction script exists and says so in its own docstring. |
| **InterProScan 5.77-108.0** (50 GB) | Acquired by hand, gitignored, **no installer script anywhere**. | The InterPro2GO BP graft, which is +0.0179 on the nine-cell mean. |
| **The 8 canonical `EmbeddingConfig` UUIDs** | Database rows, **no seed migration**. | **The ID graph.** On a clean database Postgres mints new UUIDs, so every payload, config pin and env var that names `d8979601` breaks. This is a silent, total break. |

**Consequence for the format:** items 1 to 5 are preserved as files in
`/mnt/protea-archive/archive/preformat-preserve-2026-07-27_preformat`. They must
travel to the new machine as **imports**, and each one that lacks a producer
should acquire one before the clean run claims reproducibility.

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

## 4. What regenerates and what travels

**Regenerates, do not carry:** every embedding, every reference cache, every
exported dataset, every prediction, every evaluation artifact, all derived
parquet and npz. This is the bulk of the 55 GB under `storage/` and the 44 GB of
`datasets` and `eval_artifacts` in object storage. The author's instruction is
explicit: results are not preserved, they are regenerated.

**Travels as an import:** the seven artifacts in section 1, the secret and
config surface, and the memory store.

**Travels as code:** everything now on GitHub, including the procedures
preserved today.

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
