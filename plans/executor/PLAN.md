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

### T2D.3 — services LOC cleanup

```yaml
id: T2D.3
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  protea/api/services/scoring_service.py <500 LOC
  protea/api/services/embeddings_service.py <500 LOC
  router tests green; no API-surface change
estimated_hours: 8
priority: P1
tags: [refactor, smell-budget, F2D-debt]
```

Residual debt from F2D: routers were capped at <400 LOC in the AC, but
services were not. Apply Extract Class when a single class concentrates
unrelated responsibilities (Divergent Change). Refactoring guru: Extract
Class, Move Method.

### T-CONTEXTS — Introduce Parameter Object

```yaml
id: T-CONTEXTS
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  KnnContext, FeatureBuildContext, ExportContext live in protea-contracts.contexts
  no productive function signature >6 args
  protea-contracts bumped to v0.2.0 (semver minor)
estimated_hours: 12
priority: P1
tags: [refactor, parameter-object, contracts]
```

Targets the 11-16 arg signatures: `_knn_transfer_and_label`,
`export_reranker_parquets`, `_dump_frozen_dataset`, `_predict_batch`.
Pydantic dataclasses. Refactoring guru: Introduce Parameter Object,
Preserve Whole Object.

### T1.7 — invariant tests cross-repo

```yaml
id: T1.7
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  Cross-repo invariants asserted in tests/test_contracts_invariants.py
  CI matrix runs against latest tagged versions of each plugin repo
estimated_hours: 6
priority: P2
tags: [tests, contracts]
```

### T1.8 — boundary validation

```yaml
id: T1.8
phase: F1
loop: executor
status: pending
deps: [T1.7]
acceptance: |-
  Pydantic schemas reject malformed payloads at every operation entry-point
  Contract tests cover at least one negative case per payload
estimated_hours: 4
priority: P2
tags: [tests, contracts]
```

### T2A.1 — esm backend entry_point

```yaml
id: T2A.1
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  protea-backends.esm registers protea.backend.esm via entry_points
  PROTEA compute_embeddings dispatches to plugin (not inline if-branch)
  Bit-exact embeddings vs the inline implementation on a 100-protein smoke set
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
```

### T2A.2 — t5 backend entry_point

```yaml
id: T2A.2
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  Same shape as T2A.1, for ProtT5
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
```

### T2A.3 — ankh backend entry_point

```yaml
id: T2A.3
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  Same shape as T2A.1, for Ankh
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
```

### T2A.4 — esm3c backend entry_point

```yaml
id: T2A.4
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  Same shape as T2A.1, for ESM-3C
estimated_hours: 6
priority: P2
tags: [refactor, plugin, backend]
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
```

Done in T54 per master plan §0.

### T2A.8 — knn + baseline runners entry_points

```yaml
id: T2A.8
phase: F1
loop: executor
status: pending
deps: []
acceptance: |-
  protea-runners.knn + protea-runners.baseline registered via entry_points
  PROTEA dispatches by name, not import path
estimated_hours: 4
priority: P3
tags: [refactor, plugin, runner]
```

## F2 — F2C wire complete

### F2C.5 — wire protea-method.predict() to predict_go_terms_batch

```yaml
id: F2C.5
phase: F2
loop: executor
status: pending
deps: [T-CONTEXTS]
acceptance: |-
  PROTEA predict_go_terms_batch delegates KNN + feature compute + apply_reranker
  to protea-method.pipeline.predict()
  PROTEA orchestrator <200 LOC for the operation body
  Bit-exact predictions vs current inline path on a regression test set
estimated_hours: 16
priority: P0
tags: [F-LAFA-gate, predict, F2C]
```

Bloqueante de F-LAFA v2. Sin esto, los containers v2 no pueden inferir.

## F3 — F1 close + F2B

### T1.6 — schema_sha v2 migration

```yaml
id: T1.6
phase: F3
loop: executor
status: blocked
deps: []
acceptance: |-
  Dataset + RerankerModel have schema_sha_v2 column populated
  Backfill from protea_contracts.compute_schema_sha verified
  Old schema_sha column kept until F8 cleanup
estimated_hours: 8
priority: P1
requires_human: true
tags: [migration, alembic]
```

D10 accepted 2026-05-06; blocked on Alembic on live DB + backfill
verification window.

### T2B.1 — FeatureRegistry implementation

```yaml
id: T2B.1
phase: F3
loop: executor
status: pending
deps: [T-CONTEXTS]
acceptance: |-
  protea/core/features/ package with FeatureRegistry abstraction
  Each feature family (alignment, taxonomy, anc2vec, lineage, ...) registered
  parquet_export consumes the registry, not inline compute
estimated_hours: 16
priority: P1
tags: [refactor, registry, features]
```

### T2B.2 — parquet_export refactor

```yaml
id: T2B.2
phase: F3
loop: executor
status: pending
deps: [T2B.1]
acceptance: |-
  parquet_export delegates feature compute to FeatureRegistry
  Golden parquet bit-exact gate passes
estimated_hours: 6
priority: P1
tags: [refactor, parquet, features]
```

### T2B.3 — _predict_batch decompose

```yaml
id: T2B.3
phase: F3
loop: executor
status: pending
deps: [T2B.1]
acceptance: |-
  _predict_batch decomposed using FeatureRegistry
  Predictions bit-exact vs pre-refactor on regression set
estimated_hours: 8
priority: P1
tags: [refactor, predict, features]
```

### T2B.4 — extract class on reranker pipeline

```yaml
id: T2B.4
phase: F3
loop: executor
status: blocked
deps: [T2B.3]
acceptance: |-
  Reranker scoring path lives in a dedicated class with single responsibility
estimated_hours: 8
priority: P2
requires_human: true
tags: [refactor, reranker]
```

Reranker-sensitive: human review needed before merge.

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

## F4 — F3 + F4 model + API

### T3.1-T3.4 — GOPrediction JSONB dual-write

```yaml
id: T3.1
phase: F4
loop: executor
status: blocked
deps: []
acceptance: |-
  GOPrediction features moved to JSONB column with dual-write transition
  Old columns kept until F8 cleanup
estimated_hours: 12
priority: P1
requires_human: true
tags: [migration, jsonb, alembic]
```

D3 accepted; requires DB migration window.

### T3.5 — index audit

```yaml
id: T3.5
phase: F4
loop: executor
status: pending
deps: []
acceptance: |-
  Every PG index audited; redundant indexes dropped via migration
  Frequent slow queries (>500ms in dev) covered by an index
estimated_hours: 4
priority: P3
tags: [migration, performance]
```

### T3.6 — nullables audit

```yaml
id: T3.6
phase: F4
loop: executor
status: pending
deps: []
acceptance: |-
  Every nullable column reviewed; spurious NULLs constrained via NOT NULL
  Migration covers data + schema with backfill where needed
estimated_hours: 4
priority: P3
tags: [migration, schema-quality]
```

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
status: pending
deps: []
acceptance: |-
  OTel SDK initialised at process start; spans on every request, every SQL,
  every AMQP publish/consume
  Traces exported via OTLP to a configurable endpoint
estimated_hours: 12
priority: P2
tags: [observability, otel, D7]
```

D7 accepted 2026-05-06. Autónomo.

### T5.2 — Prom /metrics endpoint

```yaml
id: T5.2
phase: F5
loop: executor
status: pending
deps: [T5.1]
acceptance: |-
  /metrics exposes process + custom counters/histograms
  Standard PROTEA metric names documented in docs/observability.rst
estimated_hours: 6
priority: P2
tags: [observability, prometheus, D7]
```

### T5.3 — Grafana dashboards

```yaml
id: T5.3
phase: F5
loop: executor
status: pending
deps: [T5.2]
acceptance: |-
  3 dashboards in deploy/grafana/: jobs, queues, predictions
  Provisioning via docker-compose.monitoring.yml
estimated_hours: 8
priority: P3
tags: [observability, grafana]
```

### T5.4 — Loki via loki-docker-driver

```yaml
id: T5.4
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  All container logs ship to Loki via loki-docker-driver
  Grafana dashboard queries log streams by container/service
estimated_hours: 4
priority: P3
tags: [observability, loki]
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
```

Done in T61.

### T5.6 — authn middleware (ApiKey + Bearer + slowapi)

```yaml
id: T5.6
phase: F5
loop: executor
status: blocked
deps: []
acceptance: |-
  ApiKey ORM + Bearer middleware + slowapi rate limit
  oauth2-proxy in deploy/nginx/ for human OIDC
estimated_hours: 12
priority: P1
requires_human: true
tags: [security, authn, D6]
```

D6 accepted; security-sensitive code paths need human review.

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
status: pending
deps: []
acceptance: |-
  protea-{contracts,method,sources,backends,runners,reranker-lab,cafaeval}
  each ship a Dockerfile + tagged image on ghcr.io
estimated_hours: 8
priority: P2
tags: [deployment, docker]
```

### T-OPS.2 — protea-bundle docker-compose

```yaml
id: T-OPS.2
phase: F5
loop: executor
status: pending
deps: [T-OPS.1]
acceptance: |-
  Single docker-compose.bundle.yml spins up the full stack from images
estimated_hours: 6
priority: P2
tags: [deployment, docker-compose]
```

### T-OPS.3 — Helm chart (mode B)

```yaml
id: T-OPS.3
phase: F5
loop: executor
status: pending
deps: [T-OPS.1]
acceptance: |-
  protea-chart/ Helm chart deploys the stack to a k8s cluster
estimated_hours: 12
priority: P3
tags: [deployment, helm, D25]
```

D25 accepted (mode B). Autónomo.

### T-OPS.4 — Docker Swarm stack file

```yaml
id: T-OPS.4
phase: F5
loop: executor
status: pending
deps: [T-OPS.1]
acceptance: |-
  deploy/swarm/stack.yml deploys the stack to a Swarm cluster
estimated_hours: 6
priority: P3
tags: [deployment, swarm]
```

### T-OPS.5 — SLURM mode B templates

```yaml
id: T-OPS.5
phase: F5
loop: executor
status: pending
deps: [T-OPS.1]
acceptance: |-
  deploy/slurm/ submission templates for HPC mode B
estimated_hours: 6
priority: P3
tags: [deployment, slurm, hpc]
```

### T-OPS.6 — pydantic-settings final

```yaml
id: T-OPS.6
phase: F5
loop: executor
status: pending
deps: []
acceptance: |-
  All env vars documented in protea/config/settings.py with descriptions
  YAML defaults overridable by env per documented hierarchy
estimated_hours: 4
priority: P2
tags: [config, deployment]
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
```

### T-OPS.11 — E2E deploy test

```yaml
id: T-OPS.11
phase: F5
loop: executor
status: pending
deps: [T-OPS.2]
acceptance: |-
  CI job spins up the bundle, hits /jobs to enqueue smoke ping, asserts success
estimated_hours: 6
priority: P2
tags: [deployment, e2e, ci]
```

### T-OPS.12 — protea-method-runtime image

```yaml
id: T-OPS.12
phase: F5
loop: executor
status: pending
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
status: blocked
deps: [F2C.5]
acceptance: |-
  protea-method.lineage feature consumed by predict_go_terms_batch
  Reranker uses lineage feature in production scoring
  Bit-exact cafaeval results reproducible against the lab champion
estimated_hours: 12
priority: P1
requires_human: true
tags: [research, lineage, reranker]
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
  Lab benchmark report (lab-runner T-LR-GeOKG) decides default
estimated_hours: 16
priority: P2
requires_human: true
tags: [research, embeddings, go]
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

## F7 — F-LAFA v2 reanudación

### F-LAFA.1 — protea-knn-v1 container

```yaml
id: F-LAFA.1
phase: F7
loop: executor
status: pending
deps: [T-OPS.12, F2C.5]
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
phase: F7
loop: executor
status: pending
deps: [F-LAFA.1]
acceptance: |-
  Multi-PLM ensemble container; 8 PLMs averaged at score level
  Submitted to LAFA
estimated_hours: 6
priority: P1
tags: [lafa, container, multi-plm]
```

### F-LAFA.3 — protea-v18 container with reranker + lineage

```yaml
id: F-LAFA.3
phase: F7
loop: executor
status: pending
deps: [F-LAFA.2, T-RES.1]
acceptance: |-
  v18 reranker + lineage feature shipping in container
  Submitted to LAFA only if lineage proves better than baseline
estimated_hours: 8
priority: P1
tags: [lafa, container, reranker, lineage]
```

## F8 — Cierre

### F6.1 — sleeps eliminated from tests

```yaml
id: F6.1
phase: F8
loop: executor
status: pending
deps: []
acceptance: |-
  Every test that uses time.sleep() replaced by event-driven wait
  pytest --collect-only | grep sleep returns 0
estimated_hours: 6
priority: P2
tags: [tests, quality]
```

### F6.2 — Hypothesis property tests

```yaml
id: F6.2
phase: F8
loop: executor
status: pending
deps: []
acceptance: |-
  Property tests on contract payloads + scoring + parquet roundtrip
  CI runs Hypothesis with deterministic seed
estimated_hours: 12
priority: P3
tags: [tests, hypothesis]
```

### F6.3 — mutation testing (cosmic-ray)

```yaml
id: F6.3
phase: F8
loop: executor
status: pending
deps: [F6.2]
acceptance: |-
  cosmic-ray run on protea/core/ with mutation score documented
estimated_hours: 8
priority: P3
tags: [tests, mutation]
```

### F6.4 — contract tests across plugin repos

```yaml
id: F6.4
phase: F8
loop: executor
status: pending
deps: [T1.7]
acceptance: |-
  Each plugin repo's CI runs contract tests against protea-contracts pinned version
estimated_hours: 6
priority: P2
tags: [tests, contracts, plugin]
```

### F6.5 — Playwright E2E

```yaml
id: F6.5
phase: F8
loop: executor
status: pending
deps: []
acceptance: |-
  Playwright suite in apps/web/ covers every critical user flow
  CI runs against the bundle from T-OPS.11
estimated_hours: 16
priority: P2
tags: [tests, e2e, playwright]
```

### F6.6 — coverage targets ≥85%

```yaml
id: F6.6
phase: F8
loop: executor
status: pending
deps: []
acceptance: |-
  Codecov gate ≥85% on protea/core/, ≥75% on protea/api/
estimated_hours: 8
priority: P2
tags: [tests, coverage]
```
