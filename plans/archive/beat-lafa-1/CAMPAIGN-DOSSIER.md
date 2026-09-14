# Campaign dossier — native LAFA reranker, deep inspection (2026-06-20/21)

Definitive record of what we tried, HOW we tried it, the state, the plan, and the insights.
Nothing here is from memory alone; every number is an EvaluationResult id, every artifact a path.

---

## 1. Executive state

- **Best confirmed native number: f_micro_w = 0.3745** (EvalResult `b21b187c`), official LAFA
  harness (frame=lafa, 7401 targets, TOI + PK-known exclusion), UI-verifiable on /benchmark.
  NK 0.4645 / LK 0.4526 / PK 0.2065. **#1-class on NK**, top-3 LAFA overall (FunBind 0.366 <
  **0.3745** < TransFew 0.381).
- Research method's sealed OFFLINE champion = **0.391** (#1, ahead of TransFew), but frame-optimistic
  and its source files are DELETED (`/tmp/canon_composite.tsv` etc., not byte-reproducible).
- We have NOT surpassed #1 natively. Bottleneck = **PK** (0.2065 vs TransFew ~0.230),
  precision-limited.
- Stack: dev workspace on develop `5809117` (#664 self_prior + #665 IA + #666 softprop live),
  restarted clean, torch GPU intact.

---

## 2. The experiment ledger (every eval on prediction set f377adae)

All on prediction set `f377adae-047a-4e52-9e79-b43d5e722a70` (the lean 7401 LAFA predict),
eval set `34a634a8` (LAFA GT), official harness unless noted.

| EvalResult | time | experiment | NK | LK | PK | MEAN | verdict |
|---|---|---|---|---|---|---|---|
| `f42faad8` | 06-20 19:15 | lean-31 boosters (baseline) | 0.4524 | 0.4362 | 0.1992 | **0.3626** | baseline |
| `184579b6` | 06-21 08:30 | + self_prior (string-fix) | 0.4627 | 0.4424 | 0.2016 | **0.3689** | +0.0063 SHIPPED |
| `cb77d55d` | 06-21 11:07 | + IA ("both") | 0.4640 | 0.4513 | 0.2013 | **0.3722** | +0.0033 SHIPPED |
| `1df357be` | 06-21 12:14 | clean-15 curated | 0.4514 | 0.4494 | 0.1973 | 0.3660 | REFUTED -0.0062 |
| `7521ab8a` | 06-21 13:18 | + S2 scale_pos_weight PK | 0.4640 | 0.4513 | 0.2065 | **0.3739** | +0.0017 |
| `b21b187c` | 06-21 14:25 | + S2 all aspects (**BEST**) | 0.4645 | 0.4526 | 0.2065 | **0.3745** | BEST CONFIRMED |
| `b657e250` | 06-21 18:12 | + L2 soft-prop (all) | 0.4657 | 0.4560 | 0.1939 | 0.3719 | REFUTED -0.0026 (PK reversed) |

Note `184579b6`/`cb77d55d`/`7521ab8a` used a backfill shortcut (see §4); `b21b187c`/`b657e250`
used the registered S2 trio; `cb77d55d` is the IA headline (0.3722).

---

## 3. Methodology (HOW we tested)

- **Temporal split:** TRAIN (rolling pairs v160->v220) -> VALIDATION/SELECT (220->227) ->
  TEST/LAFA (227->230, 7401 targets, frame=lafa).
- **De-risk-on-validation-first:** build a lever as an overlay/post-proc, train+score on the
  220->227 VALIDATION frame (cheap), only proceed to the TEST cycle if it clears the baseline.
  This caught descendant-prior (-0.0072) and the L2 false-positive (see the lesson in §6).
- **Sanity gate:** every offline score reproduces the known baseline (e.g. L2 baseline reproduced
  0.3720 EXACTLY) before any delta is trusted.
- **Validation recipe is OPTIMISTIC** (no-TOI, no-PK-exclude); only the SAME-recipe relative delta
  is meaningful. **TEST recipe is OFFICIAL** (TOI + PK-exclude), via the platform eval.
- **cafaeval recipe (no-TOI baseline):** ia, prop=fill, norm=cafa, no_orphans, th_step=0.01,
  MAX-collapse per (protein, go_id), OBO+IA from lafa_t0_Sep_2025.
- **TEST cycle:** register boosters (RerankerModel rows) -> run_cafa_evaluation via POST /jobs
  (queue protea.evaluations) -> EvaluationResult on /benchmark.

---

## 4. Levers — full detail (hypothesis / build / test / result / artifacts)

### SHIPPED + transfers

**self_prior (string-fix)** — +0.0063 TEST (0.3626->0.3689).
- Hypothesis: the platform's self_prior_score was dead in training (matched snapshot-specific INT
  go_term_id across 13 snapshots -> never lined up). Fix: match by snapshot-invariant go_id STRING.
- Build: PROTEA #664 (apply_self_prior). For the TEST number, shortcut = re-apply the
  string-fixed boosters to f377adae (the bug is training-only; at serve the single-snapshot int
  match already worked). Boosters: `native_boosters_selfpriorfix_serve/` (self_prior_fixed renamed
  to self_prior_score). RerankerModel `3f281105/71890148/15568a5b`.
- Verdict: transfers (validation +0.0060 ≈ TEST +0.0063). SHIPPED.

**IA (information accretion)** — +0.0033 TEST (0.3689->0.3722, EvalResult `cb77d55d`).
- Hypothesis: the champion's per-term IA feature (the cafaeval f_micro_w weight) is missing at serve.
- KEY INSIGHT: IA is a post-KNN JSONB feature like self_prior/association, NOT a feature_schema_sha
  change. Only serve-missing champion feature.
- Build: PROTEA #665 (apply_ia in `_ia_feature.py`, coordinator passthrough, eval readback) +
  protea-contracts #36 (compute_ia/ia_file, v0.7.0). TEST shortcut = backfill IA into f377adae's
  JSONB (1.93M rows, SQL UPDATE joining go_term + IA.tsv, faithful replica of apply_ia=IA[go_id])
  + native-both boosters. RerankerModel `d2dc467c/70ebcced/e9c946d9`. Boosters
  `native_boosters_both_serve/`.
- Verdict: transfers (validation +0.0056 vs TEST +0.0033, slightly less). SHIPPED.

**S2 scale_pos_weight (PK then all aspects)** — +0.0023 TEST (0.3722->0.3745).
- Hypothesis: PK's severe class imbalance + th_step sweep leave a sub-optimal F operating point;
  upweighting rare positives (scale_pos_weight=neg/pos) reshapes scores.
- Build: retrain PK (`train_pk_s2.py`) then NK+LK (`train_nklk_s2.py`) on the v5 export, same
  lean-31+IA recipe + scale_pos_weight. Boosters `native_boosters_pk_s2/`, `native_boosters_nklk_s2/`.
  RerankerModel `f0669e41` (pk), `198baf99/68f3232c` (nk/lk).
- Verdict: PK transferred BETTER than validation (val +0.0020 -> TEST +0.0052!). NK/LK marginal
  (+0.0012/+0.0034). `b21b187c` = 0.3745 = BEST. SHIPPED (boosters registered).

### REFUTED

**clean-15 curated representation** — REFUTED, 0.3660 < lean-31 0.3722 (EvalResult `1df357be`).
- Hypothesis: the champion's 16 curated features beat the platform's 31 raw -> restrict to a
  curated subset. Build: `train_clean15.py` (champion's 16 mapped to platform cols, num_leaves=31).
  Boosters `native_boosters_clean15/`. RerankerModel `ed589978/4ab529bc/7b4ff840`.
- Verdict: REFUTED. Restricting LOSES signal (NK -0.0126). The platform's richer lean-31 BEATS the
  curated representation -> the residual is NOT representation.

**descendant-of-known-t0 DAG prior** — REFUTED on validation, -0.0072 PK (no TEST cycle spent).
- Hypothesis: PK proteins acquire DAG-descendants of their known non-exp t0 terms (annotation
  refinement). descendant_prior=1 if ancestors(candidate) intersect K(p) and candidate not in K(p).
- Build: `build_descendant_prior.py` (reuses K(p) from selfprior_fix_data + OBO ancestors;
  overlays `selfprior_ia_experiment/{train,eval}_descprior.npz`) + de-risk
  `train_score_descprior_pk.py` (validation PK).
- Verdict: REFUTED. Validation PK 0.3648 vs both 0.3720 = -0.0072; descprior importance rank 16/32
  (weak, the booster overfits it as noise). De-risk on validation SAVED the TEST cycle.

**L2 soft Pmin/Pmax post-processing** — REFUTED on official TEST, -0.0026 (PK reversed).
- Hypothesis (ProtBoost 4.5): averaged soft propagation reshapes scores for a better F point.
  Pmin(N)=min(Pmin(parents))*0.7+P*0.3 (root->leaf); Pmax(N)=max(Pmax(children))*0.7+P*0.3
  (leaf->root); P_post=(Pmin+Pmax)/2.
- Build: de-risk `l2_softprop_pk.py` (validation, reuses `both` PK booster, no retrain) ->
  productized PROTEA #666 (opt-in `softprop` flag in run_cafa_evaluation, module
  `_run_cafa_softprop.py`).
- Result: validation PK +0.0141 (sanity-gated 0.3720), but OFFICIAL TEST PK -0.0126 (EvalResult
  `b657e250`: NK 0.4657/LK 0.4560/PK 0.1939 = 0.3719). FULL REVERSAL. Net -0.0026.
- Verdict: REFUTED net. Helps NK/LK (+0.0012/+0.0034), hurts PK; NK/LK-only projects ~0.3761
  (+0.0016, needs a per-aspect flag). Code kept in-platform as opt-in.

### Prior-session levers (context, in fullgo memory)
Re-refuted earlier: SVD label-emb, GCN-as-label-emb, BioBERT GO-def, IEA, freq-heads, ensemble
calibration, exp-only KNN, negative-NOT propagation, v6 emb_pca/anc2vec (overfit), structure
(vetoed). Trajectory pre-session 0.324->0.358->0.381->0.391 (offline champion).

---

## 5. What shipped (productized PRs)

- PROTEA **#664** self_prior snapshot-invariant string match.
- PROTEA **#665** IA per-candidate feature (apply_ia + coordinator passthrough + eval readback).
- PROTEA **#666** soft Pmin/Pmax post-processing (opt-in softprop flag).
- protea-contracts **#36** compute_ia + ia_file payload (v0.7.0, on main).
- All merged to develop `5809117`. Two stack restarts this session (clean, torch intact).

---

## 6. Insights / lessons (the durable learnings)

1. **CRITICAL — post-proc levers must be de-risked on the OFFICIAL recipe.** For levers that
   interact with propagation + PK-known exclusion (L2, L1 CondProbMod, L3 clipping), the optimistic
   validation recipe (no-TOI/no-PK-exclude) MISLEADS. L2: PK +0.0141 validation -> -0.0126 TEST.
   FEATURE levers (self_prior/IA/S2) transfer because their VALUE does not interact with the recipe.
2. **The residual to 0.391 is feature-value fidelity + frame optimism, NOT representation/pool/
   harness/data/config** (all matched + tested). Representation refuted (clean-15 < lean-31).
   Champion's offline sources are deleted -> 0.391 not byte-reproducible.
3. **PK is precision-limited, the field's open problem** (CAFA5 assessment). At Fmax: recall ~0.25,
   precision ~0.15, coverage 1.0 -> too many plausible-but-false candidates ranked high. Needs a
   DISCRIMINATIVE signal, not another plausibility prior (that's why descprior failed).
4. **De-risk-on-validation works for feature levers** (caught descprior cheaply); **richer raw
   features beat curated subsets** for our LightGBM (clean-15 lost).
5. **IA/self_prior/association are post-KNN JSONB features** (no feature_schema_sha change) ->
   cheap to add; the heavy bit is the predict/restart, not the schema.
6. **Run the FULL repo CI** (ruff protea scripts + check_smells without --target = file budgets +
   bandit), not just changed-file targeted tests (cost two CI-fix rounds on #665).
7. **scale_pos_weight transferred BETTER than validation predicted** (val +0.0020 -> TEST +0.0052)
   -- a rare positive surprise; calibration of the score distribution genuinely helps the global-
   threshold f_micro_w.

---

## 7. The plan to surpass #1 (agent-farm/plans/beat-lafa-1/PLAN.md)

Bibliography-grounded (ProtBoost arXiv:2412.04529, CAFA5 #1 GOCurator, TransFew, GORetriever,
DeepGO-SE, Obozinski 2008 guardrail), product-integrated (meta-reranker ADR-D43, each lever = one
EvidenceScorer or post-proc, no refactor). Recalibrated by the L2 lesson:

- **L6 retrieved hard-negatives** (best next bet): FEATURE lever (transfers), discriminative for PK
  precision -- per candidate, features from KNN neighbours that ARE annotated in the aspect but LACK
  the term (fraction lacking; sim-margin supporting-vs-not). Reuses the KNN set; needs neighbour-
  level data exposed (the export aggregated it away) -> the heavier build.
- **L1 CondProbMod** (ProtBoost 4.3, exact formula captured): training-variant (exclude all-parent-
  zero pairs) + post-proc recompute + ensemble. POST-PROC -> de-risk on the OFFICIAL recipe.
- **L3 low-prob clipping**, **L2 soft-prop (NK/LK-only)**, **L4 freq-bucket** -- cheap, de-risk on
  official recipe.
- **L5 GCN-stacker** over the score vector with GO-DAG message passing (ProtBoost's biggest jump
  0.59->0.62; the meta-reranker endgame; tiny <=8d GO emb to avoid the v6 overfit trap).
- **L7 GO-def text cross-encoder, PK-ONLY** (literature exists for known proteins; NK-unsafe).
- Honest: no single lever promises >0.381; ProtBoost STACKED 0.47->0.62 over 7 components.

---

## 8. Artifact map (where everything lives)

- **Experiment scripts:** `storage/fullgo_models/` -> train_clean15.py, train_pk_s2.py,
  train_nklk_s2.py, build_descendant_prior.py, train_score_descprior_pk.py, l2_softprop_pk.py,
  train_native_boosters.py, score_azucar_validation.py.
- **Boosters:** `storage/fullgo_models/native_boosters_{both_serve,selfpriorfix_serve,clean15,
  pk_s2,nklk_s2,lean,v5,azucar,assocfix}/`. Champion 0.391 boosters at
  `storage/fullgo_models/ensemble_gbm_{NK,LK,PK}.txt` + `feature_spec.json`.
- **Data:** v5 export `datasets/fullgo-union-SELECT-160-220-227-v5` (MinIO, 74M train rows);
  overlays `selfprior_ia_experiment/{train,eval}_overlay.npz` (self_prior_fixed + IA) +
  `{train,eval}_descprior.npz`; K(p) source `selfprior_fix_data/{nonexp_annotations.tsv,
  goterm_map.tsv,sets.csv}`; IA.tsv `protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv`.
- **fullgo champion code:** `worktrees/native-boosters-lab/fullgo/` (ensemble_seal.py = the 0.391
  recipe, sources in /tmp DELETED).
- **Eval results:** see the §2 ledger ids (prediction set f377adae, eval set 34a634a8).
- **RerankerModels:** native-{both,clean15,pk-s2,nk-s2,lk-s2,selfpriorfix,lean}-{cat}.
- **Plan:** `agent-farm/plans/beat-lafa-1/{PLAN.md, CAMPAIGN-DOSSIER.md}`.
- **Backlog:** `IMPROVEMENTS-BACKLOG.md` (rows H4-*). **Session resume:** `RESUME_2026-06-21.md`.
- **Memory:** `project_beat_lafa_1_plan_2026_06_21.md`, `project_native_gap_diagnosis_2026_06_20.md`,
  `feedback_native_reranker_procedure_2026_06_21.md`.

---

## 9. How to resume

1. Best number = 0.3745 (b21b187c); the registered S2 trio (198baf99/68f3232c/f0669e41) reproduces it.
2. Next lever = **L6 hard-negatives**: expose KNN neighbour-level data (predict pipeline already
   computes it), build the negative-evidence features, de-risk on validation (FEATURE lever, transfers).
3. Any POST-PROC lever (L1/L3): de-risk on the OFFICIAL recipe (TOI+PK-exclude), not the optimistic one.
4. Stack is live on develop 5809117; the S2 boosters + IA + softprop are all in-platform.
