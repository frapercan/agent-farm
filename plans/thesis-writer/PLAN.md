# thesis-writer — Plan

LaTeX manuscript slices. Lives in `~/Thesis2/thesis/`. Manuscript is in
English (no Spanish in `chapters/`). Author Francisco Miguel Pérez
Canales; co-supervisors David Orellana-Martín + Ana M. Rojas (always
"co-supervisors", never "advisor" singular).

Current snapshot (~16k words):

| Chapter | Words | Status |
|---|---|---|
| 01 introduction | 893 | preliminary |
| 02 biological background | 1396 | preliminary |
| 03 related work | 1634 | preliminary |
| 04 system design | 3535 | preliminary |
| 05 implementation | 1848 | preliminary |
| 06 evaluation | 3863 | preliminary |
| 07 conclusion | 995 | preliminary |
| appendix A | 317 | placeholder |
| appendix B | 1086 | placeholder |

## Phase semantics

| Phase | Theme |
|---|---|
| TC | Per-chapter sync with code + experiments + ADRs |
| TA | Abstract + frontmatter + acknowledgements |
| TB | Bibliography hygiene |
| TX | Cross-cutting (figures, em-dash sweep, ToC, glossary) |
| TD | Defensa-ready polish (final pass, slides) |

Hard constraints:
- INGLÉS only en `chapters/`
- Cero em-dashes (`---` / `--` / `—`) en prosa publicable; usar `, ` / `; ` /
  paréntesis o `\textemdash` cuando explícitamente quieras un dash literal
- Doctoral thesis (no master's)
- Cero menciones a Claude / AI assistance en repos públicos (incluida la tesis)
- Equipo CAFA 6 framing (no "individual entrant")
- PROTEA framing: "author and sole maintainer", no "lead engineer"

## TC — Per-chapter sync

### TC.1 — chapter 1 introduction final pass

```yaml
id: TC.1
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Motivation grounded in functional annotation gap + CAFA 6 results
  Contributions list matches actual delivered scope (PROTEA + protea-method + LAFA)
  Thesis statement crisp, single sentence
  Chapter map preview matches final chapter set
estimated_hours: 8
priority: P2
tags: [chapter-1, introduction]
```

### TC.2 — chapter 2 biological background depth check

```yaml
id: TC.2
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  GO ontology + aspects + IEA evidence codes covered
  Protein language model context (T5/ESM/Ankh) at appropriate depth for the audience
  No redundancy with related work chapter
estimated_hours: 6
priority: P3
tags: [chapter-2, background]
```

### TC.3 — chapter 3 related work expansion

```yaml
id: TC.3
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  CAFA history + winners + their methods
  TransFew, FunBind, GoCurator + comparable LAFA submitters
  GeOKG and other recent GO-DAG ML work
  Honest positioning (PROTEA's deltas + complements)
estimated_hours: 12
priority: P2
tags: [chapter-3, related-work]
```

### TC.4 — chapter 4 system design sync with F2D + F2C

```yaml
id: TC.4
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  System diagram reflects F2D services layer
  protea-contracts / protea-method / protea-{sources,backends,runners} split
  documented as Decision narrative (not implementation detail)
  Cross-reference D1-D30 ADRs
estimated_hours: 12
priority: P1
tags: [chapter-4, design, drift-prone]
```

### TC.5 — chapter 5 implementation sync (drift hotspot)

```yaml
id: TC.5
phase: TC
loop: thesis-writer
status: pending
deps: [TC.4]
acceptance: |-
  Module names + endpoints + ORM models match current code
  Code listings cite line numbers via cross-ref macros (not hardcoded)
  Re-validate after every executor PR that renames or moves
estimated_hours: 12
priority: P1
tags: [chapter-5, implementation, drift-prone]
```

### TC.6 — chapter 6 evaluation refresh

```yaml
id: TC.6
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  All cafaeval Fmax / coverage / AuPRC numbers updated to leakage-free baseline
  Paired CIs from lab-runner LB.3 imported as figures + tables
  v22 lineage delta (if positive) added as section
  Per-cell × aspect tables canonical
  CAFA 6 #2 framing as TEAM result, not individual
estimated_hours: 16
priority: P1
tags: [chapter-6, evaluation, drift-prone, lab-numbers]
```

### TC.7 — chapter 7 conclusion + future work

```yaml
id: TC.7
phase: TC
loop: thesis-writer
status: pending
deps: [TC.1, TC.6]
acceptance: |-
  Conclusion mirrors thesis statement of chapter 1
  Future work covers: PROTEA-DL piloto (R-GCN + GO-DAG), GeOKG generalisation
  if not landed, ensemble multi-K, granular plugin split (F9)
  No new content not foreshadowed in earlier chapters
estimated_hours: 4
priority: P2
tags: [chapter-7, conclusion]
```

### TC.8 — appendix A regeneration

```yaml
id: TC.8
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Appendix A serves a defined purpose (current 317 words is a placeholder).
  Decide: reproducibility checklist, dataset card catalogue, or drop.
estimated_hours: 4
priority: P3
tags: [appendix-A]
```

### TC.9 — appendix B refresh

```yaml
id: TC.9
phase: TC
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Appendix B (currently 1086 words) clearly scoped + cross-referenced
  from main chapters
estimated_hours: 4
priority: P3
tags: [appendix-B]
```

## TA — Abstract + frontmatter

### TA.1 — abstract refactor with real numbers

```yaml
id: TA.1
phase: TA
loop: thesis-writer
status: pending
deps: [TC.6]
acceptance: |-
  Abstract opens with the gap, names PROTEA, gives 1-2 headline numbers
  (e.g., LAFA submission rank, leakage-free Fmax delta), closes with the
  doctoral contribution
  ≤300 words; no em-dashes; no acronym-heavy first sentence
estimated_hours: 4
priority: P1
tags: [abstract, frontmatter]
```

### TA.2 — title page + supervisors block

```yaml
id: TA.2
phase: TA
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Author name exact: Francisco Miguel Pérez Canales
  Co-supervisors: David Orellana-Martín, Ana M. Rojas (always "co-")
  Department + university block matches Universidad de Sevilla template
estimated_hours: 1
priority: P1
tags: [title-page, frontmatter]
```

### TA.3 — acknowledgements

```yaml
id: TA.3
phase: TA
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Acknowledgements written; CABD + FANTASIA team acknowledged appropriately;
  no AI assistance mentioned
estimated_hours: 2
priority: P2
tags: [acknowledgements, frontmatter]
```

## TB — Bibliography

### TB.1 — bib entries audit

```yaml
id: TB.1
phase: TB
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Every \cite resolves; no dangling refs in pdflatex log
  Underscores in fields escaped per memory bib_underscore_escape
  CAFA, TransFew, FunBind, GoCurator, GeOKG, anc2vec, ESM/T5/Ankh papers cited
estimated_hours: 6
priority: P1
tags: [bib]
```

### TB.2 — DOI + URL backfill

```yaml
id: TB.2
phase: TB
loop: thesis-writer
status: pending
deps: [TB.1]
acceptance: |-
  Every entry has a DOI or stable URL
estimated_hours: 4
priority: P3
tags: [bib]
```

## TX — Cross-cutting

### TX.1 — em-dash sweep across chapters

```yaml
id: TX.1
phase: TX
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Zero `---` / `--` / `—` in chapters/*.tex (per memory feedback_no_em_dashes)
  pdflatex log unchanged
estimated_hours: 2
priority: P1
tags: [style, em-dash]
```

### TX.2 — figures regeneration from real data

```yaml
id: TX.2
phase: TX
loop: thesis-writer
status: pending
deps: [TC.6]
acceptance: |-
  Every figure regenerated from latest experimental data
  Source scripts in figures/ alongside outputs
  Captions name the source script + git sha
estimated_hours: 12
priority: P1
tags: [figures, drift-prone]
```

### TX.3 — ToC + LoF + LoT

```yaml
id: TX.3
phase: TX
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  ToC, list of figures, list of tables render correctly
  Chapter / section depth matches Universidad de Sevilla doctoral template
estimated_hours: 2
priority: P3
tags: [frontmatter]
```

### TX.4 — glossary entries

```yaml
id: TX.4
phase: TX
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Glossary covers technical acronyms (PLM, KNN, GO, IEA, EXP, BP/MF/CC, ...)
  Cross-linked from first use in each chapter
estimated_hours: 4
priority: P3
tags: [glossary]
```

## TD — Defensa-ready

### TD.1 — final read pass + supervisor review

```yaml
id: TD.1
phase: TD
loop: thesis-writer
status: blocked
deps: [TC.7, TA.1, TB.1, TX.1, TX.2]
acceptance: |-
  Full read by author + co-supervisors
  Edits incorporated; no open TODOs in chapters/
estimated_hours: 16
priority: P1
requires_human: true
tags: [review, polish]
```

### TD.2 — defensa slides

```yaml
id: TD.2
phase: TD
loop: thesis-writer
status: pending
deps: [TD.1]
acceptance: |-
  Slide deck of ~30 slides, 50 min talk + 10 min Q&A allotment
  PROTEA architecture diagram + headline experimental numbers + LAFA result
estimated_hours: 12
priority: P1
tags: [slides, defensa]
```

### TD.3 — deposit-ready PDF

```yaml
id: TD.3
phase: TD
loop: thesis-writer
status: pending
deps: [TD.1]
acceptance: |-
  pdflatex builds clean (zero warnings except known acceptable ones)
  Embedded fonts; PDF/A compliance per university requirement
  Final filename + metadata correct
estimated_hours: 4
priority: P1
tags: [deposit, polish]
```
