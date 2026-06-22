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

## Leading slices (this cycle, the three in parallel)

### SCIENCE - SDR-A (the cheapest decisive experiment)
- Add a `metric="tanimoto"` branch to `protea-method/.../knn_search.py` (binary
  matmul intersection over fixed-k active sets) + a k-WTA binarisation transform of
  the cached embedding matrix.
- Build the readout-1 analysis as a TRACKED runner (not a /tmp script): sample
  protein pairs; correlate (i) dense cosine, (ii) SDR Tanimoto, (iii) GO semantic
  similarity (Resnik/Lin over the DAG). Log params + Spearman to MLflow.
- Gate: if SDR overlap correlates with GO semantics at least as well as dense cosine,
  proceed to the full SDR-A k-NN arm on `/benchmark`; else record the negative
  cleanly. De-risk leakage-clean on the SELECT window first.
- Reuses: cached embeddings (`SequenceEmbedding`), the GO DAG + anc2vec, cafaeval.
  Plugs in later as an `EvidenceScorer` (ADR-D43).

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
