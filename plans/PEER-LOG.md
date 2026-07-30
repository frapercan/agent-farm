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
