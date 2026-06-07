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
status: done
deps: []
acceptance: |-
  Motivation grounded in functional annotation gap + CAFA 6 results
  Contributions list matches actual delivered scope (PROTEA + protea-method + LAFA)
  Thesis statement crisp, single sentence
  Chapter map preview matches final chapter set
estimated_hours: 8
priority: P2
tags: [chapter-1, introduction]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #29 (2026-05-11)"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TC.2 — chapter 2 biological background depth check

```yaml
id: TC.2
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  GO ontology + aspects + IEA evidence codes covered
  Protein language model context (T5/ESM/Ankh) at appropriate depth for the audience
  No redundancy with related work chapter
estimated_hours: 6
priority: P3
tags: [chapter-2, background]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #36 (2026-05-15)"
```

Shipped via thesis PR #36 2026-05-15.

### TC.3 — chapter 3 related work expansion

```yaml
id: TC.3
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  CAFA history + winners + their methods
  TransFew, FunBind, GoCurator + comparable LAFA submitters
  GeOKG and other recent GO-DAG ML work
  Honest positioning (PROTEA's deltas + complements)
estimated_hours: 12
priority: P2
tags: [chapter-3, related-work]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TC.4 — chapter 4 system design sync with F2D + F2C

```yaml
id: TC.4
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  System diagram reflects F2D services layer
  protea-contracts / protea-method / protea-{sources,backends,runners} split
  documented as Decision narrative (not implementation detail)
  Cross-reference D1-D30 ADRs
estimated_hours: 12
priority: P1
tags: [chapter-4, design, drift-prone]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TC.5 — chapter 5 implementation sync (drift hotspot)

```yaml
id: TC.5
phase: TC
loop: thesis-writer
status: done
deps: [TC.4]
acceptance: |-
  Module names + endpoints + ORM models match current code
  Code listings cite line numbers via cross-ref macros (not hardcoded)
  Re-validate after every executor PR that renames or moves
estimated_hours: 12
priority: P1
tags: [chapter-5, implementation, drift-prone]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TC.6 — chapter 6 evaluation refresh

```yaml
id: TC.6
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  All cafaeval Fmax / coverage / AuPRC numbers updated to leakage-free baseline
  Paired CIs from bioinfo-quick LB.3 imported as figures + tables
  v22 lineage delta (if positive) added as section
  Per-cell × aspect tables canonical
  CAFA 6 #2 framing as TEAM result, not individual
estimated_hours: 16
priority: P1
tags: [chapter-6, evaluation, drift-prone, lab-numbers]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TC.7 — chapter 7 conclusion + future work

```yaml
id: TC.7
phase: TC
loop: thesis-writer
status: done
deps: [TC.1, TC.6]
acceptance: |-
  Conclusion mirrors thesis statement of chapter 1
  Future work covers: dataset packaging (bench-v1-K{3,5,10}-v226-lineage-{plm}
  FAIR release), ensemble multi-K, granular plugin split (F9)
  (PROTEA-DL piloto / R-GCN deferred per [[dl-postponed-2026-05-25]];
  GeOKG deferred per [[geokg-nogo-2026-05-17]])
  No new content not foreshadowed in earlier chapters
estimated_hours: 4
priority: P2
tags: [chapter-7, conclusion]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #35 (2026-05-15). 2026-05-25 future-work text updated: DL piloto deferred [[dl-postponed-2026-05-25]]; deliverable reframed as FAIR dataset packaging."
```

Shipped via thesis PR #35 2026-05-15.

### TC.8 — appendix A regeneration

```yaml
id: TC.8
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Appendix A serves a defined purpose (current 317 words is a placeholder).
  Decide: reproducibility checklist, dataset card catalogue, or drop.
estimated_hours: 4
priority: P3
tags: [appendix-A]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #40 (2026-05-16)"
```

### TC.9 — appendix B refresh

```yaml
id: TC.9
phase: TC
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Appendix B (currently 1086 words) clearly scoped + cross-referenced
  from main chapters
estimated_hours: 4
priority: P3
tags: [appendix-B]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #42 (2026-05-16)"
```

## TA — Abstract + frontmatter

### TA.1 — abstract refactor with real numbers

```yaml
id: TA.1
phase: TA
loop: thesis-writer
status: done
deps: [TC.6]
acceptance: |-
  Abstract opens with the gap, names PROTEA, gives 1-2 headline numbers
  (e.g., LAFA submission rank, leakage-free Fmax delta), closes with the
  doctoral contribution
  ≤300 words; no em-dashes; no acronym-heavy first sentence
estimated_hours: 4
priority: P1
tags: [abstract, frontmatter]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TA.2 — title page + supervisors block

```yaml
id: TA.2
phase: TA
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Author name exact: Francisco Miguel Pérez Canales
  Co-supervisors: David Orellana-Martín, Ana M. Rojas (always "co-")
  Department + university block matches Universidad de Sevilla template
estimated_hours: 1
priority: P1
tags: [title-page, frontmatter]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TA.3 — acknowledgements

```yaml
id: TA.3
phase: TA
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Acknowledgements written; CABD + FANTASIA team acknowledged appropriately;
  no AI assistance mentioned
estimated_hours: 2
priority: P2
tags: [acknowledgements, frontmatter]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #43 (2026-05-16)"
```

## TB — Bibliography

### TB.1 — bib entries audit

```yaml
id: TB.1
phase: TB
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Every \cite resolves; no dangling refs in pdflatex log
  Underscores in fields escaped per memory bib_underscore_escape
  CAFA, TransFew, FunBind, GoCurator, GeOKG, anc2vec, ESM/T5/Ankh papers cited
estimated_hours: 6
priority: P1
tags: [bib]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #37 (2026-05-15)"
```

Shipped via thesis PR #37 2026-05-15.

### TB.2 — DOI + URL backfill

```yaml
id: TB.2
phase: TB
loop: thesis-writer
status: done
deps: [TB.1]
acceptance: |-
  Every entry has a DOI or stable URL
estimated_hours: 4
priority: P3
tags: [bib]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #38 (2026-05-15)"
```

Shipped via thesis PR #38 2026-05-15.

## TX — Cross-cutting

### TX.1 — em-dash sweep across chapters

```yaml
id: TX.1
phase: TX
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Zero `---` / `--` / `—` in chapters/*.tex (per memory feedback_no_em_dashes)
  pdflatex log unchanged
estimated_hours: 2
priority: P1
tags: [style, em-dash]
note: "2026-05-16 janitor reconcile: verified pre-session per shepherd 2026-05-15 git audit"
```

Shipped pre-session (per shepherd 2026-05-15 git audit).

### TX.2 — figures regeneration from real data

```yaml
id: TX.2
phase: TX
loop: thesis-writer
status: done
deps: [TC.6]
acceptance: |-
  Every figure regenerated from latest experimental data
  Source scripts in figures/ alongside outputs
  Captions name the source script + git sha
estimated_hours: 12
priority: P1
tags: [figures, drift-prone]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #44 (2026-05-16) + #45; fixes via PR #46"
```

### TX.3 — ToC + LoF + LoT

```yaml
id: TX.3
phase: TX
loop: thesis-writer
status: done
deps: []
acceptance: |-
  ToC, list of figures, list of tables render correctly
  Chapter / section depth matches Universidad de Sevilla doctoral template
estimated_hours: 2
priority: P3
tags: [frontmatter]
note: "2026-05-16 janitor reconcile: shipped via thesis PR #41 (2026-05-15)"
```

### TX.4 — glossary entries

```yaml
id: TX.4
phase: TX
loop: thesis-writer
status: done
deps: []
acceptance: |-
  Glossary covers technical acronyms (PLM, KNN, GO, IEA, EXP, BP/MF/CC, ...)
  Cross-linked from first use in each chapter
estimated_hours: 4
priority: P3
tags: [glossary]
note: "2026-05-16 janitor reconcile: verified done; no explicit PR but committed inline"
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


## Phase PAPER-TMLR — TMLR submission with Reproducibility Certification

Post-thesis productisation: turn cap 6 (v27-binary champion + paired CIs)
and cap 7 (F-DATA-PACK) into a TMLR manuscript and chase the
Reproducibility Certification (free, no APC). Sequential prereqs unless
noted otherwise. Strategy: parallel with TD.* if defense has runway,
otherwise sequential post-defense.

### PAPER-TMLR.0 — Strategy lock + cert target decision

```yaml
id: PAPER-TMLR.0
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: []
acceptance: |-
  Decision recorded in a memory entry (or ADR D40 in PROTEA repo):
   - venue confirmed (TMLR)
   - certification targeted (Reproducibility; optionally Featured as stretch)
   - timeline (parallel with TD.* vs strictly post-defense)
   - co-supervisor co-author order locked
   - cap 6 / cap 7 reuse percentage agreed (~70%)
  Open the OpenReview submission profile + confirm ORCID for all authors.
estimated_hours: 1
priority: P1
tags: [paper, decision]
requires_human: true
```

### PAPER-TMLR.1 — LaTeX scaffold + bibliography port

```yaml
id: PAPER-TMLR.1
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.0]
acceptance: |-
  New paper repo or subdir at ~/Thesis2/paper-tmlr/ with the official
  TMLR LaTeX class + style files, bibliography file ported from
  ~/Thesis2/thesis/refs.bib (or equivalent), 12-section skeleton
  (abstract, intro, related, method, experiments, datasets,
  reproducibility, discussion, broader impact, refs, appendix), and a
  Makefile target that builds clean to paper.pdf.
  Verify the build pipeline produces a one-column anonymous draft
  identical to TMLR template requirements.
estimated_hours: 2
priority: P1
tags: [paper, scaffold]
```

### PAPER-TMLR.2 — Introduction + Related Work

```yaml
id: PAPER-TMLR.2
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.1]
acceptance: |-
  Intro frames CAFA challenge motivation + post-CAFA-6 #2 productisation
  story (team result, technical motor, not individual entrant per
  CLAUDE.md framing). Contributions list explicit:
   (a) v27-binary recipe with paired-CI publishable Fmax,
   (b) anc2vec replication-artifact diagnosis + structural fix,
   (c) F-DATA-PACK 8-PLM benchmark family with full provenance.
  Related Work covers CAFA-style methods (NetGO3, DeepGO, etc.),
  embedding-based transfer (PLM + KNN), reranking literature (learning
  to rank, LightGBM in IR), and dataset benchmarks (CAFA, GOA timelines).
  ~3 pages combined.
estimated_hours: 6
priority: P1
tags: [paper, writing]
```

### PAPER-TMLR.3 — Method section

```yaml
id: PAPER-TMLR.3
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.1]
acceptance: |-
  Method section (~5 pages) covers:
   - 8 PLM embedding backends (ESM2 150m/650m/3B, ProtT5, ProstT5, Ankh
     base/large, ESMC 600m) with HF source + config_id pinning
   - KNN retrieval (faiss flat) over hydrated v226 train pool
   - Vote-to-ancestor expansion via anc2vec
   - LightGBM reranker with lineage features, recipe v27-binary
     (per-aspect-per-category binary classifiers, 3-seed median)
   - Feature families catalog (FEATURE_FAMILIES from protea-contracts)
   - PCA(16) transductive per-PLM cache (per memory
     project_pca_transductive_decision_2026_05_20)
  Algorithms in pseudocode where helpful. No reproducibility-critical
  param hidden behind 'Advanced' (memory:
  feedback_ui_surface_provenance_not_hide_params applies to the paper too).
estimated_hours: 8
priority: P1
tags: [paper, writing]
```

### PAPER-TMLR.4 — Experiments + Results (port from thesis cap 6)

```yaml
id: PAPER-TMLR.4
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.3, FARM-EXP.13]
acceptance: |-
  Experiments section ports thesis cap 6 with TMLR styling:
   - v27-binary champion table (Fmax 0.7291 +/- 0.0028, 3 seeds, 6/6 cells
     significant at 95% vs v22 baseline except lk-mfo per memory
     project_v27_binary_multiseed_2026_05_18)
   - Paired-CI table vs KNN baseline (publishable claim from
     project_lb3_paired_ci_2026_05_18)
   - Full (PLM x K x recipe) grid on v226 -> v230 from FARM-EXP.13-18,
     reported as a full table not a winners-curse selection (per memory
     project_multi_plm_report_full_grid)
   - Selective-deploy policy (NK+LK -> v27-binary, PK -> KNN baseline)
   - Per-aspect feature importance audit (memory
     project_lm3_feature_importance_2026_05_18)
  All tables generated by a script committed to the paper repo so
  reviewers can regenerate from raw cafaeval outputs.
estimated_hours: 6
priority: P1
tags: [paper, writing, tables]
```

### PAPER-TMLR.5 — Datasets section (port from thesis cap 7, F-DATA-PACK)

```yaml
id: PAPER-TMLR.5
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.4]
acceptance: |-
  Datasets section presents F-DATA-PACK (8 datasets, v226 -> v230) as the
  primary contribution alongside the method:
   - Per-dataset shortid + schema_sha + manifest_sha + producer_git_sha
     listed in a single table (data sourced from PROTEA's dataset table
     not from PDF copy)
   - anc2vec replication-artifact framing per memory
     project_anc2vec_leakage_mechanism (NOT label-leakage temporal —
     'replication artifact' is the correct technical story)
   - FAIR/coverage doc summary (F-DATA-PACK.4 output reused)
   - Discussion of v226-prostt5-K5 naming anomaly per memory
     project_prostt5_k5_naming_anomaly (legacy key_prefix preserved by
     design)
  ~3 pages.
estimated_hours: 4
priority: P1
tags: [paper, writing, datasets]
```

### PAPER-TMLR.6 — Reproducibility Statement + repro script verification

```yaml
id: PAPER-TMLR.6
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.5, F-DATA-PACK.5, PAPER-TMLR.9]
acceptance: |-
  Reproducibility Statement (mandatory TMLR section, ~1 page):
   - Zenodo DOIs for each of the 8 F-DATA-PACK datasets (depends on
     F-DATA-PACK.5 Zenodo upload landing)
   - GitHub release tags v1.0 for each of the 8 PROTEA repos (depends
     on PAPER-TMLR.9)
   - Explicit reproduction recipe: one command per artefact, using
     pinned schema_sha + manifest_sha (memory
     feedback_ui_surface_provenance_not_hide_params validates this is
     the right hook surface)
   - Compute requirements section (CPU/GPU specs, wall-clock per cell:
     1.5-3h, total sweep 24-48h)
   - End-to-end repro script committed to the paper repo + executed
     against the published artefacts to verify it works as written
  This section is the certification gate; reviewers will run the script
  in a fresh environment.
estimated_hours: 6
priority: P0
tags: [paper, reproducibility, cert-gate]
```

### PAPER-TMLR.7 — Discussion + Broader Impact + Abstract + final polish

```yaml
id: PAPER-TMLR.7
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.2, PAPER-TMLR.3, PAPER-TMLR.4, PAPER-TMLR.5, PAPER-TMLR.6]
acceptance: |-
  Discussion (~2 pages): selective-deploy policy rationale, anc2vec
  artifact lessons-for-the-field, limitations (compute-bound, UniProt
  sampling bias, no DL champion per memory
  project_dl_postponed_2026_05_25), future work hooks (multi-PLM
  ensemble, GeOKG when full-text Fmax improves per memory
  project_geokg_nogo_2026_05_17, neural-head if compute available).
  Broader Impact (mandatory TMLR section, ~1/2 page): biology
  application scope, potential misuse low (annotation transfer, not
  clinical), open-data benefit.
  Abstract: 200 words, lead with #2 CAFA-6 context + v27-binary +
  F-DATA-PACK as combined contribution.
  Full bibliography clean (BibTeX format consistent, all DOIs filled),
  proofread pass for em-dashes (CLAUDE.md hard constraint).
estimated_hours: 6
priority: P1
tags: [paper, writing, polish]
```

### PAPER-TMLR.10 — Anonymization sweep + OpenReview submission

```yaml
id: PAPER-TMLR.10
phase: PAPER-TMLR
loop: thesis-writer
status: pending
deps: [PAPER-TMLR.6, PAPER-TMLR.7, PAPER-TMLR.9]
acceptance: |-
  Double-blind preparation pass:
   - Strip author names, grant numbers, affiliations from main PDF
   - Replace frapercan/* GitHub URLs with anonymized archive URLs
     (anonymous.4open.science or similar)
   - Strip ORCID, ResearchGate, personal blog refs from bibliography
   - Co-supervisor names removed from Acknowledgements (TMLR adds them
     at camera-ready)
  Upload to OpenReview with cert-request checkbox 'Reproducibility'
  (and optionally 'Featured' if PAPER-TMLR.0 strategy includes it).
  Set the Action Editor request appropriately (TMLR allows author
  preference). Confirm submission ID + receipt email.
estimated_hours: 3
priority: P0
tags: [paper, submission]
requires_human: true
```



## Phase COMPLEXITY — Formal computational complexity model of PROTEA

Standalone LaTeX project (`~/Thesis2/complexity-paper/`) applying classical
complexity theory + membrane-computing complexity (Mario de Jesus Perez
Jimenez, Universidad de Sevilla NCRG) to dissect PROTEA's pipeline.
Output: ~40-60 page LaTeX document, ~30-50 references heavy on Perez
Jimenez bibliography, integrable later as thesis chapter or extracted as
companion paper. Sequential prereqs.

### COMPLEXITY.1 — Bibliographic survey + LaTeX scaffold

```yaml
id: COMPLEXITY.1
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: []
acceptance: |-
  New directory ~/Thesis2/complexity-paper/ with:
   - Bibliography file (BibTeX) populated with 30+ entries:
     * Mario de Jesus Perez Jimenez body of work (10+ key papers,
       Google Scholar + US homepage)
     * Membrane Computing / P Systems foundational (Paun, Rozenberg,
       Salomaa)
     * Complexity classes for P systems (PMC, NPMC, NMC variants)
     * Classical complexity in bioinformatics (BLAST O(mn), protein
       folding PSPACE/QMA-hard, sequence alignment NP-hard variants)
     * PLM / embedding complexity (transformer attention O(n^2),
       FAISS KNN, LightGBM training/inference)
   - Outline document outlining 8-12 chapter structure with chapter
     summaries (200 words each)
   - LaTeX scaffold (article or book class) with package imports,
     bibliography hooks, custom command definitions for membrane
     notation (M, R, V, ->_max, etc.)
   - Makefile target that builds clean to complexity.pdf
   - The outline locks the narrative: classical complexity (chapter
     2-3) -> membrane computing modeling (4-5) -> empirical
     complexity (6) -> comparison (7) -> implications (8)
estimated_hours: 8
priority: P1
tags: [complexity, research, scaffold]
```

### COMPLEXITY.2 — Chapter 1 + 2: Introduction + classical complexity background

```yaml
id: COMPLEXITY.2
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.1]
acceptance: |-
  Chapter 1 (Introduction, ~5 pages): motivation for complexity
  analysis in computational biology, position PROTEA as case study,
  preview the two analysis lenses (Turing-classical + P-system
  natural-computing). Frame: PROTEA is a real-world bioinformatic
  pipeline; what does its complexity profile look like through both
  lenses?

  Chapter 2 (Classical complexity preliminaries, ~6 pages): formal
  definitions of P / NP / NP-hard / PSPACE / EXPTIME, complexity
  classes relevant to bioinformatics (genome assembly NP-hard,
  protein folding NP-complete in lattice models, RNA secondary
  structure prediction O(n^3) Nussinov, multiple sequence alignment
  NP-hard for SP-score). Include the celebrated complexity results
  in computational biology with citations.
estimated_hours: 6
priority: P1
tags: [complexity, writing, foundations]
```

### COMPLEXITY.3 — Chapter 3: Classical complexity of PROTEA pipeline

```yaml
id: COMPLEXITY.3
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.2]
acceptance: |-
  Chapter 3 (~10 pages): formal complexity decomposition of each
  PROTEA pipeline stage with derivations:
   - Sequence ingestion + tokenization: O(L) per protein, L = sequence
     length
   - PLM forward pass: O(L^2 * d) attention + O(L * d * d_h) feedforward
     per layer; total O(L^2 * d + L * d^2) per layer x layers
     (with d=hidden dim, d_h=intermediate, L=sequence length)
   - Embedding pooling (mean / per-residue): O(L * d)
   - FAISS flat KNN: O(n * d) per query, n = corpus size; O(n * d * Q)
     for Q queries
   - Anc2vec vote-to-ancestor: O(|GO_per_protein| * D_ontology) where
     D = max GO subgraph depth (~12 for BPO)
   - LightGBM reranker training: O(N * F * log(F) * T * D) where N
     samples, F features, T trees, D depth
   - LightGBM inference: O(F * T * D) per query
   - Cafaeval per-aspect Fmax: O(P * GO * thresholds)
  Each derivation: justify the dominant term, note when constants matter
  in practice (BERT-style attention rapidly dominates for L>512), tie to
  measured wall-clock numbers from FARM-EXP.13 cells.
  Total pipeline complexity claim + proof sketch.
estimated_hours: 10
priority: P0
tags: [complexity, formal, derivations]
```

### COMPLEXITY.4 — Chapter 4: Membrane computing primer (Perez Jimenez framework)

```yaml
id: COMPLEXITY.4
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.1]
acceptance: |-
  Chapter 4 (~8 pages): introduction to membrane computing / P systems
  drawing heavily from Perez Jimenez body of work.
   - History: Paun's 1998 original P system definition
   - Architecture: membrane structure, regions, objects, rules,
     environment, communication
   - Variants: transition P systems, P systems with active membranes,
     tissue P systems, spiking neural P systems
   - Computational power: equivalence with Turing machines (universal)
   - Complexity classes in membrane computing:
     * PMC_M (problems solvable in polynomial time with confluent
       P systems of family M)
     * NPMC_M (non-deterministic variant)
     * The Perez Jimenez Conjecture (P != NP in membrane computing)
     * NMC^d (d-deterministic systems)
   - Why membrane computing matters for bioinformatics: cell-inspired
     parallelism, natural mapping to compartmentalized biological
     processes
  This chapter is the strongest Perez Jimenez tribute: cite his survey
  papers, his Sevilla-school work, the NCRG output.
estimated_hours: 8
priority: P0
tags: [complexity, membrane, perez-jimenez, foundations]
```

### COMPLEXITY.5 — Chapter 5: PROTEA modeled as P system

```yaml
id: COMPLEXITY.5
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.3, COMPLEXITY.4]
acceptance: |-
  Chapter 5 (~12 pages, longest + most original): formal P system
  model of PROTEA.
   - Map each pipeline stage to a membrane region:
     * Region 1 (outermost): sequence ingestion + sanitization
     * Region 2: PLM embedding extraction (one inner membrane per
       PLM backend, parallel)
     * Region 3: KNN retrieval (membrane with FAISS-state objects)
     * Region 4: reranker scoring (membrane with LightGBM-tree objects)
     * Region 5 (innermost / output): evaluation + champion selection
   - Define the rule set R for each region: object rewriting,
     communication, dissolution
   - Anc2vec ancestor propagation = a tissue P system communication
     rule between Region 3 and a dedicated ontology membrane
   - Selective deploy (NK+LK -> v27-binary, PK -> KNN baseline) =
     a dispatcher rule that activates different inner membranes by
     input category
   - Multi-PLM ensemble = membrane parallelism a la Perez Jimenez
     active membranes
   - Prove (or sketch) that the PROTEA P system belongs to PMC for
     fixed input size, and discuss what changes if we admit dynamic
     membrane creation (closer to NMC^d)
   - Diagram(s) using TikZ membrane notation matching standard
     P system papers.
estimated_hours: 12
priority: P0
tags: [complexity, membrane, original-contribution]
```

### COMPLEXITY.6 — Chapter 6: Empirical complexity measurements

```yaml
id: COMPLEXITY.6
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.3]
acceptance: |-
  Chapter 6 (~8 pages): empirical complexity from PROTEA logs +
  FARM-EXP.13 outputs.
   - Wall-clock per stage on bench-v1-K5-v226-lineage cells (from
     the structured log events, e.g. export_research_dataset.split_start,
     aspect_loaded, etc.)
   - Memory profile per stage
   - Scalability charts: time vs n (corpus size), time vs L (seq length),
     time vs K (KNN neighbors)
   - Empirical constants for each formal Big-O from chapter 3
   - Discussion of where formal complexity matches measured + where
     constants dominate (e.g., attention O(L^2) but in practice
     I/O-bound for L < 512)
   - Tables generated by a script committed to the paper repo
     (reproducible).
estimated_hours: 8
priority: P1
tags: [complexity, empirical, charts]
```

### COMPLEXITY.7 — Chapter 7: Comparative complexity (PROTEA vs BLAST vs InterPro vs NetGO)

```yaml
id: COMPLEXITY.7
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.6]
acceptance: |-
  Chapter 7 (~6 pages): comparative complexity analysis.
   - BLAST (Altschul et al): heuristic O(mn) worst case, sub-linear
     amortized via word-hashing
   - InterPro: HMM scan complexity, profile-HMM dynamic programming
     O(LM) per profile
   - NetGO3 / DeepGoPlus: similar PLM-based pipelines, contrast
     architectural choices
   - Position PROTEA: trades PLM cost for KNN+LightGBM speed; how does
     end-to-end Fmax/sec compare?
   - Theoretical comparison + empirical numbers where available.
   - Argue PROTEA's "selective deploy" policy is essentially a complexity
     reduction technique: PK route avoids the expensive reranker entirely.
estimated_hours: 6
priority: P1
tags: [complexity, comparison, related-work]
```

### COMPLEXITY.8 — Chapter 8: Implications + discussion + conclusion

```yaml
id: COMPLEXITY.8
phase: COMPLEXITY
loop: thesis-writer
status: done
deps: [COMPLEXITY.5, COMPLEXITY.6, COMPLEXITY.7]
acceptance: |-
  Chapter 8 (~5 pages): pull threads together.
   - What does the dual-lens analysis tell us?
   - Membrane computing as a design principle: future PROTEA versions
     could exploit parallelism more explicitly using P system semantics
     (e.g., a P system implementation of the FAISS+LightGBM dispatch)
   - Limitations: P system framing is descriptive not prescriptive;
     PROTEA runs on classical hardware, the membrane model is a
     formal abstraction
   - Future work: extension to NeurIPS-style ML systems generally;
     possible mapping of attention layers to spiking neural P systems
     (a Perez Jimenez specialty)
   - Tie back to thesis defense story + TMLR submission angle
estimated_hours: 5
priority: P1
tags: [complexity, discussion, future-work]
```

### COMPLEXITY.9 — Final polish + bibliography + figures + PDF deposit

```yaml
id: COMPLEXITY.9
phase: COMPLEXITY
loop: thesis-writer
status: done
shipped_via: "complexity-paper tag v1.0 (abstract + membrane TikZ + scalability plots + complexity.pdf, 90pp)"
deps: [COMPLEXITY.2, COMPLEXITY.5, COMPLEXITY.6, COMPLEXITY.7, COMPLEXITY.8]
acceptance: |-
  Abstract (250 words, lead with the dual-lens contribution).
  Frontispiece + author + Sevilla affiliation + acknowledgement of
  Perez Jimenez (per CLAUDE.md: co-supervisors are
  Orellana-Martin + Rojas; Perez Jimenez goes in the bibliography +
  potentially in a "with thanks to" section, NOT as supervisor).
  All figures rendered (TikZ membrane diagrams, scalability charts,
  comparison table).
  Bibliography rendered (BibTeX run clean, no missing refs).
  pdflatex build zero warnings (per TD.3 standard).
  Em-dash-free per CLAUDE.md hard constraint.
  Final PDF saved as ~/Thesis2/complexity-paper/complexity.pdf
  + tagged as v1.0 in a fresh git repo (or as subdir of thesis repo).
estimated_hours: 5
priority: P1
tags: [complexity, polish, deposit]
```

### COMPLEXITY.10 — PMC boundary as a falsifiable design principle

```yaml
id: COMPLEXITY.10
phase: COMPLEXITY
loop: thesis-writer
status: pending
deps: [COMPLEXITY.9]
acceptance: |-
  Elevate the membrane lens from complementary tribute to a falsifiable
  design principle: PROTEA is competitive because it is engineered to stay
  inside PMC (tractable, confluent, no membrane division), declining the
  NP-hard formulations rivals implicitly require (exact MSA, optimal
  phylogenetic placement).
  New closing section in ch4 (after the PROTEA-DECIDE in PMC theorem)
  stating the design thesis + the explicit falsifiability criterion (what
  observation would refute it: an NP-hard-core method beating PROTEA at
  comparable wall-clock, or PROTEA needing membrane division to stay
  competitive).
  ch7 comparative section reframed around the PMC-vs-implicit-NP-hard axis:
  each compared method (BLAST, HMMER, NetGO, exact-MSA pipelines) classified
  by whether its core stays tractable; PROTEA placed as PMC-by-construction.
  Claim stays defensible (PMC membership is a necessary part of the cost
  story, consistent with ch6 empirics, NOT a sole cause). No invented refs.
  PDF builds clean, complexity.pdf regenerated, tagged v1.1.
estimated_hours: 2
priority: P2
tags: [complexity, membrane, design-principle, narrative]
```

**Goal**: make the membrane-computing chapter pull intellectual weight by
turning the PMC/NPMC boundary into a design criterion that explains PROTEA's
cost advantage and ties together ch3 (MSA NP-hardness), ch5 (Big-O), and ch7
(comparative). Executed 2026-06-07 in a complexity-paper worktree.

