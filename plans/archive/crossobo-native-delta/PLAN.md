# Cross-OBO native delta alignment (227->230) to the official LAFA 7401 frame

Source: closed audit 2026-06-23 (memory `project_phantom_gap_crossobo_2026_06_23`). Every claim below
was traced layer by layer and verified against artefacts (band_registry comment, the two OBO
data-versions, the 7401/7002 lists, `compute_evaluation_data_reconciled`).

---

## 1. The finding

PROTEA's native eval delta for the GAF window 227 (2025-09-04) -> 230 (2026-03-04) has **7002
targets**; the official LAFA frame (`groundtruth_targets.tsv`) has **7401**. Cross of the two lists:

```
intersection 6081 | LAFA-only (PROTEA loses) 1320 | PROTEA-only 921    churn 99.8% PK (1317/1320 PK)
```

**Root cause: ontology-version churn on the t0 side only.** Not evidence filtering (42/42 lost pairs
have EXPERIMENTAL IMP/IDA evidence, zero IC/TAS in QuickGO), not a missing import (the support
annotations are pre-window, the proteins ARE in the store, 1314/1317). The lost terms are NOT
reachable from the protein's t0 knowledge under the **t0 OBO** (0% = correct control), but ARE under
the **t1 OBO** (98.7%). Concrete trace: a new edge `GO:0031507 --is_a/part_of--> GO:0022607 /
GO:0070828` was added between go-basic 2025-07-22 and 2026-01-23. The biology (IMP from 2020) did not
change; the GO graph did.

**The bug, precise:** PROTEA bound the t0(227) side to snapshot `2026-01-23` (too new, churn already
baked in) instead of `2025-07-22`. The t1(230) side `2026-01-23` is ALREADY correct and matches LAFA.
The pre-registry v226/v227/v230 eval_sets all shared `releases/2026-01-23` (the snapshot-sharing IS
the phantom-gap), documented in `PROTEA/protea/core/band_registry.py` (~line 113).

**Exact OBOs (reverse-engineered by recovery rate):**

| side | GOA release | go-basic data-version | local path |
|---|---|---|---|
| t0 | 227 (2025-09-04) | `releases/2025-07-22` | `protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo` |
| t1 | 230 (2026-03-04) | `releases/2026-01-23` | `lafa-smoke/data/go-basic.obo` |

> WARNING: pinning `2025-07-22` to BOTH sides kills the churn and gives a number that does NOT match
> 7401. Parity REQUIRES the asymmetric pair t0=2025-07-22, t1=2026-01-23.

---

## 2. Direction: A + C in parallel

- **C (safety net, already live):** keep reframing predictions against the official 7401 targets +
  OBO (RESULTS.md). This is why the reported ~0.327 ensemble / **0.3745 native champion** are ALREADY
  on 7401. Action: make C a reproducible job, not a one-off.
- **A (build, this slice):** reproduce the cross-OBO native delta on-platform so the native number is
  legitimate and auditable end to end, and matches 7401.

The infra already supports cross-OBO: `go_term` / `go_term_relationship` are per-snapshot, and
`compute_evaluation_data_reconciled` (`PROTEA/protea/core/evaluation.py:561`) already propagates each
side under its own DAG over `go_id` text (no need to re-bind the 227/230 rows).

---

## 3. Plan A (minimal: 1 ingest + 1 generate; no migration, no algorithm change)

### A1. Ingest the t0 OBO
Ingest go-basic `releases/2025-07-22` via `load_ontology_snapshot`
(`PROTEA/protea/core/operations/load_ontology_snapshot.py`; idempotent on data-version). The
2026-01-23 snapshot is already ingested. Dispatch via `POST /jobs` (operation from the registry),
never ad-hoc curl.

- **GATE 1:** the `OntologySnapshot` for 2025-07-22 + its `go_term_relationship` rows appear.

### A2. Reconciled generate
Dispatch `generate_evaluation_set` via `POST /jobs` with:
```
old_native_snapshot_id    = <2025-07-22>
new_native_snapshot_id    = <2026-01-23>   (already exists)
pivot_ontology_snapshot_id = <2026-01-23>
```
This forces `same_snapshot=False` -> `compute_evaluation_data_reconciled`
(`generate_evaluation_set.py:102-134`).

- **GATE 2 (the real one):** compare `delta_proteins` and the NK/LK/PK split against the local
  `groundtruth_targets.tsv` (7401). Success = ~7401, buckets approx NK399 / LK868 / PK6340.
  Prediction: ~98.7% recovery -> a hair from 7401; residual ~7 proteins / 45 pairs (genuinely new
  leaves or part_of/regulates relations) is an expected, separable follow-up.
- **GATE 2 MUST report PK precision AND recall separately, before/after**, to catch the downside
  (PK precision is PROTEA's known bottleneck; recovering 1317 PK targets could over-predict).

### A3. cafaeval confirmation
Run `run_cafa_evaluation` with pivot=2026-01-23 (`run_cafa_evaluation.py:337-338, 456-458`); the
native number must now match C's 7401-reframed number.

### A4. Durable wiring
- `band_registry.py` BANDS: pin the ASYMMETRIC cross-OBO pair (t0=2025-07-22, t1=2026-01-23). Do NOT
  collapse to a single congruent OBO for the window.
- `_enqueue_auto_eval_job` (`load_goa_annotations.py:341-344`): add `pivot_ontology_snapshot_id` so the
  automatic delta is born in the correct frame.

---

## 4. Score implication (manage expectations)

- The leaderboard number is ALREADY on 7401 via C; aligning A does NOT change it. A makes the
  on-platform NATIVE number RISE from the phantom-low to the true value (closes the phantom-gap).
- Direction: improvement. The 1317 recovered PK targets are high-level "easy" terms (high recall via
  propagation from strong t0 signal).
- Magnitude: probably MODEST in IA-weighted Fmax (those high terms have low IA), larger in unweighted
  Fmax.
- Downside risk: over-predicting on PK could eat the gain. GATE 2 reports PK precision/recall split.
- This corrects MEASUREMENT, not capability or relative standing (rivals are also on 7401).

---

## 5. Process constraints

- PROTEA-stack PRs base `develop`; agent-farm plan edits base `main`; commit the plan before spawning.
- `POST /jobs` with `{operation, payload}` from the registry; never ad-hoc curl/wget to endpoints.
- Never point agents at the live DB (`protea-postgres-1`).
- No Co-Authored-By / AI mentions; no em-dashes in publishable prose.

## 6. Reference artefacts (local)

- 7401: `CAFA_forever/data/releases/Sep_2025_Mar_2026/groundtruth_{targets,PK,PK_known,NK,LK}.tsv`
- 7002 native: `storage/ensemble_audit_2026_06_13/OLD_gt_34a634a8_7002.parquet`
- OBO t0: `protea-lafa-knn/lafa_t0_Sep_2025/go-basic.obo` (2025-07-22)
- OBO t1: `lafa-smoke/data/go-basic.obo` (2026-01-23)
- Nextflow LAFA cross-OBO confirmed: `CAFA_forever/modules/local/evaluation.nf:55-56` (`--graph` t0
  `--graph2` t1)
- eval set id: `34a634a8-5739-4b04-923c-26db9eaab21e`
