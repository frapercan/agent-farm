"""Phase 3a shortlist sweep: 4 (PLM, K) candidates x 6 NK+LK cells x seed=42.

Uses v27_binary recipe (binary objective, lean+lin+emb, neg_pos_ratio=10).
Compares each candidate's NK+LK selective_avg cafaeval Fmax vs the current
champion 0.7291 (bench-v1-K5-v226-lineage-prostt5 v27_binary multiseed).

Writes:
  ~/Thesis2/repositories/protea-reranker-lab/runs/phase3a_shortlist/<dataset>/<cell>/run.json
  ~/Thesis2/repositories/protea-reranker-lab/runs/phase3a_shortlist/<dataset>/<cell>/cafaeval.json
  ~/Thesis2/repositories/protea-reranker-lab/runs/phase3a_shortlist/summary.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO_DIR = Path("/home/frapercan/Thesis2/repositories/protea-reranker-lab")
REPO_DATASETS = REPO_DIR / "datasets"
LAB_PYTHON = REPO_DIR / ".venv" / "bin" / "python"
PROTEA_PYTHON = Path("/home/frapercan/Thesis2/repositories/PROTEA/.venv/bin/python")
RUNS_ROOT = REPO_DIR / "runs" / "phase3a_shortlist"
OBO_PATH = REPO_DATASETS / "bench-v1-K5" / "go.obo"

CANDIDATES = [
    "bench-v1-K10-v226-lineage-prostt5",
    "bench-v1-K5-v226-lineage-esm2_3b",
    "bench-v1-K5-v226-lineage-esmc_600m",
    "bench-v1-K5-v226-lineage-prot_t5",
]
CELLS = ["nk-mfo", "nk-bpo", "nk-cco", "lk-mfo", "lk-bpo", "lk-cco"]
SEED = 42

V26_HPARAMS = {
    "objective": "binary",
    "num_boost_round": 10000,
    "early_stopping_rounds": 100,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 100,
    "drop_features": [],
}

ASPECT_TO_NS = {"bpo": "biological_process", "mfo": "molecular_function", "cco": "cellular_component"}


def make_spec(dataset: str, cell: str, out_dir: Path) -> Path:
    spec = {
        "schema_version": "v1",
        "name": f"phase3a_{dataset}_{cell}_seed{SEED}",
        "dataset": {"manifest": str(REPO_DATASETS / dataset / "manifest.json")},
        "model": {"kind": "lgbm_reranker", "defaults": dict(V26_HPARAMS)},
        "training": {
            "cell": cell,
            "val_strategy": "protein_group",
            "val_fraction": 0.2,
            "seed": SEED,
            "propagate_labels": False,
            "neg_pos_ratio": 10,
        },
        "sweep": {"backend": "none"},
        "output_dir": str(out_dir),
        "tags": [dataset, cell, f"seed{SEED}", "phase3a_shortlist", "binary_objective"],
        "keep_staging": False,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    spec_path = out_dir / "spec_input.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))
    return spec_path


def train(dataset: str, cell: str) -> dict:
    out_dir = RUNS_ROOT / dataset / cell
    run_json = out_dir / "run.json"
    if run_json.exists():
        try:
            r = json.loads(run_json.read_text())
            if r.get("status") == "ok":
                fmax = r.get("metrics", {}).get("test_fmax", 0)
                print(f"  [skip] {dataset}/{cell} test_fmax={fmax:.4f}", flush=True)
                return r
        except Exception:
            pass
    spec = make_spec(dataset, cell, out_dir)
    print(f"  [train] {dataset}/{cell} ...", flush=True)
    t0 = time.monotonic()
    proc = subprocess.run(
        [str(LAB_PYTHON), str(REPO_DIR / "scripts/run.py"), str(spec), "--datasets-root", str(REPO_DATASETS)],
        cwd=str(REPO_DIR), capture_output=True, text=True, timeout=5400,
    )
    dur = time.monotonic() - t0
    if proc.returncode != 0:
        print(f"  [FAIL] {dataset}/{cell} exit={proc.returncode} dur={dur:.0f}s")
        print(f"  stderr-tail: {proc.stderr[-600:]}")
        return {"status": "fail", "duration_s": dur}
    try:
        r = json.loads(run_json.read_text())
        fmax = r.get("metrics", {}).get("test_fmax", 0)
        print(f"  [done] {dataset}/{cell} test_fmax={fmax:.4f} dur={dur/60:.1f}min", flush=True)
        return r
    except Exception as e:
        print(f"  [FAIL] {dataset}/{cell} could not read run.json: {e}")
        return {"status": "fail", "duration_s": dur}


_DRIVER_SRC = """
import json, signal, sys
from cafaeval.evaluation import cafa_eval
signal.signal(signal.SIGTERM, signal.SIG_DFL)
signal.signal(signal.SIGINT, signal.SIG_DFL)
result = cafa_eval(sys.argv[1], sys.argv[2], sys.argv[3], norm='cafa', prop='fill', th_step=0.001, no_orphans=True, max_terms=500)
print(json.dumps(result))
"""


def run_cafaeval(dataset: str, cell: str) -> dict | None:
    out_dir = RUNS_ROOT / dataset / cell
    metrics_json = out_dir / "cafaeval.json"
    if metrics_json.exists():
        return json.loads(metrics_json.read_text())
    pred_tsv = out_dir / "predictions.tsv"
    if not pred_tsv.exists():
        print(f"  [skip cafaeval] {dataset}/{cell} no predictions.tsv")
        return None
    gt_tsv = out_dir / "groundtruth.tsv"
    if not gt_tsv.exists():
        print(f"  [skip cafaeval] {dataset}/{cell} no groundtruth.tsv")
        return None
    driver = out_dir / "_driver.py"
    driver.write_text(_DRIVER_SRC)
    proc = subprocess.run(
        [str(PROTEA_PYTHON), str(driver), str(OBO_PATH), str(gt_tsv), str(pred_tsv)],
        capture_output=True, text=True, timeout=600,
    )
    driver.unlink(missing_ok=True)
    if proc.returncode != 0:
        print(f"  [FAIL cafaeval] {dataset}/{cell}: {proc.stderr[-300:]}")
        return None
    raw = json.loads(proc.stdout)
    aspect = cell.split("-", 1)[1]
    target_ns = ASPECT_TO_NS[aspect]
    fmax = None
    for _, records in raw.items():
        for rec in records:
            if (rec.get("ns") or rec.get("namespace") or "") == target_ns:
                for k in ("f", "Fmax", "fmax"):
                    if k in rec and rec[k] is not None:
                        try:
                            fmax = float(rec[k]); break
                        except (TypeError, ValueError): pass
                break
        if fmax is not None: break
    payload = {"cell": cell, "dataset": dataset, "cafaeval_fmax": fmax}
    metrics_json.write_text(json.dumps(payload, indent=2))
    print(f"  [cafaeval] {dataset}/{cell} fmax={fmax}", flush=True)
    return payload


def main():
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for ds in CANDIDATES:
        if not (REPO_DATASETS / ds / "train.parquet").exists():
            print(f"[MISSING] {ds} not pulled, skip")
            continue
        print(f"\n=== {ds} ===")
        ds_results = {}
        for cell in CELLS:
            t = train(ds, cell)
            c = run_cafaeval(ds, cell)
            ds_results[cell] = {"train": t.get("metrics", {}), "cafaeval": c}
        # selective_avg over 6 NK+LK
        fmaxes = [(ds_results[c].get("cafaeval") or {}).get("cafaeval_fmax") for c in CELLS]
        valid = [f for f in fmaxes if f is not None]
        sel_avg = sum(valid)/len(valid) if valid else None
        ds_results["selective_avg_nk_lk"] = sel_avg
        summary[ds] = ds_results
        print(f"[summary] {ds} selective_avg NK+LK: {sel_avg}")
        (RUNS_ROOT / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== Phase 3a Shortlist DONE ===")
    print(f"Summary at {RUNS_ROOT}/summary.json")
    print(f"Champion to beat: 0.7291 (v27_binary on bench-v1-K5-v226-lineage-prostt5)")
    for ds, res in summary.items():
        print(f"  {ds}: selective_avg={res.get('selective_avg_nk_lk')}")


if __name__ == "__main__":
    main()
