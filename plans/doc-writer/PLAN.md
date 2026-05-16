# doc-writer — Plan

Sphinx documentation initiatives + ADR maintenance + runbooks across the
PROTEA repo stack. Lives in PROTEA `docs/source/`. Drift detection is
the loop's standing job (no slice needed); slices below are about
adding net new documentation surface or doing structural sweeps.

## Phase semantics

| Phase | Theme |
|---|---|
| F7 | Final docs delivery (READMEs, ADRs, runbooks, plugin author guide, insights) |
| DS | Drift sweeps (em-dashes, naming, code refs) — recurring, not project-bound |
| DR | Reference material (autodoc, OpenAPI alignment, glossary) |

Hard constraints:
- Tesis está en inglés; PROTEA docs también en inglés
- Cero em-dashes (`--` o `—`) en prosa publicable; usar punto / coma / paréntesis
- ADRs siguen plantilla MADR (`docs/source/adr/`); commits siguen convención del repo
- No tocar código en este loop; abrir issue al executor si la doc revela bug

## F7 — Final docs delivery

### F7.1 — READMEs per repo final pass

```yaml
id: F7.1
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  Each repo (PROTEA + 8 plugins) has a README.md with: install, run, test,
  contribute, license. No stub READMEs.
estimated_hours: 8
priority: P2
tags: [readme, repo-stack]
```

### F7.2 — ADR sweep & numbering harmonisation

```yaml
id: F7.2
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  ADRs 001-008 (numbered) renamed to D01-D08 OR documented as historical
  (decision: rename to keep convention, or keep numbered with prefix note)
  All ADRs follow MADR template
estimated_hours: 6
priority: P3
tags: [adr]
note: "2026-05-16 janitor reconcile: shipped via PR #309 (2026-05-12)"
```

### F7.3 — runbooks per critical operation

```yaml
id: F7.3
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  Runbook for: stale job reaper, ngrok deploy recovery, DLQ triage,
  embedding worker OOM diagnostic, schema_sha v2 backfill
  Located in docs/source/runbooks/
  (delivered via PR #293 on 2026-05-11; supplemented by PR #295 on 2026-05-11)
estimated_hours: 8
priority: P2
tags: [runbooks, ops]
```

### F7.4 — plugin author guide

```yaml
id: F7.4
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  How to write a new backend / runner / source plugin: scaffold, contracts,
  entry_points, tests, ship
  Worked example using a fictional toy plugin
estimated_hours: 8
priority: P2
tags: [plugin, guide]
note: "2026-05-16 janitor reconcile: shipped via PR #287 (2026-05-11)"
```

### F7.5 — insights appendix (lessons learned)

```yaml
id: F7.5
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  docs/source/insights.rst with the gotchas surfaced during F-EXP campaign
  Cross-references thesis chapter 6 + relevant ADRs
  (delivered via PR #298 on 2026-05-11)
estimated_hours: 6
priority: P3
tags: [insights, narrative]
```

### F7.6 — observability runbook (post T5.x)

```yaml
id: F7.6
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  docs/source/observability.rst describes OTel + Prom + Grafana + Loki
  setup, standard metrics, dashboards
estimated_hours: 6
priority: P2
tags: [observability, runbook]
```

Blocked on executor T5.1-T5.4.

### F7.7 — deployment guide (post T-OPS)

```yaml
id: F7.7
phase: F7
loop: doc-writer
status: done
deps: []
acceptance: |-
  docs/source/deployment/ covers compose, Helm, Swarm, SLURM with worked
  examples + per-mode caveats (D25)
estimated_hours: 8
priority: P2
tags: [deployment, runbook]
```

Blocked on executor T-OPS.10.

## DS — Drift sweeps

### DS.1 — em-dash sweep across docs

```yaml
id: DS.1
phase: DS
loop: doc-writer
status: done
deps: []
acceptance: |-
  Every `--` and `—` in docs/source/ replaced per house style
  (point/comma/parens/`\textemdash`)
  CI rule blocks new em-dashes in prose
estimated_hours: 3
priority: P2
tags: [style, em-dash]
note: "2026-05-16 janitor reconcile: verified done via scan; 4 em-dashes exist only in code/literal blocks"
```

### DS.2 — code reference drift gate

```yaml
id: DS.2
phase: DS
loop: doc-writer
status: done
deps: []
acceptance: |-
  CI fails when docs reference a symbol that doesn't exist in code
  (e.g. via sphinx :py:func: roles)
  (delivered via PR #286 on 2026-05-11)
estimated_hours: 4
priority: P2
tags: [drift, ci]
```

### DS.3 — OpenAPI cross-reference

```yaml
id: DS.3
phase: DS
loop: doc-writer
status: done
deps: []
acceptance: |-
  docs/source/api/ pages cross-link to OpenAPI spec entries
  Drift detected by openapi-drift workflow
  (delivered via PR #289 on 2026-05-12)
estimated_hours: 4
priority: P2
tags: [api, drift]
```

## DR — Reference material

### DR.1 — autodoc coverage audit

```yaml
id: DR.1
phase: DR
loop: doc-writer
status: done
deps: []
acceptance: |-
  Every public symbol in protea/core/ + protea/api/ has a docstring rendered
  by autodoc; missing docstrings logged + filed
  (delivered via PR #291 on 2026-05-11)
estimated_hours: 8
priority: P2
tags: [autodoc]
```

### DR.2 — glossary

```yaml
id: DR.2
phase: DR
loop: doc-writer
status: done
deps: []
acceptance: |-
  docs/source/glossary.rst defines key terms (PLM, KNN, K, GO, aspect,
  reconciled, prediction set, query set, eval set, schema_sha, ...)
  (delivered via PR #301 on 2026-05-12)
estimated_hours: 3
priority: P3
tags: [glossary]
```

### DR.3 — architecture diagrams update

```yaml
id: DR.3
phase: DR
loop: doc-writer
status: done
deps: []
acceptance: |-
  Mermaid + plantuml diagrams updated to reflect F2D services layer +
  protea-contracts split
  (delivered via PR #308 on 2026-05-12)
estimated_hours: 4
priority: P3
tags: [architecture, diagrams]
```
