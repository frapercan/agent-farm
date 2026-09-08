# Slice: walls

Auditor slice key: `walls`.
Scope: `plans/bp-structural-lever/` (PLAN.md, RESULTS.md, DESIGN-cross-encoder.md) and
`plans/prior-knowledge-wall/`.

Central task: resolve a direct contradiction.
- DESIGN-cross-encoder.md: structure is ENTIRELY ABSENT (no FoldSeek, no AFDB, UniProt->AFDB
  not mapped).
- SIGNAL-REGISTRY.md: structural gate listed as REFUTED, i.e. measured.
- thesis-pillars/PILLARS.md:95 quotes a positive control at 66.6% MF vs 20.7% BP.
Those cannot all be true.
Second contradiction: the same design doc claims per-residue PLM embeddings are NOT
persisted, while storage/probe/ contains ~74.4M per-residue vectors.

Status: IN PROGRESS (appending as findings land).

---

## Document dating (the precondition for everything else)

All files under `agent-farm/plans/` carry mtime `Jul 28 17:01` because the tree was
restored from the snapshot on 2026-07-28. **mtimes in plans/ are worthless.** Git in
`agent-farm` is the only dating authority.

| file | commit | authored date | self-declared date in header |
|---|---|---|---|
| `plans/bp-structural-lever/{PLAN,RESULTS,DESIGN-cross-encoder}.md` | `d359edd` (#211), later `2a32d54` (#223) | **2026-06-30**, touched 2026-07-10 | DESIGN header says "(2026-06-30)" |
| `plans/thesis-pillars/PILLARS.md` | `88ccc61` (#214) | **2026-07-09** | header says "Written 2026-07-08" |
| `plans/prior-knowledge-wall/PLAN.md` | `6d66f12` (#231) | **2026-07-17** | (checked below) |
| `plans/SIGNAL-REGISTRY.md` | `f0e50a6` (#233) | **2026-07-27** | header says 2026-07-27 |

So the three "contradictory" documents are **nine days, eighteen days and twenty-seven
days apart**, in that order. Provisional reading: no contradiction in principle, a
stale-claim problem. But EVERY one of them is **pre-2026-08-27**, i.e. pre-registry-wipe,
so none of them is evidence about the current window. Confirming below what was actually
measured.

verdict on the dating: CONFIRMED
date of evidence: 2026-06-30 / 2026-07-09 / 2026-07-17 / 2026-07-27 -> window: **pre-wipe**

---

## THE CONTRADICTION, resolved: three documents, three states of one claim

### (a) 2026-06-30, the whole `bp-structural-lever` directory says structure DOES NOT EXIST

All three files were authored the same day (commit `d359edd`, #211) and agree:

- `plans/bp-structural-lever/DESIGN-cross-encoder.md:~/gap 3`:
  "STRUCTURE is entirely absent (no FoldSeek 3Di, no AFDB; UniProt->AFDB not mapped).
   FunBind's structure modality is a NEW pipeline, out of scope for v1."
- `plans/bp-structural-lever/PLAN.md` (Data): "New only for (D): FoldSeek 3Di from AFDB,
  fetched+cached as a backend." Structure is **Phase 3, optional, gated, not run**.
- `plans/bp-structural-lever/RESULTS.md` (the run report of the same day):
  "The only lever that could inject the missing signal is ORTHOGONAL MULTIMODAL EVIDENCE
   (FunBind's approach): structure (FoldSeek 3Di) ... **This is a large new data+model
   effort with uncertain payoff and is a strategic call.** ... Strategic fork left for
   the author."

So on 2026-06-30 structure was **not built, not mapped, not measured**, and the
document explicitly hands the decision back to the author.

### (b) 2026-07-09, PILLARS.md reports structure as MEASURED and RED

`plans/thesis-pillars/PILLARS.md:95` (commit `88ccc61`, authored 2026-07-09; the line is
present in the FIRST version of the file, so it was not retro-fitted):

  | **structure (AFDB/FoldSeek 3Di, real)** | **RED** (residual 0.545; structure conserves
  MOLECULAR FUNCTION not BIOLOGICAL PROCESS: a clean positive control finds the true
  functional neighbour 66.6% of the time for MF vs 20.7% for BP) |

### (c) 2026-07-27, SIGNAL-REGISTRY.md hardens it to REFUTED

`plans/SIGNAL-REGISTRY.md:125`, inside "## 4. REFUTED (measured, negative, closed)":
"... phylogenetic profiling, **structural gate (AFDB/FoldSeek)**, annotation-space RAG, ..."
Section 4's own definition is "measured, negative, closed". No number, no receipt, no CI,
no cell breakdown is attached to the structural entry anywhere in that 24 KB document
(`grep -n -iE "structur|foldseek|3di|afdb|alphafold|prostt5" SIGNAL-REGISTRY.md` returns
exactly TWO lines: 125 and 315, neither carrying a number).

verdict: the three documents are **NOT simultaneously false; they are a 9-day and then a
27-day staleness chain.** But (c) is an ECHO of (b) with the number dropped, and (b)'s
receipt is missing. See next section.

## The receipt for 66.6 / 20.7 / 0.545 does not exist on this machine

first number: `66.6% MF vs 20.7% BP`, residual `0.545` -- PILLARS.md:95
second number: NONE OBTAINABLE. `grep -rnE "66\.6|20\.7|0\.545|0\.666|0\.207"` over
  `agent-farm/` and `thesis/` returns **exactly one hit for this claim** (PILLARS.md:95).
  The only other 66.6 in the plan store is an unrelated compute ratio
  (`ABLATION-ARCHITECTURE.md:137`, "a factor of 66.6").
  Over the memory store the only 20.7 hits are a different claim entirely
  (`project_gained_side_baseline_is_experimental_only_2026_08_26.md:32`, "20.7% of
  everything gained", and the retracted 20.7% capture ratio in
  `project_rankpct_artifact_invalidates_baseline_2026_07_16.md`) -- coincidence of digits,
  not the same measurement.
verdict: **NOT_FOUND (single-source, receipt missing)**
PILLARS.md names its receipt explicitly at line 154:
  "**Evidence:** `project_structural_gate_bp_wall_2026_07_07` (the wall), ..."
That memory file **does not exist anywhere on this filesystem**
(`find / -name "project_structural_gate_bp_wall_2026_07_07*"` -> nothing;
 not in `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`).
MEMORY.md says the archived memories live in
`/mnt/protea-archive/archive/memory-archive-2026-07-27/` (98 files) --
**`/mnt/protea-archive` is an EMPTY, UNMOUNTED directory** (`mount | grep protea` -> nothing;
`ls /mnt/protea-archive` -> empty). Two of the three memories PILLARS cites as its evidence
are gone: `project_structural_gate_bp_wall_2026_07_07` MISSING,
`project_gotext_label_basis_bp_lever_2026_07_08` MISSING,
`project_text_evidence_scorer_2026_07_08` present.
date of evidence: 2026-07-07 (claimed) -> window: **pre-wipe, and now pre-reinstall-lost**
note: the number is 27 days older than the registry wipe AND its sole receipt is on an
unmounted partition. Under the project's own rule ("ANY measured result dated before
2026-08-27 is NOT evidence about the current window"), PILLARS.md:95 is not citable.

---

## FoldSeek WAS actually run. The evidence is three files, and none of them is the analysis.

`/home/xaxi/Thesis2/repositories/protea-reranker-lab/research/struct_gate/` contains exactly
three tracked files, all of them **FoldSeek's own auto-generated tmp workflow scripts**:

    research/struct_gate/tmp/1131384753032580127/download.sh          (foldseek databases)
    research/struct_gate/tmp/14482967868506212309/structuresearch.sh  (foldseek search)
    research/struct_gate/tmp/8494955556501692353/structuresearch.sh   (foldseek search)

`structuresearch.sh` is the MMseqs2/FoldSeek "Assembler workflow script" emitted into TMP_PATH
by a real `foldseek search` invocation (it references `$MMSEQS prefilter`, `tmalign`,
`structurealign`). Two distinct tmp hashes = at least two searches. `download.sh` is what
`foldseek databases` writes. **So a real structural search ran on this project.**

verdict on "structure is entirely absent": **CONTRADICTED, but only after 2026-06-30.**
  The DESIGN doc's claim was true when written and became stale within about a week.
verdict on "the structural gate was MEASURED": **CONFIRMED that foldseek ran; the
  MEASUREMENT ITSELF IS NOT_FOUND.**
first number: PILLARS.md:95 -> 66.6% MF / 20.7% BP / residual 0.545
second number: none derivable. `git ls-files research/ | grep -iE "struct|fold|3di|afdb"`
  returns those three shell scripts and one unrelated markdown. There is **no python, no
  json, no tsv, no notebook** in `struct_gate/`. Compare the sibling refuted arms preserved
  in the same commit: `phylo_profile/` 4 files, `protex/` 4, `deepgose_rescore/` 4,
  `transfew_calib/` 4, `consensus/` 2 -- all with real analysis code. `struct_gate/` 3 files,
  all machine-generated by the tool.
date of evidence: preserved 2026-07-27 in `protea-reranker-lab` commits `b86b533`/`ea4a3bd`
  ("preserve: track the research procedures that ran outside every repository", 313 files)
  -> window: **pre-wipe**
platform gap: MURO. There is no operation, and now no script, that regenerates the
  structural gate. The DESIGN doc's Phase D (UniProt->AFDB->FoldSeek 3Di as a backend) was
  never built; the run happened in a scratch directory outside every repository.
note: the preservation commit's own README says
  "**Refuted, and kept deliberately. A refutation whose code is gone cannot be defended.**
   ... `cooc_experiment/`, `struct_gate/`, `phylo_profile/`, ..."
  and lists `struct_gate/` among them. **The one it names cannot be defended: only FoldSeek's
  own temp files were caught.** The failure the README warns against happened inside the
  commit that claims to prevent it.
  (Same README lists `string_v12/` as preserved -- `git ls-files research/ | grep -i string`
  returns only `regen_headline/bp_string_{cut,maps}.py`; there is no `string_v12/` directory.
  A second entry in the same list that does not exist.)

## The project itself later called the structural gate QUALITATIVE

`repositories/protea-reranker-lab/research/regen_headline/BP_WALL_CHARACTERIZATION.md:1-5`
(dated in its own title **2026-07-16**, one week after PILLARS):

    # The BP wall is a SIGNAL limit, not an EVIDENCE limit (measured, 2026-07-16)
    ...
    This receipt answers *why*, with numbers rather than the earlier **qualitative
    "structural gate" argument**.

verdict: **DEDUCED-NOT-MEASURED (self-declared).** The lab's own successor receipt classifies
the structural gate as a *qualitative argument*, in direct conflict with SIGNAL-REGISTRY.md's
placement of it under "REFUTED (measured, negative, closed)" eleven days later.
note: the mechanism sentence in PILLARS ("structure conserves MOLECULAR FUNCTION not
BIOLOGICAL PROCESS") is a textbook proposition, and the lab's literature synthesis
`BP_SOTA_RESEARCH.md:14` ("The BP separability wall is a recognized STRUCTURAL fact ...
Historic BP Fmax capped 0.00-0.31 vs MF 0.01-0.75", PMC3584852) and `:30` ("3D structure is
credited by CAFA5 but is **in-family for PLMs**") supply exactly that argument from the
LITERATURE, with no PROTEA run behind it. A deduction from a definition is not a measurement.

## PILLARS.md contradicts itself on the same page

- `PILLARS.md:36`  | **F. [absent] Structure** | AFDB / FoldSeek 3Di | **tested**, does not help BP (Pillar 4) |
- `PILLARS.md:95`  | **structure (AFDB/FoldSeek 3Di, real)** | **RED** (residual 0.545; ...) |

Line 36 labels the modality **[absent]** and simultaneously says it was **tested**. The word
"real" in line 95's parenthesis is a tell that an earlier, non-real (proxy) structural arm
existed and that the author was distinguishing them.
note: internal inconsistency is the signal to open the source
(`feedback_internal_inconsistency_is_the_signal_2026_08_31`). The source is gone.

## The echo chain for the structural gate (three citations, one missing source)

1. **2026-07-07** `project_structural_gate_bp_wall_2026_07_07` (memory) -- **the only primary
   source ever named. MISSING from disk; the archive partition `/mnt/protea-archive` is an
   empty unmounted directory.**
2. **2026-07-08/09** `plans/thesis-pillars/PILLARS.md:95` quotes 66.6 / 20.7 / 0.545 and cites
   (1) at line 154. Present in the file's FIRST commit `d93795e`, so the run happened between
   2026-06-30 (RESULTS.md: "strategic fork left for the author") and 2026-07-08. A window of
   **eight days**.
3. **2026-07-11** memory `project_regenerate_headline_from_signal_store_2026_07_11.md:94-95`
   "(structural gate says 9/9 may be unreachable with current evidence). See
   [[project_structural_gate_bp_wall_2026_07_07]]" -- an **ECHO** of (1), no new number.
4. **2026-07-16** `research/regen_headline/BP_WALL_CHARACTERIZATION.md:5` calls (1)
   "the earlier **qualitative** 'structural gate' argument" -- a **downgrade**.
5. **2026-07-27** `plans/SIGNAL-REGISTRY.md:125` files it under
   "REFUTED (**measured**, negative, closed)" -- an **UPGRADE back to measured**, with the
   number, the frame, the population and the receipt all dropped. This is the step the
   registry's own preface warns about: "the arithmetic was sound and the classification was
   not ... The damage was in what the numbers were taken to MEAN."

verdict: **DEDUCED-NOT-MEASURED at the point of citation.** A real FoldSeek run existed
(the tmp scripts prove it), but every downstream document is quoting a source that is gone,
and the one document that reopened it (4) called it qualitative.
frame: **UNKNOWN.** PILLARS' "residual 0.545" and "66.6% / 20.7%" carry no obo/IA version, no
`prop`, no `norm`, no `max_terms`, no `th_step`, and no statement of whether `-known` was
applied. They are not even f_micro_w: "finds the true functional neighbour X% of the time" is
a **retrieval hit-rate**, a different metric from everything else in that table, presented in
the same RED/GREEN column as board-faithful f_micro_w deltas.
population: **UNKNOWN and probably not the nine cells.** "a clean positive control" names no
category, no aspect split beyond MF/BP, no n. Note CCO is absent entirely, so this cannot be
a nine-cell result.
platform gap: MURO for the number; for the capability, an AFDB-fetch + FoldSeek-3Di backend
operation writing donor hits to the database (DESIGN-cross-encoder.md Phase D) was specified
and never built.

---

## SECOND CONTRADICTION: "per-residue PLM embeddings are NOT persisted"

`plans/bp-structural-lever/DESIGN-cross-encoder.md`, section 2 gap 1 (2026-06-30):
  "1. PER-RESIDUE PLM embeddings are NOT persisted (only chunk-pooled). So cross-attention
   must be at EVIDENCE-TOKEN granularity (a small set of tokens per protein), **not residue
   level, unless we recompute residue embeddings (expensive, 12GB GPU)**."

verdict: **CONTRADICTED, and again by staleness, not by error.** True on 2026-06-30; false
from 2026-08-18. The banks are in `/home/xaxi/Thesis2/storage/probe/` (347 GB).

Header-read by hand (no numpy available; magic `\x93NUMPY`, v1.0, `<f4`, shape from the
ASCII header dict). Shape is `(residues, layers, 768)`:

| file | shape | residue rows | layers | bytes | mtime |
|---|---|---|---|---|---|
| `exp220.npy` | (45,073,591, 2, 768) | 45,073,591 | [10, 48] | 276,932,143,232 | 2026-08-20 |
| `pool60k_last.npy` | (22,018,349, 1, 768) | 22,018,349 | last | 67,640,368,256 | 2026-08-18 |
| `lafa_last.npy` | (4,622,985, 1, 768) | 4,622,985 | last | 14,201,810,048 | 2026-08-18 |
| `nk220.npy` | (1,483,599, 2, 768) | 1,483,599 | [10, 48] | 9,115,232,384 | 2026-08-20 |
| `confirmation.npy` | (1,109,436, 1, 768) | 1,109,436 | last | 3,408,187,520 | 2026-08-19 |
| `nk_extra.npy` | (128,969, 1, 768) | 128,969 | [48] | 396,192,896 | 2026-08-19 |

first number (the brief's): "74.4 million per-residue vectors"
second number (derived independently, by summing the six headers):
  **residue rows = 74,436,929** -- the 74.4M figure is the count of residue POSITIONS.
  **stored vectors = 120,994,119**, because two banks hold TWO layers per residue.
  Integrity check on the largest: 45,073,591 x 2 x 768 x 4 bytes = 276,932,143,104, plus a
  128-byte header = 276,932,143,232 = the file size exactly. **Not truncated.**
note: quote 74.4M as RESIDUES, not as vectors; the vector count is 1.63x higher.
frame: `768` dims is Ankh-base (d_model 768), not ankh-large/ESM2-650m. `chunk_size 1024,
chunk_overlap 128` in every provenance file, consistent with the project's no-truncation rule.
`pool60k_4layers.provenance.json` names `embedding_config
0868f1ff-907a-5e4a-9d73-c0f2ed3c2437`, `annotation_release 227` -- **the only probe bank that
declares a config id or a release at all.** The other five declare neither.
population: `exp220` = "corpus proteins with experimental evidence at GOA release 220",
**85,982 proteins**, and it warns in its own provenance that it also contains the 19,467
evaluation queries ("fitting a map for MEASUREMENT must exclude the queries"). `nk220` = "the
NK cell of the 220 to 230 frame, proteins with gained terms", **3,031 proteins**. So the
served population's probe is 3,031 proteins, 4.1% of the 74,436,929-residue corpus by protein
count -- consistent with the standing "NK is ~5% of a window".
date of evidence: 2026-08-18 to 2026-08-20 -> window: **pre-wipe by 7 to 9 days.**
platform gap: the extraction ran in `protea-reranker-lab` (`feat(probe): ...` commits
`0021996`, `f8a04e1`, `ce2fecf`, 2026-08-18), writing .npy to `storage/`. **No PROTEA
operation persists per-residue embeddings**; `sequence_embedding` still holds chunk-pooled
rows only. If this disk goes, 347 GB and about 40 GPU-hours die with it, and nothing in the
job registry can rebuild it.

## TWO probe banks have an index and a provenance file but NO DATA

    lafa_4layers.index.json      326,479 B   provenance: 7,401 proteins, 4,622,985 residues,
                                             layers [0,10,19,48], "supersedes lafa_last.npy"
    pool60k_4layers.index.json 2,535,486 B   provenance: 60,000 proteins, 22,018,349 residues,
                                             layers [0,10,19,48], config 0868f1ff..., rel 227
    -> lafa_4layers.npy and pool60k_4layers.npy DO NOT EXIST.

verdict: **the four-layer banks are LOST.** Only the single-layer/two-layer banks survive.
note: `lafa_4layers.provenance.json` says it **supersedes** `lafa_last.npy`. The superseding
bank is the one that is gone; what remains on disk is the bank the project itself declared
superseded. Any four-layer (0/10/19/48) result computed on 2026-08-18/19 has **no data behind
it any more** -- and the layer axis is exactly where the project's settled findings live
("the layer axis, CLOSED at four depths"). At the two banks' own residue counts this is
(4,622,985 + 22,018,349) x 4 x 768 x 4 B = **327 GB** of extraction that would have to be
redone. Whether they were deleted deliberately to reclaim space or lost is not recorded
anywhere I could find (no note in the probe dir, no lab commit message mentions deleting).

---

## `bp-structural-lever` contains NO structural work. The loop name is a trap.

`results/sparse_classifier/bp_structural_phase0/` = two-tower classifier UNION into the pool.
`results/sparse_classifier/bp_structural_phase1/` = GCN GO-label encoder + bi-encoder scorer.
Neither touches structure. The actual FoldSeek work lives in a *different* directory
(`research/struct_gate/`) under a *different* loop that has no plan file at all.

verdict: **the loop named "structural" measured the classifier; the loop that measured
structure has no plan, no results file, and no preserved code.** Anyone reading
`plans/bp-structural-lever/RESULTS.md` and concluding "structure was tested here" is wrong,
and the SIGNAL-REGISTRY entry sits exactly on that fault line.

## The bp-structural-lever numbers have no JSON receipt either

`grep -rn "0.18971|0.21631|0.19140"` over the whole tree finds them **only as hardcoded
constants inside the finalize scripts**:
  `results/sparse_classifier/bp_structural_phase0/finalize.py:193`
    "FELL -0.027 (0.21631->0.18971): the reranker cannot separate the new clf"
  `results/sparse_classifier/bp_structural_phase1/finalize.py:20`
    PHASE0_UNION = {"lk": 0.44135, "pk": 0.18971}
`find bp_structural_phase0 bp_structural_phase1 -name "*.json"` -> **nothing.**
verdict: **the procedure survives, the output does not.** Phase 1 hardcodes Phase 0's answer
as a python literal rather than reading Phase 0's output, so a re-run of Phase 1 would
reproduce the comparison even if Phase 0 now returned something else.

---

## `plans/prior-knowledge-wall/PLAN.md` (2026-07-17) RETRACTS the whole slice above

Its §0 is titled "**The plan we have been executing is built on a number that does not
exist**". It quotes `bp-structural-lever` verbatim and then:

    "Its own receipt, 25 lines later, says otherwise.
     protea-reranker-lab/results/sparse_classifier/p4_recall_ceiling.json (n=4402, ...)
     | PK-bpo | 0.4695 | 0.5372 |   | LK-bpo | 0.7668 | 0.8227 |   | NK-bpo | 0.6985 | 0.7393 |
     ... **`0.319` appears in no receipt anywhere.**
     Consequence. ... **The wall is RANKING, and it always was.** Every lever the old headline
     commissioned was a generation lever, and every one came back inert ...
     **We were pushing a door that was already open.**"

I reproduced the negative check independently: `grep -rn "0\.319"` over
`agent-farm/plans/`, `protea-reranker-lab/research/`, `thesis/` returns exactly four hits --
`bp-structural-lever/PLAN.md:13`, `bp-structural-lever/RESULTS.md:11`, and the two lines in
`prior-knowledge-wall/PLAN.md` that quote them. **0.319 exists nowhere except in the two
documents that assert it and the one that refutes it.**
verdict: **CONFIRMED (the retraction is right).** 0.319 is DEDUCED-NOT-MEASURED.
note: **`bp-structural-lever/PLAN.md` and `RESULTS.md` were never corrected.** Their last
commit is `2a32d54` (2026-07-10), a week before the retraction. Both still assert
"PK-BP recall ceiling = 0.319 ... HARD generation wall" and "the loss is
candidate-GENERATION-bound". A reader landing in that directory gets the refuted story with
no marker, and the header of the superseding file is the only place the supersession is
recorded ("**Supersedes `plans/bp-structural-lever`**", PLAN.md:3).

## The receipts of the RETRACTION are missing too

`find /` for each named receipt:
  `p4_recall_ceiling.json`   -> NOT FOUND anywhere
  `atlas_atlas.json`         -> NOT FOUND anywhere
  `atlas_per_protein.json`   -> NOT FOUND anywhere
  `atlas_rebuild.py`         -> present (`research/cooc_experiment/atlas_rebuild.py` + 3 worktrees)
  `atlas_controls.py`        -> present
  `dup_evidence_split.py`    -> present
  `anchor_deployed_recipe.py`-> present
verdict: **procedures survive, outputs do not**, exactly as the preservation README states
("the outputs were archived, the procedures were not" -- and the archive is the unmounted
`/mnt/protea-archive`). So the correction 0.6077 -> **0.7519**, capture 35.1% -> **28.3%**,
unreachable 34.6% -> **2.3%** (PKW.3 note, PLAN.md:281) is **regenerable in principle and
unverifiable today**.
frame: PKW.3's own note is unusually complete and should be quoted with its caveat:
"the BP root is an ancestor of everything, so 'reachable' may be too generous and the true
ceiling is likely between the two." That caveat is **dropped** in PLAN.md's headline §0,
which states the 0.75 flatly.
population: 4,402 PK-BPO proteins, one cell of nine.
note: PKW.3 also records a defect nobody has closed --
"NEW BUG: `neighbor_min_distance` is byte-identical to `distance` on every non-NaN row;
misnamed and miscomputed; may affect PROTEA#710's degeneracy check."

---

## THE BIGGEST FINDING IN THIS SLICE: Pillar 4's headline was reversed and PILLARS.md was never updated

Four statements of "what the BP wall is", in order:

| date | document | verdict on the wall |
|---|---|---|
| 2026-06-30 | `bp-structural-lever/RESULTS.md` | "the wall is REPRESENTATION/EVIDENCE, not scoring architecture" |
| **2026-07-09** | **`thesis-pillars/PILLARS.md`:97-99** | **"the wall is evidence-bound, not architecture-bound: no amount of fusion machinery crosses it, only *new evidence* does"** |
| 2026-07-16 | `thesis` commit `6aafc9f` "**locate the BP headroom in ranking, not in the evidence**" | "An earlier account attributed it to the limits of the available evidence. **Measurement does not support that.**" |
| 2026-07-17 | `prior-knowledge-wall/PLAN.md`:31 | "**The wall is RANKING, and it always was.** ... We were pushing a door that was already open." |
| 2026-07-22 | memory `project_bp_frontier_characterized_2026_07_22.md` | "**SEPARABILITY, not reachability/representation** ... the bottleneck is protein->term ASSIGNMENT" |

verdict: **CONTRADICTED.** PILLARS.md's Pillar 4 was refuted by the project's own measurement
within seven days, the THESIS was corrected (commits `6aafc9f` 2026-07-16 and `93ce1dc`
2026-07-17, `chapters/06_evaluation.tex:843` now reads "The headroom is therefore one of
ranking: 0.2131 against a shortlist worth 0.7764"), and **PILLARS.md was not**. Its last
commit is `88ccc61`, 2026-07-09. It is still the document the plan store points to as "the
thesis spine ... four load-bearing claims".
note: the structural-gate row (line 95) sits inside the table that carries the refuted
conclusion. It is the ONE row of that table that also has no receipt. The refutation of the
conclusion did not propagate to the row, and the row was later promoted to REFUTED-measured.

## The exhaustive Pillar-4 consolidation does NOT list structure among the tested channels

`memory/project_bp_frontier_characterized_2026_07_22.md` is the merged 2026-07-18..22
characterisation ("Supersedes/merges the sprawling ... session memories"). It enumerates the
channels tested and rejected under the temporal gate:
  generation: co-occurrence, literature/abstracts, STRING network, classifier, multi-PLM
    diversity, phylogenetic profiling, known-annotation generator
  rescoring: transition/TransFew-mechanism, frequency-partition + IA calibration graft
  architecture: TransFew-style joint model, learned k-WTA GO encoder
  consensus: cross-modality agreement
  submission: selective per-stratum
  plus DeepGO-SE, SSE (three modes), SSE+kWTA generalisation
**Structure / FoldSeek / AFDB appears nowhere in it.** I checked directly:
`grep -rln -iE "foldseek|3di|afdb|alphafold|structural gate"` over the whole memory store
returns five files, and this one is NOT among them (the five are
`project_param_count_executed_not_published_2026_08_18.md` (prostt5's 3Di vocabulary),
`project_regenerate_headline_from_signal_store_2026_07_11.md` (an echo of the missing memory),
`reference_cafa6_kaggle_solutions_2026_06_19.md` (a Kaggle notebook, "NEW" = untried),
`MEMORY.md`, `MEMORY.md.bak`).
verdict: **the structural gate is NOT part of the consolidated Pillar-4 evidence base.** Only
SIGNAL-REGISTRY.md keeps it alive, in a bare list, as "measured".
note: where the consolidation DOES talk about structure it is the LITERATURE claim from
`BP_SOTA_RESEARCH.md`: "BP wall is a recognized STRUCTURAL fact (similar chemistry/MF -> many
processes)". "Structural" there means "a structural feature of the problem", NOT protein 3D
structure. **That homonym is the most likely origin of the whole confusion**, and it is
exactly the shape of defect COLLIDING-A-NUMBER is written to catch.

## The thesis surface says structure was never used, and never cites 66.6/20.7

`thesis/chapters/07_conclusion.tex:231-234` (limitations): "**No structural information.**
... Integrating structure-based embeddings (e.g. from ESM-IF or Foldseek) is a natural
extension **not yet pursued**."
`thesis/defensa.tex:977` (limitations slide): "No structural information (AlphaFold/Foldseek)
integrated"; `:1007` (future work): "Structure-aware embeddings (ESM-IF, Foldseek)".
verdict: the publication surface **agrees with DESIGN-cross-encoder.md and contradicts
SIGNAL-REGISTRY.md**. The 66.6/20.7/0.545 numbers appear in NO thesis file
(`grep -rnE "66\.6|20\.7|0\.545" thesis/` -> nothing). Nothing was overclaimed in print.
note: the thesis last moved 2026-07-17 (`93ce1dc`). It absorbed the ranking correction and
never absorbed the structural gate in either direction.

---

## What the preserved FoldSeek artefact can and cannot tell us

`download.sh` is FoldSeek's generic `databases` script: it branches on a runtime
`${SELECTION}` over Alphafold/UniProt, Alphafold/UniProt50(-minimal), Alphafold/Proteome,
Alphafold/Swiss-Prot, ESMAtlas, PDB, CATH50, etc. **The chosen database is not recorded**, so
we cannot say whether the gate searched full AFDB, AFDB50 or AFDB-Swiss-Prot -- a difference
that changes the answer entirely. The two `structuresearch.sh` files are **byte-identical**
(md5 `d2c4220d11d374fec6f4448ab9837ef4`), i.e. the same generic workflow template written
twice, carrying no run parameters either.
`which foldseek` -> nothing; `find /home/xaxi /mnt -iname "afdb*"` -> nothing; no foldseek
binary, no structure database, no 3Di file anywhere on this disk.
verdict: **FRAME-UNKNOWN and unrecoverable.** Even the target database of the one structural
run this project performed is not knowable from what survives.

---

## Post-wipe status of this whole slice: ORPHANED

Documents in `plans/` modified after the 2026-08-27 registry wipe:
`COLLIDING-A-NUMBER.md` (2026-09-02), `DECLARED-REVISION.txt` (2026-09-02),
`TOPOLOGY.md` (2026-09-02), `DECISION-LOG.md` (2026-08-29), `rungs.yaml` (2026-08-29).
`grep -niE "pillar|bp[- ]wall|prior-knowledge-wall|bp-structural|evidence-bound"` across all
five returns **zero hits**.
verdict: **nothing written since the wipe references either loop, PILLARS.md, or the
structural gate.** Every number in this slice is pre-wipe, and none of it has been
re-measured in the current window. The `storage/probe/` banks (2026-08-18..20) are the only
artefacts in this slice that are recent, and they predate the wipe by a week.

---

## SUMMARY: the four verdicts

1. **The three documents are not simultaneously wrong; they are a staleness chain, and the
   last link upgraded a qualitative argument into a measurement.**
   2026-06-30 "structure entirely absent" (TRUE when written) -> 2026-07-07 a real FoldSeek
   run whose memory is now missing -> 2026-07-08/09 PILLARS quotes 66.6/20.7/0.545 ->
   2026-07-16 the lab calls it "the earlier **qualitative** structural gate argument" ->
   2026-07-27 SIGNAL-REGISTRY files it under "REFUTED (**measured**, negative, closed)".
   **The registry's classification is the defect.**

2. **The 66.6% / 20.7% / 0.545 triple is single-source, receipt-missing, frame-less and
   population-less.** It is a retrieval hit-rate presented in a column of board-faithful
   f_micro_w deltas, covers MF and BP only (no CCO, so not the nine cells), and its named
   evidence file is on an unmounted partition. **Do not cite it. It is the clearest
   deduction-counted-as-measurement in this slice.**

3. **PILLARS.md Pillar 4 ("the wall is evidence-bound, not architecture-bound") was refuted
   by the project's own measurement seven days later, the THESIS was corrected, and
   PILLARS.md never was.** `prior-knowledge-wall/PLAN.md` states it flatly: "The wall is
   RANKING, and it always was ... We were pushing a door that was already open", and shows
   that `bp-structural-lever`'s founding number 0.319 "appears in no receipt anywhere" -- a
   negative check I reproduced independently. `bp-structural-lever/PLAN.md` and `RESULTS.md`
   still carry the refuted claim, unmarked.

4. **"Per-residue embeddings are not persisted" is 7 weeks stale: 74,436,929 residue rows
   (120,994,119 vectors, 347 GB) sit in `storage/probe/`, verified by hand-read .npy headers
   and a byte-exact size check on the 258 GB bank. But the two FOUR-LAYER banks are gone:
   `lafa_4layers` and `pool60k_4layers` have index and provenance files and no data**, and
   the missing one is the bank whose own provenance says it *supersedes* the one that
   survives. That is 327 GB of extraction to redo.

## PLATFORM GAPS this slice exposes (operations that would have to exist)

| capability | status | what is missing |
|---|---|---|
| AFDB fetch + FoldSeek 3Di donor search | **MURO** | specified as DESIGN-cross-encoder Phase D, never built; the one run left only tool temp files, no binary, no database, no analysis code |
| per-residue embedding persistence | **MURO** | 347 GB of .npy written by lab scripts; `sequence_embedding` stores chunk-pooled rows only; no operation, no registry row, no checksum manifest, no re-extraction job |
| pool oracle / recall ceiling | procedure preserved (`atlas_rebuild.py`, `instrument_oracle_greedy.py`), **outputs lost** | no operation; every ceiling number in the thesis (0.7519, 0.7764, 0.322, 27.4%) is regenerable only by running a scratch script against frozen parquets |
| candidate-pool generator merge (`agreed_by_both`) | **MURO** | PKW.2/P0.1: the pool still records two half-views of the same (protein,term); the agreement flag is unrepresentable |
| duplicate-pair semantics in cafa_eval | **never checked** | PKW.2 is still `status: pending`. 13% of rows are handed to the evaluator twice with different scores and nobody has read which one wins |

## WHAT I SEARCHED (so the negatives count)

- `agent-farm/` (all of `plans/`, including `archive/`), `thesis/` (chapters, defensa,
  bibliography, notes), `repositories/` (8 repos), `worktrees/`, `storage/` (all 11 subdirs).
- Patterns: `66\.6`, `20\.7`, `0\.545`, `0\.666`, `0\.207`, `0\.319`, `0\.4695`, `0\.5372`,
  `0\.8227`, `0\.7519`, `0\.18971`, `0\.21631`, `0\.19140`;
  `foldseek|3di|afdb|alphafold|prostt5|structural gate|structur`.
- `find /` for `project_structural_gate_bp_wall_2026_07_07*`, `p4_recall_ceiling.json`,
  `atlas_atlas.json`, `atlas_per_protein.json`, `*foldseek*`, `afdb*`, `*4layer*`, `*struct*`.
- The whole memory store (`/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`, per-file).
- `git log --all` in `agent-farm`, `protea-reranker-lab`, `thesis` for every file in scope,
  plus `git show <commit>:<path>` on all three PILLARS.md revisions.
- `mount`, `/mnt/protea-archive` (empty, unmounted).
- Hand-read six `.npy` headers (no numpy on system python3).

Status: COMPLETE.
