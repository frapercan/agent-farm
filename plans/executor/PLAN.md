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
status: done
deps: [T-OPS.2, T-OPS.3, T-OPS.4, T-OPS.5]
acceptance: |-
  deploy/README.md covers compose, Helm, Swarm, SLURM with worked examples
estimated_hours: 4
priority: P2
tags: [deployment, docs]
note: "shipped via PROTEA PR #415 (2026-05-18)"
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
status: deferred
deps: [T-RES.1]
acceptance: |-
  GeOKG GO embeddings integrated as alternative to anc2vec
  Lab benchmark report (bioinfo-quick T-LR-GeOKG) decides default
estimated_hours: 16
priority: P2
requires_human: true
tags: [research, embeddings, go]
note: "Deferred per GeOKG NO-GO decision 2026-05-17 (project_geokg_nogo_2026_05_17). Preconditions to revisit: full-text Fmax gain >0.005 + Zenodo coverage parity on v226."
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

## F7 (Documentation, canonical home: plans/doc-writer/PLAN.md)

Slices F7.1 through F7.7 are owned by the doc-writer loop. Their
historical shadow copies were removed from this file in FARM-2.7 to
satisfy the cross-loop unique-id invariant; the canonical (status: done)
entries live in `plans/doc-writer/PLAN.md`.

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

## FARM (Farm platform + CI, canonical home: plans/farm-platform/PLAN.md)

FARM-1.x and FARM-EXP.x are owned by the farm-platform loop; their
canonical entries live in `plans/farm-platform/PLAN.md`. Historical
shadow copies were removed from this file in FARM-2.7 to satisfy the
cross-loop unique-id invariant.

The duplicate `FIX-EXP-RUN-ENUM` summary block that followed (a
status: done copy under phase FARM-EXP-prereq) was likewise removed;
the canonical FIX-EXP-RUN-ENUM slice lives earlier in this file under
phase F3.

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



### FIX-MINIO-DEP — minio python pkg missing from venv breaks export pipeline

```yaml
id: FIX-MINIO-DEP
phase: F3
loop: executor
status: done
shipped_via: PROTEA#508 (merged 2026-05-25T14:08:34Z)
deps: []
acceptance: |-
  `python -c "import minio"` succeeds inside a fresh `poetry install --sync`
  environment of PROTEA.
  Reason for slice: 2026-05-25 boot of stack found 9 of 13 EXP.13 cells
  FAILED at 13:51 UTC with `ModuleNotFoundError: No module named 'minio'`
  raised from MinioArtifactStore. Root cause: minio is not declared in any
  pyproject.toml dependency group, so `poetry install --sync` removes it;
  the export worker can no longer reach the MinIO artefact store.
  Fix is a single-line dependency add + lockfile regeneration + PR.
  After merge + redeploy, re-dispatch the 9 FAILED EXP.13 cells (NOT in
  scope of this slice; conductor will handle re-dispatch).
  RESOLUTION (2026-05-29): PR #508 promoted `minio (>=7.2,<8.0)` from a
  PEP-621 optional `storage` extra to a main project dependency,
  regenerated `poetry.lock` (`optional = false`, `groups = ["main"]`),
  and added `tests/test_minio_import.py` as a CI regression guard so any
  future demotion fails before reaching prod. Plan-progress still showed
  this slice as unblocked because no agent-farm task was ever recorded
  against the slice id; this edit closes the bookkeeping gap.
estimated_hours: 1
priority: P0
tags: [infra, deps, urgent]
```


### LAB-FORMATTER-WIP-RECOVER — close out wip/lab-train-formatter-drift (1847 LOC parked)

```yaml
id: LAB-FORMATTER-WIP-RECOVER
phase: F3
loop: executor
status: pending
deps: []
acceptance: |-
  Branch protea-reranker-lab/wip/lab-train-formatter-drift (2 commits, ~20 files,
  ~1847 LOC) is either:
   (a) audited, formatter-aligned, CI-green, PRed to develop and merged, OR
   (b) explicitly judged superseded/abandonable and the branch deleted with a
       2-line rationale captured in this slice's PR description.
  Rationale: the WIP was parked at end-of-session 2026-05-25 (see memory
  project_session_end_2026_05_25). Leaving it on a dead WIP branch risks bit-rot.
  Operate inside a SECONDARY worktree off protea-reranker-lab (NOT the default
  PROTEA worktree the spawn machinery gives you). Cleanup the secondary worktree
  with `git worktree remove --force` before returning (memory
  feedback_secondary_worktree_orphan_leak).
estimated_hours: 2
priority: P2
tags: [lab, cleanup, recovery]
```


### PAPER-TMLR.9 — Release tags v1.0 on 8 PROTEA repos (executor side of paper plan)

```yaml
id: PAPER-TMLR.9
phase: PAPER-TMLR
loop: executor
status: pending
deps: []
acceptance: |-
  Tag v1.0.0 (or v1.0-paper-tmlr) on each of the 8 PROTEA stack repos
  at the commit corresponding to the paper's reported state.
  See full acceptance criteria in plans/thesis-writer/PLAN.md under
  the same slice id (this entry exists in executor plan so the
  executor loop can pick it up; thesis-writer plan is the source of
  truth for the phase narrative).
estimated_hours: 2
priority: P1
tags: [paper, release, tagging]
```



### HARNESS-E2E-FIXTURES.1 — Seed showcase data for Playwright critical-flows

```yaml
id: HARNESS-E2E-FIXTURES.1
phase: F3
loop: executor
status: pending
deps: []
acceptance: |-
  apps/web/e2e/flows/landing.spec.ts test "landing page title and best
  result block" is re-enabled (test.skip removed) and passes in CI.
  Reason: 2026-05-25 PR #531 had to skip this test after 3 cycles of
  janitor patches because the CI environment renders the homepage with
  empty getShowcase() data (HomeShowcase Suspense fallback never
  resolves to the best-result section).
  Fix options to evaluate:
   (a) Add Playwright global-setup fixture that seeds a deterministic
       showcase response via Next.js route-handler mock or MSW
   (b) Inject a CI-only test data fixture into the showcase API
   (c) Make HomeShowcase render a 'no data yet' empty state with a
       stable testid so the test can assert that path instead
  Each option is ~2-4h. Pick (a) or (c) for stability; (b) leaks test
  data into prod-shaped code.
  Other Playwright tests in the same file may be affected; verify the
  full critical-flows job before declaring done.
estimated_hours: 4
priority: P1
tags: [test, e2e, infra]
```


### HOTFIX-RSC-SERVER-FETCH — baseUrl() server-side absolute URL fallback

```yaml
id: HOTFIX-RSC-SERVER-FETCH
phase: F3
loop: executor
status: done
shipped_via: PROTEA#533 (merged 2026-05-27T23:17:06Z)
deps: []
acceptance: |-
  apps/web/lib/api.ts baseUrl() detects server context (typeof window
  === 'undefined') and uses an absolute URL when NEXT_PUBLIC_API_URL
  is a relative path (starts with '/'). Reads optional PROTEA_INTERNAL_API_URL
  env var (defaults to http://127.0.0.1:8000).
  Reason: 2026-05-25 19:58 CEST PR #531 (RSC migration) broke production
  homepage at https://protea.ngrok.app/es/ with error
  'Failed to parse URL from /api-proxy/showcase/'. RSC server-side
  fetch can't resolve relative URLs. CI Playwright tests caught it but
  were skipped (HARNESS-E2E-FIXTURES.1). Hotfix already applied locally
  on protea-deploy worktree apps/web/lib/api.ts:29-37 + frontend rebuilt
  + restarted; this slice ships the fix through normal PR flow so the
  next git reset --hard origin/develop doesn't wipe it.
  Optionally also update protea-deploy/.env.local to set
  PROTEA_INTERNAL_API_URL explicitly (otherwise default 127.0.0.1:8000 works).
estimated_hours: 1
priority: P0
tags: [hotfix, rsc, urgent]
```


### LOGIN-PERSIST-DEBUG — Investigate + fix non-persistent login

```yaml
id: LOGIN-PERSIST-DEBUG
phase: F3
loop: executor
status: pending
deps: []
acceptance: |-
  Root cause of "login no es persistente" complaint identified and
  documented (with reproducer). Memory project_auth_role_snapshot_bug_2026_05_25
  (PR #504, MERGED 2026-05-24) is NOT the cause since the fix is
  deployed.
  Likely candidates to investigate:
   - JWT TTL too short (check apps/web/.env defaults vs backend issue
     vs cookie expiry)
   - Cookie attributes wrong (Secure / SameSite / HttpOnly mix that
     ngrok-proxied flow doesn't preserve)
   - localStorage not being written / read across navigation
   - Auth middleware not propagating session through Next.js RSC
     hop (similar pattern to the just-fixed RSC server-fetch bug)
   - Login mutation succeeds but the immediate redirect drops the
     cookie before the new page reads it
  Investigate with browser devtools-via-Playwright; reproduce; fix.
  Open PR vs develop. Verify locally that login survives a refresh
  + a navigation across locales (the locale-prefix sweep PR #530 may
  have introduced a side effect on the auth cookie path).
estimated_hours: 4
priority: P0
tags: [auth, session, hotfix]
```


## F-OPS-JOBS — Job lifecycle management (no más manipulación manual de colas)

### F-OPS-JOBS.1 — Job synchronisation hardening (dedup + lease + SIGTERM)

```yaml
id: F-OPS-JOBS.1
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  PROTEA jobs become race-safe and reap-safe end-to-end:
   - New column `job.dedup_key VARCHAR(64) NULL` with partial unique
     index on active statuses; api computes deterministic dedup_key
     from canonical(operation, payload); duplicate POSTs return 409
     with the existing job_id.
   - BaseWorker transitions to RUNNING via conditional UPDATE
     (WHERE id=:j AND status IN ('PLANNED','QUEUED')); rowcount=0
     → silent ACK + skip.
   - New column `job.leased_until TIMESTAMPTZ NULL`; worker
     heartbeats every `PROTEA_JOB_HEARTBEAT_INTERVAL_SECONDS=30`
     extending it; stale_job_reaper uses leased_until not started_at;
     reaped jobs either re-enqueue (default, while attempts < max)
     or fail with `lease_expired`.
   - SIGTERM/SIGINT handler in BaseWorker: on signal, NACK-requeue
     in-flight delivery + UPDATE job back to PLANNED with worker_id=NULL.
   - One-off recovery script `scripts/recover/reap_ghost_e0fbdf5f.sql`
     committed (NOT auto-run) to clean the legacy ghost.
   - 4 commits on one branch `feat/sync-job-hardening`; one PR.
   - Alembic migration reversible.
   - Integration tests: concurrent dispatch dedup, SIGTERM-during-job,
     lease-expiry-reap. All green.
estimated_hours: 8
priority: P0
tags: [jobs, queue, reliability, hotfix]
note: |-
  Closes orphan-jobs incident root cause set
  ([[orphan-jobs-2026-05-18]], [[deploy-keeper-paused-2026-05-23]],
  [[exp13-paused-gpu-pivot-2026-05-26]]). Pre-req for re-dispatching
  the 9 EXP.13 cells on GPU without ghost-row risk.
```

### F-OPS-JOBS.2 — Pause / resume / cancel job management API

```yaml
id: F-OPS-JOBS.2
phase: F5
loop: executor
status: pending
deps: [F-OPS-JOBS.1]
acceptance: |-
  User-directive 2026-05-26: "los jobs deberian poder ser reanudados,
  sincronizados, o cualquier funcionalidad que ayude con la gestion.
  No queremos estar manipulando las colas."
   - New endpoints on api/routers/jobs.py:
     * POST /v1/jobs/:id/pause   → if RUNNING + supports_checkpoint:
       sets `pause_requested=true` (new bool col); worker checks at
       next checkpoint barrier and persists state + flips to PAUSED;
       NACK-requeue with paused-bit so it doesn't get re-dispatched
     * POST /v1/jobs/:id/resume  → PAUSED → PLANNED; re-publish to RMQ
     * POST /v1/jobs/:id/cancel  → any active state → CANCELLED;
       NACK-no-requeue; worker observes pause_requested-like flag
     * GET  /v1/jobs/:id/checkpoint → returns last checkpoint blob
       (debug)
   - At-least one long-running operation (export_research_dataset
     first, then predict_go_terms) implements the checkpoint protocol:
     emit checkpoint event between aspect loops; persist
     {stage, completed_aspects, last_offset} to a new
     `job_checkpoint` table; on resume, skip already-completed work.
   - UI: per-job action menu (pause/resume/cancel) in `/es/operacion/trabajos/`
     and the running-jobs widget.
   - Tests: pause-then-resume produces identical final result to a
     non-paused run for the export operation.
estimated_hours: 16
priority: P1
tags: [jobs, api, ux, reliability]
```

### F-OPS-JOBS.3 — DLQ audit + management UI

```yaml
id: F-OPS-JOBS.3
phase: F5
loop: executor
status: pending
deps: [F-OPS-JOBS.1]
acceptance: |-
  protea.dead-letter currently holds 7228 messages (2026-05-26 boot).
  Goal: surface + drain by category, not by raw rabbitmqctl purge.
   - Endpoint GET /v1/admin/dlq/summary → grouped count by
     {operation, exception_class, root_dataset (if extractable)}
   - Endpoint POST /v1/admin/dlq/replay → re-enqueue subset by
     filter; UI button
   - Endpoint POST /v1/admin/dlq/purge → purge subset by filter;
     UI button with confirmation
   - UI page `/es/operacion/mantenimiento/dlq/` with the summary
     table + replay/purge controls; ADMIN role only.
   - Audit-only script `scripts/admin/dlq_audit.py` for the current
     7228-msg baseline, output committed under `docs/incidents/`.
estimated_hours: 8
priority: P1
tags: [dlq, admin, ux]
note: "depends on dedup_key landing so replay doesn't 409 against still-live duplicates"
```

## F-FEAT-WEB — Frontend feature gaps

### F-FEAT-WEB.DATASET-DETAIL — Dataset detail page UX (downloads + stats + nav + charts)

```yaml
id: F-FEAT-WEB.DATASET-DETAIL
phase: F2
loop: executor
status: pending
deps: []
acceptance: |-
  Dataset detail page at /es/datasets/<id>/ gains four UX features
  the user flagged 2026-05-26:
   1. Download buttons next to the Artifact-store URIs (train.parquet,
      eval.parquet, manifest.json). Use presigned S3/MinIO URLs minted
      by a new GET /v1/datasets/:id/download?artifact=<train|eval|manifest>
      endpoint that 302-redirects to the presigned URL (15-min TTL).
      ADMIN-only OR the dataset owner. Frontend button does a normal
      `<a download href=...>` to the endpoint.
   2. "Estadísticas por aspecto" card showing for BPO / MFO / CCO:
      protein count, distinct GO term count, total annotation count.
      Sourced from a new GET /v1/datasets/:id/stats endpoint that
      reads from `dataset.aggregated_stats JSONB` (populated on
      dataset creation; one-shot backfill script for existing
      datasets). Cache 1h.
   3. Snapshot ontológico ("releases/2026-01-23") becomes a clickable
      link to `/es/datos-de-referencia/anotaciones-go/?snapshot=<id>`
      (or wherever the existing ontology page lives — survey first).
      Same treatment for any other clickable reference (eval-set,
      annotation-set).
   4. Two charts on the page:
      a. Aspect distribution donut (uses the new stats endpoint)
      b. Training-window coverage timeline (uses the existing
         `train_versions` array; render as a simple horizontal
         segment chart spanning the version ticks the page already
         renders as pills).
   Frontend uses existing recharts/visx dependency if present;
   otherwise minimal SVG. No new heavyweight chart libs.
   Single PR with all four sub-features. Em-dash hook clean. No
   Claude/AI mention.
estimated_hours: 12
priority: P1
tags: [web, dataset, ux, charts, downloads]
note: |-
  User feedback verbatim: "Descarga... estadisticas de las ontologias
  fijadas en 1 puunto, y navegacion hacia estas... Siguen faltando
  graficos interesantes por lo que veo." (2026-05-26)
```

### F-AUTH-E2E — Auth regression e2e (login persist + role enforcement)

```yaml
id: F-AUTH-E2E
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  Playwright e2e suite covering the auth flow regression set:
   - login flow (api-key + bearer) survives page refresh + cross-locale
     navigation (the LOGIN-PERSIST-DEBUG bug class)
   - role enforcement: viewer/editor/admin cannot exceed their grants
     (regression for [[auth-role-snapshot-bug-2026-05-25]] PR #504)
   - api-key-to-jwt exchange via /auth/api-key-login
   - logout invalidates the session
  Runs under `playwright test --project=chromium`. New tests live
  in `apps/web/tests/e2e/auth/*.spec.ts`. Mark @critical so CI must
  pass them before merging anything else to develop.
  Hooked into the existing CI as a new job (do NOT block on infra
  flakiness — use generous retries + soft-fail on first run).
estimated_hours: 6
priority: P1
tags: [auth, e2e, playwright, regression]
```

### F-WEB-FORM-POLISH — Functional annotation form aesthetic + UX

```yaml
id: F-WEB-FORM-POLISH
phase: F2
loop: executor
status: pending
deps: []
acceptance: |-
  User 2026-05-26: "q feo se ve el form" (referencing /es/functional-annotation
  page). Improve the "Requisitos previos" card + the launch form:
   - Visible field labels (currently the 3 grey rectangles are bare)
   - Inline validation states (green check / red error per field)
   - "Embeddings", "Reference annotations", "Query set" each become
     pickers with autocomplete + a "Open page" affordance to their
     respective detail pages (consistent with the dataset-detail
     navigation work in F-FEAT-WEB.DATASET-DETAIL)
   - Submit button: disabled until all 3 fields valid; loading
     state during enqueue
   - Form layout: switch to 3 columns on >= md, stacked on mobile
   - Skeleton state during initial load is meaningful (real shape
     of the form, not gray boxes)
  Frontend only; reuses existing components where possible.
estimated_hours: 6
priority: P1
tags: [web, form, ux, polish]
```

### F-PERF-PROFILING — Sophisticated performance profiling of hot paths

```yaml
id: F-PERF-PROFILING
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  User 2026-05-26: "Analisis de rendimiento sofisticados". Instrument
  the three repeatedly-flagged hot paths and ship flamegraphs +
  written report under `docs/perf/`:
   1. export_research_dataset (the FARM-EXP.13 long-runner;
      pair-features + align-cache are env-gated per
      [[export-perf-optimization]])
   2. predict_go_terms_batch (the 16-min hang today on
      load_references — investigate the COUNT(*) freshness check
      under DB pressure)
   3. /v1/benchmark/matrix (the slow aggregation behind the
      Benchmark page; baseline 638ms warm — what's the constant?)
  Tools: `scalene` for CPU+memory, `py-spy` for flamegraphs on a
  live worker process, `pgbadger` or `pg_stat_statements` for the
  DB side. Output one flamegraph + a written diagnosis per path
  in `docs/perf/2026-05-26-baseline.md`, with proposed code-level
  fixes ranked by ROI. Do NOT ship the fixes in this slice — that's
  follow-up work.
estimated_hours: 8
priority: P1
tags: [perf, profiling, observability]
```

### F-UX-REVIEW-SWEEP — Broad UX friction sweep

```yaml
id: F-UX-REVIEW-SWEEP
phase: F2
loop: executor
status: pending
deps: [HOTFIX-V1-ROUTING]
acceptance: |-
  Run ux-reviewer against the main user journeys (annotate, datasets,
  benchmark, jobs, mantenimiento, stack). Output a single ranked
  backlog `docs/ux/2026-05-26-friction-backlog.md` with one row per
  finding: page + screenshot ref + severity + 1-line fix proposal.
  Do NOT ship fixes; that's separate slices per finding.
  Depends on routing fix landing first so the pages actually load.
estimated_hours: 4
priority: P2
tags: [ux, review, backlog]
```

### F-GPU-RESUME-EXP13 — Re-dispatch the 9 paused EXP.13 cells on torch GPU KNN

```yaml
id: F-GPU-RESUME-EXP13
phase: F4
loop: executor
status: pending
deps: [F-OPS-JOBS.1]
acceptance: |-
  Once FEAT-KNN-GPU-TORCH PRs merge (protea-method #31 + PROTEA #539)
  AND F-OPS-JOBS.1 (dedup + lease + SIGTERM) lands:
   1. Bump `protea-method` pin in PROTEA `pyproject.toml` to the
      new release tag; poetry lock + commit.
   2. Verify torch + CUDA work on the host:
      ```python
      python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
      ```
      If False: log "needs torch+cu128 wheel install
      (user said 'mañana actualizo si hace falta')", STOP, ask
      human.
   3. Run a parity smoke: dispatch the SMALLEST of the 9 cells
      (suggest bench-v1-K3-v226-lineage-ankh_base, job
      2fac4975-...) and wait for SUCCEEDED. Compare its produced
      Fmax vs the corresponding SUCCEEDED cell from yesterday
      (look up via `payload->>'output_name'` match); accept if
      delta < 0.005 absolute Fmax (within reranker noise).
   4. If parity passes → fan-out the remaining 8 via
      `dispatch_with_lock` (memory FARM-FEAT.13). The job rows
      already exist (snapshot in
      [[exp13-paused-gpu-pivot-2026-05-26]]); use
      `POST /v1/jobs/:id/resume` (added in F-OPS-JOBS.2) OR
      direct re-publish if F-OPS-JOBS.2 not yet shipped, marking
      the OLD CANCELLED ones with `payload.retry_of`.
   5. Monitor + report when all 9 reach SUCCEEDED. Update
      [[farm-exp-13-dispatched-2026-05-25]] memory.
  Worst case (cu128 wheel missing): produce a one-page write-up
  on `docs/incidents/2026-05-26-gpu-resume-blocked.md` with the
  exact pip command to run and the exact next-step procedure.
estimated_hours: 6
priority: P0
tags: [exp13, gpu, dispatch, jobs]
```

### F-WEB-RUNNING-JOBS-WIDGET — Running-jobs widget freshness + interactivity

```yaml
id: F-WEB-RUNNING-JOBS-WIDGET
phase: F2
loop: executor
status: pending
deps: [F-OPS-JOBS.2]
acceptance: |-
  User 2026-05-26 saw widget reporting "1 en ejecución" while psql
  showed a different RUNNING count, and "predict_go_terms parece
  pillado". Fix:
   1. Poll interval ≤ 10s while page visible; pause on visibility-
      change; refresh on focus.
   2. Surface each running job's elapsed time + last-progress-event
      (from structured log emit-store, or a new column
      `job.last_event_at TIMESTAMPTZ`).
   3. Inline "Pause / Cancel" action buttons (depends on
      F-OPS-JOBS.2 endpoints).
   4. If any RUNNING job has `NOW() - last_event_at > 5 min`,
      flag as ⚠ "stuck (no progress 5+min)" in the widget.
   5. Click-through: opens job detail page with the structured
      event timeline.
estimated_hours: 6
priority: P2
tags: [web, ux, jobs, observability]
```

### F-PRED-FASTPATH — predict_go_terms < 10s on small test queries

```yaml
id: F-PRED-FASTPATH
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  User requirement 2026-05-26: "Un requisito es que tarde segundos
  para el ejemplo de prueba". Concrete target: a predict_go_terms
  call with query_set of ≤5 proteins, on already-warm caches, must
  return SUCCEEDED in < 10 seconds wall-clock (p95 across 5 runs).
  Reference job: c5a8863d-8131-4f46-bedf-1d49e466a2e9 took 3:49 on
  this small set — unacceptable baseline.

  Probable bottlenecks (verify via py-spy on a live run, NOT
  assumption):
   1. Reference pool freshness COUNT(*) blocking on every call
      even with disk cache hit. Skip the count when the disk-cache
      mtime is fresh (< N min) — proteins/embeddings table doesn't
      change minute-to-minute.
   2. `compute_taxonomy=true` triggers NCBI taxonomy db warmup that
      could be pre-warmed lazily once per worker lifetime (already
      runs on worker boot per the log line; maybe it re-warms per
      job — confirm).
   3. `compute_alignments=true` runs Needleman-Wunsch pairwise on
      every (query × neighbour) pair. Use the persistent sqlite
      align-cache (memory `project_export_perf_optimization`); if
      cache key hit > 90% on test-set queries → near-zero
      alignment time.
   4. `search_backend=numpy` on full reference pool ~500k vectors
      x 1024d takes seconds per query. After FEAT-KNN-GPU-TORCH
      merges (PRs #31/#539), expose this path: bench the test
      query on torch GPU vs numpy and pick the faster default.
   5. `aspect_separated_knn=true` triggers 3 KNN searches in series;
      run them in parallel via thread pool or merge into a single
      batched call (most KNN backends support batched query).

  Deliverable:
   - One PR with the top-3 ROI fixes (from py-spy profile).
   - A new pytest `tests/perf/test_predict_fastpath.py` that
     enqueues + waits for a fixed 5-protein test query and
     asserts wall-clock < 10s on warm caches.
   - CI gate: mark @perf, run on every PR touching
     protea/core/operations/predict_go_terms/* (or the cache
     modules).
   - Brief write-up in `docs/perf/2026-05-26-pred-fastpath.md`
     of what changed and the before/after numbers.

  Do NOT regress any existing predict_go_terms test. The fast-path
  must be backward-compatible (all current payload flags still
  honored, just faster).
estimated_hours: 8
priority: P0
tags: [perf, predict, latency, hotfix]
```

### F-EXPORT-PIPELINE-DECOUPLE — Producer-consumer KNN/features pipelining in export

```yaml
id: F-EXPORT-PIPELINE-DECOUPLE
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  Refactor ExportResearchDatasetOperation so the GPU-bound KNN
  computation and the CPU-bound feature build (alignment, anc2vec
  propagation, lineage features) run as two concurrent flows
  connected by a bounded queue. Today they run synchronously per
  (train, test) snapshot pair, leaving the GPU idle while CPU
  computes features and vice versa.

  Architecture:
   - Producer thread/process: drives the KNN loop over all snapshot
     pairs back-to-back, pushes (pair_id, query_indices,
     top_k_neighbours, top_k_distances) tuples into a bounded
     `queue.Queue(maxsize=PROTEA_EXPORT_PIPELINE_BUFFER)`.
   - Consumer worker(s): pull from the queue, compute pair features
     using the existing parallelised pair-features path (memory
     `project_export_perf_optimization`, PR #421), aggregate, and
     emit parquet shards.
   - Backpressure: producer blocks when the queue is full. Default
     `PROTEA_EXPORT_PIPELINE_BUFFER=4` (4 pair-results worth of
     top-k indices in memory at any one time, ~few hundred MB max).
   - Failure semantics: a failure in either flow surfaces as a job
     FAILED with both stage and pair_id in error_message; partial
     parquet shards from completed pairs are discarded (no
     half-written dataset on artifact-store).

  Toggle:
   - Env var `PROTEA_EXPORT_PIPELINED=1` (default `0`, opt-in).
     Synchronous path stays intact so the in-flight EXP.13 run is
     not disturbed. Once the speedup is measured on a fresh cell,
     a follow-up slice flips the default to `1`.
   - When pipelined=0, behaviour is identical to today.

  Measurement:
   - The PR must ship a `scripts/perf/bench_export_pipeline.py`
     script that runs one small cell (suggest
     `bench-v1-K3-v226-lineage-ankh_base`, the smallest of the 9
     EXP.13 cells) twice: once pipelined=0, once pipelined=1.
     Reports wall-clock, GPU utilisation peak (`nvidia-smi
     --query-gpu=utilization.gpu` polled at 1Hz), and per-stage
     timing from the existing structured-log emit events.
   - Acceptance speedup: pipelined run must be at least 1.4x
     faster than synchronous on the same cell on the same hardware
     (RTX 3060 + driver 570 + CUDA 12.8). Fail the slice if not.

  Code locations (verify before editing):
   - `protea/core/operations/export_research_dataset.py` (or the
     equivalent under `core/operations/export/`) is the dispatcher
     loop that currently iterates over snapshot pairs.
   - `protea/core/operations/_pair_feature_compute.py` (per
     memory `project_export_perf_optimization`) already has the
     CPU pool wired; reuse it.
   - `protea-method`'s `knn_search.search_knn(...)` is the KNN
     entry; the producer wraps a loop around it.

  Tests:
   - Unit test that asserts queue backpressure: a slow consumer
     stub causes the producer to block at maxsize.
   - Integration test that runs the pipelined path against a
     synthetic 2-pair workload + verifies parquet equivalence vs
     synchronous (byte-identical schema, row count, content hash
     for a fixed seed).
   - Tests must pass with both `PROTEA_EXPORT_PIPELINED=0` and
     `=1`.

  Thesis hook:
   - Memory `project_complexity_scope_pivot_2026_05_26` covers the
     thesis Big-O section in chapter 5. After this slice ships,
     thesis-writer can add a paragraph quantifying the speedup as a
     reduction in pipeline wall-clock from `T_knn + T_features` to
     `max(T_knn, T_features) + overhead`.

  Do NOT:
   - Refactor the inner KNN call itself (already done by
     FEAT-KNN-GPU-TORCH protea-method #31).
   - Change the on-disk parquet schema.
   - Touch the worker process model (single worker-training
     process is fine; the two flows are threads inside it).
   - Disturb the active EXP.13 run (the default pipelined=0
     guarantees this).
estimated_hours: 6
priority: P1
tags: [perf, export, pipelining, concurrency, gpu]
note: |-
  Originated from a user architectural question 2026-05-26 (post
  KNN-GPU port): GPU is idle ~70% of wall-clock today because the
  per-pair loop is synchronous. Decoupling lets both flows
  saturate hardware. Theoretical speedup factor =
  (T_knn + T_features) / max(T_knn, T_features); empirically
  expected ~1.4-2x on the 9 EXP.13 cells.
```

## F-EXPORT-MINIJOB — Decompose export into coordinator + batch minijobs (compute_embeddings pattern)

User directive 2026-05-26: refactor `export_research_dataset` to mirror the
`compute_embeddings` pipeline (coordinator → batch workers → write). The
goal is to release the GPU as soon as each per-pair KNN minijob finishes,
instead of holding it for the full cell wall-clock while CPU features +
parquet write happen synchronously. All sub-slices are env-gated behind
`PROTEA_EXPORT_MINIJOBS=1` (default `0` = today's monolithic path stays
intact). Theoretical speedup ~2x intra-cell + ~1.5x cross-cell.

### F-EXPORT-MINIJOB.1 — Scaffolding: new Operations + queues + env gate

```yaml
id: F-EXPORT-MINIJOB.1
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  Catalog four new Operations as stubs (no logic yet, registered in
  OperationRegistry, smoke-tested):
   - `export_coordinator` (queue: `protea.training`): receives the cell
     spec, no-ops in this slice, returns SUCCEEDED.
   - `export_knn_batch` (queue: `protea.training.knn-batch`):
     OperationConsumer (no DB Job row, like compute_embeddings_batch).
     Stub accepts a per-pair payload, emits a `noop` event, returns.
   - `export_features_batch` (queue: `protea.training.features`):
     OperationConsumer. Stub.
   - `export_write` (queue: `protea.training.write`): OperationConsumer.
     Stub.
  Wire the three new queues into:
   - `scripts/manage.sh` (start the corresponding worker processes
     when N>0; default count = 1 each, mirror embeddings).
   - `docker-compose.yml` if a worker service is added (mirror the
     embeddings batch worker stanza).
  New env: `PROTEA_EXPORT_MINIJOBS` (default `0`).
  Tests: smoke that the four operations register without import errors
  and that each handler is invoked when a message lands on its queue.
  No behaviour change to today's `export_research_dataset` flow.
estimated_hours: 3
priority: P1
tags: [export, minijob, scaffolding, perf]
note: |-
  Mirror the compute_embeddings pattern. See CLAUDE.md queue routing
  table for the operating shape PROTEA already uses for that
  pipeline.
```

### F-EXPORT-MINIJOB.2 — export_coordinator: partition cell into per-pair minijobs

```yaml
id: F-EXPORT-MINIJOB.2
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.1]
acceptance: |-
  Implement `export_coordinator.execute()`: parse the cell payload
  (output_name, k, train_versions, test_versions, search_backend,
  embedding_config_id, annotation_set_id, ontology_snapshot_id, all
  compute_* flags). Partition into:
   - One `export_knn_batch` payload per (train_snapshot_pair) +
     one per (eval_snapshot_pair) = `len(train_versions) + 1`
     minijobs.
   - Each minijob payload carries a `coordinator_job_id` + `pair_id`
     + the relevant snapshot ids + the embedding_config_id +
     annotation_set_id + k + search_backend (so each minijob is
     self-contained).
  Publish each to `protea.training.knn-batch`. The coordinator
  remains RUNNING until all per-pair minijobs have published a
  completion event to a NEW `coordinator_progress` JobEvent stream
  (one per minijob): when all `pair_knn_done` + `pair_features_done`
  events for the expected pair set have landed, plus the
  `export_write_done` event, the coordinator transitions to
  SUCCEEDED.
  Failure semantics: if any per-pair minijob FAILS, the coordinator
  emits a CANCEL signal (publishes a kill message to the remaining
  queue) and goes FAILED with the failing pair_id + reason.
  Toggle: when `PROTEA_EXPORT_MINIJOBS=0`, `export_coordinator`
  delegates to the legacy `export_research_dataset` monolithic
  handler in-process (default).
  Tests: integration test that submits a tiny 2-pair cell payload
  with the toggle on, verifies that 2 + 1 KNN minijob messages
  are published, and that the coordinator awaits the
  `pair_knn_done` events before progressing.
estimated_hours: 4
priority: P1
tags: [export, minijob, coordinator]
```

### F-EXPORT-MINIJOB.3 — export_knn_batch + export_features_batch implementation

```yaml
id: F-EXPORT-MINIJOB.3
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.2]
acceptance: |-
  Implement the two batch operations by extracting the per-pair
  phases out of `_KnnTransferRunner.run()`
  (protea/core/_knn_transfer_runner.py):

  `export_knn_batch.execute(payload)`:
   - Load reference pool for (embedding_config_id, annotation_set_id)
     using the existing disk-cache (mtime-fresh check, F-PRED-FASTPATH).
   - Run KNN for this pair_id using `protea-method.knn_search`
     with backend=payload.search_backend (torch on GPU when env
     supports, numpy/faiss as fallback).
   - Write the (pair_id, top_k_indices, top_k_distances) result to
     a temp artifact-store prefix:
     `temp/coordinator/<coordinator_job_id>/knn/<pair_id>.npz`
     (LocalArtifactStore for dev, MinioArtifactStore for prod).
   - Emit `pair_knn_done` event with the temp URI.
   - Publish a follow-on message to `protea.training.features` with
     coordinator_job_id + pair_id + temp URI.

  `export_features_batch.execute(payload)`:
   - Read the temp KNN result from the artifact store.
   - Run the existing CPU feature path (alignment, anc2vec, lineage,
     reranker features) using the parallelised pair-features pool
     (PR #421, env-gated).
   - Write the per-pair feature shard to temp prefix:
     `temp/coordinator/<coordinator_job_id>/features/<pair_id>.parquet`.
   - Emit `pair_features_done` event with the temp URI.
   - Publish a follow-on message to `protea.training.write` with
     coordinator_job_id + pair_id + temp URI + total_expected_pairs.

  GPU is released as soon as `export_knn_batch` returns (worker
  picks up the next KNN minijob immediately, possibly from a
  different coordinator job).

  Tests: integration test that runs both batches end-to-end against
  a synthetic 2-pair workload, verifies temp artifacts exist with
  expected shape, and that the per-pair feature parquet matches
  what the monolithic path produces for the same inputs (byte-
  equivalent schema + row count + content hash for a fixed seed).
estimated_hours: 4
priority: P1
tags: [export, minijob, knn, features, gpu]
```

### F-EXPORT-MINIJOB.4 — export_write: assemble shards + upload final dataset

```yaml
id: F-EXPORT-MINIJOB.4
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.3]
acceptance: |-
  Implement `export_write.execute(payload)`:
   - Accept per-pair completion messages. Maintain an in-process
     counter (or check the coordinator's emit stream) for how many
     pairs have completed.
   - When `total_expected_pairs` are all in: read every per-pair
     feature parquet shard from the temp prefix, concatenate
     (preserving the canonical column order from the existing
     dump), write final `train.parquet` and `eval.parquet` under
     the cell's normal artifact-store prefix (e.g.
     `datasets/bench-v1-K3-v226-lineage-ankh_base/`).
   - Compose `manifest.json` from the coordinator payload + the
     concatenated row count and schema_sha (must match the
     monolithic path's manifest_sha for the same input).
   - Insert the `Dataset` row in PG once upload completes (this
     is the existing final step in `export_research_dataset`).
   - Clean up the temp prefix.
   - Emit `export_write_done` event so the coordinator can
     transition to SUCCEEDED.
  Tests: end-to-end integration that runs all four operations
  with PROTEA_EXPORT_MINIJOBS=1, asserts the resulting Dataset
  row + parquet artifacts are byte-equivalent (manifest_sha,
  schema_sha, row counts) to what the monolithic path produces
  for the same input.
estimated_hours: 3
priority: P1
tags: [export, minijob, write, dataset]
```

### F-EXPORT-MINIJOB.5 — Bench + speedup verification + default flip decision

```yaml
id: F-EXPORT-MINIJOB.5
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.4]
requires_human: true
acceptance: |-
  Ship `scripts/perf/bench_export_minijob.py` that runs one
  small cell (suggest `bench-v1-K3-v226-lineage-ankh_base`)
  twice: once monolithic, once minijob. Reports wall-clock,
  GPU utilisation peak (nvidia-smi --query-gpu polled @1Hz),
  per-stage timing from emit events.

  Acceptance speedup: ≥1.5x on RTX 3060 + driver 570 + CUDA 12.8.
  If not met, file a write-up in `docs/perf/<date>-minijob-bench.md`
  with the gap analysis and propose either a follow-up or a
  revert of the toggle default.

  Default flip: if speedup ≥1.5x AND parquet equivalence holds
  on at least three cells, open a follow-up PR that switches
  `PROTEA_EXPORT_MINIJOBS` default from `0` to `1`. This is a
  separate PR; the toggle introduction PR (this slice) does NOT
  flip the default.

  Requires human: a live GPU + uninterrupted stack for ~1h.
estimated_hours: 2
priority: P1
tags: [export, minijob, bench, requires_human]
```

### HOTFIX-GOGRAPH-CLASSIFY — Protein-detail GO graph paints known nodes as predicted

```yaml
id: HOTFIX-GOGRAPH-CLASSIFY
phase: F2
loop: executor
status: done
deps: []
acceptance: |-
  User reported 2026-05-26 viewing
  /es/proteinas/A0A011QK89/?tab=anotaciones: every query node painted
  "Predicted only" (blue) even though the page renders curated KNOWN
  annotations from protein_go_annotation. Root cause was
  `apps/web/components/GoGraph.tsx:22`:
  `const isPredicted = predictedGoIds?.has(goId) ?? true;`
  When the caller did not provide `predictedGoIds` (which is the
  case for the protein-detail page that only passes `subgraph`),
  the default of `true` made every query node classify as predicted.
  Fix: when neither set is provided, query nodes default to
  `known_only`. When either set is provided, classification respects
  explicit membership and falls back to `ancestor` rather than the
  spurious `predicted_only`. Frontend-only change; backend untouched.
estimated_hours: 0.5
priority: P1
tags: [web, hotfix, ux, go-graph]
note: |-
  Shipped 2026-05-26 as PROTEA #555
  (https://github.com/frapercan/PROTEA/pull/555). Auto-merge enabled;
  awaiting GitHub Actions outage recovery to land.
```

### HOTFIX-SPHINX-SERVING — /sphinx static mount path mismatch + ngrok 307 loop

```yaml
id: HOTFIX-SPHINX-SERVING
phase: F2
loop: executor
status: done
deps: []
acceptance: |-
  User reported 2026-05-26 that /sphinx/quality/ returns empty
  on localhost:8000, 404 on localhost:3000, and a 307 redirect
  to https://localhost:8000/api-proxy/sphinx/quality/ on ngrok.
  Root cause(s):

  1. `protea/api/app.py:325` mounts `docs/build/html/` but Sphinx's
     default `sphinx-build -b html docs/source docs/build` writes
     to `docs/build/`. Mount points at empty directory, all
     /sphinx/* requests return empty. Two fixes possible:
     a. Change mount path: `app.mount("/sphinx",
        StaticFiles(directory=project_root / "docs" / "build",
        html=True))`.
     b. Update docs build invocations (Makefile + manage.sh +
        protea-deploy startup hooks) to output to `docs/build/html/`.
     Option (a) is minimal-diff and aligned with what every other
     Sphinx-in-PROTEA reference assumes.

  2. The ngrok 307 redirect to
     `https://localhost:8000/api-proxy/sphinx/quality/` is a
     separate ProxyHeadersMiddleware + visitor_counter middleware
     interaction. Verify whether visitor_counter at
     `protea/api/middleware/visitor_counter.py:53` produces the
     redirect, and whether the X-Forwarded-Host header from ngrok
     is being parsed as `localhost`. If yes, either disable visitor
     counter for /sphinx static paths or add proper ngrok host
     trust to ProxyHeadersMiddleware.

  Build verification:
   - `curl -s http://localhost:8000/sphinx/quality/index.html` must
     return HTML containing the post-#550 H1 sections (Coverage gates,
     Type checking with mypy, Schema migration testing, Branch
     protection and auto-merge policy, Observability and SLO,
     Definition of done and PR checklist).
   - `curl -sL https://protea.ngrok.app/sphinx/quality/` must
     terminate at HTTP 200 with the same content.
   - `curl -s http://localhost:3000/sphinx/quality/` must also work
     (frontend next.config.ts rewrite already in place from PR #540).

  Documentation: update CLAUDE.md or the Sphinx-build instructions
  to canonicalise the output directory.
estimated_hours: 1
priority: P1
tags: [docs, sphinx, web, hotfix]
note: |-
  Surfaced after PR #550 (QE expand) landed: user couldn't see the
  new H1 sections in protea.ngrok.app/sphinx/quality/ because the
  static mount was looking at the wrong directory all along. Fixes
  visibility of every Sphinx page in the repo.
```

### HOTFIX-QE-SIDEBAR-NAV — QE sections show as siblings of the page title

```yaml
id: HOTFIX-QE-SIDEBAR-NAV
phase: F2
loop: executor
status: done
deps: []
acceptance: |-
  After #550 expanded `docs/source/quality/index.rst` from 14 to 20
  sections, the Sphinx sidebar rendered every section as a sibling
  of the `Quality Engineering` page entry instead of nesting them
  underneath it. Root cause: every section used `=====` underline
  (H1), which Sphinx promotes to top-level sidebar items.

  Fix: demote every section underline from `=====` to `-----` so
  the title `Quality Engineering` remains H1 and the sections
  render as H2 anchors within the page. Sidebar now shows
  `Quality Engineering` once with the right-rail "On this page"
  listing the section anchors, matching how `architecture/`,
  `appendix/`, and `runbooks/` already nest in the toctree.
estimated_hours: 0.5
priority: P1
tags: [docs, sphinx, navigation, hotfix]
note: |-
  Surfaced 2026-05-26 after redeploy of PR #550 made the H1
  proliferation visible in the sidebar. Trivial mechanical fix; no
  prose touched.
```

### F-EXPORT-MINIJOB.6 — Content-addressed minijob caching + resume + cross-cell reuse

```yaml
id: F-EXPORT-MINIJOB.6
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.3, F-EXPORT-MINIJOB.4]
acceptance: |-
  Today minijob temp artifacts live under
  `temp/coordinator/<coord_id>/{knn,features}/<pair_id>` (the
  coordinator job UUID). When a cell is re-dispatched (after a
  crash or worker restart) the new coordinator allocates a
  different UUID and re-runs every minijob from scratch, even
  though every KNN/feature output for the same (cell_signature,
  pair_id) is deterministic.

  Three layers of compute reuse, each ships as one PR:

  **1. Per-pair KNN cache (cross-coordinator, cross-cell)**

  Cache key = sha256_hex({
    "embedding_config_id": ...,
    "annotation_set_id": ...,
    "ontology_snapshot_id": ...,
    "k": ...,
    "search_backend": ...,
    "train_snapshot": ...,  (or eval pair)
    "use_embedding_pca": ...,
  })[:24]
  Cache path:
  `${PROTEA_ARTIFACT_STORE}/cache/knn/<cache_key>.npz`

  Before running KNN inside `export_knn_batch`, check the
  cache prefix; on hit, emit `pair_knn_done` with the cached
  URI and skip the GPU work. On miss, run KNN normally and
  write to BOTH the per-coordinator temp prefix (for
  features_batch to read) AND the cache prefix.

  Concrete reuse: re-dispatching the same cell repeats zero
  KNN. Different cells that share the same (embedding,
  annotation, k) but differ only in `compute_alignments` or
  `compute_taxonomy` flags ALSO share KNN cache (those flags
  affect features, not KNN).

  **2. Per-pair features cache**

  Cache key = sha256_hex({
    "knn_cache_key": ...,            # from layer 1
    "compute_alignments": ...,
    "compute_taxonomy": ...,
    "compute_reranker_features": ...,
    "expand_votes_to_ancestors": ...,
  })[:24]
  Cache path:
  `${PROTEA_ARTIFACT_STORE}/cache/features/<cache_key>.parquet`

  Same hit/miss logic. Lets a cell that retried because
  `export_write` crashed (after every KNN + features
  succeeded) skip directly to the final assembly stage.

  **3. Resume protocol in coordinator**

  When `export_coordinator` starts and finds that some of
  its pair minijob completion events are already recorded
  for the SAME `cell_signature` (a) on prior coordinator
  runs OR (b) by another coordinator's cache writes, the
  coordinator emits the corresponding `pair_knn_done` /
  `pair_features_done` events immediately and counts them as
  done. It still publishes ONLY the missing minijobs to
  protea.training.knn-batch.

  Acceptance tests:
   - Submit a coordinator, let it complete fully, re-submit
     the same payload: second run completes in seconds
     (write-only).
   - Submit, kill worker-export-knn-batch mid-flight, re-dispatch:
     completed minijobs are skipped, only missing ones run.
   - Submit two cells differing only in `compute_alignments`:
     KNN minijobs of the second cell hit cache.

  Code locations:
   - `protea/core/operations/export_minijobs/_export_knn_batch.py`
     for cache check/write on KNN.
   - `protea/core/operations/export_minijobs/_export_features_batch.py`
     for features cache.
   - `protea/core/operations/export_minijobs/_export_coordinator.py`
     for the resume protocol.
   - `protea/infrastructure/storage/artifact_store.py` for any
     new helper (exists?, get_uri()).

  Tests under `tests/test_export_minijob_cache.py`.

  Env var: `PROTEA_EXPORT_MINIJOB_CACHE=1` (default `1` once
  validated; can be flipped off for benchmarking).

estimated_hours: 6
priority: P0
tags: [export, minijob, cache, resume, reuse]
note: |-
  User directive 2026-05-26: "que se reutilicen los computos al
  maximo". Pre-requisite to the FARM-EXP.14 follow-up sweep
  (multi-seed full-grid) which would otherwise re-run every cell
  from scratch every seed iteration.
```

### F-EXPORT-MINIJOB.7 — Per-queue worker counts via env vars (dynamic parallelism)

```yaml
id: F-EXPORT-MINIJOB.7
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.1]
acceptance: |-
  User directive 2026-05-26: "podemos hacer cada operacion GPU/CPU en
  paralelo. Por ejemplo 2 workers haciendo el KNN, y ninguno haciendo
  features." Today `manage.sh start` spawns exactly 1 worker per minijob
  queue when `PROTEA_EXPORT_MINIJOBS=1`. Scaling beyond that requires
  manual `manage.sh scale protea.training.knn-batch N` invocations.

  Make worker counts configurable at startup via three env vars:
   - `PROTEA_EXPORT_KNN_WORKERS` (default 1)
   - `PROTEA_EXPORT_FEATURES_WORKERS` (default 1)
   - `PROTEA_EXPORT_WRITE_WORKERS` (default 1)

  When `manage.sh start` runs with `PROTEA_EXPORT_MINIJOBS=1` and
  `PROTEA_EXPORT_KNN_WORKERS=2`, it spawns 2 worker-export-knn-batch
  processes. Same for features and write.

  Sensible defaults documented in CLAUDE.md:
   - GPU host with 12 GB VRAM: KNN_WORKERS=2 is the safe ceiling
     (each preloads ~3-5 GB ref pool; 2 saturates the card).
   - CPU-bound features: FEATURES_WORKERS can be (cores / 2) since
     each features minijob already parallelises pair-features
     internally (PR #421).
   - WRITE_WORKERS=1 is enough (assembly is I/O bound + the cell
     needs all per-pair shards before final write anyway).

  Tests: integration test that sets KNN_WORKERS=2 + verifies
  rabbitmqctl list_queues shows `consumers=2` on the .knn-batch queue
  + that two minijobs from different coordinator_job_ids can be in
  flight concurrently.

  Documentation: add a "Dynamic worker pool" subsection in
  `docs/source/quality/index.rst` under "Architectural patterns"
  describing how to size per-stage pools for a given hardware
  profile.
estimated_hours: 2
priority: P1
tags: [export, minijob, parallelism, ops]
```

### F-MULTISTAGE-COHERENCE — Unify multi-stage pipeline patterns (embeddings + export_minijobs + predictions)

```yaml
id: F-MULTISTAGE-COHERENCE
phase: F5
loop: executor
status: pending
deps: [F-EXPORT-MINIJOB.4]
acceptance: |-
  PROTEA now has THREE coordinator+batch+write pipelines that share
  90% of the mechanism but diverge on 3 specifics:
   1. Inter-stage data transfer: compute_embeddings carries payload
      inline; export_minijobs writes temp npz/parquet and passes
      URIs. predict_go_terms is a hybrid.
   2. Module layout: compute_embeddings flat (.py files), export
      nested in a package, predictions package.
   3. Naming: ``ComputeEmbeddingsOperation`` vs
      ``ExportCoordinatorOperation`` (literal-stage suffix).

  Extract a shared multi-stage pipeline contract under
  ``protea/core/contracts/multistage.py``:

  - ``PipelineStage`` abstract Operation subclass with declared
    next-stage queue + payload-size-aware `publish_next()` helper.
  - ``StageArtifactStore``: thin facade over `ArtifactStore` that
    holds the conventions `temp/<pipeline>/<parent_job>/<stage>/<key>`
    so every pipeline writes intermediate state the same way.
  - ``Coordinator`` base class with partition + emit + reaper-safe
    completion accounting (the ``update_parent_progress`` pattern
    is already shared; this just makes it explicit).

  Then refactor each of the three existing pipelines to use the
  shared base, deleting the per-pipeline boilerplate.

  Acceptance:
   - One PR per pipeline (3 PRs in series): introduce the base,
     migrate compute_embeddings, migrate export_minijobs, migrate
     predict_go_terms.
   - Each migration is behaviour-preserving (same RMQ messages on
     the wire, same parquet/embedding outputs, same Fmax).
   - Tests: integration runs for each pipeline must produce
     byte-identical outputs vs pre-refactor baseline (capture a
     SHA-256 of one canonical output before the refactor, assert
     after).
   - Documentation: add a "Multi-stage pipeline contract" page
     under `docs/source/architecture/` that diagrams the shared
     dataflow and links the three concrete pipelines as instances.

  Non-goal: don't change the wire-level message shapes or queue
  names. The unification is internal-only.
estimated_hours: 8
priority: P2
tags: [refactor, architecture, coherence]
note: |-
  Surfaced 2026-05-26 by user audit. The pipelines work today;
  this is technical debt cleanup that pays back on the FOURTH
  pipeline (if/when one is added). Defer until the export_minijob
  series stabilises post-#554/#558 merge.
```

### F-MULTISTAGE-COHERENCE.1 — Extract `multistage` contract (base classes, no migration)

```yaml
id: F-MULTISTAGE-COHERENCE.1
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  Introduce `protea/core/contracts/multistage.py` containing:

  - `MultiStagePayload(ProteaPayload, frozen=True)` base with the
    fields every batch payload carries (`coordinator_job_id`,
    `pair_id` / `chunk_id` / equivalent).
  - `StageArtifactStore` thin facade over `ArtifactStore` that
    encodes the convention `temp/<pipeline>/<coordinator_job_id>/<stage>/<key>`
    and exposes `read_intermediate(uri)`, `write_intermediate(stage,
    key, bytes_or_file) -> uri`, `exists_intermediate(stage, key)`.
  - `publish_next_stage(emit, payload_or_uri, size_threshold_kb=64)`
    helper that auto-chooses inline payload vs artifact-store URI
    based on serialized size. Returns the message that should be
    handed to `publish_operations=`.
  - `PipelineStage(Operation)` abstract subclass providing
    `_artifact_store(settings) -> StageArtifactStore` and a thin
    template for `execute` that emits `<stage>.start` / `<stage>.done`
    consistently.
  - `Coordinator(Operation)` abstract subclass with
    `partition(payload) -> list[Operation messages]` +
    `dispatch_partition_with_progress(emit, parts) -> deferred=True
    with progress_total=len(parts)`.

  Tests under `tests/test_multistage_contract.py` exercising the
  abstractions with stub operations. NO migration of existing
  pipelines in this slice — the three real pipelines keep their
  current per-pipeline boilerplate and continue to pass their
  tests untouched.

  Documentation: new
  `docs/source/architecture/multistage-pipeline.rst` page
  diagramming the contract + linking the three pipelines as
  prospective consumers (with status "pending migration").

  Smoke: full `pytest -q` passes; ruff + mypy clean.
estimated_hours: 4
priority: P1
tags: [refactor, architecture, contract, multistage]
```

### F-MULTISTAGE-COHERENCE.2 — Migrate compute_embeddings to multistage contract

```yaml
id: F-MULTISTAGE-COHERENCE.2
phase: F5
loop: executor
status: pending
deps: [F-MULTISTAGE-COHERENCE.1]
acceptance: |-
  Refactor `compute_embeddings.py` so `ComputeEmbeddingsOperation`,
  `ComputeEmbeddingsBatchOperation`, and `StoreEmbeddingsOperation`
  inherit from `Coordinator` and `PipelineStage` per .1's contract.

  Behaviour-preserving:
   - SAME RMQ message shapes on the wire (inline embedding bytes
     still inline because they remain under the 64 KB threshold
     per batch typically; if they exceed, automatic switch to
     artifact-store URI — instrument with a metric so we can see
     when this kicks in).
   - SAME output (sequence_embeddings DB rows byte-equivalent).
   - SAME observable events.

  Tests: existing compute_embeddings tests pass unchanged. Add a
  byte-equivalence assertion (SHA-256 of the parquet/embeddings
  produced by a representative test cell) before/after the refactor.
estimated_hours: 4
priority: P1
tags: [refactor, embeddings, multistage]
```

### F-MULTISTAGE-COHERENCE.3 — Migrate predict_go_terms to multistage contract

```yaml
id: F-MULTISTAGE-COHERENCE.3
phase: F5
loop: executor
status: pending
deps: [F-MULTISTAGE-COHERENCE.1]
acceptance: |-
  Refactor `predict_go_terms` coordinator/batch/write to use
  `Coordinator` / `PipelineStage` from .1. Same behaviour-preserving
  contract as .2. Hybrid in-message + artifact-store transfer
  becomes uniform via `publish_next_stage` helper.
estimated_hours: 4
priority: P1
tags: [refactor, predictions, multistage]
```

### F-MULTISTAGE-COHERENCE.4 — Migrate export_minijobs to multistage contract

```yaml
id: F-MULTISTAGE-COHERENCE.4
phase: F5
loop: executor
status: pending
deps: [F-MULTISTAGE-COHERENCE.1, F-EXPORT-MINIJOB.4]
acceptance: |-
  Refactor `export_minijobs/` package to inherit from the
  multistage contract. The temp-prefix convention
  (`temp/coordinator/<id>/{knn,features}/...`) collapses into the
  `StageArtifactStore` default. The
  `publish_operations=[(_FEATURES_QUEUE, _build_features_msg(...))]`
  call sites become single-line `publish_next_stage(emit, payload)`.

  Behaviour-preserving as in .2/.3. Compatibility with the
  content-addressed cache from F-EXPORT-MINIJOB.6 must be
  preserved (cache key derivation lives below the contract).
estimated_hours: 4
priority: P1
tags: [refactor, export, multistage]
note: |-
  Deferred relative to .2 and .3 because export_minijobs is the
  newest pipeline and its core implementation (#554 / #558) needs
  to settle on develop before refactoring. Run after #554 + #558
  merge and at least one end-to-end EXP.13 cell completes on the
  minijob path.
```

## F-USER-OWNERSHIP — Multi-tenant data ownership

User directive 2026-05-26: "que cada usuario pueda acceder a su
historial completo de datos, operaciones, embeddings, o o que
quiera." Today PROTEA is single-tenant: every authenticated user
sees every Job, Dataset, EmbeddingConfig, PredictionSet,
EvaluationResult, RerankerModel. Add per-user ownership + a public
subscription model.

### F-USER-OWNERSHIP.1 — ADR + DB schema: owner_user_id columns + backfill

```yaml
id: F-USER-OWNERSHIP.1
phase: F4
loop: executor
status: pending
deps: []
acceptance: |-
  Open `docs/source/adr/D39-multi-tenant-ownership.rst` with
  Context / Decision / Consequences explaining the multi-tenancy
  pivot (per-user history + public subscription).

  Alembic migration adding `owner_user_id UUID NULL REFERENCES
  user(id) ON DELETE SET NULL` + indexed on:
   - `job`
   - `dataset`
   - `embedding_config`
   - `prediction_set`
   - `evaluation_set`
   - `evaluation_result`
   - `reranker_model`
   - `annotation_set`

  Migration backfills existing rows by attributing them to the
  bootstrap admin user (single tenant before this PR).

  No API change in this slice; the columns are read-only until
  .2 wires the filtering.
estimated_hours: 3
priority: P1
tags: [auth, multitenancy, schema, adr]
```

### F-USER-OWNERSHIP.2 — API filter: scope every list/read endpoint to current user

```yaml
id: F-USER-OWNERSHIP.2
phase: F4
loop: executor
status: pending
deps: [F-USER-OWNERSHIP.1]
acceptance: |-
  Add a `?scope=mine|public|all` query parameter (default `mine`)
  on every list endpoint that returns user-owned records. `all`
  is ADMIN-only.

  Endpoints touched: GET /jobs, /datasets, /embeddings,
  /annotations, /evaluation-sets, /evaluation-results,
  /prediction-sets, /reranker-models. POST endpoints stamp
  `owner_user_id` from the authenticated user.

  Tests: a non-admin user sees only their own rows by default;
  cannot mutate another user's rows; admin scope=all sees
  everything. Backward-compat: existing scripts that pass no
  scope still work, the default narrows correctly.
estimated_hours: 4
priority: P1
tags: [auth, multitenancy, api]
```

### F-USER-OWNERSHIP.3 — UI: per-user history page

```yaml
id: F-USER-OWNERSHIP.3
phase: F2
loop: executor
status: pending
deps: [F-USER-OWNERSHIP.2]
acceptance: |-
  New `/es/mi-historial/` page that aggregates the current user's:
   - Jobs (last 50, filterable by operation)
   - Datasets (the ones they originated)
   - Embedding configs they registered
   - Prediction sets + evaluation results they ran
   - Reranker models they imported

  Each item links to its detail page. Quick-filter chips at the
  top (today / this week / all).
estimated_hours: 4
priority: P1
tags: [web, history, ux]
```

## F-USER-PUBLISH — Public subscription mechanism

### F-USER-PUBLISH.1 — Workspace + visibility schema

```yaml
id: F-USER-PUBLISH.1
phase: F4
loop: executor
status: pending
deps: [F-USER-OWNERSHIP.1]
acceptance: |-
  Alembic migration adds:
   - `workspace` table: id, owner_user_id, slug (unique), name,
     description, visibility ENUM('private','public'),
     created_at, updated_at.
   - `workspace_resource` table: workspace_id + resource_type
     ENUM('job','dataset','embedding_config','prediction_set',
     'evaluation_result','reranker_model') + resource_id + added_at.
     Composite unique index on (workspace_id, resource_type,
     resource_id).

  An owner can attach any owned resource to their workspace and
  flip visibility=public. Public workspaces become discoverable
  via a new GET /workspaces?visibility=public list endpoint.
estimated_hours: 3
priority: P2
tags: [auth, schema, publish]
```

### F-USER-PUBLISH.2 — Workspace API + read-through for public visibility

```yaml
id: F-USER-PUBLISH.2
phase: F4
loop: executor
status: pending
deps: [F-USER-PUBLISH.1, F-USER-OWNERSHIP.2]
acceptance: |-
  Endpoints:
   - POST /workspaces — create a workspace
   - PUT /workspaces/:id — edit name/description/visibility
   - POST /workspaces/:id/resources — attach a resource
   - DELETE /workspaces/:id/resources/:type/:id — detach
   - GET /workspaces?visibility=public&q=... — discover public
   - GET /workspaces/:slug — view (public OR owner OR subscriber)

  When a resource is in a public workspace, any authenticated user
  can READ it through `/<resource>/:id?via_workspace=:slug` even
  though it isn't theirs. Direct list endpoints still respect
  scope=mine; the via-workspace hop is the explicit public path.
estimated_hours: 4
priority: P2
tags: [auth, api, publish]
```

### F-USER-SUBSCRIBE.1 — Subscriptions + notifications

```yaml
id: F-USER-SUBSCRIBE.1
phase: F4
loop: executor
status: pending
deps: [F-USER-PUBLISH.2]
acceptance: |-
  - `workspace_subscription` table: subscriber_user_id +
    workspace_id + created_at + last_seen_at. PK (subscriber,
    workspace).
  - POST /workspaces/:id/subscribe / DELETE /workspaces/:id/subscribe
  - When a workspace gains a new resource, a `workspace.updated`
    event is emitted; the in-app notification surface (a new
    notification table or a re-use of JobEvent fields) shows the
    subscriber a chip "X new in <workspace>" until they open it.

  Notifications surface as a bell badge on the topbar with the
  count; clicking shows the list of new items + which workspace
  they came from.
estimated_hours: 4
priority: P2
tags: [auth, subscription, notification]
```

### F-USER-SUBSCRIBE.2 — Discover + follow UI

```yaml
id: F-USER-SUBSCRIBE.2
phase: F2
loop: executor
status: pending
deps: [F-USER-SUBSCRIBE.1]
acceptance: |-
  New `/es/explora/` page with:
   - A grid of public workspaces (slug, owner, resource counts,
     last-updated, follow button).
   - Each card opens to a workspace detail page with the
     resource list grouped by type.
   - The current user's "Following" tab on the same page shows
     their subscribed workspaces + recent updates.

  Subscription discovery surfaces also on the homepage: a
  "Public workspaces" card next to the existing pipeline cards.
estimated_hours: 4
priority: P2
tags: [web, discover, social, ux]
```

### F-API-OPENAPI-POLISH — Production-grade OpenAPI specification

```yaml
id: F-API-OPENAPI-POLISH
phase: F4
loop: executor
status: pending
deps: []
acceptance: |-
  User directive 2026-05-26: "la parte de OPENAPI nos la podríamos
  currar más". Audit + harden the generated `docs/openapi.json`:

  1. **Per-endpoint descriptions**: every route under
     `protea/api/routers/*.py` has a multi-line docstring with:
      - One-sentence summary (the `summary=` argument is enforced).
      - A "When to use this" paragraph for non-obvious endpoints.
      - A "Returns" section describing the response shape semantically
        (not just the schema).
      - A "Raises" section listing the 4xx/5xx the caller can expect,
        with the meaning of each.

  2. **Realistic examples**: every request body model gets a
     `model_config.json_schema_extra.example` block with a payload
     that actually works (not a placeholder zeros UUID). Pull
     examples from the integration tests where possible.

  3. **Response schemas**: every endpoint returns a typed pydantic
     model (not `dict[str, Any]`). Error responses standardised on
     a single `ProblemDetail` schema (RFC 7807-shaped) with
     `type`, `title`, `status`, `detail`, `instance` fields. The
     existing handlers already emit that shape; expose it in OpenAPI.

  4. **Tags + grouping**: every router uses a canonical tag matching
     its concern. Add `tags_metadata` in `protea/api/app.py` with
     a one-line description per tag so Swagger UI groups + describes
     them properly.

  5. **Security schemes**: declare `bearerAuth` + `apiKeyAuth`
     security schemes in the OpenAPI top-level. Mark each endpoint
     with the required scheme (currently implicit via dependency
     injection of `require_role`).

  6. **Interactive docs**: re-enable Swagger UI at `/docs` and
     ReDoc at `/redoc` (currently disabled in `create_app`?).
     Both should serve the polished spec.

  7. **Schema versioning**: add `info.version` derived from
     `protea.__version__`; bumping the package version bumps the
     spec version. A new CI gate fails the openapi-drift check if
     a breaking spec change ships without bumping version.

  8. **Coverage check**: ship `scripts/check_openapi_completeness.py`
     that fails when any route lacks a summary / docstring / example.
     Wire into the existing `lint.yml` workflow.

  Quality bar (per [[feedback_completion_quality_bar]]):
   - Doc: new Sphinx page `docs/source/architecture/openapi.rst`
     describing the spec conventions + how to consume it.
   - UI: link to /docs and /redoc from the existing
     "OpenAPI / Swagger" sidebar item.
   - E2E: playwright spec opens /docs, asserts the title + that
     at least the `/jobs` and `/datasets` operations are listed
     under their tags.
   - Local CI 10/10 green.

  No breaking wire change: existing clients keep working.
estimated_hours: 6
priority: P1
tags: [api, openapi, docs, ux, quality]
note: |-
  Surfaced 2026-05-26 by user request. Pre-requisite to public
  subscription mechanism (F-USER-PUBLISH.2) because external users
  on a public workspace need a discoverable, professional API spec
  to consume the data.
```


### FEAT-KNN-GPU-TORCH-RESUME — Resume EXP.13 (6 missing cells); numpy backend (torch nonviable)

```yaml
id: FEAT-KNN-GPU-TORCH-RESUME
phase: F-EXP-RESET
loop: executor
status: done
shipped_via: "import-by-reference replay of surviving artefacts (executor-1780797917-02cc, 2026-06-07); no recompute needed"
deps: [FEAT-KNN-GPU-TORCH-PREP]
backend_override: |-
  search_backend=numpy, NOT torch (user decision 2026-06-07): torch GPU KNN
  thrashes in an endless CUDA-OOM loop on the 12GB host GPU. See memory
  project_torch_gpu_knn_nonviable_12gb_2026_06_07. The torch pre-conditions
  below are obsolete and were not exercised.
acceptance: |-
  Six EXP.13 cells reach status present (registered) in the `dataset` table
  for the v226-lineage grid:
   K=3: ankh_large, esm2_650m, esmc_600m, prostt5
   K=5: ankh_base, esmc_600m
  Resolution (2026-06-07): no recompute was required. All six cells already
  had complete artefacts in MinIO from the 2026-06-04 export run
  (train/eval parquet + manifest.json). Five had surviving Dataset rows;
  bench-v1-K3-v226-lineage-ankh_large lost only its DB row in the 5th DB
  wipe (2026-06-06, restored from a pre-2026-06-04 dump). It was re-registered
  via POST /v1/datasets/import-by-reference from its surviving manifest
  (n_train_rows=121240333, n_eval_rows=8698709, schema_sha=81a2a723fcf2),
  under the stack-owner lock (owner=export, task_id=executor-1780797917-02cc).
  The full 24-cell grid (8 PLM x K{3,5,10}) is now complete in `dataset`.
  Obsolete torch pre-conditions (superseded by the numpy override; not run):
   - protea-method >= the commit shipping torch GPU KNN (PRs #31 + #32)
   - both venvs have `torch.cuda.is_available() == True`
   - host driver supports CUDA 12.8 (driver 570+ ok, no upgrade required)
   - smoke parity on one small cell vs numpy baseline (per-aspect delta < 1e-3)
  If any cell artefacts had been missing, the recompute payload is the same
  v226-lineage template (k, output_name, train_versions, test_versions=[230],
  use_embedding_pca, compute_taxonomy, compute_alignments,
  expand_votes_to_ancestors, annotation_source, embedding_config_id,
  ontology_snapshot_id) with `search_backend=numpy`.
estimated_hours: 12
priority: P0
tags: [exp13, numpy, resume, db-wipe-replay]
```


### FEAT-KNN-GPU-TORCH-PREP — Pre-flight before EXP.13 torch resume

```yaml
id: FEAT-KNN-GPU-TORCH-PREP
phase: F-EXP-RESET
loop: executor
status: done
shipped_via: PROTEA#564+#573 (merged 2026-05-27T22:44:10Z + 2026-05-28T00:13:33Z)
deps: []
acceptance: |-
  PROTEA PR opened and merged that:
   1. Bumps poetry.lock so protea-method resolves to main with the torch
      GPU KNN backend (PRs #31 + #32 merged 2026-05-26 02:22Z upstream);
      previously locked at protea-method 0.3.0 (pre-torch).
   2. Flips default CUDA_VARIANT in scripts/install_gpu_torch.sh from
      cu121 to cu128 so future redeploys default to the wheel set that
      matches the driver 570+ runtime (cu130/cu132 require driver 580+).
  Post-merge manual step (out of slice scope, conductor handles):
   - run `CUDA_VARIANT=cu128 bash scripts/install_gpu_torch.sh` in both
     venvs (~/Thesis2/repositories/PROTEA and protea-deploy worktree).
estimated_hours: 1
priority: P0
tags: [exp13, torch, gpu, prep]
```


### F-OPS-CHILD-FAILED-EMIT — Surface child.failed event when OperationConsumer catches an exception

```yaml
id: F-OPS-CHILD-FAILED-EMIT
phase: F-OPS
loop: executor
status: done
deps: []
acceptance: |-
  When `OperationConsumer._on_message` catches an exception from
  `op.execute(...)`, the consumer emits a structured `child.failed`
  event on the COORDINATOR's job_event row with pair_id (if present),
  operation, error_class, truncated error_message. Already happens for
  Job-bound operations via BaseWorker fail path; this slice is the
  queue-driven equivalent. Shipped 2026-05-27 via PROTEA PR #571.
estimated_hours: 2
priority: P0
tags: [ops, observability, exp13, coord-fail-propagate]
note: "shipped via PROTEA PR #571 2026-05-27"
```
priority: P0
tags: [ops, observability, exp13, coord-fail-propagate]
note: "shipped via PROTEA PR #571 2026-05-27"
```

## F-LAFA-IA — PROTEA eval aligned to LAFA protocol + IA-weighted

Campaign spec: `~/Thesis2/IA-ALIGNED-RERANKER-BRIEF.md` (verified
2026-06-02). One story: make the lab/PROTEA evaluation match the LAFA
submission protocol AND report IA-weighted metrics (wFmax / S_min),
with every metric documented for thesis chapter 6. Repo =
`protea-reranker-lab`, base = `develop`. The honest publishable claim is
the delta over KNN baseline on the IA-weighted metric, not the
propagation-inflated unweighted Fmax (brief section 5).

### F-LAFA-IA.0 — IA artefact + weighted baseline re-eval

```yaml
id: F-LAFA-IA.0
phase: F-LAFA-IA
loop: executor
status: done
shipped_via: "lab PR #57"
deps: []
acceptance: |-
  ia.txt generated for GO release v226, consistent with
  datasets/bench-v1-K5/go.obo and propagated annotation frequencies of
  the training corpus; provenance documented (corpus, release, formula
  IA(t) = -log2 P(t | parents(t)), Clark and Radivojac 2013). Reuse any
  IA utility already in the cafaeval-protea fork before writing one.
  cafaeval re-run with ia= over the EXISTING lk-{bpo,mfo,cco} seed42
  runs for BOTH reranker and KNN baseline. The four numbers per cell
  (internal Fmax / cafaeval Fmax / wFmax / S_min) recorded in runs/ +
  a reproducible markdown summary. No training changes in this slice.
  Local CI green; PR against lab develop.
estimated_hours: 8
priority: P0
tags: [lafa, ia, metrics, baseline, chapter-6]
note: "spec brief sections 3, 7.1, 7.2; foundation for all later slices"
```

### F-LAFA-IA.1 — Pin exact LAFA protocol at v227 + verify IA + minimal-op verdict

```yaml
id: F-LAFA-IA.1
phase: F-LAFA-IA
loop: executor
status: done
shipped_via: "lab PR #58"
deps: [F-LAFA-IA.0]
acceptance: |-
  ANALYSIS slice (no heavy exports; root is at 95%/48G and Docker.raw
  does not compact hot, so dispatching a re-export here is forbidden).
  Deliver, written to runs/ + a reproducible markdown summary:
  1. EXACT LAFA protocol pinned to the v227 band (corrected: LAFA is
     227->230, deployed/checked at v227, see memory
     lafa-v227-band-correction-2026-06-04). Document with exactness every
     rule the LAFA deployed submission used: t0 cutoff, eval window,
     prediction pool, IA file, propagation (prop), normalization (norm),
     orphan handling, max_terms, threshold step, and how the gt file is
     constructed. Cross-check against protea-lafa-knn (t0=Sep 2025, 7401
     queries) AND the lab sweeps so there is ONE authoritative rule set.
  2. IA verified OK: reconcile the two IA sources
     (lab datasets/ia/IA-swissprot-exp-v227.txt vs
     protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv) -- same release, same
     term count, same values? Pick the authoritative one, document why.
  3. MINIMAL-OP VERDICT (gates the 24-cell decision): determine whether
     aligning the bench-v1 grid to v227 requires a full re-export
     (predictions regenerated at v227 train cutoff) or can be done by
     RE-SCORING the existing v226-cut predictions against the 227->230
     eval band (cheap, no new MinIO datasets). Quantify the disk cost of
     each path. GOA v227 and v230 are already ingested (verified
     2026-06-04), so re-scoring is plausible. Prove the verdict on ONE
     probe cell (e.g. prostt5 K3) before generalizing.
  4. Decide the fate of the hung phase2-lafa-v227 chain (0-preds,
     predict_go_terms coord bug): unblock via the recovery recipe or
     formally retire with rationale.
  5. Note the metrics-doc collision: lab PR #56 (docs/source/metrics.rst,
     comprehensive) vs PR #57 (docs/source/lafa_ia_metrics.rst) both add
     a metrics page to the toctree. Recommend which is canonical and how
     to deduplicate (do not merge here; just record the recommendation).
estimated_hours: 6
priority: P0
tags: [lafa, protocol, v227, ia-verify, minimal-op, disk-gated]
note: "ANALYSIS only; the 24-cell v227 grid (F-LAFA-IA.1b) is dispatched ONLY after this verdict + disk plan"
```

### F-LAFA-IA.2 — IA inside training (levers, gated)

```yaml
id: F-LAFA-IA.2
phase: F-LAFA-IA
loop: executor
status: done
shipped_via: "lab PR #60"
deps: [F-LAFA-IA.0, F-LAFA-IA.1]
acceptance: |-
  Lever 1 (probe): binary objective + weight=IA wired into both
  lgb.Dataset in reranker.py fit(), config flag ia_weighting
  (none|positives|all), probed on lk-bpo seed42. GATE: report wFmax
  reranker vs KNN (weighted and unweighted); if no wFmax lift over the
  F-LAFA-IA.0 baseline, STOP and report before proceeding. If it lifts:
  Lever 2 (lambdarank + IA-bucketed label_gain) and Lever 3 (custom
  feval = propagated IA-weighted Fmax proxy for early-stop). Fanout to
  the grid only after 3-5 cells validate. ADR in the lab recording the
  "IA-aligned training" decision + section-5 expectation management.
estimated_hours: 16
priority: P1
tags: [lafa, ia, lambdarank, training, gated, adr]
note: "gate at Lever 1; do NOT put cafaeval in the gradient loop (brief section 4)"
```

### F-LAFA-IA.1b — v227 probe re-export (1 cell) + IA-weighted eval

```yaml
id: F-LAFA-IA.1b
phase: F-LAFA-IA
loop: executor
status: done
shipped_via: "lab PR #59"
deps: [F-LAFA-IA.1]
acceptance: |-
  Validate the faithful v227 path on ONE probe cell before the 24-cell
  fanout. Steps:
  1. Construct the export_research_dataset payload for a v227-lineage
     probe cell: prostt5, K=3, TRAIN CUTOFF v227 (not v226), eval band
     227->230. Use the exact LAFA protocol pinned in F-LAFA-IA.1
     (lab PR #58, experiments/lafa_ia_v227_protocol/) + adapt from an
     existing v226-lineage prostt5 K3 dataset config (read its row via
     the API /v1/datasets or DB). Name it bench-v1-K3-v227-lineage-prostt5.
  2. Dispatch via dispatch_with_lock (FARM-FEAT.13, owner=export) to
     POST /v1/datasets. Stack is on NATIVE docker engine now (413G free,
     no Docker.raw); anc2vec + EXPORT_MINIJOBS=0 + perf env already set.
  3. Monitor the export job to SUCCEEDED (use the predict_go_terms coord
     recovery recipe from memory if it stalls at 0 preds: purge queue +
     dedupe pred_sets + force-finalize). Report per-cell DISK COST (root
     delta) for fanout planning.
  4. IA-weighted eval: cafaeval with ia=datasets/ia/IA-swissprot-exp-v227.txt
     on the v227 cell (reranker + KNN baseline), prop=fill norm=cafa
     no_orphans, headline = IA-weighted micro Fmax (wFmax) + S_min.
  5. Report the four numbers (internal Fmax / cafaeval Fmax / wFmax /
     S_min) AND the gap vs the LAFA-deployed-at-v227 score. GATE: state
     whether the v227 band closes the bench-vs-LAFA gap. If yes -> green
     light F-LAFA-IA.1c (24-cell fanout); if no -> stop and report why.
estimated_hours: 4
priority: P0
tags: [lafa, v227, probe, re-export, ia-weighted, dispatch-with-lock]
note: "release the stack-owner lock (owner=free) on completion; native engine so disk is no longer the constraint"
```

### FIX-ANON-PREDICT — anonymous annotation flow completes end-to-end

```yaml
id: FIX-ANON-PREDICT
phase: F-OPS
loop: executor
status: pending
deps: []
acceptance: |-
  The public anonymous annotation flow (home/functional-annotation form)
  must complete end-to-end without a 401. Root cause: `/embeddings/predict`
  (POST, protea/api/routers/embeddings.py ~line 185) is gated with
  `Depends(require_role(ROLE_OPERATOR))` + `Depends(require_user_quota("predict"))`,
  but the anon form's Step 3 (frontend `launchPredictGoTerms` -> POST
  /embeddings/predict) carries no token -> 401. Meanwhile `/annotate`
  (annotate.py) is anon via `Depends(require_anon_quota)`, and the home
  advertises anonymous annotation.
  FIX: let `/embeddings/predict` accept ANONYMOUS quota the same way
  `/annotate` does (mirror its auth: require_anon_quota, which also serves
  authenticated users). Do NOT break logged-in users (they keep their
  quota); just stop blocking anon. Apply the same to any other endpoint
  in the anon annotation chain that the frontend hits (verify the full
  AnnotateForm sequence: annotate -> poll embeddings -> predict ->
  prediction-set results all reachable anon). Keep anon rate-limited via
  anon_quota; do not disable auth globally.
  Local CI green (ruff+mypy+pytest+smell). PR to develop. Add/adjust a
  test asserting /embeddings/predict is reachable under anon quota.
estimated_hours: 2
priority: P0
tags: [auth, anon, annotation, demo, presentation]
note: "demo-critical for the presentation tomorrow; after merge, redeploy protea-deploy + re-verify E2E"
```

### FIX-PREDICT-COORD-RELIABLE — annotation finalizes reliably (production)

```yaml
id: FIX-PREDICT-COORD-RELIABLE
phase: F-OPS
loop: executor
status: pending
deps: []
acceptance: |-
  The public annotation flow (annotate -> embeddings -> predict_go_terms
  -> results) must finalize RELIABLY for any user, with the stale-job
  reaper RUNNING. Today it does not: a real anonymous insulin annotation
  produced 73 correct GO predictions but the predict_go_terms COORD job
  stuck at QUEUED/0%, and was requeued ~3 min in -> zombie + duplicate
  prediction_sets (RMQ re-delivery). The live UI spinner then hangs
  (AnnotateForm polls predict job for status==='succeeded').

  ROOT CAUSE (verified): the coord (protea/core/operations/predict_go_terms/
  _coordinator.py) seeds meta.expected_batches + batches_completed=0,
  dispatches KNN batches, returns OperationResult(deferred=True). BaseWorker
  keeps the job RUNNING but the lease (job.leased_until) is NOT renewed for
  a deferred coord. The StaleJobReaper requeues it once leased_until < now
  (lease_expired) BEFORE the slow batches (alignments + taxonomy + reranker
  features for the quick-annotation) finish and finalize the parent via
  _batch_op.py::_finalize_parent_if_last. #577 added the finalize but it
  RACES the reaper.

  FIX: make a deferred coordinator survive the reaper until its children
  finalize it, WITHOUT disabling the reaper. Cleanest: on deferred=True,
  set job.leased_until to a generous, configurable window (e.g. now +
  PROTEA_DEFERRED_LEASE_SECONDS, default ~3600) so the reaper does not
  reap a coord whose batches are still running; the batch-finalize flips
  it to SUCCEEDED; if the batches genuinely hang, the generous lease still
  lets the reaper clean it eventually. Make _finalize_parent_if_last
  idempotent + correct for the single-batch / quick-annotation case
  (expected_batches must be seeded correctly, including 1 batch). Prevent
  duplicate prediction_sets on any re-delivery.

  ACCEPTANCE: with the reaper RUNNING, a real anon insulin annotation
  reaches predict SUCCEEDED within a couple minutes, 3 runs in a row, no
  zombie QUEUED, no duplicate prediction_sets. Unit/integration tests for
  the deferred-lease + finalize + idempotency. Local CI green; PR to develop.
estimated_hours: 5
priority: P0
tags: [reliability, predict-coord, reaper, annotation, production, ops]
note: "operability > demo; conductor will redeploy + verify 3 real annotations after merge, then re-enable the reaper"
```

### FIX-ANNOTATE-BANNER-ACCURACY — GPU-busy banner reflects real work only

```yaml
id: FIX-ANNOTATE-BANNER-ACCURACY
phase: F-OPS
loop: executor
status: pending
deps: []
acceptance: |-
  The "Anotacion temporalmente no disponible / GPU compartida" banner in
  AnnotateForm (apps/web/components/AnnotateForm.tsx ~line 177-230) must
  reflect GENUINELY active GPU work only. Today it shows whenever ANY
  GPU-op job (compute_embeddings/predict_go_terms/export_research_dataset)
  is QUEUED or RUNNING -- including stale/zombie jobs with no live worker
  and no RMQ message, producing FALSE "GPU busy" walls that block the form
  when nothing is actually running. Fix: gate the banner on real activity
  (e.g. a job that is RUNNING with a fresh heartbeat / leased_until in the
  future, or actual queue depth + consumer activity), not merely a DB row
  in QUEUED/RUNNING. Consider a small backend availability endpoint that
  returns a truthful busy/free signal (queue depth + recently-progressing
  job), and have the frontend poll that. Stale jobs must NOT trip it.
  Local CI green; PR to develop. Verify: with 0 live GPU work the form is
  enabled; with a real running embedding it shows busy.
estimated_hours: 3
priority: P1
tags: [reliability, frontend, annotation, banner, ops]
```

### FIX-ANNOTATE-CONFIG-SLOW — /annotate fast (no 40s embedding-config scan)

```yaml
id: FIX-ANNOTATE-CONFIG-SLOW
phase: F-OPS
loop: executor
status: pending
deps: []
acceptance: |-
  POST /v1/annotate takes ~40s wall-clock, dominated by
  _best_embedding_config (protea/api/routers/annotate.py ~line 50): an
  outerjoin + GROUP BY over sequence_embedding (5.8M rows) to pick the
  smallest model that has embeddings. Make /annotate return in < ~2s.
  Options: a fast EXISTS-per-config probe instead of a full GROUP BY
  count, a cached/prewarmed "configs-with-embeddings" lookup (TTL cache
  like the other prewarms), or a covering index. Must keep picking a
  config that actually HAS embeddings for the chosen model (correctness).
  Measure before/after. Local CI green; PR to develop.
estimated_hours: 3
priority: P1
tags: [reliability, performance, annotation, ops]
```

### FIX-STACK-SELF-HEAL — stack boots robustly + stays up

```yaml
id: FIX-STACK-SELF-HEAL
phase: F-OPS
loop: executor
status: pending
deps: []
acceptance: |-
  "Operative always": the dev/deploy stack must boot correctly regardless
  of caller and self-recover from process death. Root incident tonight:
  `manage.sh start` run WITHOUT sourcing .env crashed the API
  (RuntimeError PROTEA_JWT_SECRET not set, AUTHN on) and it stayed down.
  Fixes: (1) make scripts/manage.sh SOURCE .env itself (set -a; source
  .env; set +a) at the top of cmd_start so a naive `manage.sh start` never
  crashes on missing env (memory project_stack_env_not_sourced_outage).
  (2) Add lightweight self-healing: a health-watchdog (systemd user units
  with Restart=on-failure + EnvironmentFile, OR a small supervised loop /
  cron that checks API :8000/health + worker pidfiles every ~30s and
  restarts any dead component WITH .env sourced). Keep it idempotent (no
  duplicate workers) and documented. Do NOT restart the stack while a
  long job (export/predict) is mid-flight without need. Local CI green;
  PR to develop (manage.sh + any scripts live in PROTEA repo).
estimated_hours: 5
priority: P0
tags: [reliability, ops, supervisor, stack, env-sourcing]
