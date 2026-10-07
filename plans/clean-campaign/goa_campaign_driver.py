#!/usr/bin/env python3
"""GOA campaign driver: three phases over GOA 156..235, ascending.

Single source of truth for (release -> ontology snapshot date) is
agent-farm/plans/GOA-ONTOLOGY-PAIRING.md; this script parses that table at
startup and refuses to run if it does not find exactly 75 rows.

THE THREE PHASES, and the order is the argument.

``--phase 1`` grows the protein universe from every GAF, ascending, one file at
a time, through ``extract_goa_universe``. Accession-only rows: no sequence, no
metadata, no network beyond the file. 75 passes.

``--phase 2`` loads the annotations of every release, ascending, each against
its own ontology snapshot. It gates on ``select(Protein.accession)``, so phase 1
is what stops it from dropping rows in silence, and it needs no sequence.

``--phase 3`` fetches the sequences, the audit dates and the merged-accession
links from today's UniProt, in ONE job, through
``resolve_protein_sequences``. Once, over the union of the 75 releases.

Why the sequences come last, and not in phase 1: annotations are HISTORICAL and
belong to their release, a sequence is a PROPERTY OF THE PROTEIN and only
today's UniProt has it. Fetching per release asked the same question up to 75
times and asked repeatedly about accessions UniProt does not serve at all, which
measured 34% of the requests over the ten passes that worked that way.

Properties:
  * ascending order (156 -> 235), one GAF at a time, in both file phases;
  * ontology snapshot per release (operation is idempotent on obo_version,
    so the distinct snapshots shared by the 75 releases are loaded once);
  * startup drain: waits for any in-flight load_goa_annotations /
    load_ontology_snapshot job to finish before enqueueing, so a driver
    restart never duplicates a running load;
  * every phase is resume-safe, and each asks the DATABASE what is done rather
    than remembering: phase 1 by its job rows under the declared tiers, phase 2
    by the annotation sets that exist, phase 3 by the rows still missing a
    sequence;
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
import threading
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
#: La fase 3 es UN job sobre unas 700.000 accesiones en lotes de mil, con los
#: reintentos del plugin dentro. Medido a 0,2-0,9 s por lote en la ruta rapida,
#: son horas, no minutos, y el techo generoso evita que un driver impaciente
#: declare fallida una pasada que esta funcionando.
RESOLVE_JOB_TIMEOUT_S = 24 * 3600

#: Gigabytes libres por debajo de los cuales la fase 1 vuelve a BORRAR el GAF tras
#: su pasada en vez de guardarlo para la fase 2.
#:
#: Guardarlo evita bajar los 802 GB dos veces, lo que ahorra ANCHO DE BANDA y
#: casi nada de reloj: la segunda descarga se esconde detras de las cargas de la
#: fase 2, que son 123,5 min de media por release contra 37 de descarga en las
#: grandes. Dije que ahorraba 12,5 h y era falso.
#:
#: Esos 123,5 min estan MEDIDOS (2026-10-07, sobre los 73 jobs
#: ``load_goa_annotations`` SUCCEEDED de ``protea_old``: media 123,5 min, minimo
#: 53,4, maximo 583,8, suma 150,2 h). Antes aqui decia "35 min contra 7", que no
#: salia de ninguna medida y subestimaba la carga por 3,5. La conclusion no
#: cambia, se refuerza: el margen con que la descarga se esconde es mayor. Vale la pena igualmente, porque nos cubre un dia en que
#: EBI vaya lento y baja la carga que le metemos. Las dos fases recorren
#: la serie ASCENDENTE, asi que los ficheros que la fase 1 ve primero son
#: exactamente los que la fase 2 necesita primero: un prefijo guardado se consume
#: sin una sola descarga.
#:
#: El suelo son 230 GB y NO es un numero redondo elegido a ojo. La base de la
#: campana anterior, con un corpus de tamano comparable y las anotaciones de sus
#: 71 releases, ocupa 120 GB medidos (``pg_database_size('protea_old')``). Se
#: reservan 200 GB para que la fase 2 quepa con holgura, mas 30 GB de margen para
#: el fichero que se este bajando, que llega a 24 GB en la release 202. Postgres
#: vive en el mismo sistema de ficheros, asi que llenarlo no es una parada limpia:
#: es un PANIC de WAL en la base de la propia campana.
DISK_FLOOR_GB_TO_KEEP = 230
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
#:
#: Son NIVELES y no una palabra desde PROTEA#989 (ADR-D49). "reliable" era un
#: complemento -- todo lo que no es IEA -- y un complemento admite lo que GO
#: invente despues sin que nadie lo decida: admitio IBA, propagado mecanicamente
#: por PAINT desde un nodo ancestral (58% del universo entraba solo por ahi), y
#: ND, que es como GO registra que un curador miro y no encontro nada, sobre los
#: tres terminos RAIZ cuya Information Accretion es cero por construccion.
#:
#: Los tres niveles enumeran 22 de los 26 codigos que conoce el mapeo ECO; los
#: otros cuatro (IEA, IBA, IBD, ND) quedan fuera, cada uno por su razon, y un
#: codigo desconocido se cuenta y se rechaza en vez de entrar en silencio.
ADMIT_TIERS = ["truth", "curated_inference", "swissprot_of_release"]

#: La ULTIMA release cuyo GAF trae el nombre de entrada de UniProtKB en la columna
#: DB Object Synonym. A partir de la siguiente, GOA pone el simbolo del gen y el
#: nombre no esta en ninguna otra columna de la fila: desaparecio del registro.
#:
#: MEDIDO el 2026-10-06 sobre las releases en cache, fraccion de filas con nombre
#: de entrada legible:
#:
#:     164..178   100%
#:     179          0%
#:     180          0%
#:     231          5%
#:
#: Por que es una constante aqui y no una deteccion en la operacion: el nivel es
#: una propiedad del FORMATO de la release, no de una fila, y una heuristica por
#: fila sobre una columna que no contiene el dato siempre filtra. Se intento: una
#: comprobacion de forma dejo pasar 1,6 millones de locus tags del tipo
#: `FD15_GL001936` en la pasada de la 179, que hubo que borrar. El criterio se
#: declara en el payload, queda en la fila del job, y la operacion REFUSA si
#: alguien pide el nivel donde no se puede derivar (PROTEA#995).
LAST_RELEASE_WITH_ENTRY_NAME = 178


def admit_for(release: int) -> list[str]:
    """Los niveles que esta release puede sostener.

    De la 179 en adelante sale `swissprot_of_release`, y el hueco lo cubre la
    siembra de la Swiss-Prot ACTUAL con `insert_proteins` sobre los ficheros
    planos de release: 617.103 registros en 131 s, de los que 80.061 eran nuevos.
    Decision A+B en MARCO-DECLARADO.

    Lo que se pierde al cubrirlo asi, dicho donde se decide: la pertenencia a
    Swiss-Prot deja de estar FECHADA en esa mitad de la serie. Una proteina
    sembrada por esa via queda con `first_admitted_release` a NULL, que es
    exactamente lo que significa "admitida por la fuente del presente y por
    ninguna release".
    """
    if release <= LAST_RELEASE_WITH_ENTRY_NAME:
        return list(ADMIT_TIERS)
    return [t for t in ADMIT_TIERS if t != "swissprot_of_release"]

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


def free_gb() -> int:
    """Gigabytes libres en el sistema de ficheros del cache."""
    st = os.statvfs(CACHE_DIR if os.path.isdir(CACHE_DIR) else HERE)
    return int(st.f_bavail * st.f_frsize / 1e9)


def _drop_or_keep(release: int) -> None:
    """Tras la pasada de universo: guardar el GAF si cabe, borrarlo si no.

    POR QUE GUARDARLO. La fase 2 vuelve a leer el mismo fichero, y bajarlo dos
    veces cuesta 23 h de las 47 que dura todo, medido a los 9,6 MB/s reales. Las
    dos fases recorren la serie ascendente, asi que el prefijo que la fase 1
    procesa primero es el que la fase 2 pide primero: ``ensure_cached`` ve el
    fichero y vuelve sin bajar nada.

    POR QUE NO SIEMPRE. La serie son 802 GB y no caben. El suelo decide: por
    encima se guarda, por debajo se borra, y asi el prefijo que quepa se aprovecha
    sin que el disco llegue nunca a cero. Degrada solo, sin una decision previa
    sobre cuantas releases guardar.

    POR QUE NO SE CARGAN LAS ANOTACIONES EN LA MISMA PASADA queda escrito aqui
    porque es la pregunta que todo el mundo hace, y la respuesta que di el
    2026-10-06 era FALSA en su parte central. Queda corregida.

    El mecanismo es cierto: ``load_goa_annotations`` solo guarda una fila si su
    accesion ya esta en ``protein``, asi que intercalando, una proteina admitida
    en la release N no tendria cargadas sus filas de 156..N-1.

    LO QUE DIJE MAL. Afirme que eso "perderia el sujeto del experimento". No es
    verdad, y lo contrario es DEMOSTRABLE: bajo orden ascendente, si una proteina
    se admite en N es porque en 156..N-1 no tenia ninguna evidencia admisible --
    ni codigo de verdad, ni curated_inference, ni era Swiss-Prot. Si hubiera
    tenido un IDA en la 160 se habria admitido en la 160. Luego las filas que
    intercalar perderia son EXCLUSIVAMENTE IEA, IBA, IBD y ND. Y la evaluacion
    filtra por experimentales (``protea/core/evaluation.py``, ``_EXP_CODES``) y la
    IA usa regimen ``lafa``, asi que ninguna de las dos las lee.

    POR QUE SE MANTIENEN LAS DOS FASES DE TODAS FORMAS, que es el argumento
    correcto y no el que di: mi demostracion dice que la EVALUACION esta a salvo,
    no que el CORPUS este completo, y el corpus es el activo. Intercalando,
    ``annotation_set(156)`` deja de ser "GOA 156 restringido al corpus" y pasa a
    ser "GOA 156 restringido al corpus conocido en 156". Es un objeto distinto,
    incompleto por el lado antiguo, y NO reparable sin volver a bajar los 802 GB,
    porque la informacion que haria falta para filtrar la 156 correctamente no
    existe hasta haber leido la 235.

    Y el ahorro que justificaria el riesgo no esta ahi. La segunda descarga se
    esconde detras de las cargas de la fase 2, que son 123,5 min de media por
    release contra 37 de descarga en las grandes (medido el 2026-10-07 sobre los
    73 jobs de ``protea_old``), y la fase 2 ya hace prefetch dentro de su bucle. Lo que si
    costaba horas era que la fase 1 bajara y escaneara EN SERIE, y eso lo arregla
    :class:`_Prefetcher` sin tocar la completitud de nada.
    """
    libres = free_gb()
    if libres > DISK_FLOOR_GB_TO_KEEP:
        log(f"universe {release}: GAF kept for phase 2 ({libres} GB free)")
        return
    try:
        os.remove(cache_path(release))
        log(f"universe {release}: GAF removed, {libres} GB free is under the floor")
    except OSError:
        pass


class _Prefetcher:
    """Downloads the NEXT release while the current one is being scanned.

    ``ensure_cached`` BLOCKS, so phase 1 used to spend 423 s downloading and then
    390 s scanning, in series: 813 s a release when the two could overlap almost
    entirely. Over the 67 remaining releases that serialisation costs about 7,2 h,
    which is the single biggest avoidable cost in the run, bigger than the second
    download the two-phase design needs (that one hides behind phase 2's loads,
    measured at 123.5 min a release on average against 37 of download for the
    big files).

    One prefetch at a time, deliberately. Two concurrent downloads would halve
    each other's share of the same link and double the peak disk, and the peak is
    what the floor in :func:`_drop_or_keep` has to leave room for: the worst
    adjacent pair in the series is 24 GB plus 24 GB.

    A failure here is NOT raised. The main loop calls ``ensure_cached`` for the
    release it is about to process, which finds no file and downloads it
    synchronously, exactly as it did before this existed. The prefetch is an
    optimisation, so it must never be the thing that ends a run.
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self.release: int | None = None

    def start(self, release: int | None) -> None:
        if release is None:
            return
        self.release = release
        self._thread = threading.Thread(
            target=self._quiet, args=(release,), daemon=True, name=f"prefetch-{release}"
        )
        self._thread.start()

    def wait(self) -> None:
        """Block until the in-flight prefetch ends. Its failure is the caller's to rediscover."""
        if self._thread is not None:
            self._thread.join()
        self._thread = None
        self.release = None

    @staticmethod
    def _quiet(release: int) -> None:
        try:
            ensure_cached(release)
        except Exception as exc:  # noqa: BLE001 - an optimisation never ends the run
            log(f"prefetch {release}: failed in background ({exc}); the main loop will retry")


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

    The CRITERION filter is the same failure one step removed, and it bit on
    2026-10-06. A pass under a DIFFERENT criterion also wrote something that is
    no longer there: the criterion changed, ``protein`` was truncated, ``job``
    was not, and this function went on counting 13 releases as done. "Done" has
    to mean "done under the criterion we are about to use".

    The comparison is made HERE and not in SQL, as a SET of tier names. Two
    payloads naming the same three tiers in different order are the same
    criterion, and ``payload->'admit' = '[...]'::jsonb`` would say they are not:
    JSONB array equality is ordered. A resume check that answers "not done" for
    work that was done costs a 24 GB re-read; one that answers "done" for work
    that was not costs a hole in the corpus.

    Jobs from before the split ran ``ensure_goa_universe`` under a scope word
    rather than tiers, and are counted as done by NOTHING: that operation no
    longer exists, and no tier list is equivalent to ``reliable``, which admitted
    IBA and ND.
    """
    out = subprocess.run(
        [
            "docker", "exec", "protea-postgres-1", "psql", "-U", "protea", "-d", "protea",
            "-t", "-A", "-F", "\t", "-c",
            "SELECT payload->>'gaf_url', coalesce(payload->>'admit', '[]') FROM job "
            "WHERE operation='extract_goa_universe' AND status='SUCCEEDED' "
            "AND coalesce((payload->>'dry_run')::boolean, false) = false;",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(f"universe_done psql failed: {out.stderr[:300]}")
    found: set[int] = set()
    for line in out.stdout.splitlines():
        if "\t" not in line:
            continue
        gaf_url, admit_json = line.split("\t", 1)
        try:
            admit = set(json.loads(admit_json))
        except (ValueError, TypeError):
            continue
        m = re.search(r"goa_uniprot_all\.gaf\.(\d+)\.gz", gaf_url)
        if not m:
            continue
        release = int(m.group(1))
        # El criterio esperado depende de la RELEASE: de la 179 en adelante son dos
        # niveles y no tres, asi que comparar contra un conjunto fijo marcaria como
        # no-hechas todas las pasadas correctas del extremo nuevo.
        if admit != set(admit_for(release)):
            continue
        found.add(release)
    return found


def job_result(api: Api, job_id: str, event: str = "extract_goa_universe.done") -> dict:
    """The operation's result dict, which lives ONLY in the job.succeeded event.

    There is no ``result`` column on ``job`` and the API's job detail does not
    expose one; the phase 2 loop logs ``findings``, which the universe pass
    leaves NULL. Reading ``job["result"]`` therefore logs ``null`` for a pass that
    worked, which is the exact shape of silence this campaign keeps paying for:
    the numbers that justify the run would not be in the log.
    """
    try:
        events = api.call("GET", f"/v1/jobs/{job_id}/events")
    except Exception:  # noqa: BLE001 - logging must not fail the release
        return {}
    for ev in items(events):
        if ev.get("event") == event:
            return ev.get("fields") or {}
    for ev in items(events):
        if ev.get("event") == "job.succeeded":
            return (ev.get("fields") or {}).get("result") or {}
    return {}


def run_phase1(api: Api, plan: list[tuple[int, str]]) -> int:
    """Phase 1: grow the protein universe from every GAF, before any load.

    Three things make this a different loop and not a flag on the other one.

    No ontology. ``extract_goa_universe`` reads the GAF and nothing else, never a
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

    Sequential, not MAX_IN_FLIGHT, and the reason CHANGED with PROTEA#989. It
    used to be UniProt: two passes at once both hit the batch endpoint, which was
    the slow part (release 156 scanned in 4,3 min and then spent longer than that
    fetching 117.136 accessions). The pass no longer talks to UniProt at all, so
    what remains is the disk and the laptop: one release is a single gzip stream
    of up to 24 GB decompressed on one machine that already runs Postgres,
    RabbitMQ, MinIO, the API and the frontend, and more consumers on it buy +14%
    throughput at 97 C. NOTE that ``ensure_cached`` BLOCKS, so download and pass
    do not overlap: the measured prefetch is 423 s and the releases grow from 3,4
    GB at the old end to 19 GB at the new one.

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

    ``protein.first_admitted_release`` is now a column (PROTEA migration
    ``f2a8c41d9e37``), and the ascending order is what gives it a meaning. The
    operation writes it as a MINIMUM, not as a first writer, so this loop is free
    to resume, repeat a release or process them out of order without the value
    drifting upward. It is NOT the ``first_release`` an earlier migration
    refused: that one meant the earliest release that existed once the entry
    existed, is derivable from ``date_created``, and remains unstored. See
    ADR-D49.

    WHAT ASCENDING COSTS, declared rather than discovered later. A partial run
    stops being useful: the evaluation window is GOA 220 -> 227, at the new end,
    so an interrupted ascending run leaves 2016-2019 done and the window
    untouched. Descending covered the window in its first fifteen passes. The
    cost is accepted because a pass is now far cheaper than it was: it fetches
    NOTHING from UniProt, so what used to be scan plus fetch is scan alone, and
    the whole of phase 1 is expected to finish in one stretch.

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
            f"cuentan como hechas bajo {ADMIT_TIERS} ({sorted(done)}). "
            "Seguir dejaria el universo sin lo que solo aportan esas releases. "
            "O se restauran sus filas, o sus jobs no deben contar."
        )
    if done:
        log(f"universe already done (skipped, admit={ADMIT_TIERS}): {sorted(done)}")
    # Ascendente: ver el docstring. `plan` ya llega ascendente de parse_plan.
    pending = [r for r, _ in plan if r not in done]
    log(f"phase 1 ascending: {len(pending)} releases to go, {pending[:3]}..{pending[-1:]}")

    base = serve_base()
    ensure_cache_server()
    log(f"cache: serving {CACHE_DIR} at {base}")

    failures = 0
    prefetcher = _Prefetcher()
    for i, release in enumerate(pending):
        # Lo que la iteracion anterior dejo bajando puede ser justamente esta.
        prefetcher.wait()
        try:
            ensure_cached(release)
        except Exception as exc:  # noqa: BLE001 - one release must not end the run
            log(f"universe {release}: prefetch FAILED ({exc}); skipped")
            failures += 1
            continue
        # Y la siguiente se baja MIENTRAS esta se escanea, que es el ahorro.
        prefetcher.start(pending[i + 1] if i + 1 < len(pending) else None)
        gaf_url = f"{base}/goa_uniprot_all.gaf.{release}.gz"
        job = api.call(
            "POST",
            "/v1/jobs",
            {
                "operation": "extract_goa_universe",
                "queue_name": "protea.jobs",
                "description": f"fase 1, release {release}",
                "payload": {
                    "gaf_url": gaf_url,
                    # La release va en el payload porque la operacion la escribe
                    # en cada fila que inserta, como
                    # ``protein.first_admitted_release``. La operacion NO la
                    # saca de la URL: un numero leido de un nombre de fichero es
                    # una suposicion sobre una convencion, y este entra al corpus.
                    "release": release,
                    "dry_run": False,
                    "timeout_seconds": 3600,
                    # Los niveles, declarados AQUI aunque la operacion tenga
                    # un defecto igual, porque el defecto que obligo a tirar la
                    # campana anterior fue un criterio que viajaba en el codigo
                    # y no en el payload: un ``search_criteria: reviewed:true``
                    # dentro de un payload de insert_proteins del 2026-09-15 fijo
                    # el alcance de toda una campana sin que nadie lo declarase.
                    #
                    # El razonamiento de cada nivel y de cada exclusion esta en
                    # ADR-D49 y en MARCO-DECLARADO.md, con sus mediciones.
                    "admit": admit_for(release),
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
        # solo se pasa en la fase 1, extract_goa_universe.py, nunca en
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
        _drop_or_keep(release)

    log(f"phase 1 finished: {len(pending) - failures} ok, {failures} failed")
    return 1 if failures else 0


def _sin_secuencia() -> int:
    """Cuantas filas de ``protein`` no tienen secuencia todavia.

    Por la base y no por el informe de un job: es la cifra que decide si la fase
    3 tiene algo que hacer, y leerla del resultado del job anterior seria creerle
    a un numero en vez de mirar el estado.
    """
    out = subprocess.run(
        [
            "docker", "exec", "protea-postgres-1", "psql", "-U", "protea", "-d", "protea",
            "-t", "-A", "-c", "SELECT count(*) FROM protein WHERE sequence_id IS NULL;",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(f"sin_secuencia psql failed: {out.stderr[:300]}")
    return int(out.stdout.strip() or 0)


def run_phase3(api: Api) -> int:
    """Phase 3: the universe gets its sequences, once, from today's UniProt.

    WHY IT IS A PHASE AND NOT A STEP OF PHASE 1. The sequences are needed over
    the UNION of the 75 releases, not per release. Asking per release asked
    UniProt the same question up to 75 times and asked repeatedly about
    accessions it does not serve at all: 34% of the requests across the ten
    passes that ran that way, measured.

    WHY IT RUNS AFTER PHASE 2 AND NOT BETWEEN 1 AND 2. ``load_goa_annotations``
    gates on ``select(Protein.accession)`` alone, so an accession-only row admits
    every annotation its release carries: phase 2 does not need a single
    sequence. Running the fetch first would only mean fetching sequences for
    proteins before knowing the corpus is complete, and spending a day of
    requests before the thing that can still fail has finished.

    What DOES need the sequences is the embeddings, which come after this.

    THE POPULATION IS NOT A PAYLOAD. The operation asks the table for every row
    with no ``sequence_id`` at the moment the job runs. This driver passes no
    accession list, deliberately: a list built here would be a snapshot of the
    database taken before the job was even queued.

    NO TIMEOUT OF OUR OWN BEYOND THE JOB'S. One job over some 700.000 accessions
    in batches of a thousand is on the order of hours, and the retries live in the
    plugin. The driver waits and logs; if it dies, re-running is cheap, because
    the population is "whatever is still missing" and after a complete run that is
    only the deleted accessions.
    """
    pendientes = _sin_secuencia()
    log(f"phase 3: {pendientes} protein rows with no sequence")
    if pendientes == 0:
        log("phase 3: nothing to resolve, skipped")
        return 0
    job = api.call(
        "POST",
        "/v1/jobs",
        {
            "operation": "resolve_protein_sequences",
            "queue_name": "protea.jobs",
            "description": "fase 3, secuencias y fechas de todo el universo",
            "payload": {"timeout_seconds": 300},
        },
    )
    job_id = str(job["id"])
    log(f"phase 3: job {job_id[:8]} submitted")
    try:
        finished = api.wait_job(job_id, RESOLVE_JOB_TIMEOUT_S)
    except TimeoutError as exc:
        log(f"phase 3: {exc}")
        return 1
    status = (finished.get("status") or "").lower()
    if status != "succeeded":
        log(f"phase 3: FAILURE ({status}) err={finished.get('error_message')}")
        return 1
    resultado = job_result(api, job_id, "resolve_protein_sequences.done")
    log(f"phase 3: ok {json.dumps(resultado, ensure_ascii=False)}")
    restantes = _sin_secuencia()
    # Lo que queda sin secuencia DESPUES de una pasada completa son las
    # accesiones que UniProt ya no sirve, y sus nombres estan en el artefacto
    # sin_resolver.txt de este job. No es un fallo: es una cantidad, y antes era
    # la que el filtro silencioso tiraba.
    log(f"phase 3: {restantes} rows still without a sequence (deleted in UniProt)")
    return 0


def stamp_release_dates(api: Api) -> int:
    """Fill ``annotation_set.source_published_at`` for every set phase 2 created.

    WHY THIS IS NOT OPTIONAL, and why it belongs at the end of phase 2 rather
    than in somebody's head. The holdout guard (PROTEA#932) decides whether a
    window may inform a decision by comparing the window's end against the
    board's mark, and the thing it compares is that column. A set with no date
    is PASSED, because refusing every undated window would take down the tune
    windows to protect the holdout from a case that cannot be decided either
    way.

    Phase 2 creates 75 annotation sets and none of them has a date until this
    runs. So without this call the guard's undecidable branch is not an edge
    case, it is the ONLY case, and the protection the guard exists to provide is
    absent while appearing to be present. The guard now emits
    ``holdout_guard.undecidable`` when that happens, so the absence is visible,
    but visible is not the same as closed.

    Idempotent: the operation upserts by matching ``goa`` sets to the FTP index,
    so running it twice writes the same dates.
    """
    log("stamping annotation_set.source_published_at from the EBI index")
    job = api.call(
        "POST",
        "/v1/jobs",
        {
            "operation": "refresh_goa_release_dates",
            "queue_name": "protea.jobs",
            "description": "fechas de publicacion: sin ellas la guarda del holdout no decide",
            "payload": {},
        },
    )
    job_id = str(job["id"])
    try:
        finished = api.wait_job(job_id, ONTOLOGY_JOB_TIMEOUT_S)
    except TimeoutError as exc:
        log(f"release dates: {exc}")
        return 1
    status = (finished.get("status") or "").lower()
    if status != "succeeded":
        log(f"release dates: FAILURE ({status}) err={finished.get('error_message')}")
        log("  the holdout guard cannot decide until this succeeds: rerun --phase 2")
        return 1
    log(f"release dates: ok {json.dumps(job_result(api, job_id, 'refresh_goa_release_dates.done'), ensure_ascii=False)}")
    return 0


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
    if phase not in (1, 2, 3):
        raise SystemExit(f"--phase must be 1, 2 or 3, got {phase}")

    key = open(KEY_FILE, encoding="utf-8").read().strip()
    api = Api(API, key)
    plan = parse_plan(PLAN)

    if phase == 1:
        return run_phase1(api, plan)
    if phase == 3:
        return run_phase3(api)

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
    # Las fechas, al final de la fase 2 y no antes: la operacion empareja los
    # conjuntos `goa` contra el indice FTP, asi que necesita que existan todos.
    failures += stamp_release_dates(api)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
