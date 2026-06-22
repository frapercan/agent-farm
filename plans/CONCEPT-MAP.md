# PROTEA / thesis concept map (living document)

The complete conceptual map of the project, held and updated at all times. It sits
above the per-track plans (`THESIS-FINISH.md`, `beat-lafa-1/`, etc.) and the
requirements (`REQUIREMENTS.md`): the plans are HOW, this map is WHAT and WHY, and
how every front connects. Built 2026-06-22 from a full read of sparse.pdf, the
PROTEA architecture, the thesis manuscript, the 8-repo Sphinx docs, the memory
stores, MLflow, UI/UX, and the dense/sparse and governance axes. Keep it current as
work proceeds; cite section numbers when planning.

Status legend for fronts: [ok] sound · [partial] in progress · [gap] not started ·
[stale] drifted from reality.

---

## 0. The two stories the thesis must hold (honestly)

- **Engineering / product story.** PROTEA = a hexagonal protein-function-annotation
  platform + the LAFA submission + a per-category LightGBM reranker. CAFA 6 **#19**
  is a TEAM research result (the author was the technical motor), NOT the PROTEA
  product. LAFA: **0.391 offline** (sealed champion, source files deleted) /
  **0.3745 native** (productized, UI-verifiable on `/benchmark`).
- **Scientific story (the horizon, `~/Thesis2/sparse.pdf`).** *The GEOMETRY of a
  representation space governs biological similarity more than the power of the
  model that produced it.* Dense embeddings (cosine) vs Sparse Distributed
  Representations (Tanimoto / k-WTA). The empirical validation arm of that claim
  **is PROTEA's own k-NN GO-transfer benchmark** (sparse.pdf Appendix A): same
  split, same CAFA metrics, only the representation + metric change.

**Unifying insight.** PROTEA is at once (a) the productized #1-class LAFA system and
(b) the empirical engine for a representation-geometry research program. The new
plan unifies them: the dense vs sparse axis is simultaneously a scientific question
and a product lever, validated on the same benchmark, deployed continuously,
governed by controlled entities, surfaced in the UI, written honestly in the thesis.

---

## 1. The empirical engine (the PROTEA pipeline) [ok]

`embeddings (PLM, mean-pool) -> k-NN cosine -> GO transfer (similarity-weighted vote)
-> LightGBM reranker -> cafaeval (NK/LK/PK, IA-weighted f_micro_w)`, under the **D40
leakage-free temporal protocol** (rolling-origin TRAIN/VALID/TEST, `window_role`
marker). Hexagonal, contracts-first; KNN in numpy/FAISS, **never pgvector** (ADR-001,
hard constraint). Concrete components: `EmbeddingBackend` (port) -> `search_knn` ->
`pipeline.predict` (`_tally_query_votes` / `_make_row`) -> `apply_reranker` ->
cafaeval. **This is the dense arm.** Canonical doc: `PROTEA/docs/source/architecture/
system_overview.rst` + `evaluation.rst`.

---

## 2. The DENSE <-> SPARSE axis (the new research core) [gap in thesis]

- Today = dense (ESM2/ProstT5, cosine, mean-pool). SDR arms from sparse.pdf:
  **SDR-A** k-WTA + Tanimoto over the SAME cached embeddings (cheapest, ~1 day,
  readout = overlap-vs-GO-semantic correlation) -> **SDR-B** SimHash / random
  projection -> **SDR-C** learned k-sparse autoencoder -> **SDR-D** structure-derived
  pocket pharmacophore (sequence-invariant).
- **The swap is surgical:** a `metric="tanimoto"` branch in `search_knn` + a k-WTA
  binarisation transform before retrieve. It **plugs in as one more `EvidenceScorer`**
  in the stacked meta-reranker (ADR-D43); the port already exists. Everything
  downstream (vote tally, eval) is untouched.
- **Phased with go/no-go gates** (sparse.pdf Appendix C.3): P0 dense baseline (we
  have it) -> P1 cheap signal (SDR-A) -> P2 OOD by sequence identity -> P3 structure
  ladder -> P4 joint DTI.
- **This is the thesis's forward research chapter** (today: zero occurrences of
  SDR/Tanimoto/k-WTA/pharmacophore in the manuscript). The representation ladder
  (ESM2 -> ProstT5 -> structure-derived -> SDR) maps onto the `protea.backends`
  plugin system; SDR-A/B are orthogonal post-transforms of any rung.
- Source anchors: `protea-method/src/protea_method/knn_search.py` (the metric swap
  site), `pipeline.py` (`predict`), `agent-farm/plans/meta-reranker/ARCHITECTURE.md`
  + ADR-D43 (the EvidenceScorer home).

---

## 3. The product and its continuous local deployment [partial / gap]

The **LAFA container** = the SAME `predict()` that runs in the worker (D23/D15): one
method, not two. **"The data we put in"** = versioned entities (the t0-clean
reference pool, the per-category boosters, the OBO snapshot, the IA file).
**Continuous local deployment with our best benchmark:** the local stack always runs
the current-best configuration, with LAFA `f_micro_w` live on `/benchmark`, exposed
via ngrok (NFR-PROCESS); a CD loop rebuilds container + data as beat-lafa-1 improves
(NFR-PERF: 0.391 is a floor). Precondition: **INT-8** (native seal on `/benchmark`,
blocked on an authorized redeploy). Goal: **FR-3** (the runnable local product) + the
continuous rebuild loop. Anchors: `protea-method/.../method_main.py`,
`PROTEA/docs/lafa/LAFA_SUBMISSION_GUIDE.md`, `agent-farm/plans/lafa-integrate/`.

---

## 4. Governance of features and entities (the control spine) [partial]

- **Single source of truth for features = code:** `protea-contracts/src/
  protea_contracts/feature_schema.py` (`SCHEMA_VERSION` v3 on main, 18 families,
  `ALL_FEATURES`). Any change forces a contracts SemVer major + retrain of every
  booster.
- **Fingerprint `feature_schema_sha`:** guards inference; `SchemaShaMismatchError`
  refuses a booster whose schema drifted (`PROTEA/.../predict_go_terms/
  _reranker_scorer.py`).
- **The ungoverned seam (flag):** IA / self_prior / association / classifier ride the
  `GOPrediction.features` JSONB blob, OUTSIDE the schema-sha; changing them does NOT
  trip the guard. Plus a silent KNN fallback if the contracts import fails.
- **Versioned entities with provenance:** `Dataset` (schema_sha/manifest_sha/
  producer), `RerankerModel` (feature_schema_sha/dataset_id/external_source),
  `OntologySnapshot` (obo_version), `EvaluationSet` (window_role), `Job/JobEvent`
  (audit). This underpins **NFR-REPRO** (a third party gets the same number).
- The real governance GAP is the live JSONB-blob seam above, NOT a thesis number.
  (Checked 2026-06-22: the "52" mentions in the thesis figures + defensa correctly
  label the historical Exp 6 FullFeature run, which was genuinely 52-feature
  pre-interpro; the current canon is correctly 56 in intro/conclusion/appendix_d, and
  the defensa documents the 52->56 bump. No drift; do NOT swap.) Canon = 56 at
  `PROTEA/docs/source/reference/infrastructure.rst:270`; rule: cite `feature_schema.py`,
  never hand-typed numbers.

---

## 5. Offline -> on-platform migration (a first-class direction) [partial]

Everything done offline (lab booster training, the offline champion, the grid
experiments) must move on-platform: every operation UI-actionable (**FR-1**), tracked
(MLflow), with native == offline parity (**NFR-REPRO**). This is the precondition for
the thesis claim "every number is live-verifiable in the app" to become TRUE (today
false for 0.391). Canonical example to migrate: reranker training is a UI dead-end
(`POST /scoring/rerankers/train` returns 405; training decoupled to the lab).

---

## 6. Real state of each front (what "put in order" means)

- **Thesis** [stale]: overstates 0.391 as native/live (abstract, `06_evaluation:803/
  829-835`, `07:117`); Exp 9 `\gridna` + Exp 10 `\TODO`; defensa stale (vN labels,
  residual "CAFA #2", LAFA 0.391 absent); **sparse/SDR entirely absent** (clean
  forward chapter). (52/56 was a false positive: the thesis correctly labels Exp6 as
  52-feature and the canon as 56.) Correct pattern already present: Appendix D = pre-leakage trace,
  marked. Fix philosophy = same as memories: one linear spine, only validated +
  live numbers, dev-trail quarantined + marked in appendices, reflect real method +
  forward direction, kept current as we go.
- **UI/UX** [partial]: training dead-end (405, FR-1); mixed headline metrics
  (`/benchmark` f_micro_w vs `/evaluation` fmax); CIs only on hover (FR-4 partial);
  stale sidebar label; no a11y audit artefact. No orphan pages (good).
- **MLflow** [partial, not gap]: a COMPLETE persistent deployment EXISTS at
  `~/Thesis2/storage/mlflow/` (Postgres `mlflow` DB, 7 experiments / 20 runs, MinIO
  bucket, working `MlflowLogger` client logging params / per-iteration AUC / nested
  per-category runs / artifacts). It is just STOPPED (no supervisor), `MLFLOW_TRACKING_URI`
  not pinned durably, and undocumented in the lab repo. Fix = restart + supervise +
  pin env + lab runbook. Role conceptually = the scientific instrument that tracks
  the representation-comparison experiments.
- **Memories** [stale]: 132 canonical -> target ~30 (14 durable + ~15-20 doc-pointers);
  delete the entire `context/memory/` duplicate store; point each fact at its
  canonical doc (the Sphinx doc-path map, section 10); fix the oversized 31KB index.
- **Repos** [partial]: satellite checkouts behind develop; v1.0 + develop->main
  pending; runners are stubs; no `train_reranker` exists anywhere.

---

## 7. The requirements spine (the organizer of "every front, little by little")

Everything hangs off `REQUIREMENTS.md` -> tracks in `THESIS-FINISH.md`:
- **FR-1** every op UI-actionable · **FR-2** LAFA temporal windows · **FR-3** local
  inference product · **FR-4** confidence intervals.
- **NFR-UI / TEST / INFRA / DOCS / ARCH / PROCESS / PERF / REPRO.**
The new scientific axis (dense<->sparse) extends NFR-PERF / the science spine and
adds the thesis's forward chapter.

---

## 8. The through-line (one sentence)

A scientific question (representation geometry, dense vs sparse) -> validated on
PROTEA's empirical engine (the same leakage-clean k-NN GO-transfer benchmark) -> which
is also the product's lever (#1 LAFA) -> packaged in a container deployed continuously
in local with the best benchmark -> governed by versioned features and entities ->
surfaced and actionable in the UI (the end of offline) -> tracked in MLflow ->
documented with clean pointer-memories -> and written honestly in one linear thesis
with its forward chapter.

---

## 9. Canonical source-of-truth doc map (point memories and the thesis here)

| Topic | Canonical doc |
|---|---|
| Architecture / hexagonal layers / queues | `PROTEA/docs/source/architecture/system_overview.rst` |
| ADR catalog (the "why"; 001-009 + D1-D43) | `PROTEA/docs/source/adr/index.rst` |
| Operations / job dispatch | `PROTEA/docs/source/architecture/operations.rst` |
| Job lifecycle / workers | `PROTEA/docs/source/architecture/job_lifecycle.rst` |
| Data model / ORM | `PROTEA/docs/source/architecture/data_model.rst` |
| Evaluation protocol (NK/LK/PK, math) | `PROTEA/docs/source/architecture/evaluation.rst` |
| cafaeval PK fix + parity | `cafaeval-protea/docs/parity.rst` |
| Contracts / feature schema (authoritative) | `protea-contracts/src/protea_contracts/feature_schema.py` (prose in `docs/source/schema.rst`) |
| LAFA inference pipeline | `protea-method/docs/source/reference/pipeline.rst` + `reference/method_main.rst` |
| LAFA submission ops | `PROTEA/docs/lafa/LAFA_SUBMISSION_GUIDE.md` |
| Reranker training / lab | `protea-reranker-lab` `docs/source/concepts.rst` |
| MLflow deployment | `~/Thesis2/storage/mlflow/README.md` (needs a lab `docs/source/runbooks/mlflow.rst`) |
| Plugin authoring | per-repo `docs/source/contributing.rst` + `PROTEA/docs/source/guides/plugin-authoring/` |
| Deployment / runbooks | `PROTEA/docs/source/runbooks/index.rst` |
| Canonical 56-feature count | `PROTEA/docs/source/reference/infrastructure.rst:270` |
| The science horizon | `~/Thesis2/sparse.pdf` (App. A = validation arm, B = k-WTA+Tanimoto, C = phased plan) |

---

## 10. Open threads / decisions to resolve in the plan

1. Sequencing of the fronts ("little by little"): how to interleave the science
   axis (SDR-A) with the cleanup tracks (thesis-order, memories, MLflow) and the
   product track (INT-8 seal + continuous container).
2. Whether the dense<->sparse program enters the thesis now as a forward-research
   chapter or after P1 produces a first SDR-A signal.
3. The INT-8 redeploy gate (authorized when?) and the native==offline parity target.
4. The ungoverned JSONB-blob feature seam: bring IA/self_prior/association under a
   fingerprint, or document the boundary explicitly.
5. Where MLflow's revival + supervision lands (lab runbook + systemd/compose).
