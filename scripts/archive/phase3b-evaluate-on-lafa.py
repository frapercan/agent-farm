"""Phase 3b: Import 432 trained rerankers to PROTEA + evaluate each against LAFA eval_set.

For each (PLM, K) combo:
 - 1 LAFA prediction_set in DB (query_set=045ab275, ec=PLM, k=K)
 - 18 rerankers (6 cells x 3 seeds) trained in lab
 - For each reranker, GET /scoring/prediction-sets/{pred_id}/reranker-metrics
   to get CAFA Fmax on eval_set 3b6f8064

Writes: ~/Thesis2/agent-farm/results/phase3b_lafa_eval/summary.json
"""
from __future__ import annotations
import json, os, pathlib, sys, time
import psycopg, requests, jwt

REPO_DIR = pathlib.Path("/home/frapercan/Thesis2/repositories/protea-reranker-lab")
RUNS_DIR = REPO_DIR / "runs"
OUT_DIR = pathlib.Path("/home/frapercan/Thesis2/agent-farm/results/phase3b_lafa_eval")
OUT_DIR.mkdir(parents=True, exist_ok=True)

API = os.environ.get("PROTEA_API_URL", "http://localhost:8000")
DB_URL = os.environ.get("PROTEA_DB_URL", "postgresql://protea:protea@localhost:5432/protea")
JWT_SECRET = os.environ["PROTEA_JWT_SECRET"]

EVAL_SET_ID = "3b6f8064-239c-4af4-8390-fbb0f4c59914"
QUERY_SET_ID = "045ab275-97de-4793-81dd-bcbd37997544"

PLM_EC = {
    "ankh_base":   "08234f06-ba76-4d7d-aaec-ae601096b4fa",
    "ankh_large":  "238f79b1-3068-4c6f-9013-5cc52b4f662b",
    "esm2_150m":   "500a0c59-be09-424d-9d51-b7997629c95a",
    "esm2_3b":     "55e43f1c-1a3b-4b1d-88c0-26b433f5f673",
    "esm2_650m":   "c2e9dda3-e505-4170-b50d-435a451761ac",
    "esmc_600m":   "2bf1e753-022f-44b8-a131-9a90acb4024e",
    "prostt5":     "c0ae5b69-d6dc-41cf-a711-1739d3d2e170",
    "prot_t5":     "084943c6-fec1-441d-bdc5-63b0268ada1b",
}
KS = [3, 5, 10]
CELLS = ["nk-mfo", "nk-bpo", "nk-cco", "lk-mfo", "lk-bpo", "lk-cco"]
SEEDS = [42, 137, 244]
ASPECT_TO_NS = {"bpo": "biological_process", "mfo": "molecular_function", "cco": "cellular_component"}


def mint_jwt() -> str:
    return jwt.encode(
        {"sub": "conductor-phase3b-eval", "iat": int(time.time()),
         "exp": int(time.time()) + 7200, "role": "admin"},
        JWT_SECRET, algorithm="HS256",
    )


def find_lafa_pred_set(cur, ec: str, k: int) -> str | None:
    cur.execute("""
        SELECT id FROM prediction_set
        WHERE embedding_config_id=%s AND limit_per_entry=%s AND query_set_id=%s
        ORDER BY created_at DESC LIMIT 1
    """, (ec, k, QUERY_SET_ID))
    r = cur.fetchone()
    return str(r[0]) if r else None


def import_reranker(token: str, run_dir: pathlib.Path, pred_set_id: str) -> str | None:
    """Multipart upload of model.txt+spec.yaml+run.json to /v1/reranker-models/import."""
    model_p = run_dir / "model.txt"
    spec_p = run_dir / "spec.yaml"
    run_p = run_dir / "run.json"
    if not (model_p.exists() and spec_p.exists() and run_p.exists()):
        return None
    run = json.loads(run_p.read_text())
    run_id = run.get("run_id")
    headers = {"Authorization": f"Bearer {token}"}
    with open(model_p, "rb") as mf, open(spec_p, "rb") as sf, open(run_p, "rb") as rf:
        files = {
            "model_file": (model_p.name, mf, "text/plain"),
            "spec_yaml": (spec_p.name, sf, "text/yaml"),
            "run_json": (run_p.name, rf, "application/json"),
        }
        data = {
            "name": run_id,
            "prediction_set_id": pred_set_id,
            "evaluation_set_id": EVAL_SET_ID,
            "force": "true",
        }
        resp = requests.post(f"{API}/v1/reranker-models/import", headers=headers,
                             files=files, data=data, timeout=120)
    if resp.status_code not in (200, 201):
        print(f"    [import FAIL] {run_dir.name}: {resp.status_code} {resp.text[:200]}")
        return None
    return resp.json()["id"]


def get_reranker_metrics(token: str, pred_set_id: str, reranker_id: str, category: str) -> dict | None:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{API}/v1/scoring/prediction-sets/{pred_set_id}/reranker-metrics",
        params={"reranker_id": reranker_id, "evaluation_set_id": EVAL_SET_ID, "category": category},
        headers=headers, timeout=600,
    )
    if resp.status_code != 200:
        print(f"    [metrics FAIL] cat={category}: {resp.status_code} {resp.text[:200]}")
        return None
    return resp.json()


def main():
    token = mint_jwt()
    print(f"JWT len={len(token)}")
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    summary = {}
    summary_path = OUT_DIR / "summary.json"

    for k in KS:
        for plm, ec in PLM_EC.items():
            combo = f"K{k}_{plm}"
            print(f"\n=== {combo} ===")
            pred_set = find_lafa_pred_set(cur, ec, k)
            if not pred_set:
                print(f"  [skip] no LAFA pred_set for {combo}")
                continue
            combo_results = {"pred_set": pred_set, "cells": {}}
            for cell in CELLS:
                tier, aspect = cell.split("-")
                target_ns = ASPECT_TO_NS[aspect]
                cell_results = {}
                for seed in SEEDS:
                    run_dir = RUNS_DIR / f"phase3a_{combo}" / f"{cell}_seed{seed}"
                    if not run_dir.exists():
                        cell_results[seed] = None
                        continue
                    reranker_id = import_reranker(token, run_dir, pred_set)
                    if not reranker_id:
                        cell_results[seed] = None
                        continue
                    metrics = get_reranker_metrics(token, pred_set, reranker_id, tier)
                    if not metrics:
                        cell_results[seed] = {"reranker_id": reranker_id, "fmax": None}
                        continue
                    # Extract fmax for the cell's aspect from per-namespace breakdown
                    fmax = None
                    per_ns = metrics.get("per_namespace") or metrics.get("aspect_metrics") or {}
                    if isinstance(per_ns, dict):
                        for key, val in per_ns.items():
                            if target_ns in str(key).lower() or aspect in str(key).lower():
                                if isinstance(val, dict):
                                    fmax = val.get("fmax") or val.get("Fmax") or val.get("f")
                                break
                    # Fallback: top-level if metrics is single-ns
                    if fmax is None:
                        fmax = metrics.get("fmax") or metrics.get("Fmax")
                    cell_results[seed] = {"reranker_id": reranker_id, "fmax": fmax, "raw": metrics if fmax is None else None}
                    print(f"  {cell} seed={seed}: fmax={fmax}")
                combo_results["cells"][cell] = cell_results
            summary[combo] = combo_results
            summary_path.write_text(json.dumps(summary, indent=2))

    print(f"\n=== DONE — summary at {summary_path} ===")

if __name__ == "__main__":
    main()
