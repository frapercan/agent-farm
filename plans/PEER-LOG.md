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
