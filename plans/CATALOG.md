# Plan store catalog (2026-06-22)

Single entry point to the plan store. Every direction the project has taken is
listed here with its status (`terminado` / `a medias` / `archivado`) and where it
now lives. Harmonized so `beat-lafa-1` is the one canonical research campaign
without losing any prior direction. Nothing here is deleted; superseded plans
move to `plans/archive/` and stay readable.

Status legend: **ACTIVE** (live, being worked) · **DONE** (finished, work landed)
· **ARCHIVED** (superseded, folded into a successor, kept for the record).

## 1. Canonical research campaign

| Plan | Status | What it is | Where |
|---|---|---|---|
| **beat-lafa-1** | **ACTIVE — canonical** | The current campaign to surpass LAFA #1. `PLAN.md` (bibliography-grounded levers L1-L7) + `CAMPAIGN-DOSSIER.md` (the definitive record of everything tried, how, state, insights, artifact map). Best confirmed native = **0.3745** (EvalResult `b21b187c`). Bottleneck = PK precision. | `plans/beat-lafa-1/` |
| **meta-reranker** | ACTIVE — live reference | ADR-D43 architecture: stacked EvidenceScorer ports + shallow per-category combiner. `beat-lafa-1` plugs each lever in as one scorer. Architecture doc, not a slice plan. | `plans/meta-reranker/ARCHITECTURE.md` |

## 2. LAFA-campaign lineage (archived — folded into beat-lafa-1)

These are the chronological stages that led to `beat-lafa-1`. Their findings are
captured in the campaign dossier; the plans are kept for provenance.

| Plan | Date | What it drove | Status | Outcome |
|---|---|---|---|---|
| **lafa-improve** | 06-14 | First gap diagnosis at baseline 0.324 (#4): NK strong, LK/PK weak; ruled out KNN-transfer and reference-label causes. `RESULTS.md`. | ARCHIVED | Diagnosis folded into dossier §3/§6. |
| **lafa-number-one** | 06-14 | Push-to-#1 target shape (NK +0.029 / LK +0.091 / PK +0.065); established that score-level self-prior fusion does NOT generalise -> only a learned model exploiting prior-knowledge as features. `NEURAL-HEAD.md`. | ARCHIVED | Conclusion (learned features, not blends) is the spine of beat-lafa-1. |
| **reranker-vnext** | 06-14 | LightGBM-on-KNN reranker design + InterPro as a LEARNED feature. InterProScan6 compute DONE on both query sets. | ARCHIVED | Reranker shipped natively; InterPro feature refuted (IA-harmful, dropped in MR-2.5 #94). |
| **score-ablation** | 06-11 | Derive ONE calibrated score by feature+K ablation in SELECT 220->227, replacing the trivial 0/1 hand-weighted scores. `results/`, `STAGED-*.md`. | ARCHIVED | Superseded: the learned reranker replaced hand-weighted scores entirely. |
| **lafa-levers** | 06-17 | Native 0.315->0.391 lever catalog after INT-1..8 integration landed (PROTEA computes LAFA f_micro_w natively in /benchmark). | ARCHIVED | Direct predecessor of beat-lafa-1; levers re-prioritized there with the L2 lesson. |
| **thesis-cuts** | 06-11 | Two manuscript-cut slices. | DONE (2/2) → ARCHIVED | Completed. |

## 3. Active farm threads (operational plans — keep in place)

| Plan | Status | Scope | Progress |
|---|---|---|---|
| **executor** | ACTIVE | PROTEA platform/stack hardening, fases F1-F8 (jobs, API, OPS, observability). Separate thread from the research campaign. | 78/119 done, 2 blocked. Next: F-OPS-JOBS.1 (P0). |
| **thesis-writer** | ACTIVE | LaTeX manuscript slices (`~/Thesis2/thesis/`). | 28/40 done, 1 blocked. |
| **doc-writer** | idle (DONE backlog) | Sphinx docs + ADR + drift sweeps across the repo stack. | 16/16 done; drift detection is a standing job. |
| **farm-platform** | ACTIVE | Farm freeze + 49-slice transversal benchmark catalog. | 71/112 done. |
| **bioinfo-quick** | idle | Quick bioinformatics tasks (agent-scoped). | 10/12 done. |

## 4. Historical master plans (reference — keep at store root)

| File | Status | Note |
|---|---|---|
| `plans/PLAN.md` | reference | The v3.2 master plan the executor thread was migrated from. Historical source of the F1-F8 fases. |
| `plans/ROADMAP-THESIS-10.md` | reference | Canonical 10/10 finish plan (tracks A-G). Still the north-star roadmap. |
| `plans/REQUIREMENTS.md` | reference | Standing FR+NFR framework all work is organised around ("0.391 is a floor not a ceiling"). |

## 5. Worktrees (ephemeral build state)

| Worktree | Branch | Status | Disposition |
|---|---|---|---|
| **native-boosters-lab** | `feat/native-boosters-lab` | **A MEDIAS** — 1 commit, no PR. Lab-native per-category booster training module + MLflow; replaces the ad-hoc `storage/fullgo_models/train_native_boosters.py`. Real, valuable, unpreserved. | OPEN A PR (preserve), then remove worktree. |
| **exp-combiners** | merged | DONE — HEAD merged into develop (#94, MR-2.5: drop IA-harmful frequency/interpro columns + binary-calibrated default). | Safe to remove. |
| **pm-main-hotfix** | `hotfix/v6-array-safe-centroid` | DONE — merged via protea-method #45 (array-safe centroid placeholder check). | Safe to remove. |
| **protea-deploy** | persistent | The deploy worktree (holds develop deployed at protea.ngrok.app). 6 commits behind develop. | KEEP. Sync to develop during stack-state-update. |
| **_thesis-publish** | persistent | Thesis publish worktree. | KEEP. |

## 6. Open PRs to resolve (plan store)

| PR | Title | Action |
|---|---|---|
| agent-farm #178 | purge dead reranker + 226->227 LAFA-band slices | Stale; this harmonization supersedes it. Close or fold. |
| agent-farm #176 | mark FIX-STACK-SELF-HEAL done (#593 + #626) | Land (work is done) or fold into the harmonization PR. |

## 7. Where the campaign artifacts live (pointer)

The full artifact map (scripts, boosters, overlays, datasets, evals, RerankerModels)
is in `plans/beat-lafa-1/CAMPAIGN-DOSSIER.md` §8. This catalog indexes PLANS;
the dossier indexes ARTIFACTS.
