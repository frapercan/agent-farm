# Native target-selection alignment (reproduce the official LAFA 7401 frame end to end)

Follow-up to `crossobo-native-delta` (the cross-OBO override, shipped as PROTEA PR #671). The
cross-OBO fix is necessary but NOT sufficient: with the t0 side propagated under the correct OBO
(`releases/2025-07-22`), the native reconcile recovers 99.2% of the official PK targets but produces a
**superset** of the official frame. This slice closes that residual so the native pipeline reproduces
the official 7401 frame, making the on-platform native number auditable end to end (no external
import). Memory: `project_phantom_gap_crossobo_2026_06_23`.

---

## 1. The residual (measured, read-only)

Native reconcile on the live v227->v230 pair (old=c905dffa, new=2394b9a1), t0 under 2025-07-22:

```
                  total   vs official 7401
official 7401     7401    -
native (fixed t0) 8725    intersection 7347 | native-only +1378 | official-only 54
```

- **+1378 native-only**: proteins PROTEA's raw temporal delta includes that LAFA's 7401 excludes.
- **54 official-only**: proteins LAFA has that even the fixed native delta misses (the audit's small
  residual: genuinely new leaves or part_of/regulates relations).

## 2. Root cause: LAFA restricts to a TARGET UNIVERSE before classifying

LAFA does not score the raw delta. Per `CAFA_forever/workflows/evaluate_window.nf`:

```
common_targets_ch = INTERSECT_TARGETS(window_inputs_ch)     # restrict to the target universe
groundtruth_ch    = CLASSIFY_GROUNDTRUTH(common_targets_ch)  # then split NK/LK/PK
```

`INTERSECT_TARGETS` (`CAFA_forever/modules/local/evaluation.nf`) calls
`democafa.datacollection.compare_fasta(t0/test_sequences.fasta, t1/test_sequences.fasta)` and keeps
`diff_test_sequences_common.fasta`: the proteins **present in BOTH timepoints' curated
`test_sequences` universe** whose annotations changed. PROTEA's `compute_evaluation_data_reconciled`
has no such universe restriction, so its delta is a superset. The +1378 are delta proteins outside
LAFA's `test_sequences` target universe (to characterise: likely non-reviewed / not in the curated
per-release test set / present in only one timepoint).

## 3. Plan

### T1. Characterise the +1378 and the -54 (read-only, cheap)
Diff the native-fixed delta against `groundtruth_targets.tsv` (7401). For the 1378 native-only, check:
in SwissProt-reviewed? in `democafa` `test_sequences` for v227 AND v230? present in both timepoints?
For the 54 official-only, confirm they are new-leaf / new-relation cases. Output: the exact selection
predicate LAFA applies.

### T2. Derive the target universe natively
Reproduce LAFA's target universe from the same source, NOT by hardcoding the 7401 list (that would be
circular). Options, cheapest first:
- the `democafa` `test_sequences` per release (if reproducible on-platform), or
- the SwissProt-reviewed-with-sequence set per GOA release the proteins already carry, intersected
  t0 AND t1.
Validate the derived universe reproduces the 7401 target set (not the answer leaking in).

### T3. Add a target restriction to the native delta
`compute_evaluation_data_reconciled` (and the `generate_evaluation_set` payload) gains an optional
target-universe filter (e.g. `target_accession_source` / a target set id): the delta is intersected
with the universe BEFORE NK/LK/PK classification, matching `INTERSECT_TARGETS` then
`CLASSIFY_GROUNDTRUTH`. Backward compatible (no filter = current behaviour). PROTEA-stack PR, base
develop, with a unit test.

### T4. GATE
Run the native generate with cross-OBO override (#671) + target restriction on (c905dffa, v230):
- delta intersection with 7401 -> ~7401, native-only -> ~0, official-only -> ~0.
- **Report PK precision AND recall separately, before/after** (downside guard: PK precision is
  PROTEA's known bottleneck; over-including PK could hurt). Compare the resulting native eval set's
  downstream f_micro_w to the externally-imported 34a634a8 (must match within noise).
- Only on a clean GATE: regenerate the live native eval set from the native pipeline (replacing the
  externally-imported 34a634a8), so the number is legitimately native.

### T5. Durable wiring
- `band_registry.py`: the v227 band already pins the asymmetric OBO pair; add the target-universe
  source so the auto-eval path produces the correct frame.
- `_enqueue_auto_eval_job` (`load_goa_annotations.py`): pass the native-snapshot overrides + target
  source so the automatic delta is born in the correct, target-restricted frame.

## 4. Why this matters / does not

- Corrects the MEASUREMENT pipeline (native reproduces the official frame), not the reported number
  (already on 7401 via the external eval set). Payoff = auditability + removing the external-import
  dependency.
- Do NOT regenerate the live eval set until T4 passes; the raw native delta (8725) is WORSE than the
  externally-aligned 7401, so an early regenerate would regress the frame.

## 5. Process constraints

- PROTEA-stack PRs base `develop`; agent-farm plan edits base `main`; commit the plan before spawning.
- `POST /jobs` with `{operation, payload}` from the registry; never ad-hoc curl/wget to endpoints.
- Never point agents at the live DB (`protea-postgres-1`).
- No Co-Authored-By / AI mentions; no em-dashes in publishable prose.

## 6. Reference

- Residual measured by the read-only validation in `crossobo-native-delta` (memory).
- LAFA target selection: `CAFA_forever/modules/local/evaluation.nf` (`INTERSECT_TARGETS` ->
  `democafa.datacollection.compare_fasta`; `CLASSIFY_GROUNDTRUTH`), `workflows/evaluate_window.nf`.
- Cross-OBO override: PROTEA PR #671. eval set id `34a634a8-5739-4b04-923c-26db9eaab21e`.
