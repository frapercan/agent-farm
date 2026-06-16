# PROTEA requirements (requirements engineering)

The requirements that drive the platform, the thesis, and the finishing plan. The
author wants the work organised around these, in both the manuscript and the plan,
and worked on long-term. Functional requirements (FR) state what the system must
do; non-functional requirements (NFR) state how well. Each requirement has an ID, a
statement, a rationale, a verifiable acceptance criterion, and the owning track in
`plans/THESIS-FINISH.md`. This document is the single source of truth for the
requirements; the thesis carries a requirements-engineering framing that enumerates
them and evaluates how each is met, and every finishing-plan track maps back to one
or more requirement IDs.

Status legend: [met] satisfied and verifiable; [partial] in progress; [open] not
started. Requirements are durable: they do not expire when a milestone passes.

## Functional requirements

### FR-1: every operation is actionable from the UI  [partial]
Every platform operation (embedding, prediction, scoring, evaluation, dataset
export, annotation/ontology loading, co-occurrence build, reranker import, and any
future operation) must be invokable from the web UI. No operation is API-only or
CLI-only.
- Rationale: the UI is the single source of truth and the operable surface; a
  doctoral artefact must be usable without reading code.
- Acceptance: for each operation in the registry there is a UI affordance that
  dispatches it (with the right payload form) and surfaces its job status/result; a
  test enumerates the registry and asserts UI coverage.
- Owner: a UI-operations track (extends Track B / the UI work). Today the UI has
  /benchmark, /evaluation and job views; the gap is full operation coverage.

### FR-2: scores and intervals aligned with LAFA  [partial]
The platform reproduces LAFA's metric AND its uncertainty: not only the mean
f_micro_w per category/aspect but the confidence intervals, matching LAFA's harness
and its reported intervals.
- Rationale: a score without an interval is not comparable to LAFA; the thesis
  claims must be defensible with the same uncertainty quantification.
- Acceptance: /benchmark shows, per cell, the f_micro_w plus a CI (e.g. bootstrap)
  that agrees with LAFA's published intervals within tolerance; the offline harness
  and the platform agree on both.
- Owner: Track 1 (native integration) + Track 2 (the sealed grid), extended to emit
  intervals.

### FR-3: local LAFA-inference product with our method integrated  [open]
The final product includes LAFA runnable locally in INFERENCE mode (not the whole
infrastructure) with PROTEA's first-place method integrated, so a third party runs
the method on LAFA inputs without standing up the full stack.
- Rationale: the deliverable is a usable inference artefact, not only a research
  pipeline; this is the productisation of the #1 system for external use.
- Acceptance: a single container/entrypoint takes LAFA inputs and produces the
  reranked predictions reproducing the sealed score, documented and runnable from
  the docs alone, with no database/queue/worker stack required.
- Owner: Track 3 (LAFA submission/product) on top of Track 1.

## Non-functional requirements

### NFR-UI: accessible, aesthetic, documented, fully navigable, no dead-ends  [partial]
The UI is accessible (a11y), aesthetically high quality, documented, and fully
navigable: every state reachable, every flow designed end to end, no dead-ends
where avoidable. The flows are studied and designed, not accreted.
- Acceptance: an a11y audit passes (keyboard nav, contrast, ARIA); every page links
  onward (no orphan/dead-end views); a documented flow map covers the main user
  journeys; visual quality reviewed.
- Owner: UI track.

### NFR-TEST: state-of-the-art testing, complete functional coverage  [partial]
Tests cover the complete functionality, applying every implemented technique, with
testing pushed toward the state of the art (unit, integration, property-based,
mutation, end-to-end, contract, golden, leakage guards, and coverage of every
operation and feature family).
- Acceptance: coverage targets met across repos; mutation score tracked; every
  operation, feature family, and UI flow has a test; the test taxonomy is documented.
- Owner: a testing track (cross-cutting).

### NFR-INFRA: near-automatic deployability  [partial]
The infrastructure is easily deployable, close to one command / automatic, across
the supported modes (compose, swarm, k8s/helm, slurm), from a clean machine.
- Acceptance: a documented from-zero bootstrap brings up the full stack with minimal
  manual steps; the docker-compose path is validated; a cold-boot runbook exists.
- Owner: Track 5 (reproducibility/infra).

### NFR-DOCS: clear, complete, noise-free, semantically clean  [partial]
Documentation is clear and complete; noise is removed from docs AND code; the
structure is semantically clean in every aspect. Every doc has a function; secondary
material is moved to marked appendices; nothing of value is silently lost.
- Acceptance: the doc-quality track (Track 7) exit criteria are met; no stale numbers
  or contradictory entries; the marking convention applied to all deferred docs.
- Owner: Track 7.

### NFR-ARCH: hexagonal architecture, structurally scalable repos  [partial]
The hexagonal architecture (ports/adapters, domain decoupled from infrastructure and
delivery) is respected and strengthened. The repositories (the lab AND the rest)
must scale well structurally; they are currently immature ("green") and must be
matured: clear module boundaries, no leakage of infra into domain, room to grow
beyond the current method.
- Acceptance: a documented architecture map shows the hexagon (domain core,
  ports, adapters); the lab and satellite repos have a clean, scalable package
  structure; new methods/backends/sources slot in via ports without touching the core.
- Owner: a codebase/architecture track (cross-cutting), feeding the thesis design
  chapter.

### NFR-PROCESS: develop-centric, continuous ngrok deploy, continuous audit  [met-ongoing]
Work happens on `develop`; `develop` is deployed continuously and exposed via ngrok
so everything can be audited live at all times.
- Acceptance: PRs target develop; the live stack runs develop and is reachable via
  the ngrok tunnels (protea.ngrok.app etc.); changes are auditable on the live UI.
- Owner: process discipline (all tracks).

### NFR-PERF: 0.391 is not the ceiling  [open]
The first-place result (mean 0.391) is a floor, not a limit. Keep improving,
especially the trailing PK cell (0.215 vs 0.230), under the same leakage-clean,
anti-winner's-curse discipline (converged seed-averaging, fit on SELECT, sealed once
on TEST).
- Acceptance: documented, leakage-clean improvements that beat the current sealed
  mean and generalise on the SELECT-internal held-out check; PK headroom pursued.
- Owner: a continuous-improvement track (Track A science spine), kept open.

## How this maps

- Thesis: add a requirements-engineering framing (enumerate FR/NFR; show the design
  and evaluation satisfy each). This complements the existing research questions.
- Plan: `plans/THESIS-FINISH.md` tracks are the delivery vehicles; each track names
  the requirement IDs it satisfies. This document is referenced from the plan and is
  the durable spec.
- Memory: the standing project requirements are recorded so every session works
  toward them.
