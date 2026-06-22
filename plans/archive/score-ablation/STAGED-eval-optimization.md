# A-SCORE eval optimization — all 4 wins (memory + time)

Goal: collapse the cost of the ablation/HPO. Today each scoring_config re-runs a FULL
`run_cafa_evaluation` (load predictions + build GT + cafaeval), and only the score column
changes → ~N× redundant work. Target: one load, many cheap re-scores.

## The 4 wins (in one PROTEA PR, base develop)

1. **Batch re-score operation** (the structural win). New op/endpoint: given one
   `prediction_set_id` + a LIST of `scoring_config_id`s (and the eval_set + IA), load the
   prediction feature matrix + the GT ONCE, then per config compute `score = features @ weights`
   (cheap numpy via the existing `_vectorized_scores` from #628) and run only cafaeval's
   τ-sweep. Writes one `evaluation_result` per config, identical to N separate evals.
   → turns N full evals into 1 load + N trivial re-scores.

2. **GT caching**. The eval_set IA-weighted ground truth is identical across all configs.
   Confirm whether it is already materialised (`EvaluationSet.groundtruth_uri`) and reused, or
   rebuilt per eval (the heavy join + IA). If rebuilt, cache it (disk artifact keyed by
   eval_set) and reuse across the batch + across separate evals.

3. **Column-pruned streaming load** (memory). Load only the columns the score needs
   (`_BASE_SCORE_COLS` + the config-referenced feature columns + protein/go_id), not all ~60
   `go_prediction` columns; stream in chunks rather than materialising 2.5M rows (K=30) at once.

4. **Parallel-safe + worker scaling** (wall-clock). Ensure `run_cafa_evaluation` is
   parallel-safe so `manage.sh scale protea.evaluations N` cuts wall-clock ÷N. Bound N to RAM
   (OOM lessons 2026-06-11: each worker holds the working set; N=2-3 on this box). The batch op
   (win 1) makes most of the parallelism unnecessary, but keep both.

## Sequencing (load-bearing)
This touches the SAME eval path (`run_cafa_evaluation`, `_run_cafa_artifacts`, `_vectorized_scores`)
as PR #628. To avoid conflict/rework, **branch off develop AFTER #628 merges**, building on its
vectorized scorer + `params`. Do NOT race #628.

## Acceptance
- The batch op produces evaluation_results byte-identical to N separate `run_cafa_evaluation`
  runs (golden test on a fixed set + 3 configs).
- Measured: batch of K configs costs ~1 load + K re-scores (report wall-clock + peak RSS vs the
  N-separate-evals baseline).
- GT built/loaded once per batch. Memory: peak RSS for K=30 set load drops vs full-column load.
- Local CI green (ruff+mypy+pytest+smell), PR base develop, no AI mentions.

## Fires
After #628 merges → conductor spawns an executor off develop with this spec. Then the
re-run of A-SCORE.1 (on the de-saturated scorer) uses the batch op = fast.
