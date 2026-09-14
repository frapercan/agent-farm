<!-- Vive aquí, y no en un artefacto ni en la memoria de una sesión, porque este
     es el único sitio que las dos máquinas clonan. Si lo editas, edítalo aquí. -->

> **Cómo leer este documento.** Es el diseño de la campaña, no un informe de
> resultados. Cada cifra lleva su procedencia y lo que no se pudo establecer
> aparece marcado como *not established* en vez de estimado. Fue auditado el
> 2026-09-14 por treinta agentes: catorce cifras resistieron un intento
> adversarial de refutarlas y están corregidas aquí; dos hallazgos estructurales
> sobrevivieron y están incorporados, uno de ellos cambia qué nodo cerró el eje C.
>
> Compañeros en este mismo directorio: `RUTA.md` (la ruta y sus defectos),
> `PLAN-EXPERIMENTAL.md` (el plan), `MARCO-DECLARADO.md` (el sello, con sus
> UUID), `AUDITORIA.md`. La ventana temporal **no** se declara en ninguno de los
> cuatro: la declara `protea/core/split_registry.py`, y sus tests son la barrera.

# The Clean Campaign: Design Document

**Frame under review:** GOA 220 → 227 · **Written:** 2026-09-13 · **Status:** for review, then execution

Every number below carries a command or a `file:line`. Where a claim could not be established it is
marked *not established* and left there. Where the document would change a decision that is already
written down somewhere, the change is flagged in bold. Nothing here reads the holdout, and no stage
below plans to.

---

## 1. The question

### 1.1 The campaign is narrower than the thesis

The thesis states its claim in one sentence at `thesis/chapters/01_introduction.tex:221-226`: that
PROTEA demonstrates a contracts-first platform delivering *a reproducible, leakage-free evaluation
methodology*, *quantifiable gains from feature-engineered re-ranking over PLM-embedding baselines*,
and *independently verifiable deployment as a public benchmark submission*.

Three deliverables, of three kinds. A methodology can be demonstrated by exhibiting it; an artefact
can be shipped. Only the second is a claim about the world that requires measurement, and it is the
one the record cannot support at all. Measured:

```
select count(*) filter (where reranker_model_id is not null),
       count(*) filter (where scoring_config_id is not null), count(*) from evaluation_result;
  -> 0 | 0 | 315
select count(*) from reranker_model;   -> 0
select count(*) from scoring_config;   -> 0
```

Every score in the record was produced by the unregistered third branch of the scoring priority
documented at `protea/core/operations/_run_cafa_artifacts.py:285-292`: *"Otherwise fall back to
`1 - cosine_distance / 2`."*

So the campaign is not a re-run of the thesis. It is the prerequisite all four of the thesis's
research questions assume and none of them establishes: **that a number in this project can be tied
to the decision that produced it.**

### 1.2 The top-level question

> **Which of the decisions that define a PLM-KNN annotation-transfer system are separated by
> evidence on one leak-free window, and which are merely chosen?**

*Separated* is already defined in code, not in prose. `strength_of` at
`protea/api/routers/_graph_edges.py:42-60` returns one of five words in a fixed order of tests, and
`measured` is reachable only when a floor was declared **and** the comparison cleared it. The
campaign's question is therefore answerable by construction — it asks which of the ten `SPECS` nodes
at `_graph_edges.py:73-84` can reach `measured`, and it commits in advance to reporting the rest as
`chosen`, `unpowered` or `blocked` rather than dressing them as findings.

Measured today, by running the fourteen registered graph reads and `build_graph` unmodified with the
candidate scan stubbed (total 0.409 s; the stub affects one prose sentence only):

| node | strength | levels inst. | levels avail. | results |
|---|---|---:|---:|---:|
| frame | `inherited` | 1 | 1 | 0 |
| substrate | `chosen` | 25 | 25 | 315 |
| bank | `unpowered` | 2 | 1 | 315 |
| retriever | `chosen` | 5 | 5 | 315 |
| generator | `blocked` | 0 | 0 | 0 |
| scoring | `blocked` | 0 | 0 | 0 |
| features | `blocked` | 0 | 0 | 0 |
| reranking | `blocked` | 0 | 0 | 0 |
| combination | `blocked` | 0 | 1 | 0 |
| routing | `blocked` | 0 | 1 | 0 |

**Zero of ten nodes read `measured`.** Six read `blocked`. The frame node reports `results=0` while
315 results exist. The bank node reports two levels instantiated against one available — more held
than exist. Those three facts are the campaign in one table, and §2 explains each.

### 1.3 The sub-questions, and where each stands

**Q1 — Frame.** Which window, pivot, accretion regime and *deciding statistic* every number is read
in. Decided, not discovered; see §1.5. This is the precondition for every other question.

**Q2 — Substrate.** Which representation the neighbourhood is computed in. Live, and confounded. The
`sequence_embedding` census (one grouped count, 248.2 ms) gives four populations: twelve configs at
528,294 embeddings, `rung2-residue` at 528,234, `ankh-base [48]` at 79,357, and eleven intermediate
layers at 60,797 each. 528,294 / 60,797 = **8.6895**. The arm that wins every depth comparison draws
on 8.69× more donors than the arms it is compared with. That is defect **D2** in pure form: a level
named by one field (`layer`) when two vary.

**Q3 — Bank and donor policy.** **Closed. Must not be re-opened or recomputed.**
`exclude_self_neighbour` 387/387, |d| 0.048; `expand_votes_to_ancestors` 108/108, |d| 0.038;
`aspect_separated_knn` no effect, |d| 0.0012; `donor_policy` permissive 54/54 and winning *more* at
low homology (50/50 below 30% identity, |d| 0.0780 against |d| 0.0456 above 90%). Zero verdicts
changed when the threshold grid was refined. The `experiment_run` row
`campana-limpia-eje-C-banco-donante-220-227` is `done`, finished 2026-09-11 14:18:50 UTC.

**Q4 — Bank recency.** Open, and separable from Q3. Release 160 gives 94.11% coverage against 220's
96.66%: eight years of accession drift costs 2.58 points. The ladder 160, 165, …, 205, 211, 215, 220
is 13 snapshots and 12 pairs (211, not 210 — the archive has no 206–210). Two of the thirteen are
loaded: `select id, source, source_version, source_published_at::date from annotation_set` returns
GOA 160, 219, 220, 227 and nothing else.

**Q5 — Retriever and the evaluation cut.** Measured, and the measurement is about the statistic
rather than the depth. `MARCO-DECLARADO.md:552-592` reports both readings of the same 3 × 7 × 2 grid:
under `fmax_w` the winner is K=2 and the series is monotone downward; under the paired bootstrap the
winner is K=200 and the series is monotone upward, with all five adjacent intervals excluding zero.
`MARCO-DECLARADO.md:604-606` states the consequence plainly — the register's note that "deeper is
worse in 70 of 72 series" *was `fmax_w`, not depth*. The cut grid exists in the database as a
complete factorial and no node can see one cell of it; that is **X2**.

**Q6 — Generator, scoring, features, reranking, combination, routing.** Six `blocked` nodes, each
with a named zero rather than a judgement: `interpro_annotation` 0, `interpro_go_mapping` 0,
`reranker_model` 0, `scoring_config` 0, `dataset` 0, `term_cooccurrence` 0 (one `select count(*)`
over the six). These six nodes are the whole of the thesis's RQ2, and RQ2 has no live evidence
whatever.

### 1.4 The thesis describes four different temporal walks, three of which read inside the seal

| walk | train | validate | score | stated at |
|---|---|---|---|---|
| **W1** | GOA 160→220, twelve pairs | — | **220→229** | `appendix_a.tex:125-130` |
| **W2** | "the same 12 temporal holdout splits" | — | **220→230** | `appendix_d.tex:243-245` |
| **W3** | v226-lineage dataset | — | **226 ($t_0$)→230 ($t_1$)** | `06_evaluation.tex:703` |
| **W4** | GOA 160 through 226 | 226→227 | **227→230** | `04_system_design.tex:993-998` |

The wording is explicit in each case. `appendix_a.tex:126-128`: *"re-ranker training uses GOA
snapshot pairs 160→220 (twelve pairs) as the training set; evaluation uses the GOA 220→229
hold-out."* `appendix_d.tex:245`: *"(evaluation pair GOA 220→230)."* `06_evaluation.tex:703`:
*"Evaluation window GOA 226 ($t_0$) → GOA 230 ($t_1$)."* `04_system_design.tex:993-998`: *"Training
uses GOA snapshots 160 through 226 as the train window; the internal validation fold is the GOA
226→227 delta …; the reserved test window is GOA 227→230."*

W1, W2 and W3 all terminate at 229 or 230 and therefore read annotations that accrued after 227 —
inside the seal. W4 keeps training and validation outside it, then schedules a score on 227→230, and
`04_system_design.tex:1023-1025` books that read explicitly: *"A clean recompute against the
v227-lineage GOA 227→230 window is required before a definitive performance figure can be
reported."* The thesis's only `\TODO`, at `06_evaluation.tex:889`, is the same recompute. Under this
campaign's constraint that is a plan to score on the holdout and must be struck, not deferred.

The four shapes also disagree about their own size: `abstract.tex:30` says twelve releases,
`05_implementation.tex:1233` says $P = 13$, `01_introduction.tex:437` says fifteen snapshots.

### 1.5 The walk to adopt: GOA 220 → 227, on evaluation set `b7cfed9a`

**Adopt 220 → 227.** It is the only walk the state can execute and the walk the state has already
executed:

- `annotation_set` holds four releases and stops at 227. There is no 226, no 229, no 230.
- Both scoring-side `evaluation_set` rows run 220 → 227 (`b7cfed9a…`, `b7452c0e…`, both created
  2026-09-02, `window_role='valid'`). The third, `70e53213…` (created 2026-09-12), is the 160→219
  ladder pair and carries zero results.
- All 315 `evaluation_result` rows carry `leakage_role='select'`; 85 carry
  `temporal_window='SELECT_220_227'` and 230 carry none. **No row in the record has ever been scored
  inside the seal.**
- The thesis's own methods paragraph already names it: `06_evaluation.tex:1301-1305`, *"Every choice
  that defines the system … was made on the earlier validation window (GOA 220 → 227)."*
- GOA 227 was published 2025-09-04 (`annotation_set.source_published_at`), which is where the sealed
  frame begins. The window terminates exactly at the seal with no overlap.

**Of the two variants, adopt `b7cfed9a`.** They are not two labels for one frame. They differ in
`new_native_snapshot_id`: `b7cfed9a` propagates the new side in `releases/2025-07-22`, `b7452c0e` in
`releases/2024-03-28`. The project's own rule — *the most recent published release equal to or
earlier than the one the GAF declares* (`PLAN-EXPERIMENTAL.md:196-206`) — maps GOA 227 to
`releases/2025-07-22`, which is `b7cfed9a`'s. The choice is not cosmetic; measured from the paired
operation's own `pairing` events:

| panel | `b7cfed9a` | `b7452c0e` | ratio |
|---|---:|---:|---:|
| NK:BPO | 1,509 | 1,474 | 1.02 |
| NK:CCO | 1,116 | 1,113 | 1.00 |
| NK:MFO | 1,129 | 1,120 | 1.01 |
| LK:BPO | 1,214 | 1,199 | 1.01 |
| LK:CCO | 821 | 821 | 1.00 |
| LK:MFO | 943 | 933 | 1.01 |
| PK:BPO | **13,876** | **5,674** | **2.45** |
| PK:CCO | 4,872 | 3,149 | 1.55 |
| PK:MFO | 4,947 | 3,091 | 1.60 |
| total | 30,427 | 18,574 | 1.64 |

`b7cfed9a`'s nine reproduce `MARCO-DECLARADO.md:128-133` exactly except PK:MFO (4,947 paired against
4,953 declared — the paired population is the intersection of the two arms,
`population_rule='intersect'` at `compare_paired_panels.py:664`, so it can be smaller than the
ground-truth count). The mechanism behind the 2.45× in PK:BPO is **not established**.

> **FLAG — THIS CHANGES TWO DECLARED DECISIONS.**
>
> **(a)** `agent-farm/plans/E2E-CANONICAL-RUN.md:8-9` reads *"TUNE window: 226 → 227. Every
> parameter, threshold and design decision is selected here. Nothing after 227 informs a choice,"*
> and `:16-17` adds *"This supersedes both the June roadmaps (SELECT 220 → 227) and the July working
> assumption (VALID 225 → 227)."* The header at `:1` marks it FIXED BY THE AUTHOR 2026-07-27, and
> `protea/core/split_registry.py:287` encodes it as `windows=(ReleaseWindow("v226","v227"),)` with
> the author's words quoted at `:270-273`. **Adopting 220 → 227 therefore adopts a window a dated
> author decision retired six weeks before this campaign began, and GOA 226 is not in the database.**
> The researcher must either re-affirm 220 → 227 in writing or fund the GOA 226 ingest (priced in
> §6, S0). This document does not decide it; it refuses to leave it silent.
>
> **(b)** All four `experiment_run` rows list `b7cfed9a` **and** `b7452c0e` together as one frame
> (`config->>'evaluation_set_ids'`). The seal treats them as different frames. Naming one changes
> what every declaration in the database means.

Finally, `split_registry.py:320-326` raises `SplitUndecidedError` with an instruction addressed to
this document: *"the board's own frame is recorded elsewhere as 227→230, which spans three of those
windows and is not one of them. Designate the point explicitly, in the campaign document, and write
it here."* §6 (S0, G0) discharges that.

---

## 2. The diagnosis

**The campaign writes its decisions in prose and its data in tables, and nothing connects them.**
Every defect this campaign has hit is that one defect. Measured:

**The plan documents have no reader.** `grep -rIl` over `PROTEA/` (excluding `.git`, `.venv`,
`__pycache__`) for `RUTA.md`, `MARCO-DECLARADO`, `PLAN-EXPERIMENTAL` returns **zero files each**,
while `RUTA.md:4` states *"Este documento es la fuente; la pantalla que lo dibuja lo lee de aquí."*
Nothing reads it.

**The declaration vocabulary has no reader.** Per-key file counts by the same grep:
`held_still` 0, `layer_grid_caveat` 0, `estadistico_que_decide` 0, `unidad_profundidad` 0,
`perillas` 0, `supersedes_floor` 0, `haz` 0. Of the whole vocabulary the four `experiment_run` rows
use, only `graph_node` and `floor` are read anywhere — by one query, `_Q_FLOORS` at
`_graph_reads.py:346-354`.

**That one query reads a retracted row.** It selects `config->>'graph_node'` and `config->>'floor'`
and never mentions `status`. The only row carrying both keys is
`campana-limpia-eje-A-sustrato-220-227`, `status='abandoned'`, whose own `findings` column says:
*"Abandonado el 2026-09-04 sin despachar … bajo el diseno factorial … este suelo y estos cortes
dejan de ser un punto de partida."* The retraction is in the database and unread. That is **D6**.

**And the floor it reads cannot act in either direction.** Measured by running `_Q_FLOORS` (1 row,
17.1 ms) and `_Q_PANELS` (2,835 rows, 54.5 ms) and applying `level_fields` / `_level_name` /
`separated_from_floor` from `_graph_panels.py`: five fields are in force
(`embedding_name`, `depth`, `donor_policy`, `self_exclusion`, `code_revision`); they name **61
distinct levels**; and **none of the 61 is the string `esm2_8m`**. `separated_from_floor(panels,
'esm2_8m')` raises `CrossedFrames: … carries no frame seal`. Spelled correctly
(`esm2_8m@d100:mean / retrieval depth 200 / permissive / self-excluded / 8699bfd`) it raises the
*other* `CrossedFrames`: *"appears under 2 different frame seals."* `_floor_for`
(`_graph_nodes.py:53-55`) discards the refusal, so `separated` is `None`, so `strength_of` returns
`chosen` (`_graph_edges.py:58-59`). **No floor in this database has ever produced `True` or
`False`.** The closing rule has never executed.

**No result is tied to a decision by construction.** The schema holds 58 foreign keys
(`select count(*) from pg_constraint where contype='f'`). `experiment_run` is the source of none and
the target of none, and no table carries a column matching `%experiment%`. The only link from a
declaration to the numbers it governs is a string match on `config->>'graph_node'` against a Python
constant — and three of the four declared values (`retrieval_tensor`, `cut_depth`,
`bank_and_donor`) are not `SPECS` keys.

**A declaration and its own data disagree, unnoticed.** `experiment_run` `bbb96a35` (axis B, the
cut) has `status='planned'`, while `MARCO-DECLARADO.md:545-613` reports that axis measured in full
and names `bbb96a35` as the run that did it. A full CRUD path exists to transition it
(`protea/api/routers/experiment_runs.py:13`, `PATCH`). Nothing made anyone use it. That is **D4**.

**The only closed axis's evidence is one `DELETE` away.** `select status, count(*) from job where
operation='compare_paired_panels'` gives **4,279 SUCCEEDED** and 194 FAILED. Their output exists only
as `emit(...)` calls into `job_event` (437,405 rows; `compare_paired_panels.py:501` and
`_paired_panels_events.py`), whose foreign key is `job_event_job_id_fkey … ON DELETE CASCADE`
(`confdeltype='c'`). No table receives a verdict.

**The one written prohibition was violated.** `experiment_run` `70b1dec8` declares
`layer_grid_caveat`: *"Banco reducido: los scores absolutos NO son comparables con los trece brazos
de corpus completo… Una ganadora aqui es candidata al corpus completo, no ganadora del eje A."*
Zero code reads the key, nothing refuses the comparison, and a depth result was published from
exactly the comparison it forbids.

**The record's best instrument is invisible to its own surface.** The paired operation's verdict
vocabulary is six words — `TALLY_KEYS` at `protea/core/operations/_paired_panels_panel.py:753-760`:
`resolved`, `null_with_power`, `null_unread`, `underpowered`, `refused`, `not_computed`. Measured
over every whole-panel reading in `job_event`: 6,816 `ok`/resolved, 2,299 `null_unread`, **23
`null_with_power`**. `PLAN-EXPERIMENTAL.md:150-152` says a declared null *"hoy no se puede escribir:
falta el sexto valor de fuerza."* It has been written 23 times. The graph's five-word scale cannot
receive one.

---

## 3. The structure

### 3.1 A node

A node is one decision over a field, or over a group of fields that cannot be decided apart
(`graph.py:13-14`). The grouping is substantive: the bank node holds corpus and donor policy together
because *"a corpus and the filter applied to it define one bank between them"*
(`_graph_nodes.py:218-223`), and a group is held no more firmly than its loosest member.

Ten nodes exist and exactly ten builders exist, and this is pinned rather than conventional.
`tests/test_graph_endpoint.py:716-730` walks `SPECS`, resolves `_{key}_node` by name, asserts there
are ten, and asserts every one takes a `floors` argument; `:731-740` parses the AST of `build_graph`
and asserts every one is handed it. That pair exists because until 2026-09-02 nine of ten builders
could not see a declared floor (`tests/test_graph_endpoint.py:695-714`). **It is the template for
every instrumentation change in §5.**

### 3.2 A level

**A level is a value together with every field that varies across the rows it is compared with.**
The rule is at `RUTA.md:6-8`; the implementation is `level_fields` / `_level_name` at
`_graph_panels.py:255-262` over the eight candidates at `:57-77`. Two candidates are scars:
`code_revision`, because a stored donor policy is byte-identical either side of the 2026-08-29 change
that moved evidence codes from gating pool admission to gating donation (`_arm_identity.py:10-24`);
and a prefixed `depth`, because a k-position cut of 10 and a retrieval depth of 10 both rendered as
`10` (`_arm_identity.py:26-37`).

There is a structural limit on this design that bears on every declaration. `level_fields` reads off
what *varies in the rows it is handed*, so its arity is decided at read time. Measured: over the
whole record it is five; restrict the rows to one seal and `donor_policy` becomes constant and it is
four. **No string stored in `experiment_run.config` can name a level**, because the naming function's
arity is a property of the query, not of the level. A floor must therefore be declared as a *field
tuple plus values*, not as a rendered name.

### 3.3 The five edge strengths, and why the order is the argument

| order | test (`_graph_edges.py:52-60`) | outcome | why here |
|---:|---|---|---|
| 1 | `not produced or instantiated == 0` | `blocked` | an artifact with no producer cannot have levels |
| 2 | `instantiated == 1` | `chosen` if forced, else `inherited` | with no contrast, a number is a reading |
| 3 | `scored < 2` | `unpowered` | whether a comparison *could* resolve is a fact about its shape |
| 4 | `floor is None or separated is None` | `chosen` | a spread with no declared floor is a spread |
| 5 | `separated` | `measured` else `chosen` | the only path to the strongest word |

Two properties matter downstream. **Power is tested before evidence:** no gap, however large, can
talk a node into a measurement. And **`chosen` is a sink:** four distinct situations collapse into
it — a frame-fixed single level, a powered comparison with no floor, a powered comparison whose floor
*refused*, and a powered comparison that did not separate. A reader of the payload cannot tell them
apart, because `_node` (`_graph_edges.py:119-132`) emits no `floor` key and no `separated` key. I
verified the emitted key set: `blocked_reason, constant_fields, held, key, levels_available,
levels_instantiated, question, results, stage, strength, title, varying_fields`.

### 3.4 How a node closes

- **`blocked` → anything:** produce the artifact. Each blocked node publishes its own precondition
  as a count read from `_Q_ARTIFACTS` (`_graph_reads.py:331-339`), never asserted.
- **`inherited` → `unpowered`:** instantiate a second level. Counted from rows, never from a
  declaration (`split_fields`, `_graph_edges.py:168-185`).
- **`unpowered` → `chosen`:** score the second level.
- **`chosen` → `measured`:** declare a floor that names a real level, and clear it. This is the only
  transition requiring something outside the result tables.

The rule that decides the last transition is `separated_from_floor` (`_graph_panels.py:391-436`):
restrict to the floor's seal; per panel, skip if either side is empty; refuse if the two sides'
depths are different quantities; otherwise compare `max(f_micro_w)` of rivals against
`max(f_micro_w)` of the floor; return `False` on the first testifying panel that fails. It is
unanimity over testifying panels, **on point estimates of a metric quantised to 1e-4, with no
interval.** That is **D5** sitting inside the closing rule, and it is a different rule from the one
`PLAN-EXPERIMENTAL.md:148` states (majority of nine) and from the one the two surviving declarations
state (`estadistico_que_decide`: *"bootstrap pareado a nivel de proteina, IC 95 por ciento excluyendo
cero"*). Three incompatible closing rules are live at once; nothing reconciles them.

### 3.5 A declaration is a row, plus a guard that can refuse, plus a test that demonstrates both

**A declaration is enforceable if and only if it has three parts, and it is worth nothing with two.**

1. **A row.** In a typed column, addressable by the surface that must obey it. Prose in a markdown
   file is not a declaration; nor is a free-text key in a `jsonb` blob no query names.
2. **A guard that can refuse.** Some path reads the row and *raises*, before the number is produced
   or the comparison answered. A guard that logs, or returns a default, is not a guard.
3. **Two tests: one that it REFUSES when violated, one that it ACTS when honoured.** Both halves are
   required. A guard tested only on refusal may be a function that always raises; a guard tested only
   on the happy path may be one that never fires. This is **D3**.

Two things in this tree meet the bar and are the model.

*The frame seal.* Row: `evaluation_result.frame_digest`, with the material stored beside the address
in `evaluation_frame` (`seal_evaluation_frames.py:101-118`). Guard: `_within_the_floors_frame`
(`_graph_panels.py:361-388`) raises `CrossedFrames`; `_refuse_crossed_depths`
(`_graph_panels.py:326-358`) raises `CrossedDepthAxes`. Tests: refusals at
`tests/test_graph_endpoint.py:787`, `:800`, `:614`, `:633`; actions at `:780`, `:603`, `:338`.

*The depth-unit guard.* Row: `max_sequence_rank` / `max_k_position`. Guard:
`protea/core/_depth_unit_guard.py`, both entry points raise. Tests: refusals at
`tests/test_a_depth_says_what_it_counts.py:40`, `:73`, `:83`; actions at `:57`, `:80`.

Against that bar, one guard in this tree has part 2 and part 3 but **cannot demonstrate the ACT half
on the campaign's own frame**. `refuse_uncertifiable_encoding` (`_evaluation_leakage.py:67-87`) is
live and called at `run_cafa_evaluation.py:425`. Of 25 `embedding_config` rows, three fall in
`FITTED_BACKENDS = {"residue-sparse","learned-code"}` (`_evaluation_leakage.py:42`) and all three
declare `trained_on` = release 220; the other 22 declare none and return at the first branch.
`leakage_guard.py:74` refuses iff `frame.start < training_release <= frame.end`; on (220, 227) with a
cut of 220 that is false. **The guard is live, is called, and provably cannot raise for any row in
this database on the adopted frame.** Its only demonstrated refusal is
`tests/test_leakage_guard.py:16`, on `Frame(start=220, end=230)` — the holdout frame. §6 G6 is where
that demonstration has to happen.

And `layer_grid_caveat` is the counter-example to quote whenever a fifth plan document is proposed:
part 1 and nothing else.

### 3.6 The nine panels are never aggregated; a verdict is a nine-vector

A panel is a knowledge category (NK, LK, PK) crossed with an aspect (BPO, MFO, CCO) — `PANEL_KEYS`
at `_graph_panels.py:32-34`, built from the project's own enums. The constraint is enforced by
omission: the module offers no way to add two panels; `build_panels` emits all nine whether or not
each carries a result, so a partial run cannot read as a complete one (`:265-302`);
`separated_from_floor` iterates `PANEL_KEYS` rather than pooling. The paired operation refuses an
aggregate explicitly, naming its own paragraph: `compare_paired_panels.py:49-53`, *"It does not
report a mean over the nine panels or an interval for one… Asking for one is a refusal naming this
paragraph."*

**A verdict is reported as a nine-vector and never as a number.** Each cell carries the panel key;
its population, counted from the window's own ground truth and never inferred; the levels scored,
ordered; and the strength of the verdict in that cell. The population is counted because the
alternative already failed: an earlier version inverted stored coverage against the protein count at
the optimum and intersected the rounding intervals, so every result inverted the same quantity the
same way, the intervals agreed while all being wrong together, the disagreement guard could never
fire, and two of nine panels were out by eleven and eight units with no signal
(`_graph_panels.py:88-96`). That is **D1**, named and fixed in exactly one place.

Per-panel resolving power spans nearly an order of magnitude and must be published beside every
verdict. Measured two independent ways, which agree on the ordering:

| panel | n (`b7cfed9a`) | CI half-width | MDE range | σ implied | own floor | votes |
|---|---:|---:|---:|---:|---:|:--:|
| `PK:BPO` | 13,876 | 0.00130 | 0.0001 – 0.0041 | 0.0782 | 120 | yes |
| `PK:MFO` | 4,947 | 0.00421 | 0.0005 – 0.0121 | 0.1511 | 448 | yes |
| `PK:CCO` | 4,872 | 0.00466 | 0.0004 – 0.0127 | 0.1659 | 541 | yes |
| `NK:BPO` | 1,509 | 0.00951 | 0.0010 – 0.0222 | 0.1884 | 697 | yes |
| `LK:BPO` | 1,214 | 0.01102 | 0.0011 – 0.0292 | 0.1958 | 753 | yes |
| `NK:MFO` | 1,129 | 0.01544 | 0.0018 – 0.0339 | 0.2647 | 1,376 | **no** |
| `NK:CCO` | 1,116 | 0.01520 | 0.0014 – 0.0413 | 0.2591 | 1,317 | **no** |
| `LK:MFO` | 943 | 0.01375 | 0.0016 – 0.0348 | 0.2154 | 911 | yes |
| `LK:CCO` | 821 | 0.01735 | 0.0016 – 0.0431 | 0.2536 | 1,263 | **no** |

Every column is read from the record: `n` and the bootstrap interval half-width from the
`pairing` and `panel` events, the MDE range from the `minimum_detectable_effect` field over
resolving readings, and σ implied by inverting the half-width. **The MDE is given as a range
because it is not a panel constant** — there is one per comparison, and within `LK:CCO` it spans
0.0016 to 0.0431.

**Three of the nine panels do not reach their own floor.** Applying the same rule the routing
floor uses, `ceil((2.8016·σ/0.02)²)`, but with each panel's own σ instead of a single 0.13,
`NK:MFO`, `NK:CCO` and `LK:CCO` cannot vote: their population is below what their own dispersion
demands. Two of the three are `NK`, the category the project wants to headline. A global floor of
332 let all nine vote only because it assumed a dispersion eight of the nine do not have.

**Provenance of two of these columns is pending, and they must not be quoted as
measured until it is fixed.** The paired σ is stored nowhere in the database: no
event field is `sigma` or `sd`, and reconstructing it from the interval half-width
yields nine different figures. The MDE is not a panel constant either — it is read
off each bootstrap distribution, so there is one per comparison; over the 9,138
unstratified panel readings `LK:CCO` ranges 0.00157–0.04519 and `PK:BPO`
0.00010–0.00637, and no single job carries the nine values printed here. What is
stable, and what the argument below actually needs, is the **ordering**.

The σ/√n column is arithmetic on the nine measured paired σ and is shown only as a cross-check; the
MDE column is read off the bootstrap distribution itself
(`compare_paired_panels.py:31-36`, `job_event` field `minimum_detectable_effect`) and is the number
that decides. The retracted table at `MARCO-DECLARADO.md:135-145` must not be revived.

**The consequence for the closing rule, measured.** The five smallest of the nine cohorts —
LK:CCO 821, LK:MFO 943, NK:CCO 1,116, NK:MFO 1,129, LK:BPO 1,214 — are a *majority of the nine*
holding 5,223 of 30,427 units, **17.2%** of the evidence (27.9% on `b7452c0e`). The ratio of largest
to smallest per-panel standard error is **13.43** (8.63 on `b7452c0e`). A majority-of-nine rule can
therefore seal an axis, become the next node's floor, and propagate downstream on the vote of the
least-powered sixth of the record.

**The recommended closing rule.** A cell votes only if its 95% paired-bootstrap CI against the
incumbent excludes zero; a cell whose interval covers zero reports `null_with_power` or
`null_unread` — the words the instrument already emits — and casts no vote in either direction; an
axis seals only if one level wins every voting cell; otherwise the axis carries forward the survivor
set, the levels never beaten in a voting cell. This fixes both failure modes at once (an unpowered
cell can neither carry a majority nor veto one), it is the statistic the two surviving declarations
already name and the 4,279 jobs already ran, and it is the only option under which *"the axis did not
choose"* is a writable outcome — which is what axis A actually produced
(`MARCO-DECLARADO.md:527-533`, *"El eje A queda ABIERTO … Se lleva un haz de tres"*).

The cost, stated without softening: this makes the per-protein paired rows load-bearing for every
seal, and they currently live only in `job_event` under a cascade delete. Promoting them stops being
housekeeping and becomes a precondition for closing any node at all (§5 I4, §6 S1).

---

## 4. The hypotheses

Each decision is one numbered hypothesis with its refutation and its instrument, marked
**ANSWERED**, **CONFOUNDED**, **BLOCKED** (with the named zero), or **OPEN**.

### 4.0 Hypotheses dropped, and why

| dropped | broken by, in one sentence |
|---|---|
| *"One walk suffices; no node needs a release above 227."* | Its own instrument could only return "absent", because `split_registry.py:115-129` holds nine releases and `:246` seven validation windows above 227 while the database holds none, so the hypothesis read the residue of a wipe as a property of the plan (D4 inverted). Repaired → **H1**. |
| *"The obstruction to recovering the thesis headlines is the aggregation ban."* | Both disjuncts of its own refutation already hold: `06_evaluation.tex:673-676` states a headline range (0.4386–0.4669) on the single panel NK-BPO, and `06_evaluation.tex:565-578` prints the nine-cell decomposition whose mean is 0.5427. Repaired → **H20**. |
| *"Only RQ1 has live evidence; RQ2 has none by construction."* | Four of the five nodes it calls blocked are blocked by a literal `instantiated=0` (`_graph_nodes.py:376, :520, :585, :609`) that no database state can change, and RQ1's own alignment comparator is unregistered, so the asserted asymmetry does not exist. Repaired → **H10–H13**, **H18**. |
| *"Repairing `_Q_FLOORS` changes a published number."* | Refuted by my own measurement: the substrate edge already reads `chosen` because the refusal is discarded at `_graph_nodes.py:53-55`, so a status predicate changes no published word. Repaired → **H15**, and I1 in §5 is reclassified as prophylaxis. |
| *"The floor is unenforceable because the declaration names one field and the surface five."* | `level_fields` has no fixed arity (five fields over the record, four inside one seal) and the declaring run names two `evaluation_set_id`s, so no stored string can name a level and correcting the spelling changes nothing. Repaired → **H16**. |
| *"Unanimity over testifying panels cannot seal at the measured spread."* | Untestable as written: `separated_from_floor` has never returned `True` or `False` on live rows, so the rule has never executed and its failure mode cannot be observed. Repaired → **H19**. |

### 4.1 Frame

**H1 — OPEN (decision, not discovery).** Selection is confined to one window; validation is not. Every
choice this campaign makes is selected on one designated window at or below release 227, and no node
reads a release above 227 *to inform a choice*; releases above 227 remain required and are not this
campaign's to abolish.
*Refuted by:* any selection-side result whose `frame_digest` resolves to an `evaluation_set` whose
`new_annotation_set_id` is above 227; or `comparable_window()` still raising after this document is
executed.
*Instrument:* a digest → `evaluation_set` resolver over `evaluation_frame.material`, which does not
exist today and is the one small thing worth building (§5 I3).

**H2 — ANSWERED.** The frame seal both over-partitions on a field carrying no meaning and
under-partitions on a field that decides verdicts, so digest equality is neither necessary nor
sufficient for comparability.
*Measured:* `select digest, material from evaluation_frame` returns four digests.
`f-1c80a45879c19ce07717d3d3` and `f-be61878a56c7b511852f89ad` are identical in five of six sealed
fields and differ only in `temporal_window` — `null` versus the free-text string `SELECT_220_227` in
a `varchar(32)` under no constraint, null on 230 rows and set on 85. In the other direction, crossing
digests against `job.payload->>'th_step'` shows **all four digests contain both grids**: 0.0005 on
154 rows, 0.002 on 2, absent on 159 (the `th_step: float = 0.01` default at
`_run_cafa_eval_driver.py:81`). The grid that inverted 22% of substrate verdicts shares a seal with
the grid that replaced it.
*Refuted by:* `temporal_window` constrained to a vocabulary derived from the window, or any digest
containing exactly one grid.

**H3 — ANSWERED.** The frame the surface reports is a function of row-creation order, not of any
declaration.
*Measured:* `_Q_EVALUATION_SETS` orders `created_at DESC` (`_graph_reads.py:51`) and `build_graph`
takes `[0]` (`graph.py:239`). The head is `70e53213…`, window **160 → 219**, pivot
`releases/2024-01-17`, carrying zero results, created 2026-09-12. All four declarations name the
220 → 227 sets and pivot `releases/2024-03-28`. Consequences measured in the §1.2 table: frame reads
`inherited` with `results=0` against 315 stored; bank reads `instantiated=2, available=1`. **One
insert re-framed the whole campaign.**
*Refuted by:* the head being selected by a designated identifier, by `window_role`, or by the set
that carries results.

**H4 — OPEN.** The deciding statistic is a frame field: two numbers are not comparable if they differ
in it, exactly as if they differed in pivot or window.
*Measured:* `MARCO-DECLARADO.md:619-642` reports that on both closed axes the answer depended on the
statistic — axis A: `fmax_w` ranks `ankh_large` first, the paired bootstrap ranks `protst` first and
inverts it in all three categories with zero outside the interval; axis B: `fmax_w` wins at K=2, the
paired bootstrap at K=200, two complete monotonicities toward opposite edges. `_FRAME_FIELDS`
(`seal_evaluation_frames.py:61-68`) has six fields and the statistic is not one of them.
*Refuted by:* a pair of arms whose ranking is identical under both statistics across all nine panels
in a region where the differences are small.
*Instrument:* the `estimator` field already emitted at `compare_paired_panels.start`, set against
`fmax_w` read from `evaluation_result.results`.

### 4.2 Substrate

**H5 — CONFOUNDED, and the confound is fatal as instrumented.** A substrate comparison on the present
record measures representation and donor-bank size together.
*Measured:* 528,294 / 60,797 = 8.6895 across the two populations, from one grouped count. Seal
`f-e095b41c` holds `esm2_8m@d100:mean` (528,294 donors) alongside thirteen arms on smaller banks.
`prediction_set.meta` carries no bank field — its full key set over all 86 rows is
`aspect_separated_knn, batch_size, code_revision, dependency_revisions, donor_policy,
exclude_self_neighbour, expand_votes_to_ancestors, features, job_id, metric, search_backend` — and
`_SUBSTRATE_FIELDS` (`_graph_nodes.py:120-132`) names eleven config fields and not the donor
population. `experiment_run` `70b1dec8.config.layer_grid_caveat` forbids the comparison in prose;
nothing refuses it.
*Refuted by:* a substrate verdict whose arms carry equal donor banks.
*Consequence:* no substrate verdict may be published until §5 I9 is in place, and the depth result
already published from the reduced grid must be withdrawn rather than reused.

**H6 — ANSWERED (as OPEN, which is a result).** Axis A did not seal. It discarded four substrates and
carries a survivor set of three.
*Measured:* `MARCO-DECLARADO.md:515-533` — the leader separates from the declared floor above the MDE
in 9 of 9 cells, `+0.0749 [+0.0718, +0.0781]`; the esm2 family separates from the head group in 36 of
36 gaps in both variants; and under the plan's own §5 rule *"No ocurre. El eje A queda ABIERTO."* The
`haz` is `["protst@d100:mean","prot_t5@d100:mean","ankh_large@d100:mean"]`, recorded identically on
both surviving declarations. `experiment_run` `bbb96a35.config.supersedes_floor` reads *"ninguno: el
eje A quedo ABIERTO."*
*Must not be re-opened.* Whether that set or a single level carries forward is **X3**.

### 4.3 Bank and donor

**H7 — ANSWERED. Closed. Do not recompute.** Donor policy and neighbourhood filters are decided.
*Measured:* the four knobs at 387/387, 108/108, 54/54 and no-effect (|d| 0.0012), with permissive
winning more below 30% identity (50/50, |d| 0.0780 against 0.0456 above 90%), and zero verdicts
changed when the grid was refined. `experiment_run` `651979be` is `status='done'`.
*The only thing owed:* the evidence must leave `job_event` before any `job` row is deleted (§6 S1).

**H8 — OPEN, with the prerequisite priced.** Bank recency costs measurable coverage, and the cost is
separable from bank policy.
*Predicts:* release 160 gives 94.11% coverage against 220's 96.66%; the 12-pair ladder at or below
220 can be scored without any walk touching 227 as anything but terminal ground truth.
*Refuted by:* the ladder failing to express itself without a snapshot above 220; or the 160→219 pair
behaving structurally unlike the pairs the campaign scores.
*Known obstacles, measured:* `source_published_at` is **NULL for both 160 and 219**, while
`_graph_reads.py:38-43` states that a release number *"names a file and dates nothing"* and the
surface needs the date to judge the window. The one sub-220 `evaluation_set` that exists
(`70e53213`, created 2026-09-12) carries zero `evaluation_result` rows and has `window_role` NULL.
`protein_go_annotation` holds 22,636,176 rows in 7,375 MB over four releases: ~5.66 M rows and
~1,844 MB per release, so the eleven missing ladder snapshots are roughly **20.3 GB** plus indexes on
a database already at 477 GB (`pg_database_size`). `split_registry.py:255-262` cannot name a sub-220
window at all until those releases are added to `RELEASES`.

### 4.4 Retriever and the evaluation cut

**H9 — ANSWERED, and the answer is about the statistic.** Depth is monotone with the winner at an
edge under both statistics, and the two statistics choose opposite edges; there is no interior
optimum and there is no statistic-free answer.
*Measured:* `MARCO-DECLARADO.md:552-592` — `fmax_w` 0.3818 → 0.2909 from K=2 to K=200 (protst),
monotone; the paired bootstrap gives five adjacent contrasts all favouring the deeper arm with every
interval excluding zero, effect sizes decaying 0.0123 → 0.0033 (saturation, no reversion). The
mechanism is stated at `:594-602`: `fmax_w` maximises an aggregate curve and rewards predicting
little and confidently; the paired statistic gives each protein its own best F1 and rewards covering
each protein. `:608-613` records that the inherited K=30 default is beaten by K=2 under one and by
K=200 under the other. K=1 is a different regime, not another level of the axis.
*Must not be re-opened.* What remains is H4 (which statistic is declared) and X2 (which node owns
the cut).

**H10 — ANSWERED.** The evaluation cut is a real axis with a complete factorial behind it and is
structurally invisible to the decision graph.
*Measured:* `select max_k_position, count(*) from evaluation_result group by 1` gives 12 results at
each of K ∈ {1,2,3,5,10,20,30} — 84 cut-bearing rows — and 231 with no cut. Joined to `job.payload`,
exactly 42 of the 84 are at `th_step ≤ 0.002`, forming 3 substrates (`ankh-large`, `ProtST`,
`prot_t5` — precisely the axis-A `haz`) × 7 cuts × 2 evaluation sets. The cut lives on
`evaluation_result.max_k_position`, which `_Q_RESULTS` (`_graph_reads.py:242-261`) does not select
and no node builder reads; the retriever instead reports 5 levels from `limit_per_entry`, which is
**200 on all 86 prediction sets** (`select count(*), count(distinct limit_per_entry) from
prediction_set` → `86 | 1`).
*Refuted by:* any node builder reading `max_k_position` or `max_sequence_rank`, or any node's
`levels_instantiated` changing when the 84 cut-bearing rows are withheld.

### 4.5 The six blocked nodes, each with its named zero

**H11 — BLOCKED (generator).** `interpro_annotation` 0, `interpro_go_mapping` 0. The node's own
declaration is nonetheless the strongest in the system and is satisfied: `go_prediction
.ref_protein_accession` is `NOT NULL` (read from the catalog by `_Q_DONOR_COLUMN`,
`_graph_reads.py:321-329`), so the schema forbids a donorless candidate rather than merely recording
that nobody wrote one. **Not blocked by construction:** `LoadInterProGoMappingOperation`,
`RunInterProScanBatchOperation` and `PredictGOTermsFromInterProOperation` are registered among the 39
in `operation_catalog.py`, and zero jobs of any of them have ever been created (the 12 distinct
`job.operation` values are `compare_paired_panels, run_cafa_evaluation, stratify_evaluation,
predict_go_terms, compute_embeddings, seal_evaluation_frames, generate_evaluation_set,
load_goa_annotations, load_ontology_snapshot, export_evaluation_targets, audit_evaluation_frames,
compute_information_accretion`). That is *never dispatched*, which is a sequencing fact about this
campaign, not a property of the platform.

**H12 — BLOCKED (scoring).** `scoring_config` 0, so `_Q_SCORING` returns no rows and the node reports
*"0 weightings are registered and none of them has a surviving result"* — while 315 results exist,
all scored by the unregistered fallback. Its own docstring (`_graph_nodes.py:462`) claims *"Several
weightings scored the same candidates in the same frame,"* describing a contrast its only source
table cannot supply.

**H13 — BLOCKED (features).** `reranker_model` 0. The node passes `([], [])` as its field lists
(`_graph_nodes.py:520`). The machinery for a correct ablation exists and is unwired:
`protea-contracts/src/protea_contracts/feature_schema.py` at `SCHEMA_VERSION = "v6"` (`:23`) holds 21
families over 78 features and 21 distinct column sets, of which `knn = knn_distance + knn_vote`
exactly as a disjoint union — measured — leaving 20 independent sets;
`compute_feature_schema_sha(families, drop=None)` at `:303` is the correct entry point. **An ablation
must drop columns, never families.**

**H14 — BLOCKED (reranking, combination, routing).** `reranker_model` 0 for reranking; one flow for
the other two (`_flow_count` counts distinct `annotation_set.source` over prediction sets, which is
`['goa']`, one value across all 86).

> **Read the four `blocked` words at `_graph_nodes.py:376, :520, :585, :609` as structural, not
> evidential.** They are the literal `instantiated=0`, so generator, features, combination and
> routing cannot leave `blocked` under any database state. Their reason strings print live counts
> beside a word that would print identically at 10⁶ rows. That is **D3** — a guard that cannot
> demonstrate it can ACT — and §5 I10 addresses it.

### 4.6 Routing and channelling

**H15 — OPEN, and the highest-value guard to build before it is needed.** Channelling routes whole
configurations into routing regions and will win with zero real affinity unless the policy is
cross-fitted, because the channelled arm chooses once per region and the baseline chooses once.
*Measured, and worse than stated:* the region count is frame-dependent.
`population_floor(_SIGMA_ROUTING)` = `ceil((2.8016 × 0.13 / 0.02)²)` = **332**
(`_graph_panels.py:201-216`). Counting the length-refined cells that clear the floor: **17 under the global floor of 332**,
and only **11 under each panel's own floor**. And the eleven live in five panels — four in
`PK:BPO`, three in `PK:MFO`, two in `PK:CCO`, one in `LK:BPO`, one in `NK:BPO`. **Four panels
contribute no region at all**: `NK:MFO`, `NK:CCO`, `LK:MFO`, `LK:CCO`. Put plainly, routing by
length on a defensible floor can only route inside `PK` and `BPO`; it cannot route `MFO` or
`CCO` outside `PK`. The canonical "fifteen routing regions" is a count on one variant — and one of the fifteen, `LK:BPO@length=512-1024` at
n = 332, clears its own floor by exactly zero margin.
*Refuted by:* a channelled arm whose out-of-fold verdict matches its in-fold verdict across the
regions; or a region count invariant to the frame variant.
*Instrument:* the strata already exist as MinIO parquet and ride in the panel key
(`stratum_label` at `compare_paired_panels.py:629`), with membership taken from the baseline arm
(`stratum_membership_from: "baseline"` at `:663`). Four length bands and four homology bands are
measured in `job_event`. The per-protein grid artefact carries `th_step` in its footer
(`_run_cafa_grid_artifact.py:264`), so cross-fitting is instrumentable today.
*Caveat, measured:* the homology strata have been run 3 times per panel and only under the two
`SELECT_220_227`-labelled digests. That is thin.

### 4.7 Attribution — the campaign's own subject

**H16 — ANSWERED.** No result is tied to a decision by construction, and no string stored in a
declaration can name a level.
*Measured:* 58 foreign keys, none touching `experiment_run`; no `%experiment%` column anywhere; three
of four `graph_node` values are not `SPECS` keys; `level_fields` returns five fields over the whole
record and four within one seal; `separated_from_floor` refuses both the declared floor string and
its correctly spelled form; `_node` emits neither `floor` nor `separated`.
*Refuted by:* any result-bearing table carrying a foreign key to `experiment_run`.

**H17 — ANSWERED.** The record's own verdict vocabulary is six words and the surface can receive five,
so a declared null is indistinguishable from an unasked question.
*Measured:* `TALLY_KEYS` at `_paired_panels_panel.py:753-760`; `null_with_power` defined at `:553`
and returned at `:583`; over every whole-panel reading in `job_event`, 6,816 resolved, 2,299
`null_unread`, **23 `null_with_power`**. `PLAN-EXPERIMENTAL.md:150-152` says the sixth word cannot be
written.
*Refuted by:* a graph strength that distinguishes a powered null from an unasked question.

**H18 — ANSWERED.** The evidence for the only closed axis survives only in an untyped event log under
a cascade delete.
*Measured:* 4,279 SUCCEEDED `compare_paired_panels` jobs; 437,405 `job_event` rows;
`job_event_job_id_fkey` `ON DELETE CASCADE`; `compare_paired_panels` writes no table, only `emit`.
Compounding it: `evaluation_result.job_id` is `ON DELETE SET NULL`, and `job.payload` is the sole
carrier of both `th_step` and `information_accretion_set_id`
(`seal_evaluation_frames.py:70-72` — *"no column records it, which is why a row without a job cannot
be sealed however much else survives"*). **Deleting one job silently converts a retired result into
an unmarked one and an attributable result into an unsealable one.**

**H19 — ANSWERED.** The closing rule has never executed, so its failure mode has never been observed
and it cannot be compared against the alternatives empirically.
*Measured:* no floor in this database has produced `True` or `False`; both `CrossedFrames` branches
fire, and in a hand-neutralised counterfactual the best rival in nine of nine panels is a
`cut at protein rank 1` arm, so `_refuse_crossed_depths` raises before any panel testifies. The
refusal is then discarded at `_graph_nodes.py:53-55`.
*Refuted by:* any live call to `separated_from_floor` returning a boolean.

**H20 — ANSWERED.** For each figure the thesis presents as a headline, the binding obstruction to
campaign recovery is its window, a required table with zero rows, or the absence of a prediction set
on its $t_0$ — not the ban on aggregating panels.
*Measured:* 0.7291's window is *"GOA 226 ($t_0$) → GOA 230 ($t_1$)"* (`06_evaluation.tex:703`) and
`reranker_model` holds 0 rows; 0.5427's re-ranker window is GOA 220→229 (`07_conclusion.tex:87`),
same zero; 0.4386–0.4669 is a single panel (NK-BPO, `06_evaluation.tex:673-676`) so aggregation
cannot be its obstruction under any reading; 0.391 / 0.3745 have $t_0$ = GOA 227 and
`select a.source_version, count(ps.id) … group by 1` gives **220 → 86 prediction sets, 227 → 0**, and
`select frame, count(*) from evaluation_result group by 1` gives 85 `internal` and 230 NULL with
**zero** `lafa`. The thesis itself concedes at `06_evaluation.tex:1157-1160` that the LAFA artefacts
are *"no longer byte-for-byte reproducible."*
*Predicted count of headline figures whose only obstruction is the aggregation ban: zero.*

---

## 5. The instrumentation changes

Ordered. Each states the file:line it touches, its cost, the machine, what it refuses, and what makes
it self-enforcing. "Self-enforcing" means part 3 of §3.5: one test for the refusal and one for the
action. All of it runs on the laptop, which owns state; none of it belongs on the desktop, which is a
stateless compute node.

| # | change | file:line | cost | machine | refuses | self-enforcing by |
|---|---|---|---|---|---|---|
| **I1** | `status` predicate on `_Q_FLOORS` | `_graph_reads.py:346-354` | 1 line + 2 tests | laptop | a retracted declaration gating anything | test: a floor on an `abandoned` run is absent from `floors`; test: a floor on a `done` run is present |
| **I2** | publish `floor`, `separated`, and the refusal text on the node payload | `_graph_edges.py:119-132`; `_graph_nodes.py:53-55` | small | laptop | nothing; makes a refusal *visible* | test: every node dict carries the three keys; test: a `CrossedFrames` refusal reaches the payload, as `_scoring_node` already does at `_graph_nodes.py:402-419` and `tests/test_graph_endpoint.py:646` |
| **I3** | the frame is *designated*, not the newest row; and `comparable_window()` is answered in writing | `graph.py:239`; `_graph_reads.py:51`; `split_registry.py:320-326` | small + one decision | laptop | a frame chosen by insert order; a served frame nobody declared | test: inserting a newer `evaluation_set` does not change the served frame; test: with no designated frame the surface refuses rather than guessing |
| **I4** | promote the paired verdict to a typed table; backfill from `job_event` | new migration; write path at `compare_paired_panels.py:501` | migration + backfill of **9,138** whole-panel readings (6,816 / 2,299 / 23) plus strata, over 437,405 events | laptop | deleting a job deleting the only evidence for the closed axis | FK to `evaluation_result` (both arms) `ON DELETE RESTRICT`; test: the delete raises; test: a legitimate verdict insert succeeds |
| **I5** | carry the sixth word | `_paired_panels_panel.py:753-760` → `_graph_edges.py:14-18` | small | laptop | a powered null read as an unasked question | test over `TALLY_KEYS` asserting each tally word maps to exactly one published strength, in the shape of `tests/test_graph_endpoint.py:716-730` |
| **I6** | `experiment_run` becomes the attribution spine: `evaluation_result.experiment_run_id`, FK `ON DELETE RESTRICT`; sealing refuses a result naming none | new migration; `seal_evaluation_frames.py` | migration + 315 backfill rows + one guard | laptop | a published number with no declaration behind it | test: sealing an unattributed result raises; test: sealing an attributed one succeeds |
| **I7** | materialise `th_step` and `deciding_statistic` onto `evaluation_result`, and add `deciding_statistic` to `_FRAME_FIELDS` | `seal_evaluation_frames.py:61-68` | migration + re-seal (315 rows, seconds) | laptop | comparing a 0.01 result with a 0.0005 one; comparing an `fmax_w` verdict with a paired-bootstrap one | test: two results differing only in grid get different digests; test: two identical results get one |
| **I8** | remove `temporal_window` from `_FRAME_FIELDS`, or constrain it to a vocabulary derived from the window | `seal_evaluation_frames.py:61-68`, `:91-96` | re-seal | laptop | a harness label partitioning a real frame | test: a label change does not change the digest; test: a window change does |
| **I9** | refuse a comparison whose arms hold unequal donor banks — the `layer_grid_caveat` guard | new guard beside `_graph_panels.py:361-388`; bank size onto `prediction_set.meta` or `embedding_config` | one field + one guard + 2 tests | laptop | a 528,294-donor arm against a 60,797-donor arm, which `70b1dec8.config.layer_grid_caveat` forbids in prose | test: the unequal comparison raises; test: an equal-bank comparison returns a verdict |
| **I10** | make the four `instantiated=0` literals data-driven, or rename the word so a structural block cannot be read as evidence | `_graph_nodes.py:376, :520, :585, :609` | small | laptop | reporting a verdict no experiment can move | test: with the relevant tables populated, the node leaves `blocked` |
| **I11** | bind `compute_feature_schema_sha(families, drop=[...])` into the reranker registration path and refuse a family-level drop | `feature_schema.py:303` | prepared now, built when `reranker_model` is non-empty | laptop | an ablation that drops a family rather than columns (`knn = knn_distance + knn_vote`) | test: a family-level drop request raises; test: a column-level drop yields a distinct sha |

**Three notes the researcher should read before approving.**

*I1 is prophylaxis, not repair.* Measured: the substrate edge already reads `chosen`, because the
refusal is swallowed. Adding the status predicate changes **no published word today**. It is worth
doing so that the next floor cannot be gated by a retraction; it must not be sold as fixing a
visible defect.

> **FLAG — I7 AND I8 CHANGE DECLARED DIGESTS.** Re-sealing changes `frame_digest` on all 315 rows.
> Every existing digest string in any document, plan or note becomes stale, and `evaluation_frame`'s
> `ON CONFLICT (digest) DO NOTHING` (`seal_evaluation_frames.py:117`) means the old rows survive
> beside the new. Adding `deciding_statistic` to the seal is the change `MARCO-DECLARADO.md:640-642`
> already asks for — *"Ese campo … entra en el sello, junto a los seis que ya estaban"* — so it is
> the execution of a declaration rather than a new decision, but it is still a change to a declared
> object and must be approved explicitly.

*Anything read off the live surface must be dated.* Measured: `ExecMainStartTimestamp` for the API
unit is **Mon 2026-09-07 18:56:31 CEST**, and `git log -1` in `PROTEA` is **83898f2, 2026-09-10**.
The served code is at least three days behind the tree. Every figure in this document was produced by
running the tree directly, not by calling the endpoint.

---

## 6. The procedure

Owners throughout: the **laptop** owns Postgres, RabbitMQ, MinIO, the API and every artefact; the
**desktop** (192.168.18.132, RTX 3060, 12 GiB VRAM, 12 threads, 61 GiB RAM, five worker units)
computes and publishes back. KNN runs on CPU. Mismatched code between the two mislabels results and
reports success, so no stage begins until both trees are at the same revision.

Each stage has a GATE that can fail, and the input it fails on is named.

### S0 — Designate the frame

**Precondition:** none. **Products:** (i) the researcher's answer to §1.5's flag and to X1–X4;
(ii) one designated selection window and one designated variant written into the campaign record;
(iii) the designated validation point written into `split_registry.py:326`, which asks for exactly
that. **Cost:** a decision, plus ~20 GB and one ingest if the answer is 226 → 227 (GOA 226 is absent;
~5.66 M rows, ~1,844 MB, plus its resolvable snapshot triple, plus a row in `RELEASES` at
`split_registry.py:115-129`). **Owner:** researcher, then laptop.

**GATE G0.** `comparable_window()` no longer raises, and the designated selection window's
`new_annotation_set_id` resolves to release ≤ 227.
**Fails on:** a designated selection point above 227; a designated window whose `annotation_set` does
not exist (today, any window naming 226, 229 or 230); or a designation that names two
`evaluation_set` ids, since no floor of such a run can pass `_within_the_floors_frame`.

### S1 — Carry the evidence out of the event log

**Precondition:** G0. **Products:** I4 plus the backfill. **Cost:** a migration, a write path, and one
pass over 437,405 `job_event` rows for 9,138 whole-panel readings and their strata. **Owner:** laptop.

**GATE G1.** In a transaction that is rolled back, attempt `delete from job where id = <one paired
job>`. The delete must **raise** on the verdict table's `ON DELETE RESTRICT`, and the verdict row
must be present before and after. Separately, the restored tally must reproduce 6,816 / 2,299 / 23.
**Fails on:** a cascade that removes the verdict; a backfill whose tally differs from the measured
one; any `job` deletion performed before this gate passes. **Nothing else in this plan may run
before G1**, because every later stage adds jobs whose deletion would take evidence with it.

### S2 — Re-seal under corrected frame fields

**Precondition:** G1. **Products:** I7, I8; every result carrying `th_step`, `deciding_statistic` and
a digest. **Cost:** migration plus a re-seal of 315 rows (seconds). **Owner:** laptop.

**GATE G2.** No digest contains two `th_step` values, and none contains two deciding statistics.
**Fails on the present record**, measured: all four digests contain both the 0.0005 grid and the
absent-`th_step` (0.01 default) rows.
**Also produces the retirement mark that does not exist today:** the 159 rows on the coarse grid must
become explicitly retired, not merely distinguishable by a join to a table that cascades.

### S3 — The substrate, on equal banks

**Precondition:** G2, I9. **Products:** a substrate verdict per panel, or an explicit refusal.
**Cost:** embedding work for whichever arms need bringing to a common bank — the eleven
intermediate-layer configs hold 60,797 each against 528,294, so equalising upward is ~467,497
embeddings per config on the desktop. **Owner:** desktop computes, laptop stores. **Note:** `ankh-base`
layers 10, 16 and 32 are **not evaluable** (constant score, flat grid at 1999 taus) and must not be
included.

**GATE G3.** The substrate comparison refuses unless all arms' donor bank sizes are equal, and the
refusal is visible in the payload (I2).
**Fails on:** the present `sequence_embedding` census, where 528,294 and 60,797 arms sit inside one
seal. Also fails if the axis-A `haz` of three is silently collapsed to one without X3 being answered.

### S4 — The evaluation cut

**Precondition:** G2, and X2 answered. **Products:** the 42 existing live cells published through
whichever node X2 designates; the 42 coarse-grid cells marked retired. **Cost:** near zero for the
cells that exist; the cut comes out of the materialised K=200 tensor without re-retrieving
(`MARCO-DECLARADO.md:548-550`, and `bbb96a35.config.tensor_verificado` records the ledger census as
10,423,562 of 10,423,562). **Owner:** laptop.

**GATE G4.** Withholding the 84 cut-bearing results changes some node's `levels_instantiated`.
**Fails today**, measured: `max_k_position` is selected by no query feeding a node builder and the
retriever reports five levels from `limit_per_entry = 200`, constant on all 86 prediction sets.

### S5 — Channelling, cross-fitted

**Precondition:** G3, G4, and a designated deciding statistic (H4). **Products:** a routing policy
whose fold assignment is stored, and an out-of-fold verdict per region. **Cost:** the strata already
exist; the cost is the cross-fitted scoring pass and the storage of fold membership. **Owner:**
desktop computes, laptop stores.

**GATE G5.** The published routing verdict is out-of-fold, and the comparison refuses when the fitted
and evaluated partitions intersect.
**Fails on:** a policy fitted on all fifteen regions and reported on the same fifteen; a region set
whose membership was taken from the channelled arm rather than the baseline; and — flag this to the
researcher — on `LK:BPO@length=512-1024`, which clears the routing floor of 332 at exactly n = 332
and will drop out of the region set under any variant change or any tightening of the floor rule.

### S6 — The single holdout measurement

**Precondition:** every earlier gate passed; the champion frozen; its declaration row transitioned to
`status='done'` through `PATCH /experiment-runs/{id}` so the declaration and the data agree.
**Products:** one nine-vector on the designated validation point. **Owner:** researcher authorises,
laptop executes.

**GATE G6.** Before any score is computed on the holdout frame, the leakage guard must **demonstrate a
refusal on that frame** and then permit the champion.
**Fails on:** any fitted encoding whose training cut lies inside the frame. Note precisely why this
gate is load-bearing: on the adopted 220 → 227 frame the guard **provably cannot raise** — three of
25 `embedding_config` rows are in `FITTED_BACKENDS` and all three declare a cut of 220, and
`leakage_guard.py:74` requires `frame.start < training_release <= frame.end` — so the ACT half of
**D3** for this guard is unevidenced until S6, and `tests/test_leakage_guard.py:16` demonstrates its
refusal only on `Frame(220, 230)`.

### The holdout protocol

1. **227 → 230 is never read and never planned as a scoring target.** `annotation_set` holds four
   releases and stops at 227 (measured). GOA 230 was deleted with zero dependents, and
   `PLAN-EXPERIMENTAL.md:162-165` states the consequence: *"Si el dato no está, no se puede mirar por
   accidente, ni por un select distraído, ni por un job mal parametrizado."* **The holdout is enforced
   by absence, not by discipline.** Keep it that way.
2. **The author's declared competition window is wider than 227 → 230.** `E2E-CANONICAL-RUN.md:10-13`
   reads *"COMPETE window: 227 → forward, OPEN-ENDED … This supersedes the fixed 227 → 230 test."*
   `split_registry.py:246` holds seven validation windows, v227→v228 through v233→v234. Obey the
   wider rule: **nothing at or after release 227 on the new side informs any choice.** Exactly one of
   those seven points is designated at S0, and designating it does not license reading it before S6.
3. **One deliberate act, once.** The reload recipe is recorded so it need not be reconstructed:
   `gaf_url` `…/goa_uniprot_all.gaf.230.gz` (14.4 GB), `source_version` 230, published 2026-03-04,
   GAF `!go-version` `releases/2026-03-01`, `ontology_snapshot_id` `8924aec0` =
   `releases/2026-01-23` (`PLAN-EXPERIMENTAL.md:171-177`). Fourteen point four gigabytes is the
   friction that makes the mistake deliberate.
4. **The thesis's scheduled 227 → 230 recompute is struck, not deferred.**
   `04_system_design.tex:1023-1025` and the only `\TODO` at `06_evaluation.tex:889` both book that
   read. Neither may be executed by this campaign.
5. **No campaign artefact may name 230, 231, 232, 233 or 234 as a scoring target** before G6.

---

## 7. Risks, confounds and limits

**What the campaign will not be able to claim, and why.**

*No comparison with any thesis headline figure.* 0.7291 is a *"NK + LK combined macro-average"*
(`06_evaluation.tex:729-730`); 0.5427 is *"across the nine category-aspect cells"*
(`07_conclusion.tex:88-89`); 0.391 and 0.3745 are *"averaged over the three namespaces"*
(`06_evaluation.tex:1030-1031`). Each also differs from the campaign's numbers in metric space
(`06_evaluation.tex:426-431`: `fmax_w` is the CAFA protein-centric quantity, `f_micro_w` the pooled
one), in window, and in harness. **These are different quantities and must never appear in one
comparison.** The thesis says so itself at `06_evaluation.tex:895-897`.

*No claim against alignment-based methods.* RQ1's primary comparison has no in-platform comparator.
The only eggNOG/BLAST code is `PROTEA/scripts/evaluate_external_tool.py`, which is absent from the 39
registrations in `operation_catalog.py` and from all 12 observed `job.operation` values, and whose
output cannot reach `evaluation_result`. The live claim surface is **retrieval-side and internal**: it
can rank configurations against each other and cannot yet place any of them against an external
method.

*No claim for RQ2 at all.* Six named zeros. And two RQ answers already written must be marked as
resting entirely on superseded measurement: `07_conclusion.tex:158-176` answers RQ2 *"Yes"* with
`anc2vec_query` at a mean ΔF_max of +0.1449, and `:141-157` claims +0.049 F_max for the re-ranker and
a nine-cell win over eggNOG-mapper. Nothing in the live database supports either.

*No reproducibility claim about a model.* `07_conclusion.tex:186-188` asserts that re-running a
payload reproduces *"identical models and results"*, and `04_system_design.tex:16-19` states R1
Reproducibility. What is measured is **scoring** determinism — 117 of 117 metrics reproduce exactly —
which is a weaker statement than either sentence. There are no models.

*No depth or substrate verdict from the reduced grid.* `70b1dec8.config.layer_grid_population` is
*"muestra reducida: 23.737 consultas + 40.000 del banco"*, and its `layer_grid_caveat` declares those
scores non-comparable with full-corpus arms. The published depth result came from exactly that
comparison and must be withdrawn.

*Three arms are not evaluable.* `ankh-base` layers 10, 16 and 32: constant score, flat grid at 1999
taus.

*Nothing is summed or averaged over the nine panels.* Not by the campaign, not by the surface, and not
by the paired operation, which refuses and names the paragraph (`compare_paired_panels.py:49-53`).

*"Identical" is an upper bound.* Everything stored is rounded to 1e-4. A difference read as zero from
the database is a bound on agreement, never a measured zero. Combined with `separated_from_floor`'s
bare `max <= max`, resolution can decide a verdict — **D5** — which is why §3.6's rule is
interval-based.

*`n_proteins` is a threshold count, not a cohort size.* A correlation with it has no reading.

**Confounds that remain after every change in §5.**

The 8.689× donor asymmetry is the one confound that can invalidate a whole node, and I9 refuses
rather than corrects it: until the banks are equalised the substrate axis produces refusals, not
verdicts.

The two 220 → 227 variants disagree by 2.45× in PK:BPO and are identical in LK:CCO, and the mechanism
is **not established**. Any verdict that pools them is void; any verdict published on one must name
which.

`MARCO-DECLARADO.md:148-154` records **426,385 annotations retired over 47,455 proteins** — twice as
many proteins as gain — and states plainly that *"nadie la ha mirado."* Until that is broken down by
cause (obsolete term, relation change, real retraction), the window's trustworthiness is bounded by
an unexamined number larger than the gains the campaign measures.

**Things I could not establish, stated so no reader takes them as measured.**

I did not run `GET /v1/graph`. Every statement about the served surface comes from running
`read_record` and `build_graph` on the tree with `candidates` stubbed empty. The stub affects one
prose sentence (the candidate count in the retriever's reason). I avoided the call because the served
code is three days stale and because `_Q_CANDIDATES` is a full scan.

I did not time `_Q_CANDIDATES`. The 303.3 s over 336 GB, the 240 s prewarm
(`PREDICTION_SETS_TTL_SECONDS = 300.0` at `embeddings.py:46`, `_refresh_interval` at `app.py:385-386`
giving 240) and the resulting 543 s cycle at 55.8% duty come from the brief and were **not
re-measured**; running the query is the cost. What I did measure: `go_prediction` is 439 GB total over
336 GB of heap and ~795.2 M rows with 74 columns; its six indexes include
`ix_go_prediction_set_accession` at 8,552 MB, which is the leading-column index an index-only
`GROUP BY prediction_set_id` would use.

The claim that 50 of 74 `go_prediction` columns are 100% NULL is **not established at that
precision**: the brief says 50, a prior 200,000-row sample gave 51, and two successive unordered
samples disagreed about `identity_nw` (5,047 non-null, then 0). A full count scans 439 GB. The
disagreement is itself a hazard for any planned ablation: dropping a column that is NULL on most rows
returns "no contribution" for a reason unrelated to signal.

I did not locate the thesis's `bench-v1-K5-v226-lineage-prostt5` dataset. `dataset` holds zero rows
and I did not search MinIO.

I did not investigate the 194 FAILED `compare_paired_panels` jobs, nor the
`job.queue_stall_requeue` events I observed on a SUCCEEDED one, nor why the 160→219 evaluation set's
`stats` differ in structure from the pairs the campaign scores.

The abandoned run's dates disagree with themselves: `created_at` 2026-09-03, `findings` saying
*"Abandonado el 2026-09-04"*, `finished_at` NULL. I cite both and treat the findings text as the
abandonment date.

---

## 8. The four decisions for the researcher

These are not decided here. Each is stated with the consequence of each answer.

### X1 — Which vocabulary is authoritative: `SPECS` in code, or the declared `experiment_run` rows?

Measured: `SPECS` names ten keys at `_graph_edges.py:73-84`. Of the four declared `graph_node` values,
three — `retrieval_tensor`, `cut_depth`, `bank_and_donor` — are not `SPECS` keys; the one that is,
`substrate`, sits on the row abandoned on 2026-09-04.

*If `SPECS` wins:* three of four existing declarations must be rewritten, and a check must refuse a
`graph_node` outside the ten. Cheap, and it means the declaration language can never name a decision
the surface has no node for.
*If the declared rows win:* `SPECS` becomes derived data and the ten builders must be generated from
the rows. A larger change, and the only version in which a new axis can be declared without a code
release.

### X2 — Does the evaluation cut become an eleventh `SPECS` node, or does the retriever read it?

Measured: 42 live results form a clean 3 × 7 × 2 factorial over `max_k_position`; no node sees any of
it; the retriever reports five levels, all at `limit_per_entry = 200`.

*As an eleventh node:* it gets its own floor, its own strength and its own guard, and the depth-unit
refusal at `_graph_panels.py:326-358` becomes a rule *between* two nodes rather than inside one. It
breaks the ten-builder invariant at `tests/test_graph_endpoint.py:726`, which must then be updated to
eleven deliberately.
*Folded into the retriever:* no new node, but `levels_instantiated` then mixes a re-run (retrieval
depth, which changes which candidates exist) with a truncation (an evaluation cut, which re-reads a
list already retrieved) — the exact conflation `_arm_identity.py:26-37` was written to end.

### X3 — What carries from one axis to the next: one floor level, or a survivor set?

Measured: `_Q_FLOORS` can read one string. Axis A produced neither one nor nine but a beam of three
(`MARCO-DECLARADO.md:530-533`), recorded under `haz` on both surviving declarations, which nothing
reads. Axis B's `supersedes_floor` reads *"ninguno: el eje A quedo ABIERTO."*

*A single floor:* keeps every downstream grid at its current size and forces a choice the data did not
make. It also requires choosing between `ankh_large` (first under `fmax_w`) and `protst` (first under
the paired bootstrap), which is H4 in disguise.
*A survivor set:* is honest, multiplies the next axis's grid by its size — 3× today — and requires
`_Q_FLOORS`, `Edge.floor` and `separated_from_floor` to take a set rather than a string.

### X4 — May the graph answer a derived number from a stored copy?

`_graph_reads.py:15-17` says no: *"a surface whose job is to report what the record holds right now
must not answer from a copy of what it held earlier."* Against that stands one scan over 336 GB for
one integer printed in one prose sentence, relaunched by a 240 s prewarm timer on the machine that
owns all state.

*Holding the rule:* means either paying that cost or deleting the sentence. Measured: the remaining
fourteen registered clauses total **0.409 s** (substrates 270.8 ms, panels 44.6 ms, floors 0.6 ms), so
deleting the sentence makes the surface three orders of magnitude cheaper and costs one prose clause
in the retriever's reason.
*Relaxing it:* means the surface can report a number that was true earlier, which is **D4** with a
clock on it. The relaxation would have to be typed — every cached figure carrying the time it was
read — never granted globally.

### 8.5 Declared decisions this document would change — flagged, not decided

Three items require an explicit ruling because executing this document changes something already
written down. They are listed here so that no silence reads as consent.

| # | the declaration | what this document does to it |
|---|---|---|
| **F1** | `E2E-CANONICAL-RUN.md:8-17`, FIXED BY THE AUTHOR 2026-07-27: TUNE window 226 → 227, explicitly *superseding* SELECT 220 → 227; encoded at `split_registry.py:287`. | §1.5 adopts 220 → 227, the superseded window, because GOA 226 is absent and 315 results and both scoring-side evaluation sets already sit on 220 → 227. Requires either a written re-affirmation of 220 → 227 or the GOA 226 ingest (§6 S0). |
| **F2** | All four `experiment_run` rows name `b7cfed9a` **and** `b7452c0e` together as one frame. | §1.5 names `b7cfed9a` alone, on the rule at `PLAN-EXPERIMENTAL.md:196-206`. This changes the meaning of every declaration in the database, and changes the routing region count from 15 to 17. |
| **F3** | `_FRAME_FIELDS` at `seal_evaluation_frames.py:61-68`, six fields, and `:58-60`'s argument that a scoring preset is a level and not a frame. | §5 I7 adds `deciding_statistic` and `th_step`, and I8 removes or constrains `temporal_window`. I7 executes `MARCO-DECLARADO.md:640-642`; I8 does not execute any declaration and is a new decision. Both re-digest all 315 rows. |

One further question is raised by the measurements and belongs on the researcher's list beside
X1–X4, without being one of them: **is a frame named by its annotation pair, or by its digest?** The
four declarations assume the pair. The seal assumes the digest. On the data that exists they disagree
by a factor of 1.64 in total units and 2.45 in PK:BPO.
---

## 9. Definitions

Every term this document uses, with the place in the tree where the object
actually exists. A term defined here has that meaning and no other above.

### 9.1 The chain, in one pass

A **query** is a protein needing prediction. A **substrate** turns it into a
vector. A **retriever** finds the nearest vectors. A **bank** decides which of
those neighbours is allowed to donate, and what it may donate. Each donation is
a **candidate**. **Scoring** gives the candidate a number, **features** describe
it, **re-ranking** reorders it, **combination** merges flows, and **routing**
decides which flow answers which panel. Ten decisions, ten stages, in that order.

### 9.2 Substrate, and what H5 is about

**Substrate** is the vector space in which the word *neighbour* is defined. It is
the whole encoding configuration, not the model name: `model_name`,
`model_backend`, `layer_indices`, `layer_agg`, `pooling`, `normalize`,
`normalize_residues`, `max_length`, `use_chunking`, `chunk_size`,
`chunk_overlap`. Change any of them and the distances change, so who is whose
neighbour changes, so which donors are retrieved changes, so the prediction
changes.

It is worth saying what it is **not**. It is not a classifier. Nothing is trained
here. It is only the function that turns a sequence into a vector. Everything the
base method does afterwards is measuring distances in that space and copying
annotations from the closest ones.

**H5 says that a substrate comparison on the present record cannot isolate the
substrate.** Twelve configurations hold 528,294 stored embeddings and eleven hold
60,797 — a factor of **8.6895**, from one grouped count. That ratio is of *stored
embeddings*, not of donors: netting out the 23,737 queries would give roughly 13.6×,
except that 23,737 + 40,000 does not reconcile with the 60,797 census, so **the
magnitude of the confound is not established** even though its existence is. An arm on the large
population wins partly because it has 8.69× more donors to choose from, and that
is not a property of the representation. It is the same as comparing two search
engines where one indexes 8.69× more documents: the better results might be the
algorithm or might be the index, and no quantity computed afterwards separates
them. `prediction_set.meta` carries no bank-size field, so the confound is not
even visible in the record. I9 refuses the comparison rather than correcting it,
because it cannot be corrected after the fact.

### 9.3 Bank

**Bank** is who is allowed to donate, and what they may say. Two halves that
cannot be decided apart, which is why they are one node:

| half | what it is | fields |
|---|---|---|
| corpus | which annotation set the donors come from | fixed by the frame: the window's lower endpoint is the only release a donor may come from without reading the future |
| donor policy | which subset of that corpus may actually donate | `donor_reviewed_only`, `donor_evidence_codes`, `donor_exclusions` |

**Three switches this table used to list here, and the code does not.**
`exclude_self_neighbour`, `expand_votes_to_ancestors` and `aspect_separated_knn`
modify the act of donating and read naturally as bank policy. In the tree they are
not: `_BANK_FIELDS` holds only the five above, while the three booleans sit in
`_RETRIEVER_FIELDS` under a comment reading *"Who may be a neighbour, which is this
node and not the bank"* (`_graph_nodes.py:204-210`, `:275-287`).

**The consequence has to be stated whole.** The axis the campaign declared closed as
*bank and donor* was measured on those three booleans plus the donor policy. In the
code the three booleans close the **retriever**; the `bank` node is still `unpowered`
because its only scored level is corpus 220 — and measured, the five levels §1.2
attributes to the retriever are exactly the five combinations of those three
booleans, since depth, metric and backend are constant on all 86 prediction sets. A
reader cannot tell today whether what closed was the bank or the retriever, and the
bank node leaves `unpowered` only by loading a second corpus — which is H8. That
connection is the one this document did not make.

They are one node because a corpus and the filter applied to it define one bank
between them, and a group of inseparable fields is held no more firmly than its
loosest member: corpus pinned by the frame plus an empty policy reads
`inherited` for the node as a whole.

**The distinction from substrate, in one sentence: the substrate decides who is
near; the bank decides which of the near ones gets listened to.** A permissive
bank admits donors whose own annotation rests on computational inference, which
raises coverage and lowers per-donor reliability. A bank restricted to
experimental evidence does the opposite. Which wins is not obvious a priori and
is what the campaign measured. Two corrections to how that result has been quoted.
First, the **polarity**: `_restrict_annotations` filters only `if codes`, so the
thirteen-code list *restricts* and the empty policy is the permissive one. The
substantive result survives — the no-filter arm wins — but the arm labels have been
printed backwards. Second, **the numbers**: it is not 54 of 54 in every cell. Of 216
stratified panel readings, 197 resolve, **196 favour the permissive arm and one does
not** (`LK:MFO@>90`); the effect is between **69% and 78%** larger below 30% identity
than above 90% depending on the aggregation route, not a single 71%. And the `none`
band **is not measured at all**: its six comparisons failed, so homology is measured
over four bands, not five.

One property of the bank contaminates several readings. Under the temporal
protocol a query retrieves *itself* from the earlier bank if it was already
annotated then. That self hit sits at distance zero and is the nearest donor for
most previously-annotated proteins. `exclude_self_neighbour` removes it, and the
four neighbourhood strata axes are all resolved over donors of differing
sequence for the same reason.

### 9.4 The rest, briefly

| term | definition |
|---|---|
| **frame** | the conditions a number is read under, and therefore what must match for two numbers to be comparable. Six sealed fields today, eight proposed |
| **frame digest** | the cryptographic seal over those fields. The only real one: the column called `frame`, holding the string `internal`, is a harness label |
| **level** | a value *together with every field that varies across the rows it is compared with*. Its arity is a property of the query, not of the value, so no stored string can name one |
| **node** | one decision over a field, or over a group that cannot be decided apart. Exactly ten, pinned by a test |
| **strength** | one of five words saying how firmly a decision is held. Order of tests is the argument |
| **floor** | the incumbent declared *before* measuring. The only thing needed from outside the result tables to reach `measured` |
| **survivor set** | the levels no voting cell ever beat. The correct outcome when an axis does not seal |
| **panel** | category × aspect, nine cells, mandatory, never aggregated |
| **stratum** | a point on seven axes. Three are properties of the query (`category`, `aspect`, `length`); four are properties of a retrieval and need an aligned donor |
| **population floor** | the smallest cell allowed to vote, `ceil((2.8016·σ/0.02)²)`. 332 with a global σ of 0.13; 120 to 1,376 with each panel's own σ, under which three of nine panels fall below their own |
| **`fmax_w`** | CAFA's protein-centric measure. Admits **no** `σ/√n`: it is a max over τ of a non-linear combination of two population means |
| **MDE** | the smallest difference a cell can tell from zero. Median 0.0019 (`PK:BPO`) to 0.0256 (`LK:CCO`), a factor of 13.3; and it varies by over 20× *within* a panel, so it is published as a range |

### 9.5 What a confidence interval is for here

The objection that an interval adds noise is the right objection, and the answer
is that the interval does not add the noise, it **measures** it. Without it the
noise is still there and invisible. But its role here is narrower than usual:

**It is an instrument of selection, not of publication.** Its job is to decide
which configuration goes forward. It does not need to be published to compete in
an external evaluation, where the arbiter is the organiser's leaderboard. Four
concrete reasons it earns its place:

1. **Quantisation.** Everything stored is rounded to 1e-4; the worst-resolved
   panel's MDE is 0.0234. The ratio is **234**. A rule that compares two maxima
   and keeps the larger decides, at worst, on differences 234× smaller than what
   that cell can distinguish from zero.
2. **Multiplicity, which grows with the ambition of the design.** Channelling
   lets the channelled arm choose *once per region* while the baseline chooses
   once: with 15 regions it has 15 chances to look better by luck. This is not an
   objection to channelling, it is its condition of validity, and only
   cross-fitting repairs it.
3. **It makes "this cell cannot say" writable.** The vocabulary already emits
   `null_with_power` and `null_unread` — the difference between *we looked and
   there is no effect* and *we could not look*. A point-estimate rule has to turn
   both into a vote in some direction, which is worse than abstaining.
4. **External submissions are scarce.** Validation ends in a LAFA deployment and
   later CAFA. Submissions are limited and the feedback cycle is months. Every
   configuration sent that was chosen on noise is a wasted submission. External
   validation does not reduce the need for internal rigour; it raises it, because
   it makes the error expensive.

#### The honest objection, which the rule as stated does not survive

Requiring the interval to exclude zero before a cell votes has a logical hole and an
adverse case, and both are quantifiable from the panel table above.

**The hole.** If no cell votes, *one level wins every voting cell* is vacuously true
for every level at once. The rule defines no quorum, so in the small-effect regime it
does not fail to seal — it breaks.

**The adverse case.** A uniform effect of +0.004 is resolvable only in `PK:BPO`
(MDE 0.0032); below 0.0126 no `NK` or `LK` cell can vote. The rule degenerates into
*`PK:BPO` decides* — the easiest category, and not the one the project wants to
headline. Worse: a real but small effect with the same sign in 9 of 9 panels and no
interval excluding zero casts zero votes and does not seal, while a sign test over
nine panels gives p = 0.004. **The rule loses a correct decision that consistency
does support** — and that is exactly the shape of the evidence H6 and H9 already rest
on (9 of 9 cells, 36 of 36 gaps, 5 adjacent contrasts).

**And multiplicity cuts both ways.** The argument above invokes it to justify the
interval, then does not apply it to its own rule: at 95% per cell, P(at least one of
nine votes falsely) is 37%, and with seventeen regions 58%. Under unanimity a single
false cell seals or vetoes alone. Cross-fitting repairs selection, not the
family-wise error rate.

Three clauses close it: **quorum** (no seal below three voting cells; the outcome is
*unresolved*, which is not *did not separate*), a **second sealing path by sign
consistency** (nine same-sign panels seal with a weaker, explicitly labelled mark),
and a **corrected per-cell level** (99.4% for nine cells to hold 5% family-wise,
which is conservative and should be said to be). And the cost the argument omits:
not sealing multiplies the next axis's grid by the beam size, 3× today, and with no
seal there is no champion to freeze at S6. Scarce submissions cut the other way too.

**And the holdout question resolves itself under external validation.** In CAFA
and LAFA you predict on proteins whose annotation does not exist yet, and the
organisers score later against annotations that accrue after submission closes.
Leakage is impossible by construction. All the discipline about 227 applies only
to the *internal* numbers the campaign cites to justify its own choices.

### 9.6 Stratification granularity, and its hard limit

The panel is the mandatory partition; the stratum is the refinement *within* the
panel. The stratum rides inside the panel key (`NK:MFO@length=512-1024`), so a
restriction yields nine restricted cells and never a number.

The limit is arithmetic, not computational. The full cross of seven axes is
3 × 3 × 4 × 5 × 3 × 6 × 5 = **16,200 cells** against roughly 30,427 paired units.
That is under two proteins per cell, against a voting floor of 332. **The full
cross is empty almost everywhere, and no amount of compute fixes it, because
compute does not produce more proteins.** Measured: crossing the panel with a
single length band leaves **17 cells** above the global floor and **11** above the per-panel
floor, all eleven inside five panels.

Three rules follow:

- Panel is mandatory; refinement is **one axis at a time**. Panel by length, or
  panel by homology, not both.
- The refining axis is **declared before the run**. Trying several and reporting
  the one that separated is selecting on noise under another name.
- The full seven-way cross is a tool for **describing the champion**, not for
  selecting it.
