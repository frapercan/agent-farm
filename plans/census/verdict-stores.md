# verdict-stores

Slice: `plans/SIGNAL-REGISTRY.md` and `plans/DECISION-LOG.md` in full.
For each REFUTED entry (~30) and each UNMEASURED entry (~9): date the underlying
evidence, mark it against the 2026-08-27 registry wipe. The registry itself admits
four entries were WRONGLY ARCHIVED (the measurement behind the archival does not
exist) and two RECLASSIFIED as refuted-in-one-mode-untried-in-another. My job is to
find FURTHER entries in that same position that the registry missed.

Auditor: verdict-stores. Started 2026-09-02.
Status: IN PROGRESS (appending as I go).

---

## FINDING 0 (the frame that governs every other finding in this slice)

## The entire SIGNAL-REGISTRY predates the 2026-08-27 registry wipe
verdict: CONFIRMED
first number: title line, `agent-farm/plans/SIGNAL-REGISTRY.md:1` -- "THE SIGNAL
  REGISTRY (receipt-backed, adversarially verified, **2026-07-27**)"
second number (INDEPENDENT): filesystem mtime. `ls -la agent-farm/plans/` gives
  `-rw-rw-r-- 1 xaxi xaxi 24543 Jul 28 17:01 SIGNAL-REGISTRY.md`. The file has
  not been touched since the OS reinstall commit of 2026-07-28 17:01. Every
  other plan file with a LATER mtime (DECISION-LOG 2026-08-29, rungs.yaml
  2026-08-29, COLLIDING-A-NUMBER 2026-09-02, ORCHESTRATION 2026-09-02,
  TOPOLOGY 2026-09-02, DECLARED-REVISION.txt 2026-09-02) WAS touched after.
  So the non-update is selective, not a bulk-checkout artefact.
date of evidence: 2026-07-27 -> window: **pre-wipe** for 100% of rows
frame: the registry's own declared frame is the v227->v230 ground truth, and
  section 7 defect 0 flags that eval set (`6e41eb5b`) as TRUNCATED
  (-18.87% loaded against -1.40% upstream).
population: all 9 cells; every row in sections 1-6.
platform gap: there is NO operation that rebuilds this document from the
  database. It is a hand-written verdict store whose inputs (30 untracked
  `results/` entries, section 7 defect 1) were never registered.
note: **This is the single most important sentence in my slice.** The project
  treats SIGNAL-REGISTRY.md as "what is settled". Its own header says the
  evidence was frozen 2026-07-27, one month before the experiment registry was
  wiped on 2026-08-27. The live database holds 93 evaluation_result rows all
  created 2026-08-27..30. Therefore: **not one number in sections 1, 2, 4 or 5
  is recoverable from the current registry**, and the REFUTED section in
  particular is ~30 closures whose refuting measurements are all pre-wipe. The
  registry was never revised after the wipe. Section 7 defect 0 already says
  "Nothing in sections 1 to 6 is final until v230 is reloaded" -- the wipe makes
  that stronger: nothing in 1-6 is even RE-CHECKABLE.

## The two verdict stores were never revised after the day they were written
verdict: CONFIRMED
first number: SIGNAL-REGISTRY.md self-dates 2026-07-27; DECISION-LOG entries all
  say "Decided 2026-07-28".
second number (INDEPENDENT, git rather than prose): in `/home/xaxi/Thesis2/agent-farm`
  (branch `plans/orchestration`),
  `git log -- plans/SIGNAL-REGISTRY.md` returns **exactly ONE commit**:
  `f0e50a6 2026-07-27 20:40:14 +0200  plan(e2e): canonical clean-run spec +
  receipt-backed signal registry (#233)`.
  `git log -- plans/DECISION-LOG.md` returns **three**, the last
  `0263cfa 2026-07-28 11:39:52 +0200 (#237)`.
  Meanwhile the same branch has 12 later commits (2026-08-12 .. 2026-09-02),
  four of them explicitly campaign plans:
    8b7c9bc 2026-08-20 "make the ladder a claim something can refuse" (#248)
    4c1dc7f 2026-08-20 "what carries the hard band is consensus, not similarity" (#249)
    c441702 2026-08-20 "what a comparison costs..." (#250)
    e5db895 2026-08-23 "why the ladder holds the axis that moves the score most" (#252)
    c76588a 2026-08-23 "rung 2 closes the retrieval axis, and closes it WITHOUT A WINNER" (#253)
date of evidence: registry 2026-07-27, log 2026-07-28 -> window: **pre-wipe**
frame: n/a (provenance finding)
population: all entries of both stores.
platform gap: MURO. There is no operation, and no plausible one, that would
  rebuild a verdict store; it is editorial. The gap that IS closable is the
  reverse direction: nothing forces a rung result to write back into the
  registry, so a rung can close an axis (#253, "closes the retrieval axis")
  without any REFUTED/UNMEASURED row moving.
note: The August campaign ran five rungs and produced at least twenty
  memory-recorded verdicts, and **not one of them touched either verdict store**.
  So the registry's "REFUTED (measured, negative, closed)" list and its
  "UNMEASURED" list are both frozen at a state one month stale, on the far side
  of the wipe. Concretely: #253 says rung 2 CLOSED the retrieval axis, yet
  SIGNAL-REGISTRY section 5 item 1 still lists "ProtST as the PRIMARY RETRIEVAL
  SPACE ... Still the largest unexploited measured lever" as UNMEASURED gap #1.
  A reader of the registry alone would fund an axis the campaign already closed.

## The 2026-08-27 registry wipe is recorded in NEITHER verdict store
verdict: CONFIRMED (negative check, with where I looked stated)
where I looked: `grep -niE "wipe|wiped|truncat|lost|deleted|purge|drop(ped)? the
  (registry|database)|2026-08-2[0-9]|2026-08" agent-farm/plans/SIGNAL-REGISTRY.md
  agent-farm/plans/DECISION-LOG.md` ; also the full text of both files read
  line by line (331 + 466 lines); also `git log --all --oneline` of agent-farm
  for any commit mentioning the wipe.
result: zero hits for the wipe in either store. The newest date appearing
  anywhere in DECISION-LOG.md is 2026-07-28; in SIGNAL-REGISTRY.md, 2026-07-27.
date of evidence: n/a
platform gap: the wipe destroyed 93-rows-worth of successor state and left no
  decision record. **D-00 does not exist.** By the log's own opening rule
  ("A decision that is not written here was not taken, it was drifted into"),
  the wipe was drifted into.
note: this matters for my slice specifically because it means every REFUTED
  closure below is still being read as live, by a project whose own record has
  no note saying its evidence base was destroyed.

## The registry cites exactly ONE receipt file, and it does not exist
verdict: CONFIRMED
first number: `SIGNAL-REGISTRY.md:167-168` (section 5 item 1, the #1 ranked
  UNMEASURED lever): "`protst_zscore` = 0.24849, **+0.0335 vs champion, wins
  9/9**. But RAW ProtST ... = 0.24547, **+0.0305, wins 8/9** ... Receipt:
  `storage/regen_headline/protst_repr/protst_repr_report.json`."
second number (INDEPENDENT): I enumerated every backticked path in the whole
  331-line file. There are exactly **11**, of which only **one**
  (`protst_repr_report.json`) is a result artifact; the rest are source files,
  directories, or other plan documents. So the receipt-to-claim ratio for the
  ~44 rows of sections 4 and 5 is **1 : 44**, and that one is attached to an
  UNMEASURED row, not to any REFUTED row.
  Then: `find /home/xaxi -name 'protst_repr_report.json'` -> **zero hits**.
  `/home/xaxi/Thesis2/storage/regen_headline` does not exist.
  The directory survives only as
  `/home/xaxi/Thesis2/repositories/protea-reranker-lab/research/regen_headline/protst_repr/`,
  which holds three files, all 2026-07-29 01:48: `REPR_RESULT.md`,
  `champ_codes_regen.py`, `protst_repr_screen.py`. **The script survived; the
  report it wrote did not.**
  Whole-tree confirmation: the lab's `research/` holds 314 files -- 224 `.py`,
  73 `.md`, and **0 `.json`**. Not one machine-readable receipt in the tree that
  is supposed to be the preservation path.
date of evidence: measurement pre-2026-07-27 -> window: **pre-wipe**
frame: unstated in the registry. "mean9" and "vs champion 0.2213" are the only
  frame hints; no obo/IA version, no prop, no norm, no max_terms, no th_step,
  and no statement of whether `-known` was applied. FRAME-UNKNOWN.
population: "wins 9/9" and "wins 8/9" implies the 9 cells, count of proteins
  per cell not given anywhere.
platform gap: an operation `screen_retrieval_space` writing an
  `evaluation_result` row per (arm x cell) would make this reborn in the
  database. Today it is a loose script whose stdout was a JSON nobody kept.
note: the lab's own git history says this was DELIBERATE, not an accident.
  Commits `de880a1` / `ea4a3bd` / `63ef76a` (2026-07-27, 2026-07-28) are all
  titled "**preserve: ... procedures**", and `4a81079` (2026-07-28) is titled
  "docs(readme): **withdraw the results**, keep the genealogy that explains
  them." The project chose to preserve procedures and withdraw results. That is
  a defensible choice -- but SIGNAL-REGISTRY.md, written the same 48 hours, was
  NOT updated to say its numbers no longer have receipts. **The registry still
  reads as receipt-backed. Its title literally says "(receipt-backed,
  adversarially verified, 2026-07-27)".**

## The archive partition that section 7 declares "closed and md5-verified" is an empty root-owned directory
verdict: CONFIRMED
first number: `SIGNAL-REGISTRY.md:250-258` -- "Five further gaps were found and
  all are now **closed and md5-verified**: `storage/two_tower_sparse/` (3.0G),
  `~/.secrets/`, `storage/learned_encoders/`, the `mlflow` database, and MinIO
  `rerankers` + `eval_groundtruth`."
second number (INDEPENDENT): filesystem.
  `ls -la /mnt/protea-archive/` -> `total 8`, two entries (`.`, `..`), owner
  `root:root`, mtime `Jul 28 17:09`. `mountpoint /mnt/protea-archive` -> "no es
  un punto de montaje" (not a mountpoint). `df -h` lists exactly two real
  filesystems: `/dev/nvme0n1p2` (915G, /) and `/dev/nvme0n1p1` (1.1G, /boot/efi).
  **There is no archive partition mounted on this machine.**
  `find /home/xaxi /mnt -maxdepth 6 -name two_tower_sparse -o -name learned_encoders`
  -> zero hits. Neither directory exists anywhere reachable.
  MEMORY.md's own index points 144 archived memory files at
  `/mnt/protea-archive/archive/memory-archive-2026-07-27/` -- also unreachable.
date of evidence: preservation claimed 2026-07-27 -> window: pre-wipe
population: the seven LIVE two-tower heads, without which section 1 says "two of
  the seven won cells fall below board" (PK-MFO 0.2038 < board 0.235,
  PK-CCO 0.2252 < board 0.254).
platform gap: MURO for the artifacts themselves. The closable gap is the
  *verification*: no operation reads a backup back out of its destination, which
  is precisely what the registry's own paragraph demands.
note: **The registry contains the exact warning that its own paragraph violates,
  three lines below the claim**: "A claim of PRESERVATION is as dangerous as a
  claim of deletion. 'It is saved' licenses the author to destroy the original.
  Never report an artifact as backed up without reading it back OUT of the
  destination." The paragraph above it reports five artifacts as backed up. I
  read the destination. It is empty. This is defect-1-recurrence: the SAME
  failure the paragraph was written to close ("A first archive pass was declared
  MITIGATED and that claim was WRONG") happened a second time to the second pass.
  I cannot prove the copy never happened -- only that the destination is
  unreachable now and that nothing on this disk verifies it.

---

# THE MAIN RESULT OF THIS SLICE
## Eight REFUTED/CONDITIONAL registry entries have NO surviving primary evidence: their memory files are dangling links into the unreachable archive
verdict: CONFIRMED
first number: SIGNAL-REGISTRY section 4 lists ~28 refuted items as
  "REFUTED (measured, negative, closed)" with no dates and no receipt paths.
second number (INDEPENDENT, derived by link-integrity over a store the registry
  does not cite): I extracted every `[[wikilink]]` in
  `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/` (179 distinct
  targets) and diffed against the 209 `.md` files actually present.
  **120 resolve. 59 dangle.** MEMORY.md says the missing ones were "archived
  rather than deleted" at `/mnt/protea-archive/archive/memory-archive-2026-07-27/`
  (98 files) and `../memory-archive-pre-2026-06-15/` (46 files) = 144. That path
  is an empty root-owned directory on an unmounted device (see previous finding).
  Of the 59 dangling targets, these map one-to-one onto registry verdicts:

  | registry row | section | dangling memory file that was its evidence | who still cites it |
  |---|---|---|---|
  | budgeted ontology profile | 4 REFUTED | `project_budgeted_ontology_profile_refuted_2026_07_27` | `project_sparse_contrastive_jepa_direction_2026_07_25.md:97` |
  | structural gate (AFDB/FoldSeek) | 4 REFUTED | `project_structural_gate_bp_wall_2026_07_07` | 3 files incl. `project_lofo_9cell_master_ablation_2026_07_07.md:34` |
  | GO-text BioBERT label basis | 4 REFUTED | `project_gotext_label_basis_bp_lever_2026_07_08` | `project_text_evidence_scorer_2026_07_08.md:42`, `project_layer_ablation_2026_07_08.md:67` |
  | L10-std | 4 REFUTED | `project_l10std_loses_in_production_2026_07_12` | `project_protst_path_a_productionization_2026_07_12.md:127` |
  | ProtEx exemplar verification | 4 REFUTED | `project_protex_verification_GO_2026_07_21` | `project_bp_sota_research_2026_07_21.md:46` |
  | multi-PLM POOL-AUGMENTATION union | 4 REFUTED | `project_recall_ceiling_multiplm_2026_07_20` + `multi_plm_report_full_grid` | `project_bp_sota_research_2026_07_21.md:55,89` |
  | literature/abstract text as a channel | 4 REFUTED | `project_cafa6_winners_literature_lever_2026_06_30` | `project_text_evidence_scorer_2026_07_08.md:42` ("literature RED") |
  | Learned k-WTA GO encoder | 4 RECLASSIFIED | `project_kwta_go_encoder_2026_07_20` | `project_bp_sota_research_2026_07_21.md:89` |
  | Classifier-alone as PK scorer | 2 CONDITIONAL | `project_classifier_alone_beats_reranker_on_pk_2026_07_17` | `project_sparse_classifier_2026_06_28.md:24` |

date of evidence: all 2026-06-30 .. 2026-07-27 -> window: **pre-wipe**, and now
  also **pre-reinstall-lost** at the primary-source level.
frame: FRAME-UNKNOWN for all nine. No surviving document states obo/IA version,
  prop, norm, max_terms, th_step or `-known` for any of them.
population: unstated in every case.
platform gap: MURO for the archived text. But note the shape: each of these was
  a refutation that lived ONLY in an assistant-memory note, never in a database
  row and never in a tracked receipt. An `evaluation_result` row per refuted arm
  would have survived the reinstall AND been re-derivable; a memory note is
  neither.
note: **This is the class the registry itself warned about and then missed.**
  Section 3 says: "This section used to contain four more entries. All four were
  WRONGLY ARCHIVED and have been moved to section 5, because **the measurement
  behind their archival does not exist**." The registry found four in section 3.
  I find **nine more in sections 2 and 4**, by the identical test, and the
  registry never applied that test to section 4 at all -- section 4 is a bare
  comma-separated list of names with no per-item scrutiny. The registry audited
  the small section and left the big one unaudited.

## "donor-recency weighting" is a REFUTED entry with ZERO trace anywhere
verdict: NOT_FOUND (and this is the strongest single instance of the class above)
first number: `SIGNAL-REGISTRY.md:129` -- listed inside section 4,
  "REFUTED (measured, negative, closed)".
second number (INDEPENDENT): exhaustive search.
  `grep -rn "donor-recency" agent-farm/plans repositories/protea-reranker-lab
   /home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory` returns
  **exactly one line, and it is SIGNAL-REGISTRY.md:129 itself.**
  `grep -rli "recency" repositories/protea-reranker-lab` -> **zero files**
  (whole repo, not just research/). No `donor_recency` identifier anywhere.
where I looked (so the negative counts): the full plans store; the whole
  reranker-lab repo including 224 research scripts and 73 writeups; the 210-file
  memory store; both spellings and the bare stem "recency".
date of evidence: none exists -> window: unknowable
frame: none.
population: none.
platform gap: MURO in its current form. If it is worth anything it has to be
  re-run; there is nothing to re-read.
note: **A name in a refuted list is not a refutation.** This entry cannot be
  distinguished from a lever someone thought of, wrote into the list, and never
  ran. It occupies a REFUTED slot, which means the project will not fund it
  again, on the strength of a single occurrence of its own name. By the
  registry's own section-3 standard ("the measurement behind their archival does
  not exist") it is WRONGLY ARCHIVED, and the registry missed it.

---

## "phylogenetic profiling" is a NULL at its own selected operating point, filed as REFUTED -- the identical defect the registry caught for STRING and missed here
verdict: DEDUCED-NOT-MEASURED (more precisely: measured, but below the project's
  own declared resolution, and closed as if it were resolved)
first number: `SIGNAL-REGISTRY.md:127` lists "phylogenetic profiling" flatly
  under "## 4. REFUTED (measured, negative, closed)".
second number (INDEPENDENT, from the primary writeup the registry does not cite):
  `repositories/protea-reranker-lab/research/regen_headline/PHYLO_PROFILE.md`,
  "Step 2 -- does it convert?" table:
      cell     anchor    B top5      B top10    B top25   Rnd top5
      LK-BPO   0.31323   -0.00089    -0.00274   -0.00652  -0.00071
      PK-BPO   0.14351   -0.00106    -0.00280   -0.00958  -0.00106
  The registry's OWN declared noise floor is **0.0034**
  (`SIGNAL-REGISTRY.md:233`, and again at :104 and :183).
  **-0.00089 is 3.8x INSIDE that floor. -0.00106 is 3.2x inside it.**
  top10 (-0.00274 / -0.00280) is also inside. Only top25/top50 clear it, and
  those are not the operating points a gate would select.
  And the writeup states the reason no interval exists, in its own words:
  **"No positive -> no bootstrap CI needed."**
date of evidence: undated in the file; bracketed by OrthoDB v12.2 (Nov 2024) and
  the 2026-07-27 preserve commit; the sibling CROSS_MODALITY writeup says the
  ODB12 download "was still running", placing phylo AFTER the consensus run.
  -> window: **pre-wipe**, ~2026-07.
frame: STATED, and it is the good one: `prop=fill norm=cafa no_orphans toi`,
  cafa_eval under the PROTEA venv, **PK adds `-known`**, one variable = candidate
  set only, anchor reproduction precondition PASSED (LK 0.31323 / PK 0.14351
  exact). This is the best-framed refutation I found in the whole section.
population: **LK-BPO and PK-BPO ONLY -- two of nine cells.** And within those,
  OrthoDB keying mapped only **783 / 4,922 targets = 15.9%**, vertebrate-biased:
  yeast S288C **1/508**, Arabidopsis **0/436**, S. pombe **0/302**,
  Dictyostelium **0/26**. So the refutation covers 15.9% of two of nine cells.
platform gap: an operation `screen_candidate_generator(channel, k, cell)` writing
  one `evaluation_result` per (channel x k x cell) with its bootstrap CI. The
  harness exists as `phylo_step2.py`; nothing registers its output.
note: **The registry applied exactly this test to STRING and not to phylo.**
  `SIGNAL-REGISTRY.md:148-149` reclassifies STRING PPI out of REFUTED on the
  grounds "five of six deltas **inside the 0.0034 floor, no CIs**". Phylo's
  selected-arm deltas are SMALLER than STRING's and it also has no CIs, and it
  stayed in REFUTED. By the registry's own rule phylo belongs in section 5 as
  NULL-not-refuted. Two further untried modes the registry does not record:
  (a) the writeup itself names the remedy -- "**This is a keying mismatch, not a
  biology limit; a UniProt idmapping bridge would be the follow-up**" -- and the
  bridge was never built, so the cells where phylo-profiling is classically
  strongest (compact fungal/plant genomes) were never measured at all;
  (b) never tested as a reranker FEATURE over the existing pool, the same
  no-fill-tax form the registry demanded for STRING one line earlier.

## "cross-modality consensus" was run at THREE modalities, and the registry records it as if the axis were closed
verdict: CONFIRMED as a measurement, CONTRADICTED as a closure
first number: `SIGNAL-REGISTRY.md:126` lists "cross-modality consensus" under
  REFUTED, and `:158-159` generalises it: "Cross-modality consensus compounds
  precision ~23x and still tops out at 2.5-3%."
second number (INDEPENDENT, the writeup's own header):
  `research/regen_headline/CROSS_MODALITY_CONSENSUS.md` says
  "**Phylogenetic profiling was pending** (no proposals; the ODB12 download was
  still running under `storage/phylo_profile/`), so this ran with **3 orthogonal
  modalities**: sequence-kNN (the 6-PLM family as ONE channel), the STRING
  network, and the full-BP classifier."
  So the registry's two REFUTED entries "cross-modality consensus" and
  "phylogenetic profiling" are disjoint experiments, and **the 4-modality
  consensus that would join them was never run.** That is not a nitpick: the
  mechanism the writeup confirms is *independent-error compounding*, under which
  a channel with near-zero standalone precision can still raise an intersection.
  Phylo is exactly such a channel (LK top5 precision 0.0000).
date of evidence: undated; predates PHYLO_PROFILE.md -> window: **pre-wipe**
frame: STATED and strong. `prop=fill`, PK drops `-known`(sec.1)/adds it (sec.3),
  full board frame Sep_2025->Mar_2026, blind temporal gate fit on
  Sep->Nov and applied frozen to Nov->Mar, matched-volume uniform control,
  paired protein bootstrap B=2000, anchor reproduction exact to 5 dp.
population: **LK-BPO 495 proteins / PK-BPO 4,349 proteins. Two of nine cells.**
  NK is absent entirely, and NK is the SERVED population.
platform gap: same as phylo. Also: the FIT/APPLY temporal gate here is the
  single most reusable piece of machinery in the whole refuted set and it exists
  only as `storage/consensus/phase1_temporal_gate.py`, which is gone.
note: the distribution-before-summary point, and it is IN the writeup and NOT in
  the registry: the FIT window read **+0.057 LK / +0.197 PK**, and the blind
  APPLY window read **-0.027 / -0.065**. A sign flip of that size is the single
  best argument in this project for the temporal gate, and the registry's
  one-line summary of this entry ("tops out at 2.5-3%") loses it completely.
  Also lost: the consensus arm BEATS the matched-volume uniform control by
  +0.072 / +0.052, i.e. the selection works and only the tax kills it.

---

## The registry's #1 UNMEASURED lever was REFUTED on 2026-08-23 and the registry still recommends it
verdict: CONTRADICTED
first number: `SIGNAL-REGISTRY.md:164-168`, section 5 item **1**, top of the
  ranked-by-expected-value gap list: "**ProtST as the PRIMARY RETRIEVAL SPACE.**
  ARM CORRECTED: `protst_zscore` = **0.24849, +0.0335 vs champion, wins 9/9**.
  ... **Still the largest unexploited measured lever.**" Reinforced at
  `:291-295` (section 8 THE CLEAN TRAJECTORY, step 2): "Re-baseline the retrieval
  space. Raw ProtST is +0.0305 (8/9) and the z-scored arm +0.0335 (9/9)."
second number (INDEPENDENT, and it is a decomposition rather than a re-run):
  `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/project_protst_advantage_is_text_leakage_2026_08_23.md`
  splits the NK cell on whether UniProt carries a FUNCTION comment at all:
      rival           described (2,468)   undescribed (547)
      ankh-large      +0.0095 *           **-0.0003**
      prot_t5         +0.0098 *           **-0.0120**
      esm2_t33_650M   +0.0209 *           +0.0008
      ProstT5         +0.0166 *           +0.0088
      esmc_600m       +0.0359 *           +0.0084
      esm2_t6_8M      +0.0391 *           +0.0064
      rung2-dense     +0.0088 *           +0.0046
      rung2-pooled    +0.0060 *           +0.0041
  ("*" = paired interval excludes zero.) **9 of 9 separate among the described,
  0 of 9 among the undescribed, and it INVERTS against the two strongest rivals.**
  Mechanism: ProtST is pretrained on ProtDescribe, which pairs sequences with
  Swiss-Prot FUNCTION prose. All 3,031 NK targets are reviewed Swiss-Prot; 81.9%
  carry a `function_cc`. The temporal rule does not catch it because NK means no
  EXPERIMENTAL evidence at t0, not nothing written down.
  Downstream: the twilight backbone spread falls **0.0842 -> 0.0625** when ProtST
  is removed, and is unchanged in all three other homology bands.
date of evidence: registry claim <= 2026-07-13 (`REPR_RESULT.md` header
  "2026-07-13"); refutation **2026-08-23** -> both **pre-wipe**, but the
  refutation is 41 days NEWER than the store that still recommends it.
frame: the two are in DIFFERENT frames and neither row says so.
  Registry row: kNN-only mean9 f_micro_w, query=7401, ref=15000, cosine top-30
  GO-transfer vote, single seed 42, 9 cells.
  Refutation: reachability at a 25-term budget, NK cell only, paired intervals.
  So this is not a like-for-like reversal -- it is a mechanism finding that
  disqualifies the recommendation without re-scoring the metric. The registry
  row can only be repaired by re-running the screen with the undescribed split.
population: registry row 9 cells, 7,401 queries. Refutation: NK only,
  3,031 targets, of which the clean subgroup is **547 undescribed** (the memory
  index elsewhere says 550; the file's own table says 547 -- a 3-protein
  internal inconsistency worth noting but not load-bearing).
platform gap: an `evaluate_retrieval_space(config, cohort)` operation with a
  `cohort` that can be "NK-undescribed" would have made this one row of a table
  instead of two documents that never met. Today the screen is a loose script
  and the refutation is a memory note; **nothing joins them.**
note: **This is the most expensive stale row in the registry.** Section 8 is
  the project's own execution plan and its step 2 is "re-baseline the retrieval
  space" on ProtST. Anyone following the registry today would rebuild the
  substrate on a model whose lead is text leakage. The refutation says in its own
  words: "**no thesis sentence may recommend ProtST on these numbers**". The
  registry recommends it twice.

## The registry carries digits that exist nowhere else, from a receipt that is gone
verdict: CONFIRMED
first number: registry `:165-167` gives `0.24849` and `0.24547`, and a per-cell
  detail "losing nk-MFO by ~-0.0009".
second number (INDEPENDENT): `grep -rn "0.24849" repositories/protea-reranker-lab`
  -> **zero hits.** The surviving writeup `protst_repr/REPR_RESULT.md` rounds to
  `0.2485` / `0.2455` in its leaderboard and states raw = `0.24547` once in prose;
  it gives **no nk-MFO delta at all**. The five-decimal z-score figure and the
  nk-MFO delta existed only in `protst_repr_report.json`, which does not exist
  (searched all of /home/xaxi).
date of evidence: 2026-07-13 -> window: pre-wipe
frame: kNN-only mean9, single seed 42 (see below).
population: query 7,401 / ref 15,000 / pool 100,000, 100% ProtST coverage.
platform gap: same as above.
note: this is the general shape of the whole registry -- **it is now the most
  precise surviving carrier of numbers whose receipts are destroyed.** That makes
  it uncollidable by construction: there is no second object to put next to it.

## The registry's load-bearing NEW refutation (-0.0043) is smaller than the seed wobble its own receipt declares
verdict: DEDUCED-NOT-MEASURED / below-resolution
first number: `SIGNAL-REGISTRY.md:133-137`: "**NEW ENTRY the draft was missing,
  and it is load-bearing:** a **learned k-WTA head on ProtST LOSES to raw ProtST**
  (**-0.0043 at d4096**, -0.0074 at d2048, negative on 8 of 9 cells). **The sparse
  head that helps raw Ankh does NOT transfer.** This argues against section 8 item
  1 and **against the sparse-contrastive direction generally**, and it was
  invisible in the draft."
second number (INDEPENDENT, from the receipt's own caveat section):
  `protst_repr/REPR_RESULT.md`, "## Caveats": "**Single seed 42 (screen).** The
  k-WTA-loses and ProtST-beats-champion signals are large (**0.007 to 0.034**)
  relative to **typical seed wobble (~0.01)**, so the direction is decision-grade."
  Collide the two: the receipt justifies its own decision-grade claim over a
  band that **starts at 0.007**, and **-0.0043 is not in that band.** It is
  **2.3x SMALLER than the ~0.01 seed wobble the same paragraph declares**, and
  1.26x the registry's 0.0034 noise floor. Only the d2048 arm (-0.0074) reaches
  the receipt's own stated band, and even it sits below the wobble.
  Single seed, so no interval exists for either arm.
date of evidence: 2026-07-13 -> window: **pre-wipe**
frame: kNN-only mean9 f_micro_w. **The registry does not carry this frame on the
  section-4 entry**, only on the section-1 row for the Ankh k-WTA head. A reader
  meeting the -0.0043 in section 4 has no way to know it is a kNN retrieval screen
  rather than a pipeline number.
population: 9 cells, 7,401 queries, one seed.
platform gap: `train_and_screen_encoder_head(base, d, k, seed)` writing one row
  per seed. Multi-seed is the entire fix and it is cheap; the head-train is the
  only cost and the receipt says it already trained two.
note: two separate over-reaches stack here.
  (1) **Resolution**: a -0.0043 single-seed delta is used to close an axis.
  (2) **Scope**: the receipt's own conclusion is narrow and operational --
  "Gate to expensive export: **PASS on raw ProtST**, no representation change
  required" -- a decision about which vector feeds one producer. The registry
  promotes it to an argument "**against the sparse-contrastive direction
  generally**", which is the project's own lead research direction
  (`project_sparse_contrastive_jepa_direction_2026_07_25.md`). The receipt
  measured one head, on one base, at one seed, at the kNN level; the registry
  reads it as a verdict on a research programme.
  Also dropped between receipt and registry: the receipt's other caveat,
  "kNN-only mean9 is a CANDIDATE screen number, NOT the sealed 0.4063 reranked
  headline", and the fact that d4096 is **positive on lk-bpo (+0.0059)**.

---

# THE HIGHEST-YIELD FINDING: two more "refuted in one mode, untried in another" entries, already identified as such by the project's own plan, and left in REFUTED
## `GO-text BioBERT label basis` and `GCN label encoder` are the registry's missed reclassifications
verdict: CONTRADICTED (both belong in section 5, by the registry's own stated rule)
first number: `SIGNAL-REGISTRY.md:130-131`, inside
  "## 4. REFUTED (**measured, negative, closed**)":
  "... GO-text BioBERT label basis, M3 IEA pretraining, SVD label embedding,
  **GCN label encoder**, binary objective, within-protein rank features, class
  weighting."
second number (INDEPENDENT -- and it is the project's own planning document,
  written BEFORE the registry and never consulted by it):
  `agent-farm/plans/prior-knowledge-wall/PLAN.md:133-144` sets out TransFew's
  three components against our three tests, in a table:

  | their component | our equivalent test | result |
  |---|---|---|
  | GCN over the GO hierarchy | DAG proximity as a feature | **AUC 0.5501** |
  | annotation transfer between terms | term co-occurrence | **+0.0021** |
  | BioBert over GO text | GO-text BioBERT label basis | **+0.012 on LK-BPO** |

  and then draws the conclusion in the plan's own words, emphasis original:
  "He learns them **jointly with the sequence**; we measured the ingredients one
  at a time, cold. **Our negatives do not refute the signal, they refute the
  bolt-on.**"
  The same table and the same sentence appear a second time at
  `prior-knowledge-wall/PLAN.md:325-334` inside a task acceptance block, so it is
  a gate condition, not an aside.

  **The registry rescued ONE of these three and left the other two.** Section 5
  item 6 correctly moves "Co-occurrence candidate expansion" out of REFUTED
  ("its one board number is **+0.0021 POSITIVE**"). That is the same +0.0021
  in row 2 of the table above. The registry therefore read this evidence, acted
  on row 2, and did not act on rows 1 and 3.

date of evidence: TransFew mechanism "verified 2026-07-17"; the three component
  tests are 2026-06-30..2026-07-08 -> window: **pre-wipe**.
frame: **row 1 is not even in the metric.** AUC 0.5501. Rows 2 and 3 are
  f_micro_w deltas; neither states obo/IA version, prop, norm, max_terms, th_step
  or `-known`. FRAME-UNKNOWN for all three.
population: row 3 is **LK-BPO only** ("PK/NK ~0", `thesis-pillars/PILLARS.md:94`)
  -- one of nine cells. Rows 1 and 2 unstated.
platform gap: a `screen_label_basis(basis, cell)` operation emitting f_micro_w
  per cell would have made rows 1 and 3 comparable to row 2 and to each other.
  All three were bolt-on feature ablations run outside the platform.

note: three separate defects stack in these two rows, and each alone is enough
  to move them.

  **(a) The section title is false for the GO-text row. +0.012 is POSITIVE.**
  Section 4 is titled "REFUTED (measured, **negative**, closed)". The GO-text
  label basis measured **+0.012 on LK-BPO, seed-averaged**, which is **3.5x the
  registry's own 0.0034 noise floor**. `thesis-pillars/PILLARS.md:94` grades it
  "**modest**", not negative, and PILLARS:150-153 makes it load-bearing for the
  thesis argument: "On the *label* side, term-text sees BP where DAG ancestry
  does not (+0.012 on LK-BPO). On the *protein* side, function-description
  alignment sees BP where sequence and structure do not (+0.072 on LK-BPO)...
  **That is the mechanism behind the wall, and behind its first crack.**"
  So a result the thesis uses as the mechanism of its fourth pillar is filed in
  the registry as a refutation.

  **(b) The bar is applied inconsistently, and the registry knows this failure
  mode.** Section 2 keeps "`pminmax` on **LK-BPO only**: 0.307 -> 0.370 (+0.063
  ... net +0.022)" as CONDITIONAL. The GO-text label basis is also LK-BPO-only,
  also positive, and is REFUTED. The registry flags precisely this inconsistency
  for a different row -- section 5 item 4: "The 'inside noise' bar was also
  applied inconsistently (`anc2vec_neighbor` sits inside the same band and was
  kept)" -- and then commits it again here.

  **(c) The GCN row is refuted on a statistic the registry BANS, measured on a
  DIFFERENT OBJECT.** `SIGNAL-REGISTRY.md:55-56` states the companion rule:
  "**never triage levers by AUC, which ordered arms OPPOSITE to f_micro_w at
  least five times.**" The only evidence against the GCN label encoder is
  **AUC 0.5501**. And 0.5501 was not measured on a GCN: the plan's own column
  says the tested object was "**DAG proximity as a feature**", a hand-built
  scalar. So the registry closes "GCN label encoder" using (i) a statistic it
  forbids, (ii) on a proxy that is not a GCN, (iii) with no f_micro_w anywhere.
  This is the definition-groups-two-things trap in COLLIDING-A-NUMBER section 3:
  "a hand-built DAG-proximity scalar" and "a learned graph encoder over the DAG"
  are both truthfully "the GO hierarchy as a signal", and they are not the same
  object.

## `M3 IEA pretraining` and `SVD label embedding` are PLAN ITEMS that were never run
verdict: NOT_FOUND (never measured; occupying REFUTED slots)
first number: `SIGNAL-REGISTRY.md:130` lists both under
  "REFUTED (measured, negative, closed)".
second number (INDEPENDENT): the only document in the project that defines "M3"
  is `agent-farm/plans/archive/lafa-number-one/NEURAL-HEAD.md`, and it defines it
  as a **future milestone**, not a result:
  line 32: "- **M3 backbone + scale.** ESMC-600M / ESM2-650M; train on the full
  annotated proteome (500k+) with **IEA weak-label pretraining**, strict <=t0
  cutoff."
  and it reappears in the plan's forward list, line 65-66:
  "## NEXT (prioritised by the remaining gap) ... 2. **PK + rare terms =
  frequency-grouped heads + scale.** TransFew recipe ... train on the full
  annotated proteome (500k) with **IEA weak-label pretraining** (strict <=t0).
  3. **M2 label semantics** (BioBERT GO-def + **GCN over the GO-DAG**) for
  rare/zero-shot terms."
  **The only milestone with an OUTCOME section in that file is M0.**
  ("## M0 OUTCOME (2026-06-14) ... NK 0.324 / LK 0.301 / PK 0.134 / mean 0.253".)
  M1, M2, M3, M4 have no outcome sections. And the file's own banner closes it:
  "> **[SUPERSEDED / DONE 2026-06-15]** ... This plan describes the offline push
  toward it and is **kept for history only**." Superseded one day after the
  2026-06-14 progress note, with the NEXT list unstarted.
where I looked (so the negative counts): `grep -rn` for "M3", "IEA pretrain",
  "SVD label", "GCN label" across `agent-farm/plans/` (including `archive/`),
  the whole `protea-reranker-lab` repo (224 research scripts, 73 writeups), and
  the 210-file memory store. "SVD label embedding" appears **nowhere** except
  SIGNAL-REGISTRY.md:130 -- every other `SVD` hit in the memory store is the
  **two-tower's TruncatedSVD256 basis**, which is a protein-side sparse code, a
  different object entirely (`project_sparse_classifier_2026_06_28.md:45,137`).
date of evidence: none for either -> window: unknowable
frame: none.
population: none.
platform gap: MURO as recorded. Both would have to be run from scratch.
note: **This is the "donor-recency" shape again, twice.** A milestone that was
  planned, superseded before execution, and then written into a REFUTED list, is
  the purest instance in this audit of a deduction from a plan being read later
  as a measurement. And the SVD row is worse than absent: the nearest real object
  with that name (the two-tower SVD basis) is recorded as a **preservation
  failure, not a negative result** -- "the deployed two-tower's SVD basis was
  never persisted -- **a durable thesis point independent of the negative
  f_micro_w**" (`project_bp_frontier_characterized_2026_07_22.md:117`). Someone
  compressing that note into a registry line could produce "SVD label embedding:
  refuted" out of "the SVD basis was lost". I cannot prove that is what happened,
  but no other source for the row exists.

---

## The LOFO grid -- the source of most section-1 verdicts -- is ONE SEED WITH NO INTERVALS, and one of its zeros was retracted 2026-08-26
verdict: CONTRADICTED (the zero) + DEDUCED-NOT-MEASURED (the indispensability)
first number: `SIGNAL-REGISTRY.md:69`, section 1 INDISPENSABLE SIGNALS:
  "**M2 anc2vec hybrid classifier** ... LOFO NK **+0.180 / +0.198 / +0.245**,
  LK **+0.134 / +0.104 / +0.158**, PK **exactly 0.000**. **One of only two rows
  here with a genuine counterfactual**." And `:72` for `association`:
  "LOFO PK +0.024 / +0.017 / +0.016 ... NK **exactly 0.000** (leakage-clean by
  construction)."
second number (INDEPENDENT, and it is an addendum the registry never saw):
  `memory/project_lofo_9cell_master_ablation_2026_07_07.md`, section
  "**THE INSTRUMENT MEASURES THE COMBINER, NOT THE FLOW, 2026-08-26**":
  "**A zero here does not mean the family is useless in that cell. It means the
  combiner does not use it there**, and those are different findings with
  opposite consequences. The classifier family measures exactly zero in all three
  prior-knowledge cells. **Read as uselessness for months.** Measured alone, that
  same family **beats the full re-ranker in prior-knowledge BPO, held out, in
  nine of ten disjoint protein folds**."
  and, last line of the file: "**Also of record: one seed, no intervals.**"
date of evidence: LOFO 2026-07-07; retraction **2026-08-26** -> both pre-wipe,
  retraction 30 days newer than the registry.
frame: STATED in the memory and NOT carried into the registry: "Clean 227->230
  frame; NK/LK=baseline pool, **PK=percut+knn_present**; **LK-BPO pmin-pmax**;
  **PK excludes PK_known**; train negatives **neg_frac=0.15**, full eval."
  Note `PK=percut+knn_present` is the 44%-row-removing denominator of section 6.
  Note also that the LOFO ran under `objective=binary` (see next finding).
population: 9 cells. Baselines NK 0.648/0.331/0.481, LK 0.559/0.354/0.467,
  PK 0.230/0.141/0.273. Protein counts not stated anywhere.
platform gap: the receipt is named
  `protea-reranker-lab/results/sparse_classifier/lofo_9cell/{run.py,result.json}`
  -- and `results/` is the untracked tree section 7 defect 1 calls unpreserved.
  `find` confirms neither file is on this disk. An operation
  `ablate_feature_family(family, cell, seed)` writing one row per (family, cell,
  seed) is the whole fix, and it is the one that would have made "seeds" cheap.
note: two things a reader must not miss.
  **(a) The registry calls this "one of only two rows here with a genuine
  counterfactual", and the counterfactual is single-seed with no interval.**
  Section 6 lists "Paired bootstrap CIs + declared noise floor (0.0034)" as an
  indispensable mechanism and calls it "**what separates a result from a
  story**". The row it uses to anchor section 1 has neither.
  **(b) The distinction the addendum draws is the one the registry needs and does
  not have: a STRUCTURAL zero versus a MEASURED zero.** Association on NK is zero
  by arithmetic (a no-knowledge protein holds no terms to associate against) and
  survives any change of instrument. The classifier on PK is zero because the
  combiner discards its proposals, and it reverses when measured alone.
  The registry writes both as "exactly 0.000" in the same table, in the same
  typeface, one line apart.

## The LOFO ran under `objective=binary`, which the registry itself lists as REFUTED
verdict: CONFIRMED (internal contradiction, and the registry sees only 1/8th of it)
first number: `SIGNAL-REGISTRY.md:131` lists "binary objective" under REFUTED.
second number (INDEPENDENT, the registry's own section 5 item 4):
  ":181-183" -- the homology block "was dropped **one family at a time across 8
  CORRELATED families, at one seed, with no CIs, under `objective=binary`**
  **which section 4 itself lists as REFUTED**."
  So the registry HAS made this observation. It applies it to **one row** (the
  KNN homology block) and reclassifies that row to UNMEASURED.
  But `objective=binary` is a property of the LOFO RUN, not of one family. Every
  LOFO delta in the registry comes from the same run: the M2 classifier row, the
  `association` row, the `anc2vec_query` row, the `lineage` demotion (section 1
  correction 1), and `anc2vec_neighbor` in section 2. **Five more rows sit on the
  same refuted objective, at the same one seed, with the same absent CIs, and
  none is flagged.**
date of evidence: 2026-07-07 -> window: pre-wipe
frame: as above.
population: all 9 cells.
platform gap: same operation. The point is that a per-run parameter recorded
  once (objective, seed, neg_frac) would propagate to every derived row
  automatically; in a prose registry it has to be remembered row by row, and it
  was remembered once out of six.
note: this is `feedback_shared_offset_means_shared_machinery_2026_08_20` in the
  memory store, stated forward: rows that share machinery share its defects.
  The registry's own reasoning for demoting the homology block applies verbatim
  to five rows it leaves in section 1 as INDISPENSABLE.

---

## `annotation-space RAG` is the OTHER arm of the experiment the registry reclassified -- same table, same harness, and it is the STRONGER arm
verdict: CONTRADICTED (belongs in section 5 by the registry's own argument, and
  more strongly than the arm the registry actually rescued)
first number: `SIGNAL-REGISTRY.md:125` lists "annotation-space RAG" under
  REFUTED; and `:143-147` reclassifies its table-mate:
  "**Learned k-WTA GO encoder**: refuted as a candidate-ADDER only; **untested as
  a retrieval space and as a reranker feature**. **A harness in which the
  project's own indispensable generator scores -0.018 to -0.035 and a
  random-score control scores -0.063 is measuring the `prop=fill` tax of pool
  augmentation, not GO-representation quality.**"
second number (INDEPENDENT -- the table those two figures came from):
  `research/regen_headline/KWTA_GO_ENCODER.md`, "f_micro_w, TRUE board frame":

  | cell (anchor) | arm | delta top100 | delta top200 | delta vs random control (top100) |
  |---|---|---|---|---|
  | PK_BP (0.11033) | LEARNED k-WTA | -0.05876 | -0.07237 | **+0.00407** |
  | | FIXEDSCORE control (random) | -0.06283 | -0.07631 | 0 (ref) |
  | | two-tower (fixed) | -0.01804 | -0.03466 | +0.04479 |
  | | **dense annotation-RAG** | **-0.03190** | **-0.05352** | **+0.03093** |
  | LK_BP (0.29896) | LEARNED k-WTA | -0.21548 | -0.24555 | **+0.01147** |
  | | FIXEDSCORE control (random) | -0.22695 | -0.25397 | 0 (ref) |
  | | two-tower (fixed) | -0.09826 | -0.16205 | +0.12869 |
  | | **dense annotation-RAG** | **-0.13000** | **-0.18959** | **+0.09695** |

  The registry's "-0.018 to -0.035" is the two-tower row and its "-0.063" is the
  FIXEDSCORE row, so the registry read this exact table. **The dense
  annotation-RAG is the fourth row of the same table, under the same anchor, the
  same `prop=fill` tax, the same quantile calibration, the same cafa_eval venv.**
  If the harness cannot decide GO-representation quality, it cannot decide
  annotation-RAG quality either. The registry rescued one arm and closed another
  on identical evidence.
  **And the inversion is the point**: the arm the registry RESCUED separates from
  the random control by only **+0.00407 (PK) / +0.01147 (LK)** -- 1.2x and 3.4x
  the declared 0.0034 floor. The arm it LEFT REFUTED separates by **+0.03093 (PK)
  / +0.09695 (LK)** -- **9.1x and 28.5x the floor**. On the harness's own
  discriminating statistic, annotation-space RAG carries roughly eight times more
  usable ordering signal than the entry the registry judged too poorly measured
  to close. The registry rescued the weaker arm.
date of evidence: undated writeup; frozen data is v227 = 2025-09-04, evaluation
  is v230 novel terms -> window: **pre-wipe**, ~2026-07.
frame: STATED and good: "TRUE board frame (prop=fill, norm=cafa, no_orphans,
  toi; **PK `-known`** per evaluation.nf:279), extras quantile-calibrated onto the
  pool score distribution identically per arm; cafa_eval under the PROTEA venv.
  **Noise floor 0.0034.**" The registry carries none of this on either row.
population: **PK_BP and LK_BP only -- two of nine cells.** NK is absent, and NK
  is the served population. The registry's flat list implies all nine.
platform gap: `screen_generation_channel(channel, k, cell)` with the random-score
  control as a first-class arm. The controls here are the best in the corpus and
  they exist only inside one loose script.
note: also untried in the STRING sense and the registry does not say so:
  annotation-space RAG was measured **only as a candidate ADDER** (extras on top
  of the pool, paying the fill tax). It was never tested as a reranker FEATURE
  over the existing pool, which is exactly the cheap no-fill-tax form the
  registry demands for STRING four lines earlier (`:150-151`).
  Second thing not to miss: the registry's own reason for rescuing the k-WTA arm
  is that the harness measures the tax rather than the thing. **If that is true,
  every row of this table is uninterpretable, including the -0.018 two-tower row
  the registry cites in section 1 as evidence of indispensability.** The registry
  uses the same table as (a) proof a harness is invalid and (b) proof a signal is
  indispensable, in two different sections.

## Every storage path any of these refutations names is gone; the frozen v227 corpus most of all
verdict: CONFIRMED
first number: paths named in the surviving writeups:
  `storage/regen_headline/KWTA_GO_ENCODER.json`, `storage/kwta_go_encoder/`,
  `storage/cooc_experiment/soft_cafaeval_objective.{py,json,log}`,
  `storage/cooc_experiment/soft_cafaeval_predictions.npz`,
  `storage/consensus/{phase0_precision_curve,phase1_temporal_gate}.{py,json}`,
  `storage/consensus/clf_prop_topk.pkl`, `storage/phylo_profile/`,
  `storage/text_scorer/*_result.json`, `storage/regen_headline/phylo_*.json`,
  `storage/two_tower_sparse/`, `storage/learned_encoders/`,
  `storage/feature_necessity/WRITEUP.md`,
  and the corpus everything is frozen on:
  **`storage/protea-frozen-v227-2025-09-04/reference_annotations.parquet`**.
second number (INDEPENDENT): `ls -d` on each. **Not one exists.**
  `/home/xaxi/Thesis2/storage/` currently holds eleven directories and none of
  them is any of the above: `calibration-study, coordination, encoder,
  encoder-study, logs, ontology-drift, probe, rescue, scorecard, throughput,
  worktree_salvage`. Their mtimes run 2026-07-30 .. 2026-09-02, i.e. the entire
  369 GB is **post-reinstall campaign material**, not the pre-reinstall receipts.
date of evidence: destination checked 2026-09-02 -> window: pre-reinstall-lost
platform gap: this is the whole argument of CAMPAIGN.md section 0bis, confirmed
  by measurement: "no artifact without a registered operation that produces it".
  Every path above is an unregistered artifact and every one is gone.
note: the frozen v227 reference corpus is the common denominator. Phylo, the
  consensus study, the k-WTA GO encoder and the soft-objective study all declare
  it as their sole label source. Its absence means **none of these refutations
  can be re-scored, only re-run from a rebuilt corpus** -- and a rebuilt v227 is
  not the same object, because `project_goa_not_monotone_two_contractions` says
  the corpus contracts ~30% twice.

## `soft IA-weighted-F objective (-0.023)` and `fuse_listwise (-0.0355)`: well measured, wrong scope
verdict: CONFIRMED as measurements, FRAME-UNKNOWN as registry rows
first number: `SIGNAL-REGISTRY.md:127-128` -- "soft IA-weighted-F objective
  (-0.023), fuse_listwise (-0.0355 at equal input)".
second number (INDEPENDENT, the receipt):
  `research/regen_headline/SOFT_CAFAEVAL_OBJECTIVE_LOSES.md` gives the two frames
  the registry collapses into one:
      frame                                    A lambdarank   B soft-F   B-A
      legacy (lab, `max_terms=500`)            0.22193        0.11570    -0.10623
      vectorised (board, `max_terms=None`)     0.13852        0.11570    -0.02282
  So **-0.023 is the board-frame number and -0.106 is the lab-frame number for the
  same arms**, a 4.7x difference produced entirely by `max_terms`. The writeup
  explains it: the soft-F emits sigmoid (all positive) so the legacy parser has
  nothing to drop, while lambdarank submits negatives that legacy drops as a free
  prefilter. **This is the frame problem in miniature and the registry quotes the
  number without the frame.**
  `FUSING_THE_VECTORS_FAILS.md:22` independently carries the fuse_listwise arm:
  "| **B** | neural listwise, the same 72 scalars | 0.18415 | **-0.03554** |"
  (the registry rounds to -0.0355; consistent).
date of evidence: undated -> window: pre-wipe
frame: legacy vs vectorised as above; `prop`/`norm`/`-known` not stated in the
  soft-objective writeup at all, unlike the k-WTA and phylo writeups.
population: **PK-BPO only.** "same pk-bpo pool rows (16.5M train / 131k pos)".
  One cell of nine, and the registry's flat list does not say so.
platform gap: `train_reranker(objective=...)` as a registered operation, with the
  scoring frame recorded on the evaluation row rather than in prose.
note: this pair is among the BEST work in the refuted set -- precondition passed
  and stated ("arm A legacy = 0.22193, within 0.009 of the deployed 0.21269"),
  one variable, both frames, a fairness check that gives the losing arm the
  winner's advantage, and an explicit self-limiting caveat ("This shows THIS
  soft-F implementation ... loses, not that no ontological objective can win").
  **The registry keeps the number and discards all four of those.** What survives
  into the store is "-0.023", which cannot be collided by anyone.

---

## `binary objective`, `within-protein rank features`, `class weighting`: genuinely measured, one cell, no intervals -- and the registry that refutes the binary objective also ran its keystone ablation under it
verdict: CONFIRMED as measurements; the registry's use of them is over-scoped
first number: `SIGNAL-REGISTRY.md:131` lists all three under REFUTED.
second number (INDEPENDENT, the primary source, which is in the memory store and
  not cited by the registry):
  `memory/project_rankpct_artifact_invalidates_baseline_2026_07_16.md`,
  "## The corrected picture (**all raw scores, one harness**)":
      deployed recipe (pooled-aspect lambdarank, the real booster)  0.2131
      our faithful reimplementation of it (arm P)                   0.2177
      per-cell split (PK-BPO only)                                  0.2017  (negative)
      binary objective, per-cell                                    0.1518  (negative)
      within-protein rank features                                  0.1465  (negative)
      class weighting                                               0.1441  (negative)
      drop classifier-only candidates          flat, coverage 0.978 -> 0.846
      oracle (perfect order AND count)                              0.6077
  So the deltas are **-0.061, -0.067, -0.069** against 0.2131 -- 18x to 20x the
  0.0034 floor. These three refutations are real and large. They are also
  **PK-BPO only, one arm each, single seed, no intervals**, and the registry's
  flat list says none of that.
date of evidence: **2026-07-16** -> window: **pre-wipe**
frame: raw reranker scores (the clean side of the rankpct split), same booster,
  same rows, same gt, same cafaeval, one harness. `prop`/`norm`/`-known` not
  stated in the memory. The contaminated twin of this table is the 0.1255
  baseline the registry archives in section 3.
population: PK-BPO only. One of nine.
platform gap: `train_reranker(objective=..., features=..., weighting=...)` as a
  registered operation with a run row per arm. All eight rows above came from
  loose scripts (`isolate_percell_split.py`, `isolate_pool_lever.py`) whose
  receipts (`storage/cooc_experiment/*.json`) no longer exist.
note: **the internal contradiction the registry does not resolve.** Section 4
  refutes `binary objective`. Section 5 item 4 records that the 9-cell LOFO --
  the source of the section-1 indispensability verdicts -- was run **"under
  `objective=binary` which section 4 itself lists as REFUTED"**. Both statements
  stand in the same document and the registry reconciles them for exactly one
  row. Either the objective is refuted, in which case six section-1 rows inherit
  the defect, or it is only refuted on PK-BPO at one seed, in which case the
  section-4 entry is over-scoped. It cannot be both as written.
  Second note: the same memory records the sign flip that produced the entry.
  Before the rankpct fix, the published claim was "**binary objective worth
  +0.026**", shipped to three surfaces (`insights.rst` #735, thesis
  `06_evaluation.tex` #74, `book.ts`). After: **-0.061**. That is the single
  cleanest example in this project of a number reversing under a preprocessing
  change, and the registry keeps only the post-flip verdict, not the flip.

## THE FRAME PROBLEM, made countable: PK-BPO has at least THIRTEEN distinct published values in this project
verdict: CONFIRMED
first number: `SIGNAL-REGISTRY.md:27-28`: "The same reranker reads PK-BPO
  **0.3433** in one row and **0.117** in another, and both are correct in their
  own frame."
second number (INDEPENDENT): I collected every PK-BPO figure I met while dating
  the refuted set. The registry names two. There are at least thirteen.

  | PK-BPO value | what it is | source |
  |---|---|---|
  | 0.1255 | rankpct-normalised, MANUFACTURED by a monotone map | `memory/project_rankpct_artifact_..._2026_07_16.md` |
  | 0.11666 | deployed, `-known` OMITTED | `SIGNAL-REGISTRY.md:215` |
  | 0.11033 | anchor A in the k-WTA GO encoder screen | `research/regen_headline/KWTA_GO_ENCODER.md` |
  | 0.1441 / 0.1465 / 0.1518 | class weighting / within-protein rank / binary objective arms | rankpct memory |
  | 0.14351 | deployed percutgraft anchor, true board frame | `PHYLO_PROFILE.md`, `CROSS_MODALITY_CONSENSUS.md` |
  | 0.141 | LOFO baseline | `memory/project_lofo_9cell_master_ablation_2026_07_07.md` |
  | 0.16244 | same anchor on the Nov->Mar APPLY sub-window | `CROSS_MODALITY_CONSENSUS.md` |
  | 0.2017 | per-cell split arm | rankpct memory |
  | 0.20132 | deployed WITH `-known` | `SIGNAL-REGISTRY.md:215` |
  | 0.2131 | deployed, RAW scores, no rankpct | rankpct memory |
  | 0.2177 | faithful reimplementation, arm P | rankpct memory |
  | 0.2181 | the public board's PK-BPO | rankpct memory |
  | 0.3433 | arm A of the 9-cell protst A/B, `max_terms=500`, no `-known` | `PATH_A_PROTST_EXECUTION.md` |
  | 0.4030 | `fmax_cafaeval`, v226-v230, K=5, esmc_300m, 34 feats, 3 seeds | `repositories/protea-reranker-lab/champions.md` |
  | 0.09343 / 0.09132 / 0.08135 / 0.06445 | kNN-only retrieval screen arms | `protst_repr/REPR_RESULT.md` |

  **Range 0.064 to 0.403, a factor of 6.3, all for one cell.** Four separate
  levers move it: the score transform (rankpct, -0.088), `-known` (-0.0847),
  `max_terms` (500 vs None, worth 4.7x on the soft-objective comparison), and
  the metric itself (f_micro_w vs fmax).
date of evidence: 2026-05-18 .. 2026-07-16 -> window: **all pre-wipe**
frame: this IS the frame finding.
population: PK-BPO in every row, but the protein counts differ (percut+knn_present
  removes 44% of PK rows; the champions table is a different eval window entirely).
platform gap: an `evaluation_result` row that carries its frame -- obo/IA
  version, prop, norm, max_terms, th_step, `-known`, metric, eval window, pool
  definition -- makes this table a `GROUP BY` instead of an archaeology exercise.
  **This is the single most valuable operation the platform could gain**, and
  SIGNAL-REGISTRY section 10 already lists it as outstanding work
  ("Attach a receipt path AND a frame descriptor to every row in sections 1 to
  6"). It was never done, and now most of the receipts are gone, so it can no
  longer be done from records -- only by re-running.
note: the registry says "both are correct in their own frame" and then, in
  sections 4 and 5, prints deltas with no frame at all. A delta inherits the
  frame problem from both of its terms.

---

## `ProtEx exemplar verification` is NULL-with-a-real-mechanism, not negative, and the untried mode is named in its own receipt
verdict: CONTRADICTED (belongs in section 5, and the receipt writes the experiment)
first number: `SIGNAL-REGISTRY.md:124` lists "ProtEx exemplar verification"
  under "REFUTED (**measured, negative, closed**)".
second number (INDEPENDENT -- and this one is a model of how to do it, an
  adversarial re-verification with fresh code and a different seed):
  `research/regen_headline/PROTEX_VERIFY_INDEPENDENT.md`, "## 2. Independent
  deltas vs BOTH anchors":
      PK-BPO (n=616,223)  A_raw=0.11009  D_deployed=0.14351
        blend  0.14626   vs raw +0.0362 [0.032, 0.040]   vs deployed **+0.0028 [-0.004, +0.010]**
      LK-BPO (n=52,011)   A_raw=0.28974  D_deployed=0.31323
        blend  0.32029   vs raw +0.0306 [0.016, 0.047]   vs deployed **+0.0071 [-0.006, +0.021]**
  **Both deltas against the real deployed anchor are POSITIVE with CI spanning
  zero.** That is a NULL. It is not "negative", which is what section 4's title
  asserts of every name in it. The original claim (`PROTEX_VERIFICATION.md`:
  "+0.0344 (LK-BPO) and +0.0344 (PK-BPO) ... CI strictly above zero,
  frac-positive 1.0") was refuted, correctly, as an **anchor error**: the "+0.034
  is real ONLY against the raw, unfiltered reranker pool (0.11009 / 0.28974),
  which ProtEx mislabelled 'deployed'."
date of evidence: `project_bp_sota_research_2026_07_21.md:46` dates the anchor
  error -> **2026-07-21**, window: **pre-wipe**
frame: STATED and excellent: "lab obo+IA, prop=fill norm=cafa no_orphans toi,
  **PK `-known`**", paired bootstrap CIs, a random-order control (-0.076 / -0.212),
  a full leak audit (self-as-exemplar 0, near-dup cosine cap 0.99951, temporal
  gate train<=v225 / early-stop v225-v227 / blind v227-v230), and three harnesses
  agreeing on the deployed anchor. Fresh code, seed 1 not 0.
population: **PK-BPO (616,223 candidate rows) and LK-BPO (52,011). Two of nine.**
platform gap: the anchor reconciliation is the reusable object here --
  `reconcile_anchor(submission, frame)` returning which of the candidate anchors
  a number was measured against. Its absence is what produced the error.
note: **the untried mode is written into the receipt in one sentence and the
  registry closed the entry anyway.** Section 4 of the verification:
  "Blend vs raw pool: newly-crosses candidates **3.5x more often true** than the
  ones it drops (PK 10.9% vs 3.1%; LK 27.2% vs 8.3%). **This is a genuine
  precision-improving reorder, not an artifact.** But it only lifts the raw pool
  UP TO the level the deployed prefilter+percutgraft already reaches ...
  **The verifier is a SUBSTITUTE for the deployed prefilter, not an addition on
  top of it.**"
  So the measured question was "does ProtEx ADD to the prefilter" (answer: null).
  The unmeasured question the receipt hands you is "does ProtEx REPLACE the
  prefilter, and is it cheaper or better at it". Nobody ran it. This is
  bit-for-bit the shape the registry created its RECLASSIFIED category for.
  Consistency check on the bar: ProtEx is +0.0071 on LK-BPO and REFUTED; the
  GO-text label basis is +0.012 on LK-BPO and REFUTED; `pminmax` is +0.063 (net
  +0.022) on LK-BPO and CONDITIONAL. Three LK-BPO-only positives, two closures
  and one keep, with no stated threshold separating them.

## The registry's flagship frame example (`0.117`) is a field its own source marks SUPERSEDED
verdict: CONFIRMED
first number: `SIGNAL-REGISTRY.md:27-28`, in the section headed
  "## THE FRAME PROBLEM (read before any number below)":
  "The same reranker reads PK-BPO **0.3433** in one row and **0.117** in another,
  and **both are correct in their own frame**."
second number (INDEPENDENT): `PROTEX_VERIFY_INDEPENDENT.md` section 1 enumerates
  the candidates explicitly: 'The "three anchors": **0.110/0.290 = raw pool**;
  **0.117/0.348 = a *stale* `board` field stored inside `result_9cell.json`
  (superseded)**; **0.140/0.313 = the real deployed reconstruction** (three
  harnesses agree).'
  So `0.117` is not a frame. It is a stale cached field that the project's own
  adversarial verification identified and superseded, and it is half of the pair
  the registry uses to teach the frame problem. The number that would have made
  the point correctly is 0.14351 (with `-known`, true board frame) against
  0.3433 (`max_terms=500`, no `-known`) -- both live, both defensible.
date of evidence: 2026-07-21 verification vs 2026-07-27 registry -> the registry
  is SIX DAYS NEWER than the document that supersedes the number it cites.
frame: n/a.
population: n/a.
platform gap: the same one. A stale cached field inside a result JSON is exactly
  what a registered `evaluation_result` row with a frame descriptor prevents.
note: this is small in magnitude and large in what it says: **the paragraph
  warning readers that a number is meaningless without its frame illustrates
  itself with a number that has no frame.** It does not weaken the warning; it
  shows how hard the warning is to obey without machinery.

---

## `SSE` -- the FIRST name in the REFUTED list -- is (Mode A) a fill-tax measurement that tracks its own random control, and (Mode B) six TIES
verdict: CONTRADICTED (Mode A belongs in section 5 by the registry's own rule;
  Mode B is null, not negative)
first number: `SIGNAL-REGISTRY.md:121` -- section 4 opens with
  "SSE (Mode A generator and Mode B feature, despite excellent intrinsics)".
second number (INDEPENDENT, the receipt, which says it itself):
  `research/regen_headline/SSE_FULL.md`, Mode A, "true-frame f_micro_w vs
  reproduced anchor":
      cell     anchor    best deltaB      rand-order   matched-vol
      PK-mfo   0.24831   -0.0748 (top5)   **-0.07494**  -0.15546
      PK-bpo   0.14351   -0.01029 (top5)  **-0.01036**  -0.07303
      PK-cco   0.2677    -0.02519 (top5)  **-0.02533**  -0.16621
      LK-mfo   0.42243   -0.02156 (top5)  -0.03734      -0.22436
      LK-bpo   0.31323   +0.00309 (top25) -0.01043      -0.15546
      LK-cco   0.37042   +0.02279 (top5)  -0.03397      -0.17519
  **In all three PK cells SSE equals its own random-order control to four
  decimals** (-0.0748 vs -0.07494; -0.01029 vs -0.01036; -0.02519 vs -0.02533).
  The writeup states the consequence in its own italics: "SSE generation is WORSE
  than the two-tower and **tracks its own random-order control (no ranking
  signal; the loss is volume**, matched-vol far worse)".
  That sentence IS the registry's reclassification criterion, written by the
  author of the experiment. `SIGNAL-REGISTRY.md:145-147` reclassifies the k-WTA
  GO encoder because "a harness in which ... a random-score control scores -0.063
  is **measuring the `prop=fill` tax of pool augmentation**, not GO-representation
  quality." The identical condition holds here, is stated here first, and section
  4 still opens with SSE.

  Mode B is not negative either. All six rows:
      pk-mfo  +0.00321  CI[-0.01124, 0.01761]   NO LEVER (tie)
      pk-bpo  -0.00124  CI[-0.00539, 0.00296]   NO LEVER (tie)
      pk-cco  +0.00803  CI[-0.00405, 0.01947]   NO LEVER (tie)
      lk-mfo  +0.09998  CI[0.0612, 0.13843]     SUSPECT-MEMORIZATION
      lk-bpo  +0.00582  CI[-0.01204, 0.02369]   NO LEVER (tie)
      lk-cco  +0.10269  CI[0.07267, 0.1356]     SUSPECT-MEMORIZATION
  **Four ties with CIs crossing zero and two large positives disqualified by a
  shuffled-feature control.** Not one measured negative. Section 4 is titled
  "REFUTED (measured, **negative**, closed)".
date of evidence: undated writeup; frozen corpus v225, blind eval v227-v230
  -> window: **pre-wipe**, ~2026-07
frame: STATED: true-frame f_micro_w, temporal gate train<=v225 / blind v227-v230,
  eval proteins held out of ALL SSE training, `-known` on PK and **explicitly NOT
  on LK** (which is why the two LK positives are called memorization).
population: **PK x 3 and LK x 3. The three NK cells were never measured** in
  either mode, and NK is the served population. The registry's flat name gives
  no hint that a third of the grid is missing.
platform gap: the shuffled-feature and random-order controls here are the best in
  the corpus, and they live in one loose script. A registered
  `screen_feature(feature, control=shuffled|random|matched_volume)` operation
  would make a control a required column instead of an author's virtue.
note: one more asymmetry the registry drops, from the same receipt:
  "SSE is fully reproducible from frozen inputs (seeds fixed, models + meta saved
  under `storage/sse_full/models/`). **The deployed two-tower's SVD/projection
  basis was never persisted, so its candidate generation is not re-derivable;
  SSE as a candidate source is auditable where the two-tower is not**, independent
  of the head-to-head f_micro_w outcome."
  So the REFUTED arm is reproducible and the INDISPENSABLE arm (section 1,
  "the strongest indispensability case in this section") is not. Neither store
  records that. (`storage/sse_full/` does not exist either.)

---

# MASTER INVENTORY: every section-4 REFUTED entry, dated and marked against 2026-08-27

Reading key for "status": **MISSED** = belongs in the registry's own
"wrongly archived" or "refuted in one mode, untried in another" categories and
the registry did not put it there. **SOUND** = a real measured negative, with the
scope caveat noted. **NO TRACE** = no evidence of a measurement anywhere.

Every single row is **pre-wipe**. Not one refutation in section 4 has evidence
dated on or after 2026-08-27, so none is checkable against the live registry.

| # | REFUTED entry | evidence located | date | cells measured | status |
|---|---|---|---|---|---|
| 1 | SSE Mode A (generator) | `research/regen_headline/SSE_FULL.md` | ~2026-07 | PK x3, LK x3 (**no NK**) | **MISSED** -- ties its own random-order control to 4 dp in all 3 PK cells; the receipt says "the loss is volume" |
| 2 | SSE Mode B (feature) | same | ~2026-07 | PK x3, LK x3 | **MISSED** -- four TIES with CIs crossing zero, two positives killed by a shuffled control. No negative anywhere |
| 3 | DeepGO-SE entailment | `DEEPGOSE_{RESCORE,FAITHFUL,FULLCORPUS}.md` | ~2026-07 | LK-BPO, PK-BPO | SOUND (anchor reproduced exactly 0.31323 / 0.14351); 2 of 9 cells |
| 4 | multi-PLM POOL-AUGMENTATION union | `MULTIPLM_POOL_FMICROW.md` | ~2026-07 | LK-BPO, PK-BPO | SOUND -- -0.02681 CI[-0.0415,-0.0124], -0.06141 CI[-0.0739,-0.0494]; 2 of 9 cells |
| 5 | TransFew freq-partitioned IA calibration | `TRANSFEW_CALIB_GRAFT.md` | **2026-07-21** | LK-BPO, PK-BPO | SOUND for LK (-0.01519); PK **-0.00221 is INSIDE the 0.0034 floor** though its CI excludes zero |
| 6 | ProtEx exemplar verification | `PROTEX_VERIFY_INDEPENDENT.md` | **2026-07-21** | LK-BPO, PK-BPO | **MISSED** -- +0.0028 / +0.0071 with CI spanning zero = NULL, and the receipt names the untried replace-the-prefilter mode |
| 7 | phylogenetic profiling | `PHYLO_PROFILE.md` | ~2026-07 | LK-BPO, PK-BPO, **15.9% coverage** | **MISSED** -- selected arm -0.00089/-0.00106 is 3-4x INSIDE the floor, no CIs by explicit choice; remedy named and untried |
| 8 | structural gate (AFDB/FoldSeek) | memory `project_structural_gate_bp_wall_2026_07_07` **DANGLING** | 2026-07-07 | unknown | evidence LOST; secondary trace only (`PILLARS.md:95`: residual 0.545, MF 66.6% vs BP 20.7%) |
| 9 | annotation-space RAG | `KWTA_GO_ENCODER.md` (4th row of the reclassified table) | ~2026-07 | PK-BPO, LK-BPO | **MISSED** -- same harness as the entry the registry rescued, and separates from the random control 8x more strongly |
| 10 | literature/abstract text as a channel | memory `project_cafa6_winners_literature_lever_2026_06_30` **DANGLING** + `ABSTRACT_SIGNAL_PHASE0.md`, `TEXT_AS_GENERATOR_IS_SCALE_CONFOUNDED.md` | 2026-06-30 | unknown | primary LOST; the surviving file name itself says "SCALE CONFOUNDED" |
| 11 | cross-modality consensus | `CROSS_MODALITY_CONSENSUS.md` | ~2026-07 | LK-BPO (495 prot), PK-BPO (4,349) | SOUND, and the best temporal-gate design in the corpus. But run at **3 modalities**; the 4-modality version was never run |
| 12 | soft IA-weighted-F objective (-0.023) | `SOFT_CAFAEVAL_OBJECTIVE_LOSES.md` | ~2026-07 | **PK-BPO only** | SOUND; the registry drops the frame that makes -0.023 differ from -0.106 |
| 13 | fuse_listwise (-0.0355) | `FUSING_THE_VECTORS_FAILS.md:22` (0.18415, -0.03554) | ~2026-07 | PK-BPO only | SOUND |
| 14 | L10-std | `L10STD_STEP3_RESULTS.md` (**2026-07-12**) + memory `project_l10std_loses_in_production_2026_07_12` DANGLING | 2026-07-12 | mean9 kNN-retrieval | SOUND, harness reproduces 0.21501 vs pinned 0.21500; **and independently re-confirmed 2026-08-23** (`project_july_layer_win_is_the_transform`) -- the only registry row August strengthens |
| 15 | attention pooling | `scripts/run_attn_pool_learned.py`; result only as prose in `PILLARS`/`representation-science` | ~2026-06 | unknown | receipt-less; "attention pooling never won" is an assertion with no located number |
| 16 | multivector / ColBERT | `src/protea_reranker_lab/compaction_quality.py`, `scripts/run_compaction_quality.py`; memory `project_compaction_study_2026_06_25` **DANGLING** | 2026-06-25 | unknown | evidence LOST; code survives, result does not |
| 17 | naive SDR + Tanimoto | `research/fullgo_models/SDR-STATE.md` (2026-06-23); memory `project_sdr_a_result_2026_06_22` **DANGLING** | 2026-06-22 | unknown | primary LOST; the surviving trace says the negative was "partly explained as normalization confound" (`project_layer_ablation_2026_07_08.md:67`) -- i.e. **already partly retracted and still filed as refuted** |
| 18 | budgeted ontology profile | memory `project_budgeted_ontology_profile_refuted_2026_07_27` **DANGLING** | 2026-07-27 | unknown | evidence LOST; the one surviving sentence says the refutation was itself an artifact ("the Resnik/IC proxy was an artifact") |
| 19 | donor-recency weighting | **NOTHING** | -- | -- | **NO TRACE** -- one occurrence in the whole project, and it is this line |
| 20 | soft Pmin/Pmax DAG propagation | lab commit `ee9a9b7 2026-06-24 feat(hierarchy): CondProbMod conditional modelling + soft Pmin/Pmax propagation (R2.1)` | 2026-06-24 | unknown | code merged; **no result document located** |
| 21 | GO-text BioBERT label basis | `prior-knowledge-wall/PLAN.md:139`, `thesis-pillars/PILLARS.md:94`; memory DANGLING | 2026-07-08 | **LK-BPO only** | **MISSED** -- the number is **+0.012, POSITIVE**, and the thesis uses it as the mechanism of pillar 4 |
| 22 | M3 IEA pretraining | `archive/lafa-number-one/NEURAL-HEAD.md:32,65` -- a **future milestone** | never run | -- | **NO TRACE / plan item** |
| 23 | SVD label embedding | **NOTHING** under that name | -- | -- | **NO TRACE** -- nearest object is the two-tower SVD basis, a preservation failure not a result |
| 24 | GCN label encoder | `prior-knowledge-wall/PLAN.md:139` -- **AUC 0.5501**, on "DAG proximity as a feature" | ~2026-07 | unknown | **MISSED** -- refuted on a statistic the registry BANS (`:55-56`), measured on an object that is not a GCN |
| 25 | binary objective | memory `project_rankpct_artifact_..._2026_07_16` | **2026-07-16** | PK-BPO only | SOUND (0.1518 vs 0.2131), but the registry's own keystone LOFO was run under it |
| 26 | within-protein rank features | same | 2026-07-16 | PK-BPO only | SOUND (0.1465 vs 0.2131), single arm, no interval |
| 27 | class weighting | same | 2026-07-16 | PK-BPO only | SOUND (0.1441 vs 0.2131), single arm, no interval |
| 28 | learned k-WTA head on ProtST (the NEW entry) | `protst_repr/REPR_RESULT.md` | **2026-07-13** | 9 cells, **single seed 42** | **MISSED** -- -0.0043 is 2.3x below the seed wobble its own receipt declares, and the receipt's conclusion is narrow while the registry's is a research programme |

Tally: **28 entries. 9 MISSED, 3 NO TRACE, 6 with their primary evidence
DANGLING into the unreachable archive, 10 SOUND-with-scope-caveats.**
The registry found 4 wrongly-archived and 2 reclassifiable. **By the registry's
own two tests I find 9 more**, plus 3 that were never measured at all.

## Scope, stated once because it applies to nearly every row above
Of the 28, **not one was measured on all nine cells except #28 (single seed).**
The modal population is **{LK-BPO, PK-BPO}** -- two cells of nine, and neither of
them is NK. `memory/project_serving_population_is_the_nk_cell_2026_08_19.md`
establishes that NK is the served population, about 5% of a window. So the
refuted set is, almost in its entirety, **a set of verdicts about cells the
system does not serve**, presented as a flat list of closed questions.

---

# MASTER INVENTORY: the section-5 UNMEASURED list, dated and marked

The registry calls this list "the real gaps, **ranked by expected value**". The
ranking is not sound: the top two items are measured against **different
baselines** (see the finding below the table), and at least three items have been
answered since, in August, without the registry moving.

| # | UNMEASURED entry | evidence located | date | status against 2026-08-27 |
|---|---|---|---|---|
| 1 | ProtST as PRIMARY RETRIEVAL SPACE (+0.0335 / +0.0305) | `protst_repr/REPR_RESULT.md`; the cited JSON is GONE | 2026-07-13 | **ANSWERED AND NEGATIVE 2026-08-23** -- the lead is text leakage, 9/9 described vs 0/9 undescribed. Registry unchanged. Still ranked #1 and still step 2 of the clean trajectory |
| 2 | Triple-combine `protst+protrek+d8979601` = 0.2650, +0.044 | `research/text_scorer/WRITEUP.md:84,88` | 2026-07-08 | pre-wipe. **Baseline mismatch with #1** (see below). Also inherits #1's leakage: ProtST is one of the three, and ProTrek alone (0.2154) does not beat the champion |
| 3 | `emb_pca_query_0..15` NEVER EVALUATED (100% NaN) | `FEATURE_SCHEMA_API_AUDIT.md` (2026-07-10, 2026-07-16) | 2026-07-16 | pre-wipe, still open. This is the registry's own best catch: "gain exactly 0.000" was the arithmetic of a column LightGBM cannot split on |
| 4 | KNN homology block CONDITIONAL-UNTESTED | derived from the LOFO export | 2026-07-07 | pre-wipe, still open |
| 5 | `interpro_*` as a feature, never configured | `FEATURE_SCHEMA_API_AUDIT.md` | 2026-07-16 | pre-wipe, still open. "One unset env variable away from running" |
| 6 | Co-occurrence candidate expansion (+0.0021, rankpct on both arms) | `fuse_and_score.py:121`; rankpct memory says "**NOT yet re-checked**" | 2026-07-16 | pre-wipe, still open |
| 7 | 8-PLM ensemble, NONE-MEASURED | `project_8plm_benchmark_design_2026_06_24`, `project_canonical_8plm_embedding_configs` | 2026-06-24 | **PARTLY ANSWERED in August**: the backbone matrix ran (`project_architecture_null_survives_stratification_2026_08_20`, 8 backbones incl. ProtST, full NK cell, 3,031 queries, bank of 85,982 real donors). Different frame (reachability, not f_micro_w), so not a clean closure -- but the registry's "NONE-MEASURED" is stale |
| 8 | `length_query` partially observed, NaN iff `knn_present==0` | LOFO export + newer export | 2026-07 | pre-wipe, still open |
| 9 | Categoricals never enrolled + out-of-contract `aspect_code` | `FEATURE_SCHEMA_API_AUDIT.md` | 2026-07-16 | pre-wipe, still open |
| 10 | `protst_text` declared-but-unenrolled | contracts v1.5.0, `PROTST_STEP7_SPEC.md` | 2026-07-12 | pre-wipe; and see #1 -- enrolling it now would enrol the leakage |
| 11 | `IA` in no branch of `feature_schema` | `FEATURE_SCHEMA_API_AUDIT.md` | 2026-07-16 | pre-wipe, still open |
| 12 | STRING as a reranker feature (no fill tax) | the STRING reclassification | 2026-07 | pre-wipe, still open. **Cheap and untried, and my #6 and #9 above add two more entries to this same cheap-and-untried shape** |
| 13 | Learned multi-layer mix on the production base | -- | -- | **ANSWERED 2026-08-19**: `project_layer_axis_last_layer_wins_2026_08_19` ran it. `z-mix-learned 0.2517` vs `z-layer48 0.2545` = **-0.0028, separates** (resolution floor 0.0013). Learned weights converge monotone in depth 7.1/15.3/32.5/45.1%. FRAME DIFFERS (per-residue sparse codes on 2,646 LAFA probe proteins, not the production pooled base), so mark this **answered in a neighbouring frame**, not closed |
| 14 | six trailing items (prefilter-with-classifier-swap in the TRUE frame; sparse contrastive load-bearing; per-aspect layer routing; the 8,195 discarded `regulates` edges; the t0-non-experimental trivial baseline) | -- | -- | pre-wipe, still open. Note "sparse contrastive in the load-bearing form" sits here as UNMEASURED while section 4 uses -0.0043 to argue "against the sparse-contrastive direction generally" -- **the registry both closes and opens this direction, 40 lines apart** |

## The UNMEASURED ranking compares deltas against two different champions
verdict: CONFIRMED
first number: `SIGNAL-REGISTRY.md:164-170`. Item 1: `protst_zscore = 0.24849,
  **+0.0335 vs champion**`. Item 2: `triple-combine = 0.2650 vs **champion
  0.2213** = +0.044`.
second number (INDEPENDENT): the two receipts name different champions.
  - Item 1's harness: `protst_repr/REPR_RESULT.md` -- "`champion_L48_apples`
    re-scores the champion codes on this harness and reproduces the pinned
    **mean9 = 0.2150 exactly (0.21501)**". Corroborated twice more:
    `layer_ablation/WRITEUP.md:141` "`d8979601` learned k-WTA | **0.21500**" and
    `layer_ablation/scale_WRITEUP.md:18` "served champion d8979601 ... **0.2150**".
  - Item 2's harness: `research/text_scorer/WRITEUP.md:60` --
    "| champion d8979601 | **0.2213** |", and :88 "Raw-kNN lift over the champion
    is +0.044 (**0.2213** to 0.2650)".
  **Same encoder id, same "mean9 kNN retrieval", two values 0.0063 apart --
  1.85x the registry's declared 0.0034 noise floor.**
  This is not a rounding difference and the project already knows the harnesses
  differ: `REPR_RESULT.md` says its screen "confirms the
  `project_text_evidence_scorer` claim (raw-protst-text kNN ~0.2455) **on the
  champion's exact harness**" -- i.e. the ProtST arm reproduced across the two
  harnesses and **the champion arm did not**.
date of evidence: item 2 2026-07-08; item 1 2026-07-13 -> both pre-wipe.
frame: both claim "mean9 f_micro_w, kNN retrieval". Whatever differs between them
  is worth 0.0063 on the reference arm and is undocumented in both receipts.
population: item 1 query=7,401 ref=15,000 pool=100,000. Item 2's population is
  not stated in the registry and I did not locate it in the writeup's head.
platform gap: the same frame-descriptor operation. A pinned reference arm that
  reads two values in two runs is exactly what
  `_run_cafa_grid_artifact._eligible`-style forced equality is for
  (`COLLIDING-A-NUMBER.md` rule 1).
note: two consequences. **(a) The ranking is not a ranking.** +0.0335 and +0.044
  are deltas against different references, so "ranked by expected value" orders
  two numbers that are not on the same scale. Rebased on the pinned 0.2150 the
  triple-combine is +0.050, not +0.044, which would change nothing about the
  order but everything about whether the two are comparable at all.
  **(b) It is the reference arm that disagrees, not the treatment.** That is the
  `feedback_shared_offset_means_shared_machinery` signature: when the arm that
  should be identical across two runs is the one that moves, the difference is in
  the machinery, not in the thing being measured.

---

# DECISION-LOG.md: the second verdict store

## D-05's arm count is wrong by a factor of five, and the number it needed was measured 27 days later
verdict: CONTRADICTED (in the count; the decision itself is right and understated)
first number: `DECISION-LOG.md:20-25`, D-05, "Decided 2026-07-28":
  "The audit established that the standing was not measured once: **four
  successive arms** were scored on the same frozen frame and the best kept, and
  the registry itself records the final increment as **selected on test**."
second number (INDEPENDENT):
  `memory/project_offline_champion_0391_is_three_cell_2026_08_24.md` reproduces
  the ladder from `protea-reranker-lab/fullgo/RESULTS.md`:
      classifier + M2 label-semantics (anc2vec)          0.343
      + KNN-classifier ensemble, single seed             0.358
      + seed-averaged classifier + self-prior            0.381  (ties #1)
      + cross-aspect association + 5-seed                0.390
      + 7-seed average (champion)                        0.391
  That is **five successive arms, not four**, and the memory continues: "the
  champion is the **fifth of a five-step progression** with **at least three
  named negatives beside it**, so it is a MAXIMUM OVER A SEARCH and takes a
  selection floor, not the resolution floor. Sizing that floor to this
  document's roughly **20 reported arms** gives **0.0074**, so the aggregate
  clears it by only **1.4x**."
date of evidence: D-05 2026-07-28; the quantification **2026-08-24**
  -> both **pre-wipe**; the quantification is 27 days newer and the log never moved.
frame: D-05's "standing" is the THREE-cell mean 0.391 (NK/LK/PK). The registry
  and the thesis elsewhere use the NINE-cell 0.40765. Those are different
  statistics on different arms
  (`project_sealed_headline_is_a_projection_2026_08_24.md`), and D-05 does not
  say which one it is declining to compete against.
population: 3 cells for 0.391; 9 for 0.40765.
platform gap: **the selection floor is the missing operation.** A registry that
  counts the arms scored on a frame can compute `floor = f(n_arms)` and print it
  beside every delta. Today it took a person, in August, reading a RESULTS.md.
note: the correction strengthens D-05 rather than weakening it, and that is the
  point. D-05 declines to compete against the prior standing because it was a
  max-over-arms. August measured the max-over-arms penalty at **0.0074 against a
  +0.01033 advantage, a margin of 1.4x**. That is the number D-05's argument
  wanted and did not have, and it arrived a month later into a different store.

## D-02 is the ONE decision that reached the platform, and its evidence is a single unreplicated probe
verdict: CONFIRMED (as implementation), FRAME-UNKNOWN (as measurement)
first number: `DECISION-LOG.md:102-108`, D-02: "A probe over eleven consecutive
  release dumps found that on all-evidence data as much as **63.7%** of apparent
  additions had been seen before. On experimental evidence ... about **one
  percent** ... the leak tracks the contraction points, and the validation window
  crosses one."
second number (INDEPENDENT -- and this is the good news of the audit):
  the decision is IN CODE, in the tree that is ahead of the developer workspace.
  `worktrees/protea-deploy` at `a5de702 2026-09-01` carries
  `protea/core/first_appearance.py`, whose module docstring restates the rule and
  the 63.7% verbatim, and `protea/core/split_registry.py:383` carries it again.
  **D-02 is the only one of the eight decisions with a producer on this disk.**
  It is also the only one whose reasoning survives independently of the log.
where I looked for a receipt: `grep -rn "63.7"` over `agent-farm/`,
  `repositories/`, and the memory store. Five hits, all quoting the same probe
  (`CAMPAIGN.md:172`, `DECISION-LOG.md:103`, `first_appearance.py:14`,
  `split_registry.py:383`, plus the duplicate agent-farm checkout). **No probe
  script, no output, no per-release table.** Every hit is an ECHO of one
  measurement nobody can re-read.
date of evidence: 2026-07-28 -> window: **pre-wipe**
frame: eleven consecutive releases, all-evidence vs experimental-evidence. Which
  eleven is not stated anywhere. The claim that matters -- "the leak **tracks the
  contraction points**, and the validation window crosses one" -- is the
  non-uniformity claim, and **no per-release breakdown exists to check it**. By
  COLLIDING-A-NUMBER rule 2 this is a summary published without its breakdown,
  and the breakdown is the entire argument: "One percent would be tolerable if it
  were uniform, and it is not."
population: the whole corpus, all evidence codes.
platform gap: **a `measure_restoration_rate(release_range)` operation writing one
  row per release.** D-02 itself promises this -- "the restoration rate becomes a
  published property of the corpus in its own right, which is a result rather
  than a caveat" -- and the operation registry has no such operation
  (`grep first_appearance protea/operations/` -> zero hits in the deploy tree).
  So the decision is implemented as a library function and the *result* it
  promises to publish still has no producer.
note: this is the healthiest entry in either store and it still fails the
  breakdown test. The 30% contraction it rests on is independently corroborated
  in memory (`project_goa_not_monotone_two_contractions_2026_07_27`), which is
  why I mark it CONFIRMED as a decision. But "63.7%" itself is a single number
  from a single unreplicated probe, echoed five times, and read by two code files
  as settled.

## The decision log is ordered wrongly against its own rule, and one superseded entry still reads OPEN
verdict: CONFIRMED
first number: `DECISION-LOG.md:4` -- "One entry per decision, **newest first**."
second number (INDEPENDENT): the file's actual order is
  D-05, D-04, D-03, D-02, D-01, **D-06, D-07, D-08** -- descending for the first
  five and then ascending for the last three, which were appended at the bottom.
  All eight say "Decided 2026-07-28" except D-06 ("Raised: 2026-07-28"), so the
  ordering cannot be recovered from the dates either.
  Consequences a reader hits immediately:
  - `D-06:190` says "**Status: OPEN. Needs the author.**" and `D-07:254` says
    "**Supersedes D-06**". D-06 is never edited to say so. Someone scanning for
    open author decisions finds a closed one.
  - `D-04` is superseded by `D-08` (":419 Supersedes D-04"), again only from the
    superseding end.
  - `D-07` carries two same-day amendments in its own body ("D-07 correction,
    same day: the split was narrower than first stated" and "D-07 outcome, same
    day"), one of which retracts the entry's central claim: "**That is wrong for
    the deployed path and the error was mine.** The claim came from reading the
    working copies ... rather than the branches the platform actually consumes."
date of evidence: 2026-07-28 -> window: pre-wipe
platform gap: MURO for the ordering; but "supersedes" is a relation and a store
  that recorded it in both directions would not need a reader to hold it.
note: D-07's self-correction is the single best-executed epistemic act in either
  store -- a same-day retraction that separates "what survives unchanged" (five
  items, each verified) from "what is downgraded" (the urgency argument), and
  keeps the change rather than rewriting the commits. It is the model the
  SIGNAL-REGISTRY's section 4 needed and did not get.

## Nothing that happened in August reached the decision log, including the two things that most needed a decision
verdict: CONFIRMED (negative check; where I looked is stated)
where I looked: full text of `DECISION-LOG.md` (466 lines); every date token in
  it (`grep -oE '20[0-9]{2}-[0-9]{2}-[0-9]{2}'` -> **eight hits, all
  `2026-07-28`**); `git log -- plans/DECISION-LOG.md` (three commits, last
  2026-07-28); and `git log` of the branch for any later commit touching it.
the two undecided things:
  1. **The 2026-08-27 registry wipe.** 93 evaluation_result rows and 19
     prediction_set rows survive, all created 2026-08-27..30. No entry.
  2. **The retraction of the recommendation to rebuild on ProtST**
     (2026-08-23, text leakage). The refutation says in its own words "**no
     thesis sentence may recommend ProtST on these numbers**" and section 8 of
     the registry still makes it step 2 of the clean trajectory. No entry.
  Also absent: rung 2 closing the retrieval axis "without a winner" (#253,
  2026-08-23); the rung renumbering that `rungs.yaml:71-77` calls "two months of
  drift" and which contradicts CAMPAIGN.md's declared rung numbers; and the
  gate change from retrieval-quality-as-ranking to retrieval-quality-as-floor
  (`rungs.yaml:80-86`), which is a methodological decision recorded only in a
  YAML comment.
note: by the log's own first paragraph -- "A decision that is not written here
  was not taken, it was **drifted into**" -- the campaign drifted into all five.
  `rungs.yaml` is where those decisions actually live, in comments, and it is not
  the decision log and does not claim to be.

---

# COUNT RECONCILIATION, so my "nine more" is auditable

The registry's own four wrongly-archived entries, identified by their move
markers, are all **feature families out of section 3**, none from section 4:
  - `emb_pca_query_0..15` -- `:171` "(moved from section 3)"
  - KNN homology block -- `:178` "(moved to section 2)" / `:102` "moved UP from OBSOLETE"
  - `interpro_*` as a feature -- `:185` "(moved from section 3)"
  - `length_query` -- `:194` "(corrected)", partially observed not dead
Its two reclassifications are `Learned k-WTA GO encoder` and `STRING PPI`
(`:143-151`), plus `Learned multi-layer mixing` moved out of a double listing.

**My nine are disjoint from all of those.** They are, in descending confidence:

1. `GO-text BioBERT label basis` -- measured **+0.012 POSITIVE** on LK-BPO, filed
   in a section titled "negative"; the thesis uses it as pillar 4's mechanism.
2. `GCN label encoder` -- refuted on **AUC 0.5501**, a statistic the registry
   bans at `:55-56`, measured on a hand-built DAG-proximity scalar, not a GCN.
3. `annotation-space RAG` -- the fourth row of the very table whose invalidity
   the registry uses to rescue the k-WTA GO encoder, and it separates from the
   random control **8x more strongly** than the arm that was rescued.
4. `SSE Mode A` -- ties its own random-order control to four decimals in all
   three PK cells; the receipt itself says "the loss is volume".
5. `SSE Mode B` -- four ties with CIs crossing zero and two positives killed by
   a shuffled control. No measured negative exists.
6. `ProtEx exemplar verification` -- **+0.0028 / +0.0071 with CI spanning zero**
   = null, and the receipt names the untried replace-the-prefilter mode.
7. `phylogenetic profiling` -- selected arm 3-4x **inside** the noise floor with
   no CI by explicit choice, on 15.9% coverage, with the remedy named and untried.
8. `donor-recency weighting` -- **NO TRACE ANYWHERE** but the registry line.
9. `M3 IEA pretraining` and `SVD label embedding` -- **plan milestones from a
   document superseded before they ran** (counted as one entry; they are two
   rows).
Plus two structural findings that move whole groups rather than single rows:
   the `objective=binary` contradiction, which the registry applies to one row
   and which propagates to five more; and the fact that the modal REFUTED
   population is {LK-BPO, PK-BPO}, two cells of nine, neither of them the served
   NK cell.

# WHERE I LOOKED (so the negatives above count)
- `agent-farm/plans/` in full: both verdict stores line by line, plus
  CAMPAIGN.md, E2E-CANONICAL-RUN.md, GENESIS-STATE.md, COLLIDING-A-NUMBER.md,
  rungs.yaml, thesis-pillars/PILLARS.md, prior-knowledge-wall/PLAN.md,
  representation-science/PLAN.md, thesis-clean-iteration/SIGNAL-STORE.md,
  text-evidence-scorer/PLAN.md, and `archive/` (7 directories, 13 files).
- `repositories/protea-reranker-lab/` in full: `research/` (314 files -- 224 .py,
  73 .md, **0 .json**), `champions.md`, `git log`, `git status`.
- `worktrees/protea-deploy` at `a5de702` (2026-09-01), which is ahead of
  `repositories/PROTEA`: `protea/core/first_appearance.py`,
  `protea/core/split_registry.py`, `protea/operations/`.
- `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/`: all 210 files by
  name, ~15 read in full, plus a full wikilink-integrity pass (179 targets,
  120 resolve, 59 dangle).
- The filesystem: `df`, `lsblk`, `mountpoint /mnt/protea-archive`, and `find`
  over `/home/xaxi` and `/mnt` for every storage path either store names.
- `storage/coordination/rescued/` (4 partial trails; none covered this slice).
- NOT touched, per the constraints: any database, any live connection, and
  `repositories/PROTEA/` was read only, never written.

# THE THREE SENTENCES A SUCCESSOR NEEDS
1. **Both verdict stores froze on 2026-07-27/28 and were never revised**, so
   every one of the ~28 REFUTED closures and all 14 UNMEASURED gaps is pre-wipe,
   and the registry's #1 ranked lever (rebuild retrieval on ProtST) was refuted
   as text leakage on 2026-08-23 while the registry still recommends it twice.
2. **The registry is now the most precise surviving carrier of numbers whose
   receipts no longer exist** -- one receipt path in 331 lines, and that file is
   gone; every `storage/` path it names is gone; `/mnt/protea-archive` is an
   empty unmounted directory holding the 144 archived memory files and the
   "closed and md5-verified" two-tower and learned-encoder backups -- which makes
   it uncollidable by construction, the one condition COLLIDING-A-NUMBER says
   must never be allowed.
3. **Nine more entries sit in the position the registry created two categories
   for and then stopped applying**, including one that is measured POSITIVE, one
   refuted on a statistic the registry itself bans, one that is the discarded
   half of the very experiment it rescued, and one with no trace of any
   measurement anywhere in the project.

# THE ONE OPERATION THAT WOULD HAVE PREVENTED MOST OF THIS
An `evaluation_result` row that carries its FRAME as columns -- obo/IA version,
`prop`, `norm`, `max_terms`, `th_step`, whether `-known` was applied, the metric
name, the eval window, the pool definition, the seed, the objective, and the
population count -- plus a `control` column (none / shuffled / random-order /
matched-volume) and a `selection_floor` derived from the number of arms scored on
that frame. Section 10 of the registry already asks for the first half of this
and calls it outstanding work. With it, the PK-BPO table above is a `GROUP BY`,
the two champion baselines (0.2150 vs 0.2213) collide automatically, the
random-control ties in SSE and phylo are a computed column rather than a
reader's catch, and a refuted entry cannot exist without a row behind it.

END OF REPORT. Written 2026-09-02 by auditor `verdict-stores`. Read-only
throughout; the only file written is this one.
