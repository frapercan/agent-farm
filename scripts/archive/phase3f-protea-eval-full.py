"""Phase 3f: import K=3 PK + K=5 PK + K=10 (all) rerankers and dispatch full 9-cell cafa evals.

Completes the LAFA benchmark matrix in PROTEA UI: for each (PLM, K, seed=42),
build rerankers={"nk":{...}, "lk":{...}, "pk":{...}} with cell-specific
boosters for all 9 cells where available.
"""
from __future__ import annotations
import json, os, pathlib, time
import psycopg, requests, jwt

REPO_DIR = pathlib.Path("/home/frapercan/Thesis2/repositories/protea-reranker-lab")
RUNS_DIR = REPO_DIR / "runs"
OUT = pathlib.Path("/home/frapercan/Thesis2/agent-farm/results/phase3f_full_matrix")
OUT.mkdir(parents=True, exist_ok=True)

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
KS = [3, 5, 10]
CELLS_TIERS = [("nk", a) for a in ("mfo","bpo","cco")] + [("lk", a) for a in ("mfo","bpo","cco")] + [("pk", a) for a in ("mfo","bpo","cco")]
SEED = 42


def mint_jwt():
    return jwt.encode({"sub":"phase3f","iat":int(time.time()),"exp":int(time.time())+14400,"role":"admin"},
                       JWT_SECRET, algorithm="HS256")


def find_pred_set(cur, ec, k):
    cur.execute("SELECT id FROM prediction_set WHERE embedding_config_id=%s AND limit_per_entry=%s AND query_set_id=%s ORDER BY created_at DESC LIMIT 1", (ec, k, QUERY_SET_ID))
    r = cur.fetchone()
    return str(r[0]) if r else None


def reranker_run_dir(plm, k, cell, seed):
    """Pick the right runs/ prefix for (cell, k)."""
    tier = cell.split("-")[0]
    if k == 10:
        prefix = "phase3dpk" if tier == "pk" else "phase3d"
    else:
        prefix = "phase3dpk" if tier == "pk" else "phase3d"
    return RUNS_DIR / f"{prefix}_K{k}_{plm}" / f"{cell}_seed{seed}"


def import_one(token, run_dir, pred_set_id):
    if not all((run_dir / f).exists() for f in ("model.txt","spec.yaml","run.json")):
        return None
    run_id = json.loads((run_dir / "run.json").read_text()).get("run_id")
    headers = {"Authorization": f"Bearer {token}"}
    with open(run_dir/"model.txt","rb") as mf, open(run_dir/"spec.yaml","rb") as sf, open(run_dir/"run.json","rb") as rf:
        files = {"model_file":("model.txt", mf, "text/plain"),
                 "spec_yaml":("spec.yaml", sf, "text/yaml"),
                 "run_json":("run.json", rf, "application/json")}
        data = {"name": run_id, "prediction_set_id": pred_set_id, "evaluation_set_id": EVAL_SET_ID, "force": "true"}
        resp = requests.post(f"{API}/v1/reranker-models/import", headers=headers, files=files, data=data, timeout=120)
    if resp.status_code not in (200,201):
        return None
    return resp.json()["id"]


def dispatch_eval(token, pred_set_id, rerankers_nested):
    body = {"prediction_set_id": pred_set_id, "rerankers": rerankers_nested}
    resp = requests.post(f"{API}/v1/annotations/evaluation-sets/{EVAL_SET_ID}/run",
                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                         data=json.dumps(body), timeout=30)
    if resp.status_code not in (200,201):
        return None
    return resp.json().get("id")


def wait_job(cur, job_id, max_s=900):
    elapsed = 0
    while elapsed < max_s:
        cur.execute("SELECT status FROM job WHERE id=%s", (job_id,))
        r = cur.fetchone()
        s = r[0] if r else "UNK"
        if s in ("SUCCEEDED","FAILED","CANCELLED"):
            return s
        time.sleep(5); elapsed += 5
    return "TIMEOUT"


def main():
    token = mint_jwt()
    conn = psycopg.connect(DB_URL); conn.autocommit=True; cur=conn.cursor()
    summary = {}
    for plm, ec in PLM_EC.items():
        for k in KS:
            pred = find_pred_set(cur, ec, k)
            if not pred:
                continue
            combo = f"K{k}_{plm}"
            print(f"\n=== {combo} ===")
            rer_nested = {}
            for tier, asp in CELLS_TIERS:
                rd = reranker_run_dir(plm, k, f"{tier}-{asp}", SEED)
                rid = import_one(token, rd, pred)
                if rid:
                    rer_nested.setdefault(tier, {})[asp] = rid
            if not rer_nested:
                print("  no rerankers imported, skip")
                continue
            print(f"  imported {sum(len(v) for v in rer_nested.values())} cells, dispatching eval")
            jid = dispatch_eval(token, pred, rer_nested)
            if jid:
                st = wait_job(cur, jid)
                cur.execute("SELECT results FROM evaluation_result WHERE prediction_set_id=%s AND evaluation_set_id=%s AND reranker_model_id IS NOT NULL ORDER BY created_at DESC LIMIT 1", (pred, EVAL_SET_ID))
                r = cur.fetchone()
                summary[combo] = {"job": jid, "status": st, "results": r[0] if r else None}
                print(f"  {combo} {st}")
                (OUT/"summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nDONE. wrote {OUT}/summary.json")


if __name__ == "__main__":
    main()
