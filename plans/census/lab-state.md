# Slice: lab-state

Auditor slice key: `lab-state`.
Target: `/home/xaxi/Thesis2/repositories/protea-reranker-lab`.

Mandate: establish the STATE of protea-reranker-lab as handed to this machine.
What it is; git history; current branch; what it can run today; whether its
dependencies resolve; whether its tests pass (run ONLY if no DB and no network);
what it consumes and whether that input still exists on disk; verify the claim
that 131 scripts run a whole study outside the platform, and say what they are.

Two dates that decide everything:
- 2026-07-28 OS reinstall (storage/ nominally not restored)
- 2026-08-27 experiment registry WIPED; anything dated before is not evidence
  about the current window.

Status: COMPLETE. 14 findings below, then a closing STATE section.

---

## What protea-reranker-lab IS, and its git state on this machine
verdict: CONFIRMED
first number: 132 commits, HEAD `66403930c84664873291daaf9f97aaa708cdb9d8`,
  "feat(encoder-ablation): exclude donors by sequence, and separate what is fit
  from what is retrieved (#119)", authored 2026-08-17 14:49:32 +0200.
  Branch `develop`, tracking `origin/develop`, **1 commit BEHIND**.
second number (independent): the missing commit is `270c46c`
  "feat(gates): read the frozen pool, so the encoder gates run where the card is
  (#120)". `.git/FETCH_HEAD` mtime is **2026-08-18 11:39**; `.git/HEAD` mtime is
  **2026-07-29 01:48**. So the working checkout was created 2026-07-29 (the day
  after the reinstall) and last fetched 2026-08-18. Nothing has been pulled since.
first commit: `5c9209f` 2026-04-21 02:05:32 "scaffold: initial protea-reranker-lab".
  Repo life: 2026-04-21 -> 2026-08-17, 132 commits, single author
  (Francisco Miguel Pérez Canales), PR-numbered #80..#120 visible in recent log.
date of evidence: 2026-08-17 (HEAD) -> window: **pre-wipe** (registry wiped 2026-08-27)
frame: n/a (repository state, not a metric)
population: n/a
platform gap: the lab is a *separate repository* with its own Poetry project,
  Dockerfile, Sphinx docs and CI. It is not a PROTEA plugin and dispatches no
  PROTEA operation. Everything it computes is computed OUTSIDE the platform.
note: **Every commit in this repository predates the 2026-08-27 registry wipe.**
  The newest lab commit is ten days older than the wipe. So *no* number the lab
  itself produced is evidence about the current window unless it was re-run after
  2026-08-27, and the file mtimes say the tree has not been touched since
  2026-08-25 (.claude/) and the code/results since 2026-08-18.

## The tree is a re-clone dated the day after the reinstall
verdict: CONFIRMED
first number: nearly every tracked file has mtime `2026-07-29 01:48`
  (README.md, pyproject.toml, poetry.lock, src/, docs/, results/, datasets/,
  experiments/, fullgo/, dataset_cards/, and the four loose top-level study
  scripts).
second number: `.git/HEAD` mtime 2026-07-29 01:48 matches exactly -> a fresh
  `git clone` at that moment, not a restored directory.
  The only later mtimes are `research/` 2026-08-18 20:53, `scripts/` and `tests/`
  and `.pytest_cache/` 2026-08-18 12:17, `.ruff_cache/` 2026-08-18 11:42,
  `.claude/` 2026-08-25 22:34.
date of evidence: 2026-07-29 -> window: pre-wipe
platform gap: n/a
note: the repo survived the reinstall only because it is on GitHub. Anything the
  lab produced that was NOT committed died on 2026-07-28. That is exactly what
  the four `preserve:` commits of 2026-07-27/28 (#114 #115 #116 #117) were racing.

## "131 scripts running a whole study outside the platform", verify the count
verdict: CONFIRMED (count exact), and the location is NOT the reranker lab
first number: 131. `find /home/xaxi/Thesis2/storage/encoder-study/scripts -type f | wc -l`
  = **131**, and `ls | wc -l` = 131 (flat directory, no subdirs).
second number (independent, by extension): **116 `.py` + 15 `.sh` = 131**.
  The `.py` files are numbered `01_prepare.py` .. `115_panel_populations_experimental_baseline.py`
  (115 numbered) **plus** one unnumbered helper `bank_cache.py` = 116.
  The 15 `.sh` are 12 `chain_*.sh` (chain_2stage, chain_atoms, chain_atoms2,
  chain_axes, chain_indomain, chain_next, chain_poolprobe, chain_probe,
  chain_push, chain_rung2score, chain_sizefair, chain_z) plus `gpu_queue.sh`,
  `queue_1144.sh`, `run_all.sh`.
date of evidence: mtimes 2026-08-19 (87 files) / 08-20 (24) / 08-22 (1) /
  08-23 (10) / 08-26 (9). Oldest `01_prepare.py` 2026-08-19 00:16, newest
  `115_...experimental_baseline.py` 2026-08-26 21:53.
  -> window: **entirely PRE-WIPE.** The last script was written 2026-08-26 21:53,
  roughly a day before the 2026-08-27 registry wipe. Not one of the 131 is
  post-wipe.
frame: n/a at the directory level; each script carries its own (several encode
  the frame in the filename: `..._indomain`, `..._by_band`, `..._experimental_baseline`,
  `..._full_cell`, `..._pooled`).
population: n/a
platform gap: **NONE OF THE 131 IS TRACKED IN ANY REPOSITORY.**
  I searched: (a) `git log --all -- '**/<name>'` in protea-reranker-lab for six
  representative names (01_prepare.py, 16_freeze_recipe.py, 73_architecture_on_the_task.py,
  95_publish_arms_to_store.py, 115_..., bank_cache.py, run_all.sh) -> zero hits;
  (b) `grep -rl` for the distinctive strings `73_architecture_on_the_task`,
  `95_publish_arms_to_store`, `encoder-study/scripts` across ALL of
  `/home/xaxi/Thesis2/repositories` (eight repos) and `/home/xaxi/Thesis2/agent-farm`
  -> **zero hits**. Not even a reference. The study is invisible to every repo.
note: this is the exact thing CLAUDE.md §storage forbids ("a procedure outside
  the platform is a capability that dies with the disk"), at a scale of 131 files
  and about 20 memory-store conclusions. **This is a bigger untracked body than
  anything the four 2026-07-27/28 `preserve:` commits rescued.** It is one
  `rm -rf` or one reinstall from gone, and the reinstall of 2026-07-28 is the
  proof that this happens here. What "was really measured" for the encoder study
  lives ONLY at `/home/xaxi/Thesis2/storage/encoder-study/`.

## What the lab CONSUMES, and whether the inputs still exist on disk
verdict: PARTIALLY CONTRADICTED, one of three required inputs is GONE
first number: `src/protea_reranker_lab/host_paths.py` declares exactly three host
  locations. I executed the three resolvers in a standalone interpreter
  (importlib on the file, stdlib only, no package import, no DB, no network):

    thesis_root()       -> /home/xaxi/Thesis2                        (correct)
    ground_truth_dir()  -> OK  -> /home/xaxi/Thesis2/CAFA_forever/data/releases/Sep_2025_Mar_2026
    protea_python()     -> OK  -> /usr/bin/python3
    ia_table()          -> **RAISED MissingHostPath**: "the information-accretion
                           table not found. Set PROTEA_LAB_IA_PATH, or place it at
                           one of: /home/xaxi/Thesis2/protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv"

second number (independent, filesystem):
  - GT dir EXISTS and is populated: groundtruth_{NK,LK,PK,PK_known}.tsv,
    groundtruth_targets.tsv, groundtruth_terms_of_interest.txt, all mtime
    **2026-07-28 17:09** (restored on reinstall day), plus results_{NK,LK,PK}/
    and method_{availability,names}.tsv mtime 2026-08-11 15:34. Six release
    windows exist under `CAFA_forever/data/releases/`.
  - `/home/xaxi/Thesis2/protea-lafa-knn` **does not exist at all** (not the file,
    the whole directory). The only IA.tsv on the machine are
    `/home/xaxi/Thesis2/storage/encoder/IA.tsv` and
    `/home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/IA.tsv`
    (`find /home/xaxi/Thesis2 -name IA.tsv` excluding .git -> exactly those two).
    Note the shape differs: the code wants `lafa_t0_Sep_2025/` (underscore),
    storage has `lafa_t0/Sep_2025/` (directory split).
  - `/home/xaxi/Thesis2/repositories/PROTEA/.venv/bin/python` does not exist.
date of evidence: 2026-09-02 (today, live filesystem) -> window: post-wipe-current
frame: n/a
population: n/a
platform gap: the IA table has no producer that writes it here. The lab expects it
  at a path belonging to a repository (`protea-lafa-knn`) that is **not among the
  eight repositories** on this machine and is not in `CLAUDE.md`'s layout.
  It survives only as an untracked file under `storage/encoder/`.
note: **`protea_python()` cannot fail, by construction, and that is the defect the
  module's own docstring is about.** Its fallback list ends with
  `Path(sys.executable)`, which is always an existing file, so `_resolve` returns
  before it can raise; and nothing checks that the interpreter can actually
  `import cafaeval`. The docstring promises "Interpreter that can import
  cafaeval"; the resolver only promises "an interpreter". On this machine it
  resolves to `/usr/bin/python3` (3.14.4) which has **cafaeval ABSENT** (checked
  with `importlib.util.find_spec`, along with numpy, pandas, lightgbm, pyarrow,
  scipy, sklearn, torch, pydantic, wandb, matplotlib -- ALL ABSENT). So a run
  that scores through the cafaeval subprocess would fail in the subprocess, which
  is precisely the "caught, turned into an error dictionary, metric became None,
  status: ok with every cell empty" failure the file was written to prevent.
  The file fixed two of three resolvers and left the third with the same shape.

## Does the lab's dependency set resolve, and is there an environment?
verdict: CONFIRMED that it resolves; CONTRADICTED that it is available where the repo is
first number: `poetry env list` inside
  `/home/xaxi/Thesis2/repositories/protea-reranker-lab` returns **empty** (rc=0),
  and there is no `.venv` in the repo. `find` for `pyvenv.cfg` under all nine
  repositories: **zero**. None of the nine repos has a virtualenv.
second number: a fully populated environment DOES exist in poetry's cache:
  `~/.cache/pypoetry/virtualenvs/protea-reranker-lab-s3zMI1yE-py3.12`,
  **71 installed distributions**, Python 3.12.13 (from a uv-managed CPython).
  Its `protea_reranker_lab.pth` reads
  `/home/xaxi/Thesis2/worktrees/lab-reporting/src`
  and `direct_url.json` says `{"editable": true, "url":
  "file:///home/xaxi/Thesis2/worktrees/lab-reporting"}`.
  **So the only working lab environment on this machine is bound to an EPHEMERAL
  WORKTREE, not to the repository.**
  Resolved core: numpy 2.4.4, pandas 3.0.2, scipy 1.17.1, scikit-learn 1.8.0,
  lightgbm 4.6.0, pyarrow 24.0.0, pydantic 2.13.3, matplotlib, wandb, pytest,
  mypy, sphinx + rtd-theme + myst + copybutton.
  `protea-contracts 1.0.1` installed from git at **commit
  `cc30bc5e1b658ecf527bf3db08df66e655f4cb27`**, exactly the pin in
  `pyproject.toml` -> the internal dependency pins a commit, not a branch, and it
  is satisfied. Two sibling envs exist but hold only `pip`
  (`protea-reranker-lab-aca7fNcT-py3.12`, `protea-reranker-lab-s3zMI1yE-py3.14`,
  1 dist each) -- created and never populated.
date of evidence: env mtime 2026-08-17 13:22 -> window: pre-wipe
frame: n/a
population: n/a
platform gap: n/a (packaging, not measurement)
note: three things are NOT installed and each closes a capability:
  **torch ABSENT** (so `chunk_attn_encoder.py` and the learned-encoder ablation
  cannot run; commits #102 and #106 made those imports lazy precisely so CI could
  stay green without it), **cafaeval ABSENT** (so no official LAFA scoring),
  and the whole `native` extra ABSENT (minio, mlflow-skinny, boto3 -- so
  `scripts/train_native_boosters.py --minio-fallback` and its MLflow tracking
  cannot run). Also note the interpreter split: the lab env is 3.12, the system
  and the `drift-test-*` envs are 3.14, and `pyproject` requires `>=3.12,<4.0`.

## What the lab consumes: the feature datasets are NOT on this disk
verdict: CONTRADICTED (the inputs do not exist locally)
first number: `datasets/` holds **15 entries**: twelve `bench-v1-K{3,5,10}-v22{6,7}-lineage-<plm>`
  cards, `ia/`, `smoke-K5`, `smoke-K5-knn-only`. Eleven of the twelve bench dirs
  contain **README.md and nothing else** (12K each); one contains only
  `manifest.json`. **There is not one parquet anywhere under `datasets/`.**
second number: the cards say where the data actually is. From
  `datasets/bench-v1-K5-v226-lineage-esm2_650m/README.md`:
    Train parquet `s3://protea/datasets/bench-v1-K5-v226-lineage-esm2_650m/train.parquet`
    Eval parquet  `s3://protea/datasets/.../eval.parquet`
    Storage backend `minio`
    Train rows **24,921,117**, eval rows **1,092,281**
    Train pairs 13 (`v160-v165` .. `v220-v226`), eval pair `v226-v230`
    Producer PROTEA 0.8.0, git sha `b9c1dea8f20a1d5ec6e18689653f1ba9854dc2cf`,
    export job `258a1822-f01a-445b-bef2-4c8d7e969c8a`, created **2026-05-24T11:15:43Z**,
    schema v2, schema_sha `6d97a624b8a7`.
  So the lab's inputs live in the SERVER's MinIO, reachable only over the network,
  and are pulled by `scripts/pull_dataset.py`. I did not and must not test that.
date of evidence: export job 2026-05-24 -> window: **pre-reinstall**. Whether those
  objects still exist in the laptop's MinIO is unverifiable from this machine and
  I am not permitted to check.
frame: schema v2, K in {3,5,10}, lineage delta `vNNN-vMMM` = terms present at MMM
  and absent at NNN, label binary on the eval delta, annotation source `goa`.
population: 24.9M train rows / 1.09M eval rows per bench dataset; row = (query
  protein, retrieved GO term) candidate.
platform gap: the dataset producer IS a registered operation
  (`export_research_dataset`, PROTEA 0.8.0), so this half is inside the platform.
  The consumer -- everything the lab does with the parquet -- is not.
note: the ONE piece of real input data present locally is
  `datasets/ia/IA-swissprot-exp-v227.txt` (968K) with `build_corpus.sql` and
  `provenance.md`. Note it is a DIFFERENT artifact from the `IA.tsv` that
  `host_paths.ia_table()` demands and cannot find, and the `-v227` in its name is
  the release the memory store flags as the START of the official window
  (220 -> 230), i.e. an IA table cut at 227 is not the official frame's IA table.

## The lab's own results are FORMALLY WITHDRAWN, in git, before the reinstall
verdict: CONFIRMED
first number: commit `4a81079` "docs(readme): withdraw the results, keep the
  genealogy that explains them (#116)", **2026-07-28 11:38:08 +0200** -- the day
  of the OS reinstall. The diff removes the headline
  **"NK+LK cafaeval Fmax 0.7291 +/- 0.0028"** on `bench-v1-K5-v226-lineage`
  (3 seeds, paired bootstrap N=10000, "all six NK+LK CIs strictly positive"),
  and removes "This is the publishable number for Chapter 6 of the doctoral
  thesis." It also withdraws the earlier **0.6215 +/- 0.0014** (LB.2) and names
  **0.4562** as a number that "must not be cited".
second number (the reasons, quoted from the commit body): two scoring-frame
  defects -- "a normalisation applied to the scores **manufactured the baseline**
  every lever was then measured against" and "a lookup built on a key that was
  not unique **rewrote a measurable share of rows** without failing". These are
  the two defects the memory store records as `rankpct_artifact` (2026-07-16) and
  `dict_join_bug` (2026-07-17).
date of evidence: 2026-07-28 -> window: pre-wipe (and pre-reinstall by hours)
frame: the withdrawn number's frame was cafaeval Fmax, IA-weighted, **NK+LK
  selective deployment only** (PK cells left on the KNN baseline), on the
  `v226-v230` eval delta of a v226 lineage. That is 6 of the 9 cells, not 9.
population: six NK+LK cells of one benchmark lineage; the PK cells were excluded
  by policy, not measured.
platform gap: n/a -- this is a retraction, correctly recorded.
note: **what survives the retraction is a DEDUCTION, and the commit says so in
  its own words.** "The selective deployment policy, as a **design result rather
  than a measurement**: ... That says **where** the learned component helps, not
  how much." Anyone citing "the reranker carries NK and LK" must carry that
  qualifier: the surviving claim is directional and its magnitude was measured
  against a manufactured baseline. This is the cleanest example in the repository
  of the norm's rule 3 being applied by the author to his own work.

## The retraction is INCOMPLETE: champions.md still publishes every withdrawn number
verdict: CONFIRMED (a live contradiction inside one repository)
first number: `champions.md`, tracked at the repository root, 8,988 bytes, last
  modified by commit `73daf50` **2026-05-23 14:10:59** and **never touched
  since**. `grep -niE 'withdraw|retract|not.*cite|manufactur|recompute'` over it
  returns nothing about the retraction. It still states, as the current table:
    selective_avg_cafaeval **0.6215** (repeated in all 9 rows)
    per cell champion_fmax_cafaeval:
      lk-bpo 0.6459  lk-cco 0.7368  lk-mfo 0.6807
      nk-bpo 0.5596  nk-cco 0.7774  nk-mfo 0.7065
      pk-bpo 0.4030  pk-cco 0.6010  pk-mfo 0.4830
    paired_ci_lower/upper for the six NK+LK cells all strictly positive
      (e.g. lk-mfo 0.0941..0.1061), all three PK cells exactly 0.0000/0.0000.
  It also carries **nine PROTEA `RerankerModel` UUIDs** (one per cell), i.e. the
  withdrawn models are still named as champions and are dispatchable by id.
second number (independent recomputation, rule 1): the plain unweighted mean of
  the nine `champion_fmax_cafaeval` values is **0.621544**, against the declared
  `selective_avg_cafaeval` **0.6215**. Difference **4.4e-05**, i.e. pure
  four-decimal rounding. So the "selective average" is exactly the arithmetic
  mean of nine cells, with **no IA weighting and no population weighting between
  cells** -- an equal-weight average over nine populations of very different size
  (the served NK cell is about 5% of a window). The NK+LK mean alone is 0.684483
  and the PK mean is 0.495667.
date of evidence: numbers stamped `last_updated 2026-05-18`, file last written
  2026-05-23 -> window: **pre-reinstall AND pre-wipe**. Two full frames obsolete.
frame: **fully declared here, unusually**: cafaeval with `prop=fill`, `norm=cafa`,
  `no_orphans=True`, `max_terms=500`, `th_step=0.001`; dataset
  `bench-v1-K5-v226-lineage-prostt5`; eval window `v226-v230`; seeds 42, 7, 137;
  features "34 features, anc2vec and PCA families dropped to remove historical
  leakage"; paired bootstrap N=10000, seed=42, alpha=0.05. **No `-known`
  exclusion is mentioned anywhere in the file.**
population: nine cells, all nine reported; but the deployment policy is six.
platform gap: `scripts/update_champions.py` regenerates this file from
  `experiments/lb3/per_cell_paired_ci.csv`, `experiments/lm3/...csv`,
  `experiments/lr1/lineage_delta.csv` -- CSVs in the repo, not the registry. The
  operation that would make this reborn writing to the database does not exist:
  the file's own header says "No FARM-EXP.3-format run records found yet; the
  champions table will populate once runner slices (FARM-EXP.5+) write run
  records". That writer slice was never built, so a hand-maintained Markdown file
  is the champion registry.
note: THREE things a reader must not miss.
  (1) README.md says "**why 0.4562 must not be cited**"; `0.4562` appears
      **twice** in `champions.md`, un-annotated.
  (2) The three PK rows report `paired_ci_lower = paired_ci_upper = 0.0000` in a
      column of measurements. The prose says "PK cells carry zero delta **by
      construction** (not a null result)" -- so those three rows are a
      **DEDUCTION FROM THE DEPLOYMENT POLICY formatted identically to six
      measured rows**, and the `champion_fmax_cafaeval` printed for them is the
      KNN baseline's number, not any reranker's. Norm rule 3, in the table.
  (3) README (withdrawn) headline was 0.7291 for NK+LK; champions.md headline is
      0.6215 for nine cells. They are different statistics over different cell
      sets and neither is the other's successor. The README itself once said
      "0.6215 is superseded by 0.7291", which is a comparison of a 9-cell mean
      against a 6-cell mean.

## What the lab can run TODAY: 329 of 1,049 tracked files point at a home that no longer exists
verdict: CONFIRMED
first number: `git grep -l 'home/frapercan'` over the tracked tree ->
  **329 files**, **953 occurrences**, out of **1,049 tracked files / 492 tracked
  `.py`**. That is **31.4% of the tracked repository**.
second number (independent): `ls /home` returns exactly one entry, `xaxi`.
  `/home/frapercan` does not exist. Every one of the 953 paths resolves to
  nothing. Breaking the 953 down by prefix:
      286  /home/frapercan/Thesis2/protea-lafa-knn     <- directory does not exist here
      270  /home/frapercan/Thesis2/storage             <- exists as /home/xaxi/Thesis2/storage
      251  /home/frapercan/Thesis2/repositories        <- exists as /home/xaxi/...
       78  /home/frapercan/Thesis2/CAFA_forever        <- exists as /home/xaxi/...
       55  /home/frapercan/Thesis2
        5  /home/frapercan/Thesis2/worktrees
        3  /home/frapercan/.cache/pypoetry
        2  /home/frapercan/Thesis2/agent-farm
        1  /home/frapercan/lafa_workdir/data
        1  /home/frapercan/Thesis2/protea-neural-head  <- repository not on this machine
        1  /home/frapercan/Thesis2/lafa-smoke
  Worst-hit directories: research/cooc_experiment 78 files, research/regen_headline 34,
  research/fullgo_models 21, scripts/ 16, research/layer_ablation 13, fullgo/ 11.
date of evidence: 2026-09-02 (live filesystem) -> window: post-wipe-current
frame: n/a
population: n/a
platform gap: this is the whole platform argument in one number. The four
  `preserve:` commits saved 434 files of procedure from the reinstall, but saved
  them *with the old machine's absolute paths baked in*, so what was preserved is
  the text of the procedures, not the ability to run them.
note: **the library itself is affected, not only the loose scripts.** Six hits
  inside `src/protea_reranker_lab/`:
    band_registry_bridge.py:109  `_BASE = Path("/home/frapercan/Thesis2")`
    chunk_attn_encoder.py:69     default checkpoint `/home/frapercan/Thesis2/storage/learned_encoders/ankh_base_chunk_attnpool.pt`
    evaluate.py:26               default protea python `/home/frapercan/.../PROTEA/.venv/bin/python`
    universal_runner.py:61,63    same, plus `_CANONICAL_LAB`
  `host_paths.py` was written (its docstring says so explicitly) to abolish exactly
  this pattern, and it is imported by only part of the package: the four modules
  above still carry the old constant. So the fix landed and the defect survived
  beside it.

## The golden regression test CANNOT FAIL on this machine, and its own docstring disagrees with its own constant
verdict: CONFIRMED (norm rule 4: a green suite is evidence only if it could have failed)
first number: `tests/test_band_registry_bridge.py:36`
  `_THESIS2 = Path("/home/frapercan/Thesis2")`, and every precondition of
  `test_f_micro_w_golden_prot_t5_k3` is derived from it:
    EXP15_RUNS_DIR = _THESIS2/agent-farm/results/executor-1780829216-57db/runs
    _LAFA_IA  = _THESIS2/protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv
    _LAFA_OBO = _THESIS2/protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo
    _PROTEA_PY = env PROTEA_PYTHON or _THESIS2/repositories/PROTEA/.venv/bin/python
  All four are under a home that does not exist, so
  `@pytest.mark.skipif(not (_EXP15_PRESENT and _LAFA_IA.exists() and
  _LAFA_OBO.exists() and _CAFAEVAL_PRESENT))` is unconditionally true and the
  test **silently skips**. Same for `TestResolveBandArtifacts::test_resolves_v227_obo_and_ia`
  (lines 159-165), whose `_ia`/`_obo` use the same dead prefix.
second number (the pin it guards): `_BASELINE_MEAN_F_MICRO_W = 0.5863` at line 60.
  The **module docstring at line 4 of the same file says 0.5849**. The comment
  block reconciles them -- 0.5849 was computed with `releases/2026-01-23`
  (the "phantom-gap bug"), 0.5863 with the LAFA-congruent
  `releases/2025-07-22` OBO -- but the docstring that a reader meets first was
  never updated. One file, two values for the same quantity, 0.0014 apart.
date of evidence: pin authored pre-2026-07-29; artefacts `executor-1780829216-57db`
  -> window: **pre-reinstall**. Neither value is evidence about the current window.
frame: cafaeval `f_micro_w` (POOLED, not per-protein Fmax), NK+LK **six** cells,
  mean of six cells, prot_t5 K3, band `v227`, OBO `releases/2025-07-22`,
  IA `lafa_t0_Sep_2025/IA.tsv`. Note the metric here is `f_micro_w`, a different
  statistic from the `cafaeval Fmax` in champions.md -- the norm document warns
  that four different statistics are all called F.
population: six NK+LK cells; PK not evaluated at all.
platform gap: the artefacts are agent-farm run outputs
  (`agent-farm/results/executor-.../runs/prot_t5_K3_<cell>/{pred,gt}.tsv`), not
  registry rows. Reborn writing to the database, this would be an evaluation
  operation over a stored prediction set; today it is a directory of TSVs under
  a path that no longer exists.
note: the value 0.5849 is the one that reached the memory store; the corrected
  0.5863 lives only in a test constant inside a test that never runs. If anyone
  quotes 0.5849 they are quoting the number this file says is wrong.

## The phantom-gap guard keys on a BASENAME, and three mutually different IA tables pass it
verdict: CONFIRMED, new, and this is the most consequential thing I found
first number (what the code claims): `src/protea_reranker_lab/band_registry_bridge.py`
  declares band `v227` with
    `obo_versions = {"releases/2025-07-22"}`
    `ia_tokens    = {"IA.tsv", "IA-swissprot-exp-v227.txt"}`
    description  "Canonical IA = lafa_t0_Sep_2025/IA.tsv (**39906 terms**).
                  IA_cafa6.tsv is REJECTED for this band."
  and `assert_band_consistency` raises `BandMismatchError` ("Phantom-gap guard")
  when the IA artifact is not canonical. But `accepts_ia_token` compares
  `os.path.basename(ia_ref).lower()` against the token set. **The guard's whole
  discriminating power is a filename.**
second number (independent, computed by me from the files on this disk):
  three files on this machine satisfy that band. Loading each as GO_term -> IA:

    A = storage/encoder/lafa_t0/Sep_2025/IA.tsv          39,906 terms
    B = storage/encoder/IA.tsv                           39,906 terms
    C = repositories/protea-reranker-lab/datasets/ia/IA-swissprot-exp-v227.txt
                                                         38,739 terms

    A vs B: identical term SET (39,906 common, 0 exclusive either way) but
            **14,387 differing values = 36.05% of the common terms**,
            max |diff| = 2.843991
    A vs C: 38,650 common, 1,256 only in A, 89 only in C,
            **10,264 differing values = 26.56%**, max |diff| = 14.593216
    B vs C: 38,650 common, 1,256 only in B, 89 only in C,
            **14,544 differing = 37.63%**, max |diff| = 14.600784

  A and B have the SAME NAME (`IA.tsv`), the SAME term count, and `cmp` says they
  are different files. C carries a different canonical token for the same band.
  A worked example: `GO:0000012` is 6.047841420976923 in A and
  5.992863818718371 in C.
date of evidence: A and B mtime 2026-08-11 13:50; C committed in the repo ->
  window: pre-wipe. But the DEFECT is a property of code that is current.
frame: this IS the frame. IA weighting is what turns raw cafaeval counts into
  `f_micro_w` / weighted Fmax, so a 36% shift in the weight vector is a change of
  frame, not of data. The band registry exists precisely to stop that.
population: all terms in the v227 evaluation ontology.
platform gap: the guard is a **vendored snapshot** of
  `protea.core.band_registry.BANDS` ("origin/develop, commit read 2026-06-07"),
  copied by hand into the lab with a comment saying "do NOT alter it without also
  updating the upstream registry". Nothing compares the two copies. Reborn
  properly, the IA artifact would be a registry row addressed by content hash and
  the guard would compare digests, not names.
note: TWO further things.
  (1) The module docstring says the resolver uses "an ordered search list that
      **never falls back to the old hardcoded**
      `/home/frapercan/Thesis2/protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv`" -- and
      then line 109 sets `_BASE = Path("/home/frapercan/Thesis2")` and makes that
      exact directory the **first entry** of both `IA_SEARCH_ROOTS` and
      `OBO_SEARCH_ROOTS`. The claim is contradicted five lines below itself.
  (2) `_find_ia_file` / `_find_obo_file` use `root.iterdir()`, **one level, no
      recursion**. On this machine every root is under the dead home, so both
      return `None` and the caller demands `LAB_IA_V227` / `LAB_OBO_V227`.
      Even if `_BASE` were corrected to `/home/xaxi/Thesis2`, the roots are
      `.../datasets/bench-v1-K5` (a directory that does not exist; the real ones
      are `bench-v1-K5-v226-lineage-<plm>`) and `storage` (whose IA files are two
      levels down at `storage/encoder/...`), so **the repository's own canonical
      IA file at `datasets/ia/` is not on any search root**. Fixing the username
      alone would not make the resolver work.

## The band artifacts themselves DO exist on this disk, relocated
verdict: CONFIRMED (a positive finding against the "lost" assumption)
first number: `find /home/xaxi/Thesis2 -name 'go-basic.obo' -not -path '*/.git/*'`
  -> exactly one: `/home/xaxi/Thesis2/storage/encoder/lafa_t0/Sep_2025/go-basic.obo`
  (31,428,837 bytes, mtime 2026-08-11 13:50).
second number (independent verification against the band's declaration):
  its header reads `data-version: releases/2025-07-22`, which is **exactly** the
  single `obo_version` band v227 accepts; and the IA.tsv beside it has
  `wc -l` = **39,906** with 39,906 distinct GO ids, **exactly** the "39906 terms"
  the band description claims. So the v227 (OBO, IA) pair the lab calls canonical
  is present and verifiable, at `storage/encoder/lafa_t0/Sep_2025/` instead of
  the `protea-lafa-knn/lafa_t0_Sep_2025/` the code expects. A third file,
  `train_terms.tsv` (10.9 MB), sits with them.
date of evidence: 2026-08-11 -> window: pre-wipe, but the artifacts are static
  reference data, not measurements, so the date does not retire them.
frame: band v227 = deployed LAFA window GOA v227->v230, t0 2025-09-04.
population: 39,906 GO terms.
platform gap: these are the inputs a `compute_information_accretion` operation
  would produce or register. They exist here as loose untracked files under
  `storage/`, which CLAUDE.md says is not carried across machines.
note: where I looked, so the negative half of this counts: `find` over the whole
  of `/home/xaxi/Thesis2` excluding `.git` for `IA.tsv` (2 hits) and
  `go-basic.obo` (1 hit); `ls -d` on `protea-lafa-knn`, on
  `storage/learned_encoders`, on `agent-farm/results/executor-1780829216-57db`.
  The EXP.15 golden artefacts (`executor-1780829216-57db/runs/prot_t5_K3_*`) are
  **NOT ANYWHERE**: `find /home/xaxi/Thesis2 -maxdepth 6 -name 'executor-1780829216*'`
  returns nothing, although `agent-farm/results/` itself exists. Those were lost
  on 2026-07-28. What DOES survive is a different, later artifact family,
  `experiments/phase3d_val227/prot_t5_K3_<cell>_seed42_227val.json`, present in
  the lab worktrees.

## Do the tests pass? Yes, and 41 of them cannot fail
verdict: CONFIRMED (ran them; method below)
HOW I RAN THEM, since the constraint is read-only: I did NOT run pytest inside the
  repository. I exported the tracked tree with
  `git ls-files -z | tar --null -T - -cf - | tar -xf - -C <scratchpad>/labcopy`
  (1,049 files, matching `git ls-files | wc -l`) and ran the suite there with
  `PYTHONDONTWRITEBYTECODE=1 TMPDIR=<scratchpad>/tmp
   <lab venv>/bin/python -m pytest -q -p no:cacheprovider -m 'not slow' -rs`.
  Nothing under /home/xaxi/Thesis2 was written. I first verified by grep that no
  test opens a database (no psycopg / sqlalchemy / postgres anywhere in `tests/`)
  and that the only network-shaped tests mock it: `tests/test_pull_dataset.py`
  patches `urllib.request.urlopen` with `unittest.mock`, its own docstring says
  "All S3 I/O is mocked so no live MinIO instance is required";
  `tests/test_native_boosters.py` only checks that mlflow is *absent*.
first number: **1 failed, 584 passed, 41 skipped, 1 deselected, in 5.78 s**
  (626 of 627 collected; 1 deselected by `-m 'not slow'`).
second number (is the failure real or an artifact of my copy?): the failure is
  `tests/test_farm_exp_9_partial.py::TestCompletedRunJSON::test_at_least_one_completed_run_exists`
  -- "No completed farm_exp_9_rep_*/run.json found under runs/transversal/".
  `runs/` is listed in `.gitignore` and does not exist in the real repository
  either (`ls -d runs` -> no such file), so the failure is genuine on this
  machine and is not caused by the copy. **CI deselects exactly this test by
  name** (`.github/workflows/test.yml`: `--deselect
  tests/test_farm_exp_9_partial.py::TestCompletedRunJSON::test_at_least_one_completed_run_exists`,
  comment: "researcher-only and not checked into the repo"). So the honest
  statement is: the suite is green as CI runs it, and red on a fresh clone by one
  known test.
date of evidence: 2026-09-02 (today) -> window: post-wipe-current
frame: n/a
population: 626 collected tests
platform gap: n/a
note: **the 41 skips are the finding, not the 584 passes.** Every skip is a test
  that would have touched real data, and each is silent:
      19  tests/test_multi_source.py       "smoke manifests not present under
                                            **/home/frapercan/**/datasets" -- the dead home again
      12  tests/test_farm_exp_9b.py        "No completed ablation/hparam runs yet"
       6  tests/test_golden_parquet_roundtrip.py
                                           "Golden parquet fixture missing at
                                            tests/fixtures/golden_v27.parquet"
       2  tests/test_chunk_attn_encoder.py "could not import 'torch'"
       1  tests/test_band_registry_bridge.py:164
                                           "v227 IA/OBO not present on disk"
       1  tests/test_lm3_feature_importance.py
                                           "study_v23 run artefacts not present
                                            in this worktree (gitignored)"
      +1  the `slow` golden regression, deselected here and skip-guarded anyway
  So **585 tests execute and every one of them runs on synthetic fixtures built
  inside the test file**; the entire suite finishes in 5.78 seconds. Not one
  assertion in this repository is currently made against a real feature parquet,
  a real IA table, a real embedding, or a trained model. The suite proves the
  code's shape, not any of its numbers. That is the exact pattern
  COLLIDING-A-NUMBER §4 names ("a green suite... is evidence only if the check
  could have failed").

## The one body of real measurement that survives IN the lab repo, and what its distribution says
verdict: CONFIRMED (measured, preserved, and never collided until now)
first number: `experiments/phase3d_val227/` -- **141 files, 138 per-cell result
  JSONs** plus `champions_227val.json` (18 rows), `all_results_227val.json` and
  `champions_227val.md`. This is the only place in the repository where real
  per-cell metrics are stored at full precision with their populations. A row:
    {"run_tag":"phase3a_K3_prot_t5","k":"K3","plm":"prot_t5","cell":"nk-mfo",
     "seed":42,"selection_metric":"f_micro_w","val_split":"v226-v227",
     "cafaeval_fmax":0.6985128436232537,"f_micro_w":0.6847445410662643,
     "s_min":2.5307953273903774,"n_rows_227val":4406,"n_positives_227val":212,
     "n_proteins_covered":243,"n_proteins_total_227val":251,"coverage_pct":96.8}
  Design: 8 PLMs (ankh_base, ankh_large, esm2_150m, esm2_650m, esm2_3b,
  esmc_600m, prostt5, prot_t5) x K in {3,5,10} x 6 NK+LK cells, seed 42.
second number (MY independent computation over the 138 rows -- rule 5, look at
  the distribution before the summary):
    18 (K, cell) champion decisions, each an argmax over 7-8 arms.
    **median best-vs-second gap = 0.0055**
    min 0.0016, max 0.0464
    **12 of 18 gaps are below 0.01; 14 of 18 below 0.02**
    per-cell population `n_proteins_total_227val` runs **168 to 362** proteins
  and the decisive one:
    **in 8 of the 18 cells, the two metrics printed side by side in the very same
    table pick a DIFFERENT winning PLM.**
      K10 lk-cco  f_micro_w -> ankh_large   |  fmax -> esm2_650m
      K10 lk-mfo  f_micro_w -> prot_t5      |  fmax -> ankh_base
      K10 nk-cco  f_micro_w -> esm2_150m    |  fmax -> prostt5
      K3  lk-cco  f_micro_w -> prot_t5      |  fmax -> prostt5
      K3  lk-mfo  f_micro_w -> ankh_base    |  fmax -> esm2_650m
      K3  nk-cco  f_micro_w -> esm2_3b      |  fmax -> esm2_650m
      K5  lk-cco  f_micro_w -> esm2_150m    |  fmax -> esm2_650m
      K5  nk-cco  f_micro_w -> esmc_600m    |  fmax -> esm2_650m
    All eight are CCO or MFO, the two smallest populations (168-186 proteins).
date of evidence: `val_split v226-v227`; the artifacts were committed before
  2026-07-29 -> window: **pre-wipe and pre-reinstall**. Not evidence about the
  current window.
frame: cafaeval, IA file explicitly **`datasets/ia/IA-swissprot-exp-v227.txt`**
  (stated in `champions_227val.md`), selection metric `f_micro_w`
  (IA-weighted micro, POOLED), split = the v226->v227 delta, training data
  `bench-v1-K{3,5,10}-v226-lineage-{PLM}` with "NO re-export", seed 42 only,
  coverage_threshold 80.0. **No confidence interval is computed anywhere in
  these 138 rows** and there is only one seed.
population: six NK+LK cells; PK is absent entirely. 168-362 proteins per cell,
  1,465 proteins summed over the six prot_t5 K3 cells.
platform gap: nothing writes these to the registry. `champions_227val.md` is
  hand-rendered; `champions.md` at the repo root is generated from three CSVs.
  The operation that would make this reborn is an evaluation operation that
  stores one row per (model, K, cell) with its interval and its population.
note: THREE things.
  (1) **A median winning margin of 0.0055 over a max of 8 arms on 168-362
      proteins, with no interval and one seed, does not resolve a winner.** The
      memory store's own encoder study puts a reproducibility floor at 0.0013 for
      a *different* study; here 12 of 18 decisions sit inside four times that,
      and the 8 metric disagreements are the direct demonstration that the
      ordering is not stable.
  (2) **The coverage rule, not the metric, chooses the champion in 4 of 18
      cells.** The rows carry `overridden_low_cov_plm` / `overridden_low_cov_fmw`:
      K3 nk-mfo raw best is esmc_600m at f_micro_w **0.7797**, excluded for
      coverage, champion esm2_3b at **0.6890** -- the deployed pick is 0.0907
      BELOW the raw argmax. Same shape at K5 nk-bpo (0.5698 -> 0.5650),
      K5 nk-cco (0.6722 -> 0.6531) and K5 nk-mfo (0.7427 -> 0.6756). Any
      statement "PLM X wins cell Y" from this study is a statement about the
      coverage filter as much as about the encoder.
  (3) `champions_227val.md` reports "changed from the old v226 selection" as
      **YES in 10 of 18 cells**. Given (1), that instability is what you would
      expect from re-drawing an argmax at a margin of 0.0055, not evidence that
      the new split changed the answer.

## The three "f_micro_w, prot_t5, K3, NK+LK mean" numbers, and why they are three
verdict: FRAME-UNKNOWN, resolved only partly
first number: `tests/test_band_registry_bridge.py` docstring says **0.5849**
  ("the memory value ... computed with the wrong bench OBO releases/2026-01-23,
  the phantom-gap bug"); the constant `_BASELINE_MEAN_F_MICRO_W` in the same file
  says **0.5863** ("LAFA-congruent OBO releases/2025-07-22").
second number (mine, from the in-repo artifacts): averaging `f_micro_w` over the
  six prot_t5 K3 NK+LK rows of `experiments/phase3d_val227/` gives
  **0.658854** (lk-bpo 0.666302, lk-cco 0.704415, lk-mfo 0.667873,
  nk-bpo 0.581697, nk-cco 0.648089, nk-mfo 0.684745), and the mean unweighted
  `cafaeval_fmax` over the same six is **0.711924**.
date of evidence: all pre-2026-07-29 -> window: pre-wipe
frame: **the three are not the same measurement and must not be compared as a
  series.** 0.5849/0.5863 are on the FARM-EXP.15 artefacts
  (`agent-farm/results/executor-1780829216-57db/runs/prot_t5_K3_<cell>/{pred,gt}.tsv`,
  IA = `lafa_t0_Sep_2025/IA.tsv`, differing only in OBO release);
  0.658854 is on the `v226-v227` validation delta with
  IA = `IA-swissprot-exp-v227.txt`. Different split AND different IA table --
  and I measured above that those two IA tables disagree on 26.56% of their
  common terms. Both IA tables are declared canonical for band v227 by the lab's
  own registry, so the guard would pass either.
population: 0.5849/0.5863 population unknown and unrecoverable (the artefacts do
  not exist on this machine); 0.658854 is on 1,465 proteins summed over six cells.
platform gap: MURO for the EXP.15 pair -- the inputs were deleted on 2026-07-28
  and no operation can regenerate them, so neither 0.5849 nor 0.5863 can ever be
  reproduced or refuted here.
note: what a reader must not miss is that the difference the test file attributes
  entirely to the OBO release (0.5849 -> 0.5863, +0.0014) is smaller than the
  spread I measured between two IA tables both called canonical for the same
  band. The correction was made on one axis of the frame while a larger,
  unexamined axis of the same frame was left free.

## The withdrawn lab numbers are still live in PROTEA's CURRENT docs (echo, not evidence)
verdict: CONFIRMED
first number: the lab withdrew `0.7291 +/- 0.0028`, `0.6215` and named `0.4562`
  as not-to-be-cited on **2026-07-28** (commit `4a81079`).
second number (where they still stand today, in the tree this audit is told to
  use, `worktrees/protea-deploy` at `a5de702`, 2026-09-01 22:19):
    docs/source/quality/index.rst:138  "The multi-seed binary classifier recipe
      (3 independent seeds) produced ``NK+LK cafaeval 0.7291 +/- 0.0028``,
      confirming the benchmark is not a one-seed artefact", two lines after
      "providing a publishable statistical claim for Chapter 6".
      Last touched **2026-05-26**; `grep -niE 'withdraw|retract|manufactur|
      not.*cite|superseded'` over that file returns **nothing**.
    docs/source/adr/D34-selective-rerank-resurrection.rst  :Status: **Accepted**,
      carries `0.6215 +/- 0.0014` ("95% CI half-width on 9-cell mean") at line
      136 and discusses superseding `0.4562` at lines 33/141/168/199/242.
    also docs/source/adr/D36, docs/source/adr/D38,
      docs/source/architecture/orchestration.rst, tests/test_scoring_router.py.
  Outside PROTEA the same figures sit in `agent-farm/plans/thesis-writer/PLAN.md`,
  `plans/thesis-clean-iteration/PLAN.md`, `plans/farm-platform/PLAN.md`,
  `plans/bioinfo-quick/PLAN.md` and `prompts/thesis-writer.md`.
date of evidence: retraction 2026-07-28; echoes last edited 2026-05-16..2026-05-26
  -> window: pre-wipe on both sides, but the echoes are in a CURRENT tree.
frame: see the champions.md entry -- 0.6215 is a nine-cell unweighted mean, 0.7291
  a six-cell NK+LK selective mean. D34 attaches a "+/- 0.0014 95% CI half-width on
  9-cell mean" to a mean whose three PK cells are, by that same document's policy,
  deterministic baseline constants with zero delta. An interval over nine numbers,
  three of which cannot vary, is not an interval over nine measurements.
population: as above.
platform gap: nothing links a lab retraction to the platform's documentation.
  There is no operation, no lint and no CI check that asks "does any repository
  still publish a figure the producing repository has withdrawn". The
  `coauthor-guard`, `dataset-name-lint` and `reranker-token-lint` workflows show
  the pattern exists for other classes of string.
note: this is an ECHO in the norm document's sense -- the same number quoted in a
  second document that was quoting the first -- and it is the reason the
  retraction did not take. Anyone reading PROTEA's quality page today is told
  0.7291 is a publishable Chapter 6 claim.

## 80 rescued procedures are on an UNMERGED branch, including the 24 that would have produced the PK arm
verdict: CONFIRMED
first number: `git worktree list` shows three live lab worktrees, all on branches
  unmerged into develop:
    worktrees/lab-reporting  fix/lab-reporting-surface   ahead 2, behind 2  tip 2026-08-17 14:41
    worktrees/lab-gates      feat/lab-disjointness-gate  ahead 7, behind 1  tip 2026-08-17 15:14
    worktrees/lab-bundle     feat/gate-bundle-loader     ahead **16**, behind 0, tip 2026-08-19 09:10
  (lab-bundle's checked-out branch is `feat/gate-bundle-loader` but its upstream
  is `origin/feat/window-spans` -- a tracking mismatch.) Its 16 commits are the
  per-residue probe extraction, chunking instead of truncation, the streaming
  sweep after "two OOM kills", the length-banded reporting and the architecture
  routing object -- i.e. **the machinery behind `storage/probe/` (347 GB) is not
  on develop.**
second number (the more serious one): comparing full trees with
  `git ls-tree -r --name-only` under `LC_ALL=C`:
    `origin/preserve/research-procedures-from-storage`  1,123 files
    `develop`                                            1,049 files
    files on the preserve branch and **absent from develop: 80**
  Those 80 are:
    **73** `phase3{a,d,dpk,dtemp}_K{3,5,10}_<plm>_sweep.py` at the repository
      root -- one script per (phase, K, PLM) over the 8 PLMs. `develop` contains
      **zero** files matching `phase3.*sweep`.
    **7** fullgo training scripts: `m2_ab.py`, `m2_seedavg.py`, `train_m2_flex.py`,
      `merge_aspect.py`, `merge_aspect_sa.py`, `append_5plms.py`, `eval_m2ab.py`.
  `origin/preserve/champion-training-procedures` has 0 files absent from develop
  (fully merged). `origin/main` is 117 commits behind develop, tip 2026-05-07.
date of evidence: preserve branch tip 2026-07-28 -> window: pre-wipe
frame: n/a
population: n/a
platform gap: this is the sharpest instance of the platform argument in my slice.
  **develop keeps the RESULTS and not the code that produced them.**
  `experiments/phase3d_val227/` holds 138 result JSONs on develop; the 73 sweep
  scripts that emitted them are only on an unmerged branch. A reader of develop
  can read the numbers and cannot regenerate them.
note: **24 of the 73 are the `phase3dpk_*` family -- the PK arm.** I verified that
  `experiments/phase3d_val227/` contains only
  `['lk-bpo','lk-cco','lk-mfo','nk-bpo','nk-cco','nk-mfo']` and **no `pk-*` cell
  at all**. So the code to run the prior-knowledge third of the grid exists, was
  written, was rescued, and its results are nowhere in the repository. Given that
  the served population is the NK cell and an aggregate is ~95% prior knowledge,
  a champion table with no PK arm is a table over 6 of 9 populations, and the
  three that are missing are the ones that dominate any aggregate.

## Loose ends worth recording
verdict: CONFIRMED (each checked directly)
- **`main` is abandoned.** `origin/main` tip 2026-05-07, **117 commits behind**
  develop. The published release line does not reflect anything since May.
- **Two agent-farm clones exist on this machine**, and they disagree:
  `/home/xaxi/Thesis2/agent-farm` HEAD `bb06515` 2026-09-02 ("plans: bring the two
  untracked ablation documents under version control") versus
  `/home/xaxi/Thesis2/repositories/agent-farm` HEAD `c76588a` 2026-08-23
  ("plan: rung 2 closes the retrieval axis ... without a winner (#253)").
  CLAUDE.md's layout lists only the first. Ten days of plan divergence sit in the
  second, and a grep across `repositories/` reads the stale copy.
- **`.claude/RESUME.md`** (untracked) sits in the lab repo, written
  **2026-08-25T20:34:01Z**, trigger "near-limit", session
  `2530babf-865d-43bb-8976-f9e0b85ea3c8` -- the same session id as this audit's
  scratchpad. Independent corroboration that a session was cut off mid-work in
  this repository, and that the lab was the last thing it had open.
- **The retraction's scope is one file.** The top-level `README.md` says "Nothing
  in **this file** should be cited as a result" and **never mentions `fullgo/`**
  (grep for "fullgo" in README.md: 0 hits). `fullgo/README.md` therefore still
  opens "how PROTEA reached **first place** on the LAFA benchmark" and
  `fullgo/RESULTS.md` still publishes the full ladder
  (KNN 0.324 -> ... -> **0.391 champion, OUTRIGHT #1**, against TransFew 0.381
  and FunBind 0.366; per cell NK 0.477 / LK 0.482 / PK 0.215), last touched
  2026-06-15. To its credit `RESULTS.md` declares its frame in full (f_micro_w,
  IA-weighted micro-F averaged over 3 namespaces, sealed 7401-protein
  Sep_2025-Mar_2026 frame, levers fit on SELECT 220->227 and sealed once on
  227->230) and names its own residual exposure ("which levers to include being
  read off the sealed TEST mean"), with a SELECT-internal cross-check whose
  deltas are +0.0026 and +0.0027. Those two deltas are the size at which this
  project has repeatedly failed to resolve a winner.

## Dependencies: the lock is clean, and the two things the lab needs most are not in it
verdict: CONFIRMED
first number: `poetry check --lock` on the exported tree returns **rc=0** (only
  two `[project.license]` deprecation warnings). `poetry.lock` holds **104
  packages**, `lock-version 2.1`, `python-versions ">=3.12,<4.0"`,
  content-hash `cdd33f9420...`. The internal dependency is a commit pin,
  `protea-contracts @ git+...@cc30bc5e1b658ecf527bf3db08df66e655f4cb27`, and the
  installed dist-info records that exact `commit_id`. So the declared dependency
  set resolves and is consistent.
second number (what is missing from it): `grep '^name = "torch"' poetry.lock`
  -> **0 hits**. `grep cafaeval poetry.lock` -> **0 hits**.
  `grep -ci torch pyproject.toml` -> **0**. `[[tool.poetry.source]]` blocks in
  pyproject -> **0**.
date of evidence: 2026-09-02 -> window: post-wipe-current
frame: n/a
population: n/a
platform gap: the two heaviest capabilities of the lab -- running a torch encoder
  and scoring with cafaeval -- are both outside its dependency declaration.
  cafaeval is reached by shelling out to another repository's virtualenv; torch
  is installed by a shell script after the fact.
note: `scripts/install_gpu_torch.sh` runs
    `pip install --upgrade --force-reinstall --index-url
     https://download.pytorch.org/whl/${CUDA_VARIANT:-cu128} torch torchvision`
  with **no version constraint on torch or torchvision**, and its own header
  explains that "``pyproject.toml`` pins torch to the ``pytorch-cpu`` source on
  purpose". **There is no torch entry and no source block in `pyproject.toml`
  at all**, and `git log -S'pytorch-cpu' -- pyproject.toml` finds no commit that
  ever added one. So the script documents a mechanism that does not exist, and
  the actual behaviour is an unpinned install from a floating CUDA index into a
  lock that has never contained torch. Reinstalling the lab today gives an
  unknown torch version, and the lockfile can neither record it nor detect the
  drift.

---

# STATE OF protea-reranker-lab, ON THIS MACHINE, 2026-09-02

**What it is.** A separate GitHub repository (not a PROTEA plugin), Poetry
project, Unlicense, single author, 132 commits from 2026-04-21 to 2026-08-17,
PR-numbered to #120. 1,049 tracked files, 492 of them Python. It pulls frozen
feature parquet exported by PROTEA's `export_research_dataset` operation into
MinIO, trains LightGBM rerankers (LambdaMART and binary) per (category, aspect)
cell without loading a full DataFrame, scores them by shelling out to cafaeval,
and publishes winning boosters back to PROTEA's `RerankerModel` registry by
reference. It has grown a second, larger life as the archive of every research
procedure that ran outside a repository: `research/` (224 .py), `results/`
(98 .py, no results), `fullgo/` (14 .py, the LAFA champion), plus four loose
study scripts at the root.

**Branch.** `develop`, at `6640393`, **one commit behind** `origin/develop`
(`270c46c` #120). Working tree clean. Last fetch 2026-08-18; the checkout itself
was created 2026-07-29 01:48, the day after the reinstall.

**What it can run today, precisely.**
  RUNS: the test suite (584 pass in 5.78 s, all on synthetic fixtures), ruff,
    mypy, the Sphinx docs, and any pure-library code path.
  DOES NOT RUN: anything that needs data. No feature parquet exists locally
    (`datasets/` is cards only); torch is not installed and not in the lock;
    cafaeval is not installed and not in the lock; `host_paths.ia_table()`
    raises; 329 of the 1,049 tracked files carry 953 paths under
    `/home/frapercan`, a home that does not exist.
  RUNS BUT LIES: `host_paths.protea_python()` cannot raise -- it falls through to
    `sys.executable` -- so a cafaeval scoring run would fail inside a subprocess
    rather than at the boundary, which is the failure mode that module was
    written to abolish.

**What survives as real measurement.** One body only:
`experiments/phase3d_val227/` -- 138 per-cell JSONs, full precision, with
populations, over 8 PLMs x K{3,5,10} x 6 NK+LK cells on the v226->v227 delta.
Everything else in the repository is either withdrawn (README, 2026-07-28),
un-withdrawn but stale (`champions.md`, last written 2026-05-23), out of scope of
the withdrawal (`fullgo/`, 2026-06-15), or procedure without output.

**What was lost.** The FARM-EXP.15 artefacts the golden regression pins against
(`agent-farm/results/executor-1780829216-57db/`) are gone from this machine, so
neither 0.5849 nor 0.5863 can ever be reproduced or refuted here. The `runs/`
tree the one failing test looks for is gitignored and gone. `study_v23` artefacts
are gone. `storage/learned_encoders/` does not exist.

**Every number in this repository predates 2026-08-27.** The newest commit is
2026-08-17; the newest measurement artifact family (`phase3d_val227`) predates
2026-07-29. Under the rule that anything before the registry wipe is not evidence
about the current window, **the lab currently contributes zero evidence about the
current window**, and its principal value is as the only surviving copy of the
procedures.

**The single most useful thing to fix.** Not the username. The IA guard:
`band_registry_bridge.BANDS` accepts any file *named* `IA.tsv` or
`IA-swissprot-exp-v227.txt` as canonical for band v227, and this machine holds
three such files that disagree on 26-38% of their values, with maximum
differences of 2.8 and 14.6 IA units. Every `f_micro_w` the lab has ever reported
depends on which one was on the path that day, and the guard designed to catch
exactly that class of error cannot see it.
