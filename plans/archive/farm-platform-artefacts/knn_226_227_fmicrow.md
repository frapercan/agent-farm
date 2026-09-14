# FARM-EXP.15 KNN-only baseline (226->227 validation, f_micro_w)

Grid: 8 PLM x K[3, 5, 10] x 9 cells = 216 cells (215 scored OK).

Metric: IA-weighted micro-F (f_micro_w), v227 LAFA-aligned IA. KNN-only score = 1 - cosine distance.

## Majority winner over NK+LK cells (PK excluded)

**Winner: prot_t5 K3** (4 of 6 NK+LK cells)

Win counts (plm K):
- prot_t5 K3: 4
- esm2_3b K3: 1
- esm2_150m K3: 1

Per-cell best (plm K, f_micro_w):
- lk-bpo: prot_t5 K3 (0.5996)
- lk-cco: prot_t5 K3 (0.6328)
- lk-mfo: esm2_150m K3 (0.5870)
- nk-bpo: prot_t5 K3 (0.4970)
- nk-cco: prot_t5 K3 (0.5890)
- nk-mfo: esm2_3b K3 (0.6060)
