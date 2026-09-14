# sparse-classifier overnight results (2026-06-28) — VALIDATED, integration drafted

Two-tower SPARSE FUNCTIONAL candidate generator (protein d8979601 k-WTA codes x GO sparse codes =
whitened BioBERT name+def text k-WTA + t0 co-annotation PPMI/SVD k-WTA; ASL + DAG-consistency;
7-seed). Replaces the dense 6-PLM + frozen anc2vec-2020 M2 classifier. anc2vec-2020 dropped (no
vectors for post-2020 terms; structural-only).

## P1 GO codes: functional, sharp
glycolysis~gluconeogenesis sparse-overlap 1.09 vs ~translation 0.17 vs ~plasma_membrane 0.04
(~25x related/unrelated; raw BioBERT was compressed 0.96 vs 0.89). k-WTA + PPMI co-annotation broke
the BERT anisotropy.

## P2/P2b/P3 ablation — temporal recall@100 of TRUE 227->230 NEW terms (the decisive test)
554K-curated (whole v227 minus qualifier=NOT + weak ND/NAS; keeps IEA; 6.3x the 88K-experimental)
BEATS 88K-experimental in 7/9 cells: NK 0.678/0.652, LK 0.716/0.705, PK 0.376/0.384. Gains on MFO
(+0.04..0.055) + all NK; only PK-bpo -0.019. More (curated) data helps TEMPORAL recall, not just
in-dist IEA mimicry. User's more-data instinct validated.

## P4 gate — recall CEILING uplift over the KNN-only pool: PASS, biggest on lose cells
PK-bpo 0.470->0.537 (+0.068), PK-mfo +0.057, LK-bpo +0.056, PK-cco +0.055, NK-bpo +0.041, rest
+0.009..0.027 (all 9 up). The sparse classifier adds candidate recall exactly where the board is
furthest from #1 (BPO/PK) -> justifies platform integration.

## P5 — integration drafted: DRAFT PR #690 (PROTEA, base develop)
Opt-in serve classifier (env PROTEA_CLASSIFIER_IMPL=two_tower_sparse; default M2 unchanged). New
two_tower_classifier.py + impl-aware loader + apply_classifier 2-line change + 11 tests; ruff/mypy/
pytest green incl M2 regression. Serve artifacts staged durable (vocab_go.npy in storage/
two_tower_sparse; 7 head ckpts + go_sparse_codes in the lab). NO redeploy / full export done.

## Remaining (USER GREENLIGHT — production-touching, held overnight)
merge #690 -> register artifacts in artifact store + set env -> redeploy -> 1-pair smoke export with
the flag -> full platform export (new classifier + association CSR + self_prior, d8979601,
train[160..227] test[230] k=30) -> reranker + 9 LAFA cells -> inject board if gains #1.
