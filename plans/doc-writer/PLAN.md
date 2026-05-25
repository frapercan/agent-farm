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
note: "2026-05-16 janitor plugin-scan: protea-runners#7 + protea-sources#11 + protea-backends#18 + protea-contracts#11 + protea-method#14 + protea-reranker-lab#8 + cafaeval-protea#5 (all 2026-05-15 or earlier)"
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

## F-DATA-PACK — Dataset deliverable documentation

### F-DATA-PACK.3 — Dataset card per PLM (8 cards)

```yaml
id: F-DATA-PACK.3
phase: F-DATA-PACK
loop: doc-writer
status: pending
deps: [F-DATA-PACK.2]
acceptance: |-
  One dataset_card.md per PLM (8 total) aggregating the K={3,5,10} variants:
  PLM identity (model id, layer, pooling), embedding dimensionality, PCA config,
  per-K row counts, Fmax delta vs KNN baseline (from FARM-EXP.14/15), known limits
  Hugging Face dataset card schema (YAML front-matter) compatible
  Card references the Zenodo DOI (placeholder until F-DATA-PACK.5) using a
  zenodo_doi: TBD field that F-DATA-PACK.5 backfills
estimated_hours: 8
priority: P1
tags: [dataset, card, huggingface, plm, documentation]
requires_human: false
```

**Goal**: provide the per-PLM narrative suitable for a Hugging Face
datasets repository card or a chapter 6 appendix table.

**Touches**: `protea-reranker-lab/dataset_cards/{plm}_card.md` (8 files, generated).

**Suggested agent**: doc-writer.

### F-DATA-PACK.4 — FAIR/coverage provenance doc

```yaml
id: F-DATA-PACK.4
phase: F-DATA-PACK
loop: doc-writer
status: pending
deps: [F-DATA-PACK.3, FARM-EXP.15]
acceptance: |-
  protea-reranker-lab/docs/dataset_provenance.md covers: data sources
  (UniProt v226, v230, GO release), pipeline version (PROTEA commit SHA +
  schema_sha), split methodology (train v220-v226, eval v226-v230), PCA fit
  policy (transductive, full pool per PLM), leakage-free note (anc2vec
  artefact fix PROTEA 223299c), KNN baseline numbers per cell
  Document follows FAIR principles checklist: Findable (DOI placeholder),
  Accessible (download URL), Interoperable (parquet + JSON manifest),
  Reusable (license, provenance, schema)
  Chapter 6 / appendix A cites this document
estimated_hours: 6
priority: P1
tags: [dataset, fair, provenance, documentation, chapter-6]
requires_human: false
```

**Goal**: produce the citable provenance document that turns the dataset
family from "files we made" into a reusable research contribution.

**Touches**: `protea-reranker-lab/docs/dataset_provenance.md` (new),
reference pointer in `thesis/chapters/06-evaluation/` (chapter 6 appendix A).

**Suggested agent**: doc-writer.
