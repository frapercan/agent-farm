# ROADMAP-NEXT: the unified execution plan (derived from CONCEPT-MAP)

The execution plan for the long-term horizon, derived from `plans/CONCEPT-MAP.md`
(the WHAT/WHY) and organised by `plans/REQUIREMENTS.md` (the FR/NFR spine). Six
tracks run in parallel, little by little; this doc records the tracks, the leading
first slices, the gates, and the two decisions taken 2026-06-22. It sequences the
work that `THESIS-FINISH.md` and `beat-lafa-1/` already started, and adds the new
axes the concept map surfaced (the dense<->sparse science, governance,
offline->platform, the continuous product).

## Decisions (2026-06-22)

- **D-A: run the three fronts in parallel** (fundamentals + science + product) via the
  farm. Cleanup/UI/governance ride alongside.
- **D-B: the dense<->sparse program enters the thesis ONLY when SDR-A produces a
  validated signal** (only validated numbers in the manuscript). Until then it lives
  in CONCEPT-MAP + this plan, not in `chapters/`.

## The six tracks

| Track | Requirement IDs | What | Leading first slice |
|---|---|---|---|
| **T-CIENCIA** (dense<->sparse, NEW) | NFR-PERF, (thesis forward ch.) | The SDR research program (sparse.pdf P0-P4). | **SDR-A**: `metric="tanimoto"` + k-WTA over cached embeddings; overlap-vs-GO correlation as a tracked runner logged to MLflow. |
| **T-PRODUCTO** (continuous LAFA) | FR-2, FR-3, NFR-PROCESS, NFR-PERF | Native seal + container of the best system, continuously deployed locally. | **INT-8 prep + CD design** (the seal is redeploy-gated; do the parity config + container/CD design up to the gate). |
| **T-FUNDAMENTOS / offline->platform** | FR-1, NFR-REPRO, NFR-ARCH | Make the house clean + tracked; migrate offline on-platform. | **MLflow revival**: restart + supervise + pin `MLFLOW_TRACKING_URI` + lab runbook (it EXISTS, just down). Then reranker-training UI surface. |
| **T-GOBERNANZA** (features/entities) | NFR-REPRO, NFR-ARCH | Keep features + entities controlled. | Fix 52/56 drift (cite `infrastructure.rst:270`); decide the JSONB-blob seam (fingerprint IA/self_prior/association or document the boundary). |
| **T-LIMPIEZA** (docs/memory/thesis) | NFR-DOCS | Clean, noise-free, current. | Memories 132->~30 doc-pointers (delete `context/memory/`); thesis-order (drop the native-0.391 overstatement, quarantine, fill Exp9/10). |
| **T-UI/UX** | FR-1, FR-4, NFR-UI | Coherent, accessible, no dead-ends. | Metric coherence (`/benchmark` vs `/evaluation`) + visible CIs (FR-4) + a11y audit. |
| **T-FARM** (dag-scheduler) | NFR-INFRA, NFR-ARCH (farm) | Deterministic, DAG-aware, resource-constrained, node-aware scheduler + autonomous chain dispatch. The structural fix for the autonomy stalls. | F-SCHED campaign (`plans/dag-scheduler/PLAN.md`, ADR `docs/decisions/D34`); reconcile with farm-platform F-FARM-2. Plan-only now; implement next campaign. |

## T-FARM: the DAG-scheduler campaign (autonomy structural fix)

The plan store is already a latent DAG (slices carry `deps`; `plan_parser.find_next`
gates on deps-done). What fails is concurrency + shared-resource safety, which live in
prose, not code (the OOM/DB-wipe/CUDA-OOM incident class). ADR `docs/decisions/D34`
+ `plans/dag-scheduler/PLAN.md` (8 slices, F-SCHED) formalize it: DAG validation,
a lease registry that GENERALIZES `stack_owner.sh` (resources tied to the slice:
exclusive `stack`/`db-write` + quantitative `ram_gb`/`cpu_cores`/`gpu`/`pg_consumers`/
`minio_io`), a node registry (node-aware, laptop-ready), a frontier scheduler (not
top-1), an extended status lifecycle (`in_review`/`failed`/`quarantined`) with failure
isolation, and **F-SCHED.8 autonomous chain dispatch** (a pre-loaded service ApiKey +
pre-declared per-chain authorization, so chains like INT-8 run end-to-end without
step-by-step human OK). Reconcile with farm-platform `F-FARM-2` (schema+tracking
overlaps F-SCHED; cross-reference, do not duplicate; F-SCHED.2 absorbs
`stack_owner.sh` behind a shim). Plan-only now; F-SCHED.1+ is the next campaign.

Motivation, concrete (2026-06-22, the INT-8 run): the GPU run nearly lost to an unsent
human Enter, auth discovered hot (env JWT secret mismatched the live API; the prepared
api-key was stuck at viewer role; a /proc secret-forge attempt was correctly blocked),
and every chain step needed a human OK. F-SCHED.8 closes exactly these without weakening
the per-action security boundaries (the boundaries held all night and should keep
holding; the fix is pre-loaded auth + pre-declared scope, not bypass).

## Leading slices (this cycle, the three in parallel)

### SCIENCE - SDR-A (the cheapest decisive experiment) - DONE, gate NEGATIVE (2026-06-22)
- Readout-1 ran on the SELECT v227 pool (574k ProtT5, t0). Spearman vs GO-semantic:
  dense cosine 0.3153 (Resnik) vs SDR Tanimoto k-WTA 0.2551 (k=128). **Gate NEGATIVE:**
  dense cosine is the stronger biology proxy by ~0.06. Exactly sparse.pdf's Strategy-A
  caveat (naive k-WTA inherits the dense space's miscalibration). PR #96 merged (lab):
  reusable SDR primitives + MLflow-tracked runner (`sdr-a-correlation`) + runbook + 13 tests.
  Stays OUT of the thesis (decision D-B, negative signal). See memory
  `project_sdr_a_result_2026_06_22`.
- **Next science moves (T-CIENCIA continues):** (1) cheap wider-k sweep 256/512 on the same
  runner to confirm the ceiling; (2) **SDR-C** = learned k-sparse autoencoder over cached
  embeddings (the LEARNED arm, where sparse.pdf says the value actually lives) with a
  function/contrastive objective; (3) SDR-D structure arm later (heavier). The `metric="tanimoto"`
  branch in `search_knn` + EvidenceScorer integration (ADR-D43) is only worth building once a
  sparse arm clears the correlation gate.

### PRODUCT - INT-8 prep + continuous-container design
- The native seal on `/benchmark` (full-system row beside the 0.324 baseline) is
  gated on an authorized redeploy. Do the non-gated prep: the predict + eval config
  over the 7401 LAFA frame, the parity check against the offline reference, and the
  design of the CD loop (rebuild container + data to current best, deploy local,
  surface live). Flag the redeploy gate for the maintainer.

### FUNDAMENTALS - MLflow revival + tracking on
- Restart `~/Thesis2/storage/mlflow/start-server.sh`; verify `/health` + the
  `protea-mlflow.ngrok.app` tunnel. Pin `MLFLOW_TRACKING_URI` (and
  `MLFLOW_S3_ENDPOINT_URL`) durably in `~/.secrets/protea.env`. Add a supervisor
  (user systemd unit) so it survives reboot. Add a lab runbook
  `protea-reranker-lab/docs/source/runbooks/mlflow.rst`. This unblocks tracked
  experiments for the science track.

## Gates / risks

- INT-8 native seal needs a maintainer-authorized redeploy (T-PRODUCTO).
- SDR post-proc-style levers must be de-risked on the OFFICIAL eval recipe (the L2
  lesson from beat-lafa-1); feature/representation levers transfer.
- Keep the plan store harmonized: this doc is the umbrella; `beat-lafa-1/` continues
  as the PK-precision reranker campaign under T-PRODUCTO/T-CIENCIA; `meta-reranker/`
  is the architecture; `THESIS-FINISH.md` track content stays valid.

## How this maps to the farm threads

T-CIENCIA + T-PRODUCTO + T-GOBERNANZA + offline->platform run as executor slices;
T-LIMPIEZA (memory/docs) as doc-writer + direct file work; T-UI/UX via
ux-reviewer -> frontend-designer; the thesis-order work via thesis-writer. All
hang off REQUIREMENTS and feed the thesis spine + its forward chapter (gated by D-B).
