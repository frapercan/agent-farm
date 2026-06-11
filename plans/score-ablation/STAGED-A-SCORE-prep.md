# A-SCORE.0/.1 prep + staging (2026-06-11)

Prepared while the SELECT grid finishes its last cell (ESM2-3B k=10).
A-SCORE.0/.1 target **Ankh-base** (08234f06), which is fully materialised,
so the read-only ablation can run now without waiting for the grid or
contending for the stack.

## Inputs (Ankh-base, ann=goa@220 1559d9f7, query=d95af71f SELECT 220->227)

| K | prediction_set_id | evals |
|---|---|---|
| 3 | 8a7cc6c9-3456-4e33-8f35-fc74fbc57004 | 7 |
| 5 | b7dcd6e7-a1ae-4ae8-a75f-31c44cc5bfd4 | 7 |
| 10 | d988c1df-5aad-4c34-b435-e5f181e045b4 | 7 |
| 30 | MISSING -> dispatch post-grid (see below) | - |

- eval_set (SELECT 220->227 GT, NK/LK/PK tiers): `a3be0a6d-7f21-4e7e-8ac8-eabccf77e8e0`
- IA file: `/home/frapercan/Thesis2/repositories/PROTEA/data/benchmarks/ia_select_220/IA_35c3ad67_goa220.tsv`
- 7 grid scoring_configs: embedding_only `01446858`, embedding_plus_vote `1ad536db`,
  vote_fraction `19b30773`, alignment_only `dc8aa37d`, embedding_plus_alignment `fb738ec4`,
  evidence_veto `04c55eb3`, composite `bae5ece3` (8th `IEA up` ab46ed7a not in grid).
- score.tsv endpoint: `GET /scoring/prediction-sets/{id}/score.tsv` (router `protea/api/routers/scoring.py`).

## Dep note: F-EVAL-PROTOCOL.valid

The SELECT VALID window is **220->227** (eval_set a3be0a6d, NK/LK/PK tiers), already
operational: the grid ran on it. A-SCORE.0/.1 proceed on that window. The
`F-EVAL-PROTOCOL.valid` slice in farm-platform/PLAN.md is marked `pending` but its
window framing is stale; the active selection window is 220->227 and is functional,
so it does not block this ablation.

## Auth recipe (mint admin JWT, same as the grid script)

```bash
cd ~/Thesis2/worktrees/protea-deploy
set -a; source .env; [ -f .env.local ] && source .env.local; set +a
TOKEN=$(poetry run python -c "import jwt,time,os; print(jwt.encode({'sub':'conductor-ascore','iat':int(time.time()),'exp':int(time.time())+72*3600,'role':'admin'}, os.environ['PROTEA_JWT_SECRET'], algorithm='HS256'))")
# then: curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/scoring/prediction-sets/<ps>/score.tsv
```

## STAGED: Ankh-base K=30 dispatch (fire ONLY after the grid closes; stack is busy now)

```bash
# predict (reuses Ankh-base ref pool; K not in worker cache key)
curl -sS -m 30 -X POST http://localhost:8000/v1/embeddings/predict \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query_set_id":"d95af71f-320c-43bb-a6f4-c56b3fef6f6b","search_backend":"numpy",
       "compute_taxonomy":true,"annotation_set_id":"1559d9f7-195d-4892-af16-8b58f7fc9942",
       "compute_alignments":true,"embedding_config_id":"08234f06-ba76-4d7d-aaec-ae601096b4fa",
       "aspect_separated_knn":true,"ontology_snapshot_id":"35c3ad67-3002-47db-8f71-eeed69d22ad6",
       "compute_reranker_features":true,"limit_per_entry":30}'
# then evaluate the resulting prediction_set against eval_set a3be0a6d with the 7 scoring_configs
# (mirror the grid script's eval loop), to complete the K-curve top point.
```

NOTE: K=30 ref-pool load for Ankh-base is well within RAM after PR #625; no oomd risk.

## Deferred (NOT in this prep)

- K=30 predict (above) until the grid closes.
- Champion promotion / 227->230 TEST: SEALED, never touched in this loop.
- A-SCORE.2 calibrated log-odds score: fires after .0/.1 land (uses the survivors + per-aspect K).
