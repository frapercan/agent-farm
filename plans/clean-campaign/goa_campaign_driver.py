#!/usr/bin/env python3
"""GOA campaign driver: sequential ascending loads, GOA 160..235.

Single source of truth for (release -> ontology snapshot date) is
agent-farm/plans/GOA-ONTOLOGY-PAIRING.md; this script parses that table at
startup and refuses to run if it does not find exactly 71 rows.

Properties:
  * ascending order (160 -> 235), one GAF at a time;
  * ontology snapshot per release (operation is idempotent on obo_version,
    so the 64 distinct snapshots shared by 71 releases are loaded once);
  * startup drain: waits for any in-flight load_goa_annotations /
    load_ontology_snapshot job to finish before enqueueing, so a driver
    restart never duplicates a running load;
  * skip releases whose annotation set already exists (re-run safe);
  * hard stop on first failure with the job id in the log;
  * every step appended to goa-campaign.log next to this file.

Auth: reads the raw operator key from /tmp/.protea_key (0600), minted for
this campaign (prefix qBj01gO7, name goa-campaign-2026-09-16-kimi). Revoke
in the frontend when the campaign ends.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("PROTEA_API_URL", "http://localhost:8000")
KEY_FILE = os.environ.get("PROTEA_KEY_FILE", "/tmp/.protea_key")
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(HERE, "..", "GOA-ONTOLOGY-PAIRING.md")
LOG = os.path.join(HERE, "goa-campaign.log")
CACHE_SCRIPT = os.path.join(HERE, "goa_cache.py")
CACHE_DIR = os.path.join(HERE, "gaf_cache")
SERVE_PORT = 8790

GAF_URL = "https://ftp.ebi.ac.uk/pub/databases/GO/goa/old/UNIPROT/goa_uniprot_all.gaf.{release}.gz"
OBO_URL = "https://release.geneontology.org/{date}/ontology/go-basic.obo"

ONTOLOGY_JOB_TIMEOUT_S = 30 * 60
GOA_JOB_TIMEOUT_S = 8 * 3600
POLL_S = 20

EXPECTED_RELEASES = 71


def serve_base() -> str:
    """Worker-facing base URL for cached GAFs (Tailscale IP if present)."""
    try:
        ip = (
            subprocess.run(
                ["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=10
            )
            .stdout.split()[0]
            .strip()
        )
        if ip:
            return f"http://{ip}:{SERVE_PORT}"
    except Exception:  # noqa: BLE001 - fallback below
        pass
    return f"http://127.0.0.1:{SERVE_PORT}"


def ensure_cache_server() -> None:
    import socket

    try:
        socket.create_connection(("127.0.0.1", SERVE_PORT), timeout=2).close()
        return
    except OSError:
        pass
    os.makedirs(CACHE_DIR, exist_ok=True)
    subprocess.Popen(
        [sys.executable, CACHE_SCRIPT, "serve", CACHE_DIR, str(SERVE_PORT), "0.0.0.0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(20):
        try:
            socket.create_connection(("127.0.0.1", SERVE_PORT), timeout=2).close()
            log(f"cache server up on :{SERVE_PORT}")
            return
        except OSError:
            time.sleep(1)
    raise RuntimeError("cache server did not start")


def cache_path(release: int) -> str:
    return os.path.join(CACHE_DIR, f"goa_uniprot_all.gaf.{release}.gz")


def ensure_cached(release: int) -> None:
    """Download the GAF into the local cache if not already there.

    Relies on ``goa_cache.fetch`` publishing the file atomically (rename onto
    the final path only once complete), so ``os.path.exists`` is a reliable
    "already cached" signal. A leftover ``.part`` is *kept*: ``fetch`` resumes
    from its sparse holes instead of re-downloading what is already on disk.
    """
    dest = cache_path(release)
    if os.path.exists(dest):
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    url = GAF_URL.format(release=release)
    t0 = time.time()
    log(f"goa {release}: prefetch {url} -> local cache")
    subprocess.run(
        [sys.executable, CACHE_SCRIPT, "fetch", url, dest, "24"],
        check=True,
    )
    mb = os.path.getsize(dest) / 1e6
    log(f"goa {release}: prefetched {mb:.0f} MB in {time.time() - t0:.0f}s")


def log(msg: str) -> None:
    line = f"{time.strftime('%F %T')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


class Api:
    def __init__(self, base: str, key: str) -> None:
        self.base = base.rstrip("/")
        self.key = key

    def call(self, method: str, path: str, body: dict | None = None) -> dict | list:
        req = urllib.request.Request(
            self.base + path,
            method=method,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers={"Content-Type": "application/json", "X-API-Key": self.key},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
        return json.loads(raw) if raw else {}

    def wait_job(self, job_id: str, timeout_s: int) -> dict:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            job = self.call("GET", f"/v1/jobs/{job_id}")
            status = (job.get("status") or "").lower()
            if status in {"succeeded", "failed", "canceled", "cancelled"}:
                return job
            time.sleep(POLL_S)
        raise TimeoutError(f"job {job_id} did not finish within {timeout_s}s")


def parse_plan(path: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    pattern = re.compile(r"^\s+(\d{3})\s+\d{4}-\d{2}-\d{2}\s+(\d{4}-\d{2}-\d{2})\s+\d+\s*d\b")
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = pattern.match(line)
            if m:
                rows.append((int(m.group(1)), m.group(2)))
    rows.sort()
    if len(rows) != EXPECTED_RELEASES:
        raise SystemExit(
            f"plan parse: expected {EXPECTED_RELEASES} releases, got {len(rows)} "
            f"from {path}; refusing to run"
        )
    return rows


def items(payload: dict | list) -> list:
    if isinstance(payload, list):
        return payload
    for k in ("items", "results", "data"):
        if isinstance(payload.get(k), list):
            return payload[k]
    return []


def snapshot_id_for(api: Api, obo_url: str) -> str:
    deadline = time.time() + 300
    while time.time() < deadline:
        for snap in items(api.call("GET", "/v1/annotations/snapshots")):
            if snap.get("obo_url") == obo_url and snap.get("id"):
                return str(snap["id"])
        time.sleep(10)
    raise RuntimeError(f"snapshot for {obo_url} not visible via API")


def loaded_releases(api: Api) -> set[int]:
    """Releases with a succeeded load_goa_annotations job.

    Read straight from the DB: the /v1/annotations/sets endpoint is cached
    5 minutes (stale reads caused duplicate loads) and annotation_set rows
    carry no job_id to verify against. A succeeded job implies a complete
    set; a failed/cancelled job implies partial data that must be re-run.
    """
    out = subprocess.run(
        [
            "docker", "exec", "protea-postgres-1", "psql", "-U", "protea", "-d", "protea",
            "-t", "-A", "-c",
            "SELECT DISTINCT payload->>'source_version' FROM job "
            "WHERE operation='load_goa_annotations' AND status='SUCCEEDED';",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(f"loaded_releases psql failed: {out.stderr[:300]}")
    return {int(line) for line in out.stdout.split() if line.strip().isdigit()}


def drain_in_flight(api: Api) -> None:
    while True:
        running = []
        jobs = api.call("GET", "/v1/jobs?limit=50")
        for j in items(jobs):
            if (j.get("status") or "").upper() in {"RUNNING", "QUEUED", "PENDING"} and j.get(
                "operation"
            ) in {"load_goa_annotations", "load_ontology_snapshot"}:
                running.append(j)
        if not running:
            return
        log(
            "drain: waiting for "
            + ", ".join(f"{j['operation']}:{j['id'][:8]}" for j in running)
        )
        for j in running:
            try:
                job = api.wait_job(str(j["id"]), GOA_JOB_TIMEOUT_S)
            except TimeoutError:
                log(f"drain: job {j['id']} still running after timeout; keep waiting")
                continue
            if (job.get("status") or "").lower() != "succeeded":
                log(
                    f"drain: in-flight {j['operation']}:{j['id']} ended "
                    f"{job.get('status')} err={job.get('error_message')}; aborting "
                    f"so a failed release is never silently skipped"
                )
                raise SystemExit(1)


MAX_IN_FLIGHT = 2  # one GAF load per worker node (laptop + sobremesa)


def sweep_cache(done: set[int]) -> None:
    """Drop the cached GAF of every release already loaded.

    The reaper at the bottom of the loop deletes a GAF when it sees its job
    finish, which covers the steady state and nothing else. A driver that is
    killed with loads in flight loses those ``in_flight`` entries, and their
    GAFs are then orphaned for good: on 2026-09-23 releases 213 and 216 were
    still holding 35 GB days after both had loaded, across several restarts.

    Startup is the only moment that sees the whole picture, because ``done``
    is read from the jobs that actually succeeded. Each file is ~18 GB and the
    campaign has 71 of them, so a leak of one per restart is not a rounding
    error on any disk.
    """
    freed = 0
    for release in sorted(done):
        path = cache_path(release)
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        try:
            os.remove(path)
        except OSError as exc:
            log(f"cache sweep: could not drop {path} ({exc})")
            continue
        freed += size
    if freed:
        log(f"cache sweep: {freed / 1e9:.1f} GB of GAFs for releases already loaded")


def main() -> int:
    key = open(KEY_FILE, encoding="utf-8").read().strip()
    api = Api(API, key)
    plan = parse_plan(PLAN)
    log(
        f"driver start: {len(plan)} releases, {plan[0][0]}..{plan[-1][0]}, "
        f"api={API}, max_in_flight={MAX_IN_FLIGHT}"
    )

    drain_in_flight(api)
    done = loaded_releases(api)
    if done:
        log(f"already loaded (skipped): {sorted(done)}")
    sweep_cache(done)

    base = serve_base()
    ensure_cache_server()
    log(f"cache: serving {CACHE_DIR} at {base}")

    pending = [(r, s) for r, s in plan if r not in done]
    ont_pending: dict[int, tuple[str, str]] = {}  # release -> (job_id, obo_url)
    in_flight: dict[int, tuple[str, str]] = {}  # release -> (job_id, gaf_url)
    failures = 0

    while pending or ont_pending or in_flight:
        # 1. advance ontology jobs whose snapshot just completed -> enqueue GAF
        for release, (job_id, obo_url) in list(ont_pending.items()):
            job = api.call("GET", f"/v1/jobs/{job_id}")
            status = (job.get("status") or "").lower()
            if status not in {"succeeded", "failed", "canceled", "cancelled"}:
                continue
            del ont_pending[release]
            if status != "succeeded":
                log(f"goa {release}: ontology job FAILED id={job_id} err={job.get('error_message')}")
                return 1
            snapshot_id = snapshot_id_for(api, obo_url)
            gaf_url = f"{base}/goa_uniprot_all.gaf.{release}.gz"
            job = api.call(
                "POST",
                "/v1/jobs",
                {
                    "operation": "load_goa_annotations",
                    "queue_name": "protea.jobs",
                    "payload": {
                        "ontology_snapshot_id": snapshot_id,
                        "gaf_url": gaf_url,
                        "source_version": str(release),
                    },
                },
            )
            in_flight[release] = (str(job["id"]), gaf_url)
            log(f"goa {release}: loading from local cache")

        # 2. top up the pipeline: prefetch GAF, then submit its ontology job
        while len(ont_pending) + len(in_flight) < MAX_IN_FLIGHT and pending:
            release, snap_date = pending.pop(0)
            try:
                ensure_cached(release)
            except Exception as exc:  # noqa: BLE001 - requeue at the front
                log(f"goa {release}: prefetch FAILED ({exc}); will retry")
                pending.insert(0, (release, snap_date))
                time.sleep(60)
                break
            obo_url = OBO_URL.format(date=snap_date)
            job = api.call(
                "POST",
                "/v1/jobs",
                {
                    "operation": "load_ontology_snapshot",
                    "queue_name": "protea.jobs",
                    "payload": {"obo_url": obo_url},
                },
            )
            ont_pending[release] = (str(job["id"]), obo_url)
            log(f"goa {release}: ontology snapshot {snap_date} (job {str(job['id'])[:8]})")
            # One prefetch per pass, so that step 1 gets to run in between.
            #
            # ensure_cached blocks this whole loop for as long as a GAF takes,
            # which is hours. Popping a second release here means starting that
            # block BEFORE step 1 has seen the ontology job of the first one
            # finish -- and the ontology job takes about three seconds, so it
            # almost always has. The GAF then sits fully downloaded and idle
            # for the length of the next download.
            #
            # Measured on 2026-09-23: release 218 finished downloading at
            # 17:27:44, its ontology job succeeded 2,6 s later, and the loop had
            # already moved on to prefetching 219, so its load could not be
            # enqueued for another five hours. And it does not recover by
            # itself: at the next boundary ont_pending holds two releases,
            # step 2 refuses to prefetch, and downloads and loads stop
            # overlapping altogether -- about 1,25 h of idle per release.
            #
            # Breaking here yields to step 1, which enqueues the load, and only
            # then does the next pass start the following download. That is the
            # behaviour the log shows for releases 216 and 217, which overlapped
            # correctly.
            break

        # 3. reap finished GAF loads
        for release, (job_id, _gaf_url) in list(in_flight.items()):
            job = api.call("GET", f"/v1/jobs/{job_id}")
            status = (job.get("status") or "").lower()
            if status not in {"succeeded", "failed", "canceled", "cancelled"}:
                continue
            log(
                f"goa {release}: job {status} id={job_id} "
                f"findings={json.dumps(job.get('findings'), ensure_ascii=False)} "
                f"error={job.get('error_message')}"
            )
            del in_flight[release]
            try:
                os.remove(cache_path(release))
            except OSError:
                pass
            if status != "succeeded":
                failures += 1
                log(f"goa {release}: FAILURE; release skipped, continuing with the rest")

        if pending or ont_pending or in_flight:
            time.sleep(POLL_S)

    log("driver finished: all releases processed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
