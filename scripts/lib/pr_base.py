"""pr_base — canonical PR base branch per repo (FARM-1.3).

Single source of truth for the "what base does `gh pr create` use here?"
question. Two consumers:

1. The bash wrapper `scripts/lib/pr-base.sh` (calls this module as a CLI
   subcommand `lookup <repo>`).
2. The finalize script `scripts/finalize-subagent.sh`, which scans agent
   heartbeats for PR URLs and rebases any that landed on the wrong base
   via `gh pr edit <n> --base <correct>`.

Repos are matched by their GitHub `owner/name` slug. Both `name` alone
and the full `owner/name` form resolve, so callers can pass either of
`PROTEA`, `frapercan/PROTEA`, or the full URL fragment.

Hard rule (Thesis2 CLAUDE.md): the PROTEA stack PRs against `develop`;
the meta repos (agent-farm, thesis) PR against `main`. The historical
incidents that motivate this slice are listed in
`context/memory/feedback_pr_base_develop.md`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Iterable

# Canonical mapping. Keys are GitHub repo names (case-insensitive on
# match). The "owner" is informational only since this farm is single-
# owner; if the farm grows we will switch keys to `owner/name`.
REPO_BASE: dict[str, str] = {
    # PROTEA stack: trunk-based on develop
    "PROTEA": "develop",
    "protea-contracts": "develop",
    "protea-method": "develop",
    "protea-sources": "develop",
    "protea-runners": "develop",
    "protea-backends": "develop",
    "protea-reranker-lab": "develop",
    "cafaeval-protea": "develop",
    # Meta / authoring repos: trunk-based on main
    "agent-farm": "main",
    "thesis": "main",
}

# Anything matching this slug pattern is parseable.
_REPO_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+/)?([A-Za-z0-9_.-]+?)(\.git)?$")

# Recognise PR URLs and "owner/repo#N" shortrefs so finalize can extract
# the repo + PR number from a heartbeat without per-agent custom code.
_PR_URL_PATTERN = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/pull/(\d+)"
)
_PR_SHORT_PATTERN = re.compile(
    r"(?:^|[\s(])([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)\b"
)


class UnknownRepoError(KeyError):
    """Raised when a repo has no canonical base in the table."""


def _normalize(repo: str) -> str:
    """Return just the repo name (no owner, no `.git`) for lookup."""
    m = _REPO_PATTERN.match(repo.strip())
    if not m:
        raise UnknownRepoError(f"unparseable repo string: {repo!r}")
    return m.group(2)


def lookup(repo: str) -> str:
    """Return the canonical base branch for `repo`.

    Accepts:
      - bare names: `PROTEA`, `agent-farm`
      - owner/name slugs: `frapercan/PROTEA`
      - `.git` suffix tolerated

    Raises:
      UnknownRepoError if the repo is not in the canonical table. We
      raise instead of falling back to `main` because a silent fallback
      is exactly the bug this slice fixes.
    """
    name = _normalize(repo)
    # Case-sensitive primary match (the table is the authoritative casing).
    if name in REPO_BASE:
        return REPO_BASE[name]
    # Case-insensitive secondary match for human typos.
    lower = name.lower()
    for known, base in REPO_BASE.items():
        if known.lower() == lower:
            return base
    raise UnknownRepoError(
        f"no canonical base for repo {name!r}; "
        f"update REPO_BASE in {__file__}"
    )


def known_repos() -> Iterable[str]:
    return tuple(REPO_BASE.keys())


def extract_pr_refs(text: str) -> list[tuple[str, str, int]]:
    """Return `(owner, repo, pr_number)` tuples found in `text`.

    Used by `finalize-subagent.sh` to scan heartbeat messages for PR
    URLs the agent printed. Order-preserving, deduplicated by the tuple.
    """
    seen: set[tuple[str, str, int]] = set()
    out: list[tuple[str, str, int]] = []
    for pattern in (_PR_URL_PATTERN, _PR_SHORT_PATTERN):
        for m in pattern.finditer(text):
            tup = (m.group(1), m.group(2), int(m.group(3)))
            if tup not in seen:
                seen.add(tup)
                out.append(tup)
    return out


# ---------------------------------------------------------------------------
# CLI entry points (consumed by pr-base.sh and finalize-subagent.sh)
# ---------------------------------------------------------------------------


def _cmd_lookup(args: argparse.Namespace) -> int:
    try:
        print(lookup(args.repo))
    except UnknownRepoError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


def _cmd_list(_args: argparse.Namespace) -> int:
    for name, base in sorted(REPO_BASE.items()):
        print(f"{name}\t{base}")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    text = sys.stdin.read() if args.stdin else args.text or ""
    refs = extract_pr_refs(text)
    out = [
        {"owner": o, "repo": r, "number": n, "expected_base": _try_lookup(r)}
        for (o, r, n) in refs
    ]
    print(json.dumps(out))
    return 0


def _try_lookup(repo: str) -> str | None:
    try:
        return lookup(repo)
    except UnknownRepoError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr_base")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lookup = sub.add_parser("lookup", help="print base for a repo")
    p_lookup.add_argument("repo")
    p_lookup.set_defaults(func=_cmd_lookup)

    p_list = sub.add_parser("list", help="dump the canonical table")
    p_list.set_defaults(func=_cmd_list)

    p_scan = sub.add_parser("scan", help="extract PR refs from text/stdin")
    g = p_scan.add_mutually_exclusive_group(required=True)
    g.add_argument("--stdin", action="store_true", help="read text from stdin")
    g.add_argument("--text", help="inline text")
    p_scan.set_defaults(func=_cmd_scan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
