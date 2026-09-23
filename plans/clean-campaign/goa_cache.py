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
    """
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
    return holes


def _range_resume_start(rs: int, re: int, holes: list[tuple[int, int]]) -> int | None:
    """First unwritten byte in ``[rs, re]``, or ``None`` if it is fully written."""
    for hs, he in holes:
        if he < rs:
            continue
        if hs > re:
            return None
        return max(rs, hs)
    return None


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
        os.rename(part, dest)
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
    os.rename(part, dest)


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
