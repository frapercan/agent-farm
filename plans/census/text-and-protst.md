# Census slice: text-and-protst

Auditor slice key: `text-and-protst`
Started: 2026-09-02

## Slice description

- `plans/text-evidence-scorer/` and `plans/crossobo-native-delta/`.
- SIGNAL-REGISTRY section 5 item 1 claims: ProtST as PRIMARY RETRIEVAL SPACE is the
  largest unexploited measured lever; `protst_zscore` 0.24849, +0.0335 vs champion,
  wins 9 of 9; receipt `storage/regen_headline/protst_repr/protst_repr_report.json`.
- Task: (a) does that receipt exist on this disk right now? (b) collide it against the
  memory claim that the ProtST advantage is TEXT LEAKAGE (9 of 9 separate on
  UniProt-described proteins, 0 of 9 on undescribed). Both cannot be the headline.

## Status log

- [in progress] locating receipt, plans dirs, rescued trails.

---

## F1. Does the SIGNAL-REGISTRY receipt `storage/regen_headline/protst_repr/protst_repr_report.json` exist on this disk?

verdict: **CONTRADICTED** (the cited receipt does NOT exist; a different, weaker artifact does)

first number (the claim): SIGNAL-REGISTRY.md:164-168
    "1. **ProtST as the PRIMARY RETRIEVAL SPACE.** **ARM CORRECTED**: `protst_zscore`
     = 0.24849, **+0.0335 vs champion, wins 9/9**. But **RAW ProtST, which is what
     is deployed**, = 0.24547, **+0.0305, wins 8/9, losing nk-MFO by ~-0.0009**.
     Receipt: `storage/regen_headline/protst_repr/protst_repr_report.json`. Still
     the largest unexploited measured lever."

second number (independent): exhaustive filesystem search.
    - `find /home/xaxi/Thesis2 -maxdepth 6 -name 'regen_headline*'` -> FOUR hits, ALL under
      repositories/worktrees, NONE under storage/:
        /home/xaxi/Thesis2/repositories/protea-reranker-lab/research/regen_headline
        /home/xaxi/Thesis2/worktrees/lab-reporting/research/regen_headline
        /home/xaxi/Thesis2/worktrees/lab-gates/research/regen_headline
        /home/xaxi/Thesis2/worktrees/lab-bundle/research/regen_headline
    - `find /home/xaxi -name '*protst_repr*'` -> only the DIRECTORY and
      `protst_repr_screen.py` in those four trees. NO `protst_repr_report.json` anywhere
      on the machine, under storage/ or anywhere else.
    - `find /home/xaxi/Thesis2/storage -iname '*protst*'` -> exactly TWO files, both
      SCRIPTS, both in the encoder-study (the leakage side):
        storage/encoder-study/scripts/97_protst_text_leakage.py
        storage/encoder-study/scripts/98_backbone_spread_without_protst.py
      i.e. the only ProtST artefacts in storage/ belong to the LEAKAGE investigation,
      not to the retrieval-space headline.
    - What DOES exist for the headline:
        repositories/protea-reranker-lab/research/regen_headline/protst_repr/REPR_RESULT.md
        .../protst_repr/protst_repr_screen.py
        .../protst_repr/champ_codes_regen.py
      all mtime 2026-07-29 01:48 (the git-checkout stamp of the reinstall, not a run date).

date of evidence: artifacts stamped 2026-07-29 (checkout), content predates the reinstall
    -> window: PRE-WIPE at best; NOT evidence about the current (post-2026-08-27) window.
frame: unknown at this point; to be read from REPR_RESULT.md.
population: claimed 9 cells (NK/LK/PK x MFO/BPO/CCO).
platform gap: no PROTEA operation produces a "retrieval-space screen" writing to the DB.
    The whole artefact is a lab script writing a markdown file into a git repo.
note: the registry's single highest-ranked unexploited lever is cited to a JSON receipt
    THAT DOES NOT EXIST. The path is also wrong in kind: `storage/regen_headline/...`
    vs the real `repositories/protea-reranker-lab/research/regen_headline/...`.
    A reader following the citation finds nothing.

## F2. The primary source of the +0.0335 claim, and its declared artefact list

verdict: **NOT_FOUND** (every binary/JSON artefact the source itself declares is gone;
         only the prose survives)

Primary source: `/home/xaxi/Thesis2/repositories/protea-reranker-lab/research/regen_headline/protst_repr/REPR_RESULT.md`
Title line: "# ProtST representation screen at the kNN-retrieval level (2026-07-13)"

Its own "## Artefacts" section declares FIVE artefacts, ALL under `storage/regen_headline/protst_repr/`:
  - `protst_repr_report.json`            -> ABSENT
  - `protst_repr_screen.py`              -> present, but in the REPO not in storage/
  - `protst_prod.npz` (122401 x 512)     -> ABSENT
  - `champ_codes.npz`                    -> ABSENT
  - `protst_kwta_d2048_k128.pt`, `protst_kwta_d4096_k128.pt` (+ `.scaler.npz`) -> ABSENT

So the SIGNAL-REGISTRY's "Receipt:" line is an **ECHO of this document's own Artefacts
list**, i.e. it cites a path the source ASSERTED it would write, and nobody re-checked.
The registry did not verify a file; it copied a filename.

Leaderboard as printed (REPR_RESULT.md, "## Leaderboard (mean9 f_micro_w, kNN-retrieval)"):
| arm | mean9 | vs champion | nk-bpo | lk-bpo | pk-bpo |
| protst_zscore      | 0.2485 | +0.0335 | 0.20611 | 0.23452 | 0.09343 |
| protst_raw         | 0.2455 | +0.0305 | 0.20639 | 0.23479 | 0.09132 |
| protst_kwta_d4096  | 0.2411 | +0.0261 | 0.2047  | 0.24069 | 0.08135 |
| protst_kwta_d2048  | 0.2380 | +0.0230 | 0.19957 | 0.23394 | 0.08191 |
| champion_L48_apples| 0.2150 |  0 (ref)| 0.16646 | 0.21735 | 0.06445 |

date of evidence: **2026-07-13** -> window: **PRE-REINSTALL and PRE-WIPE**. Under the audit
    rule ("any measured result dated before 2026-08-27 is NOT evidence about the current
    window"), this number is out of frame TWICE over.
frame (as declared by the source, verbatim): query=7401, ref=15000, pool=100000, cosine
    top-30 GO-transfer vote, cafaeval f_micro_w, mean9 = unweighted mean of the 9 cells,
    single seed 42, base swap ONLY (ProtST EmbeddingConfig `bd3cd470-...`, dim 512, single
    chunk per protein), "READ-ONLY DB". **`-known` is NOT mentioned anywhere in the
    document** -> frame on the `-known` axis: UNKNOWN, and the registry's own section 6 says
    omitting `-known` moves PK-BP by -0.0847.
population: 7,401 query proteins, 9 cells. Per-cell n NOT reported anywhere in the document.
platform gap: MURO for reproduction as written -- the ProtST bank (`protst_prod.npz`,
    122401 x 512) and the champion codes are both gone, and there is no registered PROTEA
    operation that produces a "retrieval-space screen" over an arbitrary embedding bank.
    To reborn it you would need (i) an operation that materialises an EmbeddingConfig bank
    for an accession list, (ii) an operation that runs top-k GO-transfer vote + cafaeval
    per cell and writes evaluation_result rows.
note: the document ITSELF caveats the number: "kNN-only mean9 is a CANDIDATE screen number,
    NOT the sealed 0.4063 reranked headline" and "Single seed 42 (screen)... exact per-cell
    values are single-seed". The SIGNAL-REGISTRY quotes the number and drops BOTH caveats.
    Also: the source's OWN RECOMMENDATION (d) is "Gate to expensive export: PASS on raw
    ProtST, **no representation change required**" -- i.e. the source concluded ProtST was
    ALREADY correctly deployed as `apply_protst_text`, while the registry recasts the same
    document as "the largest UNEXPLOITED measured lever". Those are different readings of
    one file.

## F3. THE COLLISION, PART 1: the leakage claim's own receipt says 1 of 9, not 0 of 9

verdict: **CONTRADICTED** -- the memory claim "0 of 9 separate among the undescribed" is
         refuted by the raw output of the very script it cites, which shows a NINTH row
         that separates with a starred interval on the undescribed side.

first number (as quoted): `/home/xaxi/.claude/projects/-home-xaxi-Thesis2/memory/project_protst_advantage_is_text_leakage_2026_08_23.md`
    front-matter description: "9 of 9 comparisons separate on described proteins, 0 of 9 on
    the 550 UniProt never described"
    body: "**9 of 9 separate among the described, 0 of 9 among the undescribed, and it
    INVERTS against the two strongest rivals.**"
    Its printed table has **EIGHT** rows: ankh-large, prot_t5, esm2_t33_650M, ProstT5,
    esmc_600m, esm2_t6_8M, rung2-dense, rung2-pooled.

second number (INDEPENDENT, from the receipt on disk):
    `/home/xaxi/Thesis2/storage/encoder-study/artifacts/97_run.out` (mtime 2026-08-23 10:56)
    prints **NINE** rows. The missing ninth is the FIRST one alphabetically:

      ElnaggarLab/ankh-base   descritas +0.0949[+0.086,+0.104]*   SIN describir +0.0561[+0.037,+0.076]*

    That row carries a `*` on BOTH sides. The script's own legend defines `*` as
    "el intervalo emparejado excluye el cero" (97_protst_text_leakage.py:~143,
    `star = "*" if lo > 0 or hi < 0 else " "`).

    So on the receipt the score is **described 9/9, undescribed 1/9** -- not 0/9.
    ProtST beats ankh-base by +0.0561 with a 95% paired bootstrap interval of
    [+0.037,+0.076] on the 547 proteins UniProt has NEVER described, i.e. on the group
    the memo itself calls "clean by construction".

    The row is not marginal: it is the LARGEST undescribed-side effect in the table by a
    factor of six (next largest +0.0088, and not starred).

date of evidence: 2026-08-23 -> window: **PRE-WIPE** (4 days before the 2026-08-27 registry
    wipe). It is post-reinstall, so the receipt files survive; the DB rows it read do not.
frame: reachability (NOT Fmax, NOT f_micro_w). Metric =
    |closure(union of donor terms accumulated in donor-rank order until >=25 terms) INTERSECT truth|
    / |truth|, truth = NK gained terms closed under is_a + part_of at ontology snapshot 230.
    BUDGET=25 terms, prediction sets with limit_per_entry=30 (top-30 donors), self-matches
    excluded by `qp.sequence_id <> rp.sequence_id`. Population fixed at exactly
    np = 22,498 predicted proteins per set, one set per model_name.
    NO `-known`; NO tau; NO propagation-fill; NO IA weighting. This is a RETRIEVAL CEILING,
    not a scored metric.
population: the NK cell of the 220->230 window ONLY. n=3,015 (intersection over all 10
    backbones), 2,468 described / 547 undescribed.
platform gap: the script reads the live DB directly via `os.environ["PROTEA_DB_URL"]` with
    raw SQL and pickles (`categories_220_230.pkl`). There is no registered operation for
    "reachability at a term budget, split on a UniProt metadata predicate". The prediction
    sets it read are gone (wipe), so it cannot be re-run as written: MURO until an operation
    exists that (i) re-materialises 10 backbone prediction sets over the same 22,498
    population and (ii) computes budgeted reachability per protein.
note: **This is the single most important thing in this slice.** The memo's headline
    asymmetry -- "the advantage evaporates exactly where nobody could have read anything" --
    is the whole argument for leakage, and it is stated over a table from which the one
    contradicting row was dropped. A reader must not cite "0 of 9". The honest statement is
    "8 of 9 collapse to inside the interval on the undescribed; the ninth, against the
    weakest backbone in the panel, survives at +0.0561".

## F3b. Secondary numeric inconsistencies inside the same leakage memo

verdict: CONFIRMED (three, all small, all in the same direction: the memo quotes the
         PRE-intersection population where the table is POST-intersection)

- memo says "the 550 UniProt never described" and "On the **550** undescribed proteins the
  twilight spread is 0.0835". Receipt `97_run.out` says "con comentario FUNCTION: 2468
  sin el: **547**", and `97_leak.json` says `"n": 3015, "described": 2468`.
  Where 550 comes from: `97_leak.log` line 2, "NK con comentario FUNCTION en UniProt:
  **2481 de 3031** (81.9%)" -> 3031 - 2481 = 550. That is the population BEFORE the
  `set.intersection` over the ten backbones. ankh-base only scored 3,015 of 3,031
  (`97_leak.log`: "ElnaggarLab/ankh-base 0.6705 sobre **3015**", every other model "sobre
  3031"), so the comparison table is on 3,015 and 547 undescribed.
- memo says "All 3,031 NK targets are reviewed Swiss-Prot entries ... 81.9% of them carry a
  `function_cc` comment" -- that 81.9% (2,481/3,031) is correct for 3,031 but the table is
  2,468/3,015 = 81.9% too, so the percentage survives; the COUNTS do not.
- The dropped model (ankh-base) is exactly the one whose coverage shortfall (3,015 vs 3,031)
  set the intersection. So the row that was omitted from the memo is the row that defines
  the memo's own population.
note: none of these change the verdict of F3, but they show the memo was written from the
      log's header line rather than from the result table underneath it.

## F4. The leakage test never tested the interaction it claims

verdict: **DEDUCED-NOT-MEASURED** -- the leakage conclusion rests on "significant in group A,
         not significant in group B", which is not a test that the effect differs between
         A and B. The script computes two SEPARATE bootstrap intervals and never bootstraps
         the difference-of-differences.

first number: `97_protst_text_leakage.py` inner loop:
        for mask in (desc, ~desc):
            dd = d[mask]
            ii = RNG.integers(0, mask.sum(), size=(4000, mask.sum()))
            lo, hi = np.percentile(dd[ii].mean(1), [2.5, 97.5])
            star = "*" if lo > 0 or hi < 0 else " "
    Two independent resamples. No interaction term, no test of (described - undescribed).

second number (derived here, from the receipt's own intervals):
  The undescribed group is 547 vs 2,468 described, ratio 4.51, so its intervals must be
  sqrt(4.51) = 2.12x wider PURELY from n. Observed half-widths confirm it exactly:
  ankh-large described half-width 0.0055, undescribed 0.013 -> ratio 2.36. The loss of
  significance on the undescribed side is therefore substantially a POWER effect, which is
  the thing the memo needed to rule out and did not.

  An approximate interaction check (does the undescribed 95% interval EXCLUDE the described
  point estimate?), computed by hand from `97_run.out`:
    ankh-base    desc +0.0949  undesc CI [+0.037,+0.076]  -> EXCLUDES (smaller, still >0)
    prot_t5      desc +0.0098  undesc CI [-0.027,+0.003]  -> EXCLUDES
    esm2_t33     desc +0.0209  undesc CI [-0.014,+0.015]  -> EXCLUDES
    esmc_600m    desc +0.0359  undesc CI [-0.009,+0.026]  -> EXCLUDES
    esm2_t6_8M   desc +0.0391  undesc CI [-0.010,+0.023]  -> EXCLUDES
    ankh-large   desc +0.0095  undesc CI [-0.013,+0.013]  -> CONTAINS  (no evidence of a change)
    ProstT5      desc +0.0166  undesc CI [-0.006,+0.024]  -> CONTAINS
    rung2-dense  desc +0.0088  undesc CI [-0.009,+0.018]  -> CONTAINS
    rung2-pooled desc +0.0060  undesc CI [-0.009,+0.017]  -> CONTAINS
  => **5 of 9 show evidence that the advantage shrinks on the undescribed; 4 of 9 do not**,
  and in the one case where the shrink is best resolved (ankh-base) the residual advantage
  is still +0.0561 with the interval clear of zero.
  (Approximate: it ignores the described side's own uncertainty, so it OVERSTATES how many
  cells show an interaction. The true count is 5 or fewer, never 9.)

date of evidence: 2026-08-23 -> window: PRE-WIPE.
frame: as F3 (reachability, budget 25, NK cell of 220->230, top-30 donors, self excluded).
population: 3,015 NK proteins; 2,468 described / 547 undescribed.
platform gap: same as F3, MURO.
note: "9 of 9 / 0 of 9" is the difference of two significance verdicts dressed as a measured
      interaction. The correct headline the receipt supports is "the advantage is smaller on
      the undescribed in 5 of 9 comparisons and is not resolved in the other 4".

## F5. "It INVERTS against the two strongest rivals" -- both halves are wrong

verdict: **CONTRADICTED**

first number (memo + `98_backbone_spread_without_protst.py` docstring, verbatim):
    "and against the two strongest rivals it inverts"

second number (from `97_leak.json` `means`, full precision, sorted):
    mila-intel/ProtST-esm1b                  0.7584038446   <- ProtST
    rung2-pooled:...:0868f1ff                0.7527615533   <- STRONGEST RIVAL
    Rostlab/prot_t5_xl_half_uniref50-enc     0.7525761115
    ElnaggarLab/ankh-large                   0.7507022995
    rung2-dense:...:0868f1ff                 0.7503396530
    Rostlab/ProstT5                          0.7432334657
    facebook/esm2_t33_650M_UR50D             0.7411177473
    esmc_600m                                0.7275095334
    facebook/esm2_t6_8M_UR50D                0.7252494594
    ElnaggarLab/ankh-base                    0.6705084290

  (a) The two arms the memo calls inverted are prot_t5 (-0.0120) and ankh-large (-0.0003).
      They rank #3 and #4 overall. The actual strongest rival is **rung2-pooled**, against
      which ProtST is **+0.0041 on the undescribed, i.e. NOT inverted**.
      Charitable reading: "strongest sequence-only PLM rival". Even then prot_t5 and
      ankh-large are #1 and #2 among the PLMs only if you first delete the project's own
      rung2 arms from the panel, which the memo does not say it is doing.
  (b) Neither "inversion" is resolved: prot_t5 CI [-0.027,+0.003] and ankh-large CI
      [-0.013,+0.013] both CONTAIN zero. A point estimate whose interval spans zero has no
      sign. Calling it an inversion is reading a sign out of noise -- the exact defect
      `feedback_a_fraction_is_not_a_measurement` names.
note: the phrase appears in THREE places (the memory front-matter, the memory body, and
      script 98's own docstring, written 4 minutes after script 97 ran). The two later ones
      are ECHOES of the first, not independent support.

## F6. The "0.0835 with and without" corroboration is a statistic that could not have seen the effect

verdict: **NOT_FOUND (no receipt) + FRAME-UNKNOWN (wrong statistic for the claim)**

first number: `storage/encoder-study/RESULTS.md:193-194` -- "On the 550 proteins UniProt
    never described, the twilight spread is 0.0835 with it and 0.0835 without."
    Echoed verbatim in the memory memo line 55.

second number (independent): the value is NOT on disk. `98_backbone_spread_without_protst.py`
    writes ONLY the all-proteins table to `artifacts/98_spread.json`; the undescribed-only
    table is `print`ed and never persisted, and there is no `98_run.out` in
    `storage/encoder-study/artifacts/` (every other script in the 84-114 range has one:
    84,85,86,87,88,89,90,91,96,97,99,100,102,103,104,109,110,112,113,114_run.out; 98 is the
    ONLY gap). The claim survives as prose only.
    What IS on disk, `artifacts/98_spread.json`, is the ALL-proteins table and it matches the
    memo exactly: twilight con 0.08418478052, sin 0.06251232270, n 778; distant/close/
    near-identical identical con vs sin.

WHY THE STATISTIC CANNOT SUPPORT THE CLAIM: the script defines spread as
    a, b = max(allm) - min(allm), max(nop) - min(nop)
i.e. **max minus min across arms**. Dropping one arm changes it ONLY if that arm was the max
or the min. "0.0835 with and without" therefore says exactly one thing: on undescribed
twilight proteins ProtST is not the extreme arm. It says NOTHING about whether ProtST retains
a mean advantage there -- and F3 shows it retains +0.0561 over ankh-base, with ankh-base
being the panel MINIMUM, which is precisely the configuration in which a max-min spread is
blind to ProtST.

FRAME MISMATCH, and it is not flagged anywhere: script 97 (the leakage table) uses
    `POP, BUDGET, TOPN = 22498, 25, 30`
script 98 (the spread) uses
    `POP, BUDGET, TOPN = 22498, 10, 30`
**BUDGET 25 vs BUDGET 10.** The memo presents the two tables as one argument without saying
the term budget differs by 2.5x. Script 98 also filters `AND ec.model_name NOT LIKE 'rung2-%'`
so its panel is 8 arms, while script 97's is 10 (the logs confirm: "10 backbones" vs
"8 backbones"). Two budgets, two panels, one narrative.
platform gap: MURO -- reachability-at-budget by homology band, split on a UniProt text
    predicate, has no registered operation; and the undescribed-only table has no artifact at all.

## F7. THE BIG ONE: the leakage clearance was a DEDUCTION FROM A DEFINITION, and it was false

verdict: **DEDUCED-NOT-MEASURED, and subsequently MEASURED FALSE**

first number (the deduction), `/home/xaxi/Thesis2/agent-farm/plans/text-evidence-scorer/PLAN.md`,
    section "## Leakage position (the corrected argument)", written **2026-07-08**
    (git: `cc8eacc 2026-07-09 20:25:02 plan(text-evidence-scorer): ProtST/ProTrek text->GO de-risk (#215)`):

      "NK proteins had **no function text at t0** -> fully clean, zero asymmetry
       (the strongest, primary result cell)."

    and in the candidate table, the Leakage column for BOTH ProtST-ESM2 and ProTrek-650M:
      "Cleared by dates (ICML 2023 << t0=v227 2025-09); **NK fully clean (no function text
       existed)**"

    There is no citation, no query, no count. It is inferred from what "NK" MEANS
    (no experimental evidence) to what UniProt CONTAINS (no prose). Those are different
    facts about different columns.

second number (the measurement, 46 days later):
    `/home/xaxi/Thesis2/storage/encoder-study/artifacts/97_leak.log` line 2:
      "NK con comentario FUNCTION en UniProt: **2481 de 3031 (81.9%)**"
    i.e. **81.9% of the NK cell DOES carry function prose in UniProt**, not 0%.
    The producing SQL is unambiguous:
      SELECT canonical_accession FROM protein_uniprot_metadata
      WHERE canonical_accession = ANY(:a) AND function_cc IS NOT NULL AND btrim(function_cc) <> ''

date of evidence: deduction 2026-07-08 (pre-reinstall); refutation 2026-08-23 (pre-wipe).
frame: the deduction is stated for the t0=v227(2025-09) -> t1=v230(2026-03) window; the
    refutation is measured on the 220->230 window's NK cell. **Different windows**, so
    strictly the refutation does not disprove the exact sentence -- but the deduction was
    about a PROPERTY OF THE CATEGORY ("NK means no function text"), not about a window, and
    that property is false by 81.9 percentage points. `project_nk_cell_heterogeneous_prior`
    already recorded independently that NK means no EXPERIMENTAL evidence, not nothing known.
population: 3,031 NK proteins of the 220->230 window.
platform gap: the check that would have caught it is a ONE-LINE count over
    `protein_uniprot_metadata.function_cc` restricted to the category table. There is no
    operation that reports "text availability by knowledge category" at set-construction
    time, which is why a plan could declare it clean and nobody could contradict it for
    six weeks.
note: **This is the highest-value item in the slice.** The entire ProtST programme was
    authorised on a leakage clearance that was never measured, and the primary result cell
    the plan calls "the leakage-free anchor" is 82% contaminated. Everything downstream --
    the +0.0335 screen, the reranker A/B, the registry's "largest unexploited lever" --
    inherits it.

## F8. The plan the registry cites forbids the use the registry makes of it

verdict: **CONTRADICTED**

- `plans/text-evidence-scorer/PLAN.md` line 3-5, the objective, verbatim:
    "...as a text->GO EvidenceScorer in the meta-reranker (ADR-D43), **NOT as a primary kNN
     index**."
- `plans/SIGNAL-REGISTRY.md:164`, section 5 item 1, verbatim:
    "**ProtST as the PRIMARY RETRIEVAL SPACE.**"
  The registry's #1 unexploited lever is the exact use the governing plan ruled out in its
  first paragraph.
- The plan's own "Discipline (non-negotiable)" says "Stratify EVERY metric by the 3 axes:
  length ..., category (NK/LK/PK x aspect), neighbour-identity ...; **CIs on deltas; never
  drop an axis**" and "MLflow / tracked op; **no ad-hoc scripts in storage or /tmp for the
  final receipt**".
  The receipt the registry cites (`REPR_RESULT.md`) is: a single seed 42, **no CIs
  anywhere**, **no length axis**, **no neighbour-identity axis**, produced by
  `protst_repr_screen.py` -- an ad-hoc script in storage. It satisfies exactly one of the
  four non-negotiables (the 9-cell category x aspect axis).
- Minor but real: the plan calls the champion "d8979601 learned k-WTA / **ESM-C** +
  classifier"; `REPR_RESULT.md` says the champion codes were "regenerated from the
  production L48 base 08234f06 + **`ankh_base_hardneg.pt`**". Two documents six days apart
  name two different base models for the same champion. Whichever is right, the +0.0335 is
  a delta against a comparator the two documents do not agree on.

---

# Part 2: plans/crossobo-native-delta/

## F9. The crossobo plan's target frame VERIFIES exactly against on-disk ground truth

verdict: **CONFIRMED** (this is the one number in the slice that survives an independent check)

first number: `plans/crossobo-native-delta/PLAN.md` GATE 2 -- "Success = ~7401, buckets approx
    NK399 / LK868 / PK6340."
second number (independent, counted here from the files, not from any document):
    `/home/xaxi/Thesis2/CAFA_forever/data/releases/Sep_2025_Mar_2026/`
      groundtruth_targets.tsv        7401 lines, 7401 distinct accessions, no header
      groundtruth_NK.tsv             399 distinct proteins (after header)
      groundtruth_LK.tsv             868
      groundtruth_PK.tsv             6340
      groundtruth_PK_known.tsv       6340 distinct, and PK_known == PK exactly as a protein set
    union(NK,LK,PK) = 7401 and is EQUAL to the target list as a set.
    All four predicted numbers are exact, not approximate.

BUT, and the plan does not say it: **the three "buckets" are not a partition.**
    399 + 868 + 6340 = 7607, which is 206 more than 7401.
    NK n LK = 0,  NK n PK = 0,  **LK n PK = 206**,  NK n LK n PK = 0.
    So 206 proteins are LK in one aspect and PK in another. Calling them buckets and
    summing them gives 7607, a number 2.8% too large, and any per-protein rate computed
    on the sum is wrong by that much. This is the nine-populations problem in its cheapest
    form and it is visible in four `cut | sort -u` commands.
date of evidence: files stamped 2026-07-28 17:09 (restored with CAFA_forever) -> window:
    PRE-WIPE, but these are the LAFA reference lists, not registry rows, so they are
    unaffected by the 2026-08-27 wipe. Content is the Sep_2025 -> Mar_2026 (227->230) window.
frame: LAFA official frame, groundtruth_targets.tsv, t0 OBO releases/2025-07-22,
    t1 OBO releases/2026-01-23 (asymmetric pair, per the plan).
population: 7,401 targets, 227->230. NOTE this is a DIFFERENT window from the campaign's
    220->230, and from the leakage study's 220->230 NK cell (3,031 proteins).
platform gap: none for the ground truth itself; the plan's A1/A2/A3 (load_ontology_snapshot
    for 2025-07-22, then generate_evaluation_set with an explicit distinct pivot, then
    run_cafa_evaluation) is exactly the operation chain that WOULD make this on-platform.

## F10. The crossobo plan was never executed, and half its reference artefacts are gone

verdict: **NOT_FOUND**

Searched (all absolute, all on this disk):
  EXISTS  /home/xaxi/Thesis2/CAFA_forever/data/releases/Sep_2025_Mar_2026     (the 7401 side)
  EXISTS  /home/xaxi/Thesis2/CAFA_forever/modules/local/evaluation.nf         (the --graph/--graph2 proof)
  ABSENT  /home/xaxi/Thesis2/storage/ensemble_audit_2026_06_13/               (the 7002 native parquet)
  ABSENT  /home/xaxi/Thesis2/protea-lafa-knn/                                 (the t0 OBO 2025-07-22)
  ABSENT  /home/xaxi/Thesis2/lafa-smoke/                                      (the t1 OBO 2026-01-23)
  `find /home/xaxi -name '*34a634a8*'` -> ZERO hits. The eval set id
     `34a634a8-5739-4b04-923c-26db9eaab21e` that the plan's whole 7002-side evidence hangs on
     appears in no file on this machine.
  `find /home/xaxi/Thesis2 -name 'go-basic.obo'` -> exactly ONE:
     /home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/go-basic.obo
     i.e. the t0 side only. **The t1 OBO (releases/2026-01-23) is not on this disk.**
     Since the plan's own WARNING is that parity REQUIRES the asymmetric pair
     t0=2025-07-22 / t1=2026-01-23, the reproduction is blocked on a missing file.

So the entire "root cause" trace -- intersection 6081, LAFA-only 1320, PROTEA-only 921,
churn 99.8% PK (1317/1320), 0% recovery under t0 OBO vs 98.7% under t1 OBO -- has **no
artefact on this disk**. It is sourced to "closed audit 2026-06-23 (memory
`project_phantom_gap_crossobo_2026_06_23`)", i.e. to a memory file, and the plan says
"Every claim below was traced layer by layer and verified against artefacts". Those
artefacts are gone.
date of evidence: 2026-06-23 -> window: **PRE-REINSTALL** (lost) and PRE-WIPE.
platform gap: MURO as it stands. Reborn form = the plan's own A1+A2+A3, which is a
    genuinely well-specified three-operation chain (`load_ontology_snapshot`,
    `generate_evaluation_set` with old_native/new_native/pivot, `run_cafa_evaluation`)
    -- one of the few places in this slice where the platform path is already written down.
note: I did NOT touch the database, so I cannot say whether the 2025-07-22 snapshot was ever
    ingested. What I can say is that no local receipt of GATE 1 or GATE 2 exists.

## F11. The crossobo plan is superseded on its central mechanism, and the successor is 2026-08-27

verdict: CONFIRMED (the plan is stale, not wrong)

- PLAN.md A2 prescribes `pivot_ontology_snapshot_id = <2026-01-23>` explicitly, which is
  correct.
- `memory/project_pivot_default_routes_away_from_reconciled_2026_08_27.md` shows WHY the
  explicitness matters: `generate_evaluation_set.py:301`
  `pivot_id = _resolve_snapshot(p.pivot_ontology_snapshot_id, new_native)` -- **the pivot
  DEFAULTS to new_native**, and `:121` `same_snapshot = old_native == new_native == pivot_id`
  routes to the non-reconciled path when all three coincide. So the "obvious" fix
  (set the two natives equal) silently disables reconciliation.
- The successor memory also states the residual reconciliation forces is **UNMEASURED**
  ("nobody has counted it") and is **confined to prior knowledge**, and that
  "There is no ontology snapshot contemporary with GOA 220 (April 2024). Loading one is a
  precondition, not a detail."
=> The crossobo plan solves this for the 227->230 window. The CAMPAIGN's window is 220->230.
   The same A1 step (ingest a contemporary OBO) is STILL outstanding for 220, five weeks later.
note: the plan is written for a window the campaign no longer runs. Anyone reading it as
      current will pin 2025-07-22 / 2026-01-23 into a 220->230 frame where 2025-07-22 is
      fifteen months AFTER t0.

---

# Part 3: the collision resolved

## F12. THE COLLISION: the two "9 of 9" are not the same nine, and neither refutes the other

verdict: **FRAME-UNKNOWN in the registry, and the decisive experiment was NEVER RUN**

The task premise is "both cannot be the headline". They can both be numerically true,
because they are different measurements of different things:

| | registry section 5 item 1 | leakage memo |
|---|---|---|
| date | screen 2026-07-13, registry 2026-07-27 | 2026-08-23 |
| metric | cafaeval `f_micro_w`, mean of 9 cells | budgeted REACHABILITY, |truth n reachable|/|truth| |
| "9 of 9" means | 9 CELLS (NK/LK/PK x MFO/BPO/CCO) | 9 RIVAL BACKBONES |
| comparator | the champion learned sparse encoder (d8979601 / L48) | 9 PLM + rung2 arms |
| population | 7,401 queries, all nine cells | 3,015 proteins, NK cell only |
| window | 227 -> 230 | 220 -> 230 |
| donors | ref 15,000 / pool 100,000, top-30 | index of 22,498, top-30 |
| receipt | **MISSING** | **PRESENT** (97_leak.json / 97_run.out) |

**The champion is not in the leakage panel.** `97_leak.json`'s ten arms are ankh-base,
ankh-large, esmc_600m, esm2_t33_650M, esm2_t6_8M, ProtST-esm1b, ProstT5, prot_t5,
rung2-dense, rung2-pooled. The d8979601 champion -- the ONLY comparator the +0.0335 is
measured against -- was never scored on the described/undescribed split.

=> The leakage study does NOT refute the +0.0335. It refutes a DIFFERENT claim ("ProtST is
   the best backbone"), which the leakage memo says explicitly ("What this retracts: 'ProtST
   is the best backbone' is not a statement about representation").
=> The +0.0335 is UNTESTED for leakage. The one-line experiment that would settle it --
   re-run the 9-cell screen restricted to the 547 (or 550) NK proteins with no
   `function_cc` -- has never been run, and cannot be run now: the ProtST bank
   (`protst_prod.npz`), the champion codes (`champ_codes.npz`) and the prediction sets are
   all gone.

WHAT IS ACTUALLY IN CONFLICT is not the two numbers, it is the two RECOMMENDATIONS:
  SIGNAL-REGISTRY.md:292-296 -- "**Re-baseline the retrieval space.** Raw ProtST is +0.0305
    (8/9) and the z-scored arm +0.0335 (9/9)... Every downstream number depends on the
    substrate."
  leakage memo -- "**no thesis sentence may recommend ProtST on these numbers.**"
And the registry has not been touched since **2026-07-27** (git: the only commit that ever
touched `plans/SIGNAL-REGISTRY.md` is `f0e50a6 2026-07-27 20:40:14 plan(e2e): canonical
clean-run spec + receipt-backed signal registry (#233)`; `git log` on agent-farm shows
commits through 2026-09-02 that never touch it). So the registry's #1 lever is a document
that predates the leakage finding by 27 days and has never been reconciled with it.

## F13. The A/B's anti-leakage control is VOID, and it is the load-bearing sentence

verdict: **CONTRADICTED**

`repositories/protea-reranker-lab/research/regen_headline/protst_ab/AB_RESULT.md`,
"## Rigour (full A/B agent, 2026-07-13)", verbatim:

    "- **Bootstrap CIs (protein-level paired) - all 3 BP cells EXCLUDE ZERO:**
       - NK-BPO (leakage-free anchor) +0.0284, 95% CI [0.0059, 0.0569], 100% of resamples positive.
       ...
       The leakage-free NK-BPO anchor moves the SAME direction and by the MOST -> **the lift
       is the ProtST TEXT signal, not leakage.**"

The entire anti-leakage argument is: the effect is largest on the cell that cannot leak.
The premise is F7's deduction. **81.9% of NK carries UniProt FUNCTION prose**
(`97_leak.log`), so NK is not a leakage-free anchor and "largest on NK" is exactly what
ProtDescribe-style text exposure predicts. The control does not control.

The same premise appears verbatim in three more places, each presented as established:
  - `plans/text-evidence-scorer/PLAN.md`, candidate table: "NK fully clean (no function text existed)"
  - `research/text_scorer/WRITEUP.md`, Protocol: "NK is the leakage-free anchor (those
    proteins had no function text at t0)"
  - `research/text_scorer/WRITEUP.md`, Result 1: "nk-BPO +0.062 (leakage-free)"
None of the four cites a count. All four are the same unmeasured deduction, re-asserted.

WHAT SURVIVES: nothing here says the ProtST reranker lift is fake. It says the study's
own proof that it is not leakage is not a proof. The honest status of the +0.0088 mean9 /
+0.0192 LK-BPO / +0.0092 PK-BPO reranker lift is **measured, but leakage-uncontrolled**.

frame (pin it, because this is the 0.3433 the audit brief names): reranked, sealed
    227->230, arm A = champion baseline (64 features, K=30, embedding d8979601, pool
    s3://protea/datasets/clean-learned-train227-test230/ sha 775611822dd9), arm B = same
    pool + the 3 `protst_text` columns, EXCLUDE-set is the only delta, cafaeval f_micro_w,
    9 cells, evaluation_set 6e41eb5b, seeds 42 and 7.
    **armA pk-bpo = 0.3433** -- this is the frame in which the reranker reads 0.3433.
population: 7,575 eval queries. `protst_text_score` finite on only ~60% of BP candidate
    rows (eval 60.5%, train 59.7%), so the BP lift is carried by 60% of rows and the
    document does not report the delta on the covered subset.

## F13b. The A/B's intervals are attached to a different statistic than its deltas

verdict: CONFIRMED (small, but it is the kind that hides)

Same document, two sections, three cells, three mismatches:
    9-cell table          bootstrap section
    nk-bpo  +0.0304   vs  NK-BPO +0.0284
    lk-bpo  +0.0192   vs  LK-BPO +0.0197
    pk-bpo  +0.0092   vs  PK-BPO +0.0083
The table's deltas are cafaeval `f_micro_w` differences; the CIs are "protein-level paired"
bootstraps, i.e. a per-protein statistic. They are not the same quantity, and the document
presents the second as the error bar on the first. A reader quoting "+0.0304, 95% CI
[0.0059,0.0569]" is combining two different measurements.
note: the mismatch is largest exactly where the claim is loudest (nk-bpo, the "leakage-free
      anchor", 0.0020 apart = 7% of the effect).

## F14. Two champion baselines and two ProtST values inside ONE document

verdict: **CONTRADICTED** (an unflagged frame change mid-document)

`research/text_scorer/WRITEUP.md`, same harness described once at the top, two tables:

    Result 1:  champion d8979601 0.2150 | protst-text **0.2455** | nk-BPO 0.206 lk-BPO 0.235 pk-BPO 0.091
    Result 2:  champion d8979601 **0.2213** | protst-text **0.2541** | nk-BPO 0.215 lk-BPO 0.246

Same model id, same metric name, same stated protocol, numbers 0.0063 and 0.0086 apart.
Nothing in the document says the frame changed. A shared offset in the same direction on
both arms is the signature of shared machinery (a different reference set, a different OBO,
or a different cafaeval invocation), not of noise.

CONSEQUENCE FOR THE REGISTRY: item 1 (+0.0335 vs champion 0.2150) is in the FIRST frame;
item 2 ("Triple-combine `protst + protrek + d8979601` = 0.2650 vs champion 0.2213 =
+0.044") is in the SECOND. `SIGNAL-REGISTRY.md:292-296` then reads them as a ladder:
"Raw ProtST is +0.0305 (8/9) and the z-scored arm +0.0335 (9/9); the triple-combine is
+0.044 pre-reranker."
  Within the 0.2213 frame the real decomposition is:
    protst-text alone  0.2541 = +0.0328
    pst + d89          0.2557 = +0.0344
    pst + ptk + d89    0.2650 = +0.0437
  so **the triple adds only +0.0109 over ProtST alone**; it does not stack on top of the
  +0.0335. Reading the registry's two bullets as additive overstates the headroom by ~3x.

## F15. THE THESIS PUBLISHES A ProtST NUMBER MEASURED IN THE FRAME THE PROJECT RETRACTED

verdict: **CONTRADICTED** -- a retracted-frame number is load-bearing in a thesis chapter

the published sentence, `/home/xaxi/Thesis2/thesis/chapters/06_evaluation.tex:883-889`:
    "The two structural hypotheses testable with the resources of this work are both
     eliminated by measurement: term co-occurrence as a candidate generator ($+0.002$) and
     Gene Ontology hierarchical proximity as a feature (area under the curve 0.550 ...).
     **A text-aligned representation adds $+0.002$ on this cell** and a domain-signature
     graft is actively harmful on Biological Process..."
    ("this cell" = PK-BPO; the paragraph's conclusion is "the levers currently available
     are demonstrably insufficient to reach it".)

its source (found, exact):
    `research/regen_headline/BP_TECHNIQUE_LEVERS.md:89`, under the heading
    "## Ruled out by measurement (do not revisit without new evidence)":
        "- co-occurrence candidate expansion: +0.0021 (recall 0.32 -> 0.48)
         - **protst as a feature: +0.0016 on PK-BPO**"
    echoed at `research/regen_headline/BP_WALL_CHARACTERIZATION.md:45`:
        "Same for the precision-side levers that do not add ranking power: **protst +0.0016**,
         InterPro graft *negative* on BP (0.140 vs 0.218)."
    Both documents are dated **2026-07-16** and both state their baseline explicitly:
    `BP_WALL_CHARACTERIZATION.md`:
        "RERANKER (what we deliver)                 f_micro_w = **0.1255**"
    `BP_TECHNIQUE_LEVERS.md:6-8`:
        "Baseline to beat, all measured on PK-BPO: reranker AUC 0.7903 -> f_micro_w **0.1255**"

the retraction, `/home/xaxi/Thesis2/agent-farm/plans/SIGNAL-REGISTRY.md:111`, section
"## 3. BROKEN / RETRACTED (genuinely archived)":
    "| **`rankpct()` normalisation** | A BUG that cost **0.088** f_micro_w and **MANUFACTURED
     the 0.1255 baseline**. Fixed in PROTEA#737. **Invalidated every technique lever measured
     against it** |"

So: the thesis's +0.002 for the text-aligned lever is +0.0016 measured against a baseline
the project's own registry says was manufactured by a bug and that invalidates every lever
measured against it.

AND THE REGISTRY ALREADY CAUGHT THE NEIGHBOURING BULLET BUT NOT THIS ONE.
`SIGNAL-REGISTRY.md:188-192`, section 5 item 6:
    "**Co-occurrence candidate expansion** (moved from section 4). Its one board number is
     **+0.0021 POSITIVE**, produced by `fuse_and_score.py` line 121, which is **literally the
     `rankpct` call** the registry elsewhere blames for manufacturing the 0.1255 baseline,
     **on both arms**. The true-frame cafaeval was never run."
The +0.0021 and the +0.0016 are **adjacent bullets in the same list in the same document**.
The registry rehabilitated the first (moved it out of REFUTED into UNMEASURED) and left the
second in place. The thesis then publishes BOTH of them, in one sentence, as the two
"eliminated by measurement" hypotheses.

date of evidence: 2026-07-16 -> window: PRE-REINSTALL, PRE-WIPE, and PRE-`rankpct`-fix
    (PROTEA#737).
frame: PK-BPO, retrained booster on an exported PK dataset, cafaeval f_micro_w, baseline
    0.1255, **rankpct normalisation active**, single arm, no CIs, no seeds.
population: PK-BPO only, positives 1.06% in train / 2.47% in the eval pool
    (`BP_TECHNIQUE_LEVERS.md`).
platform gap: the true-frame re-measurement is one `run_cafa_evaluation` on the post-#737
    code path against the same exported dataset. It has never been run for ProtST, exactly
    as the registry says it has never been run for co-occurrence.
note: **do not let the thesis sentence stand.** It is the second-largest defect in the slice
    after F7, and it is on the argument surface, not the verification surface.

## F16. FIVE numbers for "ProtST on PK-BPO", spanning 5.75x, none reconciled anywhere

verdict: **FRAME-UNKNOWN** (each is internally sourced; no document compares them)

| value | what it is | where | frame |
|---|---|---|---|
| **+0.0016** | ProtST as a reranker feature, PK-BPO | BP_TECHNIQUE_LEVERS.md:89 (2026-07-16) | rankpct frame, baseline 0.1255, RETRACTED |
| **+0.0092** | same lever, PK-BPO, seed 42 | protst_ab/AB_RESULT.md (2026-07-13) | sealed 227->230, armA pk-bpo 0.3433, 64 feat, K=30 |
| **+0.0059** | same lever, PK-BPO, seed 7 | protst_ab/AB_MULTISEED (in AB_RESULT.md) | as above |
| **+0.0083** | same lever, PK-BPO, protein-level paired bootstrap, CI [0.0017,0.0153] | AB_RESULT.md rigour section | a DIFFERENT statistic from the +0.0092 above (see F13b) |
| **+0.029** | ProtST as a RETRIEVAL SPACE, pk-bpo (0.09343 vs champion 0.06445) | protst_repr/REPR_RESULT.md (2026-07-13) | kNN-only, no reranker, seed 42, receipt gone |
Ratio between the smallest and the largest reranker-feature reading: **5.75x**
(+0.0016 vs +0.0092), and they are dated **three days apart**.
The thesis publishes the smallest. The SIGNAL-REGISTRY promotes the largest.
No document on this disk puts the two side by side.

And the same PK-BPO absolute reads FOUR ways:
    0.1255  BP_WALL_CHARACTERIZATION.md (rankpct, retracted)
    0.2131  thesis 06_evaluation.tex ("The reranker delivers 0.2131")
    0.2181  the real board, BP_WALL_CHARACTERIZATION.md standing table (PROTEA #3, TransFew 0.2943)
    0.3433  AB_RESULT.md arm A
This is the frame problem the audit brief names, and it is 2.7x end to end.

## F16b. Two coverage numbers for the same column

- `AB_RESULT.md`: "protst_text_score finite on ~60% of BP candidate rows (eval 60.5%,
  train 59.7%)"  [2026-07-13]
- `BP_WALL_CHARACTERIZATION.md:49`: "protst_text 0.64 but on **41% coverage**"  [2026-07-16]
Three days apart, same column, 60.5% vs 41%. One of the two conditions on a different row
population (all candidates vs PK-BPO candidates) and neither says which. A feature's AUC
computed on 41% of rows and its delta computed on 60% of rows are not the same experiment.

---

# Part 4: the platform side (audited against worktrees/protea-deploy, HEAD a5de702 2026-09-01)

## F17. One platform gap the A/B named is CLOSED; a new one has opened underneath it

verdict: CONFIRMED (closed) + **CONTRADICTED** (a second ProtST config now exists)

CLOSED. `AB_RESULT.md` "## Platform-export follow-up" said `compute_protst` "is wired into
ExportParityFlags/TrainRerankerAutoPayload but NOT into ExportResearchDatasetPayload
(missing on 03714ec/develop/main)... Until then the platform export cannot emit protst
columns." On the deploy tree today:
    protea/core/operations/export_research_dataset.py:85   `compute_protst: bool = False`
    protea/core/operations/export_research_dataset.py:357  `"compute_protst": p.compute_protst,`
    protea/core/training_dump/_payload.py:85               `compute_protst: bool = False`
    protea/core/features/_bindings.py:365-366              binds all 3 columns to family "protst_text"
    protea-contracts/src/protea_contracts/feature_schema.py:264
        `"protst_text": ["protst_text_score", "protst_vote_fraction", "protst_present"]`
  So the family IS declared in the contract and the export flag IS plumbed. Registry item 10
  ("`protst_text`: a fourth declared-but-unenrolled family") is accurate on the word
  DECLARED; ENROLLED I cannot check without a trained model, and I did not touch the DB.
  Also `origin/main` vs `origin/develop` agree on `feature_schema.py` for protst (empty diff),
  so the contract fork does NOT bite this family.

NEW GAP. **There are now TWO ProtST embedding configs and they disagree on `normalize`.**
  - served / measured-against:
      `protea/core/operations/predict_go_terms/_protst_text.py:58-62`
      "#: Canonical ProtST API EmbeddingConfig (model_backend=protst, 512-d
        ``protein_feature``, **``normalize=false``**, ADR-D35)."
      `DEFAULT_PROTST_CONFIG_ID = "bd3cd470-e384-4f6a-90cf-574704419373"`
      This is the bank the +0.0335 screen used ("ProtST bank EmbeddingConfig
      `bd3cd470-e384-4f6a-90cf-574704419373`, dim 512", REPR_RESULT.md) and the one the A/B
      enriched from ("the canonical ProtST bank `bd3cd470`").
  - rung-1 grid cell, seeded later:
      `alembic/versions/f2b8d1c6a94e_seed_t5_and_protst_cells.py` (Create Date 2026-07-31),
      GRID entry `("4d5d29ee-5a8c-53d2-bdc2-080187971454", "protst", "mila-intel/ProtST-esm1b",
      "protst", "protst", False)` with `STD = {..., "**normalize": True**, ...}`.
  Same model_name, two ids, opposite `normalize`. And the screen's whole (b) finding was that
  per-dimension z-scoring is worth +0.0030 -- a normalisation effect of the same order as the
  difference between these two configs.
  The migration's own docstring says the quiet part: "ProtST is NOT [comparable]. Its backend
  returns the whole-protein ``protein_feature`` projection (512-d, text-aligned)... pooling,
  layer selection, max_length and chunking do not apply... a reader comparing it to the T5 and
  ESM cells is comparing a different kind of representation, not a bigger one."
  **That is the platform warning against exactly the comparison the leakage study makes**
  (ProtST vs 7 sequence-only backbones in one panel).

CONSEQUENT HAZARD IN THE LEAKAGE SCRIPT (live, checkable, no DB needed):
  `97_protst_text_leakage.py` selects arms by NAME, not by config id:
      JOIN embedding_config ec ON ec.id=ps.embedding_config_id
      ... ORDER BY ec.model_name, np DESC
      for m, pid, snap, np_ in rows:
          if np_ != POP or m in seen: continue
  With two ProtST configs sharing `model_name = 'mila-intel/ProtST-esm1b'`, whichever
  prediction set the ORDER BY happens to reach first wins, and the script cannot tell the
  normalised bank from the unnormalised one. This is `feedback_assert_the_population_not_order_by`
  in its exact form. The script does pin `np_ != POP` (22,498), which is a real guard on
  population -- but it is not a guard on WHICH ProtST.
  I did NOT connect to the database, so I cannot say whether both configs had a
  22,498-protein prediction set on 2026-08-23. That check is one query and it is the first
  thing anyone re-running this should do.

## F18. Platform gap summary for this slice

| claim | reborn as an operation? |
|---|---|
| ProtST as a retrieval space (+0.0335, 9 cells) | **MURO as written.** Needs (i) an op that materialises an embedding bank for an accession list from an `embedding_config_id`, (ii) an op that runs top-k GO-transfer vote + cafaeval per cell writing `evaluation_result`. The bank, the champion codes and the report JSON are all gone. |
| ProtST as a reranker feature (+0.0088 mean9) | **CLOSE.** `compute_protst` is plumbed end to end (payload -> export -> producer -> contract family). The missing piece is that nothing writes the A/B itself: there is no operation "train two boosters differing only by an EXCLUDE set and emit the 9-cell delta with CIs". |
| the text-leakage split (described vs undescribed) | **MURO.** Needs an op that reports, for a constructed evaluation set, the fraction of each knowledge cell carrying `protein_uniprot_metadata.function_cc`. **This is the cheapest and highest-value operation in the whole slice**: it is one COUNT, and its absence let F7's false deduction stand for 46 days across four documents. |
| reachability at a term budget, by band | **MURO.** No operation computes it; it exists only as `storage/encoder-study/scripts/8x-9x_*.py` reading the DB by raw SQL. |
| crossobo native delta (227->230) | **SPECIFIED, NOT RUN.** The plan's A1/A2/A3 is a correct three-operation chain (`load_ontology_snapshot`, `generate_evaluation_set` with an EXPLICITLY DIFFERENT pivot, `run_cafa_evaluation`). Blocked on the t1 OBO `releases/2026-01-23`, which is not on this disk. |

---

# Part 5: the echo chain, and what I searched

## F19. "NK had no function text" propagates through SIX documents; none of them counts

Every one of these asserts the same unmeasured premise. Only the FIRST is a source; the rest
are echoes, and two of them explicitly claim the premise is auditable.

1. `agent-farm/plans/text-evidence-scorer/PLAN.md` (2026-07-08, git cc8eacc) --
   "NK fully clean (no function text existed)" / "NK proteins had **no function text at t0**
   -> fully clean, zero asymmetry (the strongest, primary result cell)"
2. `memory/project_text_evidence_scorer_2026_07_08.md:20` --
   "NK proteins had NO function text at t0 -> NK cell is the FULLY LEAKAGE-FREE anchor."
3. `repositories/protea-reranker-lab/research/text_scorer/WRITEUP.md`, Protocol --
   "NK is the leakage-free anchor (those proteins had no function text at t0)";
   Result 1 -- "nk-BPO +0.062 (leakage-free)"
4. `.../research/regen_headline/protst_ab/AB_RESULT.md` --
   "NK-BPO (leakage-free anchor) +0.0284 ... **the lift is the ProtST TEXT signal, not leakage.**"
5. `agent-farm/plans/thesis-clean-iteration/SIGNAL-STORE.md` --
   "**Provenance**: `{model, base_plm, text_encoder, training_text_source, license, pub_date}`
    so the leakage argument (model published before t0, **NK proteins had no function text**)
    is explicit and auditable, **not tribal knowledge**."
   -- the document that demands auditability records the unaudited premise as the thing to record.
6. `agent-farm/plans/thesis-pillars/PILLARS.md` -- carries the +0.062/+0.072 nk/lk-BP figures
   forward into the thesis pillar without the qualifier.

The count that refutes it (`97_leak.log`, 2026-08-23, **81.9%**) exists in exactly ONE place
and was never propagated back into any of the six. The registry, the plans, the lab writeups
and the thesis all still read as if NK were clean.

## F20. The negative checks -- what I searched, so the nulls count

Receipt hunt (all absolute paths, all read-only):
  `find /home/xaxi/Thesis2 -maxdepth 6 -name 'regen_headline*'`     -> 4 hits, none under storage/
  `find /home/xaxi -name '*protst_repr*'`                            -> dir + 1 .py, no report.json
  `find /home/xaxi/Thesis2/storage -iname '*protst*'`                -> 2 files, both encoder-study scripts
  `find /home/xaxi -name 'knn_confirm_text_result.json'`             -> 0
  `find /home/xaxi -name 'knn_confirm_protrek_result.json'`          -> 0
  `find /home/xaxi -name 'knn_triple_result.json'`                   -> 0
  `find /home/xaxi -name 'stratify_identity_result.json'`            -> 0
  `find /home/xaxi -name 'stratify_protrek_result.json'`             -> 0
  `find /home/xaxi -name '*34a634a8*'`                               -> 0
  `find .../protea-reranker-lab/research -type f -name '*.json'`     -> **0 of 314 files**
       (the tree is 224 .py + 73 .md + 17 .sh, and `.gitignore` excludes `runs/`, `outputs/`,
        `*.log`, `datasets/*/*.parquet`. **Every "Receipt: X.json" in every lab writeup is a
        dangling pointer.** This is systemic, not specific to ProtST.)
  storage/ subdirectories the lab documents point at:
       storage/text_scorer/  ABSENT      storage/regen_headline/  ABSENT
       storage/layer_ablation/ ABSENT    storage/fullgo_models/   ABSENT
       storage/ensemble_audit_2026_06_13/ ABSENT
       (what storage/ DOES hold: probe 347G, encoder-study 16G, rescue 3.7G, encoder 2.6G,
        ontology-drift 60M, logs 82M, calibration-study 5.6M, throughput 1.4M,
        scorecard 300K, worktree_salvage 48K, coordination 344K. So storage/ was
        partially restored, and what survived is the ENCODER STUDY, i.e. the leakage side,
        not the headline side.)
  `find /home/xaxi/Thesis2 -name 'go-basic.obo'`                     -> 1 (t0 only; t1 missing)
  `grep -rn '0.24849'` over plans + storage + memory + repositories + thesis
       -> **exactly ONE hit, SIGNAL-REGISTRY.md:165**. The headline figure appears nowhere
          else on this machine, not even in the document it is sourced from (REPR_RESULT.md
          prints 0.2485 in its table and 0.24547 for raw in prose).
  `grep -rn -i 'protst' /home/xaxi/Thesis2/thesis --include='*.tex'` -> **0**. The thesis never
       names ProtST; it appears only as "a text-aligned representation" (06_evaluation.tex:886),
       consistent with the no-identifiers-in-published-prose norm.
  `git log -- plans/SIGNAL-REGISTRY.md` -> one commit, f0e50a6, **2026-07-27**. Never updated
       after the 2026-08-23 leakage finding or the 2026-08-27 wipe.

## SUMMARY: what was really measured, what was deduced, what was lost

MEASURED, receipt present, frame stated:
  - the leakage panel itself (`97_leak.json` / `97_run.out`, 2026-08-23): 10 backbones,
    reachability at budget 25, NK 220->230, described vs undescribed with paired bootstraps.
    This is the only ProtST result in the slice whose numbers I could read off disk.
  - the backbone spread by band (`98_spread.json`): twilight 0.08418 -> 0.06251 with ProtST
    removed, n=778; identical in the other three bands. Budget 10, 8 arms.
  - the LAFA 7401 frame and its 399/868/6340 cells (counted here from the .tsv files).

DEDUCED AND COUNTED AS MEASURED (the requested output):
  - **"NK proteins had no function text at t0"** -- the leakage clearance for the whole ProtST
    programme, asserted in six documents, never counted, and measured FALSE at 81.9% (F7, F19).
  - **"the lift is the ProtST TEXT signal, not leakage"** -- a conclusion drawn from that
    premise via a control that does not control (F13).
  - **"0 of 9 among the undescribed"** -- the receipt says 1 of 9, and the ninth row was
    dropped from the table (F3).
  - **"it inverts against the two strongest rivals"** -- both inversions have intervals
    spanning zero, and neither arm is the strongest rival (F5).
  - **"the twilight spread is 0.0835 with and without"** as corroboration -- a max-minus-min
    statistic that is blind to the effect in question, with no artifact on disk (F6).
  - **"a text-aligned representation adds +0.002"** in the thesis -- +0.0016 measured in the
    `rankpct` frame the registry declares invalidates every lever measured against it (F15).

LOST:
  - the entire `storage/regen_headline/` and `storage/text_scorer/` artifact sets, so the
    +0.0335 retrieval-space headline, the triple-combine +0.044, and every ProtST/ProTrek
    kNN receipt survive as prose only.
  - the prediction sets the leakage study read (wiped 2026-08-27), so even the one measured
    result cannot be re-run.
  - the crossobo 7002-side parquet, both lab OBOs, and eval set 34a634a8.

THE ONE SENTENCE: **the receipt the registry calls its largest unexploited lever does not
exist on this disk, and the leakage study that is supposed to contradict it never scored the
comparator the lever is measured against -- so the headline is unreceipted and the refutation
is untargeted, while the premise both of them share (that NK is text-clean) is the one thing
that was actually measured, and it is false.**

## F21. Postscript: the NK cell is 3,031 in one document and 399 in another

Not an error, but anyone reading these documents together must not merge them:
  - leakage study (220 -> 230): NK = **3,031** proteins, of a prediction-set population of
    22,498 (13.5%).  `97_leak.log`, `categories_220_230.pkl`.
  - LAFA official frame (227 -> 230, Sep_2025_Mar_2026): NK = **399** proteins of 7,401
    (5.4%).  Counted here from `groundtruth_NK.tsv`.
  - the reranker A/B (227 -> 230): 7,575 eval queries.
Three different NK cells, three different windows, three different denominators. The 5%
figure the audit brief cites is the LAFA one. Every ProtST number in Part 1 and Part 3 is on
the 227->230 frame; every number in Part 2 of the leakage study is on 220->230. No document
in this slice states the window next to the number.
