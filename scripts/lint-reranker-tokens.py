#!/usr/bin/env python3
"""Reject `vN` reranker tokens in publishable prose.

The author keeps slipping back into the historical `vN` reranker
shorthand (v3, v9, v18, v22, ...) when writing prose. The canonical
form for naming a reranker is the axis-tuple notation defined in
`context/experiment-axis-map.md`:

    run--plm=<plm-id>--k=<int>--rr=<reranker-id>--feat=<bundle>
        --eval=<dataset>--prop=<propagation>--ens=<ensemble>

This linter scans publishable prose (Sphinx docs, thesis chapters,
READMEs, ADRs) for the regex ``\\bv\\d+\\b`` and flags every match
that is NOT in an explicit allowlist. By default, it scans docs/,
chapters/, README*, and ADR* files. Changelog files (CHANGELOG*) are
intentionally excluded because version histories legitimately contain
bare `vN` tokens (schema versions, build numbers, semver-without-dot)
unrelated to reranker shorthands. Four token classes are allowed:

1. GOA snapshot identifiers: v160, v200, v210, v215, v220, v226, v227,
   v229, v230
2. Semver prefixes: any token immediately followed by ``.digit``
   (e.g. ``v0.3.0``, ``v2.1.13``).  These are package/tool release
   strings, not reranker shorthands.
3. Dataset-name prefixes: any token immediately preceded by ``bench-``
   (e.g. ``bench-v1-K5-filtered``).  Dataset names use a fixed
   ``bench-vN`` scheme that is not a reranker shorthand.
4. URL path segments: any token immediately preceded by ``/`` (e.g.
   ``/v1/jobs``, ``/api/v1/jobs``, ``` ``/v1/jobs`` ``` inside an
   inline code span, ``.. http:get:: /v1/jobs`` Sphinx directives).
   URL versioning is an independent axis from reranker version
   shorthand; see ADR-D4 for the API versioning policy.

Slice: FARM-EXP.6 (farm-platform loop); policy carve-outs Q1 (semver)
and Q2 (bench-vN) added in FIX-47-linter-policy; Q3 (URL path) added
in FIX-395-api-path-carve-out.

Exit codes:
    0 — clean (no offences)
    1 — offences found (each printed to stderr with file:line:col)
    2 — invocation error
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Exact GOA snapshot allowlist. Edits here propagate to every consumer
# via the reusable workflow; do not duplicate elsewhere.
GOA_ALLOWLIST: frozenset[str] = frozenset({
    "v160", "v200", "v210", "v215", "v220",
    "v226", "v227", "v229", "v230",
})

# Word-bounded vN token. Case-sensitive; the GOA shorthand is always
# lowercase. We match v followed by one or more digits, no letters.
TOKEN_RE = re.compile(r"\bv\d+\b")

# Prose extensions worth scanning. Code files (`.py`, `.yaml`, ...)
# legitimately use `vN` as identifiers (e.g. service_v2) and are out
# of scope.
PROSE_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".rst", ".tex", ".txt",
})

# Directories to skip when scanning a tree.
SKIP_DIRS: frozenset[str] = frozenset({
    ".git", ".venv", "venv", "node_modules",
    "_build", "build", "dist",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "__pycache__",
})

# Default scan roots, relative to cwd. Used when neither positional
# files nor `--paths` are given. Missing roots are silently skipped.
DEFAULT_ROOTS: tuple[str, ...] = (
    "docs",
    "chapters",
    "appendix",
    "frontmatter",
    "bibliography",
    "decisions",
)

# Default top-level glob patterns. Same skip semantics.
DEFAULT_TOPLEVEL_GLOBS: tuple[str, ...] = (
    "README*",
    "ADR*",
)

SUGGESTION = (
    "  Use the axis-tuple form: "
    "run--plm=...--k=...--rr=...--feat=...--eval=...--prop=...--ens=...\n"
    "  See context/experiment-axis-map.md for canonical mappings.\n"
    "  GOA snapshot allowlist (these tokens are fine): "
    + " ".join(sorted(GOA_ALLOWLIST, key=lambda t: int(t[1:])))
)


def iter_scan_targets(paths: list[Path]) -> list[Path]:
    """Expand a mix of files and directories into a sorted list of
    prose files to scan.

    - Files are kept verbatim regardless of extension (caller asked
      explicitly).
    - Directories are walked; only ``PROSE_EXTENSIONS`` files kept;
      ``SKIP_DIRS`` pruned in place.
    """

    out: list[Path] = []
    seen: set[Path] = set()

    for p in paths:
        if not p.exists():
            print(
                f"warning: scan target does not exist: {p}",
                file=sys.stderr,
            )
            continue
        if p.is_file():
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                out.append(p)
            continue
        # directory walk
        for dirpath, dirnames, filenames in os.walk(p):
            # in-place prune
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if Path(fname).suffix.lower() in PROSE_EXTENSIONS:
                    fp = Path(dirpath) / fname
                    resolved = fp.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        out.append(fp)

    out.sort()
    return out


def resolve_default_targets(cwd: Path) -> list[Path]:
    """Build the default set of scan targets relative to ``cwd``."""

    targets: list[Path] = []
    for name in DEFAULT_ROOTS:
        candidate = cwd / name
        if candidate.exists():
            targets.append(candidate)
    for pattern in DEFAULT_TOPLEVEL_GLOBS:
        targets.extend(sorted(cwd.glob(pattern)))
    return targets


def scan_file(path: Path) -> list[tuple[int, int, str]]:
    """Scan a single file and return a list of ``(line, col, token)``
    offences. Non-UTF-8 files are best-effort decoded; binary noise is
    silently skipped.
    """

    offences: list[tuple[int, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return offences
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return offences

    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in TOKEN_RE.finditer(line):
            token = match.group(0)
            # GOA snapshot allowlist.
            if token in GOA_ALLOWLIST:
                continue
            # Q1: semver carve-out.  Skip tokens where the match is
            # immediately followed by a dot and at least one digit,
            # e.g. ``v0.3.0``, ``v2.1.13``.  These are release-version
            # strings, not reranker shorthands.
            suffix = line[match.end():]
            if suffix and suffix[0] == "." and len(suffix) > 1 and suffix[1].isdigit():
                continue
            # Q2: bench-dataset carve-out.  Skip tokens where the match
            # is immediately preceded by ``bench-``, e.g. the ``v1`` in
            # ``bench-v1-K5-filtered``.  Dataset names follow a fixed
            # ``bench-vN`` scheme that is not a reranker shorthand.
            prefix = line[: match.start()]
            if prefix.endswith("bench-"):
                continue
            # Q3: URL-path carve-out.  Skip tokens immediately preceded
            # by a forward slash, e.g. ``/v1/jobs`` or ``/api/v1/jobs``,
            # including the same form inside backtick code spans and
            # inside Sphinx ``.. http:get:: /v1/jobs`` directives. URL
            # versioning is an independent axis from reranker version
            # shorthand (see ADR-D4); reranker shorthand always lacks
            # the leading slash.
            if prefix.endswith("/"):
                continue
            offences.append((line_no, match.start() + 1, token))
    return offences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lint-reranker-tokens.py",
        description=(
            "Reject vN reranker shorthand in publishable prose. "
            "Only the 9 GOA snapshot tokens are allowed."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Files or directories to scan. If omitted and --paths is "
            "not given, scans the default prose roots under cwd."
        ),
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        metavar="PATH",
        help=(
            "Explicit list of paths (files or directories). Overrides "
            "positional files when both are given."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the suggestion footer (offences still print).",
    )
    args = parser.parse_args(argv)

    if args.paths:
        raw = [Path(p) for p in args.paths]
    elif args.files:
        raw = [Path(p) for p in args.files]
    else:
        raw = resolve_default_targets(Path.cwd())

    if not raw:
        # No files to scan and no defaults available is not an error;
        # treat as clean. (Useful for fresh repos.)
        return 0

    targets = iter_scan_targets(raw)

    total = 0
    for fp in targets:
        offences = scan_file(fp)
        for line, col, token in offences:
            print(
                f"{fp}:{line}:{col}: 'vN' reranker shorthand is "
                f"forbidden in publishable prose (token: {token!r}).",
                file=sys.stderr,
            )
            total += 1

    if total:
        if not args.quiet:
            print("", file=sys.stderr)
            print(SUGGESTION, file=sys.stderr)
            print("", file=sys.stderr)
            print(
                f"reranker-token linter: {total} offence(s) found.",
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
