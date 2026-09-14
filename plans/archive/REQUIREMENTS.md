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

### FR-2: temporal-interval alignment with LAFA  [partial]
The platform reproduces the LAFA evaluation across LAFA's MULTIPLE rolling temporal
windows (the t0 to t1 intervals: Sep to Nov, Sep to Dec, Sep to Mar, Nov to Dec,
Nov to Mar, Dec to Mar, and the rest of the LAFA window set), not only the single
227 to 230 window used for the headline result. The leakage-clean protocol holds
window by window, and our per-window scores align with LAFA's per-window results.
- Rationale: LAFA is a CONTINUOUS benchmark; alignment on one window is not full
  alignment. Showing the method tracks LAFA across its intervals is what makes the
  comparison and the thesis claim complete.
- Acceptance: the eval surface reports our f_micro_w per LAFA temporal window, and
  they agree with LAFA's published per-window numbers within tolerance, using the
  same harness and the same frames; each window is staged leakage-clean (its t0
  reference is at or before that window's cutoff).
- Owner: Track 2 (the sealed grid) extended to the full LAFA window set.

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

### FR-4: confidence intervals on every reported score  [partial]
Every reported score carries a confidence interval (for example bootstrap), per cell
(category by aspect). A point estimate without an interval is not a complete result;
this raises the quality and defensibility of the whole project.
- Rationale: comparability and rigour. "Ahead of TransFew (0.381)" must hold with
  the uncertainty included, not as a bare point comparison. Already done offline
  (Experiment 8 reports bootstrap CIs); the requirement is to carry intervals through
  to the LAFA-frame surface and the headline numbers.
- Acceptance: the eval surface shows score plus CI per cell; the platform and the
  offline harness agree on both the point estimate and the interval; the thesis
  reports intervals for the headline figures, including the first-place mean.
- Owner: Track 1 / Track 2, extended to emit intervals (pairs naturally with FR-2).

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

### NFR-REPRO: end-to-end reproducibility  [partial]
The complete pipeline, from raw inputs (sequences, GOA releases, the OBO) through
embeddings, KNN, features, the classifier, and the per-category combiner, to the
sealed LAFA score, is reproducible END TO END. A third party reproduces the headline
result from the documentation and persisted artifacts alone, deterministically: there
is no uncontrolled randomness (randomness is averaged out by the converged
seed-averaging of NFR-PERF, not pinned to lucky seeds), every intermediate artifact
(datasets, embeddings, models, predictions) carries provenance back to the exact data
version, code commit, and config that produced it, and the platform and the offline
harness agree at every stage.
- Rationale: a doctoral result must be independently reproducible end to end, not
  only the final number; this is the scientific bar and underpins the defence. It
  unifies NFR-PERF's anti-winner's-curse discipline, NFR-DOCS's third-party docs, and
  NFR-INFRA's deployability into one acceptance test: someone else gets our number.
- Acceptance: a documented "from raw inputs to the sealed score" runbook that a third
  party executes without privileged access and reproduces the result within the
  converged seed band; every artifact is provenance-tagged; a CI/parity check asserts
  the native platform path and the offline harness agree end to end on a fixed frame.
- Owner: cross-cutting (Tracks 1, 2, 3, 5; the lab REPRODUCE.md and the versioned data
  model are the seeds). Pairs tightly with NFR-PERF (converged seed-averaging) and FR-3
  (the local inference product is the smallest end-to-end reproducible artefact).

## How this maps

- Thesis: add a requirements-engineering framing (enumerate FR/NFR; show the design
  and evaluation satisfy each). This complements the existing research questions.
- Plan: `plans/THESIS-FINISH.md` tracks are the delivery vehicles; each track names
  the requirement IDs it satisfies. This document is referenced from the plan and is
  the durable spec.
- Memory: the standing project requirements are recorded so every session works
  toward them.
