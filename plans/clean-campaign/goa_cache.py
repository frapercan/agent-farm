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
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request

CHUNK = 1 << 20  # report progress per MiB


def _fetch_range(url: str, dest: str, start: int, end: int, timeout: int = 300) -> int:
    req = request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    written = 0
    with request.urlopen(req, timeout=timeout) as resp:
        fd = os.open(dest, os.O_WRONLY)
        try:
            while True:
                block = resp.read(1 << 18)
                if not block:
                    break
                os.pwrite(fd, block, start + written)
                written += len(block)
        finally:
            os.close(fd)
    return written


def fetch(url: str, dest: str, connections: int = 24) -> None:
    """Download ``url`` to ``dest`` atomically.

    Writes to ``dest + ".part"`` and renames onto ``dest`` only after every
    range has been written in full. The pre-truncated ``.part`` is sparse, so
    a hole reads back as zeros: publishing it under ``dest`` while it is still
    downloading makes a gzip reader see a valid prefix followed by zeros and
    fail mid-stream ("Error -3 ... invalid block type / CRC check failed").
    The atomic rename guarantees ``dest`` exists only once it is complete.
    """
    head = request.Request(url, method="HEAD")
    with request.urlopen(head, timeout=60) as resp:
        size = int(resp.headers["Content-Length"])
    part = dest + ".part"
    with open(part, "wb") as fh:
        fh.truncate(size)
    bounds = [(i * size // connections, (i + 1) * size // connections - 1) for i in range(connections)]
    errors: list[str] = []
    lock = threading.Lock()

    def worker(start: int, end: int) -> None:
        expected = end - start + 1
        last = "no data read"
        for attempt in (1, 2, 3):
            try:
                got = _fetch_range(url, part, start, end)
            except Exception as exc:  # noqa: BLE001 - retried per range
                last = f"error: {exc}"
                continue
            if got >= expected:
                return
            last = f"short read {got}/{expected}"
        # Fell through all three attempts without a full range: a short read
        # is a hole, and a hole is a corrupt file, so record it as an error
        # instead of silently accepting it (the old code only reported the
        # raised exceptions and let short reads pass).
        with lock:
            errors.append(f"{start}-{end}: {last}")

    threads = [threading.Thread(target=worker, args=b, daemon=True) for b in bounds]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        try:
            os.remove(part)
        except OSError:
            pass
        raise RuntimeError(f"{len(errors)} ranges failed: {errors[0]}")
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
        fetch(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 24)
    elif sys.argv[1] == "serve":
        serve(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1")
    else:
        raise SystemExit("usage: goa_cache.py fetch <url> <dest> [conns] | serve <dir> <port> [host]")
