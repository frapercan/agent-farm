#!/usr/bin/env python
"""Phase 3c — apply Phase 3a boosters to PROTEA LAFA predictions, cafaeval.

For each of the 24 canonical (embedding_config, k) combos:
  1. Find the latest LAFA prediction_set (query_set 045ab275).
  2. Pull every go_prediction row + features JSONB into a pandas DataFrame
     in the 56-feature schema the Phase 3a boosters expect.
  3. For each of the 18 boosters trained for this combo (6 cells x 3 seeds):
       a. score the rows;
       b. filter to the cell's (tier, aspect);
       c. write CAFA pred.tsv + gt.tsv against eval_set 3b6f8064;
       d. invoke cafaeval (in-process, signal-safe handlers) and grab Fmax.
  4. Aggregate per-combo summary + a global ranking.csv.

Skip PK (no boosters trained for PK cells in Phase 3a).

Inputs:
  - boosters at ~/Thesis2/repositories/protea-reranker-lab/runs/phase3a_K{k}_{plm}/
  - train.parquet (for the deterministic categorical code map used at fit time)
  - DB go_prediction rows for the matching pred_set
  - groundtruth.parquet from MinIO bucket protea
  - go.obo from bench-v1-K5/

Outputs under /home/frapercan/Thesis2/agent-farm/results/phase3c_lafa_eval/:
  <combo>/<cell>_seed<n>/{pred.tsv, gt.tsv, cafaeval.json}
  <combo>/summary.json
  summary.json (root)
  ranking.csv

Intentionally self-contained; uses the PROTEA venv interpreter so that
lightgbm + psycopg + minio + cafaeval all live in one process.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import signal
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import psycopg
import pyarrow.compute as pc
import pyarrow.parquet as pq
from minio import Minio

# ----------------------------- Configuration -----------------------------

DB_URL = "postgresql://protea:protea@localhost:5432/protea"
MINIO_ENDPOINT = "localhost:9000"
MINIO_KEY = "minioadmin"
MINIO_SECRET = "minioadmin"
MINIO_BUCKET = "protea"
QUERY_SET_ID = "045ab275-97de-4793-81dd-bcbd37997544"
EVAL_SET_ID = "3b6f8064-239c-4af4-8390-fbb0f4c59914"
EVAL_GT_KEY = (
    "eval_groundtruth/3b6f8064-239c-4af4-8390-fbb0f4c59914/groundtruth.parquet"
)

LAB_ROOT = Path("/home/frapercan/Thesis2/repositories/protea-reranker-lab")
RUNS_ROOT = LAB_ROOT / "runs"
DATASETS_ROOT = LAB_ROOT / "datasets"
OBO_PATH = DATASETS_ROOT / "bench-v1-K5" / "go.obo"
RESULTS_ROOT = Path(
    "/home/frapercan/Thesis2/agent-farm/results/phase3c_lafa_eval"
)

# Canonical 8 PLM EmbeddingConfig IDs (from project_canonical_8plm_embedding_configs).
PLMS: list[tuple[str, str]] = [
    ("ankh_base", "08234f06-ba76-4d7d-aaec-ae601096b4fa"),
    ("ankh_large", "238f79b1-3068-4c6f-9013-5cc52b4f662b"),
    ("esm2_150m", "500a0c59-be09-424d-9d51-b7997629c95a"),
    ("esm2_3b", "55e43f1c-1a3b-4b1d-88c0-26b433f5f673"),
    ("esm2_650m", "c2e9dda3-e505-4170-b50d-435a451761ac"),
    ("esmc_600m", "2bf1e753-022f-44b8-a131-9a90acb4024e"),
    ("prostt5", "c0ae5b69-d6dc-41cf-a711-1739d3d2e170"),
    ("prot_t5", "084943c6-fec1-441d-bdc5-63b0268ada1b"),
]
KS = (3, 5, 10)
CELLS = ("nk-mfo", "nk-bpo", "nk-cco", "lk-mfo", "lk-bpo", "lk-cco")
SEEDS = (42, 137, 244)

CATEGORICAL_COLS = ("qualifier", "evidence_code", "taxonomic_relation", "aspect")
ASPECT_TO_NS = {
    "bpo": "biological_process",
    "mfo": "molecular_function",
    "cco": "cellular_component",
}

# Numeric columns we read from go_prediction typed columns. Anything not
# present here (anc2vec_*, emb_pca_*, tax_voters_*) must come from the
# features JSONB; lineage_* are not stored by PROTEA at predict time and
# stay NaN (LightGBM will route them through the missing branch).
TYPED_NUMERIC_COLS = (
    "distance",
    "identity_nw", "similarity_nw", "alignment_score_nw", "gaps_pct_nw",
    "alignment_length_nw",
    "identity_sw", "similarity_sw", "alignment_score_sw", "gaps_pct_sw",
    "alignment_length_sw",
    "length_query", "length_ref",
    "taxonomic_distance", "taxonomic_common_ancestors",
    "vote_count", "k_position", "go_term_frequency",
    "ref_annotation_density", "neighbor_distance_std",
    "neighbor_vote_fraction", "neighbor_min_distance", "neighbor_mean_distance",
    "tax_voters_same_frac", "tax_voters_close_frac",
    "tax_voters_mean_common_ancestors",
)
EMB_PCA_COLS = tuple(f"emb_pca_query_{i}" for i in range(16))

# Features that live ONLY in the JSONB blob (NULL or absent on LAFA pred_sets).
JSONB_ONLY_NUMERIC = (
    "anc2vec_neighbor_cos", "anc2vec_neighbor_maxcos",
    "anc2vec_has_emb",
    "anc2vec_query_known_cos", "anc2vec_query_known_maxcos",
    "anc2vec_query_known_count",
)

# Booster feature order — from any phase3a spec.yaml; identical for all 432
# runs (verified across 4 random combos).
BOOSTER_FEATURE_ORDER = (
    "distance",
    "identity_nw", "similarity_nw", "alignment_score_nw", "gaps_pct_nw",
    "alignment_length_nw",
    "identity_sw", "similarity_sw", "alignment_score_sw", "gaps_pct_sw",
    "alignment_length_sw",
    "length_query", "length_ref",
    "taxonomic_distance", "taxonomic_common_ancestors",
    "vote_count", "k_position", "go_term_frequency",
    "ref_annotation_density", "neighbor_distance_std",
    "neighbor_vote_fraction", "neighbor_min_distance", "neighbor_mean_distance",
    "anc2vec_neighbor_cos", "anc2vec_neighbor_maxcos",
    "anc2vec_has_emb",
    "anc2vec_query_known_cos", "anc2vec_query_known_maxcos",
    "anc2vec_query_known_count",
    "tax_voters_same_frac", "tax_voters_close_frac",
    "tax_voters_mean_common_ancestors",
    *EMB_PCA_COLS,
    "lineage_is_ancestor_of_known", "lineage_is_descendant_of_known",
    "lineage_ancestor_of_count", "lineage_descendant_of_count",
    "qualifier", "evidence_code", "taxonomic_relation", "aspect",
)

LINEAGE_COLS = (
    "lineage_is_ancestor_of_known", "lineage_is_descendant_of_known",
    "lineage_ancestor_of_count", "lineage_descendant_of_count",
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("phase3c")


# ----------------------------- Helpers -----------------------------

def dataset_name(plm: str, k: int) -> str:
    return f"bench-v1-K{k}-v226-lineage-{plm}"


def runs_dir(plm: str, k: int, cell: str, seed: int) -> Path:
    return RUNS_ROOT / f"phase3a_K{k}_{plm}" / f"{cell}_seed{seed}"


def load_obo_aspect_map(obo_path: Path) -> dict[str, str]:
    """Return {go_id: namespace} for every [Term] in the OBO."""
    out: dict[str, str] = {}
    current_id: str | None = None
    current_ns: str | None = None
    with obo_path.open() as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "[Term]":
                if current_id and current_ns:
                    out[current_id] = current_ns
                current_id = None
                current_ns = None
            elif line.startswith("id: "):
                current_id = line[4:].strip()
            elif line.startswith("namespace: "):
                current_ns = line[len("namespace: "):].strip()
        if current_id and current_ns:
            out[current_id] = current_ns
    return out


def load_cat_codes_for_cell(
    train_parquet: Path,
    cell: str,
    batch_size: int = 200_000,
) -> dict[str, list[str]]:
    """Re-derive the lab's sorted-unique categorical codes from train.parquet.

    Mirrors :func:`protea_reranker_lab.staging._scan_pass0`: filter by cell
    (category, aspect), then for each categorical column collect distinct
    values seen and sort them ascending. The integer code at inference is the
    position of the value in this sorted list (CAT_MISSING_CODE = -1 for
    unseen / null).
    """
    cat, asp = cell.split("-", 1)
    seen: dict[str, set[str]] = {c: set() for c in CATEGORICAL_COLS}
    pf = pq.ParquetFile(train_parquet)
    for batch in pf.iter_batches(
        columns=["category", "aspect", *CATEGORICAL_COLS],
        batch_size=batch_size,
    ):
        # filter by cell
        mask = pc.and_(
            pc.equal(batch.column("category"), pa_scalar(cat)),
            pc.equal(batch.column("aspect"), pa_scalar(asp)),
        )
        b = batch.filter(mask)
        if b.num_rows == 0:
            continue
        for c in CATEGORICAL_COLS:
            for v in pc.unique(b.column(c)).to_pylist():
                if v is not None:
                    seen[c].add(v)
    return {c: sorted(seen[c]) for c in CATEGORICAL_COLS}


def pa_scalar(s: str):  # lazy import for closure simplicity
    import pyarrow as pa
    return pa.scalar(s)


def fetch_lafa_pred_set(conn: psycopg.Connection, ec_id: str, k: int) -> str | None:
    """Return the latest prediction_set.id for (ec_id, k) on the LAFA query_set."""
    cur = conn.execute(
        """
        SELECT id FROM prediction_set
        WHERE embedding_config_id = %s
          AND limit_per_entry = %s
          AND query_set_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (ec_id, k, QUERY_SET_ID),
    )
    row = cur.fetchone()
    return None if row is None else str(row[0])


def fetch_predictions_df(
    conn: psycopg.Connection,
    pred_set_id: str,
) -> pd.DataFrame:
    """Return one row per go_prediction with the booster feature columns.

    The JSON-stored features (anc2vec_*, emb_pca_query_*, tax_voters_*) are
    pulled out of the features JSONB. Lineage columns are not stored at
    inference time and are filled with NaN -> LightGBM missing branch.
    """
    typed_cols = [
        "protein_accession",
        "(SELECT go_id FROM go_term WHERE id = gp.go_term_id) AS go_id",
        "qualifier", "evidence_code", "taxonomic_relation",
        *TYPED_NUMERIC_COLS,
        *EMB_PCA_COLS,
        "features",
    ]
    sql = f"""
        SELECT {', '.join(typed_cols)}
        FROM go_prediction gp
        WHERE prediction_set_id = %s
    """
    log.info("    fetching go_prediction rows from DB...")
    t0 = time.monotonic()
    with conn.cursor(name="lafa_pred_cursor") as cur:
        cur.itersize = 50_000
        cur.execute(sql, (pred_set_id,))
        rows = cur.fetchall()
        colnames = [d.name for d in cur.description]
    log.info(
        "    fetched %d rows in %.1fs", len(rows), time.monotonic() - t0
    )
    df = pd.DataFrame(rows, columns=colnames)
    return df


def expand_features_jsonb(df: pd.DataFrame) -> pd.DataFrame:
    """Hoist anc2vec_* and tax_voters_* (and any missing emb_pca_*) out of
    the features JSONB column. Missing values stay NaN."""
    target_cols: list[str] = []
    target_cols.extend(JSONB_ONLY_NUMERIC)
    # tax_voters_* and emb_pca_* live as typed columns but the JSONB blob
    # sometimes carries different values; we trust typed columns when present.
    # The lineage columns are absent everywhere -> stay NaN.
    for c in target_cols:
        if c in df.columns:
            continue  # already populated from typed column path
        # extract from JSONB; features may be None on legacy rows
        df[c] = df["features"].map(
            lambda blob, key=c: (blob.get(key) if blob else None)
        )
    return df


def encode_categoricals(
    df: pd.DataFrame, cat_codes: dict[str, list[str]]
) -> pd.DataFrame:
    """Encode the 4 categorical columns to int codes against the lab's vocab.

    Missing or unseen values become -1 (CAT_MISSING_CODE), matching
    staging.py:_encode_cat_batch + LightGBM's missing-category branch.
    """
    for col, codes in cat_codes.items():
        mapping = {v: i for i, v in enumerate(codes)}
        if col not in df.columns:
            df[col] = -1
            continue
        s = df[col]
        df[col] = s.map(lambda v, m=mapping: m.get(v, -1)).astype("int32")
    return df


def add_missing_feature_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure every booster feature column exists; lineage_* := NaN."""
    for c in LINEAGE_COLS:
        if c not in df.columns:
            df[c] = np.nan
    for c in BOOSTER_FEATURE_ORDER:
        if c not in df.columns:
            df[c] = np.nan
    return df


def score_with_booster(
    booster: lgb.Booster,
    df: pd.DataFrame,
) -> np.ndarray:
    """Score df against booster, aligning columns to booster.feature_name().

    All non-categorical columns are coerced to numeric. Categoricals are
    already int32 encoded. Missing columns are filled with NaN.
    """
    cols = list(booster.feature_name())
    X = pd.DataFrame(index=df.index)
    cat_set = set(CATEGORICAL_COLS)
    for c in cols:
        if c not in df.columns:
            X[c] = np.nan
        elif c in cat_set:
            X[c] = pd.to_numeric(df[c], errors="coerce").astype("Int32").astype("float64")
        else:
            X[c] = pd.to_numeric(df[c], errors="coerce")
    raw = np.asarray(booster.predict(X))
    if raw.size == 0:
        return raw
    if float(raw.min()) < 0.0 or float(raw.max()) > 1.0:
        raw = 1.0 / (1.0 + np.exp(-raw))
    return np.asarray(raw, dtype=np.float64)


def write_pred_tsv(
    path: Path, proteins: np.ndarray, go_ids: np.ndarray, scores: np.ndarray
) -> int:
    """CAFA prediction TSV: protein\tgo\tscore. Returns row count."""
    n = 0
    with path.open("w") as f:
        for p, g, s in zip(proteins, go_ids, scores):
            if g is None or (isinstance(g, float) and np.isnan(g)):
                continue
            f.write(f"{p}\t{g}\t{float(s):.6f}\n")
            n += 1
    return n


def write_gt_tsv(path: Path, gt_rows: list[tuple[str, str]]) -> int:
    """CAFA ground-truth TSV: protein\tgo. Returns row count."""
    seen: set[tuple[str, str]] = set()
    with path.open("w") as f:
        for p, g in gt_rows:
            if (p, g) in seen:
                continue
            seen.add((p, g))
            f.write(f"{p}\t{g}\n")
    return len(seen)


def run_cafa_eval(
    obo_path: Path,
    pred_tsv: Path,
    gt_tsv: Path,
    aspect: str,
) -> dict[str, Any]:
    """Run cafa_eval in-process with signal-safe handlers."""
    from cafaeval.evaluation import cafa_eval

    # cafaeval's pool wants default SIGTERM/SIGINT handlers in children.
    old_sigterm = signal.signal(signal.SIGTERM, signal.SIG_DFL)
    old_sigint = signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        # Pred dir must contain ONLY our single tsv.
        pred_dir = pred_tsv.parent / "pred_dir"
        pred_dir.mkdir(exist_ok=True)
        # clear stale tsvs
        for old in pred_dir.glob("*.tsv"):
            old.unlink()
        (pred_dir / pred_tsv.name).write_bytes(pred_tsv.read_bytes())
        df, dfs_best = cafa_eval(
            str(obo_path),
            str(pred_dir),
            str(gt_tsv),
            prop="fill",
            norm="cafa",
            no_orphans=True,
            max_terms=500,
            th_step=0.001,
            n_cpu=1,
        )
    finally:
        signal.signal(signal.SIGTERM, old_sigterm)
        signal.signal(signal.SIGINT, old_sigint)

    # dfs_best is {metric_kind: dataframe}. Pull protein-centric Fmax
    # (`f`) for the cell's namespace.
    target_ns = ASPECT_TO_NS[aspect]
    out: dict[str, Any] = {"fmax": None, "per_ns": {}, "tau": None}
    for metric_kind, df_best in dfs_best.items():
        rec = df_best.reset_index().to_dict(orient="records")
        out["per_ns"][metric_kind] = rec
        for r in rec:
            ns = r.get("ns") or r.get("namespace")
            f_val = r.get("f") or r.get("Fmax") or r.get("fmax")
            tau = r.get("tau")
            if f_val is None or ns != target_ns:
                continue
            try:
                f_float = float(f_val)
            except (TypeError, ValueError):
                continue
            # prefer the `f` (Fmax) metric_kind row
            if metric_kind in ("f", "Fmax", "fmax") and out["fmax"] is None:
                out["fmax"] = f_float
                if tau is not None:
                    try:
                        out["tau"] = float(tau)
                    except (TypeError, ValueError):
                        out["tau"] = None
    # Fallback: if no `f__*` kind, pick first match.
    if out["fmax"] is None:
        for metric_kind, rec in out["per_ns"].items():
            for r in rec:
                ns = r.get("ns") or r.get("namespace")
                f_val = r.get("f") or r.get("Fmax") or r.get("fmax")
                if ns == target_ns and f_val is not None:
                    try:
                        out["fmax"] = float(f_val)
                    except (TypeError, ValueError):
                        pass
                    break
            if out["fmax"] is not None:
                break
    return out


def fetch_baseline_lafa_mean(
    conn: psycopg.Connection, pred_set_id: str
) -> dict[str, float]:
    """For the matching pred_set, return mean Fmax per (tier, aspect)
    across the 7 baseline scoring_configs (reranker_model_id IS NULL)."""
    cur = conn.execute(
        """
        SELECT results FROM evaluation_result
        WHERE evaluation_set_id = %s
          AND prediction_set_id = %s
          AND reranker_model_id IS NULL
        """,
        (EVAL_SET_ID, pred_set_id),
    )
    rows = [r[0] for r in cur.fetchall()]
    if not rows:
        return {}
    bucket: dict[str, list[float]] = {}
    for blob in rows:
        for tier in ("NK", "LK", "PK"):
            tier_d = blob.get(tier) or {}
            for asp in ("BPO", "MFO", "CCO"):
                cell_d = tier_d.get(asp) or {}
                fmax = cell_d.get("fmax")
                if fmax is None:
                    continue
                key = f"{tier.lower()}-{asp.lower()}"
                bucket.setdefault(key, []).append(float(fmax))
    return {k: statistics.fmean(v) for k, v in bucket.items()}


def selective_avg_nk_lk(per_cell_seed: dict[str, dict[str, float | None]]) -> float | None:
    """Mean Fmax over 6 cells (3 NK + 3 LK), averaged over seeds first.

    per_cell_seed[cell] = {"seed42": ..., "seed137": ..., "seed244": ...}
    """
    nk_lk_cells = [c for c in CELLS if c.startswith(("nk-", "lk-"))]
    cell_means: list[float] = []
    for cell in nk_lk_cells:
        seeds = per_cell_seed.get(cell, {})
        vals = [v for v in seeds.values() if v is not None]
        if not vals:
            return None
        cell_means.append(statistics.fmean(vals))
    if not cell_means:
        return None
    return statistics.fmean(cell_means)


# ----------------------------- Main -----------------------------

def process_combo(
    *,
    plm: str,
    k: int,
    ec_id: str,
    conn: psycopg.Connection,
    minio_client: Minio,
    obo_aspect: dict[str, str],
    gt_by_tier_aspect: dict[tuple[str, str], list[tuple[str, str]]],
    gt_proteins_by_tier: dict[str, set[str]],
) -> dict[str, Any] | None:
    combo_name = f"K{k}_{plm}"
    combo_dir = RESULTS_ROOT / combo_name
    combo_dir.mkdir(parents=True, exist_ok=True)
    log.info("[combo %s] starting", combo_name)

    pred_set_id = fetch_lafa_pred_set(conn, ec_id, k)
    if pred_set_id is None:
        log.warning("[combo %s] no LAFA pred_set found, skipping", combo_name)
        return None
    log.info("[combo %s] pred_set_id = %s", combo_name, pred_set_id)

    # 1. Pull go_prediction rows for the combo (typed cols + JSONB).
    df = fetch_predictions_df(conn, pred_set_id)
    n_rows = len(df)
    if n_rows == 0:
        log.warning("[combo %s] empty pred_set", combo_name)
        return None
    df = expand_features_jsonb(df)
    df = add_missing_feature_cols(df)

    # 2. Compute cat_codes per cell (driven by the lab's train.parquet for
    # this combo). Cache once per combo because each booster of this combo
    # uses the SAME train.parquet schema and only the cell filter differs.
    train_parquet = DATASETS_ROOT / dataset_name(plm, k) / "train.parquet"
    if not train_parquet.exists():
        log.warning("[combo %s] missing %s, skipping", combo_name, train_parquet)
        return None

    cat_codes_per_cell: dict[str, dict[str, list[str]]] = {}
    log.info("[combo %s] scanning train.parquet for cat_codes (6 cells)...", combo_name)
    t0 = time.monotonic()
    for cell in CELLS:
        cat_codes_per_cell[cell] = load_cat_codes_for_cell(train_parquet, cell)
    log.info("[combo %s] cat_codes scanned in %.1fs", combo_name, time.monotonic() - t0)

    # 3. Per-cell loop. Pre-build go_id -> aspect filter per cell.
    proteins_arr = df["protein_accession"].to_numpy()
    go_ids_arr = df["go_id"].to_numpy()
    # Map go_id -> namespace
    df_aspects = np.array([obo_aspect.get(g, "") for g in go_ids_arr])

    baseline_lafa_mean = fetch_baseline_lafa_mean(conn, pred_set_id)

    combo_summary: dict[str, Any] = {
        "combo": combo_name,
        "plm": plm,
        "k": k,
        "embedding_config_id": ec_id,
        "prediction_set_id": pred_set_id,
        "n_pred_rows": int(n_rows),
        "baseline_lafa_mean": baseline_lafa_mean,
        "per_cell_seed_fmax": {},
        "per_cell_mean_fmax": {},
    }

    # Pre-cache the per-cell row mask + filtered arrays for the 3 seed-models
    # of that cell (they only differ in booster, not in eval geometry).
    for cell in CELLS:
        if cell.startswith("pk-"):
            continue  # no boosters trained for PK
        tier, aspect = cell.split("-")
        target_ns = ASPECT_TO_NS[aspect]
        tier_proteins = gt_proteins_by_tier.get(tier, set())
        if not tier_proteins:
            log.warning("[combo %s][%s] empty tier proteins, skipping", combo_name, cell)
            continue

        # Row mask: row's protein is in tier AND row's go is in aspect
        in_tier = np.fromiter(
            (p in tier_proteins for p in proteins_arr),
            count=len(proteins_arr), dtype=bool,
        )
        in_aspect = df_aspects == target_ns
        mask = in_tier & in_aspect
        n_cell_rows = int(mask.sum())
        if n_cell_rows == 0:
            log.warning(
                "[combo %s][%s] no pred rows after (tier x aspect) filter",
                combo_name, cell,
            )
            combo_summary["per_cell_seed_fmax"][cell] = {
                f"seed{s}": None for s in SEEDS
            }
            continue

        cell_df = df.loc[mask].reset_index(drop=True)
        cell_df = encode_categoricals(cell_df, cat_codes_per_cell[cell])
        cell_proteins = proteins_arr[mask]
        cell_gos = go_ids_arr[mask]

        # GT for this cell: (tier × aspect)
        gt_rows = gt_by_tier_aspect.get((tier, aspect), [])

        cell_summary: dict[str, float | None] = {}
        for seed in SEEDS:
            run_dir = runs_dir(plm, k, cell, seed)
            model_file = run_dir / "model.txt"
            if not model_file.exists():
                log.warning(
                    "[combo %s][%s seed%d] missing model.txt, skipping",
                    combo_name, cell, seed,
                )
                cell_summary[f"seed{seed}"] = None
                continue

            try:
                booster = lgb.Booster(model_file=str(model_file))
            except Exception as exc:
                log.error("[combo %s][%s seed%d] booster load failed: %s",
                          combo_name, cell, seed, exc)
                cell_summary[f"seed{seed}"] = None
                continue

            scores = score_with_booster(booster, cell_df)
            seed_dir = combo_dir / f"{cell}_seed{seed}"
            seed_dir.mkdir(exist_ok=True)
            pred_tsv = seed_dir / "pred.tsv"
            gt_tsv = seed_dir / "gt.tsv"
            n_pred = write_pred_tsv(pred_tsv, cell_proteins, cell_gos, scores)
            n_gt = write_gt_tsv(gt_tsv, gt_rows)
            try:
                cafa_out = run_cafa_eval(OBO_PATH, pred_tsv, gt_tsv, aspect)
            except Exception as exc:
                log.error("[combo %s][%s seed%d] cafaeval failed: %s",
                          combo_name, cell, seed, exc)
                (seed_dir / "cafaeval_error.txt").write_text(str(exc))
                cell_summary[f"seed{seed}"] = None
                continue
            (seed_dir / "cafaeval.json").write_text(
                json.dumps({
                    "n_pred_rows": n_pred,
                    "n_gt_rows": n_gt,
                    "fmax": cafa_out["fmax"],
                    "tau": cafa_out["tau"],
                }, indent=2, default=str)
            )
            cell_summary[f"seed{seed}"] = cafa_out["fmax"]
            log.info(
                "[combo %s][%s seed%d] Fmax=%s n_pred=%d n_gt=%d",
                combo_name, cell, seed,
                f"{cafa_out['fmax']:.4f}" if cafa_out["fmax"] is not None else "None",
                n_pred, n_gt,
            )

        combo_summary["per_cell_seed_fmax"][cell] = cell_summary
        cell_vals = [v for v in cell_summary.values() if v is not None]
        combo_summary["per_cell_mean_fmax"][cell] = (
            statistics.fmean(cell_vals) if cell_vals else None
        )

    combo_summary["selective_avg_nk_lk"] = selective_avg_nk_lk(
        combo_summary["per_cell_seed_fmax"]
    )
    (combo_dir / "summary.json").write_text(
        json.dumps(combo_summary, indent=2, default=str)
    )
    log.info(
        "[combo %s] done. selective_avg(NK+LK) = %s",
        combo_name,
        f"{combo_summary['selective_avg_nk_lk']:.4f}"
        if combo_summary["selective_avg_nk_lk"] is not None else "None",
    )
    return combo_summary


def heartbeat(task_id: str, msg: str) -> None:
    """Best-effort agent-farm heartbeat."""
    import subprocess
    try:
        subprocess.run(
            ["python3", "/home/frapercan/Thesis2/agent-farm/scripts/lib/db.py",
             "heartbeat", task_id, "info", msg],
            check=False, capture_output=True, timeout=10,
        )
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--combos", type=str, default="",
        help="Comma-separated K{k}_{plm} filter (default: all 24)",
    )
    parser.add_argument(
        "--task-id", type=str, default="",
        help="Agent-farm task id for heartbeats",
    )
    args = parser.parse_args()

    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    # Load OBO once (~36 MB, ~50k terms)
    log.info("loading OBO from %s", OBO_PATH)
    obo_aspect = load_obo_aspect_map(OBO_PATH)
    log.info("OBO loaded: %d terms", len(obo_aspect))

    # Load groundtruth parquet once from MinIO
    log.info("loading groundtruth from MinIO s3://%s/%s",
             MINIO_BUCKET, EVAL_GT_KEY)
    minio_client = Minio(
        MINIO_ENDPOINT, access_key=MINIO_KEY, secret_key=MINIO_SECRET, secure=False,
    )
    obj = minio_client.get_object(MINIO_BUCKET, EVAL_GT_KEY)
    gt_bytes = obj.read()
    obj.close()
    obj.release_conn()
    gt_pf = pq.ParquetFile(io.BytesIO(gt_bytes))
    gt_df = gt_pf.read().to_pandas()
    log.info("groundtruth loaded: %d rows, buckets=%s",
             len(gt_df), gt_df["bucket"].value_counts().to_dict())

    # Build per-(tier, aspect) groundtruth row lists. The 'known' bucket and
    # 'pk_known' bucket are NOT eval rows (they are the train cohort and the
    # PK exclusion set). We only emit gt for nk/lk (and pk, even though we
    # don't evaluate it here).
    gt_by_tier_aspect: dict[tuple[str, str], list[tuple[str, str]]] = {}
    gt_proteins_by_tier: dict[str, set[str]] = {}
    for tier in ("nk", "lk", "pk"):
        sub = gt_df[gt_df["bucket"] == tier]
        gt_proteins_by_tier[tier] = set(sub["protein_accession"].astype(str))
        for asp in ("bpo", "mfo", "cco"):
            target_ns = ASPECT_TO_NS[asp]
            mask = sub["go_id"].map(lambda g, ns=target_ns: obo_aspect.get(g) == ns)
            rows = list(
                zip(
                    sub.loc[mask, "protein_accession"].astype(str),
                    sub.loc[mask, "go_id"].astype(str),
                )
            )
            gt_by_tier_aspect[(tier, asp)] = rows
    log.info("groundtruth indexed; per-tier protein counts: %s",
             {t: len(s) for t, s in gt_proteins_by_tier.items()})

    # Build combo list
    requested = (
        {c.strip() for c in args.combos.split(",") if c.strip()}
        if args.combos else None
    )
    all_combos = [(f"K{k}_{plm}", plm, k, ec_id) for plm, ec_id in PLMS for k in KS]
    if requested:
        all_combos = [c for c in all_combos if c[0] in requested]
    log.info("processing %d combos", len(all_combos))

    grid: list[dict[str, Any]] = []
    last_hb = time.monotonic()
    with psycopg.connect(DB_URL) as conn:
        for i, (combo_name, plm, k, ec_id) in enumerate(all_combos, start=1):
            t_combo = time.monotonic()
            try:
                summary = process_combo(
                    plm=plm, k=k, ec_id=ec_id, conn=conn,
                    minio_client=minio_client,
                    obo_aspect=obo_aspect,
                    gt_by_tier_aspect=gt_by_tier_aspect,
                    gt_proteins_by_tier=gt_proteins_by_tier,
                )
            except Exception as exc:
                log.exception("[combo %s] FAILED: %s", combo_name, exc)
                summary = {
                    "combo": combo_name, "plm": plm, "k": k,
                    "embedding_config_id": ec_id,
                    "error": repr(exc),
                }
            if summary is not None:
                grid.append(summary)
            dt = time.monotonic() - t_combo
            log.info("[combo %s] elapsed %.1fs (combo %d/%d)",
                     combo_name, dt, i, len(all_combos))
            # Heartbeat every 5 min or after each combo
            if args.task_id and (time.monotonic() - last_hb > 300 or i % 3 == 0):
                heartbeat(
                    args.task_id,
                    f"phase3c-lafa-eval: {i}/{len(all_combos)} combos done; "
                    f"current={combo_name}",
                )
                last_hb = time.monotonic()

    # Persist root summary + ranking.csv
    (RESULTS_ROOT / "summary.json").write_text(
        json.dumps(grid, indent=2, default=str)
    )

    ranking_rows: list[dict[str, Any]] = []
    for s in grid:
        if "error" in s:
            ranking_rows.append({
                "combo": s["combo"], "selective_avg_nk_lk": None,
                "selective_avg_nk_lk_std": None,
                "baseline_lafa_mean_nk_lk": None,
                "delta_vs_baseline": None, "error": s["error"],
            })
            continue
        sel_avg = s.get("selective_avg_nk_lk")
        # Per-cell std across seeds, then mean of stds across cells
        stds = []
        for cell, seeds_d in (s.get("per_cell_seed_fmax") or {}).items():
            vals = [v for v in seeds_d.values() if v is not None]
            if len(vals) > 1:
                stds.append(statistics.pstdev(vals))
        sel_std = statistics.fmean(stds) if stds else None
        base = s.get("baseline_lafa_mean") or {}
        base_nk_lk_vals: list[float] = []
        for cell in CELLS:
            if cell.startswith(("nk-", "lk-")) and cell in base:
                base_nk_lk_vals.append(base[cell])
        base_mean = statistics.fmean(base_nk_lk_vals) if base_nk_lk_vals else None
        delta = (sel_avg - base_mean) if (sel_avg is not None and base_mean is not None) else None
        ranking_rows.append({
            "combo": s["combo"],
            "selective_avg_nk_lk": sel_avg,
            "selective_avg_nk_lk_std": sel_std,
            "baseline_lafa_mean_nk_lk": base_mean,
            "delta_vs_baseline": delta,
            "error": "",
        })
    ranking_rows.sort(
        key=lambda r: (r["selective_avg_nk_lk"] is None, -(r["selective_avg_nk_lk"] or 0.0))
    )
    rk_path = RESULTS_ROOT / "ranking.csv"
    with rk_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ranking_rows[0].keys()))
        w.writeheader()
        w.writerows(ranking_rows)
    log.info("ranking.csv written to %s", rk_path)
    log.info("DONE. %d combos processed.", len(grid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
