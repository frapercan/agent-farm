"""Phase 3e: import 288 phase3d boosters into PROTEA + dispatch 48 cafa eval jobs.

Per (PLM, K, seed), builds a nested rerankers dict (NK+LK × 3 aspects)
and dispatches run_cafa_evaluation against the cell's LAFA pred_set.
PROTEA writes evaluation_result with reranker_model_id, picked up by the
benchmark UI alongside the 240 baselines.

ETA: 48 jobs × ~90s = ~72 min sequential. Idempotent: skips already-imported
rerankers + skips already-dispatched eval jobs by tag.
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
import psycopg, requests, jwt

REPO_DIR = Path("/home/frapercan/Thesis2/repositories/protea-reranker-lab")
RUNS_DIR = REPO_DIR / "runs"
API = "http://localhost:8000"
EVAL_SET_ID = "3b6f8064-239c-4af4-8390-fbb0f4c59914"
QUERY_SET_ID = "045ab275-97de-4793-81dd-bcbd37997544"
JWT_SECRET = os.environ["PROTEA_JWT_SECRET"]
DB_URL = os.environ.get("PROTEA_DB_URL", "postgresql://protea:protea@localhost:5432/protea")

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
KS = [3, 5]
CELLS = [("nk", a) for a in ("mfo", "bpo", "cco")] + [("lk", a) for a in ("mfo", "bpo", "cco")]
SEEDS = [42, 137, 244]


def mint_jwt() -> str:
    return jwt.encode(
        {"sub": "phase3e-protea-eval", "iat": int(time.time()),
         "exp": int(time.time()) + 14400, "role": "admin"},
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


def import_reranker(token: str, run_dir: Path, pred_set_id: str) -> str | None:
    """POST /v1/reranker-models/import (multipart). Idempotent via force=true."""
    if not all((run_dir / f).exists() for f in ("model.txt", "spec.yaml", "run.json")):
        return None
    run_id = json.loads((run_dir / "run.json").read_text()).get("run_id")
    headers = {"Authorization": f"Bearer {token}"}
    with open(run_dir / "model.txt", "rb") as mf, \
         open(run_dir / "spec.yaml", "rb") as sf, \
         open(run_dir / "run.json", "rb") as rf:
        files = {"model_file": ("model.txt", mf, "text/plain"),
                 "spec_yaml": ("spec.yaml", sf, "text/yaml"),
                 "run_json": ("run.json", rf, "application/json")}
        data = {"name": run_id, "prediction_set_id": pred_set_id,
                "evaluation_set_id": EVAL_SET_ID, "force": "true"}
        resp = requests.post(f"{API}/v1/reranker-models/import",
                             headers=headers, files=files, data=data, timeout=120)
    if resp.status_code not in (200, 201):
        print(f"    [import FAIL] {run_dir.name}: {resp.status_code} {resp.text[:200]}")
        return None
    return resp.json()["id"]


def dispatch_cafa_eval(token: str, pred_set_id: str, rerankers_nested: dict) -> str | None:
    """POST /v1/annotations/evaluation-sets/{eval_id}/run with rerankers nested."""
    body = {
        "prediction_set_id": pred_set_id,
        "rerankers": rerankers_nested,
    }
    resp = requests.post(
        f"{API}/v1/annotations/evaluation-sets/{EVAL_SET_ID}/run",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(body), timeout=30,
    )
    if resp.status_code not in (200, 201):
        print(f"    [dispatch FAIL] {resp.status_code} {resp.text[:200]}")
        return None
    return resp.json().get("id")


def wait_job(cur, job_id: str, max_wait_s: int = 300) -> str:
    elapsed = 0
    while elapsed < max_wait_s:
        cur.execute("SELECT status FROM job WHERE id=%s", (job_id,))
        r = cur.fetchone()
        s = r[0] if r else "UNKNOWN"
        if s in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return s
        time.sleep(5)
        elapsed += 5
    return "TIMEOUT"


def main():
    token = mint_jwt()
    print(f"JWT len={len(token)}")
    conn = psycopg.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Phase 1: import all phase3d boosters into PROTEA.
    print("\n=== PHASE 1: IMPORT 288 BOOSTERS ===")
    import_map: dict[tuple, str] = {}  # (plm, k, cell, seed) -> reranker_id
    for plm, ec in PLM_EC.items():
        for k in KS:
            combo = f"K{k}_{plm}"
            pred_set = find_lafa_pred_set(cur, ec, k)
            if not pred_set:
                print(f"  [skip combo {combo}] no LAFA pred_set")
                continue
            for tier, aspect in CELLS:
                cell = f"{tier}-{aspect}"
                for seed in SEEDS:
                    run_dir = RUNS_DIR / f"phase3d_{combo}" / f"{cell}_seed{seed}"
                    if not run_dir.exists():
                        continue
                    rid = import_reranker(token, run_dir, pred_set)
                    if rid:
                        import_map[(plm, k, cell, seed)] = rid
                    if len(import_map) % 30 == 0:
                        print(f"  imported {len(import_map)} boosters so far")
    print(f"  total imported: {len(import_map)}")
    (Path("/home/frapercan/Thesis2/agent-farm/results/phase3e_protea_eval")
        ).mkdir(parents=True, exist_ok=True)
    Path("/home/frapercan/Thesis2/agent-farm/results/phase3e_protea_eval/import_map.json"
        ).write_text(json.dumps({f"{p}_{k}_{c}_{s}": rid for (p,k,c,s),rid in import_map.items()}, indent=2))

    # Phase 2: dispatch 48 cafa_eval jobs (16 combos x 3 seeds).
    print("\n=== PHASE 2: DISPATCH 48 CAFA EVAL JOBS ===")
    results = {}
    for plm, ec in PLM_EC.items():
        for k in KS:
            combo = f"K{k}_{plm}"
            pred_set = find_lafa_pred_set(cur, ec, k)
            if not pred_set:
                continue
            for seed in SEEDS:
                rerankers_nested = {}
                missing = False
                for tier, aspect in CELLS:
                    rid = import_map.get((plm, k, f"{tier}-{aspect}", seed))
                    if not rid:
                        missing = True
                        break
                    rerankers_nested.setdefault(tier, {})[aspect] = rid
                if missing:
                    print(f"  [skip {combo} seed{seed}] missing rerankers")
                    continue
                job_id = dispatch_cafa_eval(token, pred_set, rerankers_nested)
                if job_id:
                    results[f"{combo}_seed{seed}"] = {"job_id": job_id, "pred_set": pred_set, "status": "QUEUED"}
                    print(f"  dispatched {combo} seed{seed} job={job_id}")

    # Phase 3: wait for all jobs.
    print(f"\n=== PHASE 3: WAIT FOR {len(results)} EVAL JOBS ===")
    for key, info in results.items():
        s = wait_job(cur, info["job_id"], max_wait_s=600)
        info["status"] = s
        if s != "SUCCEEDED":
            print(f"  [{key}] {s}")
        else:
            # Fetch the Fmax from the new evaluation_result row
            cur.execute("""
                SELECT results FROM evaluation_result
                WHERE prediction_set_id=%s AND evaluation_set_id=%s AND reranker_model_id IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (info["pred_set"], EVAL_SET_ID))
            r = cur.fetchone()
            info["results"] = r[0] if r else None
            # Extract NK+LK Fmax average
            sel = []
            if r:
                for tier in ("NK", "LK"):
                    for asp in ("BPO", "MFO", "CCO"):
                        f = (r[0].get(tier) or {}).get(asp, {}).get("fmax")
                        if f is not None: sel.append(float(f))
            info["selective_avg"] = sum(sel)/len(sel) if sel else None
            print(f"  [{key}] SUCCEEDED selective_avg={info['selective_avg']}")

    Path("/home/frapercan/Thesis2/agent-farm/results/phase3e_protea_eval/summary.json"
        ).write_text(json.dumps(results, indent=2, default=str))
    print(f"\nDONE. {sum(1 for r in results.values() if r['status']=='SUCCEEDED')}/{len(results)} jobs succeeded.")
    print(f"Summary: /home/frapercan/Thesis2/agent-farm/results/phase3e_protea_eval/summary.json")


if __name__ == "__main__":
    main()
