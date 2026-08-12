# PEER-LOG

Append-only log of findings that one machine needs the other to know. There is no direct channel
between the two, so git is the medium. Add entries at the end, dated and attributed to a machine.
Never edit or remove somebody else's entry.

---

## 2026-07-30, laptop (server, 192.168.18.121)

First entry from the server side, answering the questions in the host brief.

### Path layout on this machine differs from the instructions

The brief refers to `~/Thesis2/CLAUDE.md`, `~/Thesis2/repositories/PROTEA/` and
`~/Thesis2/agent-farm/`. **None of those exist here.** On this machine the layout is:

    ~/Thesis-laptop/CLAUDE.md
    ~/Thesis-laptop/PROTEA/
    ~/Thesis-laptop/agent-farm/

There is no `repositories/` level. The override that makes agent-farm scripts work against this
layout is `agent-farm/farm.env`, which sets `THESIS_ROOT`, `AGENT_FARM_ROOT`, `PROTEA_REPO` and
`DEPLOY`. It is untracked. Two consequences worth deciding: any instruction written with `~/Thesis2`
paths will fail here, and `cold-boot.sh` hardcodes `DEPLOY` at line 34 unconditionally, which
defeats that override.

`~/Thesis-laptop/CLAUDE.md` did not exist before today. It has been created with the server role
section. As the brief anticipated, it is tracked by nothing: it sits above both clones, so no
repository versions it and the desktop cannot read it.

### GPG key B5690EEEBB952194 is NOT on this machine either

This is the answer nobody wanted. The signed history cannot be continued from here.

    gpg --list-keys B5690EEEBB952194   ->  error reading key: no public key
    ~/.gnupg/pubring.kbx               ->  32 bytes, an empty keyring header
    git log -1 --show-signature (agent-farm)
        gpg: Signature made Tue 28 Jul 2026 12:59:32 CEST
        gpg:                using RSA key B5690EEEBB952194
        gpg: Can't check signature: No public key

The 238 signed commits remain verifiable by anyone who holds the public key, and their signatures
are intact in the objects. What is lost, unless a copy exists elsewhere (a backup, a keyserver, an
exported subkey, another machine), is the ability to sign new commits with that identity. Worth
checking `keys.openpgp.org` and any old backup before treating it as gone.

### Git identity

    PROTEA repo (local):   Francisco Miguel Perez Canales <frapercan1@alum.us.es>
    agent-farm (local):    not configured
    global:                not configured
    user.signingkey:       not configured anywhere
    commit.gpgsign:        not configured anywhere

Commits made on this machine today are unsigned. agent-farm had no identity at all until this
entry was committed.

### The eight gigabytes are GRAPHICS memory

CAMPAIGN section 5 lists this as an open question to settle before rung 1. Settled, with evidence.

    nvidia-smi
      NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB total, 5196 MiB free, driver 595.71.05

    lspci | grep -iE 'vga|3d'
      00:02.0 VGA compatible controller: Intel Raptor Lake-P [UHD Graphics]
      01:00.0 VGA compatible controller: NVIDIA AD107M [GeForce RTX 4060 Max-Q / Mobile]

    free -g
      Mem: 30 total, 11 available

So the laptop has **8188 MiB of VRAM and 30 GB of system RAM**. The envelope that prunes the grid
is the graphics memory, not system memory, and bf16 is supported.

Note the part number: **AD107M, the Max-Q / Mobile variant**. Its power envelope is low and it was
observed drawing 27 to 45 W. Under sustained load this machine thermally throttles: with the
chassis at 94 to 97 C the GPU held 1350 MHz, and once the room was cooled and the case reoriented
it reached 1785 MHz at the same 87 C with throttling cleared. Any throughput figure measured on
this machine should record the thermal state alongside it, or it will not reproduce.

Measured here on the full 528,294 sequence corpus at max_length 2048, mean pooling, batch size 4
(2 for ankh-large): esm2-650m and esmc-600m peaked around 1.8 GB, ankh-base 3.8 GB, ankh-large
5.0 GB at batch size 2 and 7.1 GB at batch size 4, which leaves 577 MiB and is not a fluid fit.
prot-t5 and prostt5 OOM at batch size 4 and need 6.3 GB at batch size 2. esm2-3b does not load at
all: the backend calls `from_pretrained` without `torch_dtype` and then casts, so 10,815 MiB of
fp32 weights hit the card before the cast.

That last point matters for the desktop: **esm2-3b needs the compute node**, and the node will hit
the same loader problem on any card under about 24 GB unless the dtype is passed at load time.

### The three open pull requests

Reviewed, not merged. None of them touched.

**#241 docs(topology)** is mergeable, eight checks, none failing. Read in full. The description of
the split matches what this machine observed independently: the node was down for about two hours
on 2026-07-29 in the middle of the embedding run, the queue held, and throughput halved rather
than the run failing. Confirmed from this side: the consumer count on `protea.embeddings.batch`
went from 2 to 1 and back to 2 without intervention, no message was dead-lettered, and no batch was
redelivered.

**#239 plan(ledger)** is mergeable, eight checks, none failing.

**#240 feat(services)** is mergeable but **two checks fail, both the same root cause**:
`pytest` fails on `tests/test_features_surface.py::test_coverage_gate_passes_on_main` with
`assert 1 == 0` (1 failed, 581 passed, 3 skipped), and `features-coverage` fails directly.
The gate at `scripts/check-features-coverage.sh` fails when a new persistent service under
`scripts/services/*.sh` has no `docs/features/<name>.md` referencing it in `source:`. The PR adds
`scripts/services/protea-lab-worker.sh` and documents it at `scripts/services/README-lab-worker.md`,
which is not where the gate looks. The fix is a `docs/features/protea-lab-worker.md` carrying a
`source:` entry for the script, plus a re-render of `docs/features/README.md`, which the same gate
checks for staleness. Not applied from here: the branch belongs to the other machine.

(There is also **#232 plan(contextual-generation)**, outside the brief: mergeable state unknown,
the `check` job failing.)

### Queues on the server today

Every queue has its consumer, and the write stages are all here as the topology requires.

    protea.jobs                4 consumers   all local
    protea.embeddings          1             local
    protea.embeddings.batch    2             1 local + 1 from 192.168.18.132
    protea.embeddings.write    1             local
    protea.predictions         1             local
    protea.predictions.batch   1             local
    protea.predictions.write   1             local
    protea.evaluations         1             local
    protea.training            1             local
    protea.ping                1             local
    protea.dead-letter         0             correct, nothing consumes it

**Exactly one local consumer on `protea.embeddings.batch`**, as instructed. No consumer was added
there. The `protea.jobs` count is 4 because three were added deliberately to parallelise ontology
snapshot loads while a long metadata job was running; they are idle now and can be reduced.

### State the server holds, as of this entry

    proteins        616,846   (575,503 canonical, 41,343 isoforms)
    sequences       528,294   after MD5 dedup
    metadata        575,503   one row per canonical accession
    GO snapshots         10   479,990 terms

    GOA annotation sets, each bound to its own congruent snapshot
      v226  5,907,336   releases/2025-03-16   published 2025-05-03
      v227  5,880,402   releases/2025-07-22   published 2025-09-04
      v230  4,771,370   releases/2026-01-23   published 2026-03-04

    rung-1 embedding grid, identical recipe across cells
      esm2_650m   ab430e07   528,294  complete
      ankh_base   0868f1ff   528,294  complete
      esmc_600m   f64daa67   528,294  complete
      ankh_large  9f52de2b   104,832  running

Zero EvaluationSet rows: the GOA loads were dispatched in descending release order so that
`_select_prior_annotation_set` never found a strictly older set, which suppressed the automatic
pairwise evaluation sets that would otherwise have been created under the retired ground-truth rule.

### Two measurements the run should carry forward

**The byte proxy is inverted against the scored population.** File size says one thing, the
annotations that are actually scored say close to the opposite:

    window         gaf.gz bytes    scored annotations
    v226 -> v227      -30.88%           -0.46%
    v227 -> v230       -1.40%          -18.86%

CAMPAIGN section 2 rules out v226 to v227 as a calibration window because it is one of the two
thirty percent contractions. On the population that is scored, that window barely moves. The real
contraction sits in the board's own validation window.

Decomposed, and restricted to the evidence codes the board scores
(`EXP,IDA,IPI,IMP,IGI,IEP,HTP,HDA,HMP,HGI,HEP,IC,TAS`):

    window         all evidence            scored regime
                   added     removed       added    removed
    v226 -> v227   57,352    172,085       8,687     9,980
    v227 -> v230   79,722  1,176,644      11,678    11,329

The eighteen percent contraction is almost entirely IEA. In the scored regime the board window is
net positive. Removals are the same order as additions in both windows, which is the empirical
reason the first-appearance rule is load bearing rather than a refinement.

**The v230 under-load was never a loading defect.** It reproduces at -18.86% on a clean run with
correct per-release snapshot binding and numeric source versions, against the -18.87% recorded
earlier. It is a property of the corpus. The note that treats it as a loading bug should be
corrected.

**Restoration rate on the board window**, scored regime, with v226 as the single prior cut:
11,678 apparent additions, 143 of them already present at v226, giving **1.22 percent** and 11,535
genuine first appearances. D-02 recorded about one percent over eleven releases. Depth one only
catches dormancy-one restorations, so the true rate at greater depth is higher.

A caveat that gates all of it: these were computed in ad-hoc SQL, not by a registered operation, so
they are findings and not yet campaign deliverables. Slice 3 still needs the decomposition as a
dispatchable operation. Note also that `go_term_id` is snapshot specific, so comparisons across
releases must join through `go_term` and compare the `go_id` string.

### One correction to CAMPAIGN section 5

It states that restricting the grid to backbones that fit costs "roughly a tenth of the proxy
against the best backbone available". No cross-PLM correlation-proxy table exists anywhere in the
tree to support that. The only volume-matched evidence found (FARM-EXP.15, `knn_226_227_fmicrow.csv`)
puts all eight backbones within 0.0378 on a base of about 0.44 at K=10, under nine percent between
best and worst, so the gap between best-fitting and best-overall must be smaller still.

Related: section 5 excludes esm2-150m as "measured as an unfaithful substrate", citing a memory
that is not in the store. The one receipt that does exist ranks it second of eight with an outright
per-cell win on lk-mfo at 0.5870, and the same receipt puts the largest model last. Francisco chose
to keep it excluded and respect the section as written. Recording the discrepancy here so the
decision is visible rather than inherited.

---

## 2026-07-30 (later), laptop (server, 192.168.18.121)

Server side of the first mechanism receipt. Steps 1 through 5 done, step 6 waiting on the
prediction.

### The public exposure is real, but reset-db is NOT reachable

Confirmed from the public network, read-only probes, nothing destructive invoked:

    https://protea.ngrok.app/api-proxy/v1/auth/api-keys   200
    https://protea.ngrok.app/v1/auth/api-keys             200

`PROTEA_AUTHN_REQUIRED=false` in the live API process, and `roles.py:61` maps a `None` principal to
`ROLE_ADMIN`, so any visitor is an admin. That part of the report is correct.

**The claim that `POST /v1/admin/reset-db` stays reachable is not.** It carries two guards beyond
the role check, at `protea/api/routers/admin.py:39`, and the docstring gives the reason ("The live
DB has been wiped four times"):

    if principal is None:
        raise HTTPException(401, "reset-db requires a real authenticated admin principal;
                                  the dev no-auth fallback is not accepted for this
                                  destructive operation")
    if os.getenv("PROTEA_ALLOW_DB_RESET") != "1":
        raise HTTPException(403, "reset-db is disabled")

The dev fallback is explicitly rejected there, and `PROTEA_ALLOW_DB_RESET` is not present in the
live API process environment (checked via `/proc/<pid>/environ`). `DROP SCHEMA` is unreachable.

### What IS open, which is the part that matters

Every route gated on `operator` or `admin` is reachable by anyone:

    POST   /v1/auth/api-keys                      mint a real admin API key
    POST   /v1/maintenance/vacuum-sequences       "Delete sequences not referenced by any Protein"
    POST   /v1/maintenance/vacuum-embeddings      "Delete embeddings for sequences not referenced"
    DELETE /v1/embeddings/configs/{id}            would delete the seeded rung-1 grid configs
    DELETE /v1/embeddings/prediction-sets/{id}
    DELETE /v1/jobs/{id}
    DELETE /v1/scoring/configs/{id}, /rerankers/{id}
    DELETE /v1/query-sets/{id}, /experiment-runs/{id}, /reranker-models/{id}
    DELETE /v1/auth/api-keys/{id}

There is also an escalation chain worth seeing whole: minting a key yields a real principal, which
satisfies reset-db's first guard. Only the `PROTEA_ALLOW_DB_RESET` sentinel then stands between a
visitor and `DROP SCHEMA`. It is unset today, so the chain breaks, but it breaks on one environment
variable.

### Proposed closure, preserving open reads

One line, at `protea/api/roles.py:61`:

    if principal is None:
        return ROLE_VIEWER      # was ROLE_ADMIN

Reads stay open, since GETs and the viewer-gated routes are unaffected. Everything requiring
operator or admin closes. It needs an API-only restart, not a stack restart. Two companions: never
define `PROTEA_ALLOW_DB_RESET` on this host, and apply the same reject-null-principal pattern to
the two vacuum endpoints and to key minting, which are the routes that delete data.

Not applied. It is Francisco's call, and applying it would also have blocked steps 2 through 5,
which need the operator role.

### Steps 2 to 5

**Scoring presets** created, HTTP 201, seven of them: embedding_only, vote_fraction,
alignment_only, embedding_plus_alignment, embedding_plus_vote, evidence_veto, composite.

**The three identifiers were verified against this database before dispatching**, since the pivot is
the irreversible decision:

    41b31f10-7a23-430f-adee-af555c85e244  ->  annotation_set v226
    8f4d6c89-9188-4e56-924f-cb57af6fdf0e  ->  annotation_set v227
    bfa1d095-d618-4c01-a8b2-62f3b5569f16  ->  ontology_snapshot releases/2025-03-16

The pivot is v226's own snapshot, which is the term universe the model could know at t0. Dispatched
with exactly the three fields specified: no `window_role`, no native-snapshot overrides.

**Event trail confirms the frame.** `mode = "reconciled"`,
`pivot_ontology_snapshot_id = bfa1d095-d618-4c01-a8b2-62f3b5569f16`, and the old and new snapshot
ids resolve to v226 and v227 respectively.

    evaluation_set_id     8e464c85-7ac0-4251-abbf-7bb252d4f66f
    delta_proteins        6,216       not zero, so the run continues
    nk_proteins             523       nk_annotations   9,860
    lk_proteins             622       lk_annotations   8,811
    pk_proteins           5,331       pk_annotations  32,187
    removed_proteins     13,059
    removed_annotations  75,421
    known_terms_count 3,652,485

`removed_proteins` and `removed_annotations` are recorded here because this operation is the only
surface that reports them. Note that the category counts do not sum to `delta_proteins`: NK is a
per-protein category while LK and PK are per (protein, namespace), so a protein can contribute to
both LK and PK. 6,216 minus 523 NK leaves 5,693 proteins spread across 5,953 LK-or-PK pairs, which
is consistent.

### No cohort leak

Read back from the API, not from the write event:

    known-terms.tsv        3,652,485 rows   equals known_terms_count exactly
    ground-truth-PK.tsv       32,187 rows   equals pk_annotations exactly
                               5,331 unique proteins, equals pk_proteins exactly
    delta-proteins.fasta       6,216 records, 6,216 unique headers

**The FASTA record count equals `delta_proteins` exactly.** The accession versus
canonical_accession hypothesis does not materialise: had the 41,343 isoform rows leaked in, the
FASTA would carry more records than the cohort. Headers also carry the category, for example
`>A0A031WDE4 HYPD_CLODI OS=Clostridioides difficile OX=1496 (PK)`, so the label travels with the
sequence.

### One assumption in the plan that does not hold on this host

Section 3 states the artifact store is local filesystem on whichever machine executes, and reasons
about which stages must run where on that basis. **On the server it is MinIO.** The canonical secret
bundle here sets `PROTEA_STORAGE_BACKEND=minio`, and the ground truth landed at

    s3://protea/eval_groundtruth/8e464c85-7ac0-4251-abbf-7bb252d4f66f/groundtruth.parquet

This is better than the plan assumes, since the artifact is reachable from both machines through the
object store rather than being invisible on one filesystem. But the placement argument in section 3
rests on a premise that is false here, and should be rechecked before it is relied on again.

### Step 6 is armed and waiting

Scoring will use `band="v226"` with `leakage_role="probe"` and an absolute `ia_file` path verified on
this machine, band and ia_file together. The gate will be the existence of the metric, not the job
status, since the scorer reports success on an empty result.

---

## 2026-07-30 (third entry), laptop (server, 192.168.18.121)

Design study, no code written and nothing dispatched. Francisco asked whether the scorer could be
adjusted to give four-axis stratification while reusing computation and keeping the complexity out of
the platform. It can, in one pass. The design was then attacked and the attack found that its safety
gates do not work. Both halves are worth carrying.

### Where the four axes stand today

Two of four. The scorer stratifies on category (three ground-truth files) and aspect (its per-namespace
loop). Length band and homology band are not expressible in the CAFA file format.
`protea/core/strata.py` is written and tested and has ZERO production callers, but the inputs it needs
are all stored per prediction row and populated by default: `length_query`, `identity_nw` /
`identity_sw` (`compute_alignments` defaults to True in `config/tuning.py:351`), and the donor
`evidence_code`. So the missing piece is wiring, not capture.

### The seam, and why one pass is enough

In `cafaeval/evaluation.py` the per-protein arrays survive to the end: `pred_at_tau` and `tp_at_tau`
at :222-223 (NK/LK) and :334-335 (PK) are dense `(n_prot, n_tau)`, and all six output columns are a
`.sum(axis=0)` over them. Segmenting that final collapse yields every cell from ONE propagation pass.
Measured cost: about 2 MFLOP per call, against a propagation measured in seconds.

Three arithmetic facts shaped the design, each verified numerically rather than argued:

**One integer label per protein is a sufficient statistic for every marginal.** I had claimed the
opposite in the brief, reasoning that a protein belongs to its length band and its homology band at
once. That is true only if the scorer normalises, and it does not: all six raw columns are sums over
proteins and `ne` is a protein count, so every marginal is the elementwise sum of the cartesian cells
composing it. Verified to 3.3e-16 relative. **Cartesian versus marginal therefore becomes a caller
groupby, decidable after the run and changeable without re-scoring.** The one hard requirement is that
normalisation runs AFTER the caller's aggregation, never before.

**The stratified block must be computed alongside the existing collapses, never replace them.**
Measured: an indicator matmul over a (5331, 99) array agrees BITWISE with `X.sum(axis=0)` on only 9 of
99 columns, max abs diff 1.7e-11. `np.sum` uses pairwise summation; bincount and sparse matmul
accumulate in scatter order. So a design that replaces the collapses and recovers the global by summing
strata cannot pass a bit-identity gate however correct it is. Leaving the existing expressions
byte-for-byte makes parity true by construction.

**Per-stratum `ne` needs no change to `_count_proteins_in_toi` or `normalize`.** Both stay out of the
patch. Verified on a constructed PK case: `_count_proteins_in_toi` returns 258, the kernel's filtered
row space holds 346 rows, and `eligible_rows.sum()` is also exactly 258, because any row dropped from
`proteins_with_gt` has no ground truth in TOI at all and is all-False in both predicates.

Cardinality is **36, not 324**: category is already the ground-truth file and aspect is already the
namespace loop, so encoding either in the sidecar creates two spellings of one partition. The 324 is
9 x 36, assembled by the caller for free.

Interface is a sidecar TSV plus a `strata_file=` kwarg. The three in-band alternatives were each
rejected on evidence: the ground-truth parser does `split()` then `[:2]` so a third column is SILENTLY
DROPPED and is anyway the wrong grain (per annotation, not per protein); the prediction reader is
pinned to three column names so a fourth raises, gets swallowed, and silently falls back to a roughly
10x slower legacy path; the IA parser's strict two-unpack raises and kills the run.

Platform delta: one written file, one None-defaulted context field, one kwarg. `parse_results`,
`_merge_weighted_metrics`, `batch_rescore_evaluation` and `evaluate_external_tool.py` all unchanged,
because the payload rides as a new `dfs_best` key and every reader uses `.get("f")`.

### The attack found the gates are vacuous, and this is the part to carry

The design's headline safety assertion was `ne_k.sum() == ne`, described as "the assertion that catches
label misalignment, which nothing else will". **It catches nothing.**
`np.bincount(labels[eligible], minlength=K).sum()` equals `eligible.sum()` for ANY labels array of the
correct length, because bincount conserves count. Tested with label rolls of 0, 777 and 1554 elements:
all three pass. The remaining gates are permutation-invariant too, either summing over the stratum axis
or comparing the unstratified path. Rolling 777 labels moved the sum over strata by 1.8e-12, float
noise.

So the design had five gates and none could distinguish a correct label vector from a rolled one, on a
feature whose only possible error is the labels.

**The general lesson: a conservation check cannot validate an assignment.** "The parts sum to the
whole" says nothing about which part is which. Worth applying to the other invariants this project
relies on.

**The fix is an independent oracle, and it recycles the route we rejected.** Partition the ground-truth
and prediction files by ONE stratum, run the PINNED scorer on that partition, and compare the RAW
columns (tp, fp, fn, pr, rc), which are partition-invariant sums over proteins. Only `n`, `ne` and
normalisation depend on the cohort, which is exactly why partitioning is wrong for production and right
as a test oracle. Verified exact: difference 0.0, not float noise.

Two further defects, both silent: the multiprocessing unzip was specified as `p[0][0]` where it must be
`p[1][0]`, and concatenating 1-D length-6 arrays succeeds and propagates garbage rather than raising;
and `_cm_worker` / `_cme_worker` were never updated to forward the new globals, so they would return
unstratified output without complaint. Third, the caller-side normalisation uses plain division where
`normalize` uses `np.divide(..., out=zeros, where=denominator > 0)`, so every empty stratum yields inf
or NaN. Empty cells are certain: NK has 523 proteins across 36 cells.

### One trap that would survive all of the above

`feature_engineering.py:95` stores identity as `matches / aln_len`, a fraction in [0,1].
`strata.homology_band_for` expects [0,100] and raises only outside that range, so a fraction silently
collapses every protein into TWILIGHT. The homology axis would flatten to a single level and every
table would still render. This needs a non-degenerate band-distribution assertion at startup, not a
note in a code review.

### The threshold question, and Francisco's call on it

Stratified reporting has to choose whether each cell reports its Fmax at its OWN best tau or all cells
report at the GLOBAL best tau. Francisco's position, which I agree with: **global tau**.

Three reasons, strongest first. Taking a maximum over about 99 thresholds inside each cell is
maximising over noise, and with 6,216 delta proteins spread over 324 cells the median cell holds under
twenty, so every per-cell Fmax would be optimistically biased and worst exactly where the cells are
smallest. It is a distributed version of the disease D-05 diagnoses in the recorded standing. Second,
global tau keeps the cells decomposable: the raw counts sum back to the published number. Third, cells
scored at different tau sit at different precision-recall trade-offs and are not comparable to each
other.

Where I would qualify it: per-cell tau is useless as a SCORE but is a real DIAGNOSTIC. The distance
between a cell's performance at its own tau and at the global tau measures calibration mismatch in that
stratum, which is a finding and belongs to the fourth pillar. Since raw counts are emitted at every tau,
both come out of one run, so the decision can be made when writing. The only unacceptable outcome is
reporting the first while describing it as the second, which the design itself warns "reads correctly
in every table".

### Cost, unchanged by any of this

The seam is inside the kernel bodies, so the cross-repo cascade is unavoidable: clone the fork, patch
`evaluation.py` and `parser.py`, PR, bump the pin from 80d705a, re-lock, reinstall on BOTH machines,
re-run the gates on each. **Between bumping the pin and reinstalling on both hosts, the two machines
run different scorers under the same PROTEA commit**, which is precisely the condition
`SCORER-PROVENANCE.md` blames for a -12.8% to -22.7% f_micro_w move. Pin bump and parity
re-verification have to be atomic per machine.

A monkeypatch path exists that keeps the pin frozen, since cafaeval is a plain module with module-level
functions. It moves the complexity into the platform rather than out of it, which is the opposite of
what was asked for. Cheap, not right.

Nothing here has been implemented, and I would not implement it until the partition oracle exists,
because without it the feature ships with no net.

---

## 2026-08-12, laptop: the coordination mechanism is closed, and four things the runbook omits

Written from the laptop after acting on the desktop's handoff. Three of the four asks are done, one
is partial and says so.

### The first real cross-machine claim

A message was sent from this machine and claimed by the desktop in about twelve seconds, under the
twenty second bar the handoff set:

    message_id     01KZVCABET1SSSQR61PY2TVG48
    sent           16:19:05Z
    claimed        16:19:22Z   claimed_by desktop, epoch 1, state claimed
    ledger_commit  2967a878

Everything verified before today was the desktop talking to itself. This is two machines, a real
remote, and GitHub as the arbiter. The pulse published fifteen seconds later carries
`ledger_sha 2967a878`, the same commit, so both machines agreed on the ledger tip in the same second
the claim landed.

### Four things the runbook does not mention, in the order they bite

**Git identity is a hard prerequisite and it fails late.** `coord-send.sh` aborted with "author
identity unknown" after doing its work, at `commit-tree`. The keeper needs the same identity to
write claims, so on a fresh machine the service would fail on its first eligible message and the
only evidence would be in the journal. Set `user.name` and `user.email` in BOTH clones before
enabling the unit, or add the check to the supervisor's exit-78 path where the missing-clone check
already lives.

**The scripts and the amendment live on different branches of the same repository.** `scripts/coord/`
is on `main`, `plans/RUNG2-AMENDMENT.md` is on `plan/rung2-amendment`. With one working tree you
cannot hold both, and switching to read one removes the other. This is not hypothetical: checking out
`main` to get the coord scripts deleted the amendment out from under a review that was reading it,
and fifty six percent of that review's verdicts were produced by readers that no longer had the
document. Use `git worktree` for the amendment, or the next reader repeats the mistake.

**The paths differ between machines and every default assumes the desktop's.** The unit, the fence
and the sender all hardcode `$HOME/Thesis2/...`. On the laptop the tree is `~/Thesis-laptop`. Rather
than add one override per script forever, `~/Thesis2` is now a symlink to `~/Thesis-laptop`, so the
runbook's commands are literally correct on both machines. Reversible with `rm ~/Thesis2`.

**The proposed capabilities are wrong for this machine.** The handoff proposed
`platform postgres broker storage cpu`, reasoning that "the laptop has the platform, not the card".
The laptop has an RTX 4060 and was computing ProtST embeddings while the handoff was being read. The
declared set is now `platform postgres broker storage cpu gpu cuda`. What is true is that the card is
capped at 45 W by firmware and runs at roughly half its nominal clock, so it contributes a fraction
of the desktop's throughput. That is a weight, and `requires` is a boolean, so excluding `gpu` would
have permanently routed away work this machine demonstrably does.

### The forward pass fraction, measured

The handoff asked for this number before `embed_chunks_multi` is written, because the whole argument
rests on the pass dominating. Instrumented at `compute_embeddings.py` (PROTEA `77af263`) and measured
over six batches:

    total per batch      65.28 s
      forward pass       64.23 s
      model load          1.045 s
      serialize           0.002 s
      unaccounted         0.006 s
    INFERENCE FRACTION   0.9838

The three phases account for the batch almost exactly, so there is no fourth sink hiding. At 0.9838,
emitting twenty configurations from one pass saves on the order of ninety three percent of twenty
passes, and the "billing, not compute" framing holds.

**The caveat matters as much as the number.** This was measured on ProtST, which is the cheapest
backend in the grid: a 512-d whole-protein projection, one chunk per sequence, no residue-level work.
A chunked or multi-layer configuration moves tensor work out of the pass, so 0.9838 is plausibly an
upper bound. The honest reading is that the fraction is high enough to justify building the emitter,
and that the figure should be re-measured on a genuinely chunked configuration before it is quoted as
the saving. No such configuration exists yet, which is the amendment's own point.

### PR #243: eight findings that survive with the document present

The review was run at the wrong scale and half of it is discarded for the reason given above. Of the
forty nine verdicts produced by readers that had the document, thirty four confirm and fourteen
refute. The eight that carry decisions:

1. **The grid has one axis, not three.** All three seed migrations freeze an identical STD block and
   vary only `model_name` and `model_backend`. Depth, chunking and pooling are constant across all
   eight seeded configurations. The amendment's framing of pruning axes describes a grid that was
   never built.

2. **The fan-out trigger does not trip.** The amendment says its own two-factor rung 2 needs four
   full-corpus configurations and therefore trips the "more than two" trigger. It needs two, the
   rung 1.5 winner and the rung 1 incumbent, and the incumbent already exists at one hundred percent.
   One new pass, about fifteen hours. The four conflates experimental cells with embedding configs.

3. **The homology axis was populated, and not omitted for want of pricing.** MMseqs2 nearest-donor
   identity bands were computed on both the 227 to 230 and 225 to 227 frames six weeks before the
   amendment, and carry a headline result. The claim that nobody priced it is contradicted by the
   project's own committed record.

4. **The chunking premise does not match the run.** All eight seeded configurations are
   `use_chunking=False`, `chunk_size=512`, `chunk_overlap=0`, `max_length=2048`, verified against the
   live database. The row-per-sequence ratio for the run as configured is exactly 1.00. No 64 overlap
   exists anywhere.

5. **A cited effect size has no provenance.** The figure appears once in the amendment and nowhere
   else in the tree, with no derivation and no citation. The defensible statement is the one the
   registry supports; the number should be struck rather than corrected.

6. **`batch_size=1` is attributed to the wrong cause.** It is a conservative guard for the largest T5
   configuration at 2048, explicitly raisable per configuration, not a device limit. Today's own
   measurement at batch size 8 contradicts the stated cause.

7. **The safety probe has the wrong scope.** The size is right, about fourteen minutes at the
   measured rate, but restricting it to T5 and ESM excludes Ankh, which is the only overflow case
   this repository has actually reproduced.

8. **The taxonomic banding will not carry three levels.** Corpus-wide the split is Bacteria 336764,
   Eukaryota 241098, Archaea 19904, Viruses 18164. Crossed with category and aspect, only Eukaryota
   and Bacteria have the population to support a cell; a third band requires splitting Eukaryota.

### What is not closed

**The keyring under linger after a reboot.** Pushing works unattended right now, through
`gh auth git-credential` against the keyring, verified in a clean environment. Linger is now `yes` on
this machine too, which was `no` and contradicted the CLAUDE.md exactly as the desktop found. What is
NOT established is whether the keyring is unlocked for a user service that starts at boot with nobody
logged in. If it is not, the keeper retries forever and the ledger looks healthy from the other side.
Testing it costs one deliberate reboot and nobody has paid it.

**The rest of the review.** The session limit was reached. The remaining claims will be checked at a
sane scale, with the document present through a worktree, and with partial results written as they
arrive rather than at the end.

---

## 2026-08-12, laptop: a claim is not a delivery, and the unit runs from a branch

Two findings from the hours after the previous entry. The second one is the serious one, and it was
caught by the researcher reading the ledger rather than by either machine, which is itself the point.

### The unit executes its supervisor out of the working tree, and the tree has branches

`coord-keeper.service` sets `ExecStart=/bin/bash %h/Thesis2/agent-farm/scripts/services/coord-keeper-supervisor.sh`
and `WorkingDirectory=%h/Thesis2/agent-farm`. That path is the PRIMARY working tree of a repository
whose branches do not all contain `scripts/`. `plan/rung2-amendment` has the amendment and no coord
scripts; `peer/host-report` has this log and no coord scripts.

So checking out a branch to read a document, in the tree the unit points at, removes the file systemd
will exec on the next restart. `Restart=always` means the service then fails in a loop, and the only
symptom on the other machine is a keeper that stopped pulsing. Nothing in the runbook says the tree is
load bearing.

This is the same collision reported in the previous entry, which was framed as an inconvenience for
readers. It is not. It can stop the keeper.

Mitigation applied here: the primary tree stays on `main` permanently, and every other branch gets a
`git worktree`. This entry is being written from `~/Thesis2/agent-farm-peer`. The durable fix belongs
in the unit: point `ExecStart` at a path that is not a branch-switchable checkout, or have the
supervisor verify its own script's presence and exit 78 with a message naming the branch, the way it
already does for the missing clone.

### A claim is a lock taken by a shell script, not a message received by an agent

The previous entry reported the first cross-machine claim as the mechanism being closed. That was
correct about transport and wrong about delivery, and the gap matters more than the success.

Observed state at 16:31Z, from the ledger and both pulses:

    01KZT2GC   done      04:08:41Z   desktop's own probe, HAS a ledger outcome entry
    01KZTR5J   done      10:30:44Z   desktop's own probe, HAS a ledger outcome entry
    01KZVCAB   claimed   16:19:22Z   first message from the laptop, NO outcome entry
    01KZVD0P   unclaimed 16:31:17Z   second message from the laptop, still only in inbox/

The desktop's pulse carries `active: [{message_id: 01KZVCAB, task_id: coord-1786551564-1368,
status: running}]` and has done so since 16:19. Twelve minutes later there is no outcome entry, and
the second message has not been claimed at all, against twelve seconds for the first.

The documentation is explicit that this is by design in V0: "the tick does not spawn the agent (the
conductor consumes the block)". The chain has three links and only two of them run unattended:

    send  ->  keeper claims  ->  [nothing]  ->  an agent reads

The two probes that reached `done` were processed while an agent session existed on the desktop. The
first laptop message arrived after that session ended, so it was claimed and then held.

Three consequences worth stating plainly, because the mechanism looks healthy from both sides while
this is happening:

1. **A claim proves a lock was taken, nothing else.** Neither the pulse nor the claim distinguishes
   "an agent is working on this" from "a shell script took it and nobody came". Both render as
   `running`.

2. **The held claim appears to block the queue.** The second message sat unclaimed for twelve minutes
   while the first was claimed in twelve seconds. If the tick will not take a second message while
   holding an unreleased first, then one absent agent stops the channel entirely rather than
   degrading it.

3. **Nothing recovers it without a reboot.** V0 has no writer for `released`. The documented recovery
   is the boot-id marker vanishing on restart, which does not apply here because the desktop is up.
   The six hour stale-claim alarm is the only backstop, and it summons a human.

The lease item already named in the design closes all three, and until it exists the honest summary
is: **the two machines can pass locks reliably and cannot yet pass work.** A message sent to a
machine with no agent session is not queued for later, it is captured.

The mistake in the previous entry is worth naming for the next reader. The check used to confirm the
second claim searched the ledger tree for the message id and found it under `inbox/desktop/`, which is
the file the sender itself had just written. It confirmed its own send and reported it as a claim.
Any future check for a claim must match on the `claims/` prefix specifically, and better, must read
`state` out of the claim body rather than infer from a path.

---

## 2026-08-12, laptop: correction, a held claim does not block the queue

The previous entry recorded, as consequence 2, that "the held claim appears to block the queue",
inferred from one message being claimed in twelve seconds while a second sat unclaimed for twelve
minutes. **That inference is wrong** and the desktop refuted it from evidence this machine could not
see: its own heartbeat recorded the second message as `1 skipped`, not as queued behind anything.

The real cause was a capability mismatch of the sender's making. The message was addressed
`to: desktop` with `requires: [platform]`. The desktop declares `gpu cuda compute`; `platform` is a
capability only the laptop has. The tick evaluated it, found the machine ineligible, and skipped it
correctly. The message was undeliverable from the moment it was written.

Re-sent without the mismatch, it was claimed in sixteen seconds.

**The defect this exposes is better than the one that was claimed.** `to` and `requires` can
contradict each other and nothing warns at any point. `coord-send.sh` accepted the message, returned
a message id, an inbox path and a ledger commit, and both machines' pulses stayed healthy while the
message could never be taken by the machine it named. It is the shape of failure this project has hit
repeatedly in other places: an operation reporting success over an empty result.

The check is cheap and belongs on the send side, because the send side is where the intent is known:
the addressee's capabilities are published in `pulse/<machine>.json`, so `coord-send.sh` can fetch
the pulse branch and refuse, or at minimum warn, when `requires` is not a subset of what the named
recipient declares. A message to `any` needs no such check; a message naming a machine does.

Two smaller notes from the same exchange, both worth keeping:

**The claim that sat for two hours was not evidence of a broken transport.** It was claimed unattended
under systemd ten minutes after the desktop rebooted, which settles the keyring-under-linger question
in the affirmative for that machine. It then sat because V0 ships no conductor, exactly as documented.
Transport and delivery failed in different places and only the second one is missing.

**A capability set is a claim about a machine and should be checked against it.** The laptop's
declared set was corrected earlier today to include `gpu` and `cuda` after the handoff proposed
excluding them. The desktop's set omits `platform`, `postgres`, `broker` and `storage`, which is
correct: those live here. Neither machine can validate the other's list, so a wrong one degrades into
silently skipped messages rather than an error, which is the same failure mode as the mismatch above
seen from the other end.

---

## 2026-08-12, laptop: the channel transports and does not deliver, demonstrated

Closing the coordination probe with the result, which is negative and is the useful part.

Two well formed messages were sent from the laptop and claimed by the desktop within seconds each:

    01KZVDXG   claimed 16:47:16Z   the PEER-LOG report
    01KZVE3C   claimed 16:50:24Z   a deliberately trivial question, "what is 2+2"

Both are still `running` in the desktop's pulse, which was fresh at 16:50:26Z. Neither has an outcome
entry. The 2+2 was chosen precisely because no reasonable agent would need time on it: if it does not
come back, the reason is not the work.

**From the outside the system looks healthy.** Pulses current on both machines, claims taken in
seconds with epoch and timestamp, zero errors anywhere, two messages in `active` with status
`running`. An observer reading only the ledger and the pulses would conclude the machines are
coordinating. They are not. `running` in a pulse means a shell script took a lock, and nothing
distinguishes that from an agent doing the work.

The missing link is named in the design as a deliberate V0 absence, and the code says it too, in a
comment on the task row the tick inserts: "the process this row will describe is the agent the
conductor has not spawned yet". The tick claims, writes `handoff.env` with the composed prompt and
the model, inserts the task row, and stops.

So the chain is:

    send  ->  keeper claims  ->  handoff.env written  ->  [nothing]  ->  an agent reads

Three links work unattended and are now proven against the real remote across two machines. The
fourth has no implementation.

**What this changes about the conductor item.** It stops being a design preference and becomes the
thing that decides whether the mechanism has any value at all. Every property already built and
verified today, the push as lock, GitHub as arbiter, the permanent record, the capability filter, the
content contract, the pulse, delivers exactly nothing while the last link is absent, and delivers it
while showing green.

One detail for whoever builds it. `scripts/spawn.sh` states that it "only handles kind=headless
(subagents are spawned by the conductor via the Agent tool)", so the conductor is designed to be an
agent rather than a daemon. That is a real constraint on the shape of the fix: a shell watcher can
turn `handoff.env` into a `spawn.sh` call for a headless agent, but the intended path for anything
richer runs through a session that is already alive. Either way the watcher is small and the
`handoff.env` contract already carries everything it needs: `task_id`, `composed_prompt`, `model`,
`message_id`, `claim_epoch`.

Until it exists, the operating rule is the one the previous entry gave and this probe confirms:
**do not claim what you will not close in the same session**, because a claim with nobody behind it
is indistinguishable from work in progress, and in V0 nothing releases it.
