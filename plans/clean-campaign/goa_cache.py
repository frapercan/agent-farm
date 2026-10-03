#!/usr/bin/env python3
"""GAF local cache: parallel range downloader + Range-capable HTTP server.

Purpose: EBI shapes per-connection throughput erratically (30 KB/s - 1 MB/s
on identical ranges, aggregate across connections much higher). Downloading
each GAF once with many parallel ranges and serving it to the workers over
localhost removes EBI from the load path entirely.

Usage:
  goa_cache.py fetch <url> <dest> [connections]   # parallel range download
  goa_cache.py serve <dir> <port>                 # blocking Range HTTP server

The fetcher preallocates the file and writes ranges with os.pwrite, so a
slow connection never blocks the others and retries are per-range.
"""

from __future__ import annotations

import gzip
import os
import queue
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request

CHUNK = 1 << 20  # report progress per MiB


RANGES_PER_CONNECTION = 32
"""How finely the file is cut, per connection.

This number only decides the SHAPE OF THE TAIL. While there are more ranges
left than connections every connection has something to do; from the moment
fewer remain, connections start finishing with nothing to pick up, and
throughput falls off towards the rate of the single slowest range. So the
degraded stretch is the last ``connections x range_size`` bytes, and this
constant is what makes that stretch small.

Measured on release 218 (18,06 GB) with the previous value of 4: the bulk of
the file pulled 1,52 MB/s, and the last 3% pulled 0,44 MB/s with ten ranges
left and fourteen connections idle. At 4 the degraded stretch is 24 x 188 MB =
4,5 GB; at 32 it is 24 x 23 MB = 564 MB, eight times shorter.

The cost is HTTP requests: 768 instead of 96 for an 18 GB file, about one every
sixteen seconds over a three-hour download. EBI shapes per connection and not
per request, so that is not what it charges for.
"""

class RangeIgnoredError(RuntimeError):
    """The server answered a Range request with the whole entity.

    Only 206 means the bytes in the body are the bytes that were asked for. A
    200 means the server ignored the header and is sending the file from zero,
    and writing that body at ``start`` lays the beginning of the file over the
    middle of the destination.

    Nothing downstream would catch it. The caller compares bytes written
    against the range size, and a full body is always larger, so the range
    "succeeds"; ``_find_holes`` then finds no holes, and the .part is renamed
    onto the final path. The cache ends up holding a file that is the right
    length, has no holes, and is garbage -- and the symptom is the gzip
    "Error -3 / CRC check failed" at load time, which is the same symptom the
    sparse .part used to produce. That one was fixed by the atomic rename; this
    is a second, independent route to it, and it was unguarded.
    """


def _fetch_range(url: str, dest: str, start: int, end: int, timeout: int = 300) -> int:
    req = request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    written = 0
    want = end - start + 1
    with request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 206:
            raise RangeIgnoredError(
                f"{url} answered {resp.status} to bytes={start}-{end}; only 206 "
                "means the body is the range that was asked for"
            )
        fd = os.open(dest, os.O_WRONLY)
        try:
            while written < want:
                block = resp.read(min(1 << 18, want - written))
                if not block:
                    break
                os.pwrite(fd, block, start + written)
                written += len(block)
        finally:
            os.close(fd)
    return written


def _find_holes(path: str, size: int) -> list[tuple[int, int]]:
    """Return the unwritten byte ranges of a sparse ``.part`` file.

    ``fetch`` pre-truncates the destination to its full size and writes ranges
    in place, so an unwritten region is a sparse hole. ``SEEK_DATA`` /
    ``SEEK_HOLE`` recover those holes straight from the filesystem allocation,
    which is what lets a retried fetch resume from the bytes it already has
    instead of starting over.

    ALLOCATION IS NOT CONTENT, AND THE UNIT IS A BLOCK. The kernel answers
    SEEK_HOLE at filesystem-block granularity, so a block that was written in
    part reads back as written in full, and the bytes after the last real write
    inside it are indistinguishable from data. That happens on every
    interruption: ``_fetch_range`` writes at ``start + written`` and the retry
    resumes at ``pos += got``, an offset with no reason to be block-aligned.

    Measured on 2026-09-29 on this cache's own filesystem: written cleanly up to
    byte 3.146.962, the first hole reported was 3.149.824 -- the next block
    boundary -- leaving **2.862 bytes** that were never written and that a
    resume would have skipped. Up to one block of zeros per interruption,
    injected into the middle of a gzip stream.

    It was not theoretical. GOA 219's first cached copy died with "Error -3
    while decompressing data: invalid stored block lengths", and GOA 218's
    decoded into a stretch with no newline in it, so the loader's per-line
    iteration accumulated one string of gigabytes and the worker was OOM-killed
    at 25 GB, twice, at the same page. Both files had been assembled across
    interruptions.

    So each hole is widened backwards to the start of its block, which re-fetches
    at most one block per hole and makes the partial write moot. Nothing is
    trusted that the filesystem cannot report exactly.
    """
    bloque = _block_size(path)
    holes: list[tuple[int, int]] = []
    fd = os.open(path, os.O_RDONLY)
    try:
        pos = 0
        while pos < size:
            try:
                data = os.lseek(fd, pos, os.SEEK_DATA)
            except OSError:
                holes.append((pos, size - 1))
                break
            if data > pos:
                holes.append((pos, data - 1))
            try:
                pos = os.lseek(fd, data, os.SEEK_HOLE)
            except OSError:
                break
    finally:
        os.close(fd)
    return [(max(0, (hs // bloque - 1) * bloque), he) for hs, he in holes]


def _block_size(path: str) -> int:
    """The filesystem block SEEK_HOLE answers in, or a safe 4 KiB default."""
    try:
        return max(os.statvfs(path).f_bsize, 512)
    except OSError:
        return 4096


def _range_resume_start(rs: int, re: int, holes: list[tuple[int, int]]) -> int | None:
    """First unwritten byte in ``[rs, re]``, or ``None`` if it is fully written."""
    for hs, he in holes:
        if he < rs:
            continue
        if hs > re:
            return None
        return max(rs, hs)
    return None


MAX_LINEA = 1 << 20
"""Longitud maxima admisible de una linea de GAF, en bytes.

Medido sobre este corpus: una linea son ~187 bytes y la mas larga vista en 16
millones fueron 1.278. Un MiB deja ochocientas veces de margen, asi que no
rechaza nada legitimo, y aun asi cae de inmediato en el caso que importa.
"""


def verify(path: str, max_linea: int = MAX_LINEA) -> None:
    """Recorre el .gz entero y levanta si no sirve para cargar.

    Comprueba DOS cosas en una pasada, porque las dos han fallado en esta
    campana y la segunda no la caza la primera:

    1. Integridad gzip. La primera copia cacheada de GOA 219 murio en el
       worker con "Error -3 while decompressing data: invalid stored block
       lengths", por ceros metidos en el stream.

    2. Longitud de linea. GOA 218 era gzip VALIDO: los ceros decodificaron a un
       tramo sin un solo salto de linea. El plugin del cargador itera por
       lineas y con ``errors="replace"`` los bytes invalidos pasan como texto,
       asi que una sola "linea" crecio a gigabytes y el kernel mato al worker a
       25 GB, dos veces, en la misma pagina. Un fichero puede estar
       perfectamente bien formado y seguir siendo una bomba.

    PRECIO. Medido en esta maquina, 337 MB/s descomprimiendo: unos doce minutos
    para un GAF de 20 GB comprimidos. Frente a dos horas de descarga y tres de
    carga, es un 7% por no volver a servir basura. Y lo paga quien descarga una
    vez, no el worker en cada lectura.

    POR QUE AQUI Y NO EN EL CARGADOR. El cargador vive en otro paquete
    (``protea_sources``) y no acota la linea; mientras siga asi, cualquier
    fichero mal formado lo tumba. Esta funcion es la unica puerta por la que un
    GAF entra al cache, asi que es donde la comprobacion sirve de algo.
    """
    salida = 0
    linea_n = 0
    try:
        with gzip.open(path, "rb") as fh:
            for linea in fh:
                salida += len(linea)
                linea_n += 1
                if len(linea) > max_linea:
                    raise ValueError(
                        f"linea {linea_n} mide {len(linea)} bytes (maximo {max_linea}); "
                        "un GAF legitimo no las tiene asi, el fichero esta corrupto"
                    )
    except ValueError:
        raise
    except Exception as exc:  # cualquier fallo de gzip invalida el fichero
        raise ValueError(
            f"gzip ilegible tras {salida / 1e9:.2f} GB y {linea_n:,} lineas: {exc}"
        ) from exc


def _publicar(part: str, dest: str, url: str) -> None:
    """Unica puerta por la que un .part pasa a ser un GAF servible.

    Existe porque habia DOS renames y la verificacion de #321 solo cubria uno.
    El otro es el atajo de "ya no quedan huecos", que se toma justo cuando un
    intento anterior escribio todos los rangos y murio antes de publicar -- es
    decir, exactamente el caso en el que lo que hay en disco es sospechoso.
    Publicarlo sin leerlo era el agujero.

    Con dos renames, la proxima comprobacion que alguien anada volvera a cubrir
    uno solo. Con uno, no hay donde equivocarse.

    Si no verifica, el .part se borra: no se sabe DONDE empieza a no servir, asi
    que reanudar sobre el heredaria el dano. Se empieza de cero.
    """
    try:
        verify(part)
    except ValueError as exc:
        os.remove(part)
        raise RuntimeError(f"{url}: descargado pero no verificable, descartado -> {exc}") from exc
    os.rename(part, dest)


def fetch(url: str, dest: str, connections: int = 24) -> None:
    """Download ``url`` to ``dest`` atomically, resumable and throttled.

    The file is split into fixed ranges and written to ``dest + ".part"``;
    ``dest`` only appears once every range is complete, so a partial download
    is never served. A retried fetch re-detects the sparse holes already on
    disk, skips the ranges that are fully written and resumes the rest from the
    first unwritten byte — bytes already on disk are never thrown away.

    ``connections`` bounds concurrent HTTP requests (default 24). EBI throttles
    each connection to roughly 0.1 MB/s regardless of how many are open, so
    throughput is set by this number and not by the link: measured on 2026-09-23,
    one connection gave 0.09 MB/s and two gave 0.14, while release 217 pulled
    2.9 MB/s over 24. Twenty-four sits under this machine's 4.66 MB/s link with
    room to spare. Each range retries with exponential backoff (5s doubling to
    80s), and every retry resumes from where the previous attempt stopped, so a
    connection lost to the concurrency costs its own last chunk and nothing more.

    The ranges are handed to a pool of ``connections`` threads that pull from a
    queue, not one thread per range. A thread per range meant 96 threads for 24
    connections, 96 seconds of staggered startup before the last one began, and
    a tail in which most of them had already finished and could not help with
    what was left. See :data:`RANGES_PER_CONNECTION` for what that tail cost.
    """
    head = request.Request(url, method="HEAD")
    with request.urlopen(head, timeout=60) as resp:
        size = int(resp.headers["Content-Length"])
    part = dest + ".part"
    if os.path.exists(part):
        if os.path.getsize(part) != size:
            os.remove(part)  # stale .part from a different file version
    if not os.path.exists(part):
        with open(part, "wb") as fh:
            fh.truncate(size)

    n_ranges = max(1, connections * RANGES_PER_CONNECTION)
    ranges = [
        (i * size // n_ranges, (i + 1) * size // n_ranges - 1)
        for i in range(n_ranges)
    ]
    holes = _find_holes(part, size)
    if not holes:
        _publicar(part, dest, url)
        return

    todo: list[tuple[int, int]] = []
    for rs, re in ranges:
        s = _range_resume_start(rs, re, holes)
        if s is not None:
            todo.append((s, re))

    errors: list[str] = []
    lock = threading.Lock()
    work: queue.Queue[tuple[int, int]] = queue.Queue()
    for item in todo:
        work.put(item)

    def one_range(hstart: int, hend: int) -> None:
        """Pull [hstart, hend], retrying what a retry can fix.

        A short read or a dropped connection is transient and the backoff is
        the right answer. A server answering 200 to a Range request is not: it
        will answer 200 again, so the six attempts would spend 155 seconds per
        range proving something the first response already said. That one is
        recorded and abandoned immediately.
        """
        backoff = 5.0
        pos = hstart
        last = "no data read"
        for attempt in range(6):
            try:
                got = _fetch_range(url, part, pos, hend)
            except RangeIgnoredError as exc:
                with lock:
                    errors.append(f"{hstart}-{hend}: {exc}")
                return
            except Exception as exc:  # noqa: BLE001 - retried with backoff
                got = -1
                last = f"error: {exc}"
            else:
                last = f"short read {got}/{hend - pos + 1}"
            if got >= hend - pos + 1:
                return
            pos += max(got, 0)
            if pos > hend:
                return
            if attempt < 5:
                time.sleep(backoff)
                backoff *= 2.0
        with lock:
            errors.append(f"{hstart}-{hend}: incomplete at {pos} ({last})")

    def puller(stagger: float) -> None:
        time.sleep(stagger)
        while True:
            try:
                hstart, hend = work.get_nowait()
            except queue.Empty:
                return
            try:
                one_range(hstart, hend)
            finally:
                work.task_done()

    threads = [
        threading.Thread(target=puller, args=(i * 1.0,), daemon=True)
        for i in range(min(connections, len(todo)))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        # Keep the .part: the next attempt resumes from the remaining holes.
        raise RuntimeError(f"{len(errors)}/{len(todo)} ranges failed: {errors[0]}")
    if _find_holes(part, size):
        raise RuntimeError("holes remain after fetch; refusing to rename")
    _publicar(part, dest, url)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        path = os.path.join(os.getcwd(), self.path.lstrip("/"))
        path = os.path.normpath(path)
        if path.endswith(".part"):
            # A partially-downloaded range file must never be served: its
            # holes read as zeros and corrupt any gzip consumer.
            self.send_error(404)
            return
        if not (os.path.isfile(path) and os.path.realpath(path).startswith(os.getcwd())):
            self.send_error(404)
            return
        size = os.path.getsize(path)
        range_header = self.headers.get("Range")
        if range_header:
            m = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
                end = min(end, size - 1)
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Content-Type", "application/gzip")
                self.end_headers()
                with open(path, "rb") as fh:
                    fh.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        block = fh.read(min(CHUNK, remaining))
                        if not block:
                            break
                        self.wfile.write(block)
                        remaining -= len(block)
                return
        self.send_response(200)
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Type", "application/gzip")
        self.end_headers()
        with open(path, "rb") as fh:
            while True:
                block = fh.read(CHUNK)
                if not block:
                    break
                self.wfile.write(block)

    def log_message(self, *_args: object) -> None:
        pass


def serve(directory: str, port: int, host: str = "127.0.0.1") -> None:
    os.chdir(directory)
    os.makedirs(directory, exist_ok=True)
    server = ThreadingHTTPServer((host, port), _Handler)
    server.serve_forever()


if __name__ == "__main__":
    if sys.argv[1] == "fetch":
        fetch(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2)
    elif sys.argv[1] == "serve":
        serve(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1")
    else:
        raise SystemExit("usage: goa_cache.py fetch <url> <dest> [conns] | serve <dir> <port> [host]")
