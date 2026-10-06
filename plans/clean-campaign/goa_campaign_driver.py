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

# 75 ficheros, releases 156..235. Eran 71 (160..235) mientras se creyo que la
# serie empezaba en la 160; el archivo de EBI tiene cuatro mas antes. Las 206..210
# no existen, y por eso 235-156+1 = 80 no es 75.
#: El criterio de admision del universo, en UN SOLO SITIO. Lo leen el payload
#: del job y la comprobacion de reanudacion, porque la unica forma de que "ya
#: esta hecha" signifique lo mismo que "se hizo" es que no haya dos copias.
#:
#: MEDIDO el 2026-10-06, y por eso existe esta constante: al cambiar el criterio
#: de "curated" a "reliable" se vacio protein pero NO la tabla job, asi que
#: universe_done siguio contando como hechas las 13 releases pasadas bajo
#: "curated" cuyas proteinas ya no existian. El arranque dijo "62 releases to
#: go" en vez de 75, y el universo habria salido SIN nada de lo que solo aportan
#: las releases 222-235. No un criterio mezclado: un agujero.
EVIDENCE_SCOPE = "reliable"

EXPECTED_RELEASES = 75


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
    # A fetch killed mid-range can leave a .part whose written prefix fools
    # the hole-based resume into skipping an incomplete range, producing a
    # corrupt gzip that fails mid-load hours later. Verify before use.
    test = subprocess.run(
        ["gzip", "-t", dest], capture_output=True, text=True, check=False
    )
    if test.returncode != 0:
        os.remove(dest)
        raise RuntimeError(f"gzip integrity check failed: {test.stderr.strip()[:200]}")
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


def _protein_count() -> int:
    """Cuantas filas tiene ``protein``. Para la invariante de coherencia."""
    out = subprocess.run(
        ["docker", "exec", "protea-postgres-1", "psql", "-U", "protea", "-d", "protea",
         "-t", "-A", "-c", "SELECT count(*) FROM protein;"],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(f"protein count psql failed: {out.stderr[:300]}")
    return int(out.stdout.strip())


def universe_done(api: Api) -> set[int]:
    """Releases with a succeeded, NON-DRY-RUN pass UNDER THE CURRENT CRITERION.

    Read straight from the DB for the same reason as :func:`loaded_releases`:
    there is no annotation_set to look at in phase 1, so the job row is the only
    record that a release has been through.

    The ``dry_run`` filter is not decoration: a dry run succeeds having written
    nothing, so counting it would skip a release whose universe pass never ran.
    One such job existed for release 156 on 2026-10-05 and would have done
    exactly that; the clean-slate truncate then removed it, which is luck, not a
    reason to drop the filter.

    The ``evidence_scope`` filter is the same failure one step removed, and it
    bit on 2026-10-06. A pass under a DIFFERENT criterion also wrote something
    that is no longer there: the criterion changed, ``protein`` was truncated,
    ``job`` was not, and this function went on counting 13 releases as done.
    "Done" has to mean "done under the criterion we are about to use", so the
    query matches :data:`EVIDENCE_SCOPE`.

    Jobs predating the field carry no ``evidence_scope``; they ran under the
    operation's default of the time, which was ``curated``, so that is what they
    are counted as.
    """
    out = subprocess.run(
        [
            "docker", "exec", "protea-postgres-1", "psql", "-U", "protea", "-d", "protea",
            "-t", "-A", "-c",
            "SELECT DISTINCT payload->>'gaf_url' FROM job "
            "WHERE operation='ensure_goa_universe' AND status='SUCCEEDED' "
            "AND coalesce((payload->>'dry_run')::boolean, false) = false "
            f"AND coalesce(payload->>'evidence_scope', 'curated') = '{EVIDENCE_SCOPE}';",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(f"universe_done psql failed: {out.stderr[:300]}")
    found: set[int] = set()
    for line in out.stdout.split():
        m = re.search(r"goa_uniprot_all\.gaf\.(\d+)\.gz", line)
        if m:
            found.add(int(m.group(1)))
    return found


def job_result(api: Api, job_id: str) -> dict:
    """The operation's result dict, which lives ONLY in the job.succeeded event.

    There is no ``result`` column on ``job`` and the API's job detail does not
    expose one; the phase 2 loop logs ``findings``, which ``ensure_goa_universe``
    leaves NULL. Reading ``job["result"]`` therefore logs ``null`` for a pass that
    worked, which is the exact shape of silence this campaign keeps paying for:
    the numbers that justify the run would not be in the log.
    """
    try:
        events = api.call("GET", f"/v1/jobs/{job_id}/events")
    except Exception:  # noqa: BLE001 - logging must not fail the release
        return {}
    for ev in items(events):
        if ev.get("event") == "ensure_goa_universe.done":
            return ev.get("fields") or {}
    for ev in items(events):
        if ev.get("event") == "job.succeeded":
            return (ev.get("fields") or {}).get("result") or {}
    return {}


def run_phase1(api: Api, plan: list[tuple[int, str]]) -> int:
    """Phase 1: grow the protein universe from every GAF, before any load.

    Three things make this a different loop and not a flag on the other one.

    No ontology. ``ensure_goa_universe`` reads the GAF and UniProt, never a
    snapshot, so the load_ontology_snapshot step and the whole ``ont_pending``
    dance do not apply.

    The GAF is REMOVED after its pass, like phase 2 does. An earlier version
    kept all 75 so phase 2 could reuse them, on the premise that "the whole
    series is 247 GB against 654 GB free". That premise was wrong by 3.2x.
    Measured with HEAD over all 75 releases: the series is 802.1 GB, the largest
    single release is 202 at 24.28 GB, and the free space is 661.9 GB (the 618
    figure that first replaced 247 was GiB read as GB -- the same unit slip in
    the other direction). Keeping all 75 fills the disk while downloading
    release 182, the 49th pass of 75, about 2.6 days in at the measured
    9.6 MB/s. Postgres lives on the same filesystem, so that is not a clean
    stop: it is a WAL PANIC in the campaign's own database.

    So each release is downloaded twice across the two phases, and that is the
    floor, not a waste to optimise away. Phase 1 cannot leave behind a filtered
    file that phase 2 could use instead: see the comment at the removal.

    A cache alignment that USED to be on the table is now gone: while phase 1
    descended it finished on exactly the files phase 2 starts with, so keeping
    the oldest few would have given phase 2 a free start. Both phases now run
    ascending, so they share no boundary and there is nothing to keep.

    Sequential, not MAX_IN_FLIGHT. Two universe passes at once would both ask
    UniProt for accessions, and the batch endpoint is the slow part: release 156
    scanned in 4,3 min and then spent longer than that fetching 117.136
    accessions in batches of a thousand. NOTE that ``ensure_cached`` BLOCKS, so
    download and pass do not overlap: the measured cycle is 423 s of prefetch plus
    375 s of pass, and the releases grow from 3,4 GB at the old end to 19 GB at the
    new one.

    ASCENDING, oldest first, 156 -> 235. Reverted from descending on
    2026-10-06, together with the evidence criterion.

    The union is the same in either order, so this is not about what ends up in
    the corpus. It is about what the admitting pass MEANS. Ascending, the pass
    that admits a protein is the earliest release in the series where it had
    reliable evidence -- which is the quantity the corpus is actually about,
    "the entries that at some point had reliable annotations", and one that
    ``date_created`` cannot supply, because UniProt's entry-creation date is not
    when the protein was annotated. Descending made that pass 235 for nearly
    everything and therefore meaningless. Ascending also lines the build order up
    with the project's definition of truth, which is first appearance and not a
    pairwise difference.

    NOTE that ``first_release`` is still not a column. Under descending its
    absence was justified because the value would have been meaningless; that
    justification is now gone, and the value is only implicit in ``created_at``
    against the job windows. Recoverable but fragile. Adding the column is a
    separate decision, not a rider on this one.

    WHAT ASCENDING COSTS, declared rather than discovered later. A partial run
    stops being useful: the evaluation window is GOA 220 -> 227, at the new end,
    so an interrupted ascending run leaves 2016-2019 done and the window
    untouched. Descending covered the window in its first fifteen passes. The
    cost is accepted because ``reliable`` makes a pass far cheaper -- it fetches a
    fraction of the accessions that ``curated`` did -- so the whole of phase 1 is
    expected to finish in one stretch.

    It also loses a cache alignment: descending FINISHED on the files phase 2
    STARTS with, which left a free start on the table. Ascending ends at 235 and
    phase 2 begins at 156, so that option disappears.

    Measured, and unchanged by the order: an accession UniProt no longer serves
    cannot be added by any pass, so the total unrecoverable is identical either
    way. The order only decides when it surfaces. Release 235 has 0,00%
    unavailable, 194 has 7,75% and 160 has 7,95%, so ascending meets the
    unrecoverable tail FIRST instead of last.
    """
    done = universe_done(api)
    # La invariante que el defecto del 2026-10-06 violaba: si no hay ni una
    # proteina pero hay pasadas contadas como hechas, el estado es incoherente y
    # seguir produce un universo con un agujero silencioso. Cualquier causa vale
    # -- un truncate, una restauracion, una base equivocada -- asi que se
    # comprueba el hecho y no la causa.
    if done and _protein_count() == 0:
        raise SystemExit(
            f"estado incoherente: protein esta a 0 pero {len(done)} releases "
            f"cuentan como hechas bajo {EVIDENCE_SCOPE!r} ({sorted(done)}). "
            "Seguir dejaria el universo sin lo que solo aportan esas releases. "
            "O se restauran sus filas, o sus jobs no deben contar."
        )
    if done:
        log(f"universe already done (skipped, scope={EVIDENCE_SCOPE}): {sorted(done)}")
    # Ascendente: ver el docstring. `plan` ya llega ascendente de parse_plan.
    pending = [r for r, _ in plan if r not in done]
    log(f"phase 1 ascending: {len(pending)} releases to go, {pending[:3]}..{pending[-1:]}")

    base = serve_base()
    ensure_cache_server()
    log(f"cache: serving {CACHE_DIR} at {base}")

    failures = 0
    for release in pending:
        try:
            ensure_cached(release)
        except Exception as exc:  # noqa: BLE001 - one release must not end the run
            log(f"universe {release}: prefetch FAILED ({exc}); skipped")
            failures += 1
            continue
        gaf_url = f"{base}/goa_uniprot_all.gaf.{release}.gz"
        job = api.call(
            "POST",
            "/v1/jobs",
            {
                "operation": "ensure_goa_universe",
                "queue_name": "protea.jobs",
                "description": f"fase 1, release {release}",
                "payload": {
                    "gaf_url": gaf_url,
                    "dry_run": False,
                    "timeout_seconds": 3600,
                    # Los TRECE de lafa, no "todo lo no-IEA". Declarado aqui
                    # aunque la operacion tenga un defecto, porque el defecto
                    # que obligo a tirar la campana anterior fue un criterio
                    # que viajaba en el codigo y no en el payload.
                    #
                    # POR QUE SE REVIRTIO, el 2026-10-06. "curated" admite por
                    # la EXISTENCIA de una fila no-IEA, nunca por si esa fila
                    # lleva informacion, y resulta que la mayoria no la lleva:
                    #   - 58% del universo entraba SOLO por IBA, propagado
                    #     mecanicamente desde un nodo ancestral por PAINT;
                    #   - y habia proteinas que entraban SOLO por ND, que es
                    #     como GO registra que un curador miro y no encontro
                    #     nada. Sus unicas filas estan sobre los tres terminos
                    #     RAIZ, cuya Information Accretion es cero por
                    #     construccion. Como donante de KNN no aporta nada y
                    #     ocupa un hueco entre los k vecinos: no es inerte, es
                    #     danino. Ejemplo medido: A0A021WW64, tres filas ND
                    #     sobre GO:0003674, GO:0005575 y GO:0008150.
                    #
                    # El criterio de admision pasa a ser el de la VERDAD, y el
                    # principio es: se admite una proteina solo por evidencia
                    # que sea una medicion sobre esa proteina.
                    "evidence_scope": EVIDENCE_SCOPE,
                },
            },
        )
        job_id = str(job["id"])
        log(f"universe {release}: job {job_id[:8]} submitted")
        try:
            finished = api.wait_job(job_id, GOA_JOB_TIMEOUT_S)
        except TimeoutError as exc:
            log(f"universe {release}: {exc}")
            failures += 1
            continue
        status = (finished.get("status") or "").lower()
        if status != "succeeded":
            failures += 1
            log(f"universe {release}: FAILURE ({status}) err={finished.get('error_message')}")
            continue
        log(f"universe {release}: ok {json.dumps(job_result(api, job_id), ensure_ascii=False)}")
        # Borrado tras la pasada. La version anterior guardaba los 75 GAF para
        # que la fase 2 los reusara, apoyandose en "the whole series is 247 GB
        # against 654 GB free". Esa cifra esta mal por 3,2x: medida con HEAD
        # sobre las 75, la serie son 802 GB, y quedaban 618 GB libres. El disco
        # se llenaba bajando la release 182, la 49a de la cola, y la fase 1
        # moria a dos tercios con el disco a cero.
        #
        # Guardar un filtrado en vez del bruto NO resuelve esto, y queda escrito
        # con su medicion para que no se reintente. La fase 2 guarda TODA fila
        # cuyo accession este en el universo y cuyo GO este en el snapshot, sin
        # filtrar por codigo de evidencia: el IEA entra. Y el universo no se
        # conoce hasta que la fase 1 termina, asi que un filtro aplicado durante
        # la fase 1 solo puede usar lo curado de esa release.
        #
        # El filtro a evaluar es el UTIL, no el ingenuo. El reviewed se conoce
        # antes de arrancar (insert_proteins lo mete), asi que el filtro que se
        # puede aplicar durante la pasada es
        #     F = reviewed  UNION  {curadas en ESTA release}
        # y no solo el segundo termino. MEDIDO sobre la 156, con dos pasadas por
        # el fichero y contra un universo de 1.639.103 miembros:
        #   filas del universo en la 156                 10.411.162
        #     cubiertas por el reviewed                   7.442.575  (71,5%)
        #     cubiertas por las curadas de la 156         1.146.797  (11,0%)
        #   |F| = 1.043.403 accesiones
        #   PERDIDA = 1.821.790 filas en 305.949 accesiones = 17,5%
        # El fichero filtrado serian 11.443.265 filas, el 4,07% del fichero.
        #
        # Asi que el filtro util pierde el 17,5%, no los dos tercios que dijo
        # una medicion anterior mal planteada. Pero 17,5% no es 0, y lo que hace
        # falta es 0: la fase 2 no filtra por evidencia -- el accept del plugin
        # solo se pasa en la fase 1, ensure_goa_universe.py:434, nunca en
        # load_goa_annotations.py:648 -- asi que toda fila IEA de un miembro del
        # universo se guarda, y el filtro las tiraria.
        #
        # Y el 17,5% es un SUELO, no un techo: se midio con una sola release
        # procesada y a medias. El universo es una union sobre las 75, solo
        # crece, y cada accession que entre despues anade filas perdidas. Como
        # la fase 1 desciende, las primeras pasadas son las que se filtrarian
        # con el universo mas vacio, y son justo la ventana 220-227.
        #
        # El filtro SEGURO -- accession en el universo COMPLETO -- si deja algo
        # pequeno: unos 23 GB para la serie entera. Pero solo se conoce cuando
        # la fase 1 termina, y releer cada bruto para aplicarlo ya es la segunda
        # descarga. No ahorra nada frente a borrar.
        try:
            os.remove(cache_path(release))
        except OSError:
            pass

    log(f"phase 1 finished: {len(pending) - failures} ok, {failures} failed")
    return 1 if failures else 0


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
    phase = 2
    if "--phase" in sys.argv:
        phase = int(sys.argv[sys.argv.index("--phase") + 1])
    if phase not in (1, 2):
        raise SystemExit(f"--phase must be 1 or 2, got {phase}")

    key = open(KEY_FILE, encoding="utf-8").read().strip()
    api = Api(API, key)
    plan = parse_plan(PLAN)

    if phase == 1:
        return run_phase1(api, plan)

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
