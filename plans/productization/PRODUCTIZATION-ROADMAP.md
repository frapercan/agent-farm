# PROTEA + LAFA productization roadmap (2026-07-02)

Grounded review of the live PROTEA platform and the local LAFA (cafa_forever)
deployment, with a sequenced, risk-annotated fix plan. Written after the
serve-offline reconciliation (serve mean 0.3536 -> 0.4004, within 0.006 of the
offline champion 0.4063). The reconciliation is real; this doc is about the
*productization* gaps it exposed.

## The core problem: three decoupled serving surfaces, three numbers

Verified in code + live DB, not from memory:

| surface | pipeline | number | how it is selected |
|---|---|---|---|
| `/annotate` (interactive product) | dense PLM retrieval (`param_count ASC`) + OLD reranker trio `native-s2-assocfix` (7fcecf26, `is_active=true`) | ~0.3745-era | `active_or_latest_reranker` (active-first) + `EmbeddingConfig.param_count.asc()` |
| benchmark (`evaluation_result` in DB) | d8979601 retrieval + composite classifier routing + S2e trio `851849df` (`is_active=FALSE`, via explicit payload ids) + InterPro graft | **0.4004** | explicit `reranker_model_id_*` in the `predict_go_terms` payload |
| LAFA board (public, `protea-lafa.ngrok.app`) | offline champion, hand-injected `predictions_protea.tsv` | 0.4063 | manual file write via `protea-lafa-knn/score_and_inject_windows.sh` |

The stated NFR is "UI = single source of truth, every number live-verifiable."
Today that is not met: the reconciled pipeline (0.4004) reaches the *benchmark*
path only; `/annotate` still runs the old reranker + dense retrieval; the board
is a hand-placed TSV. Three pipelines, three numbers, no single source.

## Findings (by severity)

1. **Three decoupled surfaces (above).** The productization headline.
2. **D45 blob-value seam (correctness).** `classifier / self_prior / association /
   IA` ride as VALUES in `GOPrediction.features` JSONB, OUTSIDE
   `feature_schema_sha` (which governs contract families / column names, not blob
   values). Silent train/serve value skew; caused the 0.3462 incident; is the
   residual -0.0059 (PK-MFO/CCO) today. ADR D45 Open/unimplemented.
3. **Board fed by manual file injection.** `score_and_inject_windows.sh` runs
   cafaeval on a TSV and writes into `CAFA_forever/data/.../evaluation_*.tsv` +
   `method_names.tsv`. `.bak_prereranked/.bak_preinterpro/.bak_pregraft` are the
   trace of repeated manual re-injections. 4 accumulated PROTEA variants on the
   board (PROTEA-KNN, -reranked, -percut-graft, PROTEA). Not reproducible, not
   live-fed by the serve pipeline.
4. **Model-management ergonomics + deploy footgun.** No endpoint to set
   `is_active` or DELETE a reranker (had to `docker psql` raw writes on prod).
   `deploy.sh` default flips torch to the CUDA wheel over the network -> takes the
   stack DOWN when offline (the outage). Safe path `--no-deps --no-build` is not
   the default.
5. **Observability.** `arms_enabled` does not record the new InterPro graft arm
   (shows `interpro:false` even when the graft produced the number). Board method
   metadata under-describes provenance.

## What is sensible (keep)

- `POST /jobs {operation, payload, queue_name}` dispatch: uniform, auditable,
  reproducible (let the exact seal be replayed from the stored payload).
- feature-store / eval separation (`predict_go_terms` produces features;
  `run_cafa_evaluation` scores).
- The eval-arm post-processing pattern (`_run_cafa_softprop`, now the InterPro
  graft): opt-in, non-regressive by default, cleanly mirrored.
- Board-faithful cafaeval parity (`EVAL_LAFA_PARITY.md`): th_step / TOI / IA /
  known documented and honest.
- `feature_schema_sha` governance (as far as it reaches).

## Sequenced fix plan (safe-first, risk + reversibility per step)

### P1 - Unify the reranker/serve selection (correctness-critical)
- **P1a. Pin the reconciled reranker via `is_active`.** Set S2e trio (851849df)
  active, old trio inactive. Reversible (toggle back). RISK: `/annotate` picks
  retrieval by `param_count ASC` (dense), so feeding dense candidates to an
  S2e reranker trained on the d8979601/M2 composite pool = train/serve POOL
  mismatch (the same class of gap we just closed). So P1a MUST ship with P1b.
- **P1b. Fix `/annotate` retrieval + classifier to the reconciled config.** Serve
  d8979601 retrieval (learned-query-embed path from PR #696) + the composite
  classifier routing knob (PR #699). RISK: this is the exact cutover that caused
  the earlier `/annotate` novel-query hang; #696 addressed the embed path, but
  re-verify novel-query latency + correctness before/after. Gate on a re-seal.
- **P1c. Add management endpoints:** `set-is_active` + `DELETE` on
  `/reranker-models` (close the PR #694 gaps) so model selection stops needing
  raw DB writes.

### P2 - Single source of truth for the board
- **P2a. Feed the board from the serve `evaluation_result`,** not a hand-injected
  TSV. A small exporter: `evaluation_result` (pinned canonical run) ->
  `predictions_protea.tsv` + `method_names.tsv`, run as a tracked job, not by
  hand. Kills the `.bak_*` drift and makes the board number == the serve number.
- **P2b. Make `interpro_graft=true` the default of the standing benchmark eval**
  so 0.4004 is the standing number the board/UI show (today it was a flagged
  one-off).
- **P2c. Prune accumulated board method variants** to one canonical PROTEA entry
  (archive the rest).

### P3 - Close D45 (kill silent skew)
- Bring the blob families (classifier / self_prior / association / IA) under a
  value-level guard: either fold them into `feature_schema_sha` or use the
  existing `schema_sha_v2` as a value hash. Removes the residual -0.0059 and the
  0.3462-incident class.

### P4 - Deploy + observability polish
- Make `--no-deps --no-build` the default for offline restarts (or detect no
  network and skip the torch flip instead of aborting the stack).
- Record the InterPro graft arm in `arms_enabled`.

## Ordering rationale

P1 is correctness (the product serves the validated pipeline). P2 makes the
public surface honest and reproducible. P3 removes the last silent-skew class.
P4 is hygiene. P1a+P1b ship together (never P1a alone) and gate on a re-seal;
everything else is independently shippable and reversible.

## Definition of done

`/annotate`, the benchmark, and the board all reflect ONE pipeline and ONE
number (target 0.4004 native, board == serve), reproducible from a tracked job
with no manual file edits, and no train/serve value skew.
