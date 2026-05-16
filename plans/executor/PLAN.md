# executor — Plan

Technical implementation slices for the PROTEA stack. Migrated from
PROTEA master plan v3.2 §24 ("Ruta corta priorizada por leverage") +
LAFA delta §23 + the D1-D30 decisions registry. Each slice has a `phase`
matching the original plan's fase numbering.

## Phase semantics

| Phase | Theme | Notes |
|---|---|---|
| F1 | Quick wins + parameter objects | autónomas, paralelizables, 5-7 días |
| F2 | F2C wire complete | gates F-LAFA v2 |
| F3 | F1 close + F2B | feature registry + parquet refactor |
| F4 | F3 + F4 model + API | API hardening, ExperimentRun ORM |
| F5 | F-OPS + F5 observability | OTel, Prom, Grafana, deployment |
| F6 | F-EXP + F-RESEARCH | narrative campaigns, lineage wire, GeOKG |
| F7 | F-LAFA v2 reanudación | bind-mount containers per LAFA contract |
| F8 | Cierre | tests final, docs final, defensa support |

Hard constraints (apply to every slice):
- `develop` is the integration trunk; PRs land via review + status checks
- Local-first CI: ruff + mypy + pytest BEFORE push
- Smell budget enforced by `scripts/check_smells.py` (file <800, class <500, method <60, params <6)
- No `git stash`, no force-push to main/develop, no `--no-verify`
- No "Co-Authored-By: Claude" in commits

## F1 — Quick wins autónomas

### T2D.2 — run_cafa_evaluation cleanup

```yaml
id: T2D.2
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  run_cafa_evaluation.py <500 LOC
  Helper functions extracted into submodules
  Tests green; no functional change
estimated_hours: 6
priority: P1
tags: [refactor, smell-budget, F2D-debt]
note: "[succeeded via PROTEA PR #310 @ 2026-05-12T08:01:05Z]"
```

Shipped via PR #310 2026-05-12.

### T2D.3 — services LOC cleanup

```yaml
id: T2D.3
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  protea/api/services/scoring_service.py <500 LOC
  protea/api/services/embeddings_service.py <500 LOC
  router tests green; no API-surface change
estimated_hours: 8
priority: P1
tags: [refactor, smell-budget, F2D-debt]
```

Merged PR #344 2026-05-12.

### T-CONTEXTS — Introduce Parameter Object

```yaml
id: T-CONTEXTS
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  KnnContext, FeatureBuildContext, ExportContext live in protea-contracts.contexts
  no productive function signature >6 args
  protea-contracts bumped to v0.2.0 (semver minor)
estimated_hours: 0
priority: P1
tags: [refactor, parameter-object, contracts]
note: "2026-05-17 janitor reconcile: confirmed shipped via PROTEA PR #270 (2026-05-09)"
```

Verified done 2026-05-11: protea-contracts v0.2.0 ships
`KnnContext` / `FeatureBuildContext` / `ExportContext` in
`src/protea_contracts/contexts.py:58,88,120` with tests in
`tests/test_contexts.py`. PROTEA callers refactored: `_knn_transfer_and_label`
and `run_knn_transfer_and_label` take `ctx: KnnTransferContext` (≤5 args);
`export_reranker_parquets(ctx: ParquetExportContext)` is 1 arg.
Original targets `_dump_frozen_dataset` / `_predict_batch` were dissolved
by the T2B.5 Method Object refactor.

### T1.7 — invariant tests cross-repo

```yaml
id: T1.7
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  Cross-repo invariants asserted in tests/test_contracts_invariants.py
  CI matrix runs against latest tagged versions of each plugin repo
estimated_hours: 6
priority: P2
tags: [tests, contracts]
note: "2026-05-16 janitor reconcile: shipped via PR #371 (2026-05-15)"
```

Shipped via PR #371 2026-05-15.

### T1.8 — boundary validation

```yaml
id: T1.8
phase: F1
loop: executor
status: done
deps: [T1.7]
acceptance: |-
  Pydantic schemas reject malformed payloads at every operation entry-point
  Contract tests cover at least one negative case per payload
estimated_hours: 4
priority: P2
tags: [tests, contracts]
note: "2026-05-16 janitor reconcile: shipped via PR #372 (2026-05-15)"
```

Shipped via PR #372 2026-05-15.

### T2A.1 — esm backend entry_point

```yaml
id: T2A.1
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  protea-backends.esm registers protea.backend.esm via entry_points
  PROTEA compute_embeddings dispatches to plugin (not inline if-branch)
  Bit-exact embeddings vs the inline implementation on a 100-protein smoke set
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
note: "[succeeded via PROTEA PR #312 @ 2026-05-12T08:18:52Z]"
```

### T2A.2 — t5 backend entry_point

```yaml
id: T2A.2
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  Same shape as T2A.1, for ProtT5
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
note: "[succeeded via PROTEA PR #313 @ 2026-05-12T08:36:01Z]"
```

### T2A.3 — ankh backend entry_point

```yaml
id: T2A.3
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  Same shape as T2A.1, for Ankh
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
note: "[succeeded via PROTEA PR #316 @ 2026-05-12T08:46:48Z]"
```

### T2A.4 — esm3c backend entry_point

```yaml
id: T2A.4
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  Same shape as T2A.1, for ESM-3C
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
note: "[succeeded via PROTEA PR #320 @ 2026-05-12T09:36:21Z]"
```

### T2A.5 — backend registry dispatch

```yaml
id: T2A.5
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  compute_embeddings.py:328-471 uses name-based registry dispatch
  no more inline if model_backend == ... cascade
estimated_hours: 0
priority: P2
tags: [refactor, plugin]
note: "[succeeded via PROTEA PR #322 @ 2026-05-12T11:01:11Z (T2A.5b consolidation)]"
```

### T2A.8 — knn + baseline runners entry_points

```yaml
id: T2A.8
phase: F1
loop: executor
status: done
deps: []
acceptance: |-
  protea-runners.knn + protea-runners.baseline registered via entry_points
  PROTEA dispatches by name, not import path
estimated_hours: 4
priority: P3
tags: [refactor, plugin, runner]
note: "2026-05-16 janitor reconcile: shipped via PR #240 + #243"
```

Shipped pre-session via PROTEA #240/#243 + protea-runners 48e2770.

### T-CI.DEPLOY-SKIP — Companion skip-job so deploy slice check satisfies required-status on non-deploy PRs

```yaml
id: T-CI.DEPLOY-SKIP
phase: F1
loop: executor
status: done
deps: []
target_repo: PROTEA
target_branch: develop
acceptance: |-
  Required check `deploy slice builds and smokes` reports success on a PR
  that touches ONLY paths outside the deploy-e2e.yml filter
  (e.g. apps/web/** only, README only, agent-farm only).
  Existing trigger behaviour preserved: a PR that touches Dockerfile,
  protea/**, docker/**, alembic/**, scripts/worker.py,
  scripts/test_deploy_e2e.sh, poetry.lock, pyproject.toml, or
  .github/workflows/deploy-e2e.yml still runs the full 25-min Docker E2E.
  Implementation strategy: add a companion job (same workflow or new
  workflow file) that triggers via `paths-ignore` mirroring the existing
  paths filter, has the same job name `deploy slice builds and smokes`,
  and is a no-op (`run: echo "skip: no deploy-relevant paths changed"`).
  Local CI green; PR opened against develop; check shows green on the
  fix PR itself (which DOES touch the workflow file so the full E2E runs).
context: |-
  Discovered 2026-05-15 via PR #369 (T-WEB.LOADING). Branch protection on
  develop requires `deploy slice builds and smokes`, but `deploy-e2e.yml`
  has a `paths:` filter excluding `apps/web/**`. Any frontend-only or
  docs-only PR stalls on "Expected - Waiting for status to be reported"
  forever. PR #369 is the live blocker; this slice unblocks it AND every
  future non-deploy PR.
  Canonical GitHub Actions pattern: two triggers with mirrored
  paths / paths-ignore producing the same check context name. The
  required-status gate accepts either run.
  Keep diff tiny: one new workflow file (or one new job) plus minimal
  YAML. NO refactor of the existing deploy-e2e.yml job.
estimated_hours: 1
priority: P0
tags: [ci, github-actions, branch-protection, unblocker]
```

Shipped via PR #370 2026-05-15.

### T-WEB.LOADING — Next.js loading.tsx for navigation feedback

```yaml
id: T-WEB.LOADING
phase: F1
loop: executor
status: done
deps: []
target_repo: PROTEA
target_branch: develop
acceptance: |-
  apps/web/app/[locale]/loading.tsx exists and renders a Skeleton scaffold
  (heading + main content block) using the existing Skeleton component
  Manual verification: navigating from one [locale]/* page to another
  shows the Suspense skeleton instantly (no frozen previous page) under
  the production build (npm run build && npm start)
  Local CI green: npm run lint + npm run typecheck + npm run test
  PR opened against develop, branch protection respected, no co-author
  trailer, no force-push
context: |-
  User reported 2026-05-15 that first navigation to /es/benchmark, /es/evaluation
  and similar routes feels frozen for 1-3s. Root cause: every page under
  apps/web/app/[locale]/ is a "use client" component fetching via useEffect,
  so the inner Skeleton (e.g. benchmark/page.tsx:289-294) only mounts after
  the route chunk downloads, parses and hydrates. App Router shows a
  loading.tsx INSTANTLY via auto-Suspense; a single file at the [locale]/
  segment covers every child route via segment inheritance, optional
  per-segment overrides if a child needs a different shape.
  Backend latency itself is acceptable per the user; only the feedback gap
  needs fixing. Keep the change tiny and focused, no refactor of the existing
  client-side data flow.
estimated_hours: 2
priority: P2
tags: [frontend, web, ux, next-app-router]
```

Shipped via PR #369 2026-05-15.

## F2 — F2C wire complete

### F2C.5a — protea-method pipeline.predict() output-shape extension

```yaml
id: F2C.5a
phase: F2
loop: executor
status: done
deps: []
acceptance: |-
  protea_method.pipeline.predict() emits PROTEA-compatible prediction rows
  (prediction_set_id, ref_protein_accession, qualifier, evidence_code, plus
  reranker-feature aggregates: vote_count, k_position, go_term_frequency,
  ref_annotation_density, neighbor_distance_std, neighbor_vote_fraction,
  neighbor_min_distance, neighbor_mean_distance)
  Accepts per-pair alignment/taxonomy feature maps via pipeline ctx
  protea-method bumped to semver minor; unit tests in tests/test_pipeline.py
  cover every new field
estimated_hours: 0
priority: P0
tags: [F-LAFA-gate, predict, F2C, protea-method]
note: "[succeeded via protea-method PR #9 @ 2026-05-11T09:09:12Z; release #10 @ 2026-05-11T09:18:28Z]"
```

Done 2026-05-11. Shipped in protea-method PR #9 (merged to develop) plus
release PR #10 (merged to master at commit `3a05fd8`, version 0.3.0). PROTEA
consumes via the existing `branch = "master"` pin once `poetry update
protea-method --lock` is run. Donor selection uses the closest voting ref
per `(query, go_term)` for `qualifier` / `evidence_code` / pair_features
propagation (equivalent to PROTEA's first-ref-in-KNN-order for cosine since
neighbours come back sorted). `prediction_set_id` lives on `PredictConfig`,
not as a kwarg, to keep the pre-existing 14-arg offender from worsening
(release merge later took it to 15 via PR #8's `return_diagnostics`).

### F2C.5b — PROTEA predict_go_terms_batch delegation

```yaml
id: F2C.5b
phase: F2
loop: executor
status: done
deps: [F2C.5a]
acceptance: |-
  PROTEA _predict_batch / _run_aspect_separated_knn delegate to
  protea_method.pipeline.predict()
  PROTEA orchestrator body <200 LOC; ancestor expansion + reranker
  feature_schema_sha validation + chunking remain inline
  Bit-exact predictions vs current inline path on a golden parquet fixture
estimated_hours: 0
priority: P0
tags: [F-LAFA-gate, predict, F2C]
```

Done 2026-05-11 via PROTEA PR #275 (merged 09:43 UTC).
Orchestrator body landed at **53 LOC** (target <200). `_predict_batch`
dissolved entirely; `_AspectSeparatedKnnRunner` collapsed into a 18-LOC
`_run_aspect_separated_knn` + 3 module-level helpers + `_AspectKnnPreSearch`
for per-aspect KNN scoping. `_UNIFIED_REF_KEY = "__unified__"` sentinel
shares the unified ref pool with `pipeline.predict(aspect_separated=True)`
without a second DB round-trip. File LOC: 2305 → 2026 (−279). Bit-exact
regression on a 2-query/4-ref/3-aspect in-memory fixture. F-LAFA v2
inference gate cleared: containers can now infer via `pipeline.predict()`.

## F3 — F1 close + F2B

### T1.6 — schema_sha v2 migration

```yaml
id: T1.6
phase: F3
loop: executor
status: done
deps: []
acceptance: |-
  Dataset + RerankerModel have schema_sha_v2 column populated
  Backfill from protea_contracts.compute_schema_sha verified
  Old schema_sha column kept until F8 cleanup
estimated_hours: 8
priority: P1
requires_human: true
tags: [migration, alembic]
note: "[succeeded via PROTEA PR #352 @ 2026-05-12T20:48:21Z (ADR D10 dry-run)]"
```

D10 accepted 2026-05-06. Shipped via PR #352 (dry-run on dev DB); hard migration
blocked on live DB window (requires_human). PR #391 (FARM-EXP.5) extends schema_sha_v2
with hard-fail guard on feature mismatch.

### FIX-EXP-RUN-ENUM — ExperimentRun status enum case mismatch

```yaml
id: FIX-EXP-RUN-ENUM
phase: F3
loop: executor
status: done
deps: []
acceptance: |-
  ORM Enum(ExperimentRunStatus) maps cleanly to the DB lowercase values
  ('planned', 'running', 'succeeded', 'failed', 'killed').
  A regression test inserts a row via plain session.add(ExperimentRun(...))
  and selects it back, with no LookupError / InvalidTextRepresentation.
  The FARM-EXP.1 backfill script's sqlalchemy.text workaround can be
  replaced by ORM idioms without breakage (verify by re-running it).
estimated_hours: 2
priority: P0
tags: [orm, schema, bug-fix]
requires_human: false
```

Shipped via PROTEA PR #389 (2026-05-16). ORM-side `values_callable` on
ExperimentRunStatus enum column to send `.value` (lowercase) instead of
`.name` (uppercase), resolving DB mismatch. Regression test added.

### T2B.1 — FeatureRegistry implementation

```yaml
id: T2B.1
phase: F3
loop: executor
status: done
deps: [T-CONTEXTS]
acceptance: |-
  protea/core/features/ package with FeatureRegistry abstraction
  Each feature family (alignment, taxonomy, anc2vec, lineage, ...) registered
  parquet_export consumes the registry, not inline compute
estimated_hours: 16
priority: P1
tags: [refactor, registry, features]
note: "[succeeded via PROTEA PR #277 @ 2026-05-11T11:18:31Z]"
```

### T2B.2 — parquet_export refactor

```yaml
id: T2B.2
phase: F3
loop: executor
status: done
deps: [T2B.1]
acceptance: |-
  parquet_export delegates feature compute to FeatureRegistry
  Golden parquet bit-exact gate passes
estimated_hours: 6
priority: P1
tags: [refactor, parquet, features]
note: "[succeeded via PROTEA PR #280 @ 2026-05-11T11:44:06Z]"
```

### T2B.3 — _predict_batch decompose

```yaml
id: T2B.3
phase: F3
loop: executor
status: done
deps: [T2B.1]
acceptance: |-
  _predict_batch decomposed using FeatureRegistry
  Predictions bit-exact vs pre-refactor on regression set
estimated_hours: 0
priority: P1
tags: [refactor, predict, features]
```

Superseded by F2C.5b (2026-05-11, PR #275): `_predict_batch` was dissolved
entirely by the delegation to `protea_method.pipeline.predict()`; the
remaining orchestrator body is 53 LOC. Bit-exact regression covered by the
F2C.5b fixture. FeatureRegistry-based decomposition (T2B.1) is no longer
needed for this entry point.

### T2B.4 — extract class on reranker pipeline

```yaml
id: T2B.4
phase: F3
loop: executor
status: done
deps: [T2B.3]
acceptance: |-
  Reranker scoring path lives in a dedicated class with single responsibility
estimated_hours: 8
priority: P2
requires_human: true
tags: [refactor, reranker]
note: "[succeeded via PROTEA PR #385 @ 2026-05-16T15:38:08Z]"
```

Shipped via PROTEA PR #385 (2026-05-16). RerankerScorer extracted as
compositive class (not mixin); regression test on bench-v1-K5-v226-lineage
confirms Fmax stability. Depends on T2B.6 merge (PR #384, same day).

### T2B.5 — Method Object for 300+ LOC methods

```yaml
id: T2B.5
phase: F3
loop: executor
status: done
deps: []
acceptance: |-
  No productive method >60 LOC in predict_go_terms.py / run_cafa_evaluation.py
  / training_dump_helpers.py
estimated_hours: 0
priority: P1
tags: [refactor, method-object]
```

Closed via PRs #162, #169, #170, #177, #267 (verified 2026-05-09 via AST).

### T2B.6 — split predict_go_terms.py + training_dump_helpers.py into submodules

```yaml
id: T2B.6
phase: F3
loop: executor
status: done
deps: [T2B.5]
acceptance: |-
  protea/core/operations/predict_go_terms.py <800 LOC
  protea/core/training_dump_helpers.py <800 LOC
  .smell-baseline.json entries for both files removed
  OperationRegistry surface unchanged: predict_go_terms / predict_go_terms_batch
  still registered under same names with same payload contract
  Predictions bit-exact vs pre-split on regression fixture (F2C.5b dataset)
  Existing imports kept via re-exports in the original module path; no
  consumer-side breakage in PROTEA + protea-method + protea-reranker-lab
estimated_hours: 8
priority: P2
tags: [refactor, smell-budget, file-split]
```

Shipped via PROTEA PR #384 (2026-05-16). Files split into submodules under
`protea/core/operations/predict_go_terms/` and `protea/core/training_dump/`;
original paths kept as thin re-export shims. All acceptance criteria met:
both files now <800 LOC, baseline entries removed, predictions bit-exact,
zero consumer breakage in PROTEA + protea-method + protea-reranker-lab.

## F4 — F3 + F4 model + API

### T3.1-T3.4 — GOPrediction JSONB dual-write

```yaml
id: T3.1
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  GOPrediction features moved to JSONB column with dual-write transition
  Old columns kept until F8 cleanup
estimated_hours: 12
priority: P1
requires_human: true
tags: [migration, jsonb, alembic]
note: "[succeeded via PROTEA PR #299 @ 2026-05-11T19:33:46Z (T3.1a features JSONB dual-write)]"
```

D3 accepted. Partial implementation T3.1a (GOPrediction features JSONB dual-write)
shipped via PR #299 2026-05-11. Full migration window still pending.

### T3.5 — index audit

```yaml
id: T3.5
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  Every PG index audited; redundant indexes dropped via migration
  Frequent slow queries (>500ms in dev) covered by an index
estimated_hours: 4
priority: P3
tags: [migration, performance]
note: "Done 2026-05-12 via PR #340 (merged)"
```

### T3.6 — nullables audit

```yaml
id: T3.6
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  Every nullable column reviewed; spurious NULLs constrained via NOT NULL
  Migration covers data + schema with backfill where needed
estimated_hours: 4
priority: P3
tags: [migration, schema-quality]
```

Merged PR #347 2026-05-12.

### T3.8 — ExperimentRun ORM

```yaml
id: T3.8
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  experiment_run table + ORM model + tests
estimated_hours: 0
priority: P1
tags: [orm, narrative]
```

Done in T58 (2026-05-09).

### T3.9 — Job narrative fields

```yaml
id: T3.9
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  Job has description, findings, tags fields with API + tests
estimated_hours: 0
priority: P2
tags: [orm, narrative]
```

Done in T55.

### T3.10 — JobComment ORM + endpoints

```yaml
id: T3.10
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  job_comment table + ORM + POST/GET endpoints + tests
estimated_hours: 0
priority: P2
tags: [orm, narrative]
```

Done in T56.

### T3.11 — capture_provenance helper

```yaml
id: T3.11
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  capture_provenance() helper used by every operation that creates artefacts
  Provenance dict on Dataset/RerankerModel/PredictionSet
estimated_hours: 0
priority: P2
tags: [provenance]
```

Done in T57.

### T4.x — API hardening

```yaml
id: T4.x
phase: F4
loop: executor
status: done
deps: []
acceptance: |-
  /v1/ prefix universal; cursor pagination; RFC7807 problem details;
  OpenAPI tightening; Schemathesis; narrative endpoints
estimated_hours: 0
priority: P1
tags: [api, hardening]
```

Done across T59-T68 (2026-05-09). 100% v1 op + 100% user-schema description coverage.

## F5 — F-OPS + F5 observability

### T5.1 — OTel FastAPI + SQLAlchemy + pika instrumentation

```yaml
id: T5.1
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  OTel SDK initialised at process start; spans on every request, every SQL,
  every AMQP publish/consume
  Traces exported via OTLP to a configurable endpoint
estimated_hours: 12
priority: P2
tags: [observability, otel, D7]
note: "[succeeded via PROTEA PR #325 (T5.1a boot) @ 2026-05-12T13:47:07Z; PR #330 (T5.1b instrumentation) @ 2026-05-12T14:05:42Z]"
```

D7 accepted 2026-05-06.

### T5.2 — Prom /metrics endpoint

```yaml
id: T5.2
phase: F5
loop: executor
status: done
deps: [T5.1]
acceptance: |-
  /metrics exposes process + custom counters/histograms
  Standard PROTEA metric names documented in docs/observability.rst
estimated_hours: 6
priority: P2
tags: [observability, prometheus, D7]
note: "[succeeded via PROTEA PR #346 @ 2026-05-12T18:14:21Z (redo)]"
```

### T5.3 — Grafana dashboards

```yaml
id: T5.3
phase: F5
loop: executor
status: done
deps: [T5.2]
acceptance: |-
  3 dashboards in deploy/grafana/: jobs, queues, predictions
  Provisioning via docker-compose.monitoring.yml
estimated_hours: 8
priority: P3
tags: [observability, grafana]
note: "[succeeded via PROTEA PR #332 @ 2026-05-12T14:08:31Z]"
```

### T5.4 — Loki via loki-docker-driver

```yaml
id: T5.4
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  All container logs ship to Loki via loki-docker-driver
  Grafana dashboard queries log streams by container/service
estimated_hours: 4
priority: P3
tags: [observability, loki]
note: "[succeeded via PROTEA PR #339 @ 2026-05-12T14:33:49Z]"
```

### T5.5 — CORS allowlist

```yaml
id: T5.5
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  PROTEA_ALLOWED_ORIGINS env var; CORSMiddleware locked down in prod
estimated_hours: 0
priority: P2
tags: [security, cors]
note: "[pre-existing wildcard handling + tests via PROTEA PR #393 @ 2026-05-16T22:13:30Z]"
```

Pre-existing in T61 (CORS allowlist middleware); PR #393 (post-2026-05-16) adds
wildcard handling and tests. Layer is production-ready.

### T5.6 — authn middleware (ApiKey + Bearer + slowapi)

```yaml
id: T5.6
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  ApiKey ORM + Bearer middleware + slowapi rate limit
  oauth2-proxy in deploy/nginx/ for human OIDC
  (delivered via PR #296 (T5.6a API key) and PR #303 (T5.6b Bearer JWT) on 2026-05-11..2026-05-12)
estimated_hours: 12
priority: P1
requires_human: true
tags: [security, authn, D6]
```

D6 accepted 2026-05-06; both PRs merged after human review: PR#296 (T5.6a API key ORM) 2026-05-11T19:33:27Z, PR#303 (T5.6b Bearer JWT + slowapi) 2026-05-12T08:00:09Z. Security audit completed; authentication middleware now live in production.

### T5.7 — pip-audit + bandit blocking CI

```yaml
id: T5.7
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  security.yml without || true; pip-audit + bandit gate PRs
estimated_hours: 0
priority: P1
tags: [security, ci]
```

Done in T62 (2026-05-09).

### T-OPS.1 — Dockerfiles per plugin repo

```yaml
id: T-OPS.1
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  protea-{contracts,method,sources,backends,runners,reranker-lab,cafaeval}
  each ship a Dockerfile + tagged image on ghcr.io
estimated_hours: 0
priority: P2
tags: [deployment, docker]
```

Done 2026-05-11. 7 PRs landed in one executor turn:
protea-contracts #6, protea-method #11, protea-sources #5, protea-backends #5,
protea-runners #5, protea-reranker-lab #6, cafaeval-protea #4. Template
shape: python:3.12-slim base + multi-stage builder/runtime split; Poetry
2.3.2 for the 5 poetry repos (bumped from PROTEA's 2.1.0 which fails to
resolve protea-method's transitive graph); pip+setuptools for
reranker-lab and cafaeval-protea; `libgomp1` at runtime where
numpy/lightgbm/faiss need it; ca-certificates for repos that fetch
upstream. `.github/workflows/docker.yml` per repo: actions/checkout@v4 +
setup-buildx@v3 + login-action@v3 + metadata-action@v5 +
build-push-action@v6, tagging ref-branch / ref-tag / semver / sha-short /
latest-on-default. Images namespace: `ghcr.io/frapercan/<repo>:<tag>`.

Follow-up debt flagged:
- `protea-method` `pyproject.toml` pins `protea-contracts` to
  `branch="master"` which does not exist on the remote (only `develop`).
  Poetry 2.3.2 happens to resolve it, but should be patched.
- `protea-backends` image ships only the slim plugin scaffold (no
  torch / transformers / esm). The backend-specific image with extras
  baked in is intentional T-OPS.12 work.

### T-OPS.2 — protea-bundle docker-compose

```yaml
id: T-OPS.2
phase: F5
loop: executor
status: done
deps: [T-OPS.1]
acceptance: |-
  Single docker-compose.bundle.yml spins up the full stack from images
estimated_hours: 6
priority: P2
tags: [deployment, docker-compose]
note: "[succeeded via PROTEA PR #290 @ 2026-05-11T19:00:34Z]"
```

### T-OPS.3 — Helm chart (mode B)

```yaml
id: T-OPS.3
phase: F5
loop: executor
status: done
deps: [T-OPS.1]
acceptance: |-
  protea-chart/ Helm chart deploys the stack to a k8s cluster
estimated_hours: 12
priority: P3
tags: [deployment, helm, D25]
note: "[succeeded via PROTEA PR #326 @ 2026-05-12T14:01:12Z]"
```

D25 accepted (mode B).

### T-OPS.4 — Docker Swarm stack file

```yaml
id: T-OPS.4
phase: F5
loop: executor
status: done
deps: [T-OPS.1]
acceptance: |-
  deploy/swarm/stack.yml deploys the stack to a Swarm cluster
estimated_hours: 6
priority: P3
tags: [deployment, swarm]
note: "[succeeded via PROTEA PR #327 @ 2026-05-12T14:02:17Z]"
```

### T-OPS.5 — SLURM mode B templates

```yaml
id: T-OPS.5
phase: F5
loop: executor
status: done
deps: [T-OPS.1]
acceptance: |-
  deploy/slurm/ submission templates for HPC mode B
estimated_hours: 6
priority: P3
tags: [deployment, slurm, hpc]
note: "[succeeded via PROTEA PR #333 @ 2026-05-12T14:09:50Z]"
```

### T-OPS.6 — pydantic-settings final

```yaml
id: T-OPS.6
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  All env vars documented in protea/config/settings.py with descriptions
  YAML defaults overridable by env per documented hierarchy
estimated_hours: 4
priority: P2
tags: [config, deployment]
note: "[succeeded via PROTEA PR #345 @ 2026-05-12T18:10:17Z]"
```

### T-OPS.7 — sops + age install

```yaml
id: T-OPS.7
phase: F5
loop: executor
status: blocked
deps: []
acceptance: |-
  sops + age installed on dev + prod hosts
  Age key generated; documented in deploy/secrets-management.rst
estimated_hours: 2
priority: P1
requires_human: true
tags: [security, secrets, D28]
```

PR landed; manual install + age key gen pending.

### T-OPS.9 — airgap bundle (mode C)

```yaml
id: T-OPS.9
phase: F5
loop: executor
status: deferred
deps: []
acceptance: |-
  Airgap-installable bundle per D25 mode C
estimated_hours: 16
priority: P3
tags: [deployment, airgap, D25, post-defensa]
```

Deferred per D25 decision; not blocked, scope-out for post-defensa.

### T-OPS.10 — deployment docs

```yaml
id: T-OPS.10
phase: F5
loop: executor
status: pending
deps: [T-OPS.2, T-OPS.3, T-OPS.4, T-OPS.5]
acceptance: |-
  deploy/README.md covers compose, Helm, Swarm, SLURM with worked examples
estimated_hours: 4
priority: P2
tags: [deployment, docs]
note: "2026-05-17 janitor: pending; no merged PR found"
```

### T-OPS.11 — E2E deploy test

```yaml
id: T-OPS.11
phase: F5
loop: executor
status: done
deps: [T-OPS.2]
acceptance: |-
  CI job spins up the bundle, hits /jobs to enqueue smoke ping, asserts success
estimated_hours: 6
priority: P2
tags: [deployment, e2e, ci]
note: "[succeeded via PROTEA PR #328 @ 2026-05-12T14:04:51Z]"
```

### T-OPS.12 — protea-method-runtime image

```yaml
id: T-OPS.12
phase: F5
loop: executor
status: done
deps: [T-OPS.1]
acceptance: |-
  ghcr.io/frapercan/protea-method-runtime:<tag> image with the inference
  layer + frozen artefact bind-mount support
estimated_hours: 8
priority: P0
tags: [deployment, lafa-gate, runtime]
```

Gate F-LAFA v2: container slices in F7 depend on this base image.

## F6 — F-EXP narrative + F-RESEARCH

### T-EXP.x — narrative campaign with ExperimentRun

```yaml
id: T-EXP.x
phase: F6
loop: executor
status: blocked
deps: [T3.8]
acceptance: |-
  Each significant Job has description + findings; ExperimentRun groups
  related jobs; narratives feed thesis chapter 6
estimated_hours: 8
priority: P2
requires_human: true
tags: [narrative, qa]
```

### T-RES.1 — lineage feature wire in PROTEA

```yaml
id: T-RES.1
phase: F6
loop: executor
status: done
deps: [F2C.5b]
acceptance: |-
  protea-method.lineage feature consumed by predict_go_terms_batch
  Reranker uses lineage feature in production scoring
  Bit-exact cafaeval results reproducible against the lab champion
estimated_hours: 12
priority: P1
requires_human: true
tags: [research, lineage, reranker]
note: "2026-05-16 janitor reconcile: shipped via PR #304 (2026-05-12); additional fixes #364, #368"
```

### T-RES.2 — GeOKG embeddings vs anc2vec

```yaml
id: T-RES.2
phase: F6
loop: executor
status: pending
deps: [T-RES.1]
acceptance: |-
  GeOKG GO embeddings integrated as alternative to anc2vec
  Lab benchmark report (bioinfo-quick T-LR-GeOKG) decides default
estimated_hours: 16
priority: P2
requires_human: true
tags: [research, embeddings, go]
note: "2026-05-16 janitor: still pending; no merged PR found; awaiting bioinfo-quick decision"
```

### T-RES.3 — ensemble multi-K

```yaml
id: T-RES.3
phase: F6
loop: executor
status: deferred
deps: [T-RES.1]
acceptance: |-
  Ensemble across K∈{3,5,10,20} prediction sets ships in scoring router
estimated_hours: 8
priority: P3
tags: [research, ensemble, post-defensa]
```

Diferible post-defensa.

## F7 — F-LAFA v2 + Documentation

### F7.1 — README final pass

```yaml
id: F7.1
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  PROTEA README covers quickstart, deploy, observability, semver
estimated_hours: 4
priority: P2
tags: [docs]
note: "[succeeded via PROTEA PR #335 @ 2026-05-12T14:15:41Z]"
```

### F7.2 — ADR sweep + numbering

```yaml
id: F7.2
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  All ADRs reviewed, renumbered, consistent format
estimated_hours: 8
priority: P2
tags: [docs, adr]
note: "[succeeded via PROTEA task/doc-writer-1778569111-25e2 @ 2026-05-12T07:04:34Z]"
```

### F7.3 — operational runbooks

```yaml
id: F7.3
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Runbooks for stale-job-reaper, DLQ triage, ngrok recovery
estimated_hours: 8
priority: P2
tags: [docs, runbooks]
note: "[F7.3 via PROTEA task/doc-writer-1778526859-4a70 @ 2026-05-11T19:19:47Z; F7.3b via task/doc-writer-1778527219-0b4d @ 2026-05-11T19:25:58Z]"
```

### F7.4 — plugin author guide

```yaml
id: F7.4
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Backend, runner, source plugin author guide with toy examples
estimated_hours: 8
priority: P2
tags: [docs]
note: "[succeeded via PROTEA task/doc-writer-1778524955-725b @ 2026-05-11T18:48:07Z]"
```

### F7.5 — operational insights appendix

```yaml
id: F7.5
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Appendix covering monitoring, troubleshooting, performance tuning
estimated_hours: 6
priority: P2
tags: [docs]
note: "[succeeded via PROTEA task/doc-writer-1778527590-6ad6 @ 2026-05-11T19:33:42Z]"
```

### F7.6 — observability runbook

```yaml
id: F7.6
phase: F8
loop: executor
status: done
deps: [T5.1]
acceptance: |-
  OTel SDK boot + OTLP configuration + trace examples
estimated_hours: 4
priority: P2
tags: [docs, observability]
note: "[succeeded via PROTEA PR #329 @ 2026-05-12T14:05:00Z]"
```

### F7.7 — deployment guide

```yaml
id: F7.7
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Deployment guide for compose, Helm, Swarm, SLURM, airgap modes
estimated_hours: 8
priority: P2
tags: [docs, deployment]
note: "[succeeded via PROTEA PR #334 @ 2026-05-12T14:09:52Z]"
```

## F7-LAFA — F-LAFA v2 reanudación

### F-LAFA.1 — protea-knn-v1 container

```yaml
id: F-LAFA.1
phase: F7-LAFA
loop: executor
status: done
deps: [T-OPS.12, F2C.5b]
acceptance: |-
  protea-knn-v1 container built on protea-method-runtime
  Submitted to LAFA via bind-mount FASTA-in pattern
  Method card delivered to An Phan
estimated_hours: 8
priority: P0
tags: [lafa, container, submission]
```

### F-LAFA.2 — protea-knn-8plm container

```yaml
id: F-LAFA.2
phase: F7-LAFA
loop: executor
status: done
deps: [F-LAFA.1]
acceptance: |-
  Multi-PLM ensemble container; 8 PLMs averaged at score level
  Submitted to LAFA
estimated_hours: 6
priority: P1
tags: [lafa, container, multi-plm]
note: "[succeeded via PROTEA PR #294 @ 2026-05-11T19:23:00Z]"
```

### F-LAFA.3 — protea-v18 container with reranker + lineage

```yaml
id: F-LAFA.3
phase: F7-LAFA
loop: executor
status: done
deps: [F-LAFA.2, T-RES.1]
acceptance: |-
  v18 reranker + lineage feature shipping in container
  Submitted to LAFA only if lineage proves better than baseline
estimated_hours: 8
priority: P1
tags: [lafa, container, reranker, lineage]
note: "[succeeded via PROTEA PR #305 @ 2026-05-12T01:05:17Z]"
```

## FARM — Farm platform + CI

### FARM-1.1 — worktree + branch protection + server-side guards

```yaml
id: FARM-1.1
phase: FARM
loop: conductor
status: done
deps: []
acceptance: |-
  agent-farm has branch protection on main
  worktree git-hooks bundle enforces pre-commit checks locally
  Server-side coauthor guard blocks Co-Authored-By: Claude in all repos
estimated_hours: 8
priority: P1
tags: [farm, hooks, ci]
note: "[succeeded via agent-farm PRs #19, #21, #23 @ 2026-05-16T15:23:17Z-2026-05-16T16:38:54Z; PROTEA PRs #390, #13 (protea-contracts)]"
```

### FARM-EXP.1 — ExperimentRun axis columns + UNIQUE shortid

```yaml
id: FARM-EXP.1
phase: FARM-EXP
loop: executor
status: done
deps: []
acceptance: |-
  ExperimentRun has eval_set_name, dataset_sha, reranker_sha columns
  shortid constraint ensures uniqueness per catalog entry
estimated_hours: 6
priority: P1
tags: [farm-exp, experimentrun]
note: "[succeeded via PROTEA PR #388 @ 2026-05-16T16:10:11Z]"
```

### FARM-EXP.5 — hard-fail on feature_schema_sha mismatch

```yaml
id: FARM-EXP.5
phase: FARM-EXP
loop: executor
status: done
deps: [FARM-EXP.1]
acceptance: |-
  Scoring router rejects predictions with mismatched schema_sha
  Guard prevents silent feature downstream divergence
estimated_hours: 4
priority: P1
tags: [farm-exp, schema-guard]
note: "[succeeded via PROTEA PR #391 @ 2026-05-16T19:10:27Z]"
```

### FIX-EXP-RUN-ENUM — ORM enum case mismatch fix

```yaml
id: FIX-EXP-RUN-ENUM
phase: FARM-EXP-prereq
loop: executor
status: done
deps: []
acceptance: |-
  ExperimentRun ORM Enum(ExperimentRunStatus) maps to DB lowercase values
estimated_hours: 2
priority: P0
tags: [farm-exp-prereq, orm, bug-fix]
note: "[succeeded via PROTEA PR #389 @ 2026-05-16T16:33:03Z]"
```

Done 2026-05-16.

## F8 — Cierre

### F6.1 — sleeps eliminated from tests

```yaml
id: F6.1
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Every test that uses time.sleep() replaced by event-driven wait
  pytest --collect-only | grep sleep returns 0
estimated_hours: 6
priority: P2
tags: [tests, quality]
note: "[succeeded via PROTEA PR #374 @ 2026-05-15T11:26:54Z]"
```

### F6.2 — Hypothesis property tests

```yaml
id: F6.2
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Property tests on contract payloads + scoring + parquet roundtrip
  CI runs Hypothesis with deterministic seed
estimated_hours: 12
priority: P3
tags: [tests, hypothesis]
note: "[succeeded via PROTEA PR #377 @ 2026-05-16T09:56:12Z]"
```

### F6.3 — mutation testing (cosmic-ray)

```yaml
id: F6.3
phase: F8
loop: executor
status: done
deps: [F6.2]
acceptance: |-
  cosmic-ray run on protea/core/ with mutation score documented
estimated_hours: 8
priority: P3
tags: [tests, mutation]
note: "[succeeded via PROTEA PR #383 @ 2026-05-16T10:39:27Z]"
```

### F6.4 — contract tests across plugin repos

```yaml
id: F6.4
phase: F8
loop: executor
status: done
deps: [T1.7]
acceptance: |-
  Each plugin repo's CI runs contract tests against protea-contracts pinned version
estimated_hours: 6
priority: P2
tags: [tests, contracts, plugin]
note: "2026-05-16 janitor plugin-scan: shipped via protea-runners#9 (2026-05-15) + protea-sources#13 (2026-05-15) + protea-backends#20 (2026-05-15)"
```

### F6.5 — Playwright E2E

```yaml
id: F6.5
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Playwright suite in apps/web/ covers every critical user flow
  CI runs against the bundle from T-OPS.11
estimated_hours: 16
priority: P2
tags: [tests, e2e, playwright]
note: "[succeeded via PROTEA PRs #379-#382 @ 2026-05-16T10:01:23Z-2026-05-16T10:29:40Z]"
```

### F6.6 — coverage targets ≥85%

```yaml
id: F6.6
phase: F8
loop: executor
status: done
deps: []
acceptance: |-
  Codecov gate ≥85% on protea/core/, ≥75% on protea/api/
estimated_hours: 8
priority: P2
tags: [tests, coverage]
note: "[succeeded via PROTEA PR #376 @ 2026-05-16T09:36:39Z]"
```

### T-INFRA.NACK — basic_nack on operation cancel/failure

```yaml
id: T-INFRA.NACK
phase: F5
loop: executor
status: done
deps: []
acceptance: |-
  When an operation raises (cancellation, exception, or worker-side termination),
  the consumer in protea/infrastructure/queue/consumer.py issues basic_nack
  (or basic_reject) on the AMQP delivery instead of leaving it unacked.
  Today the message stays "unacked" in RabbitMQ until the channel times out
  (default 30 min via PRECONDITION_FAILED, then it requeues), which with
  prefetch=1 deadlocks the queue: the live worker cannot pull new messages
  until the stale unack clears.
  Concretely: catch the exception path in OperationConsumer._on_message and
  QueueConsumer._on_message; on Job.status == CANCELLED OR on any unhandled
  exception, ch.basic_nack(delivery_tag, requeue=False) so the message is
  dropped from the queue. RetryLaterError keeps its existing requeue=True
  semantics. Add a regression test that submits a cancelled job and asserts
  the queue depth returns to zero within 5 s without manual purge.
estimated_hours: 4
priority: P1
tags: [infra, queue, reliability]
note: "2026-05-16 janitor reconcile: shipped via PR #373 (2026-05-15)"
```

Shipped via PR #373 2026-05-15.

### T-INFRA.EVAL-SET-UNIQUE — pair uniqueness on EvaluationSet

```yaml
id: T-INFRA.EVAL-SET-UNIQUE
phase: F3
loop: executor
status: done
deps: []
acceptance: |-
  evaluation_set table has a UNIQUE constraint on
  (old_annotation_set_id, new_annotation_set_id) via Alembic migration.
  generate_evaluation_set operation becomes idempotent: on duplicate pair,
  return the existing id instead of inserting an orphan.
  Today's incident (2026-05-13): 2 duplicate rows for (v226→v230) pair
  caused training_dump_helpers.py:746 .one_or_none() to raise
  MultipleResultsFound after ~3.5 h of completed compute on LB.1 v226.
  Manual orphan delete done; this slice prevents recurrence.
estimated_hours: 4
priority: P1
tags: [infra, schema, idempotency]
note: "2026-05-16 janitor reconcile: shipped via PR #361 (2026-05-13)"
```

Shipped via PR #361 2026-05-13.

